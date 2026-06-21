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
#include "desc_client.h"
#include "shop_manager.h"
#include "group_text_parse_tree.h"
#include "shopEx.h"
#include "shop_manager.h"
#include <cctype>
#ifdef OFFLINE_SHOP
	#include <boost/algorithm/string/replace.hpp>
#endif
#ifdef ENABLE_NEWSTUFF
#include "../../common/PulseManager.h"
#endif

CShopManager::CShopManager()
{
#ifdef OFFLINE_SHOP
	PrepareShopSearchFilters();
#endif
}

CShopManager::~CShopManager()
{
	Destroy();
}

bool CShopManager::Initialize(TShopTable * table, int size)
{
	if (!m_map_pkShop.empty())
		return false;

	int i;

	for (i = 0; i < size; ++i, ++table)
	{
		auto shop = M2_NEW CShop;

		if (!shop->Create(table->dwVnum, table->dwNPCVnum, table->items))
		{
			M2_DELETE(shop);
			continue;
		}

		m_map_pkShop.emplace(table->dwVnum, shop);
		m_map_pkShopByNPCVnum.emplace(table->dwNPCVnum, shop);
	}
	char szShopTableExFileName[256];

	snprintf(szShopTableExFileName, sizeof(szShopTableExFileName),
		"%s/shop_table_ex.txt", LocaleService_GetBasePath().c_str());

	return ReadShopTableEx(szShopTableExFileName);
}

void CShopManager::Destroy()
{
	auto it = m_map_pkShop.begin();

	while (it != m_map_pkShop.end())
	{
		M2_DELETE(it->second);
		++it;
	}

	m_map_pkShop.clear();
}

LPSHOP CShopManager::Get(DWORD dwVnum)
{
	const TShopMap::const_iterator it = m_map_pkShop.find(dwVnum);

	if (it == m_map_pkShop.end())
		return nullptr;

	return (it->second);
}

LPSHOP CShopManager::GetByNPCVnum(DWORD dwVnum)
{
	const TShopMap::const_iterator it = m_map_pkShopByNPCVnum.find(dwVnum);

	if (it == m_map_pkShopByNPCVnum.end())
		return nullptr;

	return (it->second);
}

bool CShopManager::StartShopping(LPCHARACTER pkChr, LPCHARACTER pkChrShopKeeper, int iShopVnum)
{
	if (pkChr->IsDead()) // @fixme326
		return false;

	if (pkChr->GetShopOwner() == pkChrShopKeeper)
		return false;

	// this method is only for NPC
	if (pkChrShopKeeper->IsPC())
		return false;

	//PREVENT_TRADE_WINDOW
	if (pkChr->IsOpenSafebox() || pkChr->GetExchange() || pkChr->GetMyShop() || pkChr->IsCubeOpen()
#ifdef OFFLINE_SHOP
		|| pkChr->IsEditingShop()
#endif
#ifdef ENABLE_SAFE_TRADE_SYSTEM
		|| pkChr->GetSafeTrade() || pkChr->IsSafeTradeClaiming()
#endif
		)
	{
		pkChr->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("다른 거래창이 열린상태에서는 상점거래를 할수 가 없습니다."));
		return false;
	}
	//END_PREVENT_TRADE_WINDOW

	const long distance = DISTANCE_APPROX(pkChr->GetX() - pkChrShopKeeper->GetX(), pkChr->GetY() - pkChrShopKeeper->GetY());

	if (distance >= SHOP_MAX_DISTANCE)
	{
		sys_log(1, "SHOP: TOO_FAR: %s distance %d", pkChr->GetName(), distance);
		return false;
	}

	LPSHOP pkShop;

	if (iShopVnum)
		pkShop = Get(iShopVnum);
	else
		pkShop = GetByNPCVnum(pkChrShopKeeper->GetRaceNum());

	if (!pkShop)
	{
		sys_log(1, "SHOP: NO SHOP");
		return false;
	}

	bool bOtherEmpire = false;

	if (pkChr->GetEmpire() != pkChrShopKeeper->GetEmpire())
		bOtherEmpire = true;

	pkShop->AddGuest(pkChr, pkChrShopKeeper->GetVID(), bOtherEmpire);
	pkChr->SetShopOwner(pkChrShopKeeper);
	sys_log(0, "SHOP: START: %s", pkChr->GetName());
	return true;
}

LPSHOP CShopManager::FindPCShop(DWORD dwVID)
{
	const auto it = m_map_pkShopByPC.find(dwVID);

	if (it == m_map_pkShopByPC.end())
		return nullptr;

	return it->second;
}

LPSHOP CShopManager::CreatePCShop(LPCHARACTER ch, TShopItemTable * pTable, BYTE bItemCount)
{
	if (FindPCShop(ch->GetVID()))
		return nullptr;

	auto pkShop = M2_NEW CShop;
	pkShop->SetPCShop(ch);
	pkShop->SetShopItems(pTable, bItemCount);

	m_map_pkShopByPC.emplace(ch->GetVID(), pkShop);
	return pkShop;
}

void CShopManager::DestroyPCShop(LPCHARACTER ch)
{
#ifdef OFFLINE_SHOP
	DWORD dwID = (ch->IsPrivShop()) ? (ch->GetPrivShopOwner()) : (ch->GetVID());
	if (dwID == 0)
		return;

	const LPSHOP pkShop = FindPCShop(dwID);
#else
	const LPSHOP pkShop = FindPCShop(ch->GetVID());
#endif

	if (!pkShop)
		return;

	//PREVENT_ITEM_COPY;
	ch->SetMyShopTime();
	//END_PREVENT_ITEM_COPY

#ifdef OFFLINE_SHOP
	m_map_pkShopByPC.erase(dwID);
#else
	m_map_pkShopByPC.erase(ch->GetVID());
#endif
	M2_DELETE(pkShop);
}

