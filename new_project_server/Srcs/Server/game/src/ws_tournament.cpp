#include "stdafx.h"

#ifdef ENABLE_WS_TOURNAMENT

#include "constants.h"
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "desc.h"
#include "desc_manager.h"
#include "buffer_manager.h"
#include "char.h"
#include "char_manager.h"
#include "party.h"
#include "p2p.h"
#include "db.h"
#include "log.h"
#include "event.h"
#include "questmanager.h"
#include "sectree_manager.h"
#include "start_position.h"
#include "arena.h"
#include "cmd.h"
#include "ws_tournament.h"

// ============================================================================
// tick eventi
// ============================================================================

EVENTINFO(TWSTickEventInfo)
{
	int iDummy;

	TWSTickEventInfo()
	: iDummy(0)
	{
	}
};

EVENTFUNC(ws_tournament_tick_event)
{
	if (event == nullptr || event->info == nullptr)
		return 0;

	// Tick() 0 donerse manager kendi pointer'ini zaten temizlemistir (UAF onlemi)
	return CWSTournamentManager::instance().Tick();
}

// ============================================================================
// kurulum / yikim
// ============================================================================

CWSTournamentManager::CWSTournamentManager()
	: m_iState(WS_STATE_IDLE)
	, m_bDBReady(false)
	, m_dwTournamentDBID(0)
	, m_iRound(0)
	, m_tRegDeadline(0)
	, m_tLastAnnounce(0)
	, m_tLastSync(0)
	, m_tLastResolve(0)
	, m_pkTickEvent(nullptr)
	, m_tSnapshotAt(0)
	, m_bBracketDirty(false)
	, m_tLastBracketSync(0)
{
	memset(&m_kSnapshot, 0, sizeof(m_kSnapshot));
}

CWSTournamentManager::~CWSTournamentManager()
{
}

void CWSTournamentManager::Initialize()
{
	// tablo varligi kontrolu: COUNT sorgusu tablo varsa HER ZAMAN 1 satir doner,
	// 0 satir = sorgu hata verdi = sql/ws_tournament.sql uygulanmamis
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT COUNT(*) FROM player.ws_tournament;"));
		if (pMsg->Get()->uiNumRows == 0)
		{
			sys_err("WS_TOURNAMENT: player.ws_tournament tablosu yok - sql/ws_tournament.sql uygulanmali. Sistem devre disi.");
			m_bDBReady = false;
			return;
		}
	}
	m_bDBReady = true;

	// Boot recovery: yarim kalmis turnuvalari iptal et, ucretleri claim'e yaz.
	// Tum core'lar calistirir; satir bazli kosullu UPDATE sayesinde temizligi
	// yalnizca UPDATE'i kazanan tek core yapar (yarissiz).
	std::vector<DWORD> vecStale;
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT id FROM player.ws_tournament WHERE status IN (1, 2);"));
		if (pMsg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
			{
				DWORD dwID = 0;
				str_to_number(dwID, row[0]);
				if (dwID != 0)
					vecStale.push_back(dwID);
			}
		}
	}

	for (const DWORD dwID : vecStale)
	{
		// ucret/odul kaldirildigi icin iade gerekmez; yarim kalan turnuva sadece iptal isaretlenir
		std::unique_ptr<SQLMsg> pMsgUp(DBManager::instance().DirectQuery(
			"UPDATE player.ws_tournament SET status = 4, finished_at = NOW() WHERE id = %u AND status IN (1, 2);", dwID));

		if (pMsgUp->Get()->uiAffectedRows == 1)
			sys_log(0, "WS_TOURNAMENT: boot recovery - turnuva %u iptal isaretlendi", dwID);
	}
}

void CWSTournamentManager::Destroy()
{
	if (m_pkTickEvent != nullptr)
		event_cancel(&m_pkTickEvent);

	m_vecEntries.clear();
	m_vecMatches.clear();
	m_mapPendingReg.clear();
	m_mapPrepLock.clear();
	m_iState = WS_STATE_IDLE;
}

bool CWSTournamentManager::IsHostCore() const
{
	return SECTREE_MANAGER::instance().GetMap(WS_TOURNAMENT_MAP_INDEX) != nullptr;
}

// ============================================================================
// yardimcilar
// ============================================================================

int CWSTournamentManager::GetFlagOr(const char * c_szFlag, int iDefault)
{
	const int iValue = quest::CQuestManager::instance().GetEventFlag(c_szFlag);
	return (iValue > 0) ? iValue : iDefault;
}

long long CWSTournamentManager::ClampClaim(long long llGold)
{
	if (llGold < 0)
		return 0;
	if (llGold > WS_CLAIM_MAX)
		return WS_CLAIM_MAX;
	return llGold;
}

TWSEntry * CWSTournamentManager::FindEntry(DWORD dwPID)
{
	for (auto & e : m_vecEntries)
		if (e.dwPID == dwPID)
			return &e;
	return nullptr;
}

const TWSEntry * CWSTournamentManager::FindEntry(DWORD dwPID) const
{
	for (const auto & e : m_vecEntries)
		if (e.dwPID == dwPID)
			return &e;
	return nullptr;
}

TWSEntry * CWSTournamentManager::FindEntryByName(const char * c_szName)
{
	for (auto & e : m_vecEntries)
		if (strcasecmp(e.szName, c_szName) == 0)
			return &e;
	return nullptr;
}

TWSMatch * CWSTournamentManager::FindActiveMatchByPair(DWORD dwPID1, DWORD dwPID2)
{
	for (auto & m : m_vecMatches)
	{
		if (m.iState == WS_MATCH_DONE)
			continue;
		if ((m.dwPIDA == dwPID1 && m.dwPIDB == dwPID2) || (m.dwPIDA == dwPID2 && m.dwPIDB == dwPID1))
			return &m;
	}
	return nullptr;
}

TWSMatch * CWSTournamentManager::FindActiveMatchByPID(DWORD dwPID)
{
	for (auto & m : m_vecMatches)
	{
		if (m.iState == WS_MATCH_DONE)
			continue;
		if (m.dwPIDA == dwPID || m.dwPIDB == dwPID)
			return &m;
	}
	return nullptr;
}

int CWSTournamentManager::CountAlive() const
{
	int iCount = 0;
	for (const auto & e : m_vecEntries)
		if (e.bAlive)
			++iCount;
	return iCount;
}

int CWSTournamentManager::GetFreeRingHint() const
{
	int iRings = CArenaManager::instance().GetArenaCount(WS_TOURNAMENT_MAP_INDEX);
	if (iRings <= 0)
		iRings = 1;

	int iBusy = 0;
	for (const auto & m : m_vecMatches)
		if (m.iState == WS_MATCH_SUMMON || m.iState == WS_MATCH_RUNNING || m.iState == WS_MATCH_PAUSED)
			++iBusy;	// PAUSED: arena canli kaldigi icin ring fiilen dolu

	return iRings - iBusy;
}

void CWSTournamentManager::StartTickEvent()
{
	if (m_pkTickEvent != nullptr)
		return;

	TWSTickEventInfo * info = AllocEventInfo<TWSTickEventInfo>();
	m_pkTickEvent = event_create(ws_tournament_tick_event, info, PASSES_PER_SEC(WS_TICK_SECONDS));
}

void CWSTournamentManager::SendGG(TPacketGGWSTournament & p)
{
	p.bHeader = HEADER_GG_WS_TOURNAMENT;
	P2P_MANAGER::instance().Send(&p, sizeof(p));
}

void CWSTournamentManager::SendStateSync()
{
	if (!IsHostCore())
		return;

	TPacketGGWSTournament p;
	memset(&p, 0, sizeof(p));
	p.bSubHeader = WS_GG_STATE;
	p.bState = (BYTE) m_iState;
	p.bMinLevel = (BYTE) m_kConfig.iMinLevel;
	p.bMaxLevel = (BYTE) m_kConfig.iMaxLevel;
	p.bJobFilter = (BYTE) m_kConfig.iJobFilter;
	p.bSetCount = (BYTE) m_kConfig.iSetCount;
	p.bMatchMinutes = (BYTE) m_kConfig.iMatchMinutes;
	p.llGold = m_kConfig.llFee;

	if (m_iState == WS_STATE_REGISTRATION)
	{
		p.iValue1 = (int) m_vecEntries.size();
		const time_t tNow = get_global_time();
		p.iValue2 = (m_tRegDeadline > tNow) ? (int)(m_tRegDeadline - tNow) : 0;
	}
	else if (m_iState == WS_STATE_RUNNING)
	{
		p.iValue1 = CountAlive();
		p.iValue2 = m_iRound;
	}

	SendGG(p);
}

void CWSTournamentManager::BuildAndBroadcastBracket()
{
	if (!IsHostCore())
		return;

	TPacketGGWSBracket p;
	memset(&p, 0, sizeof(p));
	p.bHeader = HEADER_GG_WS_BRACKET;
	p.bState = (BYTE) m_iState;
	p.bRound = (BYTE) m_iRound;
	p.bMinLevel = (BYTE) m_kConfig.iMinLevel;
	p.bMaxLevel = (BYTE) m_kConfig.iMaxLevel;
	p.bJobFilter = (BYTE) m_kConfig.iJobFilter;
	p.bSetCount = (BYTE) m_kConfig.iSetCount;
	p.bMatchMinutes = (BYTE) m_kConfig.iMatchMinutes;
	p.llFee = m_kConfig.llFee;
	p.llPool = GetPrizePool();

	const time_t tNow = get_global_time();
	p.iSecondsLeft = (m_iState == WS_STATE_REGISTRATION && m_tRegDeadline > tNow) ? (int) (m_tRegDeadline - tNow) : 0;

	int iEntry = 0;
	for (const auto & e : m_vecEntries)
	{
		if (iEntry >= WS_SYNC_MAX_ENTRIES)
			break;
		p.aEntries[iEntry].dwPID = e.dwPID;
		strlcpy(p.aEntries[iEntry].szName, e.szName, sizeof(p.aEntries[iEntry].szName));
		p.aEntries[iEntry].bLevel = e.bLevel;
		p.aEntries[iEntry].bJob = e.bJob;
		p.aEntries[iEntry].bAlive = e.bAlive ? 1 : 0;
		++iEntry;
	}
	p.bEntryCount = (BYTE) iEntry;

	int iMatch = 0;
	for (const auto & m : m_vecMatches)
	{
		if (iMatch >= WS_SYNC_MAX_MATCHES)
			break;
		const TWSEntry * pA = FindEntry(m.dwPIDA);
		const TWSEntry * pB = FindEntry(m.dwPIDB);
		p.aMatches[iMatch].dwPIDA = m.dwPIDA;
		p.aMatches[iMatch].dwPIDB = m.dwPIDB;
		strlcpy(p.aMatches[iMatch].szNameA, pA ? pA->szName : "?", sizeof(p.aMatches[iMatch].szNameA));
		strlcpy(p.aMatches[iMatch].szNameB, pB ? pB->szName : "?", sizeof(p.aMatches[iMatch].szNameB));
		p.aMatches[iMatch].bRound = (BYTE) m.iRound;
		p.aMatches[iMatch].bState = (BYTE) m.iState;
		p.aMatches[iMatch].bResult = (BYTE) m.iResult;
		++iMatch;
	}
	p.bMatchCount = (BYTE) iMatch;

	m_bBracketDirty = false;
	m_tLastBracketSync = get_global_time();

	ApplySnapshot(&p);
	P2P_MANAGER::instance().Send(&p, sizeof(p));
}

void CWSTournamentManager::ApplySnapshot(const TPacketGGWSBracket * p)
{
	if (p == nullptr)
		return;

	memcpy(&m_kSnapshot, p, sizeof(m_kSnapshot));
	m_kSnapshot.bHeader = HEADER_GG_WS_BRACKET;

	// bozuk/build-skew peer'e karsi sayac sertlestirmesi (wSize/dongu tutarliligi)
	if (m_kSnapshot.bEntryCount > WS_SYNC_MAX_ENTRIES)
		m_kSnapshot.bEntryCount = WS_SYNC_MAX_ENTRIES;
	if (m_kSnapshot.bMatchCount > WS_SYNC_MAX_MATCHES)
		m_kSnapshot.bMatchCount = WS_SYNC_MAX_MATCHES;

	m_tSnapshotAt = get_global_time();
}

void CWSTournamentManager::OnClientInfoRequest(LPCHARACTER ch)
{
	if (ch == nullptr || ch->GetDesc() == nullptr)
		return;

	// host cokup IDLE'a donmusse diger core'lar bayat RUNNING goruntusunu suresiz gostermesin
	// (host duzenli heartbeat yayar; 90 sn sessizlik = bayat say)
	static const TPacketGGWSBracket s_kEmptySnapshot = {};
	const bool bStale = (!IsHostCore() && m_kSnapshot.bState != WS_STATE_IDLE
			&& m_tSnapshotAt != 0 && get_global_time() - m_tSnapshotAt > 90);
	const TPacketGGWSBracket & s = bStale ? s_kEmptySnapshot : m_kSnapshot;

	TPacketGCWSTournament pack;
	memset(&pack, 0, sizeof(pack));
	pack.bHeader = HEADER_GC_WS_TOURNAMENT;
	pack.bState = s.bState;
	pack.bRound = s.bRound;
	pack.bEntryCount = s.bEntryCount;
	pack.bMatchCount = s.bMatchCount;
	pack.bMinLevel = s.bMinLevel;
	pack.bMaxLevel = s.bMaxLevel;
	pack.bJobFilter = s.bJobFilter;
	pack.bSetCount = s.bSetCount;
	pack.bMatchMinutes = s.bMatchMinutes;
	pack.llFee = s.llFee;
	pack.llPool = s.llPool;

	// kalan sure: snapshot uzerinden gecen zamani dus
	if (s.bState == WS_STATE_REGISTRATION && m_tSnapshotAt != 0)
	{
		const int iLeft = s.iSecondsLeft - (int) (get_global_time() - m_tSnapshotAt);
		pack.iSecondsLeft = (iLeft > 0) ? iLeft : 0;
	}

	const DWORD dwPID = ch->GetPlayerID();
	pack.bMyStatus = 0;
	for (int i = 0; i < (int) s.bEntryCount && i < WS_SYNC_MAX_ENTRIES; ++i)
	{
		if (s.aEntries[i].dwPID != dwPID)
			continue;
		pack.bMyStatus = s.aEntries[i].bAlive ? 1 : 2;
		break;
	}
	if (pack.bMyStatus == 1)
	{
		for (int i = 0; i < (int) s.bMatchCount && i < WS_SYNC_MAX_MATCHES; ++i)
		{
			if ((s.aMatches[i].dwPIDA == dwPID || s.aMatches[i].dwPIDB == dwPID) && s.aMatches[i].bState != WS_MATCH_DONE)
			{
				pack.bMyStatus = 3;
				break;
			}
		}
	}

	pack.wSize = (WORD) (sizeof(pack) + (int) s.bEntryCount * sizeof(TWSTournamentEntryInfo) + (int) s.bMatchCount * sizeof(TWSTournamentMatchInfo));

	TEMP_BUFFER buf;
	buf.write(&pack, sizeof(pack));

	for (int i = 0; i < (int) s.bEntryCount && i < WS_SYNC_MAX_ENTRIES; ++i)
	{
		TWSTournamentEntryInfo kInfo;
		memset(&kInfo, 0, sizeof(kInfo));
		strlcpy(kInfo.szName, s.aEntries[i].szName, sizeof(kInfo.szName));
		kInfo.bLevel = s.aEntries[i].bLevel;
		kInfo.bJob = s.aEntries[i].bJob;
		kInfo.bAlive = s.aEntries[i].bAlive;
		buf.write(&kInfo, sizeof(kInfo));
	}

	for (int i = 0; i < (int) s.bMatchCount && i < WS_SYNC_MAX_MATCHES; ++i)
	{
		TWSTournamentMatchInfo kInfo;
		memset(&kInfo, 0, sizeof(kInfo));
		strlcpy(kInfo.szNameA, s.aMatches[i].szNameA, sizeof(kInfo.szNameA));
		strlcpy(kInfo.szNameB, s.aMatches[i].szNameB, sizeof(kInfo.szNameB));
		kInfo.bRound = s.aMatches[i].bRound;
		kInfo.bState = s.aMatches[i].bState;
		kInfo.bResult = s.aMatches[i].bResult;
		buf.write(&kInfo, sizeof(kInfo));
	}

	ch->GetDesc()->Packet(buf.read_peek(), buf.size());
}

