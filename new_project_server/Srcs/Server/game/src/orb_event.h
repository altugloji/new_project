#ifndef __INC_ORB_EVENT_H__
#define __INC_ORB_EVENT_H__

#ifdef ENABLE_ORB_EVENT

// ============================================================================
// Kure Avi (Orb Event)
// ----------------------------------------------------------------------------
// - Her saatin ORB_EVENT_START_MINUTE. dakikasinda (varsayilan :30) ORB_EVENT_DURATION_SEC (300 sn) suren tur: oyuncunun etrafinda
//   KISIYE OZEL kureler dogar (sadece sahibi gorur/toplar; client efektleri
//   CHAT_TYPE_COMMAND satirlariyla kurulur, server'da entity YOKTUR).
//   Mavi kure +2 puan (ORB_EVENT_BLUE_POINTS), beyaz (gumus) kure -1 puan (ORB_EVENT_WHITE_POINTS,
//   ceza; toplam negatif olabilir, odul icin toplam > 0 sart). ORB_EVENT_ORB_COUNT kure/oyuncu.
// - Toplama server tarafinda: 200 ms tick'te oyuncunun son->simdiki konum
//   parcasi ile kure arasindaki 2B nokta-dogru parcasi mesafesi <= PICK_RADIUS.
//   Hareket butcesi (GetMoveSpeed tabanli) asilirsa o tick toplama yok;
//   RELOCATE_DIST'ten uzaga ziplama (isinlanma) = kureler yeniden dogar.
//   Suphe takibi/loglama YOK (kullanici karari).
// - Zindanlar kapali: map index > ORB_EVENT_MAX_MAP_INDEX (instance kopyalari)
//   + ORB_EVENT_BLOCKED_MAPS statik listesi (kullanici duzenler) + GetDungeon().
// - Skor: core basina MUTLAK satir (player.orb_event_score PK event_id,pid,core_id),
//   saniyede bir idempotent INSERT ... ON DUPLICATE KEY UPDATE flush; oyuncu core
//   degistirince diger core'larin toplami 2 sn sonra okunur (iBaseScore, isaretli).
// - Siralama: MASTER core (ch1 + map 1 host) 3 sn'de bir DB'den top-100 cekip
//   GG 51 (TPacketGGOrbEvent sub 1) ile tum core'lara yayar; her core kendi
//   hazir oyuncularina orb_top/orb_me satirlarini gonderir.
// - Odul: tur bitisinden 60 sn sonra master Distribute(): tek transaction'da
//   player.orb_event_reward + player.player_gift (ITEM 50253; GIFT_SYSTEM sart).
//   1-3. sira TOP3, 4-50 TOP50, 51+ REST adet. dist_token ile cift dagitim
//   kilidi; GG 51 sub 2 ile diger core'lar kazananlara bildirim yapar.
// - Bayraklar (cluster geneli, quest event flag):
//     orb_event        1 = saatlik program acik (/e orb_event 1)
//     orb_event_test   GM test turu baslangic epoch'u (/orb_admin start)
//     orb_event_stop   bu eid'li tur hemen biter (odul yine dagitilir)
//     orb_event_cancel bu eid'li tur hemen biter, state=4 (ODUL YOK)
//   eid = tur baslangic epoch'u (program: saat basi; test: bayrak degeri).
// - Wire (server->client CHAT_TYPE_COMMAND, her satir < ORB_EVENT_LINE_MAX):
//     orb_start <eid> <kalanSn> <odulEsigi>
//     orb_put <slot>,<gx>,<gy>,<tip>;...   (en fazla 12 kayit/satir; ayni slot = degistir; tip 1 beyaz 2 mavi 3 sari; slot ORB_EVENT_ORB_COUNT = sari)
//     orb_take <slot> <kazanc> <toplam> <nx> <ny> <ntip>   (ntip 0 = yenisi yok)
//     orb_clear
//     orb_del <slot>   (sari kurenin omru doldu: client sessizce siler)
//     orb_top <kalanSn>#<sira>|<isim>|<puan>;...   (<=10 kayit, isim <=16)
//     orb_me <sira> <puan> <katilimci>   (sira 0 = ilk 100 disi)
//     orb_end <eid>
//     orb_result <sira> <adet>
//   client->server: /orb_ready (entergame sonrasi), GM /orb_admin start|stop|cancel|status
// - LPCHARACTER tick'ler arasi SAKLANMAZ: her tick FindByPID + VID eslesmesi.
// - Bu header include sirasina guvenir (ffa_event.h gibi): .cpp icinde stdafx.h
//   ve char.h'den SONRA include edilmelidir. packet.h'e ihtiyac duymaz
//   (TPacketGGOrbEvent ileri bildirim; onbellek kendi yapisinda tutulur).
// ============================================================================

