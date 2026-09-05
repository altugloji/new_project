#ifndef __INC_WS_TOURNAMENT_H__
#define __INC_WS_TOURNAMENT_H__

#ifdef ENABLE_WS_TOURNAMENT

#include "packet.h"	// TPacketGGWSBracket snapshot uyesi icin tam tanim gerekli

// ============================================================================
// WS 1v1 Turnuva Sistemi
// ----------------------------------------------------------------------------
// - Kayit ucretli tek eleme (single elimination) 1v1 turnuvasi.
// - Maclar mevcut CArena altyapisi uzerinde (map 112, settings.lua ringleri) oynanir.
// - Turnuva state'i SADECE arena haritasini host eden core'da yasar (ch99/core99);
//   diger kanallar GG 47 (HEADER_GG_WS_TOURNAMENT) relay ile kayit/ozet tasir.
// - Para akisi DB-first: ucret kayit aninda kesilir (PointChange + SaveReal),
//   iade/odul HER ZAMAN player.ws_claim uzerinden idempotent claim olarak odenir
//   (UPDATE ... WHERE status=0 kapisi; cift odeme yapisal olarak engellenir).
// - Boot recovery: yarim kalan turnuva iptal edilir, ucretler claim'e yazilir.
// - Bu header OXEvent.h gibi include sirasina guvenir: .cpp icinde stdafx.h ve
//   char.h'den SONRA include edilmelidir.
// ============================================================================

#define WS_TOURNAMENT_MAP_INDEX		112		// metin2_map_duel (settings.lua arena.add_map ringleri)
// turlar arasi bekleme / giris noktalari (ornek_duello_Turnuva.lua koordinatlari, cm)
#define WS_INTERMISSION_X			857400
#define WS_INTERMISSION_Y_A			19000
#define WS_INTERMISSION_Y_B			5000
#define WS_TICK_SECONDS				2		// turnuva state-machine tick araligi
#define WS_PREP_SECONDS				10		// mac/set basi hazirlik: hareket kilitli, beceri serbest
#define WS_FEE_MAX					1000000000LL	// tek kayit ucreti tavani (INT PointChange guvenligi)
#define WS_CLAIM_MAX				1900000000LL	// tek claim tavani (GOLD_MAX altinda kalir)

enum EWSTournamentState
{
	WS_STATE_IDLE			= 0,
	WS_STATE_REGISTRATION	= 1,
	WS_STATE_RUNNING		= 2,
};

enum EWSMatchState
{
	WS_MATCH_PENDING	= 0,	// ring bekliyor
	WS_MATCH_SUMMON		= 1,	// oyuncular arenaya cagrildi
	WS_MATCH_RUNNING	= 2,	// CArena duellosu oynaniyor
	WS_MATCH_DONE		= 3,	// sonuc kaydedildi
	WS_MATCH_PAUSED		= 4,	// kopma-bekleme: arena canli, rakip ringde, kopan donunce devam (Eski_A modeli)
};

enum EWSMatchResult
{
	WS_RESULT_NONE			= 0,
	WS_RESULT_A_WIN			= 1,
	WS_RESULT_B_WIN			= 2,
	WS_RESULT_DOUBLE_LOSS	= 3,	// cift eleme (pasif oyun / cift gelmeme)
};

enum EWSMatchReason
{
	WS_REASON_NONE			= 0,
	WS_REASON_SCORE			= 1,	// set skoru
	WS_REASON_WALKOVER		= 2,	// hukmen (gelmeme / disconnect)
	WS_REASON_TIMEOUT_HP	= 3,	// sure doldu, HP% ustunlugu
	WS_REASON_TIMEOUT_DMG	= 4,	// sure doldu, hasar ustunlugu
	WS_REASON_DQ			= 5,	// GM diskalifiyesi
	WS_REASON_CANCEL		= 6,	// turnuva iptali
	WS_REASON_UNRESOLVED	= 7,	// arena sonucsuz kapandi (guvenlik agi)
	WS_REASON_PASSIVE		= 8,	// sure doldu, ikisi de savasmadi
};