void CWSTournamentManager::AnnounceAll(const char * c_szFormat, ...)
{
	char szBuf[CHAT_MAX_LEN + 1];

	va_list args;
	va_start(args, c_szFormat);
	vsnprintf(szBuf, sizeof(szBuf), c_szFormat, args);
	va_end(args);

	BroadcastNotice(szBuf);
}

const char * CWSTournamentManager::TextForPlayerMsg(int iMsgCode)
{
	switch (iMsgCode)
	{
		case WS_MSG_WALKOVER_WIN:	return "WS: Rakibin maca gelmedi, hukmen kazandin!";
		case WS_MSG_WALKOVER_LOSS:	return "WS: Macina gelmedigin icin hukmen kaybettin ve elendin.";
		case WS_MSG_DOUBLE_LOSS:	return "WS: Mac sonuclanamadi - iki taraf da elendi (cift eleme).";
		case WS_MSG_DQ:				return "WS: Turnuvadan diskalifiye edildin.";
		case WS_MSG_CANCEL_REFUND:	return "WS: Turnuva iptal edildi.";
		case WS_MSG_MATCH_LOSS:		return "WS: Maci kaybettin ve turnuvadan elendin.";
		case WS_MSG_MATCH_WIN:		return "WS: Maci kazandin! Sonraki turu bekle.";
		case WS_MSG_BYE:			return "WS: Bu turda rakipsizsin, bir ust tura yukseldin.";
		case WS_MSG_CHAMPION:		return "WS: TEBRIKLER! Turnuvanin sampiyonu oldun!";
		case WS_MSG_UNREG_OK:		return "WS: Kaydin iptal edildi.";
		case WS_MSG_UNREG_FAIL:		return "WS: Kayit iptali yapilamadi (kayit bulunamadi veya kayit donemi kapandi).";
	}
	return "WS: Turnuva bildirimi.";
}

const char * CWSTournamentManager::TextForRegResult(int iCode)
{
	switch (iCode)
	{
		case WS_REG_OK:				return "Kaydin alindi. Turnuva duyurularini takip et!";
		case WS_REG_ERR_CLOSED:		return "Su anda acik kayit donemi yok.";
		case WS_REG_ERR_FULL:		return "Turnuva kontenjani dolu.";
		case WS_REG_ERR_DUP_PID:	return "Bu karakter zaten kayitli.";
		case WS_REG_ERR_DUP_ACCOUNT:return "Bu hesaptan zaten bir kayit var.";
		case WS_REG_ERR_LEVEL:		return "Seviyen bu turnuvaya uygun degil.";
		case WS_REG_ERR_JOB:		return "Sinifin bu turnuvaya uygun degil.";
		case WS_REG_ERR_GOLD:		return "Kayit ucreti icin yeterli yang yok.";	// ucret kaldirildi, ulasilmaz
		case WS_REG_ERR_GM:			return "GM karakterleri turnuvaya katilamaz.";
		case WS_REG_ERR_DB:			return "Kayit sirasinda bir hata olustu, tekrar dene.";
		case WS_REG_ERR_IP:			return "Ayni IP adresinden zaten bir kayit var.";
	}
	return "Bilinmeyen kayit hatasi.";
}

void CWSTournamentManager::MsgLocal(LPCHARACTER ch, int iMsgCode)
{
	if (ch != nullptr)
		ch->ChatPacket(CHAT_TYPE_INFO, "%s", TextForPlayerMsg(iMsgCode));
}

void CWSTournamentManager::MsgToPlayer(DWORD dwPID, int iMsgCode)
{
	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(dwPID);
	if (ch != nullptr)
	{
		MsgLocal(ch, iMsgCode);
		return;
	}

	TPacketGGWSTournament p;
	memset(&p, 0, sizeof(p));
	p.bSubHeader = WS_GG_PLAYER_MSG;
	p.dwPID = dwPID;
	p.iValue1 = iMsgCode;
	SendGG(p);
}

// ============================================================================
// DB yardimcilari
// ============================================================================

void CWSTournamentManager::DBUpdateTournamentStatus(int iStatus)
{
	if (!m_bDBReady || m_dwTournamentDBID == 0)
		return;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"UPDATE player.ws_tournament SET status = %d, finished_at = NOW() WHERE id = %u;", iStatus, m_dwTournamentDBID));
}

void CWSTournamentManager::DBUpdateEntryStatus(DWORD dwPID, int iStatus)
{
	if (!m_bDBReady || m_dwTournamentDBID == 0)
		return;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"UPDATE player.ws_entry SET status = %d WHERE tournament_id = %u AND pid = %u;", iStatus, m_dwTournamentDBID, dwPID));
}

void CWSTournamentManager::DBUpdateMatch(const TWSMatch & m)
{
	if (!m_bDBReady || m.dwDBID == 0)
		return;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"UPDATE player.ws_match SET result = %d, reason = %d, damage_a = %lld, damage_b = %lld, ended_at = NOW() WHERE id = %u;",
		m.iResult, m.iReason, m.llDamageA, m.llDamageB, m.dwDBID));
}

// ============================================================================
// para / claim akisi
// ============================================================================

void CWSTournamentManager::InsertClaim(DWORD dwAID, DWORD dwPID, long long llGold, const char * c_szReason)
{
	if (!m_bDBReady || dwAID == 0)
		return;

	llGold = ClampClaim(llGold);
	if (llGold <= 0)
		return;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"INSERT INTO player.ws_claim (account_id, pid, gold, reason) VALUES (%u, %u, %lld, '%s');",
		dwAID, dwPID, llGold, c_szReason));

	if (pMsg->Get()->uiAffectedRows != 1)
		sys_err("WS_TOURNAMENT: claim yazilamadi! aid=%u pid=%u gold=%lld reason=%s", dwAID, dwPID, llGold, c_szReason);
	else
		sys_log(0, "WS_TOURNAMENT: claim yazildi aid=%u pid=%u gold=%lld reason=%s", dwAID, dwPID, llGold, c_szReason);
}

void CWSTournamentManager::InsertPrizeClaims(DWORD dwAID, DWORD dwPID, long long llTotal, const char * c_szReason)
{
	// tek claim tavani WS_CLAIM_MAX (GOLD_MAX guvenligi): buyuk oduller parcalara
	// bolunur, fazlalik SESSIZCE YAKILMAZ
	while (llTotal > 0)
	{
		const long long llPart = (llTotal > WS_CLAIM_MAX) ? WS_CLAIM_MAX : llTotal;
		InsertClaim(dwAID, dwPID, llPart, c_szReason);
		llTotal -= llPart;
	}
}

void CWSTournamentManager::NotifyClaim(DWORD dwPID, DWORD dwAID)
{
	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(dwPID);
	if (ch != nullptr)
	{
		ProcessClaims(ch);
		return;
	}

	TPacketGGWSTournament p;
	memset(&p, 0, sizeof(p));
	p.bSubHeader = WS_GG_CLAIM_NOTIFY;
	p.dwPID = dwPID;
	p.dwAID = dwAID;
	SendGG(p);
}

void CWSTournamentManager::ProcessClaims(LPCHARACTER ch)
{
	if (ch == nullptr || ch->GetDesc() == nullptr || !m_bDBReady)
		return;

	const DWORD dwAID = ch->GetDesc()->GetAccountTable().id;
	if (dwAID == 0)
		return;

	// CONFIRM'i kaybolmus emanet ucretlerini (status=2, 120sn+) odenebilir iadeye cevir
	{
		std::unique_ptr<SQLMsg> pMsgSweep(DBManager::instance().DirectQuery(
			"UPDATE player.ws_claim SET status = 0, reason = 'kayit-emanet-iade' "
			"WHERE account_id = %u AND status = 2 AND created_at < DATE_SUB(NOW(), INTERVAL 120 SECOND);", dwAID));
	}

	std::vector<std::pair<DWORD, long long> > vecClaims;
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"SELECT id, gold FROM player.ws_claim WHERE account_id = %u AND status = 0 ORDER BY id LIMIT 20;", dwAID));

		if (pMsg->Get()->uiNumRows == 0)
			return;

		MYSQL_ROW row;
		while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
		{
			DWORD dwClaimID = 0;
			str_to_number(dwClaimID, row[0]);
			const long long llGold = atoll(row[1]);
			if (dwClaimID != 0)
				vecClaims.emplace_back(dwClaimID, llGold);
		}
	}

	for (const auto & kClaim : vecClaims)
	{
		const long long llGold = ClampClaim(kClaim.second);

		if (llGold <= 0)
		{
			// bos/gecersiz claim'i kapat
			std::unique_ptr<SQLMsg> pMsgZero(DBManager::instance().DirectQuery(
				"UPDATE player.ws_claim SET status = 1, claimed_at = NOW() WHERE id = %u AND status = 0;", kClaim.first));
			continue;
		}

		// odeme oncesi tasma kontrolu: PointChange tasmada SESSIZCE hicbir sey vermez
		if ((long long) ch->GetGold() + llGold >= (long long) GOLD_MAX)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Bekleyen %lld yang odul/iaden var ama yang limitin dolu. Yer actiginda tekrar giris yap.", llGold);
			break;
		}

		// idempotent odeme kapisi: satiri yalnizca BIR core kapatabilir
		std::unique_ptr<SQLMsg> pMsgPay(DBManager::instance().DirectQuery(
			"UPDATE player.ws_claim SET status = 1, claimed_at = NOW() WHERE id = %u AND status = 0;", kClaim.first));

		if (pMsgPay->Get()->uiAffectedRows != 1)
			continue;	// baska yerde odendi

		ch->PointChange(POINT_GOLD, (int) llGold);
		ch->SaveReal();	// crash-dupe penceresini kapat: alinan parayi hemen diske yaz
		ch->ChatPacket(CHAT_TYPE_INFO, "WS: %lld yang hesabina gecti (turnuva odul/iade).", llGold);
		sys_log(0, "WS_TOURNAMENT: claim odendi id=%u aid=%u pid=%u gold=%lld", kClaim.first, dwAID, ch->GetPlayerID(), llGold);
	}
}

void CWSTournamentManager::RefundAllEntries(const char * c_szReason)
{
	// satir-bazli kapi: her giris icin once refunded=1 isaretle (yalniz bir kez gecer),
	// sonra claim yaz. Crash penceresi tek satirla sinirli kalir; ayni satir icin
	// cift claim yapisal olarak imkansiz (SafeTrade ilkesi: dupe > kayip).
	for (auto & e : m_vecEntries)
	{
		if (e.bRefunded)
			continue;

		e.bRefunded = true;

		bool bMark = true;
		if (m_bDBReady && m_dwTournamentDBID != 0)
		{
			std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"UPDATE player.ws_entry SET refunded = 1 WHERE tournament_id = %u AND pid = %u AND refunded = 0;",
				m_dwTournamentDBID, e.dwPID));
			bMark = (pMsg->Get()->uiAffectedRows == 1);
		}

		if (bMark)
		{
			InsertClaim(e.dwAID, e.dwPID, m_kConfig.llFee, c_szReason);
			MsgToPlayer(e.dwPID, WS_MSG_CANCEL_REFUND);
			NotifyClaim(e.dwPID, e.dwAID);
		}
	}
}

long long CWSTournamentManager::GetPrizePool() const
{
	long long llPool = 0;
	for (const auto & e : m_vecEntries)
		if (!e.bRefunded)
			llPool += m_kConfig.llFee;
	return llPool;
}

// ============================================================================
// kayit akisi
// ============================================================================

