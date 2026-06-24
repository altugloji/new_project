#include "stdafx.h"
#include "../../libgame/include/grid.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "shop.h"
#include "desc.h"
#include "desc_manager.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "buffer_manager.h"
#include "packet.h"
#include "log.h"
#include "db.h"
#include "questmanager.h"
#include "monarch.h"
#include "mob_manager.h"
#include "locale_service.h"

//#define ENABLE_SHOP_BLACKLIST
/* ------------------------------------------------------------------------------------ */
CShop::CShop()
	: m_dwVnum(0), m_dwNPCVnum(0), m_pkPC(nullptr)
{
	m_pGrid = M2_NEW CGrid(5, 9);
}

CShop::~CShop()
{
	TPacketGCShop pack;

	pack.header		= HEADER_GC_SHOP;
	pack.subheader	= SHOP_SUBHEADER_GC_END;
	pack.size		= sizeof(TPacketGCShop);

	Broadcast(&pack, sizeof(pack));

	GuestMapType::iterator it;

	it = m_map_guest.begin();

	while (it != m_map_guest.end())
	{
		const LPCHARACTER ch = it->first;
		ch->SetShop(nullptr);
		++it;
	}

	M2_DELETE(m_pGrid);
}

void CShop::SetPCShop(LPCHARACTER ch)
{
	m_pkPC = ch;
}

bool CShop::Create(DWORD dwVnum, DWORD dwNPCVnum, TShopItemTable * pTable)
{
	sys_log(0, "SHOP #%d (Shopkeeper %d)", dwVnum, dwNPCVnum);

	m_dwVnum = dwVnum;
	m_dwNPCVnum = dwNPCVnum;

	BYTE bItemCount;

	for (bItemCount = 0; bItemCount < SHOP_HOST_ITEM_MAX_NUM; ++bItemCount)
		if (0 == (pTable + bItemCount)->vnum)
			break;

	SetShopItems(pTable, bItemCount);
	return true;
}

void CShop::SetShopItems(TShopItemTable * pTable, BYTE bItemCount)
{
	if (bItemCount > SHOP_HOST_ITEM_MAX_NUM)
		return;

	m_pGrid->Clear();

	m_itemVector.resize(SHOP_HOST_ITEM_MAX_NUM);
	msl::refill(m_itemVector);

	for (int i = 0; i < bItemCount; ++i)
	{
		LPITEM pkItem = nullptr;
		const TItemTable * item_table;

		if (m_pkPC)
		{
			pkItem = m_pkPC->GetItem(pTable->pos);

			if (!pkItem)
			{
				sys_err("cannot find item on pos (%d, %d) (name: %s)", pTable->pos.window_type, pTable->pos.cell, m_pkPC->GetName());
				continue;
			}

			item_table = pkItem->GetProto();
		}
		else
		{
			if (!pTable->vnum)
				continue;

			item_table = ITEM_MANAGER::instance().GetTable(pTable->vnum);
		}

		if (!item_table)
		{
			sys_err("Shop: no item table by item vnum #%d", pTable->vnum);
			continue;
		}

		int iPos;

		if (IsPCShop())
		{
			sys_log(0, "MyShop: use position %d", pTable->display_pos);
			iPos = pTable->display_pos;
		}
		else
			iPos = m_pGrid->FindBlank(1, item_table->bSize);

		if (iPos < 0)
		{
			sys_err("not enough shop window");
			continue;
		}

		if (!m_pGrid->IsEmpty(iPos, 1, item_table->bSize))
		{
			if (IsPCShop())
			{
				sys_err("not empty position for pc shop %s[%d]", m_pkPC->GetName(), m_pkPC->GetPlayerID());
			}
			else
			{
				sys_err("not empty position for npc shop");
			}
			continue;
		}

		m_pGrid->Put(iPos, 1, item_table->bSize);

		SHOP_ITEM & item = m_itemVector[iPos];

		item.pkItem = pkItem;
		item.itemid = 0;
#ifdef ENABLE_CHEQUE_SYSTEM
		item.cheque = 0;
#endif

		if (item.pkItem)
		{
			item.vnum = pkItem->GetVnum();
			item.count = pkItem->GetCount();
			item.price = pTable->price;
			item.itemid	= pkItem->GetID();
#ifdef ENABLE_CHEQUE_SYSTEM
			item.cheque = pTable->cheque;
#endif
#ifdef ENABLE_MULTISHOP
			item.wPriceVnum = pTable->wPriceVnum;
			item.wPrice = pTable->wPrice;
			item.gemPrice = pTable->gem_price;
#endif
		}
		else
		{
			item.vnum = pTable->vnum;
			item.count = pTable->count;
#ifdef ENABLE_MULTISHOP
			item.wPriceVnum = pTable->wPriceVnum;
			item.wPrice = pTable->wPrice;
			item.gemPrice = pTable->gem_price;
#endif


			if (IS_SET(item_table->dwFlags, ITEM_FLAG_COUNT_PER_1GOLD))
			{
				if (item_table->dwGold == 0)
					item.price = item.count;
				else
					item.price = item.count / item_table->dwGold;
			}
			else
				item.price = item_table->dwGold * item.count;
		}

		char name[36];
		snprintf(name, sizeof(name), "%-20s(#%-5d) (x %d)", item_table->szName, (int) item.vnum, item.count);

		sys_log(0, "SHOP_ITEM: %-36s PRICE %-5d", name, item.price);
		++pTable;
	}
}

