#ifndef __INC_NEW_MOB_TIMER_H__
#define __INC_NEW_MOB_TIMER_H__

#include "../../common/CommonDefines.h"

#ifdef ENABLE_NEW_MOB_TIMER

class CHARACTER;

class CNewMobTimer : public singleton<CNewMobTimer>
{
public:
	enum
	{
		MAIN_UPDATE_INTERVAL = 60,
	};

	CNewMobTimer();
	~CNewMobTimer();

	bool Initialize();
	void Destroy();
	void Update();
	void BossIsDead(DWORD dwVID);

private:
	struct SRuntimeEntry
	{
		BYTE	bId;
		DWORD	dwVnum;
		long	lMapIndex;
		long	lXPos;
		long	lYPos;
		BYTE	bPerHour;
		BYTE	bPerMin;
		bool	bValid;

		DWORD	dwSpawnedVID;
		int		iLastSpawnDay;
		int		iLastSpawnMinute;
	};

	LPEVENT m_pkUpdateEvent;
	SRuntimeEntry m_aEntry[32];
	size_t m_entryCount;

	bool CanSpawnNow(const SRuntimeEntry& entry, int iSpawnDay, int iTimeAsMin) const;
	void SpawnBoss(SRuntimeEntry& entry, int iSpawnDay, int iTimeAsMin);
	bool IsBossAlive(SRuntimeEntry& entry) const;
	int GetIntervalMinute(const SRuntimeEntry& entry) const;
	void NotifyGMs(SRuntimeEntry& entry, int iSpawnDay, int iTimeAsMin);
};

#endif
#endif
