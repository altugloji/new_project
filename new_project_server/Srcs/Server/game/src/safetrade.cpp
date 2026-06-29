#include "stdafx.h"
#ifdef ENABLE_SAFE_TRADE_SYSTEM
#include "safetrade.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "desc.h"
#include "desc_client.h"
#include "desc_manager.h"
#include "buffer_manager.h"
#include "log.h"
#include "packet.h"
#include "config.h"
#include "questmanager.h"
#include "../../common/tables.h"
#include "../../common/length.h"
#include "utils.h"
#include "../../libgame/include/grid.h"

// ---- config (gerçek değerler config.cpp'de okunur; burada güvenli varsayılan) ----
int  g_iSafeTradeStartDistance = 1000;   // ≈ 10 metre
int  g_iSafeTradeMaxActive     = 5;

bool SafeTrade_IsBlockedVnum(DWORD /*dwVnum*/)
{
	// İstersen burada ek vnum kara listesi kontrolü yap (config'ten yüklenmiş bir set).
	return false;
}

// ==================================================================
//  Yerel yardımcılar
// ==================================================================
static void SafeTrade_SendText(LPCHARACTER ch, BYTE bCode)
{
	if (!ch || !ch->GetDesc())
		return;
	TPacketGCSafeTrade p;
	memset(&p, 0, sizeof(p));
	p.header    = HEADER_GC_SAFETRADE;
	p.size      = sizeof(p);
	p.subheader = SAFETRADE_SUBGC_TEXT;
	p.pos       = bCode;
	ch->GetDesc()->Packet(&p, sizeof(p));
}

// ==================================================================
//  CSafeTrade
// ==================================================================
CSafeTrade::CSafeTrade(LPCHARACTER pkOwner, DWORD dwTradeID, DWORD dwPartnerID, const char* c_pszPartnerName)
	: m_pkOwner(pkOwner), m_dwTradeID(dwTradeID), m_dwPartnerID(dwPartnerID), m_bStatus(SAFETRADE_CREATING)
{
	memset(m_apItems, 0, sizeof(m_apItems));
	strlcpy(m_szPartnerName, c_pszPartnerName ? c_pszPartnerName : "", sizeof(m_szPartnerName));
	m_pkGrid = M2_NEW CGrid(SAFE_TRADE_GRID_WIDTH, SAFE_TRADE_GRID_HEIGHT);
}

CSafeTrade::~CSafeTrade()
{
	// Yalnız CREATING (henüz kilitlenmemiş) iken iade et. LOCKED'da item'ler emanette kalır.
	if (m_bStatus == SAFETRADE_CREATING)
		__RefundAllToOwner();

	if (m_pkGrid)
	{
		M2_DELETE(m_pkGrid);
		m_pkGrid = nullptr;
	}
}

LPITEM CSafeTrade::GetItem(BYTE bDepotPos) const
{
	if (bDepotPos >= SAFE_TRADE_MAX_ITEMS)
		return nullptr;
	return m_apItems[bDepotPos];
}

int CSafeTrade::GetItemCount() const
{
	int n = 0;
	for (int i = 0; i < SAFE_TRADE_MAX_ITEMS; ++i)
		if (m_apItems[i]) ++n;
	return n;
}

bool CSafeTrade::AddItem(TItemPos inv_pos, BYTE bDepotPos)
{
	if (m_bStatus != SAFETRADE_CREATING) return false;
	if (bDepotPos >= SAFE_TRADE_MAX_ITEMS) return false;
	if (m_apItems[bDepotPos]) return false;

	LPITEM item = m_pkOwner->GetItem(inv_pos);
	if (!item) return false;

	// ---- SERVER doğrulama (client'a güvenilmez) ----
	if (item->IsExchanging() || item->IsSafeTrading()) return false;
	if (IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE)) return false;       // takas yasağı
	if (IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE)) return false;        // ruha bağlı -> KATI blok
	if (item->isLocked()) return false;
	if (item->IsItemShopEmBound()) return false;
	if (SafeTrade_IsBlockedVnum(item->GetVnum())) return false;
	if (!m_pkGrid->IsEmpty(bDepotPos, 1, item->GetSize())) return false;

	// ---- ATOMİK DEVİR (safebox checkin kalıbı) ----
	item->RemoveFromCharacter();
	item->SetSafeTrading(true);
	item->SetSafeTradeID(m_dwTradeID);          // DB owner = trade_id olacak
	item->SetWindow(SAFETRADE);
	item->SetCell(m_pkOwner, bDepotPos);        // RAM owner = A (yaşam döngüsü)
	item->Save();
	ITEM_MANAGER::instance().FlushDelayedSave(item);   // ANINDA diske (commit noktası)

	m_pkGrid->Put(bDepotPos, 1, item->GetSize());
	m_apItems[bDepotPos] = item;
	m_pkOwner->SyncQuickslot(QUICKSLOT_TYPE_ITEM, inv_pos.cell, 255);

	CSafeTradeManager::instance().Log(m_dwTradeID, "ADD_ITEM", m_pkOwner, m_dwPartnerID, item);
	__SendItemSet(bDepotPos, item);
	return true;
}

