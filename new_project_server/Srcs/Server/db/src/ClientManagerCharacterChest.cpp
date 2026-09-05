#include "stdafx.h"
#include "../../common/CommonDefines.h"

#ifdef ENABLE_CHARACTER_CHEST

#include "ClientManager.h"
#include "DBManager.h"
#include "Main.h"
#include "Cache.h"
#include "../../common/character_chest.h"

extern bool CreatePlayerTableFromRes(MYSQL_RES * res, TPlayerTable * pkTab);
extern bool CreateItemTableFromRes(MYSQL_RES * res, std::vector<TPlayerItem> * pVec, DWORD dwPID);

static void CharacterChestLog(BYTE logType, DWORD actorAccount, DWORD actorPid, DWORD targetPid, DWORD itemId, BYTE result)
{
	char szQuery[512];
	snprintf(szQuery, sizeof(szQuery),
		"INSERT INTO character_chest_log (log_type, actor_account_id, actor_pid, target_pid, item_id, result) "
		"VALUES(%u, %u, %u, %u, %u, %u)",
		logType, actorAccount, actorPid, targetPid, itemId, result);
	CDBManager::instance().AsyncQuery(szQuery, SQL_LOG);
}

static bool CharacterChestValidatePassword(DWORD accountId, const char* password)
{
	char szQuery[256];
	snprintf(szQuery, sizeof(szQuery),
		"SELECT social_id FROM account WHERE id=%u LIMIT 1", accountId);
	const auto pMsg(CDBManager::instance().DirectQuery(szQuery, SQL_ACCOUNT));
	if (!pMsg->Get() || pMsg->Get()->uiNumRows == 0)
		return false;

	const MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
	if (!row || !row[0])
		return false;

	const char* socialId = row[0];
	if (strlen(socialId) < 7)
		return false;

	return (0 == strncmp(password, socialId + strlen(socialId) - 7, 7));
}

static int CharacterChestFindEmptySlot(MYSQL_ROW row, int colStart, int colCount)
{
	for (int i = 0; i < colCount; ++i)
	{
		DWORD pid = 0;
		str_to_number(pid, row[colStart + i]);
		if (pid == 0)
			return i;
	}
	return -1;
}

