#include "stdafx.h"
#include "../../common/service.h"
#ifdef ENABLE_ITEM_SHOP_SYSTEM
#include "char.h"
#include "utils.h"
#include "log.h"
#include "db.h"
#include "config.h"
#include "desc.h"
#include "desc_manager.h"
#include "buffer_manager.h"
#include "packet.h"
#include "desc_client.h"
#include "p2p.h"
#include "item.h"
#include "item_manager.h"
#include "item_shop.h"
#include "../../common/VnumHelper.h"

static bool IsItemShopEmPurchaseBlocked(DWORD dwVnum)
{
	switch (dwVnum)
	{
		case 80014:
		case 80015:
		case 80016:
		case 80017:
			return true;
		default:
			return false;
	}
}

const CItemShopManager::TItemShopTable* CItemShopManager::GetTable(DWORD id)
{
	TItemShopDataMap::iterator itor = m_ItemShopDataMap.find(id);

	if (itor == m_ItemShopDataMap.end())
		return NULL;

	return itor->second;
}

bool CItemShopManager::LoadItemShopTable()
{
	m_ItemShopDataMap.clear();
	auto pMsg = DBManager::instance().DirectQuery("SELECT * FROM player.item_shop_table");
	if (!pMsg || !pMsg->Get())
		return false;

	SQLResult * pRes = pMsg->Get();
	if (!pRes || pRes->uiAffectedRows <= 0)
	{
		sys_err("QUERY_ERROR: SELECT * FROM player.item_shop_table \n");
		return false;
	}

	if (pRes->uiNumRows)
	{
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(pRes->pSQLResult)))
		{
			DWORD	id, category, sub_category, vnum, count, coinsold, coins, socketzero, mark;
			DWORD	socket0, socket1, socket2, socket3, socket4, socket5;
			DWORD	type0, type1, type2, type3, type4, type5, type6;
			DWORD	value0, value1, value2, value3, value4, value5, value6;

			str_to_number(id, row[0]);
			str_to_number(category, row[1]);
			str_to_number(sub_category, row[2]);
			str_to_number(vnum, row[3]);
			str_to_number(coins, row[4]);
			str_to_number(coinsold, row[5]);
			str_to_number(count, row[6]);
			str_to_number(socketzero, row[7]);
			str_to_number(mark, row[8]);
			str_to_number(socket0, row[9]);
			str_to_number(socket1, row[10]);
			str_to_number(socket2, row[11]);
			str_to_number(socket3, row[12]);
			str_to_number(socket4, row[13]);
			str_to_number(socket5, row[14]);
			str_to_number(type0, row[15]);
			str_to_number(value0, row[16]);
			str_to_number(type1, row[17]);
			str_to_number(value1, row[18]);
			str_to_number(type2, row[19]);
			str_to_number(value2, row[20]);
			str_to_number(type3, row[21]);
			str_to_number(value3, row[22]);
			str_to_number(type4, row[23]);
			str_to_number(value4, row[24]);
			str_to_number(type5, row[25]);
			str_to_number(value5, row[26]);
			str_to_number(type6, row[27]);
			str_to_number(value6, row[28]);
			
			
			const TItemShopTable* p = GetTable(id);

			if (p)
			{
				sys_log(0, "Already Inserted List %d (ItemShop Table)", id);
				continue;
			}

			TItemShopTable* pItemShopData = new TItemShopTable;
			pItemShopData->category = category;
			pItemShopData->sub_category = sub_category;
			pItemShopData->id = id;
			pItemShopData->vnum = vnum;
			pItemShopData->count = count;
			pItemShopData->coinsold = coinsold;
			pItemShopData->coins = coins;
			pItemShopData->socketzero = socketzero;
			pItemShopData->mark = mark;
			pItemShopData->socket0 = socket0;
			pItemShopData->socket1 = socket1;
			pItemShopData->socket2 = socket2;
			pItemShopData->socket3 = socket3;
			pItemShopData->socket4 = socket4;
			pItemShopData->socket5 = socket5;
			pItemShopData->type0 = type0;
			pItemShopData->type1 = type1;
			pItemShopData->type2 = type2;
			pItemShopData->type3 = type3;
			pItemShopData->type4 = type4;
			pItemShopData->type5 = type5;
			pItemShopData->type6 = type6;
			pItemShopData->value0 = value0;
			pItemShopData->value1 = value1;
			pItemShopData->value2 = value2;
			pItemShopData->value3 = value3;
			pItemShopData->value4 = value4;
			pItemShopData->value5 = value5;
			pItemShopData->value6 = value6;
			m_ItemShopDataMap.insert(TItemShopDataMap::value_type(id, pItemShopData));
			sys_log(0, "ItemShop Insert ID:%d VNUM:%d COUNT:%d", id, vnum, count);
		}
	}
	return true;
}