#ifdef OFFLINE_SHOP
void CShopManager::CreateOfflineShop(LPCHARACTER owner, const char *szSign, const std::vector<TShopItemTable *> pTable)
{
	if (!owner || !owner->IsPC())
		return;

	char szOriginalSign[SHOP_SIGN_MAX_LEN * 2 + 1];
	DBManager::Instance().EscapeString(szOriginalSign, sizeof(szOriginalSign), szSign, strlen(szSign));
	if (strlen(szOriginalSign) == 0 || strstr(szOriginalSign, "%") || strstr(szOriginalSign, "'") || strstr(szOriginalSign, "/"))
	{
		owner->ChatPacket(CHAT_TYPE_INFO, "string yanlis");
		return;
	}

	// Grid kontrolu
	CGrid *pGrid = M2_NEW CGrid(5, 9);
	for (size_t i = 0; i < pTable.size(); i++)
	{
		LPITEM item = owner->GetItem(pTable[i]->pos);
		if (!item)
			continue;

#ifdef ENABLE_ITEM_SHOP_SYSTEM
		if (item->IsItemShopEmBound())
		{
			owner->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketemitemkisitli"));
			M2_DELETE(pGrid);
			return;
		}
#endif

		const BYTE display_pos = pTable[i]->display_pos;
		const TItemTable * itemProto = item->GetProto();
		if (!itemProto || !pGrid->IsEmpty(display_pos, 1, itemProto->bSize))
		{
			owner->ChatPacket(CHAT_TYPE_INFO, "Pazarda Hatali Item Var... - [Slot Num: %d]", display_pos);
			M2_DELETE(pGrid);
			return;
		}

		pGrid->Put(display_pos, 1, itemProto->bSize);
	}
	M2_DELETE(pGrid);

	char szQuery[4096];
	DWORD date_close = get_global_time() + (60 * 60 * 24 * 7);
	snprintf(szQuery, sizeof(szQuery), "INSERT INTO player_shop SET player_id=%d, name='%s', map_index=%ld, x=%ld, y=%ld, date_close=%u, channel=%d",
									owner->GetPlayerID(), szOriginalSign, owner->GetMapIndex(), owner->GetX(), owner->GetY(), date_close, g_bChannel);

	auto pkMsg = DBManager::instance().DirectQuery(szQuery);
	if (!pkMsg || !pkMsg->Get())
		return;

	for (size_t i = 0; i < pTable.size(); i++)
	{
		LPITEM item = owner->GetItem(pTable[i]->pos);
		if (!item)
			continue;

		char query[1024];
		snprintf(query, sizeof(query), "INSERT INTO player_shop_items SET");
		snprintf(query, sizeof(query), "%s player_id = %u",			query, owner->GetPlayerID());
		snprintf(query, sizeof(query), "%s, vnum = %u",				query, item->GetVnum());
		snprintf(query, sizeof(query), "%s, count = %d",			query, item->GetCount());
		snprintf(query, sizeof(query), "%s, price = %u",			query, pTable[i]->price);
		snprintf(query, sizeof(query), "%s, display_pos = %d",		query, pTable[i]->display_pos);

		for (BYTE s = 0; s < ITEM_SOCKET_MAX_NUM; s++)
			snprintf(query, sizeof(query), "%s, socket%d = %ld",	query, s, item->GetSocket(s));

		for (BYTE ia = 0; ia < ITEM_ATTRIBUTE_MAX_NUM; ia++)
		{
			const TPlayerItemAttribute& attr = item->GetAttribute(ia);

			snprintf(query, sizeof(query), "%s, attrtype%d = %u",	query, ia, attr.bType);
			snprintf(query, sizeof(query), "%s, attrvalue%d = %d",	query, ia, attr.sValue);
		}

		DBManager::instance().DirectQuery(query);
		ITEM_MANAGER::Instance().RemoveItem(item, "Pazara Eklendi");
	}

	StartOfflineShop(owner->GetPlayerID());
	owner->SetMyShopTime();
}

bool CShopManager::StartOfflineShop(DWORD dwPID, bool onboot)
{
	std::string name;
	std::string shop_name(LC_TEXT("SHOP_NAME"));
	DWORD time = 0;
	long map_index = 0, x = 0, y = 0;

	auto pkMsg = DBManager::instance().DirectQuery("SELECT player_shop.name, player.name as player_name, player_shop.map_index, player_shop.x, player_shop.y, player_shop.date_close FROM player_shop left join player on player.id=player_shop.player_id WHERE player_shop.player_id='%u'", dwPID);
	if (!pkMsg || !pkMsg->Get())
		return false;

	if (pkMsg->Get()->uiNumRows > 0)
	{
		MYSQL_ROW row = NULL;
		while ((row = mysql_fetch_row(pkMsg->Get()->pSQLResult)) != NULL)
		{
			name =											row[0];
			boost::replace_all(shop_name, "#PLAYER_NAME#",	row[1]);
			str_to_number(map_index,						row[2]);
			str_to_number(x,								row[3]);
			str_to_number(y,								row[4]);
			str_to_number(time,								row[5]);
		}
	}
	if (map_index <= 0 || x <= 0 || y <= 0)
	{
		sys_err("location is null %u", dwPID);
		return false;
	}

	LPCHARACTER ch = CHARACTER_MANAGER::Instance().SpawnMob(30000, map_index, x, y, 0, true, 0, false);
	if (ch)
	{
		ch->SetName(shop_name.c_str());
		ch->SetPrivShopOwner(dwPID);
		ch->SetShopTime(time);
		ch->Show(map_index, x, y);
		ch->OpenShop(dwPID, name.c_str(), onboot);
		return true;
	}
	return false;
}