static bool CharacterChestIsPidInAccountIndex(const char* tablePostfix, DWORD accountId, DWORD pid)
{
	char szQuery[512];
#ifdef ENABLE_PLAYER_PER_ACCOUNT5
	snprintf(szQuery, sizeof(szQuery),
		"SELECT 1 FROM player_index%s WHERE id=%u AND (pid1=%u OR pid2=%u OR pid3=%u OR pid4=%u OR pid5=%u) LIMIT 1",
		tablePostfix, accountId, pid, pid, pid, pid, pid);
#else
	snprintf(szQuery, sizeof(szQuery),
		"SELECT 1 FROM player_index%s WHERE id=%u AND (pid1=%u OR pid2=%u OR pid3=%u OR pid4=%u) LIMIT 1",
		tablePostfix, accountId, pid, pid, pid, pid);
#endif
	const auto pMsg(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
	return (pMsg->Get() && pMsg->Get()->uiNumRows > 0);
}

static bool CharacterChestBeginTx()
{
	const auto pMsg(CDBManager::instance().DirectQuery("START TRANSACTION", SQL_PLAYER));
	return pMsg->Get() != nullptr;
}

static void CharacterChestRollbackTx()
{
	CDBManager::instance().DirectQuery("ROLLBACK", SQL_PLAYER);
}

static bool CharacterChestCommitTx()
{
	const auto pMsg(CDBManager::instance().DirectQuery("COMMIT", SQL_PLAYER));
	return pMsg->Get() != nullptr;
}

static const WORD s_aBiologistLevels[CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT] =
{
	30, 40, 50, 60, 70, 80, 85, 90, 92, 94
};

static int CharacterChestBiologistLevelToIndex(WORD wLevel)
{
	for (int i = 0; i < CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT; ++i)
	{
		if (s_aBiologistLevels[i] == wLevel)
			return i;
	}
	return -1;
}

static void CharacterChestFillBiologistStatus(const char* tablePostfix, DWORD dwPID, BYTE* abStatus)
{
	memset(abStatus, CHARACTER_CHEST_BIOLOGIST_NONE, CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT);

	char szQuery[256];
	snprintf(szQuery, sizeof(szQuery),
		"SELECT szName FROM quest%s WHERE dwPID=%u AND szName LIKE 'collect_quest_lv%%'",
		tablePostfix, dwPID);

	const auto pQuest(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
	if (!pQuest->Get() || !pQuest->Get()->pSQLResult)
		return;

	int maxIdx = -1;
	MYSQL_RES* res = pQuest->Get()->pSQLResult;
	while (MYSQL_ROW row = mysql_fetch_row(res))
	{
		if (!row[0])
			continue;

		const char* szName = row[0];
		if (strncmp(szName, "collect_quest_lv", 16) != 0)
			continue;

		int level = 0;
		str_to_number(level, szName + 16);
		const int idx = CharacterChestBiologistLevelToIndex((WORD) level);
		if (idx > maxIdx)
			maxIdx = idx;
	}

	if (maxIdx < 0)
		return;

	for (int i = 0; i < maxIdx; ++i)
		abStatus[i] = CHARACTER_CHEST_BIOLOGIST_DONE;
	abStatus[maxIdx] = CHARACTER_CHEST_BIOLOGIST_PROGRESS;
}

void CClientManager::QUERY_CHARACTER_CHEST(CPeer* peer, DWORD dwHandle, TPacketGDCharacterChest* p)
{
	TPacketDGCharacterChest pack;
	memset(&pack, 0, sizeof(pack));
	pack.bOp = p->bOp;
	pack.dwActorPID = p->dwActorPID;
	pack.dwTargetPID = p->dwTargetPID;
	pack.dwItemID = p->dwItemID;
	pack.wItemCell = p->wItemCell;

	const auto SendReply = [&](BYTE result)
	{
		pack.bResult = result;
		peer->EncodeHeader(HEADER_DG_CHARACTER_CHEST, dwHandle, sizeof(pack));
		peer->Encode(&pack, sizeof(pack));
	};

	if (!peer)
		return;

	switch (p->bOp)
	{
		case CHARACTER_CHEST_OP_LIST:
		{
			char szQuery[512];
#ifdef ENABLE_PLAYER_PER_ACCOUNT5
			snprintf(szQuery, sizeof(szQuery),
				"SELECT pid1, pid2, pid3, pid4, pid5 FROM player_index%s WHERE id=%u",
				GetTablePostfix(), p->dwAccountID);
#else
			snprintf(szQuery, sizeof(szQuery),
				"SELECT pid1, pid2, pid3, pid4 FROM player_index%s WHERE id=%u",
				GetTablePostfix(), p->dwAccountID);
#endif
			const auto pIdx(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pIdx->Get() || pIdx->Get()->uiNumRows == 0)
			{
				pack.bCount = 0;
				SendReply(CHARACTER_CHEST_OK);
				return;
			}

			const MYSQL_ROW idxRow = mysql_fetch_row(pIdx->Get()->pSQLResult);
			BYTE count = 0;

			for (int slot = 0; slot < PLAYER_PER_ACCOUNT && count < CHARACTER_CHEST_MAX_LIST; ++slot)
			{
				DWORD pid = 0;
				str_to_number(pid, idxRow[slot]);
				if (pid == 0 || pid == p->dwActorPID)
					continue;

				snprintf(szQuery, sizeof(szQuery),
					"SELECT id, name, job, level, account_id FROM player%s WHERE id=%u LIMIT 1",
					GetTablePostfix(), pid);
				const auto pPlayer(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
				if (!pPlayer->Get() || pPlayer->Get()->uiNumRows == 0)
					continue;

				const MYSQL_ROW row = mysql_fetch_row(pPlayer->Get()->pSQLResult);
				DWORD dbPid = 0;
				DWORD accountId = 0;
				str_to_number(dbPid, row[0]);
				str_to_number(accountId, row[4]);

				if (dbPid != pid)
					continue;
				if (accountId != p->dwAccountID)
					continue;
				if (accountId == CHARACTER_CHEST_PACKED_ACCOUNT_ID)
					continue;

				pack.entries[count].dwPID = pid;
				strlcpy(pack.entries[count].szName, row[1], sizeof(pack.entries[count].szName));
				str_to_number(pack.entries[count].byJob, row[2]);
				str_to_number(pack.entries[count].byLevel, row[3]);
				++count;
			}

			pack.bCount = count;
			SendReply(CHARACTER_CHEST_OK);
		}
		break;

		case CHARACTER_CHEST_OP_PACK:
		{
			if (!CharacterChestValidatePassword(p->dwAccountID, p->szPassword))
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_WRONG_PASSWORD, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_ERR_WRONG_PASSWORD);
				SendReply(CHARACTER_CHEST_ERR_WRONG_PASSWORD);
				return;
			}

			if (p->dwTargetPID == 0 || p->dwTargetPID == p->dwActorPID)
			{
				SendReply(CHARACTER_CHEST_ERR_ACTIVE_CHAR);
				return;
			}

			char szQuery[1024];
			snprintf(szQuery, sizeof(szQuery),
				"SELECT account_id, name FROM player%s WHERE id=%u LIMIT 1",
				GetTablePostfix(), p->dwTargetPID);
			const auto pCheck(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pCheck->Get() || pCheck->Get()->uiNumRows == 0)
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_INVALID_PID, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_ERR_INVALID_PID);
				SendReply(CHARACTER_CHEST_ERR_INVALID_PID);
				return;
			}

			const MYSQL_ROW row = mysql_fetch_row(pCheck->Get()->pSQLResult);
			DWORD accountId = 0;
			str_to_number(accountId, row[0]);
			if (accountId != p->dwAccountID)
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_PACK, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_ERR_NOT_OWNER);
				SendReply(CHARACTER_CHEST_ERR_NOT_OWNER);
				return;
			}

			strlcpy(pack.szPackedName, row[1], sizeof(pack.szPackedName));

			if (accountId == CHARACTER_CHEST_PACKED_ACCOUNT_ID)
			{
				SendReply(CHARACTER_CHEST_ERR_ALREADY_PACKED);
				return;
			}

			if (!CharacterChestIsPidInAccountIndex(GetTablePostfix(), p->dwAccountID, p->dwTargetPID))
			{
				SendReply(CHARACTER_CHEST_ERR_INVALID_PID);
				return;
			}

			if (!CharacterChestBeginTx())
			{
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			snprintf(szQuery, sizeof(szQuery),
				"UPDATE player%s SET account_id=%u WHERE id=%u AND account_id=%u LIMIT 1",
				GetTablePostfix(), CHARACTER_CHEST_PACKED_ACCOUNT_ID, p->dwTargetPID, p->dwAccountID);
			const auto pUpd(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pUpd->Get() || pUpd->Get()->uiAffectedRows != 1)
			{
				CharacterChestRollbackTx();
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			bool bIndexCleared = false;
			for (int slot = 1; slot <= PLAYER_PER_ACCOUNT; ++slot)
			{
				snprintf(szQuery, sizeof(szQuery),
					"UPDATE player_index%s SET pid%d=0 WHERE id=%u AND pid%d=%u LIMIT 1",
					GetTablePostfix(), slot, p->dwAccountID, slot, p->dwTargetPID);
				const auto pIdxUpd(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
				if (pIdxUpd->Get() && pIdxUpd->Get()->uiAffectedRows == 1)
					bIndexCleared = true;
			}

			if (!bIndexCleared)
			{
				CharacterChestRollbackTx();
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			if (!CharacterChestCommitTx())
			{
				CharacterChestRollbackTx();
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			{
				CPlayerTableCache* pkPlayerCache = GetPlayerCache(p->dwTargetPID);
				if (pkPlayerCache)
				{
					pkPlayerCache->Flush();
					m_map_playerCache.erase(p->dwTargetPID);
					delete pkPlayerCache;
				}

				FlushItemCacheSet(p->dwTargetPID);
			}

			CharacterChestLog(CHARACTER_CHEST_LOG_PACK, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_OK);
			SendReply(CHARACTER_CHEST_OK);
		}
		break;

		case CHARACTER_CHEST_OP_UNPACK:
		{
			if (p->dwTargetPID == 0)
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_INVALID_PID, p->dwAccountID, p->dwActorPID, 0, p->dwItemID, CHARACTER_CHEST_ERR_INVALID_PID);
				SendReply(CHARACTER_CHEST_ERR_INVALID_PID);
				return;
			}

			char szQuery[512];
			snprintf(szQuery, sizeof(szQuery),
				"SELECT account_id, name FROM player%s WHERE id=%u LIMIT 1",
				GetTablePostfix(), p->dwTargetPID);
			const auto pCheck(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pCheck->Get() || pCheck->Get()->uiNumRows == 0)
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_INVALID_PID, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_ERR_INVALID_PID);
				SendReply(CHARACTER_CHEST_ERR_INVALID_PID);
				return;
			}

			const MYSQL_ROW playerRow = mysql_fetch_row(pCheck->Get()->pSQLResult);
			DWORD packedAccount = 0;
			str_to_number(packedAccount, playerRow[0]);
			strlcpy(pack.szPackedName, playerRow[1], sizeof(pack.szPackedName));

			if (packedAccount != CHARACTER_CHEST_PACKED_ACCOUNT_ID)
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_INVALID_PID, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_ERR_NOT_PACKED);
				SendReply(CHARACTER_CHEST_ERR_NOT_PACKED);
				return;
			}