#ifdef OFFLINE_SHOP
int CShop::BuyOffline(LPCHARACTER ch, BYTE pos)
{
	if (!ch || !ch->IsPC() || pos >= m_itemVector.size())
	{
		sys_err("Shop::BuyOffline: Gecersiz karakter! (NULL veya NPC)");
		return SHOP_SUBHEADER_GC_INVALID_POS;
	}

	sys_log(0, "Shop::BuyOffline : name %s pos %d", ch->GetName(), pos);

	GuestMapType::iterator it = m_map_guest.find(ch);
	if (it == m_map_guest.end())
		return SHOP_SUBHEADER_GC_END;

	// Sahip duzenleme modundayken hic kimse bu pazardan alim yapamaz (hack paketine karsi)
	LPCHARACTER pkOwner = CHARACTER_MANAGER::instance().FindByPID(m_pkPC->GetPrivShopOwner());
	if (pkOwner && pkOwner->IsEditingShop())
		return SHOP_SUBHEADER_GC_END;

	SHOP_ITEM& r_item = m_itemVector[pos];

	if (r_item.price < 0)
		return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;

	DWORD dwPrice = r_item.price;

	if (ch->GetGold() < (int)dwPrice)
		return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;

#ifdef CANNOT_BUY_WORM
	if (ch->CountSpecifyItem(27801) > 0 && r_item.vnum == 27801)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CANNOT_BUY_WORM"));
		return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;
	}
#endif

	if (m_pkPC->GetPrivShopOwner() == ch->GetPlayerID())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Kendi dukkanindan satin alamazsin.");
		return SHOP_SUBHEADER_GC_OK;
	}

	LPITEM item = r_item.pkItem;
	if (!item)
		return SHOP_SUBHEADER_GC_OK;

	int iEmptyPos = ch->GetEmptyInventoryEx(item);
	if (iEmptyPos < 0)
		return SHOP_SUBHEADER_GC_INVENTORY_FULL;

	if (dwPrice > 0)
		ch->PointChange(POINT_GOLD, -static_cast<int>(dwPrice), false);

	LPITEM pkNewItem = ITEM_MANAGER::instance().CreateItem(r_item.vnum, r_item.count);
	if (!pkNewItem)
		return SHOP_SUBHEADER_GC_INVALID_POS;

	for (int i = 0; i < ITEM_SOCKET_MAX_NUM; i++)
		pkNewItem->SetSocket(i, item->GetSocket(i));

	item->CopyAttributeTo(pkNewItem);

	pkNewItem->AddToCharacter(ch, TItemPos(pkNewItem->GetWindowInventoryEx(), iEmptyPos));
	item->SetShop(NULL);
	item->RemoveFromCharacter();
	M2_DESTROY_ITEM(item);
	ITEM_MANAGER::instance().FlushDelayedSave(pkNewItem);

	DWORD mpid = m_pkPC->GetPrivShopOwner();

	char buf[512];
	snprintf(buf, sizeof(buf), "%s %u(%s) %u %u", pkNewItem->GetName(), mpid, m_pkPC->GetName(), dwPrice, pkNewItem->GetCount());
	LogManager::instance().ItemLog(ch, pkNewItem, "OFFLINE_SHOP_BUY", buf);
	snprintf(buf, sizeof(buf), "%s %u(%s) %u %u", pkNewItem->GetName(), ch->GetPlayerID(), ch->GetName(), dwPrice, pkNewItem->GetCount());
	LogManager::instance().ItemLog(m_pkPC, pkNewItem, "OFFLINE_SHOP_SELL", buf);

	r_item.pkItem = NULL;
	BroadcastUpdateItem(pos);

	// Offline dukkanlarda kazanc, sahibi cevrimdisi oldugu icin hediye kutusuna gider.
	DBManager::instance().DirectQuery("INSERT INTO player_gift SET owner_id = %u, vnum = 1 ,count = %u", m_pkPC->GetPrivShopOwner(), dwPrice);
	DBManager::instance().DirectQuery("DELETE FROM player_shop_items WHERE player_id = %u AND id = %u", m_pkPC->GetPrivShopOwner(), r_item.itemid);

	LPCHARACTER owner = CHARACTER_MANAGER::instance().FindByPID(m_pkPC->GetPrivShopOwner());
	if (owner)
		owner->RefreshGift();

	sys_log(0, "OFFLINE_SHOP: BUY: name %s %s(x %d):%u price %u", ch->GetName(), pkNewItem->GetName(), pkNewItem->GetCount(), pkNewItem->GetID(), dwPrice);

	ch->Save();

#ifdef SHOP_AUTO_CLOSE
	if (m_pkPC->IsPrivShop() && GetItemCount() <= 0)
		m_pkPC->DeleteMyShop();
#endif

	return (SHOP_SUBHEADER_GC_OK);
}

int CShop::GetItemCount()
{
	int count = 0;
	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		if (m_itemVector[i].pkItem)
			count++;
	}
	return count;
}

bool CShop::GetItems()
{
	if (!m_pkPC)
		return false;

	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		auto pkItem = m_itemVector[i].pkItem;
		if (!pkItem)
			continue;

		char szGiftQuery[4096];
		int giftQueryLen = snprintf(szGiftQuery, sizeof(szGiftQuery),
				"INSERT INTO player_gift SET owner_id = %u, vnum = %u, count = %u",
					m_pkPC->GetPrivShopOwner(), m_itemVector[i].vnum, m_itemVector[i].count);

		for (BYTE s = 0; s < ITEM_SOCKET_MAX_NUM; s++)
			giftQueryLen += snprintf(szGiftQuery + giftQueryLen, sizeof(szGiftQuery) - giftQueryLen, ", socket%d=%ld", s, pkItem->GetSocket(s));

		for (BYTE ia = 0; ia < ITEM_ATTRIBUTE_MAX_NUM; ia++)
		{
			const TPlayerItemAttribute& attr = pkItem->GetAttribute(ia);

			giftQueryLen += snprintf(szGiftQuery + giftQueryLen, sizeof(szGiftQuery) - giftQueryLen, ", attrtype%d=%d, attrvalue%d=%d", ia, attr.bType, ia, attr.sValue);
		}

		DBManager::instance().DirectQuery(szGiftQuery);

		DBManager::instance().DirectQuery("DELETE FROM player_shop_items WHERE id = %d", m_itemVector[i].itemid);
		pkItem->SetShop(NULL);
		pkItem->RemoveFromCharacter();
		m_itemVector[i].pkItem = NULL;
		BroadcastUpdateItem(i);
	}

	return true;
}

