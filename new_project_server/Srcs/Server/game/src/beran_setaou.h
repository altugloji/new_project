#pragma once

#ifdef BERAN_SETAOU
#include "../../common/length.h"

#include <cstdint>
#include <vector>

#define BS_CRYSTAL_ROOM_REGEN_FILE "data/dungeon/skia_deliboss.txt"

enum BeranSetaouConf {

	CRYSTAL_ROOM_MAP_IDX = 208,
	BS_MAX_TIME_LIMIT = 10 * 60,
	MAX_METIN_COUNT = 4,

	BERAN_SETAOU_VNUM = 2493,

	STONE_VNUM_START = 8031,
	STONE_VNUM_END = 8034,

	JOIN_TICKET_VNUM = 30179,
	JOIN_TICKET_COUNT = 3,

	BS_LEVEL_LIMIT = 90,
	BS_CLEAR_DELAY_AFTER_FINISH = 60 * 2,

	TIME_LIMIT_NOTICE_INTERVAL = 10 * 60,
	BS_TIMER_TICK_INVERVAL = 10,
	BS_DESTROY_TIME_WHEN_NO_PLAYER = 300,
	DUNGEON_COOLDOWN = 90 * 60,
	DUNGEON_COOLDOWN_W_KILL = 90 * 60,
	BERAN_SETAOU_DUNGEON_ID = 99,
};

enum BSJoinErrCodes : uint8_t {
	BS_JOIN_ERR_NONE,
	BS_JOIN_ERR_BUSY,
	BS_JOIN_ERR_WAITING_FOR_RETURN,
	BS_JOIN_ERR_NO_ITEM,
	BS_JOIN_ERR_HAS_CD,
	BS_JOIN_ERR_HAS_HWID_CD,

	BS_JOIN_OK,
};

enum BSStatus : uint8_t {
	BS_STATE_EMPTY,
	BS_STATE_BUSY,
	BS_STATE_FINISHED,
};

enum BSNotice : uint8_t {
	BS_NOTICE_JOIN,
	BS_NOTICE_UPDATE,
	BS_NOTICE_DRAGON_KILLED,
	BS_NOTICE_CLEAR_DELAY,
	BS_NOTICE_DRAGON_STILL_LIVING,
	BS_NOTICE_DRAGON_RETURN_BACK,
};


enum BSPositions {
	STONE_POS_X = 182,
	STONE_POS_Y = 173,

	STONE_POS_RND_EX = 20,


	PLAYER_JOIN_X = 239,
	PLAYER_JOIN_Y = 173,


	PLAYER_QUIT_X = 1801,
	PLAYER_QUIT_Y = 12204,
};

class CBeranSetaou : public singleton<CBeranSetaou>
{
	public:
		CBeranSetaou();
		~CBeranSetaou();

		void	Initialize();
		void	Destroy();


		void	StartDungeon(LPCHARACTER masterCh, uint32_t roomPasswd, bool isWithParty);
		void	EndDungeon(bool isSuccess);
		void	ClearRoom(bool bAll = false);

		void	StartUpdateEvent(bool bOnlyCancel = false);
		void	StartDestroyEvent(bool bOnlyCancel = false);


		uint8_t	CanJoin(LPCHARACTER joinCh);
		uint8_t	StartRequest(LPCHARACTER joinCh, uint32_t roomPasswd, bool isWithParty = false);

		void	JoinPlayer(LPCHARACTER joinCh);

		void	WarpPlayer(LPCHARACTER warpCh, bool bIsIn);
		void	WarpPlayer(bool bIsIn);
		void	BSNotice(uint8_t noticeType);

		void	OnDead(LPCHARACTER chDead, LPCHARACTER chKiller);
		void	OnDisconnect(LPCHARACTER ch);

		void	SpawnRandomStone();

		bool		IsInCrystalRoom(uint32_t mapIdx) const { return mapIdx == CRYSTAL_ROOM_MAP_IDX; }
		bool		IsCrystalRoomEmpty() const { return m_roomState == BS_STATE_EMPTY; }
		bool		CanStayInCrystalRoom(LPCHARACTER ch) const;
		bool		IsDestroyEventActivated() const { return m_destroyTimer != nullptr; }

		int64_t		GetRemainTime() const;
		uint32_t	GetRoomPassword() const { return m_dwPasswd; }
		uint8_t		GetRoomState() const { return m_roomState; }
		uint8_t		GetCountPlayerInMap();
		const char*	GetMasterName();
		bool		IsHwidCooldown(uint16_t dungeonID, LPCHARACTER ch);



	protected:
		SECTREE_MAP*			m_crystalRoom = nullptr;
		std::vector<uint32_t>	vec_Players;

		LPEVENT		m_updateTimer = nullptr;
		LPEVENT		m_destroyTimer = nullptr;


		uint8_t		m_roomState = BS_STATE_EMPTY;
		uint32_t	m_bsVID = 0;

		uint32_t	m_dwPasswd = 0;
		uint32_t	m_dwMasterPID = 0;
		uint32_t	m_dwStartTime = 0;
};
#endif