bool CSafeTrade::RemoveItem(BYTE bDepotPos)
{
	if (m_bStatus != SAFETRADE_CREATING) return false;   // KİLİTLİYSE geri alma YOK
	if (bDepotPos >= SAFE_TRADE_MAX_ITEMS) return false;

	LPITEM item = m_apItems[bDepotPos];
	if (!item) return false;

	const int iEmpty = m_pkOwner->GetEmptyInventory(item->GetSize());
	if (iEmpty < 0) return false;

	m_pkGrid->Get(bDepotPos, 1, item->GetSize());
	m_apItems[bDepotPos] = nullptr;

	item->RemoveFromCharacter();
	item->SetSafeTrading(false);
	item->SetSafeTradeID(0);
	item->AddToCharacter(m_pkOwner, TItemPos(INVENTORY, iEmpty));  // window=INVENTORY, owner=A
	ITEM_MANAGER::instance().FlushDelayedSave(item);

	CSafeTradeManager::instance().Log(m_dwTradeID, "REMOVE_ITEM", m_pkOwner, m_dwPartnerID, item);
	__SendItemDel(bDepotPos);
	return true;
}

bool CSafeTrade::Lock()
{
	if (m_bStatus != SAFETRADE_CREATING) return false;
	if (GetItemCount() == 0) return false;

	TPacketGDSafeTradeSetState p;
	memset(&p, 0, sizeof(p));
	p.trade_id    = m_dwTradeID;
	p.actor_id    = m_pkOwner->GetPlayerID();
	p.from_status = SAFETRADE_CREATING;
	p.to_status   = SAFETRADE_LOCKED;
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_SETSTATE, m_pkOwner->GetDesc()->GetHandle(), &p, sizeof(p));
	return true;
}

// Son Onay artık trade_id-bazlı (oturum gerekmez): manager'da CSafeTradeManager::ConfirmRequest.

// DG_SETSTATE cevabı (CSafeTradeManager -> burada)
void CSafeTrade::OnStateChanged(BYTE bToStatus, bool bOk)
{
	if (!bOk)
	{
		// CAS başarısız: durum DB'de değişmiş. (Beklenmedik) sadece UI'ı geri bildir.
		__SendStatus(m_bStatus);
		return;
	}

	if (bToStatus == SAFETRADE_LOCKED)
	{
		m_bStatus = SAFETRADE_LOCKED;
		// KİLİT: item'leri emanete kalıcı bırak (RAM serbest, DB'de owner=trade_id kalır).
		// A artık item'leri geri alamaz; pencere kapansa bile havuzda kalır.
		for (int i = 0; i < SAFE_TRADE_MAX_ITEMS; ++i)
		{
			if (!m_apItems[i]) continue;
			__DetachItemToEscrow(m_apItems[i]);
			m_apItems[i] = nullptr;
		}
		CSafeTradeManager::instance().Log(m_dwTradeID, "LOCK", m_pkOwner, m_dwPartnerID, nullptr);
		__SendStatus(SAFETRADE_LOCKED);   // client "Son Onay" butonunu gösterir

		// Oturumu serbest bırak — pencere açık kalır; "Son Onay" artık trade_id ile çalışır.
		// (status LOCKED -> dtor REFUND ETMEZ)
		LPCHARACTER owner = m_pkOwner;
		owner->SetSafeTrade(nullptr);
		M2_DELETE(this);
	}
}