void CShop::SetPrivShopItems(std::vector<TShopItemTable *> map_shop)
{
	if (!m_pkPC || !m_pGrid)
		return;
	m_pGrid->Clear();

	m_itemVector.resize(SHOP_HOST_ITEM_MAX_NUM);
	memset(&m_itemVector[0], 0, sizeof(SHOP_ITEM) * m_itemVector.size());

	for (DWORD count = 0; count < map_shop.size(); count++)
	{
		TShopItemTable * pTable = map_shop[count];
		LPITEM pkItem = m_pkPC->GetItem(pTable->pos);

		if (!pkItem)
		{
			sys_err("cannot find item on pos (%d, %d) (name: %s)", pTable->pos.window_type, pTable->pos.cell, m_pkPC->GetName());
			continue;
		}

		const TItemTable * item_table = pkItem->GetProto();
		if (!item_table)
		{
			sys_err("Shop: no item table by item vnum #%d", pTable->vnum);
			continue;
		}

		WORD iPos = pTable->display_pos;

		if (!m_pGrid->IsEmpty(iPos, 1, item_table->bSize))
		{
			sys_err("not empty position for pc shop %s[%d] fixing", m_pkPC->GetName(), m_pkPC->GetPlayerID());
			iPos = m_pGrid->FindBlank(1, item_table->bSize);
			if (!m_pGrid->IsEmpty(iPos, 1, item_table->bSize))
			{
				sys_err("not empty position for pc shop %s[%d]", m_pkPC->GetName(), m_pkPC->GetPlayerID());
				continue;
			}
		}

		m_pGrid->Put(iPos, 1, item_table->bSize);

		SHOP_ITEM & item	= m_itemVector[iPos];
		item.pkItem			= pkItem;
		item.itemid			= 0;

		if (item.pkItem)
		{
			pkItem->SetShop(this);

			item.vnum		= pkItem->GetVnum();
			item.count		= pkItem->GetCount();
			item.price		= pTable->price;
			item.itemid		= pkItem->GetRealID();
		}

		char name[36];
		snprintf(name, sizeof(name), "%-20s(#%-5d) (x %d)", item_table->szName, (int)item.vnum, item.count);
		sys_log(0, "PRIV_SHOP_ITEM: %-36s PRICE %-5d", name, item.price);
	}
}

void CShop::RemoveItemForShop(DWORD dwItemID)// Suresi biten Kostum icin
{
	if (!m_pkPC || !dwItemID || m_itemVector.size() < SHOP_HOST_ITEM_MAX_NUM)
		return;

	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		if (m_itemVector[i].pkItem && m_itemVector[i].itemid == dwItemID)
		{
			DBManager::instance().DirectQuery("DELETE FROM player_shop_items WHERE id = %u", dwItemID);
			m_itemVector[i].pkItem->SetShop(NULL);
			m_itemVector[i].pkItem = NULL;
			BroadcastUpdateItem(i);

#ifdef SHOP_AUTO_CLOSE
			if (m_pkPC->IsPrivShop() && GetItemCount() <= 0)
				m_pkPC->DeleteMyShop();
#endif
			break;
		}
	}
}

void CShop::KickGuestsExcept(LPCHARACTER keep)
{
	// RemoveGuest map'i degistirdigi icin once kopya al
	std::vector<LPCHARACTER> vec;
	for (GuestMapType::iterator it = m_map_guest.begin(); it != m_map_guest.end(); ++it)
		if (it->first && it->first != keep)
			vec.push_back(it->first);

	for (DWORD i = 0; i < vec.size(); ++i)
	{
		LPCHARACTER guest = vec[i];
		RemoveGuest(guest);				// map'ten siler + SHOP_SUBHEADER_GC_END gonderir
		guest->SetShopOwner(NULL);
	}
}

void CShop::RebuildGrid()
{
	if (!m_pGrid)
		return;
	m_pGrid->Clear();
	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		LPITEM pkItem = m_itemVector[i].pkItem;
		if (!pkItem)
			continue;
		const TItemTable * proto = pkItem->GetProto();
		if (!proto)
			continue;
		m_pGrid->Put(i, 1, proto->bSize);
	}
}

bool CShop::EditWouldExceedLimit(const BYTE * pbRemovePos, BYTE byRemoveCount, const TShopItemTable * pAdd, BYTE byAddCount, const TOfflineShopPriceUpdate * pUpdate, BYTE byUpdateCount) const
{
	long long total = 0;

	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		if (!m_itemVector[i].pkItem)
			continue;

		bool removed = false;
		if (pbRemovePos)
			for (BYTE r = 0; r < byRemoveCount; ++r)
				if (pbRemovePos[r] == i) { removed = true; break; }
		if (removed)
			continue;

		long long price = (long long)m_itemVector[i].price;
		if (pUpdate)
			for (BYTE u = 0; u < byUpdateCount; ++u)
				if (pUpdate[u].display_pos == i) { price = (long long)pUpdate[u].price; break; }

		total += price;
	}

	if (pAdd)
		for (BYTE a = 0; a < byAddCount; ++a)
			total += (long long)pAdd[a].price;

	return total > (long long)GOLD_MAX;
}

