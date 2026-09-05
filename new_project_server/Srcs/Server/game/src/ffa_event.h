#ifndef __INC_FFA_EVENT_H__
#define __INC_FFA_EVENT_H__

#ifdef ENABLE_FFA_EVENT

// ============================================================================
// Anonim FFA Savas Etkinligi (Kaos Savasi)
// ----------------------------------------------------------------------------
// - Map 70 (metin2_map_nusluck01) uzerinde herkes-herkese PvP: ayni imparatorluk,
//   ayni lonca, ayni parti fark etmez (battle_is_attackable erken-izin kapisi).
// - Kimlik maskesi SERVER tarafinda: haritadaki oyuncular birbirini FFA_MASK_NAME
//   ("Player") olarak gorur; lonca/unvan/seviye gizli. Izleyiciye DUSMAN bEmpire
//   gonderilir: client IsAttackableInstance farkli-imparatorluk dalinda saldiriya
//   kosulsuz izin verir + isim kirmizi (NAMECOLOR_PVP) cizilir. (PK_MODE_FREE
//   denemesi ise yaramazdi: client SALDIRANIN kendi modunu okur - canli test.)
//   Kendine ve GM izleyicilere gercek kimlik gider.
// - Olum cezasiz (item drop / karma / EP / exp yok), 5 sn sonra rastgele spawn
//   noktasinda tam canla dogus + 5 sn dogus korumasi (revive-invisible cift yonlu
//   dokunulmazlik). Kill sayaci son-vuran; ayni kurban icin cooldown (feed onlemi).
// - Acilis/kapanis: /e ffa_open 1|0 (event flag, cluster geneli). Sure: ffa_minutes
//   flag'i (0 = FFA_DEFAULT_MINUTES). Sure dolunca bayrak otomatik dusurulur;
//   kapaniste haritadakiler sehre suprulur. Maske/saldiri kapilari HARITA-varligina
//   baglidir (bayraga degil): bayrak dususu iceridekileri canli unmask edemez.
// - Skor yayini: CHAT_TYPE_COMMAND "ffa_rank <kalanSn>#<sira>|<isim>|<kill>|<olum>|<irk>;...#<benSira>|<benKill>|<benOlum>"
//   (Faz 2 client penceresi bu komutu okuyacak; eski client komutu yok sayar).
// - Bu header include sirasina guvenir (ws_tournament.h gibi): .cpp icinde stdafx.h
//   ve char.h'den SONRA include edilmelidir.
// ============================================================================

#define FFA_EVENT_MAP_INDEX			70			// metin2_map_nusluck01 (test haritasi)
#define FFA_MASK_NAME				"Player"	// haritada gorunen takma isim (kullanici karari)
#define FFA_SPAWN_X					829900		// giris/dogus noktasi (global cm; kullanici karari)
#define FFA_SPAWN_Y					763300
#define FFA_SPAWN_SPREAD			600			// dogus noktasi rastgele yayilim (+-cm; spawn-camp onlemi)
#define FFA_RESPAWN_SECONDS			5			// olumden dogusa gecen sure
#define FFA_DEFAULT_MINUTES			20			// varsayilan savas suresi (ffa_minutes flag ile ezilir; isinma haric)
#define FFA_WARMUP_SECONDS			60			// isinma evresi: giris serbest, PC-PC saldiri kapali, ortada sayac
#define FFA_TICK_SECONDS			2			// yonetici tick araligi
#define FFA_RANK_TOP_COUNT			10			// skor yayinindaki satir sayisi
#define FFA_BROADCAST_MIN_INTERVAL	3			// skor yayini alt siniri (sn)

