#ifndef __INC_BOSS_RANKING_H__
#define __INC_BOSS_RANKING_H__

#ifdef ENABLE_BOSS_DAMAGE_RANKING

// ============================================================================
// Boss Hasar Siralamasi
// ----------------------------------------------------------------------------
// - BOSS_RANKING_VNUMS listesindeki bosslar dogdugunda (SetProto) hasar oturumu
//   acilir; boss olunce (Dead) final top-3 duyurusu + kapatma komutu gider,
//   olmeden yok edilirse (Destroy: purge/dungeon temizligi vb.) oturum sessiz
//   silinir (pencere client tarafinda bayat-gizlenir).
// - Hasar kaydi PID bazlidir (relog VID degistirir, m_map_kDamage'deki gibi
//   hasar kaybolmasin) ve isim onbellegiyle tutulur: cikan oyuncu listede kalir.
// - Yayin: CHAT_TYPE_COMMAND (client binary degisikligi YOK, root repack yeter):
//     boss_rank <vnum>,<vid>#<sira>|<isim>|<hasar>|<yuzde>|<irk>|<imp>|<seviye>;...#<benSira>|<benHasar>|<benYuzde>
//     boss_rank_end <vid>
//   (irk 0-8 = client ikon indeksi, polymorph aninda guncellenmez; imp 1-3 = isim
//   bayrak rengi; yeni alanlar satir SONUNA eklenir - eski parser len>=4 toleransli;
//   isim wire'da 11 karaktere kesilir - 10 satir CHAT_MAX_LEN'e boyle sigar)
//   Alicilar: boss'un cevresindeki (gorus mesafesi) desc'li oyuncular. Eski root
//   komutu sessizce yok sayar (stringCommander KeyError -> 0), skew-safe.
// - Yuzde tabani: toplam verilen hasar (paylar %100'e toplanir; Eski_A USE_TOTAL_DMG
//   davranisi, ancak int64/double ile - DWORD tasma buglari tasinmadi).
// - Tick eventi ilk oturumla bir kez kurulur ve process omru boyunca calisir
//   (bos dongude maliyeti tek map.empty() kontrolu; dangling event riski yok).
// - Bu header include sirasina guvenir (ffa_event.h gibi): .cpp icinde stdafx.h
//   ve char.h'den SONRA include edilmelidir.
// ============================================================================

struct TBossRankEntry
{
	std::string		stName;		// isim onbellegi (oyuncu cikarsa da listede kalir)
	uint64_t		ullDamage;
	int				iRace;		// PC irki 0-8 (client ikonu; -1 = bilinmiyor/hep polymorph)
	BYTE			bEmpire;	// 1-3 (client isim rengi = bayrak rengi)
	BYTE			bLevel;

	TBossRankEntry() : ullDamage(0), iRace(-1), bEmpire(0), bLevel(0) {}
};

struct TBossRankSession
{
	DWORD								dwBossVnum;
	std::map<DWORD, TBossRankEntry>		mapDamage;	// PID -> hasar

	TBossRankSession() : dwBossVnum(0) {}
};

// Olum-ani siralamasinin anlik goruntusu: OnDead oturumu silmeden ONCE yazar,
// ayni Dead() cagri yiginindaki Reward() GetRankDropOwner ile okur (kural itemleri
// sira sahibine), OnDestroy supurur. BOSS_RANKING_DROP_RULES tuketicisi.
struct TBossFinalRank
{
	DWORD						dwBossVnum;
	std::vector<DWORD>			vecTopPIDs;		// sirali: [0] = 1. sira
	std::vector<std::string>	vecTopNames;	// log icin (PID ile ayni indeks)

	TBossFinalRank() : dwBossVnum(0) {}
};

class CBossRankingManager
{
	public:
		static CBossRankingManager & instance();

		static bool	IsRankedBossVnum(DWORD dwVnum);

		void	OnSpawn(LPCHARACTER pkBoss);	// SetProto: vnum listedeyse oturum acar
		void	OnDamage(LPCHARACTER pkBoss, LPCHARACTER pkAttacker, int iDam);
		void	OnDead(LPCHARACTER pkBoss);		// final top-3 duyurusu + kapatma komutu + oturum silme
		void	OnDestroy(LPCHARACTER pkBoss);	// olmeden despawn: sessiz temizlik
		int		Tick();							// periyodik yayin (BOSS_RANKING_TICK_SECONDS)

		// Reward() drop kancasi: item BOSS_RANKING_DROP_RULES'a uyuyorsa olum-ani
		// siralamasindaki sira sahibini dondurur (cevrimdisi/kural-disi -> nullptr =
		// stok akis; item her durumda duser, kaybolmaz)
		LPCHARACTER	GetRankDropOwner(LPCHARACTER pkBoss, DWORD dwItemVnum);

	private:
		CBossRankingManager();

		void	StartTickEvent();
		void	BroadcastSession(DWORD dwBossVID, const TBossRankSession & session, LPCHARACTER pkBoss);
		void	CollectViewers(LPCHARACTER pkBoss, std::vector<LPCHARACTER> & vecOut) const;
		void	BuildSortedRank(const TBossRankSession & session,
					std::vector<std::pair<DWORD, const TBossRankEntry *> > & vecOut, uint64_t & ullTotal) const;

		std::map<DWORD, TBossRankSession>	m_mapSessions;	// boss VID -> oturum
		std::map<DWORD, TBossFinalRank>		m_mapFinalRanks;	// boss VID -> olum-ani sirasi (drop kurallari; Destroy supurur)
		LPEVENT								m_pkTickEvent;
};

#endif // ENABLE_BOSS_DAMAGE_RANKING

#endif // __INC_BOSS_RANKING_H__