int CWSTournamentManager::CheckRegistration(DWORD dwPID, DWORD dwAID, BYTE bLevel, BYTE bJob, const char * c_szIP) const
{
	if (m_iState != WS_STATE_REGISTRATION)
		return WS_REG_ERR_CLOSED;

	// snapshot dizisi WS_SYNC_MAX_ENTRIES ile sinirli; kontenjan da ayni tavana bagli
	const int iMaxPlayers = MINMAX(2, GetFlagOr("ws_max_players", 64), WS_SYNC_MAX_ENTRIES);
	if ((int) (m_vecEntries.size() + m_mapPendingReg.size()) >= iMaxPlayers)
		return WS_REG_ERR_FULL;

	// ayni IP filtresi (ws_allow_same_ip=1 ile kapatilabilir; ev/kafe icin GM karari)
	if (c_szIP != nullptr && c_szIP[0] != '\0' && quest::CQuestManager::instance().GetEventFlag("ws_allow_same_ip") == 0)
	{
		for (const auto & e : m_vecEntries)
			if (strcmp(e.szIP, c_szIP) == 0)
				return WS_REG_ERR_IP;

		for (const auto & kPending : m_mapPendingReg)
			if (strcmp(kPending.second.szIP, c_szIP) == 0)
				return WS_REG_ERR_IP;
	}

	if (FindEntry(dwPID) != nullptr)
		return WS_REG_ERR_DUP_PID;

	if (m_mapPendingReg.find(dwPID) != m_mapPendingReg.end())
		return WS_REG_ERR_DUP_PID;

	for (const auto & e : m_vecEntries)
		if (e.dwAID == dwAID)
			return WS_REG_ERR_DUP_ACCOUNT;

	for (const auto & kPending : m_mapPendingReg)
		if (kPending.second.dwAID == dwAID)
			return WS_REG_ERR_DUP_ACCOUNT;

	if (bLevel < m_kConfig.iMinLevel || bLevel > m_kConfig.iMaxLevel)
		return WS_REG_ERR_LEVEL;

	if (m_kConfig.iJobFilter != 0 && bJob != (BYTE)(m_kConfig.iJobFilter - 1))
		return WS_REG_ERR_JOB;

	return WS_REG_OK;
}

bool CWSTournamentManager::AddEntry(DWORD dwPID, DWORD dwAID, const char * c_szName, BYTE bLevel, BYTE bJob, const char * c_szIP)
{
	if (m_bDBReady && m_dwTournamentDBID != 0)
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"INSERT INTO player.ws_entry (tournament_id, account_id, pid, name, level, job, fee_gold) "
			"VALUES (%u, %u, %u, '%s', %d, %d, %lld);",
			m_dwTournamentDBID, dwAID, dwPID, c_szName, (int) bLevel, (int) bJob, m_kConfig.llFee));

		if (pMsg->Get()->uiAffectedRows != 1)
		{
			sys_err("WS_TOURNAMENT: ws_entry insert basarisiz pid=%u aid=%u", dwPID, dwAID);
			return false;
		}
	}

	TWSEntry kEntry;
	kEntry.dwPID = dwPID;
	kEntry.dwAID = dwAID;
	strlcpy(kEntry.szName, c_szName, sizeof(kEntry.szName));
	if (c_szIP != nullptr)
		strlcpy(kEntry.szIP, c_szIP, sizeof(kEntry.szIP));
	kEntry.bLevel = bLevel;
	kEntry.bJob = bJob;
	m_vecEntries.push_back(kEntry);
	MarkBracketDirty();

	sys_log(0, "WS_TOURNAMENT: kayit pid=%u aid=%u name=%s lv=%d job=%d fee=%lld",
			dwPID, dwAID, c_szName, (int) bLevel, (int) bJob, m_kConfig.llFee);
	return true;
}

int CWSTournamentManager::RegisterLocal(LPCHARACTER ch)
{
	if (ch == nullptr || ch->GetDesc() == nullptr)
		return WS_REG_ERR_DB;

	if (ch->GetGMLevel() != GM_PLAYER && !test_server)
		return WS_REG_ERR_GM;

	const DWORD dwPID = ch->GetPlayerID();
	const DWORD dwAID = ch->GetDesc()->GetAccountTable().id;
	const char * c_szIP = ch->GetDesc()->GetHostName();

	const int iCode = CheckRegistration(dwPID, dwAID, (BYTE) MINMAX(0, ch->GetLevel(), 255), (BYTE) ch->GetJob(), c_szIP);
	if (iCode != WS_REG_OK)
		return iCode;

	if (!AddEntry(dwPID, dwAID, ch->GetName(), (BYTE) MINMAX(0, ch->GetLevel(), 255), (BYTE) ch->GetJob(), c_szIP))
		return WS_REG_ERR_DB;

	return WS_REG_OK;
}

void CWSTournamentManager::HandleRegRequest(const TPacketGGWSTournament * p)
{
	const int iCode = CheckRegistration(p->dwPID, p->dwAID, p->bLevel, p->bJob, p->szIP);

	TPacketGGWSTournament kAck;
	memset(&kAck, 0, sizeof(kAck));
	kAck.bSubHeader = WS_GG_REG_ACK;
	kAck.dwPID = p->dwPID;
	kAck.dwAID = p->dwAID;
	kAck.iValue1 = iCode;
	kAck.llGold = 0;

	// ucret kaldirildi: origin'de kesinti gerekmedigi icin kayit TEK fazli -
	// uygunsa dogrudan buraya yazilir, ACK yalnizca sonucu bildirir
	if (iCode == WS_REG_OK)
	{
		if (!AddEntry(p->dwPID, p->dwAID, p->szName, p->bLevel, p->bJob, p->szIP))
			kAck.iValue1 = WS_REG_ERR_DB;
	}

	SendGG(kAck);
}

void CWSTournamentManager::HandleRegConfirm(const TPacketGGWSTournament * p)
{
	auto it = m_mapPendingReg.find(p->dwPID);

	BYTE bLevel = p->bLevel;
	BYTE bJob = p->bJob;
	char szName[CHARACTER_NAME_MAX_LEN + 1];
	char szIP[16];
	strlcpy(szName, p->szName, sizeof(szName));
	strlcpy(szIP, p->szIP, sizeof(szIP));

	if (it != m_mapPendingReg.end())
	{
		bLevel = it->second.bLevel;
		bJob = it->second.bJob;
		strlcpy(szName, it->second.szName, sizeof(szName));
		strlcpy(szIP, it->second.szIP, sizeof(szIP));
		m_mapPendingReg.erase(it);
	}

	// UCRET KARSI TARAFTA KESILDI: bu noktadan sonra kayit reddedilirse iade sarttir
	const int iCode = CheckRegistration(p->dwPID, p->dwAID, bLevel, bJob, szIP);
	if (iCode != WS_REG_OK)
	{
		sys_log(0, "WS_TOURNAMENT: gec REG_CONFIRM reddedildi pid=%u kod=%d - ucret iade edildi", p->dwPID, iCode);
		ReleaseSafetyClaimOrRefund(p, "gec-kayit-iade");
		return;
	}

	// ONCE emaneti yakala, SONRA kaydi kesinlestir: emanet 120sn sweep'ine kapildiysa
	// (asiri gecikmis CONFIRM) para zaten iadeye donmustur - kayit YAPILMAZ, boylece
	// "hem kayit hem iade" cift kazanci yapisal olarak imkansizdir
	if (p->iValue1 > 0 && m_bDBReady)
	{
		std::unique_ptr<SQLMsg> pMsgVoid(DBManager::instance().DirectQuery(
			"UPDATE player.ws_claim SET status = 1, claimed_at = NOW() WHERE id = %d AND status = 2;", p->iValue1));

		if (pMsgVoid->Get()->uiAffectedRows != 1)
		{
			sys_log(0, "WS_TOURNAMENT: emanet claim %d sweep'e kapilmis - gec CONFIRM, kayit yapilmadi pid=%u", p->iValue1, p->dwPID);
			NotifyClaim(p->dwPID, p->dwAID);
			return;
		}
	}

	if (!AddEntry(p->dwPID, p->dwAID, szName, bLevel, bJob, szIP))
	{
		// ucret yakalandi ama entry yazilamadi: yeni iade claim'i ac
		InsertClaim(p->dwAID, p->dwPID, p->llGold > 0 ? p->llGold : m_kConfig.llFee, "kayit-hata-iade");
		NotifyClaim(p->dwPID, p->dwAID);
	}
}

void CWSTournamentManager::ReleaseSafetyClaimOrRefund(const TPacketGGWSTournament * p, const char * c_szReason)
{
	// origin emanet claim'i yazdiysa onu odenebilir yap; yazamadiysa (ucretsiz turnuva
	// veya DB'siz origin) yeni claim ac. Iki yol da idempotent.
	if (p->iValue1 > 0 && m_bDBReady)
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"UPDATE player.ws_claim SET status = 0, reason = '%s' WHERE id = %d AND status = 2;", c_szReason, p->iValue1));

		if (pMsg->Get()->uiAffectedRows == 1)
		{
			NotifyClaim(p->dwPID, p->dwAID);
			return;
		}
	}

	InsertClaim(p->dwAID, p->dwPID, p->llGold > 0 ? p->llGold : m_kConfig.llFee, c_szReason);
	NotifyClaim(p->dwPID, p->dwAID);
}

int CWSTournamentManager::HandleUnregister(DWORD dwPID)
{
	if (m_iState != WS_STATE_REGISTRATION)
		return 1;

	for (auto it = m_vecEntries.begin(); it != m_vecEntries.end(); ++it)
	{
		if (it->dwPID != dwPID)
			continue;

		// DELETE (UPDATE degil): UNIQUE(tournament_id, account_id) yuzunden satir kalirsa
		// ayni hesap tekrar kayit olamazdi
		if (m_bDBReady && m_dwTournamentDBID != 0)
		{
			std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"DELETE FROM player.ws_entry WHERE tournament_id = %u AND pid = %u;", m_dwTournamentDBID, dwPID));
		}

		m_vecEntries.erase(it);
		MarkBracketDirty();
		return 0;
	}

	return 1;
}

void CWSTournamentManager::ExpirePendingConfirms(time_t tNow)
{
	for (auto it = m_mapPendingReg.begin(); it != m_mapPendingReg.end(); )
	{
		if (tNow >= it->second.tExpire)
			it = m_mapPendingReg.erase(it);
		else
			++it;
	}
}

// ============================================================================
// turnuva yasam dongusu (host)
// ============================================================================

int CWSTournamentManager::CreateTournament(const TWSConfig & kConfig, int iRegMinutes, const char * c_szGMName)
{
	if (!IsHostCore())
		return 1;

	if (!m_bDBReady)
		return 2;

	if (m_iState != WS_STATE_IDLE)
		return 3;

	if (quest::CQuestManager::instance().GetEventFlag("ws_disabled") != 0)
		return 4;

	m_kConfig = kConfig;
	m_kConfig.llFee = 0;	// giris ucreti/odul havuzu KALDIRILDI (kullanici karari) - alan yalnizca wire uyumu icin
	m_kConfig.iSetCount = MINMAX(1, m_kConfig.iSetCount, 5);
	m_kConfig.iMatchMinutes = MINMAX(5, m_kConfig.iMatchMinutes, 15);
	m_kConfig.iMinLevel = MINMAX(1, m_kConfig.iMinLevel, 255);
	m_kConfig.iMaxLevel = MINMAX(m_kConfig.iMinLevel, m_kConfig.iMaxLevel, 255);
	m_kConfig.iJobFilter = MINMAX(0, m_kConfig.iJobFilter, 4);
	iRegMinutes = MINMAX(1, iRegMinutes, 30);

	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"INSERT INTO player.ws_tournament (status, fee_gold, set_count, match_minutes, min_level, max_level, job_filter, rake_pct, created_by) "
			"VALUES (1, %lld, %d, %d, %d, %d, %d, %d, '%s');",
			m_kConfig.llFee, m_kConfig.iSetCount, m_kConfig.iMatchMinutes, m_kConfig.iMinLevel, m_kConfig.iMaxLevel,
			m_kConfig.iJobFilter, MINMAX(0, GetFlagOr("ws_rake_pct", 15), 90), c_szGMName));

		if (pMsg->Get()->uiAffectedRows != 1)
		{
			sys_err("WS_TOURNAMENT: ws_tournament insert basarisiz");
			return 2;
		}

		m_dwTournamentDBID = pMsg->Get()->uiInsertID;
	}

	m_iState = WS_STATE_REGISTRATION;
	m_iRound = 0;
	m_vecEntries.clear();
	m_vecMatches.clear();
	m_mapPendingReg.clear();

	const time_t tNow = get_global_time();
	m_tRegDeadline = tNow + (time_t) iRegMinutes * 60;
	m_tLastAnnounce = tNow;
	m_tLastSync = 0;

	StartTickEvent();
	SendStateSync();
	BuildAndBroadcastBracket();

	static const char * c_apszJobNames[] = { "Tum siniflar", "Savasci", "Ninja", "Sura", "Saman" };
	AnnounceAll("WS Turnuvasi basliyor! Kayit: /ws kayit veya haritadaki Usta | Seviye: %d-%d | Sinif: %s | Kayit suresi: %d dk",
			m_kConfig.iMinLevel, m_kConfig.iMaxLevel,
			c_apszJobNames[m_kConfig.iJobFilter], iRegMinutes);

	sys_log(0, "WS_TOURNAMENT: turnuva %u olusturuldu (gm=%s fee=%lld set=%d dk=%d lv=%d-%d job=%d reg=%ddk)",
			m_dwTournamentDBID, c_szGMName, m_kConfig.llFee, m_kConfig.iSetCount, m_kConfig.iMatchMinutes,
			m_kConfig.iMinLevel, m_kConfig.iMaxLevel, m_kConfig.iJobFilter, iRegMinutes);

	return 0;
}

void CWSTournamentManager::ResetRuntime()
{
	m_iState = WS_STATE_IDLE;
	m_dwTournamentDBID = 0;
	m_iRound = 0;
	m_vecEntries.clear();
	m_vecMatches.clear();
	m_mapPendingReg.clear();
	m_mapPrepLock.clear();
	SendStateSync();
	BuildAndBroadcastBracket();	// paneller bosalsin
}

void CWSTournamentManager::CancelTournament(int iDBStatus, const char * c_szReason)
{
	if (m_iState == WS_STATE_IDLE)
		return;

	// once hook'lari sustur: arena kapanirken gelen OnArenaClosed cagrilarinin
	// yeni sonuc uretmemesi icin maclari kapat
	std::vector<DWORD> vecEndPids;
	for (auto & m : m_vecMatches)
	{
		// PAUSED da dahil: arena canli - kapatilmazsa ResetRuntime sonrasi hicbir
		// yedek yol kalmaz, bekleyen duellocunun m_pArena'si relog'a kadar takili
		// kalir (duello chat filtresi kalici karartir)
		if (m.iState == WS_MATCH_RUNNING || m.iState == WS_MATCH_PAUSED)
			vecEndPids.push_back(m.dwPIDA);
		m.iState = WS_MATCH_DONE;
		if (m.iResult == WS_RESULT_NONE)
		{
			m.iResult = WS_RESULT_DOUBLE_LOSS;
			m.iReason = WS_REASON_CANCEL;
			DBUpdateMatch(m);
		}
	}

	m_iState = WS_STATE_IDLE;

	for (const DWORD dwPID : vecEndPids)
		CArenaManager::instance().EndDuel(dwPID);

	for (const auto & e : m_vecEntries)
		MsgToPlayer(e.dwPID, WS_MSG_CANCEL_REFUND);

	DBUpdateTournamentStatus(iDBStatus);

	AnnounceAll("WS Turnuvasi iptal edildi (%s).", c_szReason);
	sys_log(0, "WS_TOURNAMENT: turnuva %u iptal (%s)", m_dwTournamentDBID, c_szReason);

	ResetRuntime();
}