// packet.h (GG 51, bilerek ifdef'siz): TPacketGGOrbEvent bir typedef adidir (struct etiketi SPacketGGOrbEvent),
// bu yuzden ileri bildirim etiket uzerinden yapilir; ayni tipe tekrar typedef C++'ta gecerlidir
struct SPacketGGOrbEvent;
typedef struct SPacketGGOrbEvent TPacketGGOrbEvent;

enum
{
	ORB_EVENT_SNAP_TOP_MAX	= 10,	// snapshot onbellegi ilk 10 (packet.h ORB_EVENT_TOP_COUNT ile ayni; static_assert .cpp)
	ORB_EVENT_SNAP_RANK_MAX	= 100,	// snapshot onbellegi ilk 100 sira (ORB_EVENT_RANK_COUNT)
	ORB_EVENT_NAME_BUF		= 25,	// CHARACTER_NAME_MAX_LEN + 1 (static_assert .cpp)
};

struct TOrb
{
	long	x;
	long	y;
	BYTE	type;		// 1 = beyaz (ORB_EVENT_WHITE_POINTS, eksi), 2 = mavi (ORB_EVENT_BLUE_POINTS), 3 = sari (ORB_EVENT_GOLD_POINTS, 3 sn omurlu)
	bool	valid;

	TOrb() : x(0), y(0), type(0), valid(false) {}
};

struct TOrbSession
{
	DWORD	dwPID;
	DWORD	dwVID;			// 0 = bu core'da cevrimdisi (skor kalir, flush devam eder)
	long	lMapIndex;
	long	lLastX;
	long	lLastY;
	bool	bHasLast;
	float	fBudget;		// hareket butcesi (cm)
	TOrb	aOrbs[ORB_EVENT_ORB_COUNT + 1];	// son slot (ORB_EVENT_ORB_COUNT) = sari kure (en fazla 1, omurlu)
	bool	bOrbsActive;	// uygun haritada kureler uretildi
	int		iScore;			// bu core'da bu turda kazanilan MUTLAK puan (isaretli: beyaz kure eksi verir)
	DWORD	dwBlue;
	DWORD	dwWhite;
	DWORD	dwGold;
	unsigned long long	ullGoldExpireMs;	// sari kure kaybolma ani (ms epoch; 0 = yok)
	unsigned long long	ullGoldNextRollMs;	// bir sonraki sari kure sans kontrolu (ms epoch)
	bool	bGoldSpawnPending;	// sans tuttu ama yer bulunamadi: sans harcanmadan kisa sure sonra yeniden denenir
	int		iBaseScore;		// diger core'lardan gelen toplam (SUM, isaretli)
	bool	bBaseLoaded;
	time_t	tBaseReadAt;	// bu andan sonra okunur (ready + 2 sn)
	bool	bDirty;			// flush bekliyor
	unsigned long long	ullLastTs;	// son toplama ms epoch (beraberlik kirici, core'lar arasi karsilastirilabilir)
	bool	bGenPending;	// ilk uretim kuyrugunda
	time_t	tLastResend;	// ayni VID ile ikinci /orb_ready yeniden gonderim ani (saniyede en fazla bir)

	TOrbSession()
		: dwPID(0), dwVID(0), lMapIndex(0), lLastX(0), lLastY(0), bHasLast(false), fBudget(0.0f)
		, bOrbsActive(false), iScore(0), dwBlue(0), dwWhite(0), dwGold(0), ullGoldExpireMs(0), ullGoldNextRollMs(0), bGoldSpawnPending(false), iBaseScore(0), bBaseLoaded(false)
		, tBaseReadAt(0), bDirty(false), ullLastTs(0), bGenPending(false), tLastResend(0)
	{
	}
};

struct TOrbSnapshotTop
{
	DWORD	dwPID;
	int		iScore;
	char	szName[ORB_EVENT_NAME_BUF];
};

struct TOrbSnapshotRank
{
	DWORD	dwPID;
	int		iScore;
};

// master'dan gelen (veya master'in kendi urettigi) siralama goruntusu
struct TOrbSnapshot
{
	DWORD				dwEventID;
	DWORD				dwParticipants;
	BYTE				bTopCount;
	BYTE				bRankCount;
	TOrbSnapshotTop		top[ORB_EVENT_SNAP_TOP_MAX];
	TOrbSnapshotRank	rank[ORB_EVENT_SNAP_RANK_MAX];
	time_t				tReceived;		// 0 = yok

	TOrbSnapshot() { Clear(); }

	void Clear()
	{
		dwEventID = 0;
		dwParticipants = 0;
		bTopCount = 0;
		bRankCount = 0;
		memset(top, 0, sizeof(top));
		memset(rank, 0, sizeof(rank));
		tReceived = 0;
	}
};

class COrbEventManager : public singleton<COrbEventManager>
{
	public:
		COrbEventManager();
		~COrbEventManager();

