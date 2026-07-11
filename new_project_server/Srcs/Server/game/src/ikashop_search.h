#ifndef __INC_METIN_II_GAME_IKASHOP_SEARCH_H__
#define __INC_METIN_II_GAME_IKASHOP_SEARCH_H__

#ifdef ENABLE_IKASHOP_SEARCH

// ============================================================================
// IKASHOP tarzi global Pazar Arama + uzaktan satin alma + dukkan goruntuleme.
//
// Mimari: tum dogrulama alicinin bagli oldugu game core'dadir. Kalici veri
// mevcut player_shop / player_shop_items(sold) / player_gift tablolarindadir;
// db core'a SIFIR dokunus vardir. Kanallar-arasi tek serilestirme noktasi
// MySQL satir kilididir:
//     UPDATE player_shop_items SET sold = 1 WHERE id = ? AND sold = 0 AND price = ?
// Para YALNIZCA claim kazanildiktan sonra dusulur. GG 42 paketi yalnizca
// gorsel senkron tasir; kaybolsa bile dupe imkansizdir (tezgah alicisi da
// BuyOffline'daki claim-first ile ayni satirda serilesir).
//
// Arama sorgusu ASYNC ReturnQuery(QID_IKASEARCH) ile calisir; arama yolunda
// DirectQuery YASAKTIR (pulse stall). BUY/VIEW yollarindaki tekil PK
// sorgulari senkron kalabilir (tek satir, indeksli).
// ============================================================================

typedef struct _SQLMsg SQLMsg;	// AsyncSQL.h forward-decl (db.h include zorunlulugu olmasin)

enum EIkaSearchConst
{
	IKASEARCH_MAX_RESULTS			= 250,		// client'a donecek en fazla sonuc karti
	IKASEARCH_SQL_LIMIT				= 1000,		// SQL LIMIT (post-filter oncesi tavan)
	IKASEARCH_VNUM_IN_MAX			= 350,		// vnum IN (...) aday tavani (ReturnQuery 4096B tamponuna sigmali); ustunde IN kullanilmaz, post-filter calisir
	IKASEARCH_SEARCH_COOLDOWN_MS	= 5000,
	IKASEARCH_BUY_COOLDOWN_MS		= 2000,
	IKASEARCH_VIEW_COOLDOWN_MS		= 2000,
	IKASEARCH_INFLIGHT_TIMEOUT_SEC	= 30,		// callback kaybolursa in-flight kilidinin omru
};

// Async arama sorgusuyla tasinan filtre kopyasi (ReturnQuery pvData; POD)
typedef struct SIkaSearchFilterCopy
{
	DWORD	dwPID;
	char	szName[IKASEARCH_FILTER_NAME_LEN];		// kucuk harfe cevrilmis
	BYTE	bType;									// 0xFF = filtre yok
	BYTE	bSubType;								// 0xFF = filtre yok
	DWORD	dwPriceMin;
	DWORD	dwPriceMax;								// 0 = filtre yok
	int		iLevelMin;
	int		iLevelMax;								// 0 = filtre yok
	TPlayerItemAttribute	aAttrs[IKASEARCH_FILTER_ATTR_NUM];	// bType=0 bos
} TIkaSearchFilterCopy;

class CIkaShopSearchManager
{
	public:
		static CIkaShopSearchManager & Instance();

		// input_main.cpp CG 84 dispatch girisi
		void	ReceivePacket(LPCHARACTER ch, const TPacketCGIkaShopSearch * p);

		// db.cpp AnalyzeReturnQuery -> QID_IKASEARCH callback'i
		void	OnSearchQueryResult(SQLMsg * pMsg, DWORD dwPID, void * pvData);

		// GG 42 isleyicisi (input_p2p.cpp) + yerel satis sonrasi dogrudan cagri:
		// canli tezgah bu core'daysa kirmizi ghost + oto-kapanis; sahip online ise bildirim
		void	OnShopItemSold(DWORD dwOwnerPID, DWORD dwItemDBID);

	private:
		CIkaShopSearchManager();

		void	HandleFilterRequest(LPCHARACTER ch, const TPacketCGIkaShopSearch * p);
		void	HandleBuyRequest(LPCHARACTER ch, const TPacketCGIkaShopSearch * p);
		void	HandleViewShopRequest(LPCHARACTER ch, const TPacketCGIkaShopSearch * p);

		// Proto onbellegi: kucuk-harf locale isim + tip + seviye limiti (ilk aramada kurulur)
		struct SProtoCacheEntry
		{
			DWORD		dwVnum;
			BYTE		bType;
			BYTE		bSubType;
			int			iLevelLimit;
			std::string	stLowerName;
		};

		void	BuildProtoCache();
		bool	MatchProtoFilters(DWORD dwVnum, const TIkaSearchFilterCopy & filter) const;
		// Aday vnum kumesi; donus: false = isim/tip/seviye filtresi yok (IN gereksiz)
		bool	CollectCandidateVnums(const TIkaSearchFilterCopy & filter, std::vector<DWORD> & vecOut) const;

		void	SendPopup(LPCHARACTER ch, const char * c_szLocaleKey);
		void	SendResultDelete(LPCHARACTER ch, DWORD dwItemDBID);
		void	BroadcastSoldP2P(DWORD dwOwnerPID, DWORD dwItemDBID);

		std::vector<SProtoCacheEntry>		m_vecProtoCache;
		std::map<DWORD, SProtoCacheEntry*>	m_mapProtoByVnum;
		bool								m_bProtoCacheReady;

		std::map<DWORD, time_t>				m_mapInFlight;	// pid -> arama istek zamani
};

#endif // ENABLE_IKASHOP_SEARCH
#endif // __INC_METIN_II_GAME_IKASHOP_SEARCH_H__