void CWSTournamentManager::CloseRegistration(bool bForced)
{
	m_mapPendingReg.clear();

	const int iMinPlayers = MINMAX(2, GetFlagOr("ws_min_players", 4), 64);

	if ((int) m_vecEntries.size() < iMinPlayers)
	{
		AnnounceAll("WS Turnuvasi: Yeterli katilim olmadi (%d/%d). Turnuva iptal edildi.",
				(int) m_vecEntries.size(), iMinPlayers);
		CancelTournament(5, "yetersiz katilim");
		return;
	}

	m_iState = WS_STATE_RUNNING;

	if (m_bDBReady && m_dwTournamentDBID != 0)
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"UPDATE player.ws_tournament SET status = 2 WHERE id = %u;", m_dwTournamentDBID));
	}

	AnnounceAll("WS Turnuvasi: Kayitlar kapandi! %d oyuncu ile turnuva basliyor.",
			(int) m_vecEntries.size());

	sys_log(0, "WS_TOURNAMENT: kayit kapandi (%s) oyuncu=%d",
			bForced ? "erken" : "sure", (int) m_vecEntries.size());

	BuildRound(1);
}

void CWSTournamentManager::BuildRound(int iRound)
{
	m_iRound = iRound;
	m_vecMatches.clear();

	// hayatta kalanlari topla ve karistir (Fisher-Yates, oyun RNG'si ile)
	std::vector<int> vecAlive;
	for (int i = 0; i < (int) m_vecEntries.size(); ++i)
		if (m_vecEntries[i].bAlive)
			vecAlive.push_back(i);

	for (int i = (int) vecAlive.size() - 1; i > 0; --i)
	{
		const int j = number(0, i);
		std::swap(vecAlive[i], vecAlive[j]);
	}

	// tek sayida oyuncu: en az bye almis olanlar arasindan rastgele bye
	if (vecAlive.size() % 2 == 1)
	{
		int iMinBye = 999999;
		for (const int idx : vecAlive)
			if (m_vecEntries[idx].iByeCount < iMinBye)
				iMinBye = m_vecEntries[idx].iByeCount;

		std::vector<int> vecCandidates;
		for (int k = 0; k < (int) vecAlive.size(); ++k)
			if (m_vecEntries[vecAlive[k]].iByeCount == iMinBye)
				vecCandidates.push_back(k);

		const int iPick = vecCandidates[number(0, (int) vecCandidates.size() - 1)];
		TWSEntry & kByeEntry = m_vecEntries[vecAlive[iPick]];
		kByeEntry.iByeCount++;

		AnnounceAll("WS Turnuvasi Tur %d: %s rakipsiz kaldi, bir ust tura yukseldi.", iRound, kByeEntry.szName);
		MsgToPlayer(kByeEntry.dwPID, WS_MSG_BYE);

		vecAlive.erase(vecAlive.begin() + iPick);
	}

	MarkBracketDirty();
	AnnounceAll("WS Turnuvasi Tur %d basliyor! %d mac oynanacak.", iRound, (int) vecAlive.size() / 2);

	for (size_t i = 0; i + 1 < vecAlive.size(); i += 2)
	{
		const TWSEntry & kA = m_vecEntries[vecAlive[i]];
		const TWSEntry & kB = m_vecEntries[vecAlive[i + 1]];

		TWSMatch m;
		m.iRound = iRound;
		m.dwPIDA = kA.dwPID;
		m.dwPIDB = kB.dwPID;

		if (m_bDBReady && m_dwTournamentDBID != 0)
		{
			std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"INSERT INTO player.ws_match (tournament_id, round, pid_a, pid_b, name_a, name_b) "
				"VALUES (%u, %d, %u, %u, '%s', '%s');",
				m_dwTournamentDBID, iRound, kA.dwPID, kB.dwPID, kA.szName, kB.szName));

			if (pMsg->Get()->uiAffectedRows == 1)
				m.dwDBID = pMsg->Get()->uiInsertID;
		}

		m_vecMatches.push_back(m);

		// buyuk bracketlerde global duyuru spam'i olmasin
		if (vecAlive.size() <= 16)
			AnnounceAll("WS Turnuvasi Tur %d: %s vs %s", iRound, kA.szName, kB.szName);
	}

	SendStateSync();
}

void CWSTournamentManager::EnterReconnectWait(TWSMatch & m, DWORD dwMatchSetA, DWORD dwMatchSetB, const char * c_szDcName)
{
	const time_t tNow = get_global_time();

	// mevcut cagirma (SUMMON) dongusu beklemeyi/yeniden kurulumu yurutur:
	// donen oyuncu tespit edilir -> TryStartDuel skoru geri yukler; donmeyen deadline'da hukmen elenir
	m.iState = WS_MATCH_SUMMON;
	m.bResume = true;
	m.dwResumeSetA = dwMatchSetA;
	m.dwResumeSetB = dwMatchSetB;
	m.bArrivedA = false;
	m.bArrivedB = false;

	const int iWait = MINMAX(15, GetFlagOr("ws_reconnect_seconds", 60), 300);
	m.tSummonDeadline = tNow + iWait;
	m.tNextSummonRetry = tNow + 5;

	EndMatchPrep(m.dwPIDA, m.dwPIDB);
	MarkBracketDirty();

	if (c_szDcName != nullptr)
		AnnounceAll("WS Turnuvasi: %s baglantisi koptu! %d saniye icinde donmezse hukmen elenecek. (Skor korunuyor: %u - %u)",
				c_szDcName, iWait, dwMatchSetA, dwMatchSetB);
	else
		AnnounceAll("WS Turnuvasi: Mac kesildi, %d saniye icinde yeniden kurulacak. (Skor korunuyor: %u - %u)",
				iWait, dwMatchSetA, dwMatchSetB);

	sys_log(0, "WS_TOURNAMENT: kopma-bekleme tur=%d A=%u B=%u skor=%u-%u sure=%d dcA=%d dcB=%d",
			m.iRound, m.dwPIDA, m.dwPIDB, dwMatchSetA, dwMatchSetB, iWait, (int) m.byDcCountA, (int) m.byDcCountB);
}

void CWSTournamentManager::SummonPlayer(DWORD dwPID)
{
	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(dwPID);

	if (ch != nullptr)
	{
		if (ch->IsDead())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Macin basliyor ama olu durumdasin! Hemen canlan, tekrar isinlanacaksin.");
			return;
		}

		if (ch->GetDungeon() != nullptr || ch->GetWarMap() != nullptr)
		{
			// zindan/savas ilerlemesini zorla warp'la yakmayiz; cikmazsa hukmen kaybeder
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Macin basliyor ama zindan/savas icindesin! Cikmazsan hukmen kaybedeceksin.");
			return;
		}

		if (ch->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX)
			return;

		WORD wX = 0, wY = 0;
		if (!CArenaManager::instance().GetObserverPoint(WS_TOURNAMENT_MAP_INDEX, wX, wY))
		{
			sys_err("WS_TOURNAMENT: arena ring tanimi yok (settings.lua arena.add_map)");
			return;
		}

		ch->ChatPacket(CHAT_TYPE_INFO, "WS: Macin basliyor! Arenaya isinlaniyorsun.");
		ch->WarpSet(wX * 100, wY * 100);
		return;
	}

	// oyuncu bu core'da degil: diger core'lara duyur, sahibi olan warplar
	TPacketGGWSTournament p;
	memset(&p, 0, sizeof(p));
	p.bSubHeader = WS_GG_SUMMON;
	p.dwPID = dwPID;
	SendGG(p);
}

void CWSTournamentManager::BeginSummon(TWSMatch & m, time_t tNow)
{
	m.iState = WS_MATCH_SUMMON;
	m.tSummonDeadline = tNow + MINMAX(20, GetFlagOr("ws_summon_seconds", 60), 300);
	m.tNextSummonRetry = tNow + 10;
	m.bArrivedA = false;
	m.bArrivedB = false;

	SummonPlayer(m.dwPIDA);
	SummonPlayer(m.dwPIDB);
}

bool CWSTournamentManager::TryStartDuel(TWSMatch & m)
{
	const LPCHARACTER chA = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDA);
	const LPCHARACTER chB = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDB);

	if (chA == nullptr || chB == nullptr)
		return false;

	if (chA->GetMapIndex() != WS_TOURNAMENT_MAP_INDEX || chB->GetMapIndex() != WS_TOURNAMENT_MAP_INDEX)
		return false;

	// onceden seyirci moduna girmis olabilirler: StartDuel oncesi observer durumunu temizle
	for (LPCHARACTER pkChar : { chA, chB })
	{
		if (pkChar->GetArena() != nullptr)
		{
			pkChar->GetArena()->RemoveObserver(pkChar->GetPlayerID());
			pkChar->SetArena(nullptr);
		}
		if (pkChar->IsObserverMode())
		{
			pkChar->SetObserverMode(false);
			pkChar->SetArenaObserverMode(false);
		}
	}

	// do_duel deseni: buff temizligi + parti dagitma (adil baslangic)
	chA->RemoveGoodAffect();
	chA->RemoveBadAffect();
	chB->RemoveGoodAffect();
	chB->RemoveBadAffect();

	for (LPCHARACTER pkChar : { chA, chB })
	{
		const LPPARTY pParty = pkChar->GetParty();
		if (pParty != nullptr)
		{
			if (pParty->GetMemberCount() == 2)
				CPartyManager::instance().DeleteParty(pParty);
			else
				pParty->Quit(pkChar->GetPlayerID());
		}
	}

	if (!CArenaManager::instance().StartDuel(chA, chB, m_kConfig.iSetCount, m_kConfig.iMatchMinutes))
		return false;	// ring dolu (ornegin eski bir serbest duello) - sonraki tick'te tekrar dene

	m.iState = WS_MATCH_RUNNING;
	m.tRunStart = get_global_time();
	m.iRemainSec = m_kConfig.iMatchMinutes * 60;
	MarkBracketDirty();

	// kopma sonrasi yeniden kurulum: korunan set skorunu geri yukle
	if (m.bResume)
	{
		if (m.dwResumeSetA > 0 || m.dwResumeSetB > 0)
		{
			CArenaManager::instance().WSRestoreSetPoints(m.dwPIDA, m.dwResumeSetA, m.dwResumeSetB);

			const TWSEntry * pEA = FindEntry(m.dwPIDA);
			const TWSEntry * pEB = FindEntry(m.dwPIDB);
			AnnounceAll("WS Turnuvasi: %s vs %s maci kaldigi skordan devam ediyor: %u - %u",
					pEA ? pEA->szName : "?", pEB ? pEB->szName : "?", m.dwResumeSetA, m.dwResumeSetB);
		}

		m.bResume = false;
		m.dwResumeSetA = 0;
		m.dwResumeSetB = 0;
	}

	// kilit ILK kose isinlanmasindan itibaren: kose warp + hazirlik + DUEL_START'a kadar
	// (arena ready event'i state 0'da kilidi WS_PREP_SECONDS'a tazeler, state 1'de acar)
	BeginMatchPrep(m.dwPIDA, m.dwPIDB, WS_PREP_SECONDS * 2);
	chA->ChatPacket(CHAT_TYPE_NOTICE, "WS: Mac alanina isinlaniyorsun! Dovus baslayana kadar hareket kilitli - becerilerini simdi bas.");
	chB->ChatPacket(CHAT_TYPE_NOTICE, "WS: Mac alanina isinlaniyorsun! Dovus baslayana kadar hareket kilitli - becerilerini simdi bas.");

	sys_log(0, "WS_TOURNAMENT: mac basladi tur=%d A=%u B=%u", m.iRound, m.dwPIDA, m.dwPIDB);
	return true;
}

void CWSTournamentManager::ProcessMatches(time_t tNow)
{
	int iFreeRings = GetFreeRingHint();

	for (auto & m : m_vecMatches)
	{
		switch (m.iState)
		{
			case WS_MATCH_PENDING:
				if (iFreeRings > 0)
				{
					BeginSummon(m, tNow);
					--iFreeRings;
				}
				break;

			case WS_MATCH_SUMMON:
			{
				const LPCHARACTER chA = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDA);
				const LPCHARACTER chB = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDB);

				// yapiskan degil: gelip sonra ayrilan/cikan "gelmedi" sayilir (grief-kilit onlemi)
				m.bArrivedA = (chA != nullptr && chA->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX);
				m.bArrivedB = (chB != nullptr && chB->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX);

				if (m.bArrivedA && m.bArrivedB)
				{
					if (TryStartDuel(m))
						break;

					// iki taraf da hazir ama ring dolu (or. eski serbest duello):
					// mac hakki yanmasin, sure uzasin - ring bosalinca baslar
					if (tNow >= m.tSummonDeadline)
						m.tSummonDeadline = tNow + 30;
					break;
				}

				if (tNow >= m.tNextSummonRetry)
				{
					// gelmeyenlere tekrar cagri (olen canlandiysa / warp kacirdiysa)
					if (!m.bArrivedA)
						SummonPlayer(m.dwPIDA);
					if (!m.bArrivedB)
						SummonPlayer(m.dwPIDB);
					m.tNextSummonRetry = tNow + 10;
				}

				if (tNow >= m.tSummonDeadline)
				{
					if (m.bArrivedA && !m.bArrivedB)
						ResolveMatch(m, WS_RESULT_A_WIN, WS_REASON_WALKOVER);
					else if (!m.bArrivedA && m.bArrivedB)
						ResolveMatch(m, WS_RESULT_B_WIN, WS_REASON_WALKOVER);
					else
						ResolveMatch(m, WS_RESULT_DOUBLE_LOSS, WS_REASON_WALKOVER);
				}
				break;
			}

			case WS_MATCH_RUNNING:
				// sonucu arena hook'lari uretir (OnArenaMatchEnd / OnArenaTimeout / OnArenaClosed)
				break;

			case WS_MATCH_PAUSED:
			{
				// yerinde duraklatilmis mac: kopan donunce kaldigi yerden devam.
				// Resume ayrica OnPlayerLogin'den (Entergame sonunda) senkron tetiklenir;
				// buradaki cagri sadece tick-tabanli yedektir
				if (TryResumePausedMatch(m))
					break;

				const LPCHARACTER chA = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDA);
				const LPCHARACTER chB = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDB);
				// PHASE_GAME sarti: karakter PlayerLoad aninda (Entergame'den once, client
				// daha yukleme ekranindayken) FindByPID + map 112 kosullarini saglar; o anda
				// resume ateslenirse DUEL_START client'ta coplenir ve mac saati erken baslar
				const bool bHereA = (chA != nullptr && chA->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX
						&& chA->GetDesc() != nullptr && chA->GetDesc()->IsPhase(PHASE_GAME));
				const bool bHereB = (chB != nullptr && chB->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX
						&& chB->GetDesc() != nullptr && chB->GetDesc()->IsPhase(PHASE_GAME));

				if (tNow >= m.tSummonDeadline)
				{
					// baglanmis ama hala yukleme ekraninda olan oyuncuya hukmen verme:
					// kisa tolerans (en fazla deadline+30sn; desc timeout'lari stall'i keser)
					const bool bLoadingA = (chA != nullptr && chA->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX && !bHereA);
					const bool bLoadingB = (chB != nullptr && chB->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX && !bHereB);
					if ((bLoadingA || bLoadingB) && tNow < m.tSummonDeadline + 30)
						break;

					if (bHereA && !bHereB)
						ResolveMatch(m, WS_RESULT_A_WIN, WS_REASON_WALKOVER);
					else if (!bHereA && bHereB)
						ResolveMatch(m, WS_RESULT_B_WIN, WS_REASON_WALKOVER);
					else
						ResolveMatch(m, WS_RESULT_DOUBLE_LOSS, WS_REASON_WALKOVER);

					// canli birakilan arenayi fiziksel olarak kapat (mac DONE -> Closed hook atlar)
					CArenaManager::instance().EndDuel(m.dwPIDA);
				}
				break;
			}

			case WS_MATCH_DONE:
			default:
				break;
		}
	}
}