LPSHOP CShopManager::CreateNPCShop(LPCHARACTER ch, std::vector<TShopItemTable *> map_shop)
{
	if (FindPCShop(ch->GetPrivShopOwner()))
		return NULL;

	LPSHOP pkShop = M2_NEW CShop;
	pkShop->SetPCShop(ch);
	pkShop->SetPrivShopItems(map_shop);

	m_map_pkShopByPC.insert(TShopMap::value_type(ch->GetPrivShopOwner(), pkShop));
	return pkShop;
}
#endif

void CShopManager::StopShopping(LPCHARACTER ch) const
{
	LPSHOP shop;

	if (!(shop = ch->GetShop()))
		return;

	//PREVENT_ITEM_COPY;
	ch->SetMyShopTime();
	//END_PREVENT_ITEM_COPY

	shop->RemoveGuest(ch);
	sys_log(0, "SHOP: END: %s", ch->GetName());
}

void CShopManager::Buy(LPCHARACTER ch, BYTE pos) const
{
#ifdef ENABLE_NEWSTUFF
	if (g_BuySellTimeLimitValue && !PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), ePulse::BoxOpening, std::chrono::milliseconds(g_BuySellTimeLimitValue)))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("아직 골드를 버릴 수 없습니다."));
		return;
	}
#endif
	if (!ch->GetShop())
		return;

	if (!ch->GetShopOwner())
		return;

	if (DISTANCE_APPROX(ch->GetX() - ch->GetShopOwner()->GetX(), ch->GetY() - ch->GetShopOwner()->GetY()) > 2000)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("상점과의 거리가 너무 멀어 물건을 살 수 없습니다."));
		return;
	}

	CShop* pkShop = ch->GetShop();

	//PREVENT_ITEM_COPY
	ch->SetMyShopTime();
	//END_PREVENT_ITEM_COPY

	const int ret = pkShop->Buy(ch, pos);

	if (SHOP_SUBHEADER_GC_OK != ret)
	{
		TPacketGCShop pack;

		pack.header	= HEADER_GC_SHOP;
		pack.subheader	= ret;
		pack.size	= sizeof(TPacketGCShop);

		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}
}

void CShopManager::Sell(LPCHARACTER ch, BYTE bCell, BYTE bCount) const
{
#ifdef ENABLE_NEWSTUFF
	if (g_BuySellTimeLimitValue && !PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), ePulse::BoxOpening, std::chrono::milliseconds(g_BuySellTimeLimitValue)))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("아직 골드를 버릴 수 없습니다."));
		return;
	}
#endif
	if (!ch->GetShop())
		return;

	if (!ch->GetShopOwner())
		return;

	if (!ch->CanHandleItem())
		return;

	if (ch->GetShop()->IsPCShop())
		return;

	if (DISTANCE_APPROX(ch->GetX()-ch->GetShopOwner()->GetX(), ch->GetY()-ch->GetShopOwner()->GetY())>2000)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("상점과의 거리가 너무 멀어 물건을 팔 수 없습니다."));
		return;
	}

	const LPITEM item = ch->GetInventoryItem(bCell);

	if (!item)
		return;

	if (item->IsEquipped() == true)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("착용 중인 아이템은 판매할 수 없습니다."));
		return;
	}

	if (true == item->isLocked())
	{
		return;
	}

#ifdef ENABLE_ITEM_SHOP_SYSTEM
	if (item->IsItemShopEmBound())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketemitemkisitli"));
		return;
	}
#endif

	if (IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_SELL))
		return;

	if (bCount == 0 || bCount > item->GetCount())
		bCount = item->GetCount();

	DWORD dwPrice = item->GetShopBuyPrice();

	if (IS_SET(item->GetFlag(), ITEM_FLAG_COUNT_PER_1GOLD))
	{
		if (dwPrice == 0)
			dwPrice = bCount;
		else
			dwPrice = bCount / dwPrice;
	}
	else
		dwPrice *= bCount;

#ifndef ENABLE_NO_SELL_PRICE_DIVIDED_BY_5
	if ((item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR) && item->GetLevelLimit() >= 40)
	{
		if (item->GetType() == ITEM_WEAPON && item->GetLevelLimit() >= 60)
			dwPrice /= 15;
		else
			dwPrice /= 10;
	}
	else
		dwPrice /= 5;
#endif

	DWORD dwTax = 0;
	const int iVal = 3;

	{
		dwTax = dwPrice * iVal/100;
		dwPrice -= dwTax;
	}

	if (test_server)
		sys_log(0, "Sell Item price id %d %s itemid %d", ch->GetPlayerID(), ch->GetName(), item->GetID());

	const int64_t nTotalMoney = static_cast<int64_t>(ch->GetGold()) + static_cast<int64_t>(dwPrice);

	if (GOLD_MAX <= nTotalMoney)
	{
		sys_err("[OVERFLOW_GOLD] id %u name %s gold %u", ch->GetPlayerID(), ch->GetName(), ch->GetGold());
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("20억냥이 초과하여 물품을 팔수 없습니다."));
		return;
	}

	sys_log(0, "SHOP: SELL: %s item name: %s(x%d):%u price: %u", ch->GetName(), item->GetName(), bCount, item->GetID(), dwPrice);

	if (iVal > 0)
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("판매금액의 %d %% 가 세금으로 나가게됩니다"), iVal);

	DBManager::instance().SendMoneyLog(MONEY_LOG_SHOP, item->GetVnum(), dwPrice);

	if (bCount == item->GetCount())
		ITEM_MANAGER::instance().RemoveItem(item, "SELL");
	else
		item->SetCount(item->GetCount() - bCount);

	CMonarch::instance().SendtoDBAddMoney(dwTax, ch->GetEmpire(), ch);
	ch->PointChange(POINT_GOLD, dwPrice, false);
	if (test_server)
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Item sold for %d yang"), dwPrice);
}