void CSafeTrade::__DetachItemToEscrow(LPITEM item)
{
	// DB satırı zaten doğru (window=SAFETRADE, owner=trade_id). RAM'i, satırı SİLMEDEN bırak.
	ITEM_MANAGER::instance().FlushDelayedSave(item);   // son hâli kesinleştir
	item->SetSkipSave(true);                           // DestroyItem ITEM_DESTROY ATMASIN
	item->SetCell(nullptr, 0);                         // owner=NULL (ama save etmeyeceğiz)
	ITEM_MANAGER::instance().RemoveFromDelayedSave(item);
	ITEM_MANAGER::instance().DestroyItem(item);        // RAM serbest, DB satırı KORUNUR
}

void CSafeTrade::__RefundAllToOwner()
{
	for (int i = 0; i < SAFE_TRADE_MAX_ITEMS; ++i)
	{
		LPITEM item = m_apItems[i];
		if (!item) continue;
		m_apItems[i] = nullptr;

		const int iEmpty = m_pkOwner->GetEmptyInventory(item->GetSize());
		if (iEmpty >= 0)
		{
			item->RemoveFromCharacter();
			item->SetSafeTrading(false);
			item->SetSafeTradeID(0);
			item->AddToCharacter(m_pkOwner, TItemPos(INVENTORY, iEmpty));
			ITEM_MANAGER::instance().FlushDelayedSave(item);
		}
		else
		{
			// Envanter dolu: item KAYBOLMAZ. owner=trade_id, window=SAFETRADE olarak
			// DB'de bırak; login reconciliation (trade CANCELLED ise) A'ya iade eder.
			__DetachItemToEscrow(item);
		}
		CSafeTradeManager::instance().Log(m_dwTradeID, "REFUND", m_pkOwner, 0, item);
	}

	// Trade başlığını da iptal et (CAS CREATING/LOCKED -> CANCELLED_BY_GM = "kapatıldı")
	TPacketGDSafeTradeSetState p;
	memset(&p, 0, sizeof(p));
	p.trade_id    = m_dwTradeID;
	p.actor_id    = m_pkOwner->GetPlayerID();
	p.from_status = m_bStatus;
	p.to_status   = SAFETRADE_CANCELLED_BY_GM;
	if (db_clientdesc)
		db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_SETSTATE,
			m_pkOwner->GetDesc() ? m_pkOwner->GetDesc()->GetHandle() : 0, &p, sizeof(p));
}

void CSafeTrade::__SendItemSet(BYTE bDepotPos, LPITEM item) const
{
	if (!m_pkOwner->GetDesc() || !item)
		return;
	TPacketGCSafeTrade p;
	memset(&p, 0, sizeof(p));
	p.header    = HEADER_GC_SAFETRADE;
	p.size      = sizeof(p);
	p.subheader = SAFETRADE_SUBGC_ITEM_SET;
	p.trade_id  = m_dwTradeID;
	p.pos       = bDepotPos;
	p.vnum      = item->GetVnum();
	p.count     = item->GetCount();
	thecore_memcpy(p.alSockets, item->GetSockets(),    sizeof(p.alSockets));
	thecore_memcpy(p.aAttr,     item->GetAttributes(), sizeof(p.aAttr));
	m_pkOwner->GetDesc()->Packet(&p, sizeof(p));
}

void CSafeTrade::__SendItemDel(BYTE bDepotPos) const
{
	if (!m_pkOwner->GetDesc())
		return;
	TPacketGCSafeTrade p;
	memset(&p, 0, sizeof(p));
	p.header    = HEADER_GC_SAFETRADE;
	p.size      = sizeof(p);
	p.subheader = SAFETRADE_SUBGC_ITEM_DEL;
	p.trade_id  = m_dwTradeID;
	p.pos       = bDepotPos;
	m_pkOwner->GetDesc()->Packet(&p, sizeof(p));
}

void CSafeTrade::__SendStatus(BYTE bStatus) const
{
	if (!m_pkOwner->GetDesc())
		return;
	TPacketGCSafeTrade p;
	memset(&p, 0, sizeof(p));
	p.header    = HEADER_GC_SAFETRADE;
	p.size      = sizeof(p);
	p.subheader = SAFETRADE_SUBGC_STATUS;
	p.trade_id  = m_dwTradeID;
	p.pos       = bStatus;
	m_pkOwner->GetDesc()->Packet(&p, sizeof(p));
}

