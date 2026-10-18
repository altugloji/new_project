#include "stdafx.h"

#ifdef ENABLE_ORB_EVENT

#include "constants.h"	// tables.h tiplerini packet.h'ten ONCE getirir (ffa_event.cpp sirasi)
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "desc.h"
#include "desc_manager.h"
#include "char.h"
#include "char_manager.h"
#include "sectree.h"
#include "sectree_manager.h"
#include "db.h"
#include "p2p.h"
#include "event.h"
#include "questmanager.h"
#include "dungeon.h"
#include "cmd.h"
#include "log.h"
#include "orb_event.h"

#include <time.h>
#if !defined(_WIN32) && !defined(_WIN64)
#include <sys/time.h>
#endif

// packet.h (GG 51) ile onbellek boyutlari ayni olmali
static_assert(ORB_EVENT_SNAP_TOP_MAX == ORB_EVENT_TOP_COUNT, "ORB_EVENT_SNAP_TOP_MAX != packet.h ORB_EVENT_TOP_COUNT");
static_assert(ORB_EVENT_SNAP_RANK_MAX == ORB_EVENT_RANK_COUNT, "ORB_EVENT_SNAP_RANK_MAX != packet.h ORB_EVENT_RANK_COUNT");
static_assert(ORB_EVENT_NAME_BUF == CHARACTER_NAME_MAX_LEN + 1, "ORB_EVENT_NAME_BUF != CHARACTER_NAME_MAX_LEN + 1");
static_assert(ORB_EVENT_ORB_COUNT >= 1 && ORB_EVENT_ORB_COUNT <= 30, "ORB_EVENT_ORB_COUNT 1..30 araliginda olmali");
static_assert(ORB_EVENT_LINE_MAX < CHAT_MAX_LEN, "ORB_EVENT_LINE_MAX CHAT_MAX_LEN altinda olmali (ChatPacket clamp'siz)");
static_assert(ORB_EVENT_GOLD_MAX_DIST >= ORB_EVENT_SPAWN_MIN_DIST && ORB_EVENT_GOLD_PCT >= 0 && ORB_EVENT_GOLD_PCT <= 100, "ORB_EVENT_GOLD_* degerleri gecersiz");
static_assert(ORB_EVENT_GOLD_INTERVAL_SEC >= 1 && ORB_EVENT_GOLD_LIFETIME_SEC >= 1, "ORB_EVENT_GOLD_INTERVAL_SEC / LIFETIME_SEC en az 1 olmali");
static_assert(ORB_EVENT_START_MINUTE >= 0 && ORB_EVENT_START_MINUTE < 60 && ORB_EVENT_START_MINUTE * 60 + ORB_EVENT_DURATION_SEC <= 3600, "ORB_EVENT_START_MINUTE + sure ayni saat icinde kalmali");

// ============================================================================
// sabitler / yardimcilar
// ============================================================================

namespace
{
	const int	ORB_TICKS_PER_SEC		= 5;		// 200 ms tick
	const int	ORB_GEN_PER_TICK		= 40;		// tick basina ilk uretim yapilan oturum sayisi
	const int	ORB_PICK_PER_TICK		= 3;		// tick basina en fazla toplanan kure
	const int	ORB_RELOC_PER_PASS		= 6;		// saniyelik gecis basina oturum basina yeniden dogan kure
	const int	ORB_PUT_PER_LINE		= 12;		// orb_put satiri basina kayit
	const int	ORB_PLACE_ATTEMPTS		= 8;		// TryPlaceOrb deneme sayisi
	const int	ORB_GOLD_SLOT			= ORB_EVENT_ORB_COUNT;	// sari kure slotu (aOrbs son elemani)
	const int	ORB_LINE_STEP_CM		= 100;		// gorus hatti ornekleme adimi
	const int	ORB_FLUSH_ROWS			= 200;		// flush ifadesi basina satir
	const int	ORB_POLL_INTERVAL_SEC	= 3;		// master snapshot araligi
	const int	ORB_POLL_TIMEOUT_SEC	= 15;		// cevapsiz poll sonrasi yeniden izin
	const int	ORB_POST_POLL_SEC		= 10;		// tur bitisinden sonra poll suresi
	const int	ORB_REWARD_CHECK_SEC	= 60;		// master odul kontrol araligi
	const int	ORB_BASE_READ_DELAY_SEC	= 2;		// ready sonrasi diger core toplam okuma gecikmesi
	const float	ORB_BUDGET_START		= 600.0f;	// hareket butcesi baslangic (cm)
	const float	ORB_BUDGET_MAX			= 1200.0f;	// hareket butcesi tavani (cm)
	const float	ORB_BUDGET_SLACK		= 10.0f;	// tick basina sabit pay (cm)
	const float	ORB_TICK_SEC			= 0.2f;
	const double ORB_PI					= 3.14159265358979323846;

	const long	s_alBlockedMaps[] = { ORB_EVENT_BLOCKED_MAPS };

	long TickPasses()
	{
		const long lPasses = PASSES_PER_SEC(1) / ORB_TICKS_PER_SEC;
		return lPasses < 1 ? 1 : lPasses;
	}

	// ms epoch: core'lar arasi karsilastirilabilir (get_dword_time boot-bagimli, kullanilmaz)
	unsigned long long NowMs()
	{
#if defined(_WIN32) || defined(_WIN64)
		return (unsigned long long) time(nullptr) * 1000ULL;
#else
		struct timeval tv;
		gettimeofday(&tv, nullptr);
		return (unsigned long long) tv.tv_sec * 1000ULL + (unsigned long long) (tv.tv_usec / 1000);
#endif
	}

	// CHAT_TYPE_COMMAND satiri: CHARACTER::ChatPacket vsnprintf would-be uzunlugunu
	// clamp'siz pakete yazar; sinir burada zorlanir (ORB_EVENT_LINE_MAX < CHAT_MAX_LEN)
	bool SendCommandLine(LPCHARACTER ch, const char * c_pszLine)
	{
		if (!ch || !ch->GetDesc() || !c_pszLine)
			return false;

		const size_t uLen = strlen(c_pszLine);

		if (uLen == 0 || uLen >= (size_t) ORB_EVENT_LINE_MAX)
		{
			sys_err("ORB_EVENT: komut satiri siniri asildi (%u bayt) - satir atlandi", (unsigned) uLen);
			return false;
		}

		ch->ChatPacket(CHAT_TYPE_COMMAND, "%s", c_pszLine);
		return true;
	}

	// 2B nokta (px,py) -> dogru parcasi (a,b) mesafesi (cm)
	float PointSegmentDist(long px, long py, long ax, long ay, long bx, long by)
	{
		const double vx = (double) (bx - ax);
		const double vy = (double) (by - ay);
		const double wx = (double) (px - ax);
		const double wy = (double) (py - ay);
		const double dLen2 = vx * vx + vy * vy;
		double t = 0.0;

		if (dLen2 > 0.0)
		{
			t = (wx * vx + wy * vy) / dLen2;

			if (t < 0.0)
				t = 0.0;
			else if (t > 1.0)
				t = 1.0;
		}

		const double cx = (double) ax + t * vx - (double) px;
		const double cy = (double) ay + t * vy - (double) py;
		return (float) sqrt(cx * cx + cy * cy);
	}

	void CopyName(char * pszDst, size_t uDstSize, const char * c_pszSrc)
	{
		snprintf(pszDst, uDstSize, "%s", c_pszSrc ? c_pszSrc : "");
	}
}

// ============================================================================
// tick eventi
// ============================================================================

EVENTINFO(TOrbTickEventInfo)
{
	int iDummy;

	TOrbTickEventInfo()
	: iDummy(0)
	{
	}
};

EVENTFUNC(orb_event_tick_event)
{
	if (event == nullptr || event->info == nullptr)
		return 0;

	COrbEventManager::instance().Tick();
	return TickPasses();
}

// ============================================================================
// yasam dongusu
// ============================================================================

COrbEventManager::COrbEventManager()
	: m_bDBReady(false)
	, m_bActive(false)
	, m_dwEventID(0)
	, m_tRoundEnd(0)
	, m_tRoundStartedAt(0)
	, m_dwLastEventID(0)
	, m_tLastRoundEnd(0)
	, m_bPendingValid(false)
	, m_bPollInFlight(false)
	, m_tPollSentAt(0)
	, m_tLastPoll(0)
	, m_tLastRewardCheck(0)
	, m_pkTickEvent(nullptr)
	, m_iTickCounter(0)
{
}

COrbEventManager::~COrbEventManager()
{
	Destroy();
}

void COrbEventManager::Initialize()
{
	// tablo varligi kontrolu (ws_tournament kalibi): COUNT tablo varsa HER ZAMAN 1 satir doner,
	// 0 satir = sorgu hata verdi = sql/orb_event.sql uygulanmamis
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT COUNT(*) FROM player.orb_event"));

		if (!pMsg || !pMsg->Get() || pMsg->Get()->uiNumRows == 0)
		{
			sys_err("ORB_EVENT: player.orb_event tablosu yok - sql/orb_event.sql uygulanmali. Sistem devre disi.");
			m_bDBReady = false;
			return;
		}
	}

	m_bDBReady = true;

	if (m_pkTickEvent == nullptr)
	{
		TOrbTickEventInfo * info = AllocEventInfo<TOrbTickEventInfo>();
		m_pkTickEvent = event_create(orb_event_tick_event, info, TickPasses());
	}

	sys_log(0, "ORB_EVENT: manager hazir (master %d, core %u, kanal %d)", IsMaster() ? 1 : 0, (unsigned) mother_port, (int) g_bChannel);
}

