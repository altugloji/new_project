#ifndef __INC_METIN_II_GAME_SAFETRADE_H__
#define __INC_METIN_II_GAME_SAFETRADE_H__
#include "../../common/CommonDefines.h"
#ifdef ENABLE_SAFE_TRADE_SYSTEM
#include "../../common/stl.h"
#include "../../common/tables.h"
#include "../../common/length.h"

class CGrid;

// ------------------------------------------------------------------
//  Limitler / sabitler (config'e bağlanabilir; bkz. g_iSafeTrade*)
// ------------------------------------------------------------------
enum ESafeTradeConst
{
	SAFE_TRADE_GRID_WIDTH  = 6,
	SAFE_TRADE_GRID_HEIGHT = 4,
	SAFE_TRADE_MAX_ITEMS   = SAFE_TRADE_GRID_WIDTH * SAFE_TRADE_GRID_HEIGHT,  // 24
};

// safetrade.status ENUM ile BİREBİR sıra (CreateItemTableFromRes / +0 gibi sayısal eşleşme)
enum ESafeTradeStatus
{
	SAFETRADE_CREATING        = 0,
	SAFETRADE_LOCKED          = 1,
	SAFETRADE_READY_TO_CLAIM  = 2,
	SAFETRADE_CLAIMED         = 3,
	SAFETRADE_CANCELLED_BY_GM = 4,
};

// safetrade.start() sonuç kodları (quest mesaj eşlemesi için)
enum ESafeTradeStartResult
{
	SAFETRADE_START_OK = 0,
	SAFETRADE_START_EMPTY_NAME,
	SAFETRADE_START_NOT_FOUND,
	SAFETRADE_START_SELF,
	SAFETRADE_START_NOT_NEAR,
	SAFETRADE_START_BUSY,
};

// İstemciye gönderilen kısa mesaj kodları (SAFETRADE_SUBGC_TEXT)
enum ESafeTradeTextCode
{
	SAFETRADE_TEXT_NO_SPACE     = 1,   // "Envanterinde yeterli boş yer yok."
	SAFETRADE_TEXT_CLAIMED_OK   = 2,   // "Itemler başarıyla teslim alındı."
	SAFETRADE_TEXT_ALREADY      = 3,   // "Bu güvenli ticaret zaten alınmış."
	SAFETRADE_TEXT_CONFIRMED    = 4,   // "Ticaret onaylandi..."
	SAFETRADE_TEXT_EMPTY_LIST   = 5,   // "Sana gelen guvenli ticaret bulunmuyor."
	SAFETRADE_TEXT_TOO_MANY     = 6,   // "Cok fazla aktif guvenli ticaretin var."
};

// ==================================================================
//  CSafeTrade : A oyuncusunun açık depo oturumu (CREATING/LOCKED yaşar)
//  CExchange/CSafebox kalıbı. Confirm sonrası item'ler DB'ye detach olur.
// ==================================================================
class CSafeTrade
{
	public:
		CSafeTrade(LPCHARACTER pkOwner, DWORD dwTradeID, DWORD dwPartnerID, const char* c_pszPartnerName);
		~CSafeTrade();

		bool        AddItem(TItemPos inv_pos, BYTE bDepotPos);   // CREATING
		bool        RemoveItem(BYTE bDepotPos);                  // CREATING (tek item iade)
		bool        Lock();                                      // CREATING -> LOCKED (DB CAS) + emanete bırak

		// DB cevapları (CSafeTradeManager -> buraya):
		void        OnStateChanged(BYTE bToStatus, bool bOk);

		LPITEM      GetItem(BYTE bDepotPos) const;
		int         GetItemCount() const;

		DWORD       GetTradeID() const   { return m_dwTradeID; }
		DWORD       GetPartnerID() const { return m_dwPartnerID; }
		const char* GetPartnerName() const { return m_szPartnerName; }
		BYTE        GetStatus() const    { return m_bStatus; }
		LPCHARACTER GetOwner() const     { return m_pkOwner; }

	private:
		void        __RefundAllToOwner();        // CREATING/LOCKED iptalinde A'ya iade
		void        __DetachItemToEscrow(LPITEM item);   // Confirm: RAM bırak, satır korunur
		void        __SendItemSet(BYTE bDepotPos, LPITEM item) const;
		void        __SendItemDel(BYTE bDepotPos) const;
		void        __SendStatus(BYTE bStatus) const;

		LPCHARACTER m_pkOwner;
		DWORD       m_dwTradeID;
		DWORD       m_dwPartnerID;
		char        m_szPartnerName[CHARACTER_NAME_MAX_LEN + 1];
		BYTE        m_bStatus;
		LPITEM      m_apItems[SAFE_TRADE_MAX_ITEMS];
		CGrid*      m_pkGrid;
};

// ==================================================================
//  CSafeTradeManager : başlatma akışı, claim, gelen/giden liste,
//  DB cevap yönlendirme. Singleton.
// ==================================================================
class CSafeTradeManager : public singleton<CSafeTradeManager>
{
	public:
		CSafeTradeManager();
		virtual ~CSafeTradeManager();

		// ---- A tarafı ----
		int   StartRequest(LPCHARACTER ch, const char* c_pszPartnerName);  // -> ESafeTradeStartResult
		void  OnCreated(LPCHARACTER ch, DWORD dwTradeID, DWORD dwPartnerID, const char* c_pszPartnerName);
		void  RequestOutgoingList(LPCHARACTER ch);
		void  ConfirmRequest(LPCHARACTER ch, DWORD dwTradeID);   // "Son Onay" (LOCKED->READY)
		void  OnConfirmResult(LPCHARACTER ch, DWORD dwTradeID, bool bOk);

		// ---- B tarafı ----
		void  RequestIncomingList(LPCHARACTER ch);
		void  RequestView(LPCHARACTER ch, DWORD dwTradeID);
		bool  ClaimRequest(LPCHARACTER ch, DWORD dwTradeID);

		// ---- DB cevapları (input_db -> buraya) ----
		void  OnList(LPCHARACTER ch, BYTE bOutgoing, BYTE bCount, const char* c_pData);
		void  OnItemsLoaded(LPCHARACTER ch, DWORD dwTradeID, BYTE bCount, TPlayerItem* pItems);
		void  OnClaimResult(LPCHARACTER ch, DWORD dwTradeID, BYTE bResult, BYTE bCount, TPlayerItem* pItems);

		// ---- ortak ----
		void  Log(DWORD dwTradeID, const char* c_pszAction, LPCHARACTER actor, DWORD dwTargetID, LPITEM item);

	private:
		bool  __CheckSpaceForAll(LPCHARACTER ch, BYTE bCount, TPlayerItem* pItems);
};

// config (config.cpp / config.h):
extern int  g_iSafeTradeStartDistance;   // varsayılan 3000 (≈30m)
extern int  g_iSafeTradeMaxActive;       // oyuncu başına aktif trade limiti, varsayılan 5
bool        SafeTrade_IsBlockedVnum(DWORD dwVnum);   // ek vnum kara listesi (opsiyonel)

#endif // ENABLE_SAFE_TRADE_SYSTEM
#endif