// ==================================================================
//  CSafeTradeManager
// ==================================================================
CSafeTradeManager::CSafeTradeManager()  {}
CSafeTradeManager::~CSafeTradeManager() {}

int CSafeTradeManager::StartRequest(LPCHARACTER ch, const char* c_pszPartnerName)
{
	if (!ch || !ch->GetDesc())
		return SAFETRADE_START_BUSY;
	if (ch->GetSafeTrade())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SafeTrade_AlreadyOpen"));
		return SAFETRADE_START_BUSY;
	}
	if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->GetMall() || ch->IsCubeOpen())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SafeTrade_Busy"));
		return SAFETRADE_START_BUSY;
	}
	if (!c_pszPartnerName || !c_pszPartnerName[0])
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SafeTrade_EmptyName"));
		return SAFETRADE_START_EMPTY_NAME;
	}

	LPCHARACTER partner = CHARACTER_MANAGER::instance().FindPC(c_pszPartnerName);
	if (!partner)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SafeTrade_NotFound"));
		return SAFETRADE_START_NOT_FOUND;
	}
	if (partner == ch)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SafeTrade_Self"));
		return SAFETRADE_START_SELF;
	}
	if (partner->GetMapIndex() != ch->GetMapIndex() ||
		DISTANCE_APPROX(ch->GetX() - partner->GetX(), ch->GetY() - partner->GetY()) >= g_iSafeTradeStartDistance)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SafeTrade_NotNear"));
		return SAFETRADE_START_NOT_NEAR;
	}

	TPacketGDSafeTradeCreate p;
	memset(&p, 0, sizeof(p));
	p.initiator_id = ch->GetPlayerID();
	strlcpy(p.initiator_name, ch->GetName(), sizeof(p.initiator_name));
	p.partner_id = partner->GetPlayerID();
	strlcpy(p.partner_name, partner->GetName(), sizeof(p.partner_name));
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_CREATE, ch->GetDesc()->GetHandle(), &p, sizeof(p));
	return SAFETRADE_START_OK;
}

void CSafeTradeManager::OnCreated(LPCHARACTER ch, DWORD dwTradeID, DWORD dwPartnerID, const char* c_pszPartnerName)
{
	if (!ch || !ch->GetDesc())
		return;                              // A çıktıysa: boş CREATING satırı zararsız, reconcile siler
	if (dwTradeID == 0)
	{
		SafeTrade_SendText(ch, SAFETRADE_TEXT_TOO_MANY);   // locale: SAFETRADE_TOO_MANY
		return;
	}
	if (ch->GetSafeTrade())
		return;                              // yarış koruması

	CSafeTrade* pkTrade = M2_NEW CSafeTrade(ch, dwTradeID, dwPartnerID, c_pszPartnerName);
	ch->SetSafeTrade(pkTrade);
	Log(dwTradeID, "CREATE", ch, dwPartnerID, nullptr);

	// Depo penceresini aç
	TPacketGCSafeTrade p;
	memset(&p, 0, sizeof(p));
	p.header    = HEADER_GC_SAFETRADE;
	p.size      = sizeof(p);
	p.subheader = SAFETRADE_SUBGC_OPEN;
	p.trade_id  = dwTradeID;
	ch->GetDesc()->Packet(&p, sizeof(p));
}

void CSafeTradeManager::RequestIncomingList(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
		return;
	TPacketGDSafeTradeList p;
	p.player_id = ch->GetPlayerID();
	p.outgoing  = 0;
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_LIST, ch->GetDesc()->GetHandle(), &p, sizeof(p));
}

void CSafeTradeManager::RequestOutgoingList(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
		return;
	TPacketGDSafeTradeList p;
	p.player_id = ch->GetPlayerID();
	p.outgoing  = 1;
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_LIST, ch->GetDesc()->GetHandle(), &p, sizeof(p));
}