void COrbEventManager::Destroy()
{
	if (m_pkTickEvent)
		event_cancel(&m_pkTickEvent);

	m_pkTickEvent = nullptr;
	m_bActive = false;
	m_mapSessions.clear();
	m_mapReady.clear();
}

bool COrbEventManager::IsMaster() const
{
	return g_bChannel == 1 && SECTREE_MANAGER::instance().GetMap(1) != nullptr;
}

// ============================================================================
// program / tur
// ============================================================================

void COrbEventManager::ComputeSchedule(time_t tNow, bool & bActive, DWORD & dwEventID, time_t & tEnd)
{
	bActive = false;
	dwEventID = 0;
	tEnd = 0;

	quest::CQuestManager & q = quest::CQuestManager::instance();

	// test penceresi programa gore onceliklidir
	const int iTest = q.GetEventFlag("orb_event_test");

	// stop/cancel ile bitirilmis test turu pencere dolana kadar programi kilitlemesin: program dalina duser
	const bool bTestEnded = iTest > 0 &&
		((DWORD) q.GetEventFlag("orb_event_stop") == (DWORD) iTest || (DWORD) q.GetEventFlag("orb_event_cancel") == (DWORD) iTest);

	if (iTest > 0 && !bTestEnded && tNow >= (time_t) iTest && tNow < (time_t) iTest + ORB_EVENT_DURATION_SEC)
	{
		dwEventID = (DWORD) iTest;
		tEnd = (time_t) iTest + ORB_EVENT_DURATION_SEC;
		bActive = true;
	}
	else if (q.GetEventFlag("orb_event") > 0)
	{
		struct tm tmLocal;
		memset(&tmLocal, 0, sizeof(tmLocal));

#if defined(_WIN32) || defined(_WIN64)
		localtime_s(&tmLocal, &tNow);
#else
		localtime_r(&tNow, &tmLocal);
#endif

		const time_t tHourStart = tNow - (time_t) tmLocal.tm_min * 60 - (time_t) tmLocal.tm_sec;
		// tur saat basinda degil, saatin ORB_EVENT_START_MINUTE. dakikasinda baslar (orn. 01:30, 02:30)
		const time_t tSlotStart = tHourStart + (time_t) ORB_EVENT_START_MINUTE * 60;

		if (tNow >= tSlotStart && tNow - tSlotStart < ORB_EVENT_DURATION_SEC)
		{
			dwEventID = (DWORD) tSlotStart;
			tEnd = tSlotStart + ORB_EVENT_DURATION_SEC;
			bActive = true;
		}
	}

	if (!bActive)
		return;

	// stop/cancel bayraklari bu eid'yi gosteriyorsa tur bitmis sayilir
	if ((DWORD) q.GetEventFlag("orb_event_stop") == dwEventID || (DWORD) q.GetEventFlag("orb_event_cancel") == dwEventID)
		bActive = false;
}

void COrbEventManager::SendStartTo(LPCHARACTER ch)
{
	const time_t tNow = get_global_time();
	const int iRemain = (m_tRoundEnd > tNow) ? (int) (m_tRoundEnd - tNow) : 0;

	char szLine[ORB_EVENT_LINE_MAX + 1];
	snprintf(szLine, sizeof(szLine), "orb_start %u %d %d", m_dwEventID, iRemain, (int) ORB_EVENT_REWARD_MIN_SCORE);	// 3. alan: odul esigi (eski client *rest ile yok sayar)
	SendCommandLine(ch, szLine);
}

void COrbEventManager::StartRound(DWORD dwEventID, time_t tEnd)
{
	const time_t tNow = get_global_time();

	m_mapSessions.clear();
	m_bActive = true;
	m_dwEventID = dwEventID;
	m_tRoundEnd = tEnd;
	m_tRoundStartedAt = tNow;
	m_kSnapshot.Clear();
	m_kPending.Clear();
	m_bPendingValid = false;
	m_bPollInFlight = false;
	m_tLastPoll = 0;

	// her core: tur kaydi (INSERT IGNORE idempotent; master odul dagitiminda da garanti altina alinir)
	{
		char szQuery[256];
		snprintf(szQuery, sizeof(szQuery),
				"INSERT IGNORE INTO player.orb_event (event_id, start_time, end_time, state) VALUES (%u, FROM_UNIXTIME(%u), FROM_UNIXTIME(%u), 0)",
				dwEventID, dwEventID, (DWORD) tEnd);
		DBManager::instance().AsyncSafeQuery(szQuery);
	}

	// hazir oyunculara oturum ac + orb_start; bayat kayitlari supur
	std::vector<DWORD> vecStale;

	for (std::map<DWORD, DWORD>::iterator it = m_mapReady.begin(); it != m_mapReady.end(); ++it)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);

		if (!ch || (DWORD) ch->GetVID() != it->second || !ch->GetDesc())
		{
			vecStale.push_back(it->first);
			continue;
		}

		TOrbSession & s = m_mapSessions[it->first];
		s.dwPID = it->first;
		s.dwVID = it->second;
		s.lMapIndex = ch->GetMapIndex();
		s.bHasLast = false;
		s.bOrbsActive = false;
		s.bGenPending = true;
		s.fBudget = ORB_BUDGET_START;
		s.tBaseReadAt = tNow + ORB_BASE_READ_DELAY_SEC;
		s.bBaseLoaded = false;

		SendStartTo(ch);
	}

	for (size_t i = 0; i < vecStale.size(); ++i)
		m_mapReady.erase(vecStale[i]);

	// cluster-tekil buyuk duyuru: yalnizca master core (ch1 + map 1) basar, diger core'lar cift basmasin (FFA kalibi)
	if (IsMaster())
		BroadcastNotice("Orb Rush etkinligi basladi!", true);

	sys_log(0, "ORB_EVENT: tur basladi eid %u bitis %ld hazir %u master %d",
			dwEventID, (long) tEnd, (unsigned) m_mapSessions.size(), IsMaster() ? 1 : 0);
}

void COrbEventManager::EndRound()
{
	char szLine[ORB_EVENT_LINE_MAX + 1];
	snprintf(szLine, sizeof(szLine), "orb_end %u", m_dwEventID);

	DWORD dwOnline = 0;

	for (std::map<DWORD, TOrbSession>::iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); ++it)
	{
		if (it->second.dwVID == 0)
			continue;

		LPCHARACTER ch = FindOnline(it->second);

		if (!ch)
			continue;

		SendCommandLine(ch, szLine);
		++dwOnline;
	}

	// son skorlar DB'ye (sorgu metni kopyalanir; oturumlar sonra silinebilir)
	FlushScores();

	if (IsMaster())
		BroadcastNotice("Orb Rush etkinligi sona erdi!", true);

	sys_log(0, "ORB_EVENT: tur bitti eid %u oturum %u cevrimici %u", m_dwEventID, (unsigned) m_mapSessions.size(), dwOnline);

	m_bActive = false;
	m_dwLastEventID = m_dwEventID;
	m_tLastRoundEnd = get_global_time();
	m_mapSessions.clear();
}

// ============================================================================
// oyuncu kancalari
// ============================================================================

void COrbEventManager::OnReady(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc())
		return;

	const DWORD dwPID = ch->GetPlayerID();
	const DWORD dwVID = (DWORD) ch->GetVID();

	if (dwPID == 0)
		return;

	m_mapReady[dwPID] = dwVID;

	if (!m_bActive)
		return;

	const time_t tNow = get_global_time();
	TOrbSession & s = m_mapSessions[dwPID];	// var olan oturum: skorlar korunur (ayni turda yeniden giris)
	s.dwPID = dwPID;

	// ayni VID ile ikinci /orb_ready: kureleri YENIDEN URETME, mevcutlari yeniden gonder
	// (saniyede en fazla bir yeniden gonderim: degistirilmis client spam'i paket urettirmesin)
	if (s.dwVID == dwVID && s.bOrbsActive)
	{
		if (s.tLastResend == tNow)
			return;

		s.tLastResend = tNow;
		SendStartTo(ch);
		SendOrbPutAll(ch, s);

		if (m_kSnapshot.tReceived != 0 && m_kSnapshot.dwEventID == m_dwEventID)
			SendSnapshotTo(ch, &s);

		return;
	}

	s.dwVID = dwVID;
	s.lMapIndex = ch->GetMapIndex();
	s.bHasLast = false;
	s.bOrbsActive = false;
	s.bGenPending = true;
	s.fBudget = ORB_BUDGET_START;
	s.tBaseReadAt = tNow + ORB_BASE_READ_DELAY_SEC;
	s.bBaseLoaded = false;

	SendStartTo(ch);

	if (m_kSnapshot.tReceived != 0 && m_kSnapshot.dwEventID == m_dwEventID)
		SendSnapshotTo(ch, &s);
}