void CShop::ApplyOwnerEdit(LPCHARACTER owner, const BYTE * pbRemovePos, BYTE byRemoveCount, const TShopItemTable * pAdd, BYTE byAddCount, const TOfflineShopPriceUpdate * pUpdate, BYTE byUpdateCount)
{
	if (!m_pkPC || !owner)
		return;

	const DWORD dwOwnerPID = owner->GetPlayerID();

	// 0) Fiyat guncellemeleri (var olan item'ler, sol-tik fiyat duzenleme)
	if (pUpdate)
	{
		for (BYTE i = 0; i < byUpdateCount; ++i)
		{
			const BYTE pos = pUpdate[i].display_pos;
			if (pos >= m_itemVector.size())
				continue;
			SHOP_ITEM & r = m_itemVector[pos];
			if (!r.pkItem)
				continue;

			// Yang overflow korumasi: fiyat GOLD_MAX'i asamaz
			DWORD price = pUpdate[i].price;
			if (price >= (DWORD)GOLD_MAX)
				price = (DWORD)GOLD_MAX - 1;

			DBManager::instance().DirectQuery("UPDATE player_shop_items SET price = %u WHERE id = %u", price, r.itemid);
			r.price = price;
			BroadcastUpdateItem(pos);
		}
	}

	// 1) Kaldirilanlar: dukkandaki item'in bir kopyasini sahibine ver (envanter, dolu ise hediye), DB satirini sil
	if (pbRemovePos)
	{
		for (BYTE i = 0; i < byRemoveCount; ++i)
		{
			const BYTE pos = pbRemovePos[i];
			if (pos >= m_itemVector.size())
				continue;
			SHOP_ITEM & r = m_itemVector[pos];
			LPITEM pkItem = r.pkItem;
			if (!pkItem)
				continue;

			DBManager::instance().DirectQuery("DELETE FROM player_shop_items WHERE id = %u", r.itemid);

			LPITEM pkNew = ITEM_MANAGER::instance().CreateItem(r.vnum, r.count);
			if (pkNew)
			{
				for (int s = 0; s < ITEM_SOCKET_MAX_NUM; s++)
					pkNew->SetSocket(s, pkItem->GetSocket(s));
				pkItem->CopyAttributeTo(pkNew);

				int iEmptyPos = owner->GetEmptyInventoryEx(pkNew);
				if (iEmptyPos >= 0)
				{
					pkNew->AddToCharacter(owner, TItemPos(pkNew->GetWindowInventoryEx(), iEmptyPos));
					ITEM_MANAGER::instance().FlushDelayedSave(pkNew);
				}
				else
				{
					char szGiftQuery[4096];
					int giftLen = snprintf(szGiftQuery, sizeof(szGiftQuery),
						"INSERT INTO player_gift SET owner_id = %u, vnum = %u, count = %u",
						dwOwnerPID, pkNew->GetVnum(), pkNew->GetCount());
					for (BYTE s = 0; s < ITEM_SOCKET_MAX_NUM; s++)
						giftLen += snprintf(szGiftQuery + giftLen, sizeof(szGiftQuery) - giftLen, ", socket%d=%ld", s, pkNew->GetSocket(s));
					for (BYTE ia = 0; ia < ITEM_ATTRIBUTE_MAX_NUM; ia++)
					{
						const TPlayerItemAttribute & attr = pkNew->GetAttribute(ia);
						giftLen += snprintf(szGiftQuery + giftLen, sizeof(szGiftQuery) - giftLen, ", attrtype%d=%d, attrvalue%d=%d", ia, attr.bType, ia, attr.sValue);
					}
					DBManager::instance().DirectQuery(szGiftQuery);
					M2_DESTROY_ITEM(pkNew);

					LPCHARACTER online = CHARACTER_MANAGER::instance().FindByPID(dwOwnerPID);
					if (online)
						online->RefreshGift();
				}
			}

			pkItem->SetShop(NULL);
			pkItem->RemoveFromCharacter();
			M2_DESTROY_ITEM(pkItem);

			r.pkItem = NULL;
			r.vnum = 0; r.count = 0; r.price = 0; r.itemid = 0;
			BroadcastUpdateItem(pos);
		}
	}

	// Kaldirmalardan sonra grid'i guncelle (eklemelerde bos slot dogru bulunsun)
	RebuildGrid();

	// 2) Eklenenler: sahibin envanterinden dukkana
	if (pAdd)
	{
		for (BYTE i = 0; i < byAddCount; ++i)
		{
			const TShopItemTable & t = pAdd[i];
			LPITEM pkSrc = owner->GetItem(t.pos);
			if (!pkSrc)
				continue;
			if (pkSrc->GetOwner() != owner || pkSrc->IsExchanging() || pkSrc->IsEquipped() || pkSrc->isLocked())
				continue;
			const TItemTable * proto = pkSrc->GetProto();
			if (!proto || (IS_SET(proto->dwAntiFlags, ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP)))
				continue;
			if (!pkSrc->CheckItemEnchant())
				continue;

#ifdef ENABLE_ITEM_SHOP_SYSTEM
	  // Markete eklenmesi kisitli (EmShop'a bagli) itemler pazara eklenemez
	  if (pkSrc->IsItemShopEmBound())
	  {
		owner->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketemitemkisitli"));
		continue;
	  }
#endif

			WORD iPos = t.display_pos;
			if (!m_pGrid || iPos >= SHOP_HOST_ITEM_MAX_NUM || !m_pGrid->IsEmpty(iPos, 1, proto->bSize))
			{
				if (!m_pGrid)
					continue;
				iPos = m_pGrid->FindBlank(1, proto->bSize);
				if (iPos >= SHOP_HOST_ITEM_MAX_NUM || !m_pGrid->IsEmpty(iPos, 1, proto->bSize))
					continue;
			}

			// Yang overflow korumasi: fiyat GOLD_MAX'i asamaz
			DWORD dwPrice = t.price;
			if (dwPrice >= (DWORD)GOLD_MAX)
				dwPrice = (DWORD)GOLD_MAX - 1;

			char query[1024];
			snprintf(query, sizeof(query), "INSERT INTO player_shop_items SET");
			snprintf(query, sizeof(query), "%s player_id = %u",			query, dwOwnerPID);
			snprintf(query, sizeof(query), "%s, vnum = %u",				query, pkSrc->GetVnum());
			snprintf(query, sizeof(query), "%s, count = %d",			query, pkSrc->GetCount());
			snprintf(query, sizeof(query), "%s, price = %u",			query, dwPrice);
			snprintf(query, sizeof(query), "%s, display_pos = %d",		query, iPos);
			for (BYTE s = 0; s < ITEM_SOCKET_MAX_NUM; s++)
				snprintf(query, sizeof(query), "%s, socket%d = %ld",	query, s, pkSrc->GetSocket(s));
			for (BYTE ia = 0; ia < ITEM_ATTRIBUTE_MAX_NUM; ia++)
			{
				const TPlayerItemAttribute & attr = pkSrc->GetAttribute(ia);
				snprintf(query, sizeof(query), "%s, attrtype%d = %u",	query, ia, attr.bType);
				snprintf(query, sizeof(query), "%s, attrvalue%d = %d",	query, ia, attr.sValue);
			}
			auto pkMsg = DBManager::instance().DirectQuery(query);
			if (!pkMsg || !pkMsg->Get() || pkMsg->Get()->uiInsertID == 0)
				continue;
			const DWORD newId = pkMsg->Get()->uiInsertID;

			// NPC'de tutulacak skip-save display item'i olustur (OpenShop ile ayni mantik)
			LPITEM pkDisplay = ITEM_MANAGER::instance().CreateItem(pkSrc->GetVnum(), pkSrc->GetCount(), 0, false, -1, true);
			if (!pkDisplay)
			{
				DBManager::instance().DirectQuery("DELETE FROM player_shop_items WHERE id = %u", newId);
				continue;
			}
			pkDisplay->ClearAttribute();
			pkDisplay->SetSkipSave(true);
			pkDisplay->SetRealID(newId);
			for (int s = 0; s < ITEM_SOCKET_MAX_NUM; s++)
				pkDisplay->SetSocket(s, pkSrc->GetSocket(s), false);
			for (int at = 0; at < ITEM_ATTRIBUTE_MAX_NUM; at++)
			{
				const TPlayerItemAttribute & attr = pkSrc->GetAttribute(at);
				pkDisplay->SetForceAttribute(at, attr.bType, attr.sValue);
			}

			const int iCell = m_pkPC->GetEmptyInventory(proto->bSize);
			if (iCell < 0)
			{
				M2_DESTROY_ITEM(pkDisplay);
				DBManager::instance().DirectQuery("DELETE FROM player_shop_items WHERE id = %u", newId);
				continue;
			}
			pkDisplay->AddToCharacter(m_pkPC, TItemPos(INVENTORY, iCell));

			// Sahibin envanterindeki orijinali tuket
			ITEM_MANAGER::instance().RemoveItem(pkSrc, "Pazara Eklendi (Duzenleme)");

			SHOP_ITEM & it = m_itemVector[iPos];
			it.pkItem = pkDisplay;
			it.vnum   = pkDisplay->GetVnum();
			it.count  = pkDisplay->GetCount();
			it.price  = dwPrice;
			it.itemid = newId;
			pkDisplay->SetShop(this);

			m_pGrid->Put(iPos, 1, proto->bSize);
			BroadcastUpdateItem(iPos);
		}
	}
}
#endif

