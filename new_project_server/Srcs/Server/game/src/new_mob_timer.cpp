#include "stdafx.h"
#include "../../common/CommonDefines.h"

#ifdef ENABLE_NEW_MOB_TIMER

#include "new_mob_timer.h"
#include "char.h"
#include "char_manager.h"
#include "sectree_manager.h"
#include "config.h"
#include "event.h"

#include <time.h>
#include <stdio.h>

//#define NEW_MOB_TIMER_DEBUG

#ifdef NEW_MOB_TIMER_DEBUG
#define NMT_LOG(fmt, ...) sys_log(0, "NewMobTimer: " fmt, ##__VA_ARGS__)
#else
#define NMT_LOG(fmt, ...) ((void)0)
#endif

namespace
{
	struct SNewMobTimerConfigRow
	{
		BYTE	bId;
		DWORD	dwVnum;
		long	lMapIndex;
		long	lXPos;
		long	lYPos;
		BYTE	bPerHour;
		BYTE	bPerMin;
	};

	// ID, VNUM, MAP_INDEX, X_POS, Y_POS, PER_HOUR, PER_MIN
	const SNewMobTimerConfigRow g_aNewMobTimerConfig[] =
	{
		{ 0,	1901,	61,		775,	575,	3,	0 },		// Dokuz kuyruk
		{ 1,	2206,	62,		125,	785,	3,	0 },		// Alev kral
		{ 2,	791,	65,		910,	847,	3,	0 },		// Karanlik lider
		{ 3,	691,	64,		770,	810,	3,	0 },		// Ork reisi
		{ 4,	1304,	65,		370,	420,	3,	0 },		// Sari kaplan
		{ 5,	2191,	63,		900,	619,	3,	0 },		// Kaplumbaga
		{ 6,	2091,	104,	390,	390,	3,	0 },		// Orumcek
		{ 7,	2491,	73,		395,	175,	4,	0 },		// Komutan
		{ 8,	2492,	73,		735,	1115,	4,	0 },		// General1
		{ 9,	2492,	73,		1260,	576,	4,	0 },		// General2
		{ 10,	2492,	73,		350,	275,	4,	0 },		// General3
		// { 11,	1192,	72,		1355,	1405,	12,	0 },		// Cadi
	};

	EVENTINFO(new_mob_timer_event_info)
	{
		int dummy;
	};

	EVENTFUNC(new_mob_timer_update_event)
	{
		new_mob_timer_event_info* info = dynamic_cast<new_mob_timer_event_info*>(event->info);

		if (!info)
		{
			sys_err("new_mob_timer_update_event> <Factor> Null pointer");
			return 0;
		}

		CNewMobTimer::instance().Update();
		return PASSES_PER_SEC(CNewMobTimer::MAIN_UPDATE_INTERVAL);
	}

	int BuildSpawnDay(const struct tm& tmLocal)
	{
		return (tmLocal.tm_year + 1900) * 1000 + tmLocal.tm_yday;
	}

	int GetNextSpawnMinute(int iTimeAsMin, int iIntervalMinute)
	{
		if (iIntervalMinute <= 0)
			return -1;

		int iRemainder = iTimeAsMin % iIntervalMinute;
		int iNext = iTimeAsMin + (iIntervalMinute - iRemainder) % iIntervalMinute;
		if (iNext <= iTimeAsMin)
			iNext += iIntervalMinute;

		if (iNext >= 24 * 60)
			iNext -= 24 * 60;

		return iNext;
	}

	struct FNewMobTimerGMChat
	{
		char szMsg[256];

		void operator () (LPCHARACTER ch) const
		{
			if (!ch || !ch->IsPC() || !ch->IsGM())
				return;

			ch->ChatPacket(CHAT_TYPE_INFO, "%s", szMsg);
		}
	};

	void SendGMChat(const char* szMsg)
	{
		if (!szMsg || !*szMsg)
			return;

		FNewMobTimerGMChat f;
		strlcpy(f.szMsg, szMsg, sizeof(f.szMsg));
		CHARACTER_MANAGER::instance().for_each_pc(f);
	}
}

CNewMobTimer::CNewMobTimer()
	: m_pkUpdateEvent(nullptr)
	, m_entryCount(0)
{
	memset(m_aEntry, 0, sizeof(m_aEntry));
}