void COrbEventManager::OnDestroy(LPCHARACTER ch)
{
	// NPC'lerde PID 0: bos map'lerde find maliyeti sifira yakin
	if (!ch || ch->GetPlayerID() == 0)
		return;

	if (m_mapReady.empty() && m_mapSessions.empty())
		return;

	const DWORD dwPID = ch->GetPlayerID();
	const DWORD dwVID = (DWORD) ch->GetVID();

	std::map<DWORD, DWORD>::iterator itReady = m_mapReady.find(dwPID);

	if (itReady != m_mapReady.end() && itReady->second == dwVID)
		m_mapReady.erase(itReady);

	std::map<DWORD, TOrbSession>::iterator itSession = m_mapSessions.find(dwPID);

	if (itSession != m_mapSessions.end() && itSession->second.dwVID == dwVID)
	{
		// skorlar kalir, bDirty flush'a girmeye devam eder
		itSession->second.dwVID = 0;
		itSession->second.bHasLast = false;
	}
}

bool COrbEventManager::IsMapAllowed(long lMapIndex) const
{
	if (lMapIndex <= 0 || lMapIndex > ORB_EVENT_MAX_MAP_INDEX)
		return false;

	for (size_t i = 0; i < sizeof(s_alBlockedMaps) / sizeof(s_alBlockedMaps[0]); ++i)
		if (s_alBlockedMaps[i] == lMapIndex)
			return false;

	return true;
}

bool COrbEventManager::IsEligible(LPCHARACTER ch) const
{
	if (!ch || !ch->GetDesc() || !ch->GetSectree())
		return false;

	if (ch->IsDead() || ch->IsWarping() || ch->GetMyShop() != nullptr || ch->IsObserverMode())
		return false;

	if (ch->GetDungeon() != nullptr)
		return false;

	return IsMapAllowed(ch->GetMapIndex());
}

LPCHARACTER COrbEventManager::FindOnline(TOrbSession & s)
{
	if (s.dwVID == 0)
		return nullptr;

	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(s.dwPID);

	if (!ch || (DWORD) ch->GetVID() != s.dwVID || !ch->GetDesc())
	{
		s.dwVID = 0;
		s.bHasLast = false;
		return nullptr;
	}

	return ch;
}

// ============================================================================
// kure uretimi
// ============================================================================

bool COrbEventManager::IsLineClear(long lMapIndex, long ax, long ay, long bx, long by) const
{
	const float fLen = DISTANCE_SQRT(bx - ax, by - ay);
	const int iSteps = (int) (fLen / (float) ORB_LINE_STEP_CM);

	for (int i = 1; i < iSteps; ++i)
	{
		const double t = (double) i * (double) ORB_LINE_STEP_CM / (double) fLen;
		const long sx = ax + (long) ((double) (bx - ax) * t);
		const long sy = ay + (long) ((double) (by - ay) * t);

		if (sx < 0 || sy < 0)
			return false;

		LPSECTREE tree = SECTREE_MANAGER::instance().Get((DWORD) lMapIndex, (DWORD) sx, (DWORD) sy);

		if (!tree)
			return false;

		if (tree->IsAttr(sx, sy, ATTR_BLOCK | ATTR_OBJECT))
			return false;
	}

	return true;
}

bool COrbEventManager::TryPlaceOrb(const TOrbSession & s, long lMapIndex, long px, long py, int iSlot, TOrb & out, int iMaxDist, BYTE bForceType) const
{
	if (iMaxDist < ORB_EVENT_SPAWN_MIN_DIST)
		iMaxDist = ORB_EVENT_SPAWN_MIN_DIST;

	for (int iAttempt = 0; iAttempt < ORB_PLACE_ATTEMPTS; ++iAttempt)
	{
		const int iAngle = number(0, 359);
		const int iDist = number(ORB_EVENT_SPAWN_MIN_DIST, iMaxDist);
		const double dRad = (double) iAngle * ORB_PI / 180.0;
		const long x = px + (long) ((double) iDist * cos(dRad));
		const long y = py + (long) ((double) iDist * sin(dRad));

		if (x < 0 || y < 0)
			continue;

		LPSECTREE tree = SECTREE_MANAGER::instance().Get((DWORD) lMapIndex, (DWORD) x, (DWORD) y);

		if (!tree)
			continue;

		if (tree->IsAttr(x, y, ATTR_BLOCK | ATTR_OBJECT | ATTR_WATER))
			continue;

		if (!IsLineClear(lMapIndex, px, py, x, y))
			continue;

		// diger gecerli kurelerle en az ORB_EVENT_ORB_MIN_GAP mesafe (kendi slotu haric; sari slot dahil)
		bool bTooClose = false;

		for (int i = 0; i < ORB_EVENT_ORB_COUNT + 1; ++i)
		{
			if (i == iSlot || !s.aOrbs[i].valid)
				continue;

			if (DISTANCE_SQRT(s.aOrbs[i].x - x, s.aOrbs[i].y - y) < (float) ORB_EVENT_ORB_MIN_GAP)
			{
				bTooClose = true;
				break;
			}
		}

		if (bTooClose)
			continue;

		out.x = x;
		out.y = y;
		out.type = bForceType ? bForceType : ((number(1, 100) <= ORB_EVENT_BLUE_PCT) ? 2 : 1);
		out.valid = true;
		return true;
	}

	out.x = 0;
	out.y = 0;
	out.type = 0;
	out.valid = false;
	return false;
}

void COrbEventManager::GenerateAll(TOrbSession & s, LPCHARACTER ch)
{
	const bool bRegenerate = s.bOrbsActive;
	const long px = ch->GetX();
	const long py = ch->GetY();

	s.lMapIndex = ch->GetMapIndex();

	for (int i = 0; i < ORB_EVENT_ORB_COUNT + 1; ++i)
		s.aOrbs[i] = TOrb();

	// sari kure de sifirlanir; ilk sans kontrolu ORB_EVENT_GOLD_INTERVAL_SEC sonra
	s.ullGoldExpireMs = 0;
	s.bGoldSpawnPending = false;
	s.ullGoldNextRollMs = NowMs() + (unsigned long long) ORB_EVENT_GOLD_INTERVAL_SEC * 1000ULL;

	for (int i = 0; i < ORB_EVENT_ORB_COUNT; ++i)
	{
		TOrb kNew;

		if (TryPlaceOrb(s, s.lMapIndex, px, py, i, kNew))
			s.aOrbs[i] = kNew;
	}

	// yeniden uretimde client'taki eski kureler silinir (basarisiz slotlar hayalet kalmasin)
	if (bRegenerate)
		SendCommandLine(ch, "orb_clear");

	s.bOrbsActive = true;
	s.bGenPending = false;
	SendOrbPutAll(ch, s);
}

void COrbEventManager::SendOrbPutSlots(LPCHARACTER ch, const TOrbSession & s, const int * aiSlots, int iCount)
{
	if (!ch || !aiSlots || iCount <= 0)
		return;

	char szLine[ORB_EVENT_LINE_MAX + 1];
	int iLen = snprintf(szLine, sizeof(szLine), "orb_put");
	int iInLine = 0;

	for (int i = 0; i < iCount; ++i)
	{
		const int iSlot = aiSlots[i];

		if (iSlot < 0 || iSlot > ORB_GOLD_SLOT)
			continue;

		const TOrb & o = s.aOrbs[iSlot];

		if (!o.valid)
			continue;

		char szEntry[64];
		const int iEntryLen = snprintf(szEntry, sizeof(szEntry), "%d,%ld,%ld,%d", iSlot, o.x, o.y, (int) o.type);

		// +1: ayirici (' ' ilk kayit, ';' sonrakiler)
		if (iInLine >= ORB_PUT_PER_LINE || iLen + 1 + iEntryLen >= ORB_EVENT_LINE_MAX)
		{
			if (iInLine > 0)
				SendCommandLine(ch, szLine);

			iLen = snprintf(szLine, sizeof(szLine), "orb_put");
			iInLine = 0;
		}

		iLen += snprintf(szLine + iLen, sizeof(szLine) - iLen, "%c%s", iInLine == 0 ? ' ' : ';', szEntry);
		++iInLine;
	}

	if (iInLine > 0)
		SendCommandLine(ch, szLine);
}

void COrbEventManager::SendOrbPutAll(LPCHARACTER ch, const TOrbSession & s)
{
	// sari slot (ORB_GOLD_SLOT) dahil: /orb_ready yeniden gonderiminde canli sari kure de gitsin (gecersiz slotlar atlanir)
	int aiSlots[ORB_EVENT_ORB_COUNT + 1];

	for (int i = 0; i <= ORB_GOLD_SLOT; ++i)
		aiSlots[i] = i;

	SendOrbPutSlots(ch, s, aiSlots, ORB_EVENT_ORB_COUNT + 1);
}

// ============================================================================
// hareket / toplama (200 ms)
// ============================================================================