void CItemShopManager::SendClientPacket(LPCHARACTER ch)
{
	if (NULL == ch)
		return;

	if (!ch || !ch->GetDesc())
		return;
	
	ch->ChatPacket(CHAT_TYPE_COMMAND, "ItemShopDataClear");

	for (auto itor=m_ItemShopDataMap.begin(); itor!=m_ItemShopDataMap.end(); ++itor)
	{
		TItemShopTable * pTable = itor->second;
		if (pTable)
		{
			
			TPacketItemShopData pack;
			pack.header = HEADER_GC_ITEM_SHOP;

			pack.id = pTable->id;
			pack.category = pTable->category;
			pack.sub_category = pTable->sub_category;
			pack.vnum = pTable->vnum;
			pack.count = pTable->count;
			pack.coinsold = pTable->coinsold;
			pack.coins = pTable->coins;
			pack.socketzero = pTable->socketzero;
			pack.mark = pTable->mark;
			pack.socket0 = pTable->socket0;
			pack.socket1 = pTable->socket1;
			pack.socket2 = pTable->socket2;
			pack.socket3 = pTable->socket3;
			pack.socket4 = pTable->socket4;
			pack.socket5 = pTable->socket5;
			pack.type0 = pTable->type0;
			pack.type1 = pTable->type1;
			pack.type2 = pTable->type2;
			pack.type3 = pTable->type3;
			pack.type4 = pTable->type4;
			pack.type5 = pTable->type5;
			pack.type6 = pTable->type6;
			pack.value0 = pTable->value0;
			pack.value1 = pTable->value1;
			pack.value2 = pTable->value2;
			pack.value3 = pTable->value3;
			pack.value4 = pTable->value4;
			pack.value5 = pTable->value5;
			pack.value6 = pTable->value6;

			ch->GetDesc()->Packet(&pack, sizeof(pack)); 
		}
	}
}