CNewMobTimer::~CNewMobTimer()
{
	Destroy();
}

bool CNewMobTimer::Initialize()
{
	Destroy();

	m_entryCount = sizeof(g_aNewMobTimerConfig) / sizeof(g_aNewMobTimerConfig[0]);
	if (m_entryCount > sizeof(m_aEntry) / sizeof(m_aEntry[0]))
	{
		sys_err("NewMobTimer: config table exceeds runtime capacity (%u)", (unsigned)m_entryCount);
		m_entryCount = sizeof(m_aEntry) / sizeof(m_aEntry[0]);
	}

	for (size_t i = 0; i < m_entryCount; ++i)
	{
		const SNewMobTimerConfigRow& row = g_aNewMobTimerConfig[i];
		SRuntimeEntry& entry = m_aEntry[i];

		entry.bId = row.bId;
		entry.dwVnum = row.dwVnum;
		entry.lMapIndex = row.lMapIndex;
		entry.lXPos = row.lXPos;
		entry.lYPos = row.lYPos;
		entry.bPerHour = row.bPerHour;
		entry.bPerMin = row.bPerMin;
		entry.bValid = true;
		entry.dwSpawnedVID = 0;
		entry.iLastSpawnDay = -1;
		entry.iLastSpawnMinute = -1;

		if (row.bId != i)
			sys_err("NewMobTimer: config row index %u id mismatch (id=%u)", (unsigned)i, row.bId);

		if (row.bPerHour == 0 && row.bPerMin == 0)
		{
			sys_err("NewMobTimer: invalid interval for id %u vnum %u (per_hour=0 per_min=0)", row.bId, row.dwVnum);
			entry.bValid = false;
		}

		if (row.dwVnum == 0)
		{
			sys_err("NewMobTimer: invalid vnum for id %u", row.bId);
			entry.bValid = false;
		}
	}

	new_mob_timer_event_info* info = AllocEventInfo<new_mob_timer_event_info>();
	m_pkUpdateEvent = event_create(new_mob_timer_update_event, info, PASSES_PER_SEC(MAIN_UPDATE_INTERVAL));

	if (!m_pkUpdateEvent)
	{
		sys_err("NewMobTimer: failed to create update event");
		return false;
	}

	NMT_LOG("Initialize entries=%u interval=%d sec", (unsigned)m_entryCount, MAIN_UPDATE_INTERVAL);
	Update();
	return true;
}

void CNewMobTimer::Destroy()
{
	if (m_pkUpdateEvent)
	{
		event_cancel(&m_pkUpdateEvent);
		m_pkUpdateEvent = nullptr;
	}

	m_entryCount = 0;
	memset(m_aEntry, 0, sizeof(m_aEntry));
}

int CNewMobTimer::GetIntervalMinute(const SRuntimeEntry& entry) const
{
	int intervalMinute = 0;

	if (entry.bPerHour > 0)
		intervalMinute += entry.bPerHour * 60;

	if (entry.bPerMin > 0)
		intervalMinute += entry.bPerMin;

	return intervalMinute;
}

bool CNewMobTimer::CanSpawnNow(const SRuntimeEntry& entry, int iSpawnDay, int iTimeAsMin) const
{
	if (!entry.bValid)
		return false;

	const int intervalMinute = GetIntervalMinute(entry);
	if (intervalMinute <= 0)
		return false;

	if (iTimeAsMin % intervalMinute != 0)
		return false;

	if (entry.iLastSpawnDay == iSpawnDay && entry.iLastSpawnMinute == iTimeAsMin)
		return false;

	return true;
}

bool CNewMobTimer::IsBossAlive(SRuntimeEntry& entry) const
{
	if (entry.dwSpawnedVID == 0)
		return false;

	LPCHARACTER pkBoss = CHARACTER_MANAGER::instance().Find(entry.dwSpawnedVID);
	if (!pkBoss || pkBoss->IsDead())
		return false;

	if (pkBoss->GetRaceNum() != entry.dwVnum)
		return false;

	return true;
}