int CShop::Buy(LPCHARACTER ch, BYTE pos)
{
	if (pos >= m_itemVector.size())
	{
		sys_log(0, "Shop::Buy : invalid position %d : %s", pos, ch->GetName());
		return SHOP_SUBHEADER_GC_INVALID_POS;
	}

	sys_log(0, "Shop::Buy : name %s pos %d", ch->GetName(), pos);

	const auto it = m_map_guest.find(ch);

	if (it == m_map_guest.end())
		return SHOP_SUBHEADER_GC_END;

	SHOP_ITEM& r_item = m_itemVector[pos];

#ifdef ENABLE_FISHING_ANTI_MACRO
	// Balik makro engeli: sadece NPC dukkanlarinda (m_pkPC == NULL) gecerli.
	// Envanterinde zaten Solucan (27801) varken NPC'den yeni Solucan satin alinamaz.
	if (!m_pkPC && r_item.vnum == 27801 && ch->CountSpecifyItem(27801) > 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("SHOP_BUY_NO_WORM"));
		// GC_OK: satin almayi sessizce iptal eder (yaniltici "yetersiz para" mesaji cikmaz), pazar acik kalir
		return SHOP_SUBHEADER_GC_OK;
	}
#endif

#ifdef OFFLINE_SHOP
	// Offline (kalici) sahis dukkanlari icin ayri satin alma yolu;
	// normal NPC dukkanlari ve online sahis dukkanlari asagidaki standart akistan gecer.
	if (m_pkPC && m_pkPC->IsPrivShop())
		return BuyOffline(ch, pos);
#endif

#ifdef ENABLE_SHOP_USE_CHEQUE
	if (r_item.price < 0)
	{
		LogManager::instance().HackLog("SHOP_BUY_GOLD_OVERFLOW", ch);
		return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;
	}
	else if (r_item.cheque < 0)
	{
		LogManager::instance().HackLog("SHOP_BUY_CHEQUE_OVERFLOW", ch);
		return SHOP_SUBHEADER_GC_NOT_ENOUGH_CHEQUE;
	}
#else
	if (r_item.price <= 0
#ifdef ENABLE_MULTISHOP
		&& r_item.gemPrice <= 0
		&& r_item.wPriceVnum == 0
#endif
		)
	{
		LogManager::instance().HackLog("SHOP_BUY_GOLD_OVERFLOW", ch);
		return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;
	}