bool CItemShopManager::Buy(LPCHARACTER ch, DWORD id, DWORD count, BYTE bPayType)
{
	if (!ch)
		return false;
	if (count <= 0)
		return false;

	if (count > 200)
		count = 200;

	const TItemShopTable* c_pTable = GetTable(id);

	if (!c_pTable)
	{
		sys_err("%s has request buy unknown id(%d) item", ch->GetName(), id);
		return false;
	}

	DWORD dwCoins = c_pTable->coins;
	DWORD dwVnum = c_pTable->vnum;
	DWORD dwCount = c_pTable->count;
	DWORD dwSocketZero = c_pTable->socketzero;
	DWORD dwMark = c_pTable->mark;

	DWORD dwRealCount = dwCount * count;

	const bool bBlockEmPurchase = IsItemShopEmPurchaseBlocked(dwVnum);

	bool pricetypecoin = false;

	if (bBlockEmPurchase && bPayType == 1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketemilealinemez"));
		return false;
	}

	if (bPayType == 0)
	{
		if (dwCoins <= 0)
			return false;

		pricetypecoin = true;

		if (ch->GetDragonCoin() < (dwCoins * count))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketyeterliepyok"));
			return false;
		}
	}
	else if (bPayType == 1)
	{
		if (dwMark <= 0)
			return false;

		pricetypecoin = false;

		if (ch->GetDragonMark() < (dwMark * count))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketyeterliemyok"));
			return false;
		}
	}
	else
	{
		if (bBlockEmPurchase)
		{
			if (dwCoins <= 0)
			{
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketemilealinemez"));
				return false;
			}

			pricetypecoin = true;

			if (ch->GetDragonCoin() < (dwCoins * count))
			{
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketyeterliepyok"));
				return false;
			}
		}
		else
		{
			if (dwCoins >= dwMark)
				pricetypecoin = true;
			else
				pricetypecoin = false;

			if (dwCoins >= dwMark)
			{
				if (ch->GetDragonCoin() < (dwCoins * count))
				{
					ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketyeterliepyok"));
					return false;
				}
			}
			else
			{
				if (ch->GetDragonMark() < (dwMark * count))
				{
					ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketyeterliemyok"));
					return false;
				}
			}
		}
	}

	TItemTable * table = ITEM_MANAGER::instance().GetTable(dwVnum);
	if (!table)
		return false;

	LPITEM pkItem = ITEM_MANAGER::instance().CreateItem(dwVnum, dwRealCount, 0, true, -1);

	if (!pkItem)
		return false;

	int iEmptyPos;
	if (pkItem->IsDragonSoul())
		iEmptyPos = ch->GetEmptyDragonSoulInventory(pkItem);
	else
		iEmptyPos = ch->GetEmptyInventory(pkItem->GetSize());

	if (iEmptyPos < 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("nesnemarketenvanterdebosyer"));
		M2_DESTROY_ITEM(pkItem);
		return false;
	}

	if (pricetypecoin == true)
	{
		ch->SetDragonCoin(ch->GetDragonCoin() - (dwCoins * count));
	}
	else
	{
		ch->SetDragonMark(ch->GetDragonMark() - (dwMark * count));
	}

	if (table->bGainSocketPct)
		pkItem->AlterToSocketItem(table->bGainSocketPct);

	if (c_pTable->socket0 != 0)
	{
		pkItem->SetSocket(0, c_pTable->socket0);
	}
	if (c_pTable->socket1 != 0)
	{
		pkItem->SetSocket(1, c_pTable->socket1);
	}
	if (c_pTable->socket2 != 0)
	{
		pkItem->SetSocket(2, c_pTable->socket2);
	}
	if (c_pTable->socket3 != 0)
	{
		pkItem->SetSocket(3, c_pTable->socket3);
	}
	if (c_pTable->socket4 != 0)
	{
		pkItem->SetSocket(4, c_pTable->socket4);
	}
	if (c_pTable->socket5 != 0)
	{
		pkItem->SetSocket(5, c_pTable->socket5);
	}

	pkItem->SetForceAttribute(0, c_pTable->type0, c_pTable->value0);
	pkItem->SetForceAttribute(1, c_pTable->type1, c_pTable->value1);
	pkItem->SetForceAttribute(2, c_pTable->type2, c_pTable->value2);
	pkItem->SetForceAttribute(3, c_pTable->type3, c_pTable->value3);
	pkItem->SetForceAttribute(4, c_pTable->type4, c_pTable->value4);

	pkItem->SetForceAttribute(5, c_pTable->type5, c_pTable->value5);

	const bool bApplyEmBind = (bPayType == 1) || (bPayType != 0 && !pricetypecoin);

	if (bApplyEmBind)
		pkItem->ApplyItemShopEmBind();
	else
		pkItem->SetForceAttribute(6, c_pTable->type6, c_pTable->value6);

	if (pkItem->IsRealTimeItem())
		pkItem->SetSocket(0, get_global_time() + dwSocketZero);
	else
	{
		if (pkItem->GetType() != ITEM_BLEND && c_pTable->socket0 == 0)
			pkItem->SetSocket(0, dwSocketZero);
	}

	if (pkItem->IsDragonSoul())
		pkItem->AddToCharacter(ch, TItemPos(DRAGON_SOUL_INVENTORY, iEmptyPos));
	else
		pkItem->AddToCharacter(ch, TItemPos(INVENTORY, iEmptyPos));

	ITEM_MANAGER::instance().FlushDelayedSave(pkItem);
	
	DBManager::instance().DirectQuery(
		"INSERT INTO log.nesne_market (id, alan, pid, account_id, item_isim, item_kod, count, tarih)"
		"VALUES(%u,'%s',%u,%u,'%s',%d,%d,NOW())", pkItem->GetID(), ch->GetName(), ch->GetPlayerID(), ch->GetAID(), table->szLocaleName, pkItem->GetVnum(), dwRealCount);

	return true;
}

void CItemShopManager::Destroy()
{
	for (TItemShopDataMap::iterator itor = m_ItemShopDataMap.begin(); itor != m_ItemShopDataMap.end(); ++itor)
	{
		delete itor->second;
	}
	m_ItemShopDataMap.clear();
}

CItemShopManager::CItemShopManager()
{
}

CItemShopManager::~CItemShopManager()
{
	Destroy();
}
#endif