void COrbEventManager::ProcessSession(TOrbSession & s, LPCHARACTER ch, int & iGenBudget)
{
	if (!IsEligible(ch))
	{
		// uygun olmayan tick: parca bir sonraki uygun tick'te yeniden baslar
		s.bHasLast = false;
		// sari kurenin omru burada da isler (olu/pazar/gozlemci iken client'ta gorunur kalmasin)
		ExpireGoldIfDue(s, ch, NowMs());
		return;
	}

	const long cx = ch->GetX();
	const long cy = ch->GetY();

	// ayni core icinde harita degisimi (guvenlik agi: normalde VID degisir ve OnReady yeniden kurar)
	if (s.bOrbsActive && s.lMapIndex != ch->GetMapIndex())
	{
		SendCommandLine(ch, "orb_clear");	// eski haritanin kureleri client'ta silinsin (GenerateAll bRegenerate=false gorecek)
		s.bOrbsActive = false;
		s.bGenPending = true;
		s.bHasLast = false;
	}

	if (s.bGenPending || !s.bOrbsActive)
	{
		if (iGenBudget <= 0)
			return;	// bu tick kuyruk dolu, sonraki tick

		--iGenBudget;
		GenerateAll(s, ch);
		s.lLastX = cx;
		s.lLastY = cy;
		s.bHasLast = true;
		s.fBudget = ORB_BUDGET_START;
		return;
	}

	// sari kure omur/sans dongusu (hareketten bagimsiz, her tick)
	GoldStep(s, ch);

	if (!s.bHasLast)
	{
		s.lLastX = cx;
		s.lLastY = cy;
		s.bHasLast = true;
		s.fBudget = ORB_BUDGET_START;
		return;
	}

	const long lx = s.lLastX;
	const long ly = s.lLastY;
	const float fDist = DISTANCE_SQRT(cx - lx, cy - ly);

	s.fBudget += ch->GetMoveSpeed() * 1.25f * ORB_TICK_SEC + ORB_BUDGET_SLACK;

	if (s.fBudget > ORB_BUDGET_MAX)
		s.fBudget = ORB_BUDGET_MAX;

	if (fDist > s.fBudget)
	{
		// butce asimi: bu tick toplama yok; isinlanma mesafesindeyse kureler yeniden dogar
		if (fDist > (float) ORB_EVENT_RELOCATE_DIST)
			GenerateAll(s, ch);

		s.lLastX = cx;
		s.lLastY = cy;
		return;
	}

	s.fBudget -= fDist;

	// toplama: last->cur parcasina PICK_RADIUS icinde kalan kureler (tick basina en fazla 3)
	int iPicked = 0;

	for (int i = 0; i < ORB_EVENT_ORB_COUNT + 1 && iPicked < ORB_PICK_PER_TICK; ++i)	// son slot = sari kure
	{
		TOrb & o = s.aOrbs[i];

		if (!o.valid)
			continue;

		if (PointSegmentDist(o.x, o.y, lx, ly, cx, cy) > (float) ORB_EVENT_PICK_RADIUS)
			continue;

		int iGain;

		if (o.type == 3)
		{
			iGain = ORB_EVENT_GOLD_POINTS;	// sari kure
			++s.dwGold;
		}
		else if (o.type == 2)
		{
			iGain = ORB_EVENT_BLUE_POINTS;
			++s.dwBlue;
		}
		else
		{
			iGain = ORB_EVENT_WHITE_POINTS;	// beyaz kure eksi puan (ceza)
			++s.dwWhite;
		}

		s.iScore += iGain;
		s.bDirty = true;
		s.ullLastTs = NowMs();
		++iPicked;

		// toplanan slot once bosalir (min-gap kontrolu kendisini saymasin), sonra yenisi denenir
		o = TOrb();

		TOrb kNew;

		if (i != ORB_GOLD_SLOT)
			TryPlaceOrb(s, s.lMapIndex, cx, cy, i, kNew);
		else
		{
			// sari kure alindi: yerine yenisi gelmez, sans dongusu yeniden baslar
			s.ullGoldExpireMs = 0;
			s.ullGoldNextRollMs = NowMs() + (unsigned long long) ORB_EVENT_GOLD_INTERVAL_SEC * 1000ULL;
		}

		if (kNew.valid)
			o = kNew;

		const int iTotal = s.iScore + s.iBaseScore;

		char szLine[ORB_EVENT_LINE_MAX + 1];
		snprintf(szLine, sizeof(szLine), "orb_take %d %d %d %ld %ld %d",
				i, iGain, iTotal,
				o.valid ? o.x : 0L, o.valid ? o.y : 0L, o.valid ? (int) o.type : 0);
		SendCommandLine(ch, szLine);
	}

	s.lLastX = cx;
	s.lLastY = cy;
}

bool COrbEventManager::ExpireGoldIfDue(TOrbSession & s, LPCHARACTER ch, unsigned long long ullNow)
{
	TOrb & gold = s.aOrbs[ORB_GOLD_SLOT];

	if (!gold.valid || ullNow < s.ullGoldExpireMs)
		return false;

	// omur doldu: kaybolur, sans dongusu yeniden baslar
	gold = TOrb();
	s.ullGoldExpireMs = 0;
	s.ullGoldNextRollMs = ullNow + (unsigned long long) ORB_EVENT_GOLD_INTERVAL_SEC * 1000ULL;

	char szLine[ORB_EVENT_LINE_MAX + 1];
	snprintf(szLine, sizeof(szLine), "orb_del %d", ORB_GOLD_SLOT);
	SendCommandLine(ch, szLine);
	return true;
}

// sari kure: oyuncu basina tek slot; her ORB_EVENT_GOLD_INTERVAL_SEC'de %ORB_EVENT_GOLD_PCT sansla oyuncuya
// yakin (<= ORB_EVENT_GOLD_MAX_DIST) dogar, ORB_EVENT_GOLD_LIFETIME_SEC icinde alinmazsa silinir (orb_del)
void COrbEventManager::GoldStep(TOrbSession & s, LPCHARACTER ch)
{
	const unsigned long long ullNow = NowMs();
	TOrb & gold = s.aOrbs[ORB_GOLD_SLOT];

	if (gold.valid)
	{
		ExpireGoldIfDue(s, ch, ullNow);
		return;
	}

	if (ullNow < s.ullGoldNextRollMs)
		return;

	s.ullGoldNextRollMs = ullNow + (unsigned long long) ORB_EVENT_GOLD_INTERVAL_SEC * 1000ULL;

	// sans: tutmazsa cik; tuttuysa (veya onceki tutan sans yer bulamadiysa) yerlestirmeyi dene
	if (!s.bGoldSpawnPending && number(1, 100) > ORB_EVENT_GOLD_PCT)
		return;

	TOrb kNew;

	if (!TryPlaceOrb(s, s.lMapIndex, ch->GetX(), ch->GetY(), ORB_GOLD_SLOT, kNew, ORB_EVENT_GOLD_MAX_DIST, 3))
	{
		// yer bulunamadi (kalabalik/engel): sans harcanmaz, 1 sn sonra yeniden denenir
		s.bGoldSpawnPending = true;
		s.ullGoldNextRollMs = ullNow + 1000ULL;
		return;
	}

	s.bGoldSpawnPending = false;
	gold = kNew;
	s.ullGoldExpireMs = ullNow + (unsigned long long) ORB_EVENT_GOLD_LIFETIME_SEC * 1000ULL;

	const int iSlot = ORB_GOLD_SLOT;
	SendOrbPutSlots(ch, s, &iSlot, 1);
}

void COrbEventManager::RelocationPass()
{
	for (std::map<DWORD, TOrbSession>::iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); ++it)
	{
		TOrbSession & s = it->second;

		if (s.dwVID == 0 || !s.bOrbsActive || s.bGenPending)
			continue;

		LPCHARACTER ch = FindOnline(s);

		if (!ch || !IsEligible(ch))
			continue;

		const long cx = ch->GetX();
		const long cy = ch->GetY();

		int aiChanged[ORB_RELOC_PER_PASS];
		int iChanged = 0;

		for (int i = 0; i < ORB_EVENT_ORB_COUNT && iChanged < ORB_RELOC_PER_PASS; ++i)
		{
			TOrb & o = s.aOrbs[i];

			if (o.valid && DISTANCE_SQRT(o.x - cx, o.y - cy) <= (float) ORB_EVENT_RELOCATE_DIST)
				continue;

			// yeni yer bulunamazsa eski (uzak) kure yerinde kalir - client'ta hayalet olusmaz
			TOrb kNew;

			if (!TryPlaceOrb(s, s.lMapIndex, cx, cy, i, kNew))
				continue;

			o = kNew;
			aiChanged[iChanged++] = i;
		}

		if (iChanged > 0)
			SendOrbPutSlots(ch, s, aiChanged, iChanged);
	}
}

// ============================================================================
// skor flush / diger core toplami
// ============================================================================

