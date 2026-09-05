#include "stdafx.h"

#ifdef ENABLE_PLAYER_STATISTICS
#include "statistics_rank.h"
#include "desc.h"
#include "char.h"
#include "config.h"
#include "db.h"
#include "utils.h"

CStatisticsRanking::CStatisticsRanking()
{
	Initialize();
}

CStatisticsRanking::~CStatisticsRanking()
{
	Destroy();
}

void CStatisticsRanking::Initialize()
{
	memset(&nextFetchTime, 0, sizeof(nextFetchTime));
	memset(&szFetchQuery, 0, sizeof(szFetchQuery));
	memset(&szFetchTimesStr, 0, sizeof(szFetchTimesStr));
	map_Rankings.clear();

	// "[%%": sorgu DirectQuery'nin printf katmanindan gecerken "[%" olur;
	// boylece '[' ile baslayan (GM etiketli) isimler siralamaya girmez.
	const char* szStr = "[%%";

	snprintf(szFetchQuery[RANKING_LEVEL], sizeof(szFetchQuery[RANKING_LEVEL]), "SELECT name, level,job, NOW() FROM player.player WHERE level > 0 AND name NOT LIKE '%s' ORDER BY level DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_MAX_STONE_DMG], sizeof(szFetchQuery[RANKING_MAX_STONE_DMG]), "SELECT name, st_max_stone_dmg,job, NOW() FROM player.player WHERE st_max_stone_dmg > 0 AND name NOT LIKE '%s' ORDER BY st_max_stone_dmg DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_MAX_BOSS_DMG], sizeof(szFetchQuery[RANKING_MAX_BOSS_DMG]), "SELECT name, st_max_boss_dmg,job, NOW() FROM player.player WHERE st_max_boss_dmg > 0 AND name NOT LIKE '%s' ORDER BY st_max_boss_dmg DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_MAX_PLAYER_DMG], sizeof(szFetchQuery[RANKING_MAX_PLAYER_DMG]), "SELECT name, st_max_player_dmg,job, NOW() FROM player.player WHERE st_max_player_dmg > 0 AND name NOT LIKE '%s' ORDER BY st_max_player_dmg DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_DESTROYED_BOSS_COUNT], sizeof(szFetchQuery[RANKING_DESTROYED_BOSS_COUNT]), "SELECT name, st_dst_boss_cnt,job, NOW() FROM player.player WHERE st_dst_boss_cnt > 0 AND name NOT LIKE '%s' ORDER BY st_dst_boss_cnt DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_DESTROYED_STONE_COUNT], sizeof(szFetchQuery[RANKING_DESTROYED_STONE_COUNT]), "SELECT name, st_dst_stone_cnt,job, NOW() FROM player.player WHERE st_dst_stone_cnt > 0 AND name NOT LIKE '%s' ORDER BY st_dst_stone_cnt DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_ALIGN], sizeof(szFetchQuery[RANKING_ALIGN]), "SELECT name, (alignment*0.10),job, NOW() FROM player.player WHERE alignment > 0 AND name NOT LIKE '%s' ORDER BY alignment DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);
	snprintf(szFetchQuery[RANKING_PLAYTIME], sizeof(szFetchQuery[RANKING_PLAYTIME]), "SELECT name, playtime,job, NOW() FROM player.player WHERE playtime > 0 AND name NOT LIKE '%s' ORDER BY playtime DESC LIMIT 0, %d;", szStr, RANKING_MAX_PLAYER_COUNT);

	// Isimli boss siralamalari: skorlar player.boss_kill_ranking tablosundan gelir
	for (int i = RANKING_BOSS_LUSIFER; i <= RANKING_BOSS_EJDER; ++i)
	{
		const int iBossGroup = i - RANKING_BOSS_LUSIFER;
		snprintf(szFetchQuery[i], sizeof(szFetchQuery[i]),
			"SELECT p.name, b.kill_count, p.job, NOW() FROM player.boss_kill_ranking b "
			"JOIN player.player p ON p.id = b.pid "
			"WHERE b.boss_group = %d AND b.kill_count > 0 AND p.name NOT LIKE '%s' "
			"ORDER BY b.kill_count DESC LIMIT 0, %d;",
			iBossGroup, szStr, RANKING_MAX_PLAYER_COUNT);
	}
}

