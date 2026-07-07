// gift.h - Hediye Gonderme Sistemi (ENABLE_GIFT_SEND_SYSTEM)
// Oyuncudan oyuncuya kozmetik hediye gonderimi. Aliciya item VERILMEZ;
// hediyenin EP fiyati kadar deger, alicinin "hediye puani" olarak birikir.
#ifndef __INC_METIN2_GIFT_H
#define __INC_METIN2_GIFT_H

#include "../../common/CommonDefines.h"

#ifdef ENABLE_GIFT_SEND_SYSTEM

#include "../../common/stl.h"
#include "../../common/singleton.h"
#include "typedef.h"
#include "packet.h"		// TGiftRankEntry + GIFT_* sabitleri

// Bir hediye tanimi (player.gift_item satiri, bellekte cache).
typedef struct SGiftItemDef
{
	DWORD		dwId;			// gift_item.id (client'a "index" olarak gider)
	DWORD		dwIconVnum;		// gift_item.icon_image = ikon item vnum'u
	DWORD		dwPriceEP;		// gift_item.price_ep (birim fiyat)
	BYTE		bPage;			// gift_item.page
	BYTE		bSlot;			// gift_item.slot_index
	std::string	stName;			// gift_item.locale_name
	std::string	stDesc;			// gift_item.locale_desc
} TGiftItemDef;

// Gonderim sonuc kodlari (GC_GIFT_SEND_RESULT.bResult).
enum EGiftSendResult
{
	GIFT_SEND_OK				= 0,	// basarili
	GIFT_SEND_NOT_ENOUGH_EP		= 1,	// yetersiz EP
	GIFT_SEND_TARGET_NOT_FOUND	= 2,	// oyuncu bulunamadi
	GIFT_SEND_SELF				= 3,	// kendine / kendi hesabina
	GIFT_SEND_COOLDOWN			= 4,	// cok sik gonderim (flood)
	GIFT_SEND_INVALID_GIFT		= 5,	// gecersiz hediye index
	GIFT_SEND_INVALID_COUNT		= 6,	// gecersiz adet
	GIFT_SEND_BLOCKED			= 7,	// ticaret/hapis/olu vb. engel
	GIFT_SEND_DB_ERROR			= 8,	// DB hatasi
};

// Isim dogrulama sonuc kodlari (GC_GIFT_FIND_RESULT.bResult).
enum EGiftFindResult
{
	GIFT_FIND_NOT_FOUND			= 0,	// karakter yok
	GIFT_FIND_OK				= 1,	// gecerli hedef
	GIFT_FIND_SELF				= 2,	// kendisi / kendi hesabi
};

class CGiftManager : public singleton<CGiftManager>
{
	public:
		CGiftManager();
		virtual ~CGiftManager();

		// gift_item cache
		bool				LoadGiftItems();				// player.gift_item -> cache
		void				Reload();						// cache'i yeniden yukle
		const TGiftItemDef*	FindGift(DWORD dwId) const;		// id ile tanim bul

		// Client istekleri (input_main.cpp'den cagrilir)
		void				SendGiftList(LPCHARACTER ch);						// katalog + EP + puan
		void				SendEP(LPCHARACTER ch);								// GC_GIFT_EP
		void				SendGiftPoint(LPCHARACTER ch);						// GC_GIFT_POINT
		void				FindTarget(LPCHARACTER ch, const char* c_szName);	// GC_GIFT_FIND_RESULT
		void				SendGift(LPCHARACTER ch, const char* c_szName, WORD wGiftIndex, BYTE bCount, BYTE bFlags, const char* c_szMessage);
		void				SendRank(LPCHARACTER ch, BYTE bBoardType);			// GC_GIFT_RANK (ilk 10 + kendi siram)

		// Login teslimati (input_login.cpp'den cagrilir)
		void				LoadGiftData(LPCHARACTER ch);						// puan yukle + okunmamis bildirimleri gonder

		// P2P (input_p2p.cpp'den cagrilir) - baska core'daki online aliciya canli teslimat
		void				OnP2PGiftNotify(const void* c_pvData);

	private:
		// Adi verilen karakterin pid + account_id'sini (offline dahil) bulur.
		bool				GetTargetByName(const char* c_szName, DWORD& r_dwPID, DWORD& r_dwAID) const;
		// EP hesabini atomik olarak duser; basarili ise yeni bakiyeyi r_dwNewEP'e yazar.
		bool				DeductEP(DWORD dwAccountID, DWORD dwTotal, DWORD& r_dwNewEP) const;
		// Hediye puanini atomik olarak ekler (player.gift_point).
		bool				AddGiftPoint(DWORD dwTargetPID, DWORD dwPoint) const;
		// Gonderen puanini biriktirir (player.gift_sent_point, siralama icin; best-effort).
		void				AddGiftSentPoint(DWORD dwSenderPID, DWORD dwPoint) const;
		// Ilk GIFT_RANK_MAX oyuncuyu getirir (30 sn cache'li).
		const std::vector<TGiftRankEntry>&	GetTopList(BYTE bBoardType);
		// Canli bildirim: aliciya GC_GIFT_NOTIFY paketi (ch bu core'da online olmali).
		void				DeliverNotify(LPCHARACTER ch, const char* c_szSenderName, const char* c_szGiftName, const char* c_szMessage, bool bAnonymous, DWORD dwPoint, DWORD dwTotalPoint) const;
		// gonderim engel kontrolu (ticaret/hapis/olu ...)
		bool				IsBlocked(LPCHARACTER ch) const;

	private:
		std::vector<TGiftItemDef>	m_vecGifts;
		bool						m_bLoaded;

		// siralama cache (0=gonderen, 1=alan); TTL: GIFT_RANK_CACHE_SEC
		std::vector<TGiftRankEntry>	m_avecRankCache[2];
		int							m_aiRankCacheTime[2];
};

#endif
#endif