void COrbEventManager::FlushScores()
{
	static const char * c_pszHead = "INSERT INTO player.orb_event_score (event_id, pid, core_id, score, blue_cnt, white_cnt, last_ts) VALUES ";
	static const char * c_pszTail = " ON DUPLICATE KEY UPDATE score=VALUES(score), blue_cnt=VALUES(blue_cnt), white_cnt=VALUES(white_cnt), last_ts=VALUES(last_ts)";

	std::string stQuery;
	int iRows = 0;

	for (std::map<DWORD, TOrbSession>::iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); ++it)
	{
		TOrbSession & s = it->second;

		if (!s.bDirty)
			continue;

		s.bDirty = false;

		char szRow[160];
		snprintf(szRow, sizeof(szRow), "(%u,%u,%u,%d,%u,%u,%llu)",
				m_dwEventID, s.dwPID, (unsigned) mother_port, s.iScore, s.dwBlue, s.dwWhite, s.ullLastTs);

		if (iRows == 0)
			stQuery = c_pszHead;
		else
			stQuery += ",";

		stQuery += szRow;
		++iRows;

		if (iRows >= ORB_FLUSH_ROWS)
		{
			stQuery += c_pszTail;
			DBManager::instance().AsyncSafeQuery(stQuery.c_str());
			stQuery.clear();
			iRows = 0;
		}
	}

	if (iRows > 0)
	{
		stQuery += c_pszTail;
		DBManager::instance().AsyncSafeQuery(stQuery.c_str());
	}
}

void COrbEventManager::BaseReadPass(time_t tNow)
{
	for (std::map<DWORD, TOrbSession>::iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); ++it)
	{
		TOrbSession & s = it->second;

		if (s.dwVID == 0 || s.bBaseLoaded || s.tBaseReadAt == 0 || s.tBaseReadAt > tNow)
			continue;

		s.tBaseReadAt = 0;	// tek istek; sonuc gelene kadar yeniden sorulmaz
		RequestBaseScore(s);
	}
}

void COrbEventManager::RequestBaseScore(TOrbSession & s)
{
	const DWORD dwEventID = m_dwEventID;
	const DWORD dwPID = s.dwPID;

	char szQuery[256];
	snprintf(szQuery, sizeof(szQuery),
			"SELECT IFNULL(SUM(score),0) FROM player.orb_event_score WHERE event_id=%u AND pid=%u AND core_id<>%u",
			dwEventID, dwPID, (unsigned) mother_port);

	DBManager::instance().FuncSafeQuery(
		[dwEventID, dwPID](SQLMsg * pMsg)
		{
			// callback ana thread'de (DBManager::Process); tur bitmis/oyuncu cikmis olabilir
			if (!pMsg || pMsg->uiSQLErrno != 0 || !pMsg->Get() || !pMsg->Get()->pSQLResult)
			{
				COrbEventManager::instance().OnBaseScoreResult(dwEventID, dwPID, 0, false);	// yeniden denensin
				return;
			}

			MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
			int iSum = 0;

			if (row && row[0])
				str_to_number(iSum, row[0]);

			COrbEventManager::instance().OnBaseScoreResult(dwEventID, dwPID, iSum, true);
		},
		szQuery);
}

void COrbEventManager::OnBaseScoreResult(DWORD dwEventID, DWORD dwPID, int iSum, bool bOK)
{
	if (!m_bActive || m_dwEventID != dwEventID)
		return;

	std::map<DWORD, TOrbSession>::iterator it = m_mapSessions.find(dwPID);

	if (it == m_mapSessions.end())
		return;

	if (!bOK)
	{
		// gecici DB hatasi: ORB_BASE_READ_DELAY_SEC sonra BaseReadPass yeniden ister (tek atislik kalmasin)
		it->second.tBaseReadAt = get_global_time() + ORB_BASE_READ_DELAY_SEC;
		return;
	}

	it->second.iBaseScore = iSum;
	it->second.bBaseLoaded = true;
}

// ============================================================================
// siralama snapshot'i (master uretir, P2P ile yayar; herkes kendi oyuncusuna gonderir)
// ============================================================================

void COrbEventManager::PollSnapshot(time_t tNow)
{
	if (m_bPollInFlight && tNow - m_tPollSentAt < ORB_POLL_TIMEOUT_SEC)
		return;

	const DWORD dwEventID = m_bActive ? m_dwEventID : m_dwLastEventID;

	if (dwEventID == 0)
		return;

	m_bPollInFlight = true;
	m_bPendingValid = false;
	m_tPollSentAt = tNow;
	m_tLastPoll = tNow;
	m_kPending.Clear();
	m_kPending.dwEventID = dwEventID;

	// 1) ilk 100 (isimle): GROUP BY'a p.name eklenir (ONLY_FULL_GROUP_BY uyumu)
	{
		char szQuery[512];
		snprintf(szQuery, sizeof(szQuery),
				"SELECT s.pid, p.name, SUM(s.score) AS sc, MAX(s.last_ts) AS lt FROM player.orb_event_score s JOIN player.player p ON p.id = s.pid WHERE s.event_id=%u GROUP BY s.pid, p.name HAVING sc > 0 ORDER BY sc DESC, lt ASC, s.pid ASC LIMIT %d",
				dwEventID, (int) ORB_EVENT_SNAP_RANK_MAX);

		DBManager::instance().FuncSafeQuery(
			[dwEventID](SQLMsg * pMsg)
			{
				TOrbSnapshot kRows;
				kRows.dwEventID = dwEventID;

				if (!pMsg || pMsg->uiSQLErrno != 0 || !pMsg->Get() || !pMsg->Get()->pSQLResult)
				{
					COrbEventManager::instance().OnPollRowsResult(dwEventID, false, kRows);
					return;
				}

				MYSQL_ROW row;
				int iIdx = 0;

				while (iIdx < ORB_EVENT_SNAP_RANK_MAX && (row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
				{
					DWORD dwPID = 0;
					int iScore = 0;

					if (row[0]) str_to_number(dwPID, row[0]);
					if (row[2]) str_to_number(iScore, row[2]);

					if (dwPID == 0 || iScore <= 0)
						continue;

					kRows.rank[iIdx].dwPID = dwPID;
					kRows.rank[iIdx].iScore = iScore;

					if (iIdx < ORB_EVENT_SNAP_TOP_MAX)
					{
						kRows.top[iIdx].dwPID = dwPID;
						kRows.top[iIdx].iScore = iScore;
						CopyName(kRows.top[iIdx].szName, sizeof(kRows.top[iIdx].szName), row[1]);
					}

					++iIdx;
				}

				kRows.bRankCount = (BYTE) iIdx;
				kRows.bTopCount = (BYTE) (iIdx < ORB_EVENT_SNAP_TOP_MAX ? iIdx : ORB_EVENT_SNAP_TOP_MAX);
				COrbEventManager::instance().OnPollRowsResult(dwEventID, true, kRows);
			},
			szQuery);
	}

	// 2) katilimci sayisi (ayni FIFO kuyruk: her zaman 1'den SONRA gelir)
	{
		char szQuery[256];
		snprintf(szQuery, sizeof(szQuery),
				"SELECT COUNT(*) FROM (SELECT pid FROM player.orb_event_score WHERE event_id=%u GROUP BY pid HAVING SUM(score) > 0) t",
				dwEventID);

		DBManager::instance().FuncSafeQuery(
			[dwEventID](SQLMsg * pMsg)
			{
				if (!pMsg || pMsg->uiSQLErrno != 0 || !pMsg->Get() || !pMsg->Get()->pSQLResult)
				{
					COrbEventManager::instance().OnPollCountResult(dwEventID, false, 0);
					return;
				}

				MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
				DWORD dwCount = 0;

				if (row && row[0])
					str_to_number(dwCount, row[0]);

				COrbEventManager::instance().OnPollCountResult(dwEventID, true, dwCount);
			},
			szQuery);
	}
}

void COrbEventManager::OnPollRowsResult(DWORD dwEventID, bool bOK, const TOrbSnapshot & kRows)
{
	if (m_kPending.dwEventID != dwEventID)
		return;	// bayat cevap (yeni tur basladi)

	if (!bOK)
	{
		m_bPendingValid = false;
		return;
	}

	m_kPending = kRows;
	m_kPending.dwEventID = dwEventID;
	m_bPendingValid = true;
}

void COrbEventManager::OnPollCountResult(DWORD dwEventID, bool bOK, DWORD dwCount)
{
	if (m_kPending.dwEventID != dwEventID)
		return;

	m_bPollInFlight = false;

	if (!bOK || !m_bPendingValid)
		return;

	m_kPending.dwParticipants = dwCount;
	m_kPending.tReceived = get_global_time();
	m_kSnapshot = m_kPending;
	m_bPendingValid = false;

	ApplySnapshot();
	BroadcastSnapshotP2P();
}

void COrbEventManager::BroadcastSnapshotP2P()
{
	TPacketGGOrbEvent pkt;
	memset(&pkt, 0, sizeof(pkt));

	pkt.bHeader = HEADER_GG_ORB_EVENT;
	pkt.bSub = ORB_EVENT_SUB_SNAPSHOT;
	pkt.dwEventID = m_kSnapshot.dwEventID;
	pkt.dwParticipants = m_kSnapshot.dwParticipants;
	pkt.bTopCount = m_kSnapshot.bTopCount;
	pkt.bRankCount = m_kSnapshot.bRankCount;

	for (int i = 0; i < (int) pkt.bTopCount && i < ORB_EVENT_TOP_COUNT; ++i)
	{
		pkt.top[i].dwPID = m_kSnapshot.top[i].dwPID;
		pkt.top[i].iScore = m_kSnapshot.top[i].iScore;
		CopyName(pkt.top[i].szName, sizeof(pkt.top[i].szName), m_kSnapshot.top[i].szName);
	}

	for (int i = 0; i < (int) pkt.bRankCount && i < ORB_EVENT_RANK_COUNT; ++i)
	{
		pkt.rank[i].dwPID = m_kSnapshot.rank[i].dwPID;
		pkt.rank[i].iScore = m_kSnapshot.rank[i].iScore;
	}

	P2P_MANAGER::instance().Send(&pkt, sizeof(pkt));
}

void COrbEventManager::OnP2P(const TPacketGGOrbEvent * p)
{
	if (!p)
		return;

	switch (p->bSub)
	{
		case ORB_EVENT_SUB_SNAPSHOT:
			// master kendi snapshot'ini yerelde uygular; ikinci bir (yanlis-config) master'in yayini ezmesin
			if (IsMaster())
				return;

			m_kSnapshot.Clear();
			m_kSnapshot.dwEventID = p->dwEventID;
			m_kSnapshot.dwParticipants = p->dwParticipants;
			m_kSnapshot.bTopCount = (p->bTopCount < ORB_EVENT_SNAP_TOP_MAX) ? p->bTopCount : (BYTE) ORB_EVENT_SNAP_TOP_MAX;
			m_kSnapshot.bRankCount = (p->bRankCount < ORB_EVENT_SNAP_RANK_MAX) ? p->bRankCount : (BYTE) ORB_EVENT_SNAP_RANK_MAX;

			for (int i = 0; i < (int) m_kSnapshot.bTopCount; ++i)
			{
				m_kSnapshot.top[i].dwPID = p->top[i].dwPID;
				m_kSnapshot.top[i].iScore = p->top[i].iScore;
				// wire'dan gelen isim sonlandirilmamis olabilir: uzunluk sinirli kopya
				snprintf(m_kSnapshot.top[i].szName, sizeof(m_kSnapshot.top[i].szName), "%.*s",
						(int) (sizeof(p->top[i].szName) - 1), p->top[i].szName);
			}

			for (int i = 0; i < (int) m_kSnapshot.bRankCount; ++i)
			{
				m_kSnapshot.rank[i].dwPID = p->rank[i].dwPID;
				m_kSnapshot.rank[i].iScore = p->rank[i].iScore;
			}

			m_kSnapshot.tReceived = get_global_time();
			ApplySnapshot();
			break;

		case ORB_EVENT_SUB_RESULT:
			if (IsMaster())
				return;	// master zaten yerelde bildirdi

			sys_log(0, "ORB_EVENT: odul sonucu alindi eid %u katilimci %u", p->dwEventID, p->dwParticipants);
			NotifyWinners(p->dwEventID);
			break;

		default:
			sys_err("ORB_EVENT: bilinmeyen P2P alt basligi %d", (int) p->bSub);
			break;
	}
}

void COrbEventManager::ApplySnapshot()
{
	if (m_kSnapshot.tReceived == 0)
		return;

	// hazir oyuncular (oturum olmayabilir: tur bitmis, final liste gidiyor)
	std::vector<DWORD> vecStale;

	for (std::map<DWORD, DWORD>::iterator it = m_mapReady.begin(); it != m_mapReady.end(); ++it)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);

		if (!ch || (DWORD) ch->GetVID() != it->second || !ch->GetDesc())
		{
			vecStale.push_back(it->first);
			continue;
		}

		std::map<DWORD, TOrbSession>::const_iterator itSession = m_mapSessions.find(it->first);
		SendSnapshotTo(ch, itSession != m_mapSessions.end() ? &itSession->second : nullptr);
	}

	for (size_t i = 0; i < vecStale.size(); ++i)
		m_mapReady.erase(vecStale[i]);
}