#endif

	const LPITEM pkSelectedItem = ITEM_MANAGER::instance().Find(r_item.itemid);

	if (IsPCShop())
	{
		if (!pkSelectedItem)
		{
			sys_log(0, "Shop::Buy : Critical: This user seems to be a hacker : invalid pcshop item : BuyerPID:%d SellerPID:%d",
					ch->GetPlayerID(),
					m_pkPC->GetPlayerID());

			return SHOP_SUBHEADER_GC_SOLD_OUT; // @fixme132 false to SHOP_SUBHEADER_GC_SOLD_OUT
		}

		if ((pkSelectedItem->GetOwner() != m_pkPC))
		{
			sys_log(0, "Shop::Buy : Critical: This user seems to be a hacker : invalid pcshop item : BuyerPID:%d SellerPID:%d",
					ch->GetPlayerID(),
					m_pkPC->GetPlayerID());

			return SHOP_SUBHEADER_GC_SOLD_OUT; // @fixme132 false to SHOP_SUBHEADER_GC_SOLD_OUT
		}
	}

	DWORD dwPrice = r_item.price;

#ifdef ENABLE_SHOP_USE_CHEQUE
	DWORD dwCheque = r_item.cheque;
#endif

	DWORD dwWItemVnum = 0;
	DWORD dwWItemPrice = 0;
	DWORD dwGemPrice = 0;
#ifdef ENABLE_MULTISHOP
	dwWItemVnum = r_item.wPriceVnum;
	dwWItemPrice = r_item.wPrice;
	dwGemPrice = r_item.gemPrice;
#endif

	//if (it->second)	// if other empire, price is triple
	//	dwPrice *= 3;

#ifdef ENABLE_SHOP_USE_CHEQUE
	{
		const bool bItemPay =
#ifdef ENABLE_MULTISHOP
			(dwGemPrice == 0 && dwWItemVnum > 0);
#else
			false;
#endif
#if defined(ENABLE_MULTISHOP) && defined(__GEM_SYSTEM__)
		const bool bGemPay = (dwGemPrice > 0);
#else
		const bool bGemPay = false;
#endif

		if (bGemPay)
		{
#ifdef __GEM_SYSTEM__
			if (ch->GetGem() < static_cast<int>(dwGemPrice))
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_GEM;
#endif
		}
		else if (bItemPay)
		{
			if (ch->CountSpecifyItem(dwWItemVnum) < static_cast<int>(dwWItemPrice))
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_ITEM;
		}
		else if ((int)dwPrice > 0 && (int)dwCheque > 0) // Yang-Cheque
		{
			if (ch->GetGold() < (int)dwPrice || ch->GetCheque() < (int)dwCheque)
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY_CHEQUE;
		}
		else if ((int)dwPrice > 0 && (int)dwCheque <= 0) // Yang
		{
			if (ch->GetGold() < (int)dwPrice)
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;
		}
		else if ((int)dwPrice <= 0 && (int)dwCheque > 0) // cheque
		{
			if (ch->GetCheque() < (int)dwCheque)
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_CHEQUE;
		}
	}
#else
	{
		const bool bItemPay =
#ifdef ENABLE_MULTISHOP
			(dwGemPrice == 0 && dwWItemVnum > 0);
#else
			false;
#endif
#if defined(ENABLE_MULTISHOP) && defined(__GEM_SYSTEM__)
		const bool bGemPay = (dwGemPrice > 0);
#else
		const bool bGemPay = false;
#endif

		if (bGemPay)
		{
#ifdef __GEM_SYSTEM__
			if (ch->GetGem() < static_cast<int>(dwGemPrice))
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_GEM;
#endif
		}
		else if (bItemPay)
		{
			if (ch->CountSpecifyItem(dwWItemVnum) < static_cast<int>(dwWItemPrice))
				return SHOP_SUBHEADER_GC_NOT_ENOUGH_ITEM;
		}
		else if (ch->GetGold() < (int) dwPrice)
		{
			sys_log(1, "Shop::Buy : Not enough money : %s has %d, price %d", ch->GetName(), ch->GetGold(), dwPrice);
			return SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY;
		}
	}
#endif

	LPITEM item;

	if (m_pkPC)
		item = r_item.pkItem;
	else
		item = ITEM_MANAGER::instance().CreateItem(r_item.vnum, r_item.count);

	if (!item)
		return SHOP_SUBHEADER_GC_SOLD_OUT;

#ifdef ENABLE_SHOP_BLACKLIST
	if (!m_pkPC)
	{
		if (quest::CQuestManager::instance().GetEventFlag("hivalue_item_sell") == 0)
		{
			if (item->GetVnum() == 70024 || item->GetVnum() == 70035)
			{
				return SHOP_SUBHEADER_GC_END;
			}
		}
	}
#endif

	const int iEmptyPos = ch->GetEmptyInventoryEx(item);
	if (iEmptyPos < 0)
	{
		if (m_pkPC)
		{
			sys_log(1, "Shop::Buy at PC Shop : Inventory full : %s size %d", ch->GetName(), item->GetSize());
			return SHOP_SUBHEADER_GC_INVENTORY_FULL;
		}
		else
		{
			sys_log(1, "Shop::Buy : Inventory full : %s size %d", ch->GetName(), item->GetSize());
			M2_DESTROY_ITEM(item);
			return SHOP_SUBHEADER_GC_INVENTORY_FULL;
		}
	}

#if defined(ENABLE_MULTISHOP) && defined(__GEM_SYSTEM__)
	if (dwGemPrice > 0)
		ch->PointChange(POINT_GEM, -static_cast<int>(dwGemPrice), false);
	else
#endif
#ifdef ENABLE_MULTISHOP
	if (dwWItemVnum > 0)
		ch->RemoveSpecifyItem(dwWItemVnum, dwWItemPrice);
	else
#endif
		ch->PointChange(POINT_GOLD, -dwPrice, false);