// A: "Son Onay" (LOCKED -> READY_TO_CLAIM). trade_id-bazlı, oturum gerekmez.
void CSafeTradeManager::ConfirmRequest(LPCHARACTER ch, DWORD dwTradeID)
{
	if (!ch || !ch->GetDesc())
		return;
	TPacketGDSafeTradeSetState p;
	memset(&p, 0, sizeof(p));
	p.trade_id    = dwTradeID;
	p.actor_id    = ch->GetPlayerID();
	p.from_status = SAFETRADE_LOCKED;
	p.to_status   = SAFETRADE_READY_TO_CLAIM;
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_SETSTATE, ch->GetDesc()->GetHandle(), &p, sizeof(p));
}

// DG_SETSTATE(READY_TO_CLAIM) cevabı -> burada
void CSafeTradeManager::OnConfirmResult(LPCHARACTER ch, DWORD dwTradeID, bool bOk)
{
	if (!ch || !ch->GetDesc())
		return;
	if (!bOk)
		return;   // CAS başarısız (zaten onaylanmış/iptal): sessiz geç

	Log(dwTradeID, "CONFIRM", ch, 0, nullptr);
	SafeTrade_SendText(ch, SAFETRADE_TEXT_CONFIRMED);

	// depo penceresini kapat
	TPacketGCSafeTrade c;
	memset(&c, 0, sizeof(c));
	c.header = HEADER_GC_SAFETRADE;
	c.size = sizeof(c);
	c.subheader = SAFETRADE_SUBGC_CLOSE;
	ch->GetDesc()->Packet(&c, sizeof(c));
}

void CSafeTradeManager::RequestView(LPCHARACTER ch, DWORD dwTradeID)
{
	if (!ch || !ch->GetDesc())
		return;
	// Baska bir pencere/islem aciksa goruntuleme baslatma (karsilikli kilit)
	if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->GetMall() || ch->IsCubeOpen())
		return;
	ch->SetSafeTradeClaimingID(0);            // sadece görüntüleme niyeti
	TPacketGDSafeTradeLoadItem p;
	p.trade_id     = dwTradeID;
	p.requester_id = ch->GetPlayerID();
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_LOADITEM, ch->GetDesc()->GetHandle(), &p, sizeof(p));
}

bool CSafeTradeManager::ClaimRequest(LPCHARACTER ch, DWORD dwTradeID)
{
	if (!ch || !ch->GetDesc())
		return false;
	if (ch->IsSafeTradeClaiming())
		return false;
	// Baska bir pencere/islem aciksa claim baslatma (karsilikli kilit)
	if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->GetMall() || ch->IsCubeOpen())
		return false;

	ch->SetSafeTradeClaimingID(dwTradeID);    // niyet: claim
	ch->SetSafeTradeClaiming(true);           // claim süresince B envanteri kilitli

	TPacketGDSafeTradeLoadItem p;
	p.trade_id     = dwTradeID;
	p.requester_id = ch->GetPlayerID();
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_LOADITEM, ch->GetDesc()->GetHandle(), &p, sizeof(p));
	return true;
}

// DG_LIST cevabı -> client'a GC INCOMING olarak ilet (değişken uzunluk)
void CSafeTradeManager::OnList(LPCHARACTER ch, BYTE bOutgoing, BYTE bCount, const char* c_pData)
{
	if (!ch || !ch->GetDesc())
		return;

	if (bCount == 0)
	{
		SafeTrade_SendText(ch, SAFETRADE_TEXT_EMPTY_LIST);
		return;
	}

	TPacketGCSafeTrade p;
	memset(&p, 0, sizeof(p));
	p.header    = HEADER_GC_SAFETRADE;
	p.size      = sizeof(p) + bCount * sizeof(TSafeTradeListEntry);
	p.subheader = SAFETRADE_SUBGC_INCOMING;
	p.pos       = bOutgoing;
	p.count     = bCount;

	TEMP_BUFFER buf;
	buf.write(&p, sizeof(p));
	buf.write(c_pData, bCount * sizeof(TSafeTradeListEntry));
	ch->GetDesc()->Packet(buf.read_peek(), buf.size());
}