enum EWSGGSubHeader
{
	WS_GG_STATE			= 0,	// host -> tum core'lar: ozet durum senkronu
	WS_GG_REG_REQUEST	= 1,	// oyuncu core'u -> host: kayit istegi
	WS_GG_REG_ACK		= 2,	// host -> tum core'lar: kayit karari (iValue1=0 kabul, degilse hata kodu)
	WS_GG_REG_CONFIRM	= 3,	// oyuncu core'u -> host: ucret kesildi, kaydi kesinlestir
	WS_GG_REG_ABORT		= 4,	// oyuncu core'u -> host: ucret kesilemedi, slotu birak
	WS_GG_UNREG_REQUEST	= 5,	// oyuncu core'u -> host: kayit iptali
	WS_GG_UNREG_ACK		= 6,	// host -> tum core'lar: iptal sonucu (iValue1 kod)
	WS_GG_SUMMON		= 7,	// host -> tum core'lar: oyuncuyu arenaya isinla
	WS_GG_CLAIM_NOTIFY	= 8,	// host -> tum core'lar: bekleyen claim odemesini dene
	WS_GG_ADMIN_OP		= 9,	// herhangi core -> host: GM yonetim islemi (iValue1=op)
	WS_GG_PLAYER_MSG	= 10,	// host -> tum core'lar: oyuncuya kod bazli mesaj (iValue1=kod)
};

enum EWSAdminOp
{
	WS_OP_CREATE	= 1,
	WS_OP_CANCEL	= 2,
	WS_OP_START		= 3,	// kayit suresini beklemeden baslat
	WS_OP_DQ		= 4,	// szName = hedef oyuncu adi
};

enum EWSRegResult
{
	WS_REG_OK				= 0,
	WS_REG_ERR_CLOSED		= 1,
	WS_REG_ERR_FULL			= 2,
	WS_REG_ERR_DUP_PID		= 3,
	WS_REG_ERR_DUP_ACCOUNT	= 4,
	WS_REG_ERR_LEVEL		= 5,
	WS_REG_ERR_JOB			= 6,
	WS_REG_ERR_GOLD			= 7,
	WS_REG_ERR_GM			= 8,
	WS_REG_ERR_DB			= 9,
	WS_REG_ERR_IP			= 10,
};

enum EWSPlayerMsg
{
	WS_MSG_WALKOVER_WIN		= 1,
	WS_MSG_WALKOVER_LOSS	= 2,
	WS_MSG_DOUBLE_LOSS		= 3,
	WS_MSG_DQ				= 4,
	WS_MSG_CANCEL_REFUND	= 5,
	WS_MSG_MATCH_LOSS		= 6,
	WS_MSG_MATCH_WIN		= 7,
	WS_MSG_BYE				= 8,
	WS_MSG_CHAMPION			= 9,
	WS_MSG_UNREG_OK			= 10,
	WS_MSG_UNREG_FAIL		= 11,
};

struct TWSConfig
{
	long long	llFee;			// kayit ucreti (yang)
	int			iSetCount;		// mac basina set (galibiyet) sayisi
	int			iMatchMinutes;	// mac suresi (dk)
	int			iMinLevel;
	int			iMaxLevel;
	int			iJobFilter;		// 0 = tum siniflar, 1..4 = JOB 0..3
	TWSConfig() : llFee(0), iSetCount(3), iMatchMinutes(5), iMinLevel(1), iMaxLevel(135), iJobFilter(0) {}
};

struct TWSEntry
{
	DWORD		dwPID;
	DWORD		dwAID;
	char		szName[CHARACTER_NAME_MAX_LEN + 1];
	char		szIP[16];
	BYTE		bLevel;
	BYTE		bJob;
	bool		bAlive;
	bool		bRefunded;
	int			iByeCount;
	TWSEntry() : dwPID(0), dwAID(0), bLevel(0), bJob(0), bAlive(true), bRefunded(false), iByeCount(0) { szName[0] = '\0'; szIP[0] = '\0'; }
};

struct TWSMatch
{
	int			iRound;
	DWORD		dwPIDA;
	DWORD		dwPIDB;
	int			iState;			// EWSMatchState
	int			iResult;		// EWSMatchResult
	int			iReason;		// EWSMatchReason
	time_t		tSummonDeadline;
	time_t		tNextSummonRetry;
	bool		bArrivedA;
	bool		bArrivedB;
	long long	llDamageA;		// A'nin verdigi toplam hasar
	long long	llDamageB;
	DWORD		dwDBID;			// player.ws_match satir id

