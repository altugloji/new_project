#ifndef __CLASS_ARENA_MANAGER__
#define __CLASS_ARENA_MANAGER__

#include <lua.h>

enum MEMBER_IDENTITY
{
	MEMBER_NO,
	MEMBER_DUELIST,
	MEMBER_OBSERVER,

	MEMBER_MAX
};

// #ifdef ENABLE_NEWSTUFF
extern bool IsAllowedPotionOnPVP(DWORD dwVnum);
extern bool IsLimitedPotionOnPVP(DWORD dwVnum);
extern bool IsLimitedPotion(DWORD dwVnum);
// #endif

class CArena
{
	friend class CArenaMap;

	private :
	DWORD m_dwPIDA;
	DWORD m_dwPIDB;

	LPEVENT m_pEvent;
	LPEVENT m_pTimeOutEvent;

	PIXEL_POSITION m_StartPointA;
	PIXEL_POSITION m_StartPointB;
	PIXEL_POSITION m_ObserverPoint;

	DWORD m_dwSetCount;
	DWORD m_dwSetPointOfA;
	DWORD m_dwSetPointOfB;

	std::map<DWORD, LPCHARACTER> m_mapObserver;

	protected :
	CArena(WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y);

	bool StartDuel(LPCHARACTER pCharFrom, LPCHARACTER pCharTo, int nSetPoint, int nMinute = 5);

	bool IsEmpty() const	{ return ((m_dwPIDA==0) && (m_dwPIDB==0)); }
	bool IsMember(DWORD dwPID) const	{ return ((m_dwPIDA==dwPID) || (m_dwPIDB==dwPID)); }

	bool CheckArea(WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y) const;
	void Clear();

	bool CanAttack(DWORD dwPIDA, DWORD dwPIDB) const;
	bool OnDead(DWORD dwPIDA, DWORD dwPIDB);

	bool IsObserver(DWORD pid);
	bool IsMyObserver(WORD ObserverX, WORD ObserverY) const;
	bool AddObserver(LPCHARACTER pChar);
	bool RegisterObserverPtr(LPCHARACTER pChar);

	public :
	DWORD GetPlayerAPID() const { return m_dwPIDA; }
	DWORD GetPlayerBPID() const { return m_dwPIDB; }

	LPCHARACTER GetPlayerA() const { return CHARACTER_MANAGER::instance().FindByPID(m_dwPIDA); }
	LPCHARACTER GetPlayerB() const { return CHARACTER_MANAGER::instance().FindByPID(m_dwPIDB); }

	PIXEL_POSITION GetStartPointA() const { return m_StartPointA; }
	PIXEL_POSITION GetStartPointB() const { return m_StartPointB; }

	PIXEL_POSITION GetObserverPoint() const { return m_ObserverPoint; }

	void EndDuel();
#ifdef ENABLE_WS_TOURNAMENT
	bool WSPauseIfMember(DWORD dwPID);					// kopma: eventleri durdur, arena canli kalsin
	bool WSResumeDuelIfMember(DWORD dwPID, int iRemainSec);	// donus: anahtar tazele + mac saatini kalanla kur
	bool WSSendDuelStartIfMember(DWORD dwPID);	// relog: duello anahtarlarini (taze VID) iki tarafa yeniden gonder
#endif
	void ClearEvent() { m_pEvent = nullptr; }
	void OnDisconnect(DWORD pid);
	void RemoveObserver(DWORD pid);

	void SendPacketToObserver(const void * c_pvData, int iSize) const;
	void SendChatPacketToObserver(BYTE type, const char * format, ...) const;

#ifdef ENABLE_WS_TOURNAMENT
	DWORD GetSetPointA() const { return m_dwSetPointOfA; }
	DWORD GetSetPointB() const { return m_dwSetPointOfB; }

	// kopma sonrasi yeniden kurulan turnuva macinda korunan set skorunu geri yukle
	// (pid bu arenanin uyesiyse uygular ve true doner - IsMember protected oldugu icin kontrol burada)
	bool WSRestoreSetPoints(DWORD dwPID, DWORD dwOwnPoints, DWORD dwOppPoints)
	{
		if (m_dwPIDA == dwPID)
		{
			m_dwSetPointOfA = dwOwnPoints;
			m_dwSetPointOfB = dwOppPoints;
			return true;
		}
		if (m_dwPIDB == dwPID)
		{
			m_dwSetPointOfB = dwOwnPoints;
			m_dwSetPointOfA = dwOppPoints;
			return true;
		}
		return false;
	}
#endif
};

class CArenaMap
{
	friend class CArenaManager;

	private :
	DWORD m_dwMapIndex;
	std::list<CArena*> m_listArena;

	protected :
	void Destroy();

	bool AddArena(DWORD mapIdx, WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y);
	void SendArenaMapListTo(LPCHARACTER pChar, DWORD dwMapIndex);

	bool StartDuel(LPCHARACTER pCharFrom, LPCHARACTER pCharTo, int nSetPoint, int nMinute = 5);
	void EndAllDuel();
	bool EndDuel(DWORD pid);

	int GetDuelList(lua_State* L, int index);

	bool CanAttack(LPCHARACTER pCharAttacker, LPCHARACTER pCharVictim);
	bool OnDead(LPCHARACTER pCharKiller, LPCHARACTER pCharVictim);

	bool AddObserver(LPCHARACTER pChar, WORD ObserverX, WORD ObserverY);
	bool RegisterObserverPtr(LPCHARACTER pChar, DWORD mapIdx, WORD ObserverX, WORD ObserverY);

	MEMBER_IDENTITY IsMember(DWORD PID);
};

class CArenaManager : public singleton<CArenaManager>
{
	private :
		std::map<DWORD, CArenaMap*> m_mapArenaMap;

	public :
		bool Initialize();
		void Destroy();

		bool StartDuel(LPCHARACTER pCharFrom, LPCHARACTER pCharTo, int nSetPoint, int nMinute = 5);

		bool AddArena(DWORD mapIdx, WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y);

		void SendArenaMapListTo(LPCHARACTER pChar);

		void EndAllDuel();
		bool EndDuel(DWORD pid);

		void GetDuelList(lua_State* L);

		bool CanAttack(LPCHARACTER pCharAttacker, LPCHARACTER pCharVictim);

		bool OnDead(LPCHARACTER pCharKiller, LPCHARACTER pCharVictim);

		bool AddObserver(LPCHARACTER pChar, DWORD mapIdx, WORD ObserverX, WORD ObserverY);
		bool RegisterObserverPtr(LPCHARACTER pChar, DWORD mapIdx, WORD ObserverX, WORD ObserverY);

		bool IsArenaMap(DWORD dwMapIndex);
		MEMBER_IDENTITY IsMember(DWORD dwMapIndex, DWORD PID);

		bool IsLimitedItem( long lMapIndex, DWORD dwVnum );

#ifdef ENABLE_WS_TOURNAMENT
		// WS Turnuvasi yardimcilari
		int GetArenaCount(DWORD dwMapIndex);
		bool GetObserverPoint(DWORD dwMapIndex, WORD & wX, WORD & wY);
		bool WSRestoreSetPoints(DWORD dwPID, DWORD dwOwnPoints, DWORD dwOppPoints);
		bool WSPauseDuel(DWORD dwPID);
		bool WSResumeDuel(DWORD dwPID, int iRemainSec);
		bool WSSendDuelStart(DWORD dwPID);
#endif
};

#endif /*__CLASS_ARENA_MANAGER__*/
//archive's 6b9a24beef838d9382c750a6b44ccdb4