void COrbEventManager::SendSnapshotTo(LPCHARACTER ch, const TOrbSession * pSession)
{
	if (!ch || !ch->GetDesc() || m_kSnapshot.tReceived == 0)
		return;

	const time_t tNow = get_global_time();
	const int iRemain = (m_bActive && m_tRoundEnd > tNow) ? (int) (m_tRoundEnd - tNow) : 0;

	// orb_top <kalanSn>#<sira>|<isim>|<puan>;...  (isim <=16, toplam < ORB_EVENT_LINE_MAX)
	char szLine[ORB_EVENT_LINE_MAX + 1];
	int iLen = snprintf(szLine, sizeof(szLine), "orb_top %d#", iRemain);

	for (int i = 0; i < (int) m_kSnapshot.bTopCount && i < ORB_EVENT_SNAP_TOP_MAX; ++i)
	{
		char szEntry[64];
		const int iEntryLen = snprintf(szEntry, sizeof(szEntry), "%s%d|%.16s|%d",
				i == 0 ? "" : ";", i + 1, m_kSnapshot.top[i].szName, m_kSnapshot.top[i].iScore);

		if (iLen + iEntryLen >= ORB_EVENT_LINE_MAX)
			break;	// satir siniri: kalan satirlar dusurulur

		iLen += snprintf(szLine + iLen, sizeof(szLine) - iLen, "%s", szEntry);
	}

	SendCommandLine(ch, szLine);

	// orb_me <sira> <puan> <katilimci>
	const DWORD dwPID = ch->GetPlayerID();
	int iRank = 0;
	int iSnapScore = 0;

	for (int i = 0; i < (int) m_kSnapshot.bRankCount && i < ORB_EVENT_SNAP_RANK_MAX; ++i)
	{
		if (m_kSnapshot.rank[i].dwPID == dwPID)
		{
			iRank = i + 1;
			iSnapScore = m_kSnapshot.rank[i].iScore;
			break;
		}
	}

	// tur bittikten sonra (oturum silinmis) ilk 100 disindaki oyuncunun puani bilinmez:
	// orb_me GONDERME, client son bilinen degeri korur (aksi halde "Siralama disi - Puan 0" yazardi)
	if (!pSession && iRank == 0)
		return;

	int iScore = iSnapScore;

	if (pSession)
	{
		// ilk 100'de degilse (negatif/sifir puan dahil) gercek yerel toplam gosterilir
		const int iLocal = pSession->iScore + pSession->iBaseScore;

		if (iRank == 0 || iLocal > iScore)
			iScore = iLocal;
	}

	snprintf(szLine, sizeof(szLine), "orb_me %d %d %u", iRank, iScore, m_kSnapshot.dwParticipants);
	SendCommandLine(ch, szLine);
}

// ============================================================================
// odul dagitimi (master)
// ============================================================================

void COrbEventManager::CheckPendingRewards()
{
	// Saat notu: end_time StartRound/Distribute'ta game saatinden FROM_UNIXTIME(eid) ile yazilir ve burada
	// UNIX_TIMESTAMP(end_time) ile yine game saatine (get_global_time) gore okunur; FROM_UNIXTIME/UNIX_TIMESTAMP
	// ayni DB oturum saat diliminde gidis-donus tutarlidir, bu yuzden DB sunucu saati sapsa bile dagitim
	// bitis+60 sn'de olur. distributed_at=NOW() DB saatidir: game ve DB sunucu saatleri yine de NTP ile
	// senkron tutulmali (fark 60 sn altinda kalmali; bkz. sql/orb_event.sql basi).
	const DWORD dwNow = (DWORD) get_global_time();

	char szQuery[320];
	snprintf(szQuery, sizeof(szQuery),
			"SELECT event_id FROM player.orb_event WHERE state < 3 AND UNIX_TIMESTAMP(end_time) + 60 <= %u AND UNIX_TIMESTAMP(end_time) + 86400 >= %u",
			dwNow, dwNow);

	DBManager::instance().FuncSafeQuery(
		[](SQLMsg * pMsg)
		{
			if (!pMsg || pMsg->uiSQLErrno != 0 || !pMsg->Get() || !pMsg->Get()->pSQLResult)
				return;

			std::vector<DWORD> vecEventIDs;
			MYSQL_ROW row;

			while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
			{
				DWORD dwEventID = 0;

				if (row[0])
					str_to_number(dwEventID, row[0]);

				if (dwEventID != 0)
					vecEventIDs.push_back(dwEventID);
			}

			if (!vecEventIDs.empty())
				COrbEventManager::instance().OnPendingRewardsResult(vecEventIDs);
		},
		szQuery);
}

void COrbEventManager::OnPendingRewardsResult(const std::vector<DWORD> & vecEventIDs)
{
	if (!IsMaster())
		return;

	for (size_t i = 0; i < vecEventIDs.size(); ++i)
	{
		const DWORD dwEventID = vecEventIDs[i];

		if ((DWORD) quest::CQuestManager::instance().GetEventFlag("orb_event_cancel") == dwEventID)
			MarkCancelled(dwEventID);
		else
			Distribute(dwEventID);
	}
}

void COrbEventManager::MarkCancelled(DWORD dwEventID)
{
	char szQuery[256];
	snprintf(szQuery, sizeof(szQuery),
			"UPDATE player.orb_event SET state=4 WHERE event_id=%u AND state<3", dwEventID);

	std::unique_ptr<SQLMsg> pMsg = DBManager::instance().DirectSafeQuery(szQuery);

	if (pMsg && pMsg->uiSQLErrno == 0 && pMsg->Get() && pMsg->Get()->uiAffectedRows == 1)
		sys_log(0, "ORB_EVENT: tur iptal isaretlendi eid %u (odul yok)", dwEventID);
}