#ifdef ENABLE_SHOP_USE_CHEQUE
#if defined(ENABLE_MULTISHOP) && defined(__GEM_SYSTEM__)
	if (dwGemPrice == 0)
#endif
	ch->PointChange(POINT_CHEQUE, -dwCheque, false);
#endif

	DWORD dwTax = 0;
	int iVal = 0;

	{
		iVal = quest::CQuestManager::instance().GetEventFlag("personal_shop");

		if (0 < iVal)
		{
			if (iVal > 100)
				iVal = 100;

			dwTax = dwPrice * iVal / 100;
			dwPrice = dwPrice - dwTax;
		}
		else
		{
			iVal = 0;
			dwTax = 0;
		}
	}

	if (!m_pkPC)
	{
		CMonarch::instance().SendtoDBAddMoney(dwTax, ch->GetEmpire(), ch);
	}

	if (m_pkPC)
	{
		m_pkPC->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);

		{
			char buf[512];

			if (item->GetVnum() >= 80003 && item->GetVnum() <= 80007)
			{
				snprintf(buf, sizeof(buf), "%s FROM: %u TO: %u PRICE: %u", item->GetName(), ch->GetPlayerID(), m_pkPC->GetPlayerID(), dwPrice);
				LogManager::instance().GoldBarLog(ch->GetPlayerID(), item->GetID(), SHOP_BUY, buf);
				LogManager::instance().GoldBarLog(m_pkPC->GetPlayerID(), item->GetID(), SHOP_SELL, buf);
			}

			item->RemoveFromCharacter();
			ch->AutoStackItemEx(item, false, iEmptyPos); // @fixme316

			snprintf(buf, sizeof(buf), "%s %u(%s) %u %u", item->GetName(), m_pkPC->GetPlayerID(), m_pkPC->GetName(), dwPrice, item->GetCount());
			LogManager::instance().ItemLog(ch, item, "SHOP_BUY", buf);

			snprintf(buf, sizeof(buf), "%s %u(%s) %u %u", item->GetName(), ch->GetPlayerID(), ch->GetName(), dwPrice, item->GetCount());
			LogManager::instance().ItemLog(m_pkPC, item, "SHOP_SELL", buf);
		}

		r_item.pkItem = nullptr;
		BroadcastUpdateItem(pos);

		m_pkPC->PointChange(POINT_GOLD, dwPrice, false);
#ifdef ENABLE_SHOP_USE_CHEQUE
		m_pkPC->PointChange(POINT_CHEQUE, dwCheque, false);
#endif
		if (iVal > 0)
			m_pkPC->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("판매금액의 %d %% 가 세금으로 나가게됩니다"), iVal);

		CMonarch::instance().SendtoDBAddMoney(dwTax, m_pkPC->GetEmpire(), m_pkPC);
	}
	else
	{
		ch->AutoStackItemEx(item, false, iEmptyPos); // @fixme316

		LogManager::instance().ItemLog(ch, item, "BUY", item->GetName());
		if (item->GetVnum() >= 80003 && item->GetVnum() <= 80007)
			LogManager::instance().GoldBarLog(ch->GetPlayerID(), item->GetID(), PERSONAL_SHOP_BUY, "");
		DBManager::instance().SendMoneyLog(MONEY_LOG_SHOP, item->GetVnum(), -dwPrice);
	}

	if (item)
		sys_log(0, "SHOP: BUY: name %s %s(x %d):%u price %u", ch->GetName(), item->GetName(), item->GetCount(), item->GetID(), dwPrice);

    ch->Save();

    return (SHOP_SUBHEADER_GC_OK);
}

bool CShop::AddGuest(LPCHARACTER ch, DWORD owner_vid, bool bOtherEmpire)
{
	if (!ch)
		return false;

	if (ch->GetExchange())
		return false;

	if (ch->GetShop())
		return false;

	ch->SetShop(this);

	m_map_guest.emplace(ch, bOtherEmpire);

	TPacketGCShop pack;

	pack.header		= HEADER_GC_SHOP;
	pack.subheader	= SHOP_SUBHEADER_GC_START;

	TPacketGCShopStart pack2;

	memset(&pack2, 0, sizeof(pack2));
	pack2.owner_vid = owner_vid;
#ifdef OFFLINE_SHOP
	pack2.byIsMyShop = (m_pkPC && m_pkPC->GetPrivShopOwner() == ch->GetPlayerID()) ? 1 : 0;
#endif

	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		const SHOP_ITEM & item = m_itemVector[i];

#ifdef ENABLE_SHOP_BLACKLIST
		//HIVALUE_ITEM_EVENT
		if (quest::CQuestManager::instance().GetEventFlag("hivalue_item_sell") == 0)
		{
			if (item.vnum == 70024 || item.vnum == 70035)
			{
				continue;
			}
		}
#endif
		//END_HIVALUE_ITEM_EVENT
		if (m_pkPC && !item.pkItem)
			continue;

		pack2.items[i].vnum = item.vnum;

		// REMOVED_EMPIRE_PRICE_LIFT
#ifdef ENABLE_NEWSTUFF
		if (bOtherEmpire && !g_bEmpireShopPriceTripleDisable) // no empire price penalty for pc shop
#else
		if (bOtherEmpire) // no empire price penalty for pc shop
#endif
		{
			pack2.items[i].price = item.price * 3;
		}
		else
			pack2.items[i].price = item.price;

#ifdef ENABLE_CHEQUE_SYSTEM
		pack2.items[i].cheque = item.cheque;
#endif
		// END_REMOVED_EMPIRE_PRICE_LIFT
#ifdef ENABLE_MULTISHOP
		pack2.items[i].wPriceVnum = item.wPriceVnum;
		pack2.items[i].wPrice = item.wPrice;
		pack2.items[i].gem_price = item.gemPrice;
#endif

		pack2.items[i].count = item.count;

		if (item.pkItem)
		{
			thecore_memcpy(pack2.items[i].alSockets, item.pkItem->GetSockets(), sizeof(pack2.items[i].alSockets));
			thecore_memcpy(pack2.items[i].aAttr, item.pkItem->GetAttributes(), sizeof(pack2.items[i].aAttr));
		}
	}

	pack.size = sizeof(pack) + sizeof(pack2);

	ch->GetDesc()->BufferedPacket(&pack, sizeof(TPacketGCShop));
	ch->GetDesc()->Packet(&pack2, sizeof(TPacketGCShopStart));
	return true;
}