bool CompareShopItemName(const SShopItemTable& lhs, const SShopItemTable& rhs)
{
	const TItemTable* lItem = ITEM_MANAGER::instance().GetTable(lhs.vnum);
	const TItemTable* rItem = ITEM_MANAGER::instance().GetTable(rhs.vnum);
	if (lItem && rItem)
		return strcmp(lItem->szLocaleName, rItem->szLocaleName) < 0;
	else
		return true;
}

bool ConvertToShopItemTable(IN CGroupNode* pNode, OUT TShopTableEx& shopTable)
{
	if (!pNode->GetValue("vnum", 0, shopTable.dwVnum))
	{
		sys_err("Group %s does not have vnum.", pNode->GetNodeName().c_str());
		return false;
	}

	if (!pNode->GetValue("name", 0, shopTable.name))
	{
		sys_err("Group %s does not have name.", pNode->GetNodeName().c_str());
		return false;
	}

	if (shopTable.name.length() >= SHOP_TAB_NAME_MAX)
	{
		sys_err("Shop name length must be less than %d. Error in Group %s, name %s", SHOP_TAB_NAME_MAX, pNode->GetNodeName().c_str(), shopTable.name.c_str());
		return false;
	}

	std::string stCoinType;
	if (!pNode->GetValue("cointype", 0, stCoinType))
	{
		stCoinType = "Gold";
	}

	if (strcasecmp(stCoinType.c_str(), "Gold") == 0)
	{
		shopTable.coinType = SHOP_COIN_TYPE_GOLD;
	}
	else if (strcasecmp(stCoinType.c_str(), "SecondaryCoin") == 0)
	{
		shopTable.coinType = SHOP_COIN_TYPE_SECONDARY_COIN;
	}
	else
	{
		sys_err("Group %s has undefine cointype(%s).", pNode->GetNodeName().c_str(), stCoinType.c_str());
		return false;
	}

	const CGroupNode* pItemGroup = pNode->GetChildNode("items");
	if (!pItemGroup)
	{
		sys_err("Group %s does not have 'group items'.", pNode->GetNodeName().c_str());
		return false;
	}

	const int itemGroupSize = pItemGroup->GetRowCount();
	std::vector <TShopItemTable> shopItems(itemGroupSize);
	if (itemGroupSize >= SHOP_HOST_ITEM_MAX_NUM)
	{
		sys_err("count(%d) of rows of group items of group %s must be smaller than %d", itemGroupSize, pNode->GetNodeName().c_str(), SHOP_HOST_ITEM_MAX_NUM);
		return false;
	}

	for (int i = 0; i < itemGroupSize; i++)
	{
		if (!pItemGroup->GetValue(i, "vnum", shopItems[i].vnum))
		{
			sys_err("row(%d) of group items of group %s does not have vnum column", i, pNode->GetNodeName().c_str());
			return false;
		}

		if (!pItemGroup->GetValue(i, "count", shopItems[i].count))
		{
			sys_err("row(%d) of group items of group %s does not have count column", i, pNode->GetNodeName().c_str());
			return false;
		}
		if (!pItemGroup->GetValue(i, "price", shopItems[i].price))
		{
			sys_err("row(%d) of group items of group %s does not have price column", i, pNode->GetNodeName().c_str());
			return false;
		}
		#ifdef ENABLE_CHEQUE_SYSTEM
		pItemGroup->GetValue(i, "won", shopItems[i].cheque);
		#endif
#ifdef ENABLE_MULTISHOP
		pItemGroup->GetValue(i, "multishop_price_vnum", shopItems[i].wPriceVnum);
		pItemGroup->GetValue(i, "multishop_price_count", shopItems[i].wPrice);
		pItemGroup->GetValue(i, "gem_price", shopItems[i].gem_price);
#endif
	}
	std::string stSort;
	if (!pNode->GetValue("sort", 0, stSort))
	{
		stSort = "None";
	}

	if (strcasecmp(stSort.c_str(), "Asc") == 0)
	{
		std::sort(shopItems.begin(), shopItems.end(), CompareShopItemName);
	}
	else if(strcasecmp(stSort.c_str(), "Desc") == 0)
	{
		std::sort(shopItems.rbegin(), shopItems.rend(), CompareShopItemName);
	}

	const auto grid = CGrid(5, 9);
	int iPos;

	msl::refill(shopTable.items);

	for (size_t i = 0; i < shopItems.size(); i++)
	{
		const TItemTable * item_table = ITEM_MANAGER::instance().GetTable(shopItems[i].vnum);
		if (!item_table)
		{
			sys_err("vnum(%d) of group items of group %s does not exist", shopItems[i].vnum, pNode->GetNodeName().c_str());
			return false;
		}

		iPos = grid.FindBlank(1, item_table->bSize);

		grid.Put(iPos, 1, item_table->bSize);
		shopTable.items[iPos] = shopItems[i];
	}

	shopTable.byItemCount = shopItems.size();
	return true;
}