// Gorsel uniforma (kullanici vnum secimleri, 2026-09-04): maskeli izleyicilere gercek
// ekipman yerine sabit gorunum gider (guc DEGISMEZ, sadece gorunus). Silah TUR bazinda
// sabitlenir ki client vurus animasyonlari dogru kalsin; zirh sinif bazinda (modeller
// sinifa ozel). Kask/sac/acce gizlenir. Bilinmeyen sinif/tur -> 0 (varsayilan gorunum).
#define FFA_UNIFORM_ARMOR_WARRIOR	11299
#define FFA_UNIFORM_ARMOR_ASSASSIN	11499
#define FFA_UNIFORM_ARMOR_SURA		11699
#define FFA_UNIFORM_ARMOR_SHAMAN	11899
#define FFA_UNIFORM_WEAPON_SWORD	149			// tek el
#define FFA_UNIFORM_WEAPON_DAGGER	1109		// bicak
#define FFA_UNIFORM_WEAPON_BOW		2149		// yay
#define FFA_UNIFORM_WEAPON_TWOHAND	3159		// cift el
#define FFA_UNIFORM_WEAPON_BELL		5109		// can
#define FFA_UNIFORM_WEAPON_FAN		7159		// yelpaze

struct TFFAEntry
{
	std::string				stName;
	int						iKills;
	int						iDeaths;
	int						iRace;		// karakter irki 0-7 (client skorboard sira ikonlari)

	TFFAEntry() : iKills(0), iDeaths(0), iRace(-1) {}
};

class CFFAManager : public singleton<CFFAManager>
{
	public:
		CFFAManager();
		~CFFAManager();

		void	Initialize();
		void	Destroy();

		bool	IsFFAMap(long lMapIndex) const { return lMapIndex == FFA_EVENT_MAP_INDEX; }
		bool	HasMap() const;		// bu core FFA haritasini host ediyor mu
		bool	IsOpen() const;		// ffa_open event flag

		// battle_is_attackable kapisi: 1 = serbest vurus, -1 = engelli, 0 = normal kurallara dus
		int		CheckAttack(LPCHARACTER ch, LPCHARACTER victim) const;

		// EncodeInsertPacket kimlik maskesi: hedef haritadaki normal oyuncu ise ve
		// izleyici kendisi/GM degilse true (isim/lonca/unvan/seviye maskelenir)
		bool	ShouldMask(const CHARACTER * pkTarget, LPENTITY pkViewer) const;

		// gorsel uniforma: maskeli paketlerde gonderilecek sabit gorunum vnum'lari
		DWORD	GetUniformArmorPart(LPCHARACTER ch) const;		// sinifa gore zirh
		DWORD	GetUniformWeaponPart(LPCHARACTER ch) const;		// silah alt-turune gore (animasyon korunur)

		// haritadaki oyuncuyla sosyal etkilesim engeli (ticaret/parti/arkadas/lonca daveti);
		// engellendiyse a'ya bilgi mesaji yazip true doner
		bool	BlocksInteraction(LPCHARACTER a, LPCHARACTER b);

		void	OnEventFlagChange(int iPrev, int iNow);	// questmanager SetEventFlag("ffa_open") hook'u
		bool	OnPlayerEnterMap(LPCHARACTER ch);		// Entergame; false = haritada kalamaz (sehre)
		void	OnKill(LPCHARACTER pkKiller, LPCHARACTER pkVictim);
		bool	OnDeadRespawn(LPCHARACTER ch);			// dead_event; true = akis islendi
		bool	OnRestart(LPCHARACTER ch, bool bTown);	// do_restart; true = akis islendi
		int		Tick();

		void	ShowStatus(LPCHARACTER ch);				// /ffa GM komutu

	private:
		void	ResetScores();
		void	FinishEvent();
		void	CollectMapPlayers(std::vector<LPCHARACTER> & vecOut) const;
		void	BroadcastCommandToMap(const char * c_pszCommand);
		void	BroadcastScoreboard(bool bForce);
		void	SendScoreboard(LPCHARACTER ch);
		void	BuildSortedRank(std::vector<std::pair<DWORD, const TFFAEntry *> > & vecOut) const;
		void	WarpToSpawn(LPCHARACTER ch);
		void	StartTick();
		void	StopTick();

		std::map<DWORD, TFFAEntry>	m_mapScore;
		time_t						m_tEndTime;
		time_t						m_tFightStart;		// isinma bitis ani (0 = savas modu degil)
		bool						m_bFightAnnounced;	// "savas basladi" tek kez duyurulsun
		time_t						m_tLastBroadcast;
		LPEVENT						m_pkTickEvent;
};

#endif // ENABLE_FFA_EVENT

#endif // __INC_FFA_EVENT_H__