bool CWSTournamentManager::TryResumePausedMatch(TWSMatch & m)
{
	if (m.iState != WS_MATCH_PAUSED)
		return false;

	const LPCHARACTER chA = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDA);
	const LPCHARACTER chB = CHARACTER_MANAGER::instance().FindByPID(m.dwPIDB);
	const bool bHereA = (chA != nullptr && chA->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX
			&& chA->GetDesc() != nullptr && chA->GetDesc()->IsPhase(PHASE_GAME));
	const bool bHereB = (chB != nullptr && chB->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX
			&& chB->GetDesc() != nullptr && chB->GetDesc()->IsPhase(PHASE_GAME));

	if (!bHereA || !bHereB)
		return false;

	if (!CArenaManager::instance().WSResumeDuel(m.dwPIDA, m.iRemainSec))
		return false;

	m.iState = WS_MATCH_RUNNING;
	m.tRunStart = get_global_time();
	MarkBracketDirty();

	const TWSEntry * pEA = FindEntry(m.dwPIDA);
	const TWSEntry * pEB = FindEntry(m.dwPIDB);
	AnnounceAll("WS Turnuvasi: %s vs %s maci kaldigi yerden devam ediyor!",
			pEA ? pEA->szName : "?", pEB ? pEB->szName : "?");
	return true;
}

void CWSTournamentManager::ResolveMatch(TWSMatch & m, int iResult, int iReason)
{
	if (m.iState == WS_MATCH_DONE)
		return;	// idempotent: ayni mac icin ikinci sonuc kabul edilmez

	m.iState = WS_MATCH_DONE;
	m.iResult = iResult;
	m.iReason = iReason;
	m_tLastResolve = get_global_time();
	EndMatchPrep(m.dwPIDA, m.dwPIDB);	// yarim kalan hazirlik kilidi kalmasin

	TWSEntry * pA = FindEntry(m.dwPIDA);
	TWSEntry * pB = FindEntry(m.dwPIDB);

	const char * c_szNameA = pA ? pA->szName : "?";
	const char * c_szNameB = pB ? pB->szName : "?";

	if (iResult == WS_RESULT_A_WIN)
	{
		if (pB != nullptr && pB->bAlive)
		{
			pB->bAlive = false;
			DBUpdateEntryStatus(m.dwPIDB, 1);
		}
		MsgToPlayer(m.dwPIDA, (iReason == WS_REASON_WALKOVER) ? WS_MSG_WALKOVER_WIN : WS_MSG_MATCH_WIN);
		MsgToPlayer(m.dwPIDB, (iReason == WS_REASON_WALKOVER) ? WS_MSG_WALKOVER_LOSS : WS_MSG_MATCH_LOSS);
		AnnounceAll("WS Turnuvasi Tur %d: %s, %s karsisinda kazandi!", m.iRound, c_szNameA, c_szNameB);
	}
	else if (iResult == WS_RESULT_B_WIN)
	{
		if (pA != nullptr && pA->bAlive)
		{
			pA->bAlive = false;
			DBUpdateEntryStatus(m.dwPIDA, 1);
		}
		MsgToPlayer(m.dwPIDB, (iReason == WS_REASON_WALKOVER) ? WS_MSG_WALKOVER_WIN : WS_MSG_MATCH_WIN);
		MsgToPlayer(m.dwPIDA, (iReason == WS_REASON_WALKOVER) ? WS_MSG_WALKOVER_LOSS : WS_MSG_MATCH_LOSS);
		AnnounceAll("WS Turnuvasi Tur %d: %s, %s karsisinda kazandi!", m.iRound, c_szNameB, c_szNameA);
	}
	else	// WS_RESULT_DOUBLE_LOSS
	{
		if (pA != nullptr && pA->bAlive)
		{
			pA->bAlive = false;
			DBUpdateEntryStatus(m.dwPIDA, 1);
		}
		if (pB != nullptr && pB->bAlive)
		{
			pB->bAlive = false;
			DBUpdateEntryStatus(m.dwPIDB, 1);
		}
		MsgToPlayer(m.dwPIDA, WS_MSG_DOUBLE_LOSS);
		MsgToPlayer(m.dwPIDB, WS_MSG_DOUBLE_LOSS);
		AnnounceAll("WS Turnuvasi Tur %d: %s vs %s maci sonuclanamadi - iki oyuncu da elendi!", m.iRound, c_szNameA, c_szNameB);
	}

	DBUpdateMatch(m);
	MarkBracketDirty();
	sys_log(0, "WS_TOURNAMENT: mac sonucu tur=%d A=%u B=%u sonuc=%d sebep=%d dmgA=%lld dmgB=%lld",
			m.iRound, m.dwPIDA, m.dwPIDB, iResult, iReason, m.llDamageA, m.llDamageB);
}

void CWSTournamentManager::CheckRoundEnd(time_t tNow)
{
	if (m_vecMatches.empty())
		return;

	for (const auto & m : m_vecMatches)
		if (m.iState != WS_MATCH_DONE)
			return;

	// son cozumden sonra kisa bekleme: arena EndDuel'inin (10 sn) oyunculari
	// disari tasimasini bekle, yeni tur summon'u ile cakismasin
	if (tNow - m_tLastResolve < 12)
		return;

	const int iAlive = CountAlive();

	if (iAlive == 1)
	{
		for (const auto & e : m_vecEntries)
		{
			if (e.bAlive)
			{
				FinishWithChampion(e);
				return;
			}
		}
	}
	else if (iAlive == 0)
	{
		FinishNoChampion();
	}
	else
	{
		BuildRound(m_iRound + 1);
	}
}

void CWSTournamentManager::FinishWithChampion(const TWSEntry & kChampion)
{
	// ikinci: final macinin kaybedeni (final = son turun maci, cift eleme degilse)
	DWORD dwRunnerPID = 0;
	const char * c_szRunnerName = nullptr;

	for (const auto & m : m_vecMatches)
	{
		if (m.iRound != m_iRound)
			continue;
		if (m.iResult == WS_RESULT_A_WIN && m.dwPIDA == kChampion.dwPID)
			dwRunnerPID = m.dwPIDB;
		else if (m.iResult == WS_RESULT_B_WIN && m.dwPIDB == kChampion.dwPID)
			dwRunnerPID = m.dwPIDA;
	}

	if (dwRunnerPID != 0)
	{
		const TWSEntry * pRunner = FindEntry(dwRunnerPID);
		if (pRunner != nullptr)
			c_szRunnerName = pRunner->szName;
	}

	// odul/havuz KALDIRILDI: sampiyonluk yalnizca duyuru + DB kaydi
	MsgToPlayer(kChampion.dwPID, WS_MSG_CHAMPION);

	if (c_szRunnerName != nullptr)
		AnnounceAll("WS Turnuvasi bitti! SAMPIYON: %s | Ikinci: %s", kChampion.szName, c_szRunnerName);
	else
		AnnounceAll("WS Turnuvasi bitti! SAMPIYON: %s", kChampion.szName);

	if (m_bDBReady && m_dwTournamentDBID != 0)
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"UPDATE player.ws_tournament SET status = 3, winner_pid = %u, winner_name = '%s', finished_at = NOW() WHERE id = %u;",
			kChampion.dwPID, kChampion.szName, m_dwTournamentDBID));
	}

	DBUpdateEntryStatus(kChampion.dwPID, 3);

	sys_log(0, "WS_TOURNAMENT: turnuva %u bitti sampiyon=%s(%u)", m_dwTournamentDBID, kChampion.szName, kChampion.dwPID);

	ResetRuntime();
}

void CWSTournamentManager::FinishNoChampion()
{
	AnnounceAll("WS Turnuvasi kazanansiz bitti (cift eleme).");

	DBUpdateTournamentStatus(6);
	sys_log(0, "WS_TOURNAMENT: turnuva %u kazanansiz bitti", m_dwTournamentDBID);

	ResetRuntime();
}

int CWSTournamentManager::Tick()
{
	if (m_iState == WS_STATE_IDLE)
	{
		ClearTickEvent();	// event 0 donup serbest kalacak; bayat pointer birakma
		return 0;
	}

	const time_t tNow = get_global_time();

	if (m_iState == WS_STATE_REGISTRATION)
	{
		ExpirePendingConfirms(tNow);

		if (tNow >= m_tRegDeadline)
		{
			CloseRegistration(false);
		}
		else
		{
			if (tNow - m_tLastAnnounce >= 60)
			{
				m_tLastAnnounce = tNow;
				AnnounceAll("WS Turnuvasi: Kayitlar acik! %d oyuncu kayitli, kalan sure %d dk. Katilim: /ws kayit",
						(int) m_vecEntries.size(), (int) ((m_tRegDeadline - tNow) / 60) + 1);
			}
			if (tNow - m_tLastSync >= 10)
			{
				m_tLastSync = tNow;
				SendStateSync();
			}
			if ((m_bBracketDirty && tNow - m_tLastBracketSync >= 3) || tNow - m_tLastBracketSync >= 30)
				BuildAndBroadcastBracket();	// heartbeat: bayat-snapshot tespiti icin duzenli yayin
		}
	}
	else if (m_iState == WS_STATE_RUNNING)
	{
		ProcessMatches(tNow);
		CheckRoundEnd(tNow);

		if (m_iState != WS_STATE_IDLE && tNow - m_tLastSync >= 10)
		{
			m_tLastSync = tNow;
			SendStateSync();
		}
		if (m_iState != WS_STATE_IDLE && ((m_bBracketDirty && tNow - m_tLastBracketSync >= 3) || tNow - m_tLastBracketSync >= 30))
			BuildAndBroadcastBracket();	// heartbeat: bayat-snapshot tespiti icin duzenli yayin
	}

	if (m_iState == WS_STATE_IDLE)
	{
		ClearTickEvent();
		return 0;
	}

	return PASSES_PER_SEC(WS_TICK_SECONDS);
}

// ============================================================================
// arena kancalari
// ============================================================================

void CWSTournamentManager::OnArenaMatchEnd(DWORD dwWinnerPID, DWORD dwLoserPID)
{
	if (m_iState != WS_STATE_RUNNING)
		return;

	TWSMatch * pM = FindActiveMatchByPair(dwWinnerPID, dwLoserPID);
	// PAUSED da kabul edilir: duraklama sirasinda gelen gercek olum sonucu
	// (ornek: DoT/zehir) dusurulmemeli - aksi halde karar verilmis mac rebuild olur
	if (pM == nullptr || (pM->iState != WS_MATCH_RUNNING && pM->iState != WS_MATCH_PAUSED))
		return;	// turnuva disi (serbest) duello ya da bizim baslatmadigimiz arena olayi

	ResolveMatch(*pM, (pM->dwPIDA == dwWinnerPID) ? WS_RESULT_A_WIN : WS_RESULT_B_WIN, WS_REASON_SCORE);
}

void CWSTournamentManager::OnArenaTimeout(DWORD dwPIDA, DWORD dwPIDB, DWORD dwSetA, DWORD dwSetB, LPCHARACTER chA, LPCHARACTER chB)
{
	if (m_iState != WS_STATE_RUNNING)
		return;

	TWSMatch * pM = FindActiveMatchByPair(dwPIDA, dwPIDB);
	if (pM == nullptr || pM->iState != WS_MATCH_RUNNING)
		return;

	// eslesme yonu: pM->dwPIDA her zaman bizim A'miz; parametreler arena sirasiyla gelir
	const bool bSameOrder = (pM->dwPIDA == dwPIDA);
	const DWORD dwOurSetA = bSameOrder ? dwSetA : dwSetB;
	const DWORD dwOurSetB = bSameOrder ? dwSetB : dwSetA;
	const LPCHARACTER chOurA = bSameOrder ? chA : chB;
	const LPCHARACTER chOurB = bSameOrder ? chB : chA;

	// karar zinciri: set > HP% > verilen hasar > cift eleme (pasif oyun odullendirilmez)
	if (dwOurSetA != dwOurSetB)
	{
		ResolveMatch(*pM, (dwOurSetA > dwOurSetB) ? WS_RESULT_A_WIN : WS_RESULT_B_WIN, WS_REASON_SCORE);
		return;
	}

	const int iHPA = (chOurA != nullptr && chOurA->GetMaxHP() > 0) ? chOurA->GetHPPct() : -1;
	const int iHPB = (chOurB != nullptr && chOurB->GetMaxHP() > 0) ? chOurB->GetHPPct() : -1;

	if (iHPA != iHPB)
	{
		ResolveMatch(*pM, (iHPA > iHPB) ? WS_RESULT_A_WIN : WS_RESULT_B_WIN, WS_REASON_TIMEOUT_HP);
		return;
	}

	if (pM->llDamageA != pM->llDamageB)
	{
		ResolveMatch(*pM, (pM->llDamageA > pM->llDamageB) ? WS_RESULT_A_WIN : WS_RESULT_B_WIN, WS_REASON_TIMEOUT_DMG);
		return;
	}

	ResolveMatch(*pM, WS_RESULT_DOUBLE_LOSS, WS_REASON_PASSIVE);
}