bool CShopManager::ReadShopTableEx(const char* stFileName)
{
	FILE* fp = fopen(stFileName, "rb");
	if (nullptr == fp)
		return true;
	fclose(fp);

	CGroupTextParseTreeLoader loader;
	if (!loader.Load(stFileName))
	{
		sys_err("%s Load fail.", stFileName);
		return false;
	}

	const CGroupNode* pShopNPCGroup = loader.GetGroup("shopnpc");
	if (nullptr == pShopNPCGroup)
	{
		sys_err("Group ShopNPC is not exist.");
		return false;
	}

	typedef std::multimap <DWORD, TShopTableEx> TMapNPCshop;
	TMapNPCshop map_npcShop;
	for (int i = 0; i < pShopNPCGroup->GetRowCount(); i++)
	{
		DWORD npcVnum;
		std::string shopName;
		if (!pShopNPCGroup->GetValue(i, "npc", npcVnum) || !pShopNPCGroup->GetValue(i, "group", shopName))
		{
			sys_err("Invalid row(%d). Group ShopNPC rows must have 'npc', 'group' columns", i);
			return false;
		}
		std::transform(shopName.begin(), shopName.end(), shopName.begin(), (int(*)(int))std::tolower);
		CGroupNode* pShopGroup = loader.GetGroup(shopName.c_str());
		if (!pShopGroup)
		{
			sys_err("Group %s is not exist.", shopName.c_str());
			return false;
		}
		TShopTableEx table;
		if (!ConvertToShopItemTable(pShopGroup, table))
		{
			sys_err("Cannot read Group %s.", shopName.c_str());
			return false;
		}
		if (m_map_pkShopByNPCVnum.contains(npcVnum))
		{
			sys_err("%d cannot have both original shop and extended shop", npcVnum);
			return false;
		}

		map_npcShop.emplace(npcVnum, table);
	}

	for (auto it = map_npcShop.begin(); it != map_npcShop.end(); ++it)
	{
		DWORD npcVnum = it->first;
		TShopTableEx& table = it->second;
		if (m_map_pkShop.contains(table.dwVnum))
		{
			sys_err("Shop vnum(%d) already exists", table.dwVnum);
			return false;
		}
		auto shop_it = m_map_pkShopByNPCVnum.find(npcVnum);

		LPSHOPEX pkShopEx = nullptr;
		if (m_map_pkShopByNPCVnum.end() == shop_it)
		{
			pkShopEx = M2_NEW CShopEx;
			pkShopEx->Create(0, npcVnum);
			m_map_pkShopByNPCVnum.emplace(npcVnum, pkShopEx);
		}
		else
		{
			pkShopEx = dynamic_cast <CShopEx*> (shop_it->second);
			if (nullptr == pkShopEx)
			{
				sys_err("WTF!!! It can't be happend. NPC(%d) Shop is not extended version.", shop_it->first);
				return false;
			}
		}

		if (pkShopEx->GetTabCount() >= SHOP_TAB_COUNT_MAX)
		{
			sys_err("ShopEx cannot have tab more than %d", SHOP_TAB_COUNT_MAX);
			return false;
		}

		if (pkShopEx->GetVnum() != 0 && m_map_pkShop.contains(pkShopEx->GetVnum()))
		{
			sys_err("Shop vnum(%d) already exist.", pkShopEx->GetVnum());
			return false;
		}
		m_map_pkShop.emplace(pkShopEx->GetVnum(), pkShopEx);
		pkShopEx->AddShopTable(table);
	}

	return true;
}

#ifdef OFFLINE_SHOP
// ===========================================================================
// Pazar Arama (ShopSearch)
// Kaynak: mt2009 ikarus CShopManager::PrepareShopSearchFilters /
//         SearchItemsByCategory / RecvShopSearchItemClientPacket
// new_project'in standart CShop (m_map_pkShopByPC) sistemine uyarlanmistir.
// ===========================================================================
namespace
{
	// Pazar arama icin maksimum mesafe (kaynaktaki 7500 ile ayni).
	// Tum haritadaki dukkanlari isaretlemek isterseniz bu degeri buyutun.
	const int SHOP_SEARCH_MAX_DISTANCE = 7500;
	const size_t SHOP_SEARCH_MAX_RESULTS = 400;
}