void CSafeTradeManager::OnItemsLoaded(LPCHARACTER ch, DWORD dwTradeID, BYTE bCount, TPlayerItem* pItems)
{
	if (!ch || !ch->GetDesc())
		return;

	// Sadece görüntüleme (A re-open / B claim penceresi): item'leri depo hücrelerine yaz.
	if (ch->GetSafeTradeClaimingID() != dwTradeID)
	{
		// Önce tüm slotları temizle (önceki trade'den kalıntı olmasın)
		for (BYTE s = 0; s < SAFE_TRADE_MAX_ITEMS; ++s)
		{
			TPacketGCSafeTrade d;
			memset(&d, 0, sizeof(d));
			d.header = HEADER_GC_SAFETRADE; d.size = sizeof(d);
			d.subheader = SAFETRADE_SUBGC_ITEM_DEL;
			d.trade_id = dwTradeID; d.pos = s;
			ch->GetDesc()->Packet(&d, sizeof(d));
		}
		// Item'leri GERÇEK slot pozisyonlarına (item.pos) yaz
		for (BYTE i = 0; i < bCount; ++i)
		{
			BYTE slot = (BYTE) pItems[i].pos;
			if (slot >= SAFE_TRADE_MAX_ITEMS)
				slot = i;
			TPacketGCSafeTrade p;
			memset(&p, 0, sizeof(p));
			p.header = HEADER_GC_SAFETRADE; p.size = sizeof(p);
			p.subheader = SAFETRADE_SUBGC_ITEM_SET;
			p.trade_id  = dwTradeID;
			p.pos       = slot;
			p.vnum      = pItems[i].vnum;
			p.count     = pItems[i].count;
			thecore_memcpy(p.alSockets, pItems[i].alSockets, sizeof(p.alSockets));
			thecore_memcpy(p.aAttr,     pItems[i].aAttr,     sizeof(p.aAttr));
			ch->GetDesc()->Packet(&p, sizeof(p));
		}
		return;
	}

	// CLAIM niyeti: hepsi-veya-hiçbiri boş yer kontrolü
	if (bCount == 0)
	{
		ch->SetSafeTradeClaiming(false);
		ch->SetSafeTradeClaimingID(0);
		return;
	}
	if (!__CheckSpaceForAll(ch, bCount, pItems))
	{
		ch->SetSafeTradeClaiming(false);
		ch->SetSafeTradeClaimingID(0);
		SafeTrade_SendText(ch, SAFETRADE_TEXT_NO_SPACE);
		return;
	}

	// Faz 2: CAS claim + owner->B (DB). window=SAFETRADE kalır.
	TPacketGDSafeTradeClaim p;
	p.trade_id   = dwTradeID;
	p.claimer_id = ch->GetPlayerID();
	db_clientdesc->DBPacket(HEADER_GD_SAFETRADE_CLAIM, ch->GetDesc()->GetHandle(), &p, sizeof(p));
}

bool CSafeTradeManager::__CheckSpaceForAll(LPCHARACTER ch, BYTE bCount, TPlayerItem* pItems)
{
	// Gerçek grid kontrolü (CExchange::CheckSpace kalıbı): envanteri sayfa-grid'lerine kopyala,
	// gelen her item için bir sayfada boş yer ara + rezerve et. Sayfalar arası taşma yok.
	std::array<std::unique_ptr<CGrid>, INVENTORY_PAGE_COUNT> grids;
	for (int iPage = 0; iPage < INVENTORY_PAGE_COUNT; ++iPage)
	{
		grids[iPage] = std::make_unique<CGrid>(INVENTORY_PAGE_COLUMN, INVENTORY_PAGE_ROW);
		grids[iPage]->Clear();

		const int pageStart = iPage * INVENTORY_PAGE_SIZE;
		for (int i = 0; i < INVENTORY_PAGE_SIZE; ++i)
		{
			LPITEM it = ch->GetInventoryItem(pageStart + i);
			if (it)
				grids[iPage]->Put(i, 1, it->GetSize());
		}
	}

	for (BYTE n = 0; n < bCount; ++n)
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(pItems[n].vnum);
		const BYTE bSize = proto ? proto->bSize : 1;

		int iPos = -1;
		for (int iPage = 0; iPage < INVENTORY_PAGE_COUNT; ++iPage)
		{
			if ((iPos = grids[iPage]->FindBlank(1, bSize)) >= 0)
			{
				grids[iPage]->Put(iPos, 1, bSize);
				break;
			}
		}
		if (iPos < 0)
			return false;   // bu item hiçbir sayfaya sığmadı -> envanter dolu
	}
	return true;
}