bool CWSTournamentManager::OnArenaPlayerDisconnect(DWORD dwArenaPIDA, DWORD dwArenaPIDB, DWORD dwDcPID)
{
	if (m_iState != WS_STATE_RUNNING)
		return false;

	TWSMatch * pM = FindActiveMatchByPair(dwArenaPIDA, dwArenaPIDB);
	if (pM == nullptr || (pM->iState != WS_MATCH_RUNNING && pM->iState != WS_MATCH_PAUSED))
		return false;

	// kopma hakki: her oyuncu mac basina en fazla ws_reconnect_limit kez kopabilir;
	// ws_reconnect_disabled=1 ile ozellik kapatilir (eski aninda-eleme davranisi)
	const bool bGraceOff = quest::CQuestManager::instance().GetEventFlag("ws_reconnect_disabled") != 0;
	const int iLimit = MINMAX(1, GetFlagOr("ws_reconnect_limit", 2), 5);

	BYTE & rbyDcCount = (pM->dwPIDA == dwDcPID) ? pM->byDcCountA : pM->byDcCountB;
	++rbyDcCount;

	if (bGraceOff || (int) rbyDcCount > iLimit)
	{
		if (!bGraceOff)
		{
			const TWSEntry * pDcOut = FindEntry(dwDcPID);
			AnnounceAll("WS Turnuvasi: %s kopma hakkini tuketti!", pDcOut ? pDcOut->szName : "?");
		}

		const DWORD dwStayPID = (pM->dwPIDA == dwDcPID) ? pM->dwPIDB : pM->dwPIDA;
		ResolveMatch(*pM, (pM->dwPIDA == dwStayPID) ? WS_RESULT_A_WIN : WS_RESULT_B_WIN, WS_REASON_WALKOVER);
		return false;	// vanilla EndDuel arenayi kapatir (mac DONE -> Closed hook atlar)
	}

	// YERINDE DURAKLAT (Eski_A modeli): arena kapatilmaz, rakip ringde serbest bekler,
	// skor arenada oldugu gibi durur; kopan donunce mac kaldigi yerden devam eder
	const time_t tNow = get_global_time();

	if (pM->iState == WS_MATCH_RUNNING)
	{
		// mac saatinden kalani dondur (devam ederken kalan sureyle yeniden kurulur)
		int iElapsed = (int) (tNow - pM->tRunStart);
		if (iElapsed < 0)
			iElapsed = 0;
		pM->iRemainSec = (pM->iRemainSec > iElapsed) ? (pM->iRemainSec - iElapsed) : 30;
	}

	pM->iState = WS_MATCH_PAUSED;
	pM->tSummonDeadline = tNow + MINMAX(15, GetFlagOr("ws_reconnect_seconds", 60), 300);

	EndMatchPrep(pM->dwPIDA, pM->dwPIDB);
	CArenaManager::instance().WSPauseDuel(dwDcPID);		// arena eventleri durur, arena CANLI kalir
	MarkBracketDirty();

	const TWSEntry * pDc = FindEntry(dwDcPID);
	AnnounceAll("WS Turnuvasi: %s baglantisi koptu! %d saniye icinde donmezse hukmen elenecek. Rakibi ringde bekliyor, skor korunuyor.",
			pDc ? pDc->szName : "?", (int) (pM->tSummonDeadline - tNow));

	sys_log(0, "WS_TOURNAMENT: yerinde-duraklat tur=%d A=%u B=%u dc=%u kalan_mac_sn=%d dcA=%d dcB=%d",
			pM->iRound, pM->dwPIDA, pM->dwPIDB, dwDcPID, pM->iRemainSec, (int) pM->byDcCountA, (int) pM->byDcCountB);

	return true;
}

void CWSTournamentManager::OnArenaMatchAborted(DWORD dwPIDA, DWORD dwPIDB, bool bAPresent, bool bBPresent, DWORD dwSetA, DWORD dwSetB)
{
	if (m_iState != WS_STATE_RUNNING)
		return;

	TWSMatch * pM = FindActiveMatchByPair(dwPIDA, dwPIDB);
	if (pM == nullptr || pM->iState != WS_MATCH_RUNNING)
		return;

	const bool bSameOrder = (pM->dwPIDA == dwPIDA);
	const bool bOurAPresent = bSameOrder ? bAPresent : bBPresent;
	const bool bOurBPresent = bSameOrder ? bBPresent : bAPresent;

	if (bOurAPresent && bOurBPresent)
		return;

	const DWORD dwMatchSetA = bSameOrder ? dwSetA : dwSetB;
	const DWORD dwMatchSetB = bSameOrder ? dwSetB : dwSetA;

	const bool bGraceOff = quest::CQuestManager::instance().GetEventFlag("ws_reconnect_disabled") != 0;
	const int iLimit = MINMAX(1, GetFlagOr("ws_reconnect_limit", 2), 5);

	if (!bOurAPresent)
		++pM->byDcCountA;
	if (!bOurBPresent)
		++pM->byDcCountB;

	const bool bAOut = bGraceOff ? !bOurAPresent : ((int) pM->byDcCountA > iLimit);
	const bool bBOut = bGraceOff ? !bOurBPresent : ((int) pM->byDcCountB > iLimit);

	if (bAOut && bBOut)
	{
		ResolveMatch(*pM, WS_RESULT_DOUBLE_LOSS, WS_REASON_WALKOVER);
		return;
	}
	if (bAOut)
	{
		ResolveMatch(*pM, WS_RESULT_B_WIN, WS_REASON_WALKOVER);
		return;
	}
	if (bBOut)
	{
		ResolveMatch(*pM, WS_RESULT_A_WIN, WS_REASON_WALKOVER);
		return;
	}

	const TWSEntry * pDc = FindEntry(bOurAPresent ? pM->dwPIDB : pM->dwPIDA);
	EnterReconnectWait(*pM, dwMatchSetA, dwMatchSetB, pDc ? pDc->szName : "?");
}

void CWSTournamentManager::OnArenaClosed(DWORD dwPIDA, DWORD dwPIDB, DWORD dwSetA, DWORD dwSetB)
{
	if (m_iState != WS_STATE_RUNNING)
		return;

	TWSMatch * pM = FindActiveMatchByPair(dwPIDA, dwPIDB);
	if (pM == nullptr || pM->iState != WS_MATCH_RUNNING)
		return;	// normal akista mac coktan cozulmustur (DONE), kopma-beklemededir (SUMMON) ya da yeni tur maci (PENDING)

	// ozellik kapaliysa eski davranis: sonucsuz kapanis = cift eleme
	if (quest::CQuestManager::instance().GetEventFlag("ws_reconnect_disabled") != 0)
	{
		sys_err("WS_TOURNAMENT: arena sonucsuz kapandi! tur=%d A=%u B=%u - cift eleme uygulandi", pM->iRound, dwPIDA, dwPIDB);
		ResolveMatch(*pM, WS_RESULT_DOUBLE_LOSS, WS_REASON_UNRESOLVED);
		return;
	}

	// sonucsuz kapanis (or. GM /end_duel): cift eleme yerine skor korunarak yeniden kurulum
	sys_log(0, "WS_TOURNAMENT: arena sonucsuz kapandi, mac yeniden kurulacak tur=%d A=%u B=%u", pM->iRound, dwPIDA, dwPIDB);

	const bool bSameOrder = (pM->dwPIDA == dwPIDA);
	EnterReconnectWait(*pM, bSameOrder ? dwSetA : dwSetB, bSameOrder ? dwSetB : dwSetA, nullptr);
}

// ============================================================================
// oyun kancalari
// ============================================================================

namespace
{
	// map 112 seyirci yayini functoru (Eski_A SHOW_DAMAGE_TO_WATCHERS/FCountPC paritesi).
	// Duellocular haric tutulur (onlara SendDamagePacket zaten unicast atiyor); bizde
	// arena SEYIRCILERI de SetArena'li oldugu icin filtre PID-bazli duellist kontrolu
	struct FWSSendToWatchers
	{
		const void * c_pvData;
		int iSize;

		FWSSendToWatchers(const void * pData, int pSize) : c_pvData(pData), iSize(pSize) {}

		void operator()(LPENTITY ent)
		{
			if (!ent->IsType(ENTITY_CHARACTER))
				return;

			LPCHARACTER ch = (LPCHARACTER) ent;
			if (!ch->IsPC() || ch->GetDesc() == nullptr)
				return;

			CArena * pArena = ch->GetArena();
			if (pArena != nullptr)
			{
				const DWORD dwPID = ch->GetPlayerID();
				if (pArena->GetPlayerAPID() == dwPID || pArena->GetPlayerBPID() == dwPID)
					return;	// aktif duellocu: cift gonderim olmasin
			}

			ch->GetDesc()->Packet(c_pvData, iSize);
		}
	};
}

void CWSTournamentManager::BroadcastToWatchers(const void * c_pvData, int iSize)
{
	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(WS_TOURNAMENT_MAP_INDEX);
	if (pMap == nullptr)
		return;	// bu core 112'yi host etmiyor

	FWSSendToWatchers f(c_pvData, iSize);
	pMap->for_each(f);
}

void CWSTournamentManager::OnPlayerLogin(LPCHARACTER ch)
{
	// ucret/odul kaldirildi: claim odemesi yok (ws_claim altyapisi atil durur)

	// Mac ici relog (yerinde duraklatma): duello anahtarlari Entergame SONUNDA tazelenmeli.
	// Tick resume'u client yukleme ekranindayken ateslenebilir - o anda gonderilen
	// DUEL_START client'ta ana karakter instance'i olmadigi icin coplenir; ustune
	// vanilla MEMBER_DUELIST dali BOS DUEL_START yollayip modu CANNOTATTACK'e ceker.
	// Buradaki cift-tarafli yeniden gonderim (taze VID'lerle) ikisini de duzeltir
	// (Eski_A ReconnectPlayer paritesi). input_login.cpp bu fonksiyonu Entergame'in
	// sonunda, ch->Show + PHASE_GAME sonrasinda cagirir.
	if (ch == nullptr || !IsHostCore())
		return;

	if (ch->GetMapIndex() != WS_TOURNAMENT_MAP_INDEX || m_iState != WS_STATE_RUNNING)
		return;

	const DWORD dwPID = ch->GetPlayerID();

	TWSMatch * pM = FindActiveMatchByPID(dwPID);
	if (pM == nullptr)
		return;

	if (pM->iState == WS_MATCH_PAUSED)
	{
		// Iki taraf da hazirsa maci HEMEN devam ettir: anahtarlar dagitilip mac
		// PAUSED birakilirsa, tick'e kadar gecen <=2sn'lik pencerede dusen final
		// kill OnArenaMatchEnd tarafindan reddedilir ve mac yanlis yeniden kurulurdu.
		// Rakip henuz hazir degilse sadece uyelik tazelenir (SetArena) - cift DC'de
		// ikinci kopusun DC sayacina islenebilmesi GetArena'ya bagli.
		if (!TryResumePausedMatch(*pM))
			CArenaManager::instance().WSSendDuelStart(dwPID);
		return;
	}

	if (pM->iState != WS_MATCH_RUNNING)
		return;

	CArenaManager::instance().WSSendDuelStart(dwPID);

	// hazirlik kilidi hala aktifse client kilidini de tazele
	if (IsMoveLocked(dwPID))
		SendMoveLockCommand(dwPID);
}

bool CWSTournamentManager::OnPlayerEnterArenaMap(LPCHARACTER ch)
{
	if (ch == nullptr || !IsHostCore())
		return false;

	const DWORD dwPID = ch->GetPlayerID();

	if (m_iState == WS_STATE_RUNNING)
	{
		TWSMatch * pM = FindActiveMatchByPID(dwPID);
		if (pM != nullptr && pM->iState != WS_MATCH_RUNNING)
		{
			// PENDING/SUMMON mac oyuncusu seyircilige ALINMAZ: observer durumu
			// (SetArena + ObserverMode) StartDuel'i ve saldiri iznini bozar
			if (pM->iState == WS_MATCH_SUMMON)
			{
				if (pM->dwPIDA == dwPID)
					pM->bArrivedA = true;
				else
					pM->bArrivedB = true;
			}

			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Arenaya geldin. Mac birazdan basliyor...");
			return true;
		}

		if (pM != nullptr && pM->iState == WS_MATCH_RUNNING)
		{
			// kose warp'i sonrasi giris veya mac ici relog: client kilidini tazele
			SendMoveLockCommand(dwPID);
			return true;
		}

		// hayatta olan katilimci turlar arasinda haritada bekler (observer yapilmaz)
		const TWSEntry * pEntry = FindEntry(dwPID);
		if (pEntry != nullptr && pEntry->bAlive)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Sonraki turunu bekle. Mac zamani otomatik cagirilacaksin.");
			return true;
		}
	}

	// GM harita bayragi acikken serbest giris: NPC 11001 -> harita, kayit NPC 20082'de
	// (kayit donemi, seyircilik ve elenmis oyuncular dahil - kimse sehre geri atilmaz)
	if (quest::CQuestManager::instance().GetEventFlag("duello_harita") != 0)
		return true;

	if (m_iState == WS_STATE_RUNNING)
	{
		// harita bayragi kapali: /ws izle seyircisi arena observer olarak kaydedilir
		WORD wX = 0, wY = 0;
		if (CArenaManager::instance().GetObserverPoint(WS_TOURNAMENT_MAP_INDEX, wX, wY))
		{
			if (CArenaManager::instance().AddObserver(ch, WS_TOURNAMENT_MAP_INDEX, wX, wY))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Seyirci modundasin. Cikmak icin seyirci cikis butonunu kullan.");
				return true;
			}
		}
	}

	return false;
}