#ifdef ENABLE_PLAYER_PER_ACCOUNT5
			snprintf(szQuery, sizeof(szQuery),
				"SELECT pid1, pid2, pid3, pid4, pid5 FROM player_index%s WHERE id=%u",
				GetTablePostfix(), p->dwAccountID);
#else
			snprintf(szQuery, sizeof(szQuery),
				"SELECT pid1, pid2, pid3, pid4 FROM player_index%s WHERE id=%u",
				GetTablePostfix(), p->dwAccountID);
#endif
			const auto pIdx(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pIdx->Get() || pIdx->Get()->uiNumRows == 0)
			{
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			const MYSQL_ROW idxRow = mysql_fetch_row(pIdx->Get()->pSQLResult);
			const int emptySlot = CharacterChestFindEmptySlot(idxRow, 0, PLAYER_PER_ACCOUNT);
			if (emptySlot < 0)
			{
				CharacterChestLog(CHARACTER_CHEST_LOG_NO_SLOT, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_ERR_NO_EMPTY_SLOT);
				SendReply(CHARACTER_CHEST_ERR_NO_EMPTY_SLOT);
				return;
			}

			if (CharacterChestIsPidInAccountIndex(GetTablePostfix(), p->dwAccountID, p->dwTargetPID))
			{
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			if (!CharacterChestBeginTx())
			{
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			snprintf(szQuery, sizeof(szQuery),
				"UPDATE player%s SET account_id=%u WHERE id=%u AND account_id=%u LIMIT 1",
				GetTablePostfix(), p->dwAccountID, p->dwTargetPID, CHARACTER_CHEST_PACKED_ACCOUNT_ID);
			const auto pUpd(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pUpd->Get() || pUpd->Get()->uiAffectedRows != 1)
			{
				CharacterChestRollbackTx();
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			snprintf(szQuery, sizeof(szQuery),
				"UPDATE player_index%s SET pid%d=%u WHERE id=%u AND pid%d=0 LIMIT 1",
				GetTablePostfix(), emptySlot + 1, p->dwTargetPID, p->dwAccountID, emptySlot + 1);
			const auto pIdxUpd(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pIdxUpd->Get() || pIdxUpd->Get()->uiAffectedRows != 1)
			{
				CharacterChestRollbackTx();
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			if (!CharacterChestCommitTx())
			{
				CharacterChestRollbackTx();
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			{
				CPlayerTableCache* pkPlayerCache = GetPlayerCache(p->dwTargetPID);
				if (pkPlayerCache)
				{
					pkPlayerCache->Flush();
					m_map_playerCache.erase(p->dwTargetPID);
					delete pkPlayerCache;
				}

				FlushItemCacheSet(p->dwTargetPID);
			}

			CharacterChestLog(CHARACTER_CHEST_LOG_UNPACK, p->dwAccountID, p->dwActorPID, p->dwTargetPID, p->dwItemID, CHARACTER_CHEST_OK);
			SendReply(CHARACTER_CHEST_OK);
		}
		break;

		case CHARACTER_CHEST_OP_PREVIEW:
		{
			if (p->dwTargetPID == 0)
			{
				SendReply(CHARACTER_CHEST_ERR_INVALID_PID);
				return;
			}

			char szQuery[1024];
			snprintf(szQuery, sizeof(szQuery),
				"SELECT account_id, name FROM player%s WHERE id=%u LIMIT 1",
				GetTablePostfix(), p->dwTargetPID);
			const auto pCheck(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pCheck->Get() || pCheck->Get()->uiNumRows == 0)
			{
				SendReply(CHARACTER_CHEST_ERR_INVALID_PID);
				return;
			}

			const MYSQL_ROW playerRow = mysql_fetch_row(pCheck->Get()->pSQLResult);
			DWORD packedAccount = 0;
			str_to_number(packedAccount, playerRow[0]);
			strlcpy(pack.szPackedName, playerRow[1], sizeof(pack.szPackedName));

			if (packedAccount != CHARACTER_CHEST_PACKED_ACCOUNT_ID)
			{
				SendReply(CHARACTER_CHEST_ERR_NOT_PACKED);
				return;
			}

			snprintf(szQuery, sizeof(szQuery),
				"SELECT "
				"id,name,job,voice,dir,x,y,z,map_index,exit_x,exit_y,exit_map_index,hp,mp,stamina,random_hp,random_sp,playtime,"
				"gold,level,level_step,st,ht,dx,iq,exp,"
				"stat_point,skill_point,sub_skill_point,stat_reset_count,part_base,part_hair,"
				#ifdef ENABLE_ACCE_COSTUME_SYSTEM
				"part_acce, "
				#endif
				"skill_level,quickslot,skill_group,alignment,horse_level,horse_riding,horse_hp,horse_hp_droptime,horse_stamina,"
				"UNIX_TIMESTAMP(NOW())-UNIX_TIMESTAMP(last_play),horse_skill_point"
				#ifdef ENABLE_CHEQUE_SYSTEM
				", cheque "
				#endif
				#ifdef __GEM_SYSTEM__
				", gem "
				#endif
				#ifdef ENABLE_BOT_CONTROL
				",bot_control_time "
				#endif
				#ifdef ENABLE_PLAYER_STATISTICS
				", st_dst_boss_cnt "
				", st_dst_stone_cnt "
				", st_max_boss_dmg "
				", st_max_stone_dmg "
				", st_max_player_dmg "
				", st_ronark_scores "
				#endif
				" FROM player%s WHERE id=%u LIMIT 1",
				GetTablePostfix(), p->dwTargetPID);

			const auto pPlayer(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			if (!pPlayer->Get() || !pPlayer->Get()->pSQLResult || !CreatePlayerTableFromRes(pPlayer->Get()->pSQLResult, &pack.playerTable))
			{
				SendReply(CHARACTER_CHEST_ERR_DB);
				return;
			}

			snprintf(szQuery, sizeof(szQuery),
				"SELECT id,`window`+0,pos,count,vnum,socket0,socket1,socket2,attrtype0,attrvalue0,attrtype1,attrvalue1,attrtype2,attrvalue2,attrtype3,attrvalue3,attrtype4,attrvalue4,attrtype5,attrvalue5,attrtype6,attrvalue6"
#ifdef ENABLE_ITEM_ENCHANT_USE_COUNT
				",enchant_use_count"
#endif
#ifdef ENABLE_ITEM_UPGRADE_OWNER
				",upgrade_owner"
#endif
				" "
				"FROM item%s WHERE owner_id=%u "
				"ORDER BY `window`, pos LIMIT %d",
				GetTablePostfix(), p->dwTargetPID, CHARACTER_CHEST_MAX_PREVIEW_ITEMS);

			const auto pItems(CDBManager::instance().DirectQuery(szQuery, SQL_PLAYER));
			std::vector<TPlayerItem> vec;
			const DWORD itemRows = (pItems->Get() && pItems->Get()->pSQLResult)
				? (DWORD) mysql_num_rows(pItems->Get()->pSQLResult) : 0;
			CreateItemTableFromRes(pItems->Get() ? pItems->Get()->pSQLResult : nullptr, &vec, p->dwTargetPID);
			pack.bCount = (BYTE) (vec.size() > CHARACTER_CHEST_MAX_PREVIEW_ITEMS ? CHARACTER_CHEST_MAX_PREVIEW_ITEMS : vec.size());
			for (BYTE i = 0; i < pack.bCount; ++i)
				pack.items[i] = vec[i];

			CharacterChestFillBiologistStatus(GetTablePostfix(), p->dwTargetPID, pack.abBiologistStatus);

			sys_log(0, "CHARACTER_CHEST DB preview pid %u sql_rows %u items %u bio %u,%u,%u,%u,%u,%u,%u,%u,%u,%u",
				p->dwTargetPID, itemRows, pack.bCount,
				pack.abBiologistStatus[0], pack.abBiologistStatus[1], pack.abBiologistStatus[2],
				pack.abBiologistStatus[3], pack.abBiologistStatus[4], pack.abBiologistStatus[5],
				pack.abBiologistStatus[6], pack.abBiologistStatus[7], pack.abBiologistStatus[8],
				pack.abBiologistStatus[9]);
			SendReply(CHARACTER_CHEST_OK);
		}
		break;

		default:
			SendReply(CHARACTER_CHEST_ERR_DB);
			break;
	}
}

#endif