		void	Initialize();						// main.cpp (ffaManager.Initialize ile ayni blok)
		void	Destroy();							// main.cpp shutdown
		void	OnReady(LPCHARACTER ch);			// /orb_ready (client entergame sonrasi gonderir)
		void	OnDestroy(LPCHARACTER ch);			// CHARACTER::Destroy
		void	OnP2P(const TPacketGGOrbEvent* p);	// input_p2p.cpp (GG 51)
		void	Tick();								// 200 ms event
		bool	IsRoundActive() const { return m_bActive; }
		DWORD	GetEventID() const { return m_dwEventID; }
		bool	IsMaster() const;					// g_bChannel == 1 && map 1 bu core'da
		void	AdminCommand(LPCHARACTER ch, const char* szSub);	// start|stop|cancel|status

	private:
		// program / tur yasam dongusu
		void	ComputeSchedule(time_t tNow, bool & bActive, DWORD & dwEventID, time_t & tEnd);
		void	StartRound(DWORD dwEventID, time_t tEnd);
		void	EndRound();

		// oyuncu / harita
		bool	IsMapAllowed(long lMapIndex) const;
		bool	IsEligible(LPCHARACTER ch) const;
		LPCHARACTER	FindOnline(TOrbSession & s);		// FindByPID + VID eslesmesi; yoksa dwVID = 0
		void	SendStartTo(LPCHARACTER ch);

		// kure uretimi / toplama
		bool	TryPlaceOrb(const TOrbSession & s, long lMapIndex, long px, long py, int iSlot, TOrb & out, int iMaxDist = ORB_EVENT_SPAWN_MAX_DIST, BYTE bForceType = 0) const;
		void	GoldStep(TOrbSession & s, LPCHARACTER ch);	// sari kure: omur/sans dongusu (her tick)
		bool	ExpireGoldIfDue(TOrbSession & s, LPCHARACTER ch, unsigned long long ullNow);	// omru dolan sari kureyi siler (orb_del); true = silindi
		bool	IsLineClear(long lMapIndex, long ax, long ay, long bx, long by) const;
		void	GenerateAll(TOrbSession & s, LPCHARACTER ch);
		void	ProcessSession(TOrbSession & s, LPCHARACTER ch, int & iGenBudget);
		void	RelocationPass();
		void	SendOrbPutSlots(LPCHARACTER ch, const TOrbSession & s, const int * aiSlots, int iCount);
		void	SendOrbPutAll(LPCHARACTER ch, const TOrbSession & s);

		// skor / DB
		void	FlushScores();
		void	BaseReadPass(time_t tNow);
		void	RequestBaseScore(TOrbSession & s);
		void	OnBaseScoreResult(DWORD dwEventID, DWORD dwPID, int iSum, bool bOK);	// bOK false = DB hatasi, yeniden denenir

		// siralama snapshot'i
		void	PollSnapshot(time_t tNow);
		void	OnPollRowsResult(DWORD dwEventID, bool bOK, const TOrbSnapshot & kRows);
		void	OnPollCountResult(DWORD dwEventID, bool bOK, DWORD dwCount);
		void	ApplySnapshot();
		void	SendSnapshotTo(LPCHARACTER ch, const TOrbSession * pSession);
		void	BroadcastSnapshotP2P();

		// odul dagitimi (master)
		void	CheckPendingRewards();
		void	OnPendingRewardsResult(const std::vector<DWORD> & vecEventIDs);
		void	MarkCancelled(DWORD dwEventID);
		void	Distribute(DWORD dwEventID);
		void	NotifyWinners(DWORD dwEventID);

		std::map<DWORD, TOrbSession>	m_mapSessions;		// PID -> oturum (tur boyunca yasar)
		std::map<DWORD, DWORD>			m_mapReady;			// PID -> VID (bu core'da cevrimici hazir oyuncular)

		bool		m_bDBReady;
		bool		m_bActive;
		DWORD		m_dwEventID;
		time_t		m_tRoundEnd;
		time_t		m_tRoundStartedAt;
		DWORD		m_dwLastEventID;	// bitis sonrasi 10 sn'lik snapshot poll'u icin
		time_t		m_tLastRoundEnd;

		TOrbSnapshot	m_kSnapshot;		// son uygulanan goruntu
		TOrbSnapshot	m_kPending;			// master: satirlar geldi, COUNT bekleniyor
		bool		m_bPendingValid;
		bool		m_bPollInFlight;
		time_t		m_tPollSentAt;
		time_t		m_tLastPoll;
		time_t		m_tLastRewardCheck;

		LPEVENT		m_pkTickEvent;
		int			m_iTickCounter;
};

// cmd.cpp komut tablosu (ACMD makrosunun acik hali: cmd.h include sirasina bagimli olmasin)
void do_orb_ready(LPCHARACTER ch, const char * argument, int cmd, int subcmd);
void do_orb_admin(LPCHARACTER ch, const char * argument, int cmd, int subcmd);

#endif // ENABLE_ORB_EVENT

#endif // __INC_ORB_EVENT_H__