void CWSTournamentManager::ShowParticipants(LPCHARACTER ch)
{
	if (ch == nullptr)
		return;

	static const char * c_apszJobNames[] = { "Savasci", "Ninja", "Sura", "Saman" };

	if (m_vecEntries.empty())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "WS: Henuz kayitli oyuncu yok.");
		return;
	}

	int iShown = 0;
	for (const auto & e : m_vecEntries)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "WS: %2d) %s  Lv%d %s%s", ++iShown, e.szName, (int) e.bLevel,
				(e.bJob < 4) ? c_apszJobNames[e.bJob] : "?", e.bAlive ? "" : " [ELENDI]");

		if (iShown >= 40)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: ... liste kirpildi (toplam %d oyuncu)", (int) m_vecEntries.size());
			break;
		}
	}
}

bool CWSTournamentManager::BeginMatchPrep(DWORD dwPIDA, DWORD dwPIDB, int iLockSeconds)
{
	if (m_iState != WS_STATE_RUNNING)
		return false;

	// yalnizca baslamis turnuva maclari (serbest arena duellolari etkilenmez)
	TWSMatch * pM = FindActiveMatchByPair(dwPIDA, dwPIDB);
	if (pM == nullptr || pM->iState != WS_MATCH_RUNNING)
		return false;

	TWSPrepLock kLock;
	kLock.tUntil = get_global_time() + iLockSeconds + 2;	// +2: event gecikme payi (emniyet)
	kLock.tLastSync = 0;
	m_mapPrepLock[dwPIDA] = kLock;
	m_mapPrepLock[dwPIDB] = kLock;

	// client input kilidi (sure bazli: komut kaybolsa/unlock gelmese bile kendini acar)
	SendMoveLockCommand(dwPIDA);
	SendMoveLockCommand(dwPIDB);
	return true;
}

bool CWSTournamentManager::EndMatchPrep(DWORD dwPIDA, DWORD dwPIDB)
{
	const bool bHad = (m_mapPrepLock.erase(dwPIDA) + m_mapPrepLock.erase(dwPIDB)) > 0;

	if (bHad)
	{
		// client kilidini hemen ac (sure dolmasini bekletme)
		SendMoveLockCommand(dwPIDA);
		SendMoveLockCommand(dwPIDB);
	}

	return bHad;
}

void CWSTournamentManager::SendMoveLockCommand(DWORD dwPID)
{
	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(dwPID);
	if (ch == nullptr || ch->GetDesc() == nullptr)
		return;

	auto it = m_mapPrepLock.find(dwPID);
	if (it == m_mapPrepLock.end())
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WSMoveLock 0");
		return;
	}

	const int iLeft = (int) (it->second.tUntil - get_global_time());
	if (iLeft > 0)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WSMoveLock %d", iLeft);
	else
		ch->ChatPacket(CHAT_TYPE_COMMAND, "WSMoveLock 0");
}

bool CWSTournamentManager::OnPlayerMoveBlocked(LPCHARACTER ch)
{
	if (ch == nullptr || m_mapPrepLock.empty())
		return false;

	auto it = m_mapPrepLock.find(ch->GetPlayerID());
	if (it == m_mapPrepLock.end())
		return false;

	const time_t tNow = get_global_time();
	if (tNow >= it->second.tUntil)
	{
		m_mapPrepLock.erase(it);
		return false;
	}

	// hareket paketi dusuruldu: client'i saniyede bir sunucu konumuna geri cek
	// (sunucu konumu hic degismedi = ring kosesi; SyncPacket sahibi de duzeltir)
	if (tNow != it->second.tLastSync)
	{
		it->second.tLastSync = tNow;
		ch->SyncPacket();
		ch->ChatPacket(CHAT_TYPE_INFO, "WS: Hazirlik suresi - hareket kilitli, becerilerini kullanabilirsin!");
		SendMoveLockCommand(ch->GetPlayerID());	// client komutu kaybolduysa tazele
	}

	return true;
}

bool CWSTournamentManager::IsMoveLocked(DWORD dwPID) const
{
	if (m_mapPrepLock.empty())
		return false;

	auto it = m_mapPrepLock.find(dwPID);
	return it != m_mapPrepLock.end() && get_global_time() < it->second.tUntil;
}

bool CWSTournamentManager::IsGearLocked(DWORD dwPID) const
{
	if (m_iState != WS_STATE_RUNNING)
		return false;

	for (const auto & m : m_vecMatches)
	{
		if (m.iState != WS_MATCH_RUNNING && m.iState != WS_MATCH_PAUSED)
			continue;
		if (m.dwPIDA != dwPID && m.dwPIDB != dwPID)
			continue;

		// hazirlik kilidi aktifken (10 sn pencere) degisim SERBEST; dovus basladiktan
		// sonra kilit (Eski_A CanWearItem semantigi). PAUSED da kilitli: rakibin
		// kopmasi sirasinda gear degisimi avantaji olmasin.
		return !IsMoveLocked(dwPID);
	}

	return false;
}

bool CWSTournamentManager::IsPrepBlocked(DWORD dwPID1, DWORD dwPID2) const
{
	if (m_mapPrepLock.empty())
		return false;

	const time_t tNow = get_global_time();

	auto it = m_mapPrepLock.find(dwPID1);
	if (it != m_mapPrepLock.end() && tNow < it->second.tUntil)
		return true;

	it = m_mapPrepLock.find(dwPID2);
	if (it != m_mapPrepLock.end() && tNow < it->second.tUntil)
		return true;

	return false;
}

bool CWSTournamentManager::GetIntermissionPoint(DWORD dwPID, long & lX, long & lY) const
{
	if (m_iState != WS_STATE_RUNNING)
		return false;

	if (FindEntry(dwPID) == nullptr)
		return false;

	lX = WS_INTERMISSION_X;
	lY = (number(0, 1) == 0) ? WS_INTERMISSION_Y_A : WS_INTERMISSION_Y_B;
	return true;
}

bool CWSTournamentManager::GetSpectatorIntermissionPoint(long & lX, long & lY) const
{
	if (m_iState != WS_STATE_RUNNING)
		return false;

	lX = WS_INTERMISSION_X;
	lY = (number(0, 1) == 0) ? WS_INTERMISSION_Y_A : WS_INTERMISSION_Y_B;
	return true;
}

void CWSTournamentManager::OnPlayerDamage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iDam)
{
	if (m_iState != WS_STATE_RUNNING || iDam <= 0)
		return;

	if (pkVictim == nullptr || pkAttacker == nullptr)
		return;

	TWSMatch * pM = FindActiveMatchByPID(pkVictim->GetPlayerID());
	if (pM == nullptr || pM->iState != WS_MATCH_RUNNING)
		return;

	const DWORD dwAttackerPID = pkAttacker->GetPlayerID();

	if (pM->dwPIDA == dwAttackerPID && pM->dwPIDB == pkVictim->GetPlayerID())
		pM->llDamageA += iDam;
	else if (pM->dwPIDB == dwAttackerPID && pM->dwPIDA == pkVictim->GetPlayerID())
		pM->llDamageB += iDam;
}

// ============================================================================
// P2P
// ============================================================================

void CWSTournamentManager::HandleDQ(const char * c_szName, const char * c_szGMName)
{
	if (m_iState == WS_STATE_IDLE)
		return;

	TWSEntry * pEntry = FindEntryByName(c_szName);
	if (pEntry == nullptr)
	{
		sys_log(0, "WS_TOURNAMENT: DQ hedefi bulunamadi: %s (gm=%s)", c_szName, c_szGMName);
		return;
	}

	const DWORD dwPID = pEntry->dwPID;

	if (m_iState == WS_STATE_REGISTRATION)
	{
		// kayit doneminde DQ = kayittan cikar + iade
		HandleUnregister(dwPID);
		AnnounceAll("WS Turnuvasi: %s kayittan cikarildi (GM).", c_szName);
		sys_log(0, "WS_TOURNAMENT: DQ (kayit donemi) %s gm=%s", c_szName, c_szGMName);
		return;
	}

	// RUNNING: elendi, iade yok
	if (pEntry->bAlive)
	{
		pEntry->bAlive = false;
		DBUpdateEntryStatus(dwPID, 2);
		MarkBracketDirty();
	}

	TWSMatch * pM = FindActiveMatchByPID(dwPID);
	if (pM != nullptr)
	{
		// PAUSED da dahil: duraklatmada arena canli tutulur (WSPauseIfMember);
		// kapatilmazsa bekleyen rakibin m_pArena'si takili kalir (ring kilitli +
		// duello chat filtresi kalici karartir) - EndDuel PAUSED arenada guvenli
		const bool bArenaAlive = (pM->iState == WS_MATCH_RUNNING || pM->iState == WS_MATCH_PAUSED);
		ResolveMatch(*pM, (pM->dwPIDA == dwPID) ? WS_RESULT_B_WIN : WS_RESULT_A_WIN, WS_REASON_DQ);
		if (bArenaAlive)
			CArenaManager::instance().EndDuel(dwPID);	// mac fiziksel olarak kapansin (hook DONE gorup yok sayar)
	}

	MsgToPlayer(dwPID, WS_MSG_DQ);
	AnnounceAll("WS Turnuvasi: %s diskalifiye edildi (GM).", c_szName);
	sys_log(0, "WS_TOURNAMENT: DQ %s(%u) gm=%s", c_szName, dwPID, c_szGMName);
}

void CWSTournamentManager::HandleAdminOp(const TPacketGGWSTournament * p)
{
	switch (p->iValue1)
	{
		case WS_OP_CREATE:
		{
			TWSConfig kConfig;
			kConfig.llFee = 0;
			kConfig.iSetCount = p->bSetCount;
			kConfig.iMatchMinutes = p->bMatchMinutes;
			kConfig.iMinLevel = p->bMinLevel;
			kConfig.iMaxLevel = p->bMaxLevel;
			kConfig.iJobFilter = p->bJobFilter;

			const int iResult = CreateTournament(kConfig, p->iValue2, p->szName);
			if (iResult != 0)
				sys_log(0, "WS_TOURNAMENT: uzak kur istegi reddedildi kod=%d gm=%s", iResult, p->szName);
			break;
		}

		case WS_OP_CANCEL:
			CancelTournament(5, "GM iptali");
			break;

		case WS_OP_START:
			if (m_iState == WS_STATE_REGISTRATION)
				CloseRegistration(true);
			break;

		case WS_OP_DQ:
			HandleDQ(p->szName, "uzak-gm");
			break;
	}
}

void CWSTournamentManager::OnP2P(const TPacketGGWSTournament * p)
{
	if (p == nullptr)
		return;

	switch (p->bSubHeader)
	{
		case WS_GG_STATE:
			if (!IsHostCore())
			{
				m_kSync.bState = p->bState;
				m_kSync.iCount = p->iValue1;
				m_kSync.iValue = p->iValue2;
				m_kSync.kConfig.llFee = p->llGold;
				m_kSync.kConfig.iSetCount = p->bSetCount;
				m_kSync.kConfig.iMatchMinutes = p->bMatchMinutes;
				m_kSync.kConfig.iMinLevel = p->bMinLevel;
				m_kSync.kConfig.iMaxLevel = p->bMaxLevel;
				m_kSync.kConfig.iJobFilter = p->bJobFilter;
				m_kSync.tUpdated = get_global_time();
			}
			break;

		case WS_GG_REG_REQUEST:
			if (IsHostCore())
				HandleRegRequest(p);
			break;

		case WS_GG_REG_ACK:
		{
			// ucret kaldirildi: kayit host'ta REG_REQUEST aninda kesinlesti,
			// ACK yalnizca sonucu oyuncuya bildirir
			const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(p->dwPID);
			if (ch == nullptr || ch->GetDesc() == nullptr)
				break;

			ch->ChatPacket(CHAT_TYPE_INFO, "WS: %s", TextForRegResult(p->iValue1));
			break;
		}

		case WS_GG_REG_CONFIRM:
			if (IsHostCore())
				HandleRegConfirm(p);
			break;

		case WS_GG_REG_ABORT:
			if (IsHostCore())
				m_mapPendingReg.erase(p->dwPID);
			break;

		case WS_GG_UNREG_REQUEST:
			if (IsHostCore())
			{
				const int iCode = HandleUnregister(p->dwPID);

				TPacketGGWSTournament kAck;
				memset(&kAck, 0, sizeof(kAck));
				kAck.bSubHeader = WS_GG_UNREG_ACK;
				kAck.dwPID = p->dwPID;
				kAck.iValue1 = iCode;
				SendGG(kAck);
			}
			break;

		case WS_GG_UNREG_ACK:
		{
			const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(p->dwPID);
			if (ch != nullptr)
				MsgLocal(ch, (p->iValue1 == 0) ? WS_MSG_UNREG_OK : WS_MSG_UNREG_FAIL);
			break;
		}

		case WS_GG_SUMMON:
		{
			const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(p->dwPID);
			if (ch == nullptr)
				break;

			if (ch->IsDead())
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Macin basliyor ama olu durumdasin! Hemen canlan, tekrar isinlanacaksin.");
				break;
			}

			if (ch->GetDungeon() != nullptr || ch->GetWarMap() != nullptr)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Macin basliyor ama zindan/savas icindesin! Cikmazsan hukmen kaybedeceksin.");
				break;
			}

			WORD wX = 0, wY = 0;
			if (!CArenaManager::instance().GetObserverPoint(WS_TOURNAMENT_MAP_INDEX, wX, wY))
				break;

			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Macin basliyor! Arenaya isinlaniyorsun.");
			ch->WarpSet(wX * 100, wY * 100);
			break;
		}

		case WS_GG_CLAIM_NOTIFY:
		{
			const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(p->dwPID);
			if (ch != nullptr)
				ProcessClaims(ch);
			break;
		}

		case WS_GG_ADMIN_OP:
			if (IsHostCore())
				HandleAdminOp(p);
			break;

		case WS_GG_PLAYER_MSG:
		{
			const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(p->dwPID);
			if (ch != nullptr)
				MsgLocal(ch, p->iValue1);
			break;
		}
	}
}

// ============================================================================
// komutlar
// ============================================================================