void CStatisticsRanking::Destroy()
{
	memset(&nextFetchTime, 0, sizeof(nextFetchTime));
	memset(&szFetchQuery, 0, sizeof(szFetchQuery));
	memset(&szFetchTimesStr, 0, sizeof(szFetchTimesStr));
	map_Rankings.clear();
}

void CStatisticsRanking::CheckIsTimedOutOrEmpty(BYTE rankType)
{
	auto iter = map_Rankings.find(rankType);

	if (nextFetchTime[rankType] <= get_global_time() || iter == map_Rankings.end())
		FetchRankingList(rankType);
}

void CStatisticsRanking::RequestRankingList(BYTE rankType, CHARACTER * ch)
{
	if (NULL == ch)
		return;

	if (rankType >= RANKING_MAX)
		return;

	CheckIsTimedOutOrEmpty(rankType);

	auto iter = map_Rankings.find(rankType);

	if (iter != map_Rankings.end())
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "RankingProcess start");

		for (auto it = iter->second.begin(); it != iter->second.end(); ++it)
			ch->ChatPacket(CHAT_TYPE_COMMAND, "RankingData %d|%d|%d|%lld|%s|%s", rankType, it->bOrder, it->bJob, it->llScore, it->szPlayerName, szFetchTimesStr[rankType]);

		ch->ChatPacket(CHAT_TYPE_COMMAND, "RankingProcess end");
	}
	else
		ch->ChatPacket(CHAT_TYPE_COMMAND, "RankingProcess null");
}

void CStatisticsRanking::FetchRankingList(BYTE rankType)
{
	if (rankType >= RANKING_MAX)
		return;

	// Sonuc bos olsa bile cache suresini isle: aksi halde her istek
	// ana thread'de DirectQuery calistirir (spam korumasi).
	nextFetchTime[rankType] = get_global_time() + CACHE_TIME;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(szFetchQuery[rankType]));

	if (pMsg->Get()->uiNumRows == 0)
		return;

	MYSQL_ROW mRow;
	std::vector<TRankingInfo> playerList;
	BYTE bOrder = 0;

	while (NULL != (mRow = mysql_fetch_row(pMsg->Get()->pSQLResult)))
	{
		bOrder++;
		BYTE cur = 0;

		TRankingInfo addToList;
		addToList.bOrder = bOrder;
		snprintf(addToList.szPlayerName, sizeof(addToList.szPlayerName), "%s", mRow[cur++]);
		str_to_number(addToList.llScore, mRow[cur++]);
		str_to_number(addToList.bJob, mRow[cur++]);

		if (bOrder == 1)
			snprintf(szFetchTimesStr[rankType], sizeof(szFetchTimesStr[rankType]), "%s", mRow[cur++]);

		playerList.push_back(addToList);
	}

	if (playerList.size())
	{
		map_Rankings.erase(rankType);
		map_Rankings.insert(std::make_pair(rankType, playerList));
	}
}

int CStatisticsRanking::GetBossGroupByVnum(DWORD dwVnum)
{
	switch (dwVnum)
	{
		case 1093:	// Lusifer
			return 0;
		case 2598:	// Azrail
			return 1;
		case 2491:	// Generaller
		case 2492:
		case 2494:
		case 2495:
			return 2;
		case 1192:	// Cadi
			return 3;
		case 2493:	// Ejder (BeranSetaou)
			return 4;
	}

	return -1;
}

void CStatisticsRanking::UpdateBossKillCount(DWORD dwPID, int iBossGroup)
{
	if (dwPID == 0)
		return;

	if (iBossGroup < 0 || iBossGroup > (RANKING_BOSS_EJDER - RANKING_BOSS_LUSIFER))
		return;

	DBManager::instance().Query(
		"INSERT INTO player.boss_kill_ranking (pid, boss_group, kill_count) "
		"VALUES(%u, %d, 1) ON DUPLICATE KEY UPDATE kill_count = kill_count + 1",
		dwPID, iBossGroup);
}
#endif