void CNewMobTimer::SpawnBoss(SRuntimeEntry& entry, int iSpawnDay, int iTimeAsMin)
{
	if (!map_allow_find(entry.lMapIndex))
	{
		NMT_LOG("map %ld not loaded for id %u", entry.lMapIndex, entry.bId);
		return;
	}

	LPSECTREE_MAP pkSectreeMap = SECTREE_MANAGER::instance().GetMap(entry.lMapIndex);
	if (!pkSectreeMap)
	{
		sys_err("NewMobTimer: GetMap failed id %u vnum %u map %ld", entry.bId, entry.dwVnum, entry.lMapIndex);
		return;
	}

	const long x = pkSectreeMap->m_setting.iBaseX + entry.lXPos * 100;
	const long y = pkSectreeMap->m_setting.iBaseY + entry.lYPos * 100;

	LPCHARACTER pkBoss = CHARACTER_MANAGER::instance().SpawnMob(
		entry.dwVnum,
		entry.lMapIndex,
		x,
		y,
		0,
		false,
		-1,
		true);

	if (!pkBoss)
	{
		sys_err("NewMobTimer: SpawnMob failed id %u vnum %u map %ld x %ld y %ld",
			entry.bId, entry.dwVnum, entry.lMapIndex, x, y);
		return;
	}

	entry.dwSpawnedVID = pkBoss->GetVID();
	entry.iLastSpawnDay = iSpawnDay;
	entry.iLastSpawnMinute = iTimeAsMin;

	NMT_LOG("spawned id %u vnum %u vid %u day %d min %d", entry.bId, entry.dwVnum, entry.dwSpawnedVID, iSpawnDay, iTimeAsMin);
}

void CNewMobTimer::NotifyGMs(SRuntimeEntry& entry, int iSpawnDay, int iTimeAsMin)
{
	if (!entry.bValid)
		return;

	const int iIntervalMinute = GetIntervalMinute(entry);
	if (iIntervalMinute <= 0)
		return;

	char szBuf[256];

	if (IsBossAlive(entry))
	{
		snprintf(szBuf, sizeof(szBuf), "[BossTimer] %u yasiyor (id %u map %ld)",
			entry.dwVnum, entry.bId, entry.lMapIndex);
		SendGMChat(szBuf);
		return;
	}

	if (CanSpawnNow(entry, iSpawnDay, iTimeAsMin))
	{
		snprintf(szBuf, sizeof(szBuf), "[BossTimer] %u bu dakikada doguyor (id %u)",
			entry.dwVnum, entry.bId);
		SendGMChat(szBuf);
		return;
	}

	const int iNextMin = GetNextSpawnMinute(iTimeAsMin, iIntervalMinute);
	if (iNextMin < 0)
		return;

	snprintf(szBuf, sizeof(szBuf), "[BossTimer] %u olu bekliyor - sonraki %02d:%02d (id %u)",
		entry.dwVnum,
		iNextMin / 60,
		iNextMin % 60,
		entry.bId);
	SendGMChat(szBuf);
}

void CNewMobTimer::Update()
{
	const time_t now = time(nullptr);
	struct tm tmLocal;
	memset(&tmLocal, 0, sizeof(tmLocal));

#if defined(_WIN32) || defined(_WIN64)
	localtime_s(&tmLocal, &now);
#else
	localtime_r(&now, &tmLocal);
#endif

	const int iTimeAsMin = tmLocal.tm_min + (tmLocal.tm_hour * 60);
	const int iSpawnDay = BuildSpawnDay(tmLocal);

	for (size_t i = 0; i < m_entryCount; ++i)
	{
		SRuntimeEntry& entry = m_aEntry[i];

		if (!entry.bValid)
			continue;

		if (IsBossAlive(entry))
			continue;

		entry.dwSpawnedVID = 0;

		if (!CanSpawnNow(entry, iSpawnDay, iTimeAsMin))
			continue;

		SpawnBoss(entry, iSpawnDay, iTimeAsMin);
	}

	for (size_t i = 0; i < m_entryCount; ++i)
	{
		if (m_aEntry[i].bValid)
			NotifyGMs(m_aEntry[i], iSpawnDay, iTimeAsMin);
	}
}

void CNewMobTimer::BossIsDead(DWORD dwVID)
{
	if (dwVID == 0)
		return;

	for (size_t i = 0; i < m_entryCount; ++i)
	{
		if (m_aEntry[i].dwSpawnedVID == dwVID)
		{
			NMT_LOG("boss dead id %u vid %u", m_aEntry[i].bId, dwVID);
			m_aEntry[i].dwSpawnedVID = 0;
			return;
		}
	}
}

#endif