void COrbEventManager::Distribute(DWORD dwEventID)
{
	// 1) tum katilimcilar (LIMIT yok)
	std::vector<std::pair<DWORD, int> > vecRank;	// (pid, puan) sirali; yalniz puan > 0

	{
		char szQuery[320];
		snprintf(szQuery, sizeof(szQuery),
				"SELECT pid, SUM(score) AS sc, MAX(last_ts) AS lt FROM player.orb_event_score WHERE event_id=%u GROUP BY pid HAVING sc >= %d ORDER BY sc DESC, lt ASC, pid ASC",
				dwEventID, (int) ORB_EVENT_REWARD_MIN_SCORE);	// odul esigi: toplam >= ORB_EVENT_REWARD_MIN_SCORE

		std::unique_ptr<SQLMsg> pMsg = DBManager::instance().DirectSafeQuery(szQuery);

		if (!pMsg || pMsg->uiSQLErrno != 0 || !pMsg->Get())
		{
			sys_err("ORB_EVENT: dagitim siralama sorgusu basarisiz eid %u (sonraki dakika yeniden denenir)", dwEventID);
			return;
		}

		if (pMsg->Get()->pSQLResult)
		{
			MYSQL_ROW row;

			while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
			{
				DWORD dwPID = 0;
				int iScore = 0;

				if (row[0]) str_to_number(dwPID, row[0]);
				if (row[1]) str_to_number(iScore, row[1]);

				if (dwPID != 0 && iScore > 0 && iScore >= ORB_EVENT_REWARD_MIN_SCORE)
					vecRank.push_back(std::make_pair(dwPID, iScore));
			}
		}
	}

	// 2) katilimci yok: tur kapanir
	if (vecRank.empty())
	{
		char szQuery[256];
		snprintf(szQuery, sizeof(szQuery),
				"UPDATE player.orb_event SET state=3, participants=0, distributed_at=NOW() WHERE event_id=%u AND state<3", dwEventID);
		DBManager::instance().DirectSafeQuery(szQuery);
		sys_log(0, "ORB_EVENT: dagitim eid %u - katilimci yok, tur kapatildi", dwEventID);
		return;
	}

	// 3) siralar + adetler + dagitim jetonu
	DWORD dwToken = ((DWORD) number(1, 0x7fffffff)) ^ (DWORD) mother_port;

	if (dwToken == 0)
		dwToken = 1;

	const DWORD dwParticipants = (DWORD) vecRank.size();

	// 4) tek DirectSafeQuery, TAM 6 ifade
	std::string stQuery;
	stQuery.reserve(512 + vecRank.size() * 48);

	char szBuf[512];

	stQuery += "START TRANSACTION;";

	snprintf(szBuf, sizeof(szBuf),
			"INSERT IGNORE INTO player.orb_event (event_id, start_time, end_time, state) VALUES (%u, FROM_UNIXTIME(%u), FROM_UNIXTIME(%u), 0);",
			dwEventID, dwEventID, dwEventID + ORB_EVENT_DURATION_SEC);
	stQuery += szBuf;

	snprintf(szBuf, sizeof(szBuf),
			"UPDATE player.orb_event SET state=3, dist_token=%u, participants=%u, distributed_at=NOW() WHERE event_id=%u AND state<3;",
			dwToken, dwParticipants, dwEventID);
	stQuery += szBuf;

	snprintf(szBuf, sizeof(szBuf),
			"INSERT INTO player.orb_event_reward (event_id, pid, rank_no, score, reward_vnum, reward_count) SELECT %u, t.pid, t.r, t.s, %u, t.c FROM (",
			dwEventID, (DWORD) ORB_EVENT_REWARD_VNUM);
	stQuery += szBuf;

	for (size_t i = 0; i < vecRank.size(); ++i)
	{
		const DWORD dwRank = (DWORD) i + 1;
		const DWORD dwCount = (dwRank <= 3) ? ORB_EVENT_REWARD_TOP3 : (dwRank <= 50) ? ORB_EVENT_REWARD_TOP50 : ORB_EVENT_REWARD_REST;

		if (i == 0)
			snprintf(szBuf, sizeof(szBuf), "SELECT %u AS r, %u AS pid, %d AS s, %u AS c", dwRank, vecRank[i].first, vecRank[i].second, dwCount);
		else
			snprintf(szBuf, sizeof(szBuf), " UNION ALL SELECT %u, %u, %d, %u", dwRank, vecRank[i].first, vecRank[i].second, dwCount);

		stQuery += szBuf;
	}

	snprintf(szBuf, sizeof(szBuf), ") t JOIN player.orb_event e ON e.event_id = %u AND e.dist_token = %u;", dwEventID, dwToken);
	stQuery += szBuf;

	snprintf(szBuf, sizeof(szBuf),
			"INSERT INTO player.player_gift (owner_id, vnum, count) SELECT r.pid, r.reward_vnum, r.reward_count FROM player.orb_event_reward r JOIN player.orb_event e ON e.event_id = r.event_id AND e.dist_token = %u WHERE r.event_id = %u;",
			dwToken, dwEventID);
	stQuery += szBuf;

	stQuery += "COMMIT";

	std::unique_ptr<SQLMsg> pMsg = DBManager::instance().DirectSafeQuery(stQuery.c_str());

	// ara ifade hatasi uiSQLErrno'yu SET ETMEZ: sonuc sayisi zorunlu kontrol
	if (!pMsg || pMsg->uiSQLErrno != 0 || pMsg->vec_pkResult.size() != 6)
	{
		DBManager::instance().DirectQuery("ROLLBACK");
		sys_err("ORB_EVENT: dagitim transaction'i basarisiz eid %u (errno %u, sonuc %u/6) - ROLLBACK, sonraki dakika yeniden denenir",
				dwEventID, pMsg ? pMsg->uiSQLErrno : 0u, pMsg ? (unsigned) pMsg->vec_pkResult.size() : 0u);
		return;
	}

	if (pMsg->vec_pkResult[2]->uiAffectedRows != 1)
	{
		sys_log(0, "ORB_EVENT: dagitim eid %u baska bir core tarafindan zaten yapilmis (state>=3)", dwEventID);
		return;
	}

	sys_log(0, "ORB_EVENT: odul dagitildi eid %u katilimci %u jeton %u (vnum %u; 1-3:%d 4-50:%d 51+:%d)",
			dwEventID, dwParticipants, dwToken, (DWORD) ORB_EVENT_REWARD_VNUM,
			(int) ORB_EVENT_REWARD_TOP3, (int) ORB_EVENT_REWARD_TOP50, (int) ORB_EVENT_REWARD_REST);

	// 5) yerel bildirim + diger core'lara sonuc paketi + duyuru
	NotifyWinners(dwEventID);

	TPacketGGOrbEvent pkt;
	memset(&pkt, 0, sizeof(pkt));
	pkt.bHeader = HEADER_GG_ORB_EVENT;
	pkt.bSub = ORB_EVENT_SUB_RESULT;
	pkt.dwEventID = dwEventID;
	pkt.dwParticipants = dwParticipants;
	pkt.bTopCount = (BYTE) (vecRank.size() < 3 ? vecRank.size() : 3);

	for (int i = 0; i < (int) pkt.bTopCount; ++i)
	{
		pkt.top[i].dwPID = vecRank[i].first;
		pkt.top[i].iScore = vecRank[i].second;
	}

	// ilk uc isim
	{
		std::string stIn;

		for (int i = 0; i < (int) pkt.bTopCount; ++i)
		{
			snprintf(szBuf, sizeof(szBuf), "%s%u", i == 0 ? "" : ",", vecRank[i].first);
			stIn += szBuf;
		}

		std::string stNameQuery = "SELECT id, name FROM player.player WHERE id IN (" + stIn + ")";
		std::unique_ptr<SQLMsg> pMsgName = DBManager::instance().DirectSafeQuery(stNameQuery.c_str());

		if (pMsgName && pMsgName->uiSQLErrno == 0 && pMsgName->Get() && pMsgName->Get()->pSQLResult)
		{
			MYSQL_ROW row;

			while ((row = mysql_fetch_row(pMsgName->Get()->pSQLResult)) != nullptr)
			{
				DWORD dwPID = 0;

				if (row[0])
					str_to_number(dwPID, row[0]);

				for (int i = 0; i < (int) pkt.bTopCount; ++i)
					if (pkt.top[i].dwPID == dwPID)
						CopyName(pkt.top[i].szName, sizeof(pkt.top[i].szName), row[1]);
			}
		}
	}

	P2P_MANAGER::instance().Send(&pkt, sizeof(pkt));

	// ilk-3 genel duyurusu kullanici istegiyle KALDIRILDI (2026-10-13); tur basi/sonu duyurulari StartRound/EndRound'da
}