	// kopma bekleme (reconnect grace): skor korunur, kopma hakki sinirli
	bool		bResume;
	DWORD		dwResumeSetA;
	DWORD		dwResumeSetB;
	BYTE		byDcCountA;
	BYTE		byDcCountB;
	time_t		tRunStart;		// bu kosunun basladigi an (mac saati kalanini hesaplamak icin)
	int			iRemainSec;		// mac saatinden kalan sure (pause aninda dondurulur)

	TWSMatch() : iRound(0), dwPIDA(0), dwPIDB(0), iState(WS_MATCH_PENDING), iResult(WS_RESULT_NONE), iReason(WS_REASON_NONE),
		tSummonDeadline(0), tNextSummonRetry(0), bArrivedA(false), bArrivedB(false), llDamageA(0), llDamageB(0), dwDBID(0),
		bResume(false), dwResumeSetA(0), dwResumeSetB(0), byDcCountA(0), byDcCountB(0), tRunStart(0), iRemainSec(0) {}
};

// diger kanallardaki /ws goruntusu icin host'tan yayilan ozet
struct TWSSyncState
{
	BYTE		bState;
	int			iCount;			// kayit sayisi / hayatta kalan sayisi
	int			iValue;			// REG: kalan sn, RUNNING: tur no
	TWSConfig	kConfig;
	time_t		tUpdated;
	TWSSyncState() : bState(WS_STATE_IDLE), iCount(0), iValue(0), tUpdated(0) {}
};

// kayit onayi bekleyen uzak oyuncu (REG_ACK gonderildi, REG_CONFIRM bekleniyor)
struct TWSPendingReg
{
	DWORD		dwAID;
	char		szName[CHARACTER_NAME_MAX_LEN + 1];
	char		szIP[16];
	BYTE		bLevel;
	BYTE		bJob;
	time_t		tExpire;
	TWSPendingReg() : dwAID(0), bLevel(0), bJob(0), tExpire(0) { szName[0] = '\0'; szIP[0] = '\0'; }
};

class CWSTournamentManager : public singleton<CWSTournamentManager>
{
	public:
		CWSTournamentManager();
		~CWSTournamentManager();

		void	Initialize();		// DB kontrolu + boot recovery (tum core'larda calisir, satir bazli yarissiz)
		void	Destroy();

		bool	IsHostCore() const;						// arena haritasi bu core'da mi
		bool	IsBusy() const { return m_iState == WS_STATE_RUNNING; }	// ringler turnuvaya ayrildi mi
		int		GetState() const { return m_iState; }

		// komutlar (cmd.cpp tablosundan)
		void	CmdWS(LPCHARACTER ch, const char * argument);
		void	CmdWSAdmin(LPCHARACTER ch, const char * argument);

		// P2P
		void	OnP2P(const struct SPacketGGWSTournament * p);