// DG_CLAIM cevabı.  bResult: 0=OK, 1=ALREADY, 2=ERROR
void CSafeTradeManager::OnClaimResult(LPCHARACTER ch, DWORD dwTradeID, BYTE bResult, BYTE bCount, TPlayerItem* pItems)
{
	if (!ch)
		return;
	ch->SetSafeTradeClaiming(false);
	ch->SetSafeTradeClaimingID(0);

	if (bResult == 1)
	{
		SafeTrade_SendText(ch, SAFETRADE_TEXT_ALREADY);
		RequestIncomingList(ch);
		return;
	}
	if (bResult != 0)
		return;

	// OK: item'ler artık owner=B, window=SAFETRADE. Envantere al (window->INVENTORY).
	for (BYTE i = 0; i < bCount; ++i)
	{
		TPlayerItem* p = &pItems[i];

		// H1: id RAM'de zaten varsa CreateItem nullptr döner -> KAYIP. Bunun yerine atla.
		// DB satırı owner=B,window=SAFETRADE DURUYOR -> reconciliation relog'da teslim eder.
		if (ITEM_MANAGER::instance().Find(p->id))
		{
			sys_err("SAFETRADE_CLAIM_COLLISION item %u trade %u (reconcile edilecek)", p->id, dwTradeID);
			Log(dwTradeID, "CLAIM_COLLISION", ch, 0, nullptr);
			continue;
		}

		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(p->vnum);
		const BYTE bSize = proto ? proto->bSize : 1;
		const int pos = ch->GetEmptyInventory(bSize);
		if (pos < 0)
			continue;   // beklenmez (önceden doğrulandı); item kaybolmaz, reconcile teslim eder

		LPITEM item = ITEM_MANAGER::instance().CreateItem(p->vnum, p->count, p->id);   // MEVCUT id
		if (!item)
		{
			sys_err("SAFETRADE_CLAIM CreateItem FAIL id %u vnum %u", p->id, p->vnum);
			continue;
		}
		item->SetSkipSave(false);
		item->SetSockets(p->alSockets);
		item->SetAttributes(p->aAttr);
		item->SetSafeTrading(false);
		item->SetSafeTradeID(0);
		item->AddToCharacter(ch, TItemPos(INVENTORY, pos));   // window=INVENTORY, owner=B, Save
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		const DWORD dwFlushID = item->GetID();
		db_clientdesc->DBPacketHeader(HEADER_GD_ITEM_FLUSH, 0, sizeof(DWORD));
		db_clientdesc->Packet(&dwFlushID, sizeof(DWORD));

		Log(dwTradeID, "CLAIM", ch, 0, item);
		LogManager::instance().ItemLog(ch, item, "SAFETRADE_TAKE", item->GetName());
	}

	SafeTrade_SendText(ch, SAFETRADE_TEXT_CLAIMED_OK);

	// Teslimat tamam -> depo penceresini kapat (client grid'i de temizler).
	// Liste penceresini de kapatmak client'a CLAIMED_OK (text=2) ile bildiriliyor;
	// burada RequestIncomingList'i KASITLI cagirmiyoruz ki "bana gelen ticaretler"
	// penceresi claim sonrasi tekrar acilmasin (kullanici NPC'den yeniden acar).
	if (ch->GetDesc())
	{
		TPacketGCSafeTrade c;
		memset(&c, 0, sizeof(c));
		c.header = HEADER_GC_SAFETRADE;
		c.size = sizeof(c);
		c.subheader = SAFETRADE_SUBGC_CLOSE;
		ch->GetDesc()->Packet(&c, sizeof(c));
	}
}

void CSafeTradeManager::Log(DWORD dwTradeID, const char* c_pszAction, LPCHARACTER actor, DWORD dwTargetID, LPITEM item)
{
	LogManager::instance().SafeTradeLog(
		dwTradeID,
		c_pszAction,
		actor ? actor->GetPlayerID() : 0,
		actor ? actor->GetName() : "",
		dwTargetID,
		item ? item->GetID() : 0,
		item ? item->GetVnum() : 0,
		item ? item->GetCount() : 0,
		(actor && actor->GetDesc()) ? actor->GetDesc()->GetHostName() : "");
}

#endif // ENABLE_SAFE_TRADE_SYSTEM