void COrbEventManager::NotifyWinners(DWORD dwEventID)
{
	char szQuery[256];
	snprintf(szQuery, sizeof(szQuery),
			"SELECT pid, rank_no, reward_count FROM player.orb_event_reward WHERE event_id=%u", dwEventID);

	DBManager::instance().FuncSafeQuery(
		[dwEventID](SQLMsg * pMsg)
		{
			if (!pMsg || pMsg->uiSQLErrno != 0 || !pMsg->Get() || !pMsg->Get()->pSQLResult)
				return;

			MYSQL_ROW row;
			DWORD dwNotified = 0;

			while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
			{
				DWORD dwPID = 0;
				DWORD dwRank = 0;
				DWORD dwCount = 0;

				if (row[0]) str_to_number(dwPID, row[0]);
				if (row[1]) str_to_number(dwRank, row[1]);
				if (row[2]) str_to_number(dwCount, row[2]);

				if (dwPID == 0)
					continue;

				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(dwPID);

				if (!ch || !ch->GetDesc())
					continue;

#ifdef GIFT_SYSTEM
				ch->RefreshGift();
#endif
				ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: %u. oldun, hediye kutuna %u adet odul gonderildi.", dwRank, dwCount);
				ch->ChatPacket(CHAT_TYPE_COMMAND, "orb_result %u %u", dwRank, dwCount);
				++dwNotified;
			}

			sys_log(0, "ORB_EVENT: kazanan bildirimi eid %u cevrimici %u", dwEventID, dwNotified);
		},
		szQuery);
}

// ============================================================================
// tick
// ============================================================================

void COrbEventManager::Tick()
{
	if (!m_bDBReady)
		return;

	++m_iTickCounter;

	const time_t tNow = get_global_time();
	const bool bSecond = (m_iTickCounter % ORB_TICKS_PER_SEC) == 0;

	// bayraklar saniyede bir okunur (ucuz map lookup); gecisler saniye hassasiyetinde
	if (bSecond)
	{
		bool bShouldBeActive = false;
		DWORD dwEventID = 0;
		time_t tEnd = 0;

		ComputeSchedule(tNow, bShouldBeActive, dwEventID, tEnd);

		if (bShouldBeActive)
		{
			if (!m_bActive || m_dwEventID != dwEventID)
			{
				if (m_bActive)
					EndRound();

				StartRound(dwEventID, tEnd);
			}
		}
		else if (m_bActive)
			EndRound();
	}

	if (m_bActive)
	{
		int iGenBudget = ORB_GEN_PER_TICK;

		for (std::map<DWORD, TOrbSession>::iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); ++it)
		{
			TOrbSession & s = it->second;

			if (s.dwVID == 0)
				continue;

			LPCHARACTER ch = FindOnline(s);

			if (!ch)
				continue;

			ProcessSession(s, ch, iGenBudget);
		}
	}

	if (!bSecond)
		return;

	if (m_bActive)
	{
		FlushScores();
		RelocationPass();
		BaseReadPass(tNow);
	}

	if (IsMaster())
	{
		const bool bPostWindow = (!m_bActive && m_tLastRoundEnd != 0 && tNow - m_tLastRoundEnd <= ORB_POST_POLL_SEC);

		if ((m_bActive || bPostWindow) && tNow - m_tLastPoll >= ORB_POLL_INTERVAL_SEC)
			PollSnapshot(tNow);

		if (m_tLastRewardCheck == 0 || tNow - m_tLastRewardCheck >= ORB_REWARD_CHECK_SEC)
		{
			m_tLastRewardCheck = tNow;
			CheckPendingRewards();
		}
	}
}

// ============================================================================
// GM komutu
// ============================================================================

void COrbEventManager::AdminCommand(LPCHARACTER ch, const char * szSub)
{
	if (!ch || !ch->GetDesc())
		return;

	if (!m_bDBReady)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: DB tablolari yok (sql/orb_event.sql uygulanmali).");
		return;
	}

	if (!szSub)
		szSub = "";

	quest::CQuestManager & q = quest::CQuestManager::instance();

	if (!strcmp(szSub, "start"))
	{
		// saatlik tur surerken test baslatilamaz: test onceligi saatlik turu bitirir, test bitince
		// ayni eid ile saatlik tur SIFIRDAN yeniden baslar ve mutlak flush bu core'un puanlarini ezerdi
		if (m_bActive && (int) m_dwEventID != q.GetEventFlag("orb_event_test"))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: saatlik tur zaten aktif (eid %u), test baslatilamaz; once /orb_admin stop veya cancel.", m_dwEventID);
			return;
		}

		const int iNow = (int) get_global_time();
		q.RequestSetEventFlag("orb_event_test", iNow);
		ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: test turu istendi (eid %d, tum core'lar 1 sn icinde baslar).", iNow);
		sys_log(0, "ORB_EVENT: GM %s test turu baslatti (eid %d)", ch->GetName(), iNow);
	}
	else if (!strcmp(szSub, "stop"))
	{
		if (!m_bActive)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: aktif tur yok.");
			return;
		}

		q.RequestSetEventFlag("orb_event_stop", (int) m_dwEventID);
		ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: tur %u durduruluyor (odul bitis+60 sn'de dagitilir).", m_dwEventID);
		sys_log(0, "ORB_EVENT: GM %s turu durdurdu (eid %u)", ch->GetName(), m_dwEventID);
	}
	else if (!strcmp(szSub, "cancel"))
	{
		if (!m_bActive)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: aktif tur yok.");
			return;
		}

		q.RequestSetEventFlag("orb_event_cancel", (int) m_dwEventID);

		// bayrak tek slotludur (sonraki bir cancel onu ezer): iptal karari HEMEN DB'ye yazilir;
		// CheckPendingRewards state<3 filtreler, Distribute UPDATE ... state<3 etkilenen satir !=1 ise
		// dagitmaz. Ayni core FIFO: StartRound INSERT IGNORE bu UPDATE'ten once islenir. Bayrak kontrolu yedek kalir.
		{
			char szQuery[160];
			snprintf(szQuery, sizeof(szQuery), "UPDATE player.orb_event SET state=4 WHERE event_id=%u AND state<3", m_dwEventID);
			DBManager::instance().AsyncSafeQuery(szQuery);
		}

		ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: tur %u iptal ediliyor (ODUL YOK).", m_dwEventID);
		sys_log(0, "ORB_EVENT: GM %s turu iptal etti (eid %u)", ch->GetName(), m_dwEventID);
	}
	else if (!strcmp(szSub, "status"))
	{
		const time_t tNow = get_global_time();
		const int iRemain = (m_bActive && m_tRoundEnd > tNow) ? (int) (m_tRoundEnd - tNow) : 0;
		DWORD dwOnline = 0;

		for (std::map<DWORD, TOrbSession>::const_iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); ++it)
			if (it->second.dwVID != 0)
				++dwOnline;

		ch->ChatPacket(CHAT_TYPE_INFO, "Orb Rush: %s - eid %u - kalan %d sn", m_bActive ? "AKTIF" : "KAPALI", m_bActive ? m_dwEventID : m_dwLastEventID, iRemain);
		ch->ChatPacket(CHAT_TYPE_INFO, "Oturum %u (cevrimici %u) - hazir %u - master %s - program bayragi %d",
				(unsigned) m_mapSessions.size(), dwOnline, (unsigned) m_mapReady.size(),
				IsMaster() ? "evet" : "hayir", q.GetEventFlag("orb_event"));
		ch->ChatPacket(CHAT_TYPE_INFO, "Bayraklar: test %d - stop %d - cancel %d - snapshot eid %u katilimci %u",
				q.GetEventFlag("orb_event_test"), q.GetEventFlag("orb_event_stop"), q.GetEventFlag("orb_event_cancel"),
				m_kSnapshot.dwEventID, m_kSnapshot.dwParticipants);

		std::map<DWORD, TOrbSession>::const_iterator itMe = m_mapSessions.find(ch->GetPlayerID());

		if (itMe != m_mapSessions.end())
		{
			int iValid = 0;

			for (int i = 0; i < ORB_EVENT_ORB_COUNT; ++i)
				if (itMe->second.aOrbs[i].valid)
					++iValid;

			ch->ChatPacket(CHAT_TYPE_INFO, "Senin oturumun: puan %d (mavi %u beyaz %u sari %u) + diger core %d - kure %d/%d - butce %.0f",
					itMe->second.iScore, itMe->second.dwBlue, itMe->second.dwWhite, itMe->second.dwGold, itMe->second.iBaseScore,
					iValid, (int) ORB_EVENT_ORB_COUNT, itMe->second.fBudget);
		}
	}
	else
		ch->ChatPacket(CHAT_TYPE_INFO, "Kullanim: /orb_admin start|stop|cancel|status");
}

// ============================================================================
// komutlar (cmd.cpp tablosu: orb_ready GM_PLAYER, orb_admin GM_IMPLEMENTOR)
// ============================================================================

void do_orb_ready(LPCHARACTER ch, const char * argument, int cmd, int subcmd)
{
	COrbEventManager::instance().OnReady(ch);
}

void do_orb_admin(LPCHARACTER ch, const char * argument, int cmd, int subcmd)
{
	char szSub[64];
	one_argument(argument, szSub, sizeof(szSub));
	COrbEventManager::instance().AdminCommand(ch, szSub);
}

#endif // ENABLE_ORB_EVENT