		// oyun kancalari
		void	OnPlayerLogin(LPCHARACTER ch);				// host: mac ici relog'da anahtar tazele / maci devam ettir (Entergame sonu)
		void	BroadcastToWatchers(const void * c_pvData, int iSize);	// map 112 seyirci yayini (aktif duellocular haric)
		bool	OnPlayerEnterArenaMap(LPCHARACTER ch);		// host: davetli/seyirci ise true (haritada kalir)
		void	OnPlayerDamage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iDam);

		// client paneli (CG 235 -> GC 247): her core snapshot'tan cevaplar
		void	OnClientInfoRequest(LPCHARACTER ch);
		void	ApplySnapshot(const struct SPacketGGWSBracket * p);

		// --- quest API (NPC 20082 / questlua_ws.cpp; NPC map 112'de -> host core'da calisir) ---
		int		QuestRegister(LPCHARACTER ch) { return RegisterLocal(ch); }
		int		QuestUnregister(DWORD dwPID) { return HandleUnregister(dwPID); }
		int		QuestCreate(const TWSConfig & kConfig, int iRegMinutes, const char * c_szGMName) { return CreateTournament(kConfig, iRegMinutes, c_szGMName); }
		void	QuestCancel() { CancelTournament(5, "GM iptali"); }
		void	QuestStartNow() { if (m_iState == WS_STATE_REGISTRATION) CloseRegistration(true); }
		long long	GetFee() const { return m_kConfig.llFee; }
		int		GetEntryCount() const { return (int) m_vecEntries.size(); }
		bool	IsRegistered(DWORD dwPID) const { return FindEntry(dwPID) != nullptr; }
		void	ShowParticipants(LPCHARACTER ch);

		// turlar arasi donus noktasi: turnuva katilimcilari sehre degil haritada kalir
		bool	GetIntermissionPoint(DWORD dwPID, long & lX, long & lY) const;
		bool	GetSpectatorIntermissionPoint(long & lX, long & lY) const;

		// --- hazirlik kilidi (arena.cpp ready event + input_main Move + battle.cpp) ---
		// mac/set baslangicinda hareket kilitli, beceri serbest; client'a "WSMoveLock <sn>"
		// komutu da gider (client input kilidi; eski client'ta komut yok sayilir, server yine korur)
		bool	BeginMatchPrep(DWORD dwPIDA, DWORD dwPIDB, int iLockSeconds = WS_PREP_SECONDS);
		bool	EndMatchPrep(DWORD dwPIDA, DWORD dwPIDB);
		void	SendMoveLockCommand(DWORD dwPID);
		bool	OnPlayerMoveBlocked(LPCHARACTER ch);					// sync + mesaj (throttle icerde)
		bool	IsMoveLocked(DWORD dwPID) const;						// sure kontrollu sade sorgu
		bool	IsPrepBlocked(DWORD dwPID1, DWORD dwPID2) const;		// cift-ici saldiri engeli
		bool	IsGearLocked(DWORD dwPID) const;						// dovus sirasinda ekipman degistirme kilidi (hazirlikta serbest)

		// arena kancalari (arena.cpp) - set skorlari kopma-bekleme icin tasinir
		void	OnArenaMatchEnd(DWORD dwWinnerPID, DWORD dwLoserPID);
		// kopma: true = mac yerinde duraklatildi (arena KAPATILMAZ, rakip ringde bekler);
		// false = turnuva disi ya da hak bitti (vanilla EndDuel akisi calisir)
		bool	OnArenaPlayerDisconnect(DWORD dwArenaPIDA, DWORD dwArenaPIDB, DWORD dwDcPID);
		void	OnArenaTimeout(DWORD dwPIDA, DWORD dwPIDB, DWORD dwSetA, DWORD dwSetB, LPCHARACTER chA, LPCHARACTER chB);
		void	OnArenaMatchAborted(DWORD dwPIDA, DWORD dwPIDB, bool bAPresent, bool bBPresent, DWORD dwSetA, DWORD dwSetB);
		void	OnArenaClosed(DWORD dwPIDA, DWORD dwPIDB, DWORD dwSetA, DWORD dwSetB);

		// tick (EVENTFUNC tarafindan cagrilir); 0 donerse event biter
		int		Tick();
		void	ClearTickEvent() { m_pkTickEvent = nullptr; }

	private:
		// --- host tarafi akis ---
		int		CreateTournament(const TWSConfig & kConfig, int iRegMinutes, const char * c_szGMName);
		void	CancelTournament(int iDBStatus, const char * c_szReason);
		void	CloseRegistration(bool bForced);
		void	BuildRound(int iRound);
		void	ProcessMatches(time_t tNow);
		bool	TryResumePausedMatch(TWSMatch & m);			// iki taraf PHASE_GAME'deyse maci hemen devam ettir
		void	CheckRoundEnd(time_t tNow);
		void	BeginSummon(TWSMatch & m, time_t tNow);
		void	EnterReconnectWait(TWSMatch & m, DWORD dwMatchSetA, DWORD dwMatchSetB, const char * c_szDcName);
		void	SummonPlayer(DWORD dwPID);
		bool	TryStartDuel(TWSMatch & m);
		void	ResolveMatch(TWSMatch & m, int iResult, int iReason);
		void	FinishWithChampion(const TWSEntry & kChampion);
		void	FinishNoChampion();
		void	ResetRuntime();

		// --- kayit ---
		int		CheckRegistration(DWORD dwPID, DWORD dwAID, BYTE bLevel, BYTE bJob, const char * c_szIP) const;
		int		RegisterLocal(LPCHARACTER ch);
		void	HandleRegRequest(const struct SPacketGGWSTournament * p);
		void	HandleRegConfirm(const struct SPacketGGWSTournament * p);
		int		HandleUnregister(DWORD dwPID);
		bool	AddEntry(DWORD dwPID, DWORD dwAID, const char * c_szName, BYTE bLevel, BYTE bJob, const char * c_szIP);
		void	ExpirePendingConfirms(time_t tNow);
		void	HandleAdminOp(const struct SPacketGGWSTournament * p);
		void	HandleDQ(const char * c_szName, const char * c_szGMName);

		// --- para / claim ---
		void	InsertClaim(DWORD dwAID, DWORD dwPID, long long llGold, const char * c_szReason);
		void	InsertPrizeClaims(DWORD dwAID, DWORD dwPID, long long llTotal, const char * c_szReason);
		void	ReleaseSafetyClaimOrRefund(const struct SPacketGGWSTournament * p, const char * c_szReason);
		void	NotifyClaim(DWORD dwPID, DWORD dwAID);
		void	ProcessClaims(LPCHARACTER ch);
		void	RefundAllEntries(const char * c_szReason);
		long long	GetPrizePool() const;

		// --- yardimcilar ---
		TWSEntry *	FindEntry(DWORD dwPID);
		TWSEntry *	FindEntryByName(const char * c_szName);
		const TWSEntry *	FindEntry(DWORD dwPID) const;
		TWSMatch *	FindActiveMatchByPair(DWORD dwPID1, DWORD dwPID2);
		TWSMatch *	FindActiveMatchByPID(DWORD dwPID);
		int		CountAlive() const;
		int		GetFreeRingHint() const;
		void	StartTickEvent();
		void	MarkBracketDirty() { m_bBracketDirty = true; }
		void	BuildAndBroadcastBracket();		// host: snapshot uret + tum core'lara yay + yerel uygula
		void	SendGG(struct SPacketGGWSTournament & p);
		void	SendStateSync();
		void	AnnounceAll(const char * c_szFormat, ...);
		void	MsgToPlayer(DWORD dwPID, int iMsgCode);
		void	MsgLocal(LPCHARACTER ch, int iMsgCode);
		static const char *	TextForPlayerMsg(int iMsgCode);
		static const char *	TextForRegResult(int iCode);
		void	DBUpdateTournamentStatus(int iStatus);
		void	DBUpdateEntryStatus(DWORD dwPID, int iStatus);
		void	DBUpdateMatch(const TWSMatch & m);
		static int		GetFlagOr(const char * c_szFlag, int iDefault);
		static long long	ClampClaim(long long llGold);

	private:
		int			m_iState;
		bool		m_bDBReady;
		DWORD		m_dwTournamentDBID;
		TWSConfig	m_kConfig;
		int			m_iRound;
		time_t		m_tRegDeadline;
		time_t		m_tLastAnnounce;
		time_t		m_tLastSync;
		time_t		m_tLastResolve;

		std::vector<TWSEntry>	m_vecEntries;
		std::vector<TWSMatch>	m_vecMatches;
		std::map<DWORD, TWSPendingReg>	m_mapPendingReg;

		// hazirlik kilidi: pid -> (bitis, son sync zamani)
		struct TWSPrepLock
		{
			time_t	tUntil;
			time_t	tLastSync;
		};
		std::map<DWORD, TWSPrepLock>	m_mapPrepLock;

		LPEVENT		m_pkTickEvent;

		// host disi core'larin /ws goruntusu
		TWSSyncState	m_kSync;

		// client panelini besleyen bracket goruntusu (host uretir, GG 48 ile herkese yayilir)
		TPacketGGWSBracket	m_kSnapshot;
		time_t		m_tSnapshotAt;
		bool		m_bBracketDirty;
		time_t		m_tLastBracketSync;
};

#endif // ENABLE_WS_TOURNAMENT
#endif // __INC_WS_TOURNAMENT_H__