void CShopManager::PrepareShopSearchFilters()
{
	m_shopSearchFilters.clear();

	// SHOP_SEARCH_CATEGORY_BOOKS
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WARRIOR_0] = {
		{50300, 1}, {50300, 2}, {50300, 3}, {50300, 4}, {50300, 5}, {50300, 6},
		{50401, 0}, {50402, 0}, {50403, 0}, {50404, 0}, {50405, 0}, {50406, 0},
		{70037, 1}, {70037, 2}, {70037, 3}, {70037, 4}, {70037, 5}, {70037, 6},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WARRIOR_1] = {
		{50300, 16}, {50300, 17}, {50300, 18}, {50300, 19}, {50300, 20}, {50300, 21},
		{50416, 0}, {50417, 0}, {50418, 0}, {50419, 0}, {50420, 0}, {50421, 0},
		{70037, 16}, {70037, 17}, {70037, 18}, {70037, 19}, {70037, 20}, {70037, 21},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ASSASSIN_0] = {
		{50300, 31}, {50300, 32}, {50300, 33}, {50300, 34}, {50300, 35}, {50300, 36},
		{50431, 0}, {50432, 0}, {50433, 0}, {50434, 0}, {50435, 0}, {50436, 0},
		{70037, 31}, {70037, 32}, {70037, 33}, {70037, 34}, {70037, 35}, {70037, 36},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ASSASSIN_1] = {
		{50300, 46}, {50300, 47}, {50300, 48}, {50300, 49}, {50300, 50}, {50300, 51},
		{50446, 0}, {50447, 0}, {50448, 0}, {50449, 0}, {50450, 0}, {50451, 0},
		{70037, 46}, {70037, 47}, {70037, 48}, {70037, 49}, {70037, 50}, {70037, 51},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SURA_0] = {
		{50300, 61}, {50300, 62}, {50300, 63}, {50300, 64}, {50300, 65}, {50300, 66},
		{50461, 0}, {50462, 0}, {50463, 0}, {50464, 0}, {50465, 0}, {50466, 0},
		{70037, 61}, {70037, 62}, {70037, 63}, {70037, 64}, {70037, 65}, {70037, 66},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SURA_1] = {
		{50300, 76}, {50300, 77}, {50300, 78}, {50300, 79}, {50300, 80}, {50300, 81},
		{50476, 0}, {50477, 0}, {50478, 0}, {50479, 0}, {50480, 0}, {50481, 0},
		{70037, 76}, {70037, 77}, {70037, 78}, {70037, 79}, {70037, 80}, {70037, 81},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SHAMAN_0] = {
		{50300, 91}, {50300, 92}, {50300, 93}, {50300, 94}, {50300, 95}, {50300, 96},
		{50491, 0}, {50492, 0}, {50493, 0}, {50494, 0}, {50495, 0}, {50496, 0},
		{70037, 91}, {70037, 92}, {70037, 93}, {70037, 94}, {70037, 95}, {70037, 96},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SHAMAN_1] = {
		{50300, 106}, {50300, 107}, {50300, 108}, {50300, 109}, {50300, 110}, {50300, 111},
		{50506, 0}, {50507, 0}, {50508, 0}, {50509, 0}, {50510, 0}, {50511, 0},
		{70037, 106}, {70037, 107}, {70037, 108}, {70037, 109}, {70037, 110}, {70037, 111},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_BOOKS * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_PASSIVE_SKILL] = {
		{50513, 0}, {50600, 0}, {50301, 0}, {50302, 0}, {50303, 0}, {50304, 0}, {50305, 0}, {50306, 0}, {50311, 0}, {50312, 0}, {50313, 0}, {50314, 0}, {50315, 0}, {50316, 0},
	};

	// SHOP_SEARCH_CATEGORY_REFINE
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_M1] = {
		{30003, 0}, {30004, 0}, {30010, 0}, {30023, 0}, {30027, 0}, {30028, 0}, {30037, 0}, {30038, 0}, {30053, 0}, {30069, 0}, {30070, 0}, {30071, 0}, {30072, 0}, {30346, 0}, {30347, 0}, {30353, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_OATH] = {
		{30011, 0}, {30017, 0}, {30018, 0}, {30031, 0}, {30034, 0}, {30035, 0}, {30073, 0}, {30356, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_M2] = {
		{30005, 0}, {30021, 0}, {30030, 0}, {30032, 0}, {30033, 0}, {30041, 0}, {30052, 0}, {30074, 0}, {30075, 0}, {30092, 0}, {30357, 0}, {30358, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_ORC] = {
		{30007, 0}, {30076, 0}, {30352, 0}, {30006, 0}, {30077, 0}, {30008, 0}, {30078, 0}, {30051, 0}, {30079, 0}, {30047, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_DESERT1] = {
		{30022, 0}, {30025, 0}, {30045, 0}, {30046, 0}, {30081, 0}, {30055, 0}, {30056, 0}, {30057, 0}, {30058, 0}, {30059, 0}, {30067, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_DESERT2] = {
		{30350, 0}, {30351, 0}, {30359, 0}, {30082, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_SNOW] = {
		{30009, 0}, {30014, 0}, {30039, 0}, {30048, 0}, {30049, 0}, {30050, 0}, {30083, 0}, {30085, 0}, {30088, 0}, {30089, 0}, {30090, 0}, {30348, 0}, {30355, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_HWANG] = {
		{30040, 0}, {30060, 0}, {30061, 0}, {30080, 0}, {30344, 0}, {30345, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_END] = {
		{30019, 0}, {30042, 0}, {30091, 0}, {30367, 0}, {30354, 0}, {30349, 0}, {30015, 0}, {30087, 0}, {30016, 0}, {30086, 0}, {30343, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_SPECIAL] = {
		{30371, 0}, {30372, 0}, {30373, 0}, {30374, 0}, {30375, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_REFINE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_REFINE_PEARL] = {
		{27992, 0}, {27993, 0}, {27994, 0},
	};

	// SHOP_SEARCH_CATEGORY_HERBALISM
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_PRIMARY] = {
		{50721, 0}, {50722, 0}, {50723, 0}, {50724, 0}, {50725, 0}, {50726, 0}, {50727, 0}, {50728, 0}, {50729, 0}, {50730, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_SPECIAL] = {
		{50731, 0}, {50732, 0}, {50733, 0}, {50734, 0}, {50735, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_WATER_OFFENSIVE] = {
		{51720, 0}, {51725, 0}, {51740, 0}, {51745, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_WATER_DEFENSIVE] = {
		{51730, 0}, {51750, 0}, {51800, 0}, {51805, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_WATER_POWER] = {
		{27100, 0}, {27103, 0}, {51700, 0}, {51705, 0}, {51710, 0}, {51715, 0}, {51735, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_JUICE_OFFENSIVE] = {
		{51721, 0}, {51726, 0}, {51741, 0}, {51746, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_JUICE_DEFENSIVE] = {
		{51731, 0}, {51751, 0}, {51801, 0}, {51806, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_JUICE_POWER] = {
		{27101, 0}, {27104, 0}, {51701, 0}, {51706, 0}, {51711, 0}, {51716, 0}, {51736, 0}, {51755, 0}, {51760, 0}, {51775, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_DEW_OFFENSIVE] = {
		{51722, 0}, {51727, 0}, {51742, 0}, {51747, 0}, {51748, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_DEW_DEFENSIVE] = {
		{51732, 0}, {51752, 0}, {51753, 0}, {51802, 0}, {51807, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_DEW_POWER] = {
		{27102, 0}, {27105, 0}, {51702, 0}, {51707, 0}, {51712, 0}, {51717, 0}, {51737, 0}, {51756, 0}, {51761, 0}, {51776, 0}, {51765, 0}, {51766, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_OTHER_POTION] = {
		{51782, 0}, {51783, 0}, {51784, 0}, {51785, 0}, {71153, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_AUTOPOTION] = {
		{72723, 0}, {72724, 0}, {72725, 0}, {72727, 0}, {72728, 0}, {72729, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_RECIPE_OFFENSIVE] = {
		{50917, 0}, {50918, 0}, {50921, 0}, {50922, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_RECIPE_DEFENSIVE] = {
		{50919, 0}, {50942, 0}, {50943, 0}, {50923, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_RECIPE_POWER] = {
		{50911, 0}, {50912, 0}, {50913, 0}, {50914, 0}, {50915, 0}, {50916, 0}, {50920, 0}, {50924, 0}, {50925, 0}, {50926, 0}, {50927, 0}, {50929, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HERBALISM * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HERB_RECIPE_OTHER] = {
		{50930, 0}, {50932, 0}, {50933, 0}, {50934, 0}, {50935, 0},
	};

	// SHOP_SEARCH_CATEGORY_FISHING
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_FISHING * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_FISHING_FISH] = {
		{27802, 0}, {27803, 0}, {27804, 0}, {27805, 0}, {27806, 0}, {27807, 0}, {27808, 0}, {27809, 0}, {27810, 0}, {27811, 0}, {27812, 0}, {27813, 0}, {27814, 0}, {27815, 0}, {27816, 0}, {27818, 0}, {27819, 0}, {27820, 0}, {27821, 0}, {27822, 0}, {27823, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_FISHING * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_FISHING_FISH_COOK] = {
		{27866, 0}, {27868, 0}, {27869, 0}, {27870, 0}, {27871, 0}, {27872, 0}, {27873, 0}, {27875, 0}, {27879, 0}, {27880, 0}, {27881, 0}, {27882, 0}, {27883, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_FISHING * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_FISHING_FISH_OTHER] = {
		{70201, 0}, {70007, 0}, {70051, 0}, {70050, 0}, {70048, 0}, {70049, 0}, {70102, 0}, {27798, 0}, {27799, 0}, {27987, 0},
	};

	// SHOP_SEARCH_CATEGORY_MINING
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_MINING * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_MINING_ORE] = {
		{50601, 0}, {50603, 0}, {50604, 0}, {50605, 0}, {50606, 0}, {50607, 0}, {50608, 0}, {50609, 0}, {50610, 0}, {50611, 0}, {50612, 0}, {50613, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_MINING * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_MINING_MELT] = {
		{50621, 0}, {50623, 0}, {50624, 0}, {50625, 0}, {50626, 0}, {50627, 0}, {50628, 0}, {50629, 0}, {50630, 0}, {50631, 0}, {50632, 0}, {50633, 0},
	};

	// SHOP_SEARCH_CATEGORY_HORSE
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HORSE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HORSE_LEARN] = {
		{50050, 0}, {50060, 0}, {50061, 0}, {50062, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_HORSE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_HORSE_OTHER] = {
		{50054, 0}, {50055, 0}, {50056, 0}, {50083, 0}, {30378, 0},
	};

	// SHOP_SEARCH_CATEGORY_SPECIAL
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_REFINE] = {
		{25040, 0}, {25043, 0}, {25044, 0}, {25045, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_TOITEM] = {
		{25100, 0}, {30368, 0}, {30370, 0}, {71282, 0}, {71284, 0}, {71285, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_CHARACTER] = {
		{71201, 0}, {71294, 0}, {70102, 0}, {50513, 0}, {70014, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_OTHER] = {
		{70008, 0}, {72002, 0}, {72005, 0}, {72006, 0}, {70042, 0}, {70038, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_DRAGON_VOUCHER] = {
		{80017, 0}, {80014, 0}, {80018, 0}, {80015, 0}, {80016, 0}, {72199, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_QUEST] = {
		{50307, 0}, {50308, 0}, {50309, 0}, {50310, 0},
	};
	m_shopSearchFilters[SHOP_SEARCH_CATEGORY_SPECIAL * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SPECIAL_LOOTBOX] = {
		{50006, 0}, {50007, 0}, {50008, 0}, {50009, 0}, {50011, 0}, {50012, 0}, {50013, 0}, {50037, 0}, {50024, 0}, {50025, 0},
		{50070, 0}, {50071, 0}, {50073, 0}, {50076, 0}, {50077, 0}, {50078, 0}, {50079, 0}, {50081, 0}, {50082, 0}, {50097, 0},
		{50098, 0},
	};
}

bool CShopManager::SearchItemsByCategory(DWORD category, LPSHOP shop)
{
	if (!shop)
		return false;

	switch (category)
	{
		case SHOP_SEARCH_CATEGORY_POLYMORPH * SHOP_CATEGORY_MAX_SUB:
			return shop->HasItem(70104);

		// WEAPON
		case SHOP_SEARCH_CATEGORY_WEAPON * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_ONEHAND:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_SWORD, false);
		case SHOP_SEARCH_CATEGORY_WEAPON_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_ONEHAND:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_SWORD, true);

		case SHOP_SEARCH_CATEGORY_WEAPON * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_TWOHAND:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_TWO_HANDED, false);
		case SHOP_SEARCH_CATEGORY_WEAPON_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_TWOHAND:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_TWO_HANDED, true);

		case SHOP_SEARCH_CATEGORY_WEAPON * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_DAGGER:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_DAGGER, false);
		case SHOP_SEARCH_CATEGORY_WEAPON_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_DAGGER:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_DAGGER, true);

		case SHOP_SEARCH_CATEGORY_WEAPON * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_BOW:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_BOW, false);
		case SHOP_SEARCH_CATEGORY_WEAPON_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_BOW:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_BOW, true);

		case SHOP_SEARCH_CATEGORY_WEAPON * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_BELL:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_BELL, false);
		case SHOP_SEARCH_CATEGORY_WEAPON_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_BELL:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_BELL, true);

		case SHOP_SEARCH_CATEGORY_WEAPON * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_FAN:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_FAN, false);
		case SHOP_SEARCH_CATEGORY_WEAPON_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_WEAPON_FAN:
			return shop->HasItemType(ITEM_WEAPON, WEAPON_FAN, true);

		// ARMOR
		case SHOP_SEARCH_CATEGORY_ARMOR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ARMOR_BODY:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_BODY, false);
		case SHOP_SEARCH_CATEGORY_ARMOR_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ARMOR_BODY:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_BODY, true);

		case SHOP_SEARCH_CATEGORY_ARMOR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ARMOR_SHIELD:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_SHIELD, false);
		case SHOP_SEARCH_CATEGORY_ARMOR_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ARMOR_SHIELD:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_SHIELD, true);

		case SHOP_SEARCH_CATEGORY_ARMOR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ARMOR_HEAD:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_HEAD, false);
		case SHOP_SEARCH_CATEGORY_ARMOR_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_ARMOR_HEAD:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_HEAD, true);

		// JEWELRY (ITEM_ARMOR alt tipleri)
		case SHOP_SEARCH_CATEGORY_JEWELRY * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_EAR:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_EAR, false);
		case SHOP_SEARCH_CATEGORY_JEWELRY_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_EAR:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_EAR, true);

		case SHOP_SEARCH_CATEGORY_JEWELRY * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_NECK:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_NECK, false);
		case SHOP_SEARCH_CATEGORY_JEWELRY_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_NECK:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_NECK, true);

		case SHOP_SEARCH_CATEGORY_JEWELRY * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_WRIST:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_WRIST, false);
		case SHOP_SEARCH_CATEGORY_JEWELRY_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_WRIST:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_WRIST, true);

		case SHOP_SEARCH_CATEGORY_JEWELRY * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_BOOTS:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_FOOTS, false);
		case SHOP_SEARCH_CATEGORY_JEWELRY_ATTR * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_JEWELRY_BOOTS:
			return shop->HasItemType(ITEM_ARMOR, ARMOR_FOOTS, true);

		// SOUL STONES
		case SHOP_SEARCH_CATEGORY_SOULSTONE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SOULSTONE_0:
			return shop->HasSoulStoneSocket(0);
		case SHOP_SEARCH_CATEGORY_SOULSTONE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SOULSTONE_1:
			return shop->HasSoulStoneSocket(1);
		case SHOP_SEARCH_CATEGORY_SOULSTONE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SOULSTONE_2:
			return shop->HasSoulStoneSocket(2);
		case SHOP_SEARCH_CATEGORY_SOULSTONE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SOULSTONE_3:
			return shop->HasSoulStoneSocket(3);
		case SHOP_SEARCH_CATEGORY_SOULSTONE * SHOP_CATEGORY_MAX_SUB + SHOP_SEARCH_SUB_SOULSTONE_4:
			return shop->HasSoulStoneSocket(4);

		default:
		{
			auto it = m_shopSearchFilters.find(category);
			if (it != m_shopSearchFilters.end())
			{
				for (const auto & filter : it->second)
				{
					if (shop->HasItem(filter.itemVnum, filter.socket0))
						return true;
				}
			}
		}
	}
	return false;
}

void CShopManager::SearchShopItem(LPCHARACTER ch, DWORD searchIndex, int socket0)
{
	if (!ch || !ch->GetDesc())
		return;

	// Akis korumasi: kisa surede tekrar tekrar arama yapilmasini engelle
	if (!PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), ePulse::ShopSearch, std::chrono::milliseconds(3000)))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Lutfen tekrar aramadan once biraz bekleyin.");
		return;
	}

	if (searchIndex >= (DWORD)(SHOP_SEARCH_CATEGORY_MAX * SHOP_CATEGORY_MAX_SUB))
		return;

	std::vector<TShopSearchResultElement> foundShops;

	for (auto & it : m_map_pkShopByPC)
	{
		LPSHOP shop = it.second;
		if (!shop)
			continue;

		LPCHARACTER owner = shop->GetOwner();
		if (!owner)
			continue;

		// Ayni harita
		if (owner->GetMapIndex() != ch->GetMapIndex())
			continue;

		// Kendi dukkanini eleme (online sahis dukkani veya offline dukkan)
		const DWORD ownerPID = owner->IsPrivShop() ? owner->GetPrivShopOwner() : owner->GetPlayerID();
		if (ownerPID != 0 && ownerPID == ch->GetPlayerID())
			continue;

		// Mesafe siniri (kaynaktaki 7500 ile ayni; istege gore buyutulebilir)
		if (DISTANCE_APPROX(ch->GetX() - owner->GetX(), ch->GetY() - owner->GetY()) > SHOP_SEARCH_MAX_DISTANCE)
			continue;

		if (!SearchItemsByCategory(searchIndex, shop))
			continue;

		TShopSearchResultElement found;
		found.shopVid = owner->GetVID();
		found.x = owner->GetX();
		found.y = owner->GetY();
		foundShops.push_back(found);

		if (foundShops.size() >= SHOP_SEARCH_MAX_RESULTS)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Arama durduruldu. %d'den fazla dukkan bulundu.", (int)SHOP_SEARCH_MAX_RESULTS);
			break;
		}
	}

	ch->ChatPacket(CHAT_TYPE_INFO, "Arama tamamlandi. %d dukkan bulundu.", (int)foundShops.size());

	if (!foundShops.empty())
	{
		TPacketGCShopSearch pack;
		pack.header = HEADER_GC_SHOP_SEARCH;
		pack.count = (WORD)foundShops.size();
		pack.size = (WORD)(sizeof(pack) + sizeof(TShopSearchResultElement) * foundShops.size());

		TEMP_BUFFER buff;
		buff.write(&pack, sizeof(pack));
		for (const auto & e : foundShops)
			buff.write(&e, sizeof(e));

		ch->GetDesc()->Packet(buff.read_peek(), buff.size());
	}
}
#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