void CShop::RemoveGuest(LPCHARACTER ch)
{
	if (ch->GetShop() != this)
		return;

	m_map_guest.erase(ch);
	ch->SetShop(nullptr);

	TPacketGCShop pack;

	pack.header		= HEADER_GC_SHOP;
	pack.subheader	= SHOP_SUBHEADER_GC_END;
	pack.size		= sizeof(TPacketGCShop);

	ch->GetDesc()->Packet(&pack, sizeof(pack));
}

void CShop::Broadcast(const void * data, int bytes)
{
	sys_log(1, "Shop::Broadcast %p %d", data, bytes);

	GuestMapType::iterator it;

	it = m_map_guest.begin();

	while (it != m_map_guest.end())
	{
		const LPCHARACTER ch = it->first;

		if (ch->GetDesc())
			ch->GetDesc()->Packet(data, bytes);

		++it;
	}
}

void CShop::BroadcastUpdateItem(BYTE pos)
{
	TPacketGCShop pack;
	TPacketGCShopUpdateItem pack2;

	TEMP_BUFFER	buf;

	pack.header		= HEADER_GC_SHOP;
	pack.subheader	= SHOP_SUBHEADER_GC_UPDATE_ITEM;
	pack.size		= sizeof(pack) + sizeof(pack2);

	pack2.pos		= pos;

	if (m_pkPC && !m_itemVector[pos].pkItem)
		pack2.item.vnum = 0;
	else
	{
		pack2.item.vnum	= m_itemVector[pos].vnum;
		if (m_itemVector[pos].pkItem)
		{
			thecore_memcpy(pack2.item.alSockets, m_itemVector[pos].pkItem->GetSockets(), sizeof(pack2.item.alSockets));
			thecore_memcpy(pack2.item.aAttr, m_itemVector[pos].pkItem->GetAttributes(), sizeof(pack2.item.aAttr));
		}
		else
		{
			memset(pack2.item.alSockets, 0, sizeof(pack2.item.alSockets));
			memset(pack2.item.aAttr, 0, sizeof(pack2.item.aAttr));
		}
	}

	pack2.item.price	= m_itemVector[pos].price;
	pack2.item.count	= m_itemVector[pos].count;
#ifdef ENABLE_CHEQUE_SYSTEM
	pack2.item.cheque = m_itemVector[pos].cheque;
#endif

#ifdef ENABLE_MULTISHOP
	pack2.item.wPriceVnum = m_itemVector[pos].wPriceVnum;
	pack2.item.wPrice = m_itemVector[pos].wPrice;
	pack2.item.gem_price = m_itemVector[pos].gemPrice;
#endif

	buf.write(&pack, sizeof(pack));
	buf.write(&pack2, sizeof(pack2));

	Broadcast(buf.read_peek(), buf.size());
}

int CShop::GetNumberByVnum(DWORD dwVnum) const
{
	int itemNumber = 0;

	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		const SHOP_ITEM & item = m_itemVector[i];

		if (item.vnum == dwVnum)
		{
			itemNumber += item.count;
		}
	}

	return itemNumber;
}

bool CShop::IsSellingItem(DWORD itemID)
{
	bool isSelling = false;

	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		if ((unsigned int)(m_itemVector[i].itemid) == itemID)
		{
			isSelling = true;
			break;
		}
	}

	return isSelling;
}

#ifdef OFFLINE_SHOP
// ---------------------------------------------------------------------------
// Pazar Arama (ShopSearch) - esya eslestirme yardimcilari
// Kaynak (mt2009 ikarus) CShop::HasItem / HasItemType / HasSoulStoneSocket
// fonksiyonlarinin new_project CShop::m_itemVector modeline uyarlanmis halidir.
// ---------------------------------------------------------------------------
bool CShop::HasItem(DWORD itemVnum, int socket0) const
{
	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		const SHOP_ITEM & item = m_itemVector[i];

		if (item.vnum != itemVnum)
			continue;

		// socket0 == 0 ise sadece vnum eslesmesi yeterli (NPC/offline esyalar dahil)
		if (socket0 == 0)
			return true;

		// socket0 verilmisse (orn. beceri kitabi soketi) gercek item gerekir
		if (item.pkItem && item.pkItem->GetSocket(0) == socket0)
			return true;
	}
	return false;
}

bool CShop::HasItemType(BYTE type, BYTE subtype, bool checkAttribute) const
{
	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		LPITEM pkItem = m_itemVector[i].pkItem;
		if (!pkItem)
			continue;

		const TItemTable * proto = pkItem->GetProto();
		if (proto && proto->bType == type && proto->bSubType == subtype)
		{
			// "Bonuslu ara" secili ise sadece bonusu olan esyalar
			if (checkAttribute && pkItem->GetAttribute(0).bType == 0)
				continue;

			return true;
		}
	}
	return false;
}

bool CShop::HasSoulStoneSocket(BYTE level) const
{
	for (DWORD i = 0; i < m_itemVector.size() && i < SHOP_HOST_ITEM_MAX_NUM; ++i)
	{
		const DWORD vnum = m_itemVector[i].vnum;
		if (vnum >= (DWORD)(28030 + 100 * level) && vnum <= (DWORD)(28043 + 100 * level))
			return true;
	}
	return false;
}
#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
