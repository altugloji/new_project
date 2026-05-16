#include "stdafx.h"
#include "../../common/CommonDefines.h"

#ifdef ENABLE_CHARACTER_CHEST

#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "desc_client.h"
#include "item.h"
#include "item_manager.h"
#include "packet.h"
#include "protocol.h"
#include "db.h"
#include "log.h"
#include "../../common/character_chest.h"
#include "char_character_chest.h"
#include <stddef.h>
#include <set>

namespace character_chest
{
	static std::set<DWORD> s_busyAccountIds;

	static void SetAccountBusy(DWORD accountId, bool busy)
	{
		if (accountId == 0)
			return;

		if (busy)
			s_busyAccountIds.insert(accountId);
		else
			s_busyAccountIds.erase(accountId);
	}

	static bool IsAccountBusy(DWORD accountId)
	{
		return s_busyAccountIds.find(accountId) != s_busyAccountIds.end();
	}

	static bool CanUseChestNow(CHARACTER* ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc())
			return false;

		if (ch->IsDead() || ch->IsStun())
			return false;

		if (!ch->CanHandleItem())
			return false;

		if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->GetShop() || ch->IsOpenSafebox() || ch->IsCubeOpen())
			return false;

		return true;
	}

	static void NotifyCannotUse(CHARACTER* ch)
	{
		if (!ch)
			return;

		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CANT_DO_THIS_BECAUSE_OTHER_WINDOW_OPEN"));
	}

	static void NotifyBusy(CHARACTER* ch)
	{
		if (!ch)
			return;

		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_FAILED"));
	}

	static bool IsAllowedMapForMutation(CHARACTER* ch)
	{
		if (!ch)
			return false;

		return ch->GetMapIndex() == CHARACTER_CHEST_ALLOWED_MAP_INDEX;
	}

	static void NotifyWrongMap(CHARACTER* ch)
	{
		if (!ch)
			return;

		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_WRONG_MAP"));
	}

	static void KickActor(CHARACTER* ch)
	{
		if (ch && ch->GetDesc())
			ch->Disconnect("CHARACTER_CHEST");
	}

	static void SyncAccountTableRemoveCharacter(DESC* d, DWORD pid)
	{
		if (!d)
			return;

		TAccountTable& r = d->GetAccountTable();
		for (int i = 0; i < PLAYER_PER_ACCOUNT; ++i)
		{
			if (r.players[i].dwID != pid)
				continue;

			memset(&r.players[i], 0, sizeof(TSimplePlayer));

			if (d->IsPhase(PHASE_SELECT))
			{
				d->BufferedPacket(encode_byte(HEADER_GC_CHARACTER_DELETE_SUCCESS), 1);
				d->Packet(encode_byte(i), 1);
			}
			return;
		}
	}

	static void SyncAccountTableAddCharacter(DESC* d, DWORD pid, const char* name)
	{
		if (!d || !name || !*name)
			return;

		TAccountTable& r = d->GetAccountTable();
		for (int i = 0; i < PLAYER_PER_ACCOUNT; ++i)
		{
			if (r.players[i].dwID == pid)
				return;
		}

		for (int i = 0; i < PLAYER_PER_ACCOUNT; ++i)
		{
			if (r.players[i].dwID != 0)
				continue;

			r.players[i].dwID = pid;
			strlcpy(r.players[i].szName, name, sizeof(r.players[i].szName));
			return;
		}
	}

	static const size_t s_gcBaseSize = offsetof(TPacketGCCharacterChest, entries);

	static void FillPreviewPlayer(TCharacterChestPreviewPlayer& out, const TPlayerTable& tab)
	{
		memset(&out, 0, sizeof(out));
		strlcpy(out.szName, tab.name, sizeof(out.szName));
		out.bJob = static_cast<BYTE>(tab.job);
		out.bLevel = tab.level;
		out.sST = tab.st;
		out.sHT = tab.ht;
		out.sDX = tab.dx;
		out.sIQ = tab.iq;
		out.dwExp = tab.exp;
		out.iGold = tab.gold;
		out.iPlaytime = tab.playtime;
		out.bPartBase = tab.part_base;
		for (int i = 0; i < CHARACTER_CHEST_PREVIEW_PART_COUNT && i < PART_MAX_NUM; ++i)
			out.adwParts[i] = tab.parts[i];
		out.bSkillGroup = tab.skill_group;
#ifdef ENABLE_CHEQUE_SYSTEM
		out.iCheque = tab.cheque;
#else
		out.iCheque = 0;
#endif
#ifdef __GEM_SYSTEM__
		out.iGem = tab.gem;
#else
		out.iGem = 0;
#endif
	}

	static void FillPreviewItem(TCharacterChestPreviewItem& out, const TPlayerItem& item)
	{
		memset(&out, 0, sizeof(out));
		out.bWindow = item.window;
		out.wPos = item.pos;
		out.dwVnum = item.vnum;
		out.dwCount = item.count;
		for (int i = 0; i < CHARACTER_CHEST_PREVIEW_SOCKET_NUM; ++i)
			out.alSockets[i] = item.alSockets[i];
		for (int i = 0; i < CHARACTER_CHEST_PREVIEW_ATTR_NUM; ++i)
		{
			out.aAttrType[i] = item.aAttr[i].bType;
			out.aAttrValue[i] = item.aAttr[i].sValue;
		}
	}

	static void SendGCPreviewPacket(DESC* d, const TPacketDGCharacterChest& pack)
	{
		BYTE buf[CHARACTER_CHEST_GC_MAX_SIZE];
		memset(buf, 0, sizeof(buf));

		TPacketGCCharacterChest* gc = reinterpret_cast<TPacketGCCharacterChest*>(buf);
		gc->bHeader = HEADER_GC_CHARACTER_CHEST;
		gc->bOp = pack.bOp;
		gc->bResult = pack.bResult;
		gc->dwTargetPID = pack.dwTargetPID;
		gc->wItemCell = (pack.dwItemID == 0)
			? static_cast<WORD>(CHARACTER_CHEST_PREVIEW_READONLY_CELL)
			: pack.wItemCell;
		gc->bCount = pack.bCount;
		strlcpy(gc->szPackedName, pack.szPackedName, sizeof(gc->szPackedName));

		size_t offset = s_gcBaseSize;

		if (offset + CHARACTER_CHEST_PREVIEW_PLAYER_WIRE_SIZE > CHARACTER_CHEST_GC_MAX_SIZE)
			return;

		TCharacterChestPreviewPlayer playerData;
		FillPreviewPlayer(playerData, pack.playerTable);
		playerData.bSkillCount = 0;
		memcpy(buf + offset, &playerData, CHARACTER_CHEST_PREVIEW_PLAYER_WIRE_SIZE);
		const size_t playerOffset = offset;
		offset += CHARACTER_CHEST_PREVIEW_PLAYER_WIRE_SIZE;

		BYTE skillCount = 0;
		for (WORD i = 0; i < SKILL_MAX_NUM && skillCount < CHARACTER_CHEST_MAX_PREVIEW_SKILLS; ++i)
		{
			if (pack.playerTable.skills[i].bLevel == 0)
				continue;

			if (offset + sizeof(TCharacterChestPreviewSkill) > CHARACTER_CHEST_GC_MAX_SIZE)
				break;

			TCharacterChestPreviewSkill* skill = reinterpret_cast<TCharacterChestPreviewSkill*>(buf + offset);
			skill->wVnum = i;
			skill->bMasterType = pack.playerTable.skills[i].bMasterType;
			skill->bLevel = pack.playerTable.skills[i].bLevel;
			offset += sizeof(TCharacterChestPreviewSkill);
			++skillCount;
		}
		buf[playerOffset + offsetof(TCharacterChestPreviewPlayer, bSkillCount)] = skillCount;

		const BYTE itemCount = (pack.bCount > CHARACTER_CHEST_MAX_PREVIEW_ITEMS) ? CHARACTER_CHEST_MAX_PREVIEW_ITEMS : pack.bCount;
		gc->bCount = itemCount;

		for (BYTE i = 0; i < itemCount; ++i)
		{
			if (offset + sizeof(TCharacterChestPreviewItem) > CHARACTER_CHEST_GC_MAX_SIZE)
			{
				gc->bCount = i;
				break;
			}

			TCharacterChestPreviewItem* item = reinterpret_cast<TCharacterChestPreviewItem*>(buf + offset);
			FillPreviewItem(*item, pack.items[i]);
			offset += sizeof(TCharacterChestPreviewItem);
		}

		if (offset + CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT <= CHARACTER_CHEST_GC_MAX_SIZE)
		{
			memcpy(buf + offset, pack.abBiologistStatus, CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT);
			offset += CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT;
		}

		gc->wSize = static_cast<WORD>(offset);

		sys_log(0, "CHARACTER_CHEST GC preview pid %u size %u skills %u items %u player_wire %u bio %u,%u,%u,%u,%u,%u,%u,%u,%u,%u",
			pack.dwTargetPID, gc->wSize, skillCount, gc->bCount, (DWORD) CHARACTER_CHEST_PREVIEW_PLAYER_WIRE_SIZE,
			pack.abBiologistStatus[0], pack.abBiologistStatus[1], pack.abBiologistStatus[2],
			pack.abBiologistStatus[3], pack.abBiologistStatus[4], pack.abBiologistStatus[5],
			pack.abBiologistStatus[6], pack.abBiologistStatus[7], pack.abBiologistStatus[8],
			pack.abBiologistStatus[9]);

		d->Packet(buf, gc->wSize);
	}

	static void SendGCPacket(DESC* d, const TPacketDGCharacterChest& pack)
	{
		if (!d)
			return;

		if (pack.bOp == CHARACTER_CHEST_OP_PREVIEW && pack.bResult == CHARACTER_CHEST_OK)
		{
			SendGCPreviewPacket(d, pack);
			return;
		}

		TPacketGCCharacterChest gc;
		memset(&gc, 0, sizeof(gc));
		gc.bHeader = HEADER_GC_CHARACTER_CHEST;
		gc.bOp = pack.bOp;
		gc.bResult = pack.bResult;
		gc.dwTargetPID = pack.dwTargetPID;
		gc.wItemCell = pack.wItemCell;
		strlcpy(gc.szPackedName, pack.szPackedName, sizeof(gc.szPackedName));

		if (pack.bOp == CHARACTER_CHEST_OP_LIST)
		{
			gc.bCount = pack.bCount;
			for (BYTE i = 0; i < pack.bCount && i < CHARACTER_CHEST_MAX_LIST; ++i)
				gc.entries[i] = pack.entries[i];
			gc.wSize = static_cast<WORD>(s_gcBaseSize + gc.bCount * sizeof(TCharacterChestEntry));
		}
		else
		{
			gc.bCount = 0;
			gc.wSize = static_cast<WORD>(s_gcBaseSize);
		}

		sys_log(0, "CHARACTER_CHEST GC send op %u result %u count %u size %u",
			gc.bOp, gc.bResult, gc.bCount, gc.wSize);

		d->Packet(&gc, gc.wSize);
	}

	void KickPID(DWORD pid)
	{
		LPCHARACTER tch = CHARACTER_MANAGER::instance().FindByPID(pid);
		if (tch && tch->GetDesc())
			tch->Disconnect("CHARACTER_CHEST");
	}

	static void SendGD(CHARACTER* ch, BYTE op, DWORD targetPid, CItem* item, const char* password)
	{
		if (!ch || !ch->GetDesc())
			return;

		TPacketGDCharacterChest p;
		memset(&p, 0, sizeof(p));
		p.bOp = op;
		p.dwAccountID = ch->GetDesc()->GetAccountTable().id;
		p.dwActorPID = ch->GetPlayerID();
		p.dwTargetPID = targetPid;
		if (item)
		{
			p.dwItemID = item->GetID();
			p.wItemCell = item->GetCell();
		}
		if (password)
			strlcpy(p.szPassword, password, sizeof(p.szPassword));

		db_clientdesc->DBPacket(HEADER_GD_CHARACTER_CHEST, ch->GetDesc()->GetHandle(), &p, sizeof(p));
	}

	bool UseChestItem(CHARACTER* ch, CItem* item)
	{
		if (!ch || !item)
			return false;

		if (!CanUseChestNow(ch))
		{
			NotifyCannotUse(ch);
			return false;
		}

		if (item->GetVnum() != CHARACTER_CHEST_ITEM_VNUM)
			return false;

		sys_log(0, "CHARACTER_CHEST use item %u cell %u socket0 %u",
			item->GetID(), item->GetCell(), item->GetSocket(CHARACTER_CHEST_SOCKET_PID));

		const DWORD packedPid = item->GetSocket(CHARACTER_CHEST_SOCKET_PID);
		if (packedPid != 0)
		{
			SendPreview(ch, packedPid, item);
			return true;
		}

		SendList(ch, item);
		return true;
	}

	void SendList(CHARACTER* ch, CItem* item)
	{
		SendGD(ch, CHARACTER_CHEST_OP_LIST, 0, item, nullptr);
	}

	void SendPack(CHARACTER* ch, DWORD targetPid, const char* password, CItem* item)
	{
		if (!ch || !password || !item)
			return;

		if (!IsAllowedMapForMutation(ch))
		{
			NotifyWrongMap(ch);
			return;
		}

		if (!CanUseChestNow(ch))
		{
			NotifyCannotUse(ch);
			return;
		}

		const DWORD accountId = ch->GetDesc()->GetAccountTable().id;
		if (IsAccountBusy(accountId))
		{
			NotifyBusy(ch);
			return;
		}

		if (targetPid == ch->GetPlayerID())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_CANNOT_PACK_ACTIVE"));
			return;
		}

		if (item->GetSocket(CHARACTER_CHEST_SOCKET_PID) != 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_ALREADY_USED"));
			return;
		}

		const std::string playerCode(ch->GetDesc()->GetAccountTable().social_id);
		if (playerCode.size() < 7 || playerCode.compare(playerCode.size() - 7, 7, password) != 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_WRONG_PASSWORD"));
			return;
		}

		if (LPCHARACTER target = CHARACTER_MANAGER::instance().FindByPID(targetPid))
		{
			target->FlushDelayedSaveItem();
			target->Save();
			if (target->GetDesc())
				target->Disconnect("CHARACTER_CHEST_PACK");
		}

		SetAccountBusy(accountId, true);
		SendGD(ch, CHARACTER_CHEST_OP_PACK, targetPid, item, password);
	}

	void SendUnpack(CHARACTER* ch, CItem* item)
	{
		if (!ch || !item)
			return;

		if (!IsAllowedMapForMutation(ch))
		{
			NotifyWrongMap(ch);
			return;
		}

		if (!CanUseChestNow(ch))
		{
			NotifyCannotUse(ch);
			return;
		}

		const DWORD accountId = ch->GetDesc()->GetAccountTable().id;
		if (IsAccountBusy(accountId))
		{
			NotifyBusy(ch);
			return;
		}

		const DWORD packedPid = item->GetSocket(CHARACTER_CHEST_SOCKET_PID);
		if (packedPid == 0 || item->GetSocket(CHARACTER_CHEST_SOCKET_SEAL) == 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_INVALID"));
			return;
		}

		SetAccountBusy(accountId, true);
		SendGD(ch, CHARACTER_CHEST_OP_UNPACK, packedPid, item, nullptr);
	}

	void SendPreview(CHARACTER* ch, DWORD packedPid, CItem* item)
	{
		SendGD(ch, CHARACTER_CHEST_OP_PREVIEW, packedPid, item, nullptr);
	}

	void SendRemotePreview(CHARACTER* ch, DWORD packedPid)
	{
		if (!ch || !ch->IsPC() || packedPid == 0)
			return;

		SendGD(ch, CHARACTER_CHEST_OP_PREVIEW, packedPid, nullptr, nullptr);
	}

	void OnDBPacket(DESC* d, const TPacketDGCharacterChest* pack)
	{
		if (!d)
			return;

		LPCHARACTER ch = d->GetCharacter();
		const DWORD accountId = d->GetAccountTable().id;
		const bool bMutationOp = (pack->bOp == CHARACTER_CHEST_OP_PACK || pack->bOp == CHARACTER_CHEST_OP_UNPACK);

		if (bMutationOp)
			SetAccountBusy(accountId, false);

		if (!ch)
			return;

		switch (pack->bResult)
		{
			case CHARACTER_CHEST_OK:
				break;
			case CHARACTER_CHEST_ERR_WRONG_PASSWORD:
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_WRONG_PASSWORD"));
				SendGCPacket(d, *pack);
				return;
			case CHARACTER_CHEST_ERR_NO_EMPTY_SLOT:
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_NO_SLOT"));
				SendGCPacket(d, *pack);
				return;
			case CHARACTER_CHEST_ERR_NOT_PACKED:
			case CHARACTER_CHEST_ERR_INVALID_PID:
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_INVALID"));
				SendGCPacket(d, *pack);
				return;
			default:
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_FAILED"));
				SendGCPacket(d, *pack);
				return;
		}

		if (pack->bOp == CHARACTER_CHEST_OP_PACK && pack->bResult == CHARACTER_CHEST_OK)
		{
			LPITEM item = ch->GetInventoryItem(pack->wItemCell);
			if (!item || item->GetID() != pack->dwItemID || item->GetVnum() != CHARACTER_CHEST_ITEM_VNUM)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_FAILED"));
				SendGCPacket(d, *pack);
				KickActor(ch);
				return;
			}

			if (item->GetSocket(CHARACTER_CHEST_SOCKET_PID) != 0 || item->GetSocket(CHARACTER_CHEST_SOCKET_SEAL) != 0)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_ALREADY_USED"));
				SendGCPacket(d, *pack);
				KickActor(ch);
				return;
			}

			KickPID(pack->dwTargetPID);
			SyncAccountTableRemoveCharacter(d, pack->dwTargetPID);

			item->SetSocket(CHARACTER_CHEST_SOCKET_PID, pack->dwTargetPID);
			item->SetSocket(CHARACTER_CHEST_SOCKET_SEAL, 1);
			item->UpdatePacket();
			ITEM_MANAGER::instance().FlushDelayedSave(item);
			ITEM_MANAGER::instance().SaveSingleItem(item);

			LogManager::instance().ItemLog(ch, item, "CHARACTER_CHEST_PACK", pack->szPackedName);
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_PACK_OK"));
			SendGCPacket(d, *pack);
			KickActor(ch);
			return;
		}
		else if (pack->bOp == CHARACTER_CHEST_OP_UNPACK && pack->bResult == CHARACTER_CHEST_OK)
		{
			LPITEM item = ch->GetInventoryItem(pack->wItemCell);
			if (!item || item->GetID() != pack->dwItemID || item->GetVnum() != CHARACTER_CHEST_ITEM_VNUM)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_FAILED"));
				SendGCPacket(d, *pack);
				KickActor(ch);
				return;
			}

			if (item->GetSocket(CHARACTER_CHEST_SOCKET_PID) != pack->dwTargetPID || item->GetSocket(CHARACTER_CHEST_SOCKET_SEAL) == 0)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_INVALID"));
				SendGCPacket(d, *pack);
				KickActor(ch);
				return;
			}

			KickPID(pack->dwTargetPID);
			SyncAccountTableAddCharacter(d, pack->dwTargetPID, pack->szPackedName);

			// SetCount(0) already removes and destroys the item via RemoveFromCharacter.
			item->SetCount(item->GetCount() - 1);

			LogManager::instance().CharLog(ch, pack->dwTargetPID, "CHARACTER_CHEST_UNPACK", pack->szPackedName);
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CHARACTER_CHEST_UNPACK_OK"));
			SendGCPacket(d, *pack);
			KickActor(ch);
			return;
		}

		SendGCPacket(d, *pack);
	}

	void RefreshSelectCharacterList(DESC* d)
	{
		if (!d || !d->IsPhase(PHASE_SELECT))
			return;

		d->SendLoginSuccessPacket();
	}
}

#endif
