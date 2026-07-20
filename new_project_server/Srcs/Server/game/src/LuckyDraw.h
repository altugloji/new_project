#ifndef _LUCKY_DRAW_
#define _LUCKY_DRAW_

#ifdef ENABLE_LUCKY_DRAW

enum LDConf {
	LD_TIMER_TICK_DELAY = 1,
	LD_JOINERS_FETCH_DELAY = 10,
};

typedef struct SLuckyDrawInfo
{
	uint32_t	joinCount;
	uint32_t	maxJoinCount;	// oyun geneli toplam kapasite
	uint32_t	maxTicketCount;	// oyuncu basina bilet limiti
	uint32_t	endTime;
	uint32_t	neededItemVnum[LD_MAX_REQ_ITEMS];	// [0] eski tek item kolonu, [1..4] v2 kolonlari
	uint32_t	neededItemCount[LD_MAX_REQ_ITEMS];
	uint64_t	neededYang;
}TLuckyDrawInfo;

typedef struct SJoinerListInfo
{
	char		szName[LD_MAX_JOINER_LIST][CHARACTER_NAME_MAX_LEN + 1];
	uint32_t	ticketCount[LD_MAX_JOINER_LIST];
}TJoinerListInfo;

typedef struct SWinnerInfo
{
	uint8_t iPlace[LD_MAX_WINNERS];
	uint32_t playerID[LD_MAX_WINNERS];
	uint32_t ticketCount[LD_MAX_WINNERS];	// kazananin bu cekilisteki bilet sayisi (joiners'tan sayilir)
	char szName[LD_MAX_WINNERS][CHARACTER_NAME_MAX_LEN + 1];
	int32_t iReward1[LD_MAX_WINNERS];
	int32_t iReward2[LD_MAX_WINNERS];
	int32_t iReward3[LD_MAX_WINNERS];
	int32_t iReward4[LD_MAX_WINNERS];
	int32_t iReward5[LD_MAX_WINNERS];
}TWinnerInfo;

class CLuckyDraw : public singleton<CLuckyDraw>
{
	protected:
		LPEVENT updateTimer;
		DWORD	lastFetchTime;
		TLuckyDrawInfo m_luckyDrawInf;
		TWinnerInfo m_winnerInfo;
		TJoinerListInfo m_joinerList;
		bool	m_bIsActivated;
		bool	m_bIsMainHandler;

	public:
		CLuckyDraw();
		void	Initialize();
		void	Destroy();

		// timer EVENTFUNC 0 dondurup kendini yok ederken sarkan pointer kalmasin
		void	ClearUpdateTimer() { updateTimer = NULL; }

		void	EndLuckyDraw(bool determineWinners = false);
		void	RequestLuckyDraw(bool bStart = false);
		void	RequestLuckyDrawJoiners(bool bBroadcast = false);
		void	RequestWinnerInfo();

		void	ClientPacket(LPCHARACTER ch);
		void	SendP2PPacket(DWORD arg1 = 0, DWORD arg2 = 0, DWORD arg3 = 0);

		void	StartLuckyDraw(DWORD maxTime, bool fromP2P = true);

		uint32_t GetJoinCountByPID(DWORD playerID);
		bool	JoinLuckyDraw(LPCHARACTER pCh);
		bool	RequestReward(LPCHARACTER pCh);
		bool	IsLuckyDrawActivated();

};

#endif // ENABLE_LUCKY_DRAW

#endif