void CWSTournamentManager::CmdWS(LPCHARACTER ch, const char * argument)
{
	if (ch == nullptr || ch->GetDesc() == nullptr)
		return;

	char szArg[64];
	one_argument(argument, szArg, sizeof(szArg));

	const bool bHost = IsHostCore();

	// ---- /ws (durum) ----
	if (!*szArg)
	{
		if (bHost)
		{
			switch (m_iState)
			{
				case WS_STATE_IDLE:
					ch->ChatPacket(CHAT_TYPE_INFO, "WS: Su anda aktif turnuva yok.");
					break;

				case WS_STATE_REGISTRATION:
				{
					const time_t tNow = get_global_time();
					ch->ChatPacket(CHAT_TYPE_INFO, "WS: Kayitlar ACIK! Seviye: %d-%d | Set: %d | Kayitli: %d",
							m_kConfig.iMinLevel, m_kConfig.iMaxLevel, m_kConfig.iSetCount, (int) m_vecEntries.size());
					ch->ChatPacket(CHAT_TYPE_INFO, "WS: Kalan sure: %d dk | Katilim: /ws kayit | Iptal: /ws iptal",
							(int) ((m_tRegDeadline > tNow ? m_tRegDeadline - tNow : 0) / 60) + 1);
					if (FindEntry(ch->GetPlayerID()) != nullptr)
						ch->ChatPacket(CHAT_TYPE_INFO, "WS: Bu karakter turnuvaya KAYITLI.");
					break;
				}

				case WS_STATE_RUNNING:
				{
					ch->ChatPacket(CHAT_TYPE_INFO, "WS: Turnuva DEVAM EDIYOR. Tur: %d | Kalan oyuncu: %d | Izlemek icin: /ws izle",
							m_iRound, CountAlive());

					const TWSEntry * pMe = FindEntry(ch->GetPlayerID());
					if (pMe != nullptr)
					{
						if (!pMe->bAlive)
							ch->ChatPacket(CHAT_TYPE_INFO, "WS: Turnuvadan elendin.");
						else
						{
							TWSMatch * pM = FindActiveMatchByPID(ch->GetPlayerID());
							if (pM != nullptr)
							{
								const TWSEntry * pOpp = FindEntry(pM->dwPIDA == ch->GetPlayerID() ? pM->dwPIDB : pM->dwPIDA);
								ch->ChatPacket(CHAT_TYPE_INFO, "WS: Aktif macin var! Rakip: %s", pOpp ? pOpp->szName : "?");
							}
							else
								ch->ChatPacket(CHAT_TYPE_INFO, "WS: Hayattasin, sonraki turu bekle.");
						}
					}
					break;
				}
			}
		}
		else
		{
			if (m_kSync.tUpdated == 0)
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Turnuva bilgisi henuz alinmadi (turnuva yok ya da senkron bekleniyor).");
			else if (m_kSync.bState == WS_STATE_IDLE)
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Su anda aktif turnuva yok.");
			else if (m_kSync.bState == WS_STATE_REGISTRATION)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Kayitlar ACIK! Seviye: %d-%d | Kayitli: %d | Kalan: ~%d dk",
						m_kSync.kConfig.iMinLevel, m_kSync.kConfig.iMaxLevel,
						m_kSync.iCount, m_kSync.iValue / 60 + 1);
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Katilim: /ws kayit");
			}
			else
				ch->ChatPacket(CHAT_TYPE_INFO, "WS: Turnuva DEVAM EDIYOR. Tur: %d | Kalan oyuncu: %d | Izlemek icin: /ws izle",
						m_kSync.iValue, m_kSync.iCount);
		}
		return;
	}

	// ---- /ws kayit ----
	if (strcasecmp(szArg, "kayit") == 0)
	{
		if (ch->GetGMLevel() != GM_PLAYER && !test_server)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: %s", TextForRegResult(WS_REG_ERR_GM));
			return;
		}

		if (bHost)
		{
			const int iCode = RegisterLocal(ch);
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: %s", TextForRegResult(iCode));
			return;
		}

		// uzak kayit: on kontrol (kesin karar host'ta)
		if (m_kSync.tUpdated != 0 && m_kSync.bState != WS_STATE_REGISTRATION)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: %s", TextForRegResult(WS_REG_ERR_CLOSED));
			return;
		}

		TPacketGGWSTournament p;
		memset(&p, 0, sizeof(p));
		p.bSubHeader = WS_GG_REG_REQUEST;
		p.dwPID = ch->GetPlayerID();
		p.dwAID = ch->GetDesc()->GetAccountTable().id;
		strlcpy(p.szName, ch->GetName(), sizeof(p.szName));
		strlcpy(p.szIP, ch->GetDesc()->GetHostName(), sizeof(p.szIP));
		p.bLevel = (BYTE) MINMAX(0, ch->GetLevel(), 255);
		p.bJob = (BYTE) ch->GetJob();
		SendGG(p);

		ch->ChatPacket(CHAT_TYPE_INFO, "WS: Kayit istegin iletildi, onay bekleniyor...");
		return;
	}

	// ---- /ws iptal ----
	if (strcasecmp(szArg, "iptal") == 0)
	{
		if (bHost)
		{
			const int iCode = HandleUnregister(ch->GetPlayerID());
			MsgLocal(ch, (iCode == 0) ? WS_MSG_UNREG_OK : WS_MSG_UNREG_FAIL);
			return;
		}

		TPacketGGWSTournament p;
		memset(&p, 0, sizeof(p));
		p.bSubHeader = WS_GG_UNREG_REQUEST;
		p.dwPID = ch->GetPlayerID();
		p.dwAID = ch->GetDesc()->GetAccountTable().id;
		SendGG(p);

		ch->ChatPacket(CHAT_TYPE_INFO, "WS: Kayit iptal istegin iletildi...");
		return;
	}

	// ---- /ws izle ----
	if (strcasecmp(szArg, "izle") == 0)
	{
		const int iRunState = bHost ? m_iState : (int) m_kSync.bState;
		if (iRunState != WS_STATE_RUNNING)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Su anda izlenecek bir turnuva maci yok.");
			return;
		}

		if (ch->GetMapIndex() == WS_TOURNAMENT_MAP_INDEX)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Zaten arenadasin.");
			return;
		}

		if (ch->GetArena() != nullptr || ch->GetDungeon() != nullptr || ch->GetWarMap() != nullptr)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Su anki durumunda izlemeye gidemezsin.");
			return;
		}

		if (bHost)
		{
			WORD wX = 0, wY = 0;
			if (CArenaManager::instance().GetObserverPoint(WS_TOURNAMENT_MAP_INDEX, wX, wY))
				CArenaManager::instance().AddObserver(ch, WS_TOURNAMENT_MAP_INDEX, wX, wY);
			return;
		}

		// uzak kanaldan: arena koordinatlari her core'da ayni (settings.lua) - direkt isinlan,
		// host EnterGame kancasi seyirci kaydini yapar
		WORD wX = 0, wY = 0;
		if (!CArenaManager::instance().GetObserverPoint(WS_TOURNAMENT_MAP_INDEX, wX, wY))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Arena tanimi bulunamadi.");
			return;
		}

		ch->ChatPacket(CHAT_TYPE_INFO, "WS: Arenaya seyirci olarak isinlaniyorsun...");
		ch->WarpSet(wX * 100, wY * 100);
		return;
	}

	// ---- /ws don ----
	if (strcasecmp(szArg, "don") == 0)
	{
		if (ch->GetMapIndex() != WS_TOURNAMENT_MAP_INDEX)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Arena haritasinda degilsin.");
			return;
		}

		if (ch->GetArena() != nullptr)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS: Seyirci/duello modundayken ekrandaki cikis butonunu kullan.");
			return;
		}

		ch->WarpSet(EMPIRE_START_X(ch->GetEmpire()), EMPIRE_START_Y(ch->GetEmpire()));
		return;
	}

	ch->ChatPacket(CHAT_TYPE_INFO, "WS: Kullanim: /ws | /ws kayit | /ws iptal | /ws izle | /ws don");
}

void CWSTournamentManager::CmdWSAdmin(LPCHARACTER ch, const char * argument)
{
	if (ch == nullptr)
		return;

	char szArg[64];
	argument = one_argument(argument, szArg, sizeof(szArg));

	const bool bHost = IsHostCore();

	// ---- /ws_admin kur [set] [dk] [minlv] [maxlv] [sinif 0-4] [kayit_dk] ----
	if (strcasecmp(szArg, "kur") == 0)
	{
		char szParam[64];
		long long llParams[6] = { 3, 5, 1, 135, 0, 5 };

		for (int i = 0; i < 6; ++i)
		{
			argument = one_argument(argument, szParam, sizeof(szParam));
			if (!*szParam)
				break;
			llParams[i] = atoll(szParam);
		}

		TWSConfig kConfig;
		kConfig.llFee = 0;	// ucret/odul sistemi kaldirildi
		kConfig.iSetCount = (int) llParams[0];
		kConfig.iMatchMinutes = (int) llParams[1];
		kConfig.iMinLevel = (int) llParams[2];
		kConfig.iMaxLevel = (int) llParams[3];
		kConfig.iJobFilter = (int) llParams[4];
		const int iRegMinutes = (int) llParams[5];

		if (bHost)
		{
			const int iResult = CreateTournament(kConfig, iRegMinutes, ch->GetName());
			switch (iResult)
			{
				case 0: ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Turnuva olusturuldu."); break;
				case 2: ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: DB hazir degil (sql/ws_tournament.sql uygulanmali)."); break;
				case 3: ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Zaten aktif bir turnuva var."); break;
				case 4: ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Sistem kapali (event flag ws_disabled=1)."); break;
				default: ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Turnuva kurulamadi (kod %d).", iResult); break;
			}
		}
		else
		{
			TPacketGGWSTournament p;
			memset(&p, 0, sizeof(p));
			p.bSubHeader = WS_GG_ADMIN_OP;
			p.iValue1 = WS_OP_CREATE;
			p.iValue2 = iRegMinutes;
			p.llGold = 0;
			p.bSetCount = (BYTE) MINMAX(1, kConfig.iSetCount, 5);
			p.bMatchMinutes = (BYTE) MINMAX(5, kConfig.iMatchMinutes, 15);
			p.bMinLevel = (BYTE) MINMAX(1, kConfig.iMinLevel, 255);
			p.bMaxLevel = (BYTE) MINMAX(1, kConfig.iMaxLevel, 255);
			p.bJobFilter = (BYTE) MINMAX(0, kConfig.iJobFilter, 4);
			strlcpy(p.szName, ch->GetName(), sizeof(p.szName));
			SendGG(p);

			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Kurulum istegi arena core'una (CH99) iletildi. Sonuc duyuru ile gelir.");
		}

		LogManager::instance().CharLog(ch, 0, "WS_ADMIN", "kur");
		return;
	}

	// ---- /ws_admin iptal ----
	if (strcasecmp(szArg, "iptal") == 0)
	{
		if (bHost)
			CancelTournament(5, "GM iptali");
		else
		{
			TPacketGGWSTournament p;
			memset(&p, 0, sizeof(p));
			p.bSubHeader = WS_GG_ADMIN_OP;
			p.iValue1 = WS_OP_CANCEL;
			strlcpy(p.szName, ch->GetName(), sizeof(p.szName));
			SendGG(p);
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Iptal istegi iletildi.");
		}

		LogManager::instance().CharLog(ch, 0, "WS_ADMIN", "iptal");
		return;
	}

	// ---- /ws_admin baslat ----
	if (strcasecmp(szArg, "baslat") == 0)
	{
		if (bHost)
		{
			if (m_iState == WS_STATE_REGISTRATION)
				CloseRegistration(true);
			else
				ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Kayit doneminde degil.");
		}
		else
		{
			TPacketGGWSTournament p;
			memset(&p, 0, sizeof(p));
			p.bSubHeader = WS_GG_ADMIN_OP;
			p.iValue1 = WS_OP_START;
			strlcpy(p.szName, ch->GetName(), sizeof(p.szName));
			SendGG(p);
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Baslat istegi iletildi.");
		}

		LogManager::instance().CharLog(ch, 0, "WS_ADMIN", "baslat");
		return;
	}

	// ---- /ws_admin dq <isim> ----
	if (strcasecmp(szArg, "dq") == 0)
	{
		char szTarget[64];
		one_argument(argument, szTarget, sizeof(szTarget));

		if (!*szTarget)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Kullanim: /ws_admin dq <oyuncu_adi>");
			return;
		}

		if (bHost)
			HandleDQ(szTarget, ch->GetName());
		else
		{
			TPacketGGWSTournament p;
			memset(&p, 0, sizeof(p));
			p.bSubHeader = WS_GG_ADMIN_OP;
			p.iValue1 = WS_OP_DQ;
			strlcpy(p.szName, szTarget, sizeof(p.szName));
			SendGG(p);
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: DQ istegi iletildi: %s", szTarget);
		}

		LogManager::instance().CharLog(ch, 0, "WS_ADMIN", szTarget);
		return;
	}

	// ---- /ws_admin durum ----
	if (strcasecmp(szArg, "durum") == 0)
	{
		if (!bHost)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Detayli durum icin CH99 (arena core) uzerinde olmalisin.");
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Ozet - durum: %d, oyuncu: %d", (int) m_kSync.bState, m_kSync.iCount);
			return;
		}

		ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: durum=%d db_id=%u tur=%d kayit=%d hayatta=%d bekleyen_onay=%d havuz=%lld",
				m_iState, m_dwTournamentDBID, m_iRound, (int) m_vecEntries.size(), CountAlive(),
				(int) m_mapPendingReg.size(), GetPrizePool());

		int iShown = 0;
		for (const auto & m : m_vecMatches)
		{
			const TWSEntry * pA = FindEntry(m.dwPIDA);
			const TWSEntry * pB = FindEntry(m.dwPIDB);
			ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: mac[%d] %s vs %s durum=%d sonuc=%d",
					++iShown, pA ? pA->szName : "?", pB ? pB->szName : "?", m.iState, m.iResult);
			if (iShown >= 16)
				break;
		}
		return;
	}

	ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: /ws_admin kur [set] [dk] [minlv] [maxlv] [sinif] [kayit_dk]");
	ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: /ws_admin iptal | baslat | dq <isim> | durum");
	ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Harita girisi: /e duello_harita 1 (NPC 11001) | Kayit NPC'si: 20082 (map 112)");
	ch->ChatPacket(CHAT_TYPE_INFO, "WS_ADMIN: Event flag'lar: ws_disabled ws_min_players ws_max_players ws_summon_seconds ws_reconnect_seconds ws_reconnect_limit ws_allow_same_ip");
}

// ============================================================================
// ACMD girisleri (cmd.cpp tablosundan cagrilir)
// ============================================================================

ACMD(do_ws)
{
	CWSTournamentManager::instance().CmdWS(ch, argument);
}

ACMD(do_ws_admin)
{
	CWSTournamentManager::instance().CmdWSAdmin(ch, argument);
}

#endif // ENABLE_WS_TOURNAMENT
