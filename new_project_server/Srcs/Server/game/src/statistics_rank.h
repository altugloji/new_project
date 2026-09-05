#pragma once

// Oyun ici siralama sistemi (ENABLE_PLAYER_STATISTICS)
// Eski_A_Src'den porte edildi; KYGN_NEW_LEAGUE_SYSTEM dali cikarildi.
#ifdef ENABLE_PLAYER_STATISTICS
#include "../../common/length.h"
#include <map>
#include <vector>

class CHARACTER;

enum RankingTypes
{
	RANKING_LEVEL,
	RANKING_MAX_STONE_DMG,
	RANKING_MAX_BOSS_DMG,
	RANKING_MAX_PLAYER_DMG,
	RANKING_DESTROYED_BOSS_COUNT,
	RANKING_DESTROYED_STONE_COUNT,
	RANKING_ALIGN,
	RANKING_PLAYTIME,
	// Isimli boss kesim siralamalari (player.boss_kill_ranking tablosu;
	// boss_group = tip - RANKING_BOSS_LUSIFER)
	RANKING_BOSS_LUSIFER,
	RANKING_BOSS_AZRAIL,
	RANKING_BOSS_GENERAL,
	RANKING_BOSS_CADI,
	RANKING_BOSS_EJDER,
	RANKING_MAX
};

enum RankingConf
{
	RANKING_MAX_PLAYER_COUNT = 10,
	CACHE_TIME = 60 * 60,
	RQUERY_MAX_LEN = 512,
	TIME_STR_MAX_LEN = 56,
};

typedef struct SRankingInfo
{
	BYTE		bOrder;
	char		szPlayerName[CHARACTER_NAME_MAX_LEN + 1];
	long long	llScore;
	BYTE		bJob;
} TRankingInfo;

class CStatisticsRanking : public singleton<CStatisticsRanking>
{
	public:
		CStatisticsRanking();
		virtual ~CStatisticsRanking();

		void Initialize();
		void Destroy();

		void CheckIsTimedOutOrEmpty(BYTE rankType);
		void RequestRankingList(BYTE rankType, CHARACTER * ch);
		void FetchRankingList(BYTE rankType);

		// Isimli boss vnum -> boss_group (0..4); listede yoksa -1
		static int GetBossGroupByVnum(DWORD dwVnum);
		// Asenkron INSERT..ON DUPLICATE KEY UPDATE (oyun thread'ini bloklamaz)
		void UpdateBossKillCount(DWORD dwPID, int iBossGroup);

	protected:
		std::map<BYTE, std::vector<TRankingInfo> > map_Rankings;
		DWORD nextFetchTime[RANKING_MAX];
		char szFetchQuery[RANKING_MAX][RQUERY_MAX_LEN];
		char szFetchTimesStr[RANKING_MAX][TIME_STR_MAX_LEN];
};
#endif
