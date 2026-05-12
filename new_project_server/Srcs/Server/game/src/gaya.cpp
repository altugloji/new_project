#include "stdafx.h"

#ifdef __GEM_SYSTEM__
#include "char.h"
#include "gaya.h"
#include "db.h"
#include "packet.h"
#include "desc.h"
#include "utils.h"
#include "questmanager.h"
#include "buffer_manager.h"
#include "desc_manager.h"
#include "log.h"

ACMD(do_gem)
{
	std::vector<std::string> vecArgs;
	split_argument_ex(argument, vecArgs);
	if (vecArgs.size() < 2) { return; }
	else if (vecArgs[1] == "time")
	{
		if (ch->GetProtectTime("last_gem_time") > time(0))
			return;
		ch->SetProtectTime("last_gem_time", time(0) + 5);

		ch->SendGemData();
	}
	else if (vecArgs[1] == "close")
	{
		if (ch->GetGemShop())
		{
			ch->SetGemShop(false);
		}
	}
	else if (vecArgs[1] == "close_convert")
	{
		if (ch->GetGemConvertShop())
		{
			ch->SetGemConvertShop(false);
		}
	}
	else if (vecArgs[1] == "slot")
	{
		ch->OpenGemSlot();
	}
	else if (vecArgs[1] == "refresh")
	{
		CGayaManager::Instance().Reset(ch);
	}
	else if (vecArgs[1] == "buy")
	{
		if (vecArgs.size() < 3) { return; }
		BYTE bPos;
		if (!str_to_number(bPos, vecArgs[2].c_str()))
			return;
		ch->BuyGemItem(bPos);
	}
	else if (vecArgs[1] == "convert")
	{
		if (vecArgs.size() < 4) { return; }
		BYTE bPos;
		if (!str_to_number(bPos, vecArgs[2].c_str()))
			return;
		int iCount;
		if (!str_to_number(iCount, vecArgs[3].c_str()))
			return;
		CGayaManager::Instance().Convert(ch, bPos, iCount);

		ch->BuyGemItem(bPos);
	}
	else if (vecArgs[1] == "reload" && ch->IsGM())
	{
		CGayaManager::Instance().Load(false);
	}
}

const TGemConvertItem* CGayaManager::GetConvertItem(BYTE bPos)
{
	for (const auto& item : m_vecConvertItems)
	{
		if (item.bPos == bPos)
			return &item;
	}
	return NULL;
}
void CGayaManager::Convert(LPCHARACTER ch, BYTE bPos, int iCount)
{
	if (iCount <= 0 || !ch->GetGemConvertShop())
		return;

	const TGemConvertItem* pItem = GetConvertItem(bPos);
	if (!pItem)
		return;

	const int llCurPoint = ch->GetGem();
	const int llGemPoint = static_cast<int>(iCount * pItem->dwPrice);
	if ((llCurPoint + llGemPoint) > GEM_MAX)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "You can't convert because gem point already max.");
		return;
	}

	int iRequiredCount = iCount * pItem->dwCount;
	if (iRequiredCount > ch->CountSpecifyItem(pItem->dwVnum))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "You don't have enough item");
		return;
	}


	char szReason[256];
	snprintf(szReason, sizeof(szReason),
		"vnum: %u required_count: %d convert_count: %d "
		"price_per_convert: %u total_gem: %d "
		"current_gem: %d after_gem: %d pos: %u",
		pItem->dwVnum,
		iRequiredCount,
		iCount,
		pItem->dwPrice,
		llGemPoint,
		llCurPoint,
		llCurPoint + llGemPoint,
		bPos);
	LogManager::Instance().GemLog(ch->GetPlayerID(), ch->GetName(), "CONVERT", szReason);

	ch->RemoveSpecifyItem(pItem->dwVnum, iRequiredCount);
	ch->PointChange(POINT_GEM, llGemPoint);
	ch->ChatPacket(CHAT_TYPE_INFO, "Gem convert successfully.");
}

void CGayaManager::OpenConvertShop(LPCHARACTER ch)
{
	if (ch)
	{
		if (ch->IsHack() || !ch->CanHandleItem())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "You can't open convert window.");
			return;
		}
	}

	TPacketGCGem pack;
	pack.header = HEADER_GC_GEM;
	pack.sub_header = GEM_SUBHEADER_GC_CONVERT_LOAD;
	BYTE bItemCount = m_vecConvertItems.size();
	pack.size = sizeof(TPacketGCGem) + sizeof(BYTE) + (bItemCount * sizeof(TGemConvertItem));
	TEMP_BUFFER buf;
	buf.write(&pack, sizeof(TPacketGCGem));
	buf.write(&bItemCount, sizeof(BYTE));
	if (bItemCount > 0)
		buf.write(m_vecConvertItems.data(), bItemCount * sizeof(TGemConvertItem));

	LPDESC d = ch ? ch->GetDesc() : NULL;
	if (d)
	{
		ch->SetGemConvertShop(true);
		d->Packet(buf.read_peek(), buf.size());
	}
	else
	{
		const DESC_MANAGER::DESC_SET& c_ref_set = DESC_MANAGER::instance().GetClientSet();
		for (auto desc : c_ref_set)
		{
			LPCHARACTER ch = desc->GetCharacter();
			if (!ch || !ch->GetGemConvertShop())
				continue;
			desc->Packet(buf.read_peek(), buf.size());
		}
	}
}

void CGayaManager::Reset(LPCHARACTER ch)
{
	if (!ch->GetGemShop())
		return;

	if (ch->CountSpecifyItem(GEM_RESET_ITEM) < 1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "You don't have enought refresh gaya shop item.");
		return;
	}
	ch->RemoveSpecifyItem(GEM_RESET_ITEM, 1);
	ch->SetGemTime(0);
	ch->SendGemData();
	ch->ChatPacket(CHAT_TYPE_INFO, "Gem shop refresh succesfully.");
}

void CGayaManager::ResetPlayerShop(LPCHARACTER ch, std::vector<TGemItem>& vecItems)
{
	vecItems.clear();

	if (!m_vecItems.size())
		return;

	std::vector<int> vecSelectedIndexes;

	BYTE bPos = 0;
	while (true)
	{
		if (vecSelectedIndexes.size() >= m_vecItems.size())
			break;

		int iSelectedIndex = m_vecItems.size() == 1 ? 0 : number(0, m_vecItems.size() - 1);
		if (std::find(vecSelectedIndexes.begin(), vecSelectedIndexes.end(), iSelectedIndex) != vecSelectedIndexes.end())
			continue;

		const SGemShopItem& selected_item = m_vecItems[iSelectedIndex];

		if (number(1, 100) < selected_item.bLuck)
			continue;

		TGemItem item;
		item.bBuyed = false;
		item.bPos = bPos++;
		item.dwVnum = selected_item.dwVnum;
		item.dwCount = selected_item.dwCount;
		item.dwPrice = selected_item.dwPrice;
		
		vecItems.emplace_back(item);

		vecSelectedIndexes.emplace_back(iSelectedIndex);
		if (vecSelectedIndexes.size() >= GEM_SLOT_COUNT_MAX)
			break;
	}
}

bool CGayaManager::Load(bool is_p2p)
{
	m_vecItems.clear();
	m_vecConvertItems.clear();

	if (!is_p2p)
	{
		quest::CQuestManager::Instance().RequestSetEventFlag("gaya_reload", 0);
	}

	const std::unique_ptr<SQLMsg> pShopMsg(DBManager::Instance().DirectQuery("SELECT * FROM player.gaya_shop"));
	if (pShopMsg->Get()->uiNumRows != 0)
	{
		MYSQL_ROW row = NULL;
		SGemShopItem shopItem;
		while (NULL != (row = mysql_fetch_row(pShopMsg->Get()->pSQLResult)))
		{
			str_to_number(shopItem.dwVnum, row[0]);
			str_to_number(shopItem.dwCount, row[1]);
			str_to_number(shopItem.dwPrice, row[2]);
			str_to_number(shopItem.bLuck, row[3]);
			m_vecItems.emplace_back(shopItem);
		}
	}

	const std::unique_ptr<SQLMsg> pConvertMsg(DBManager::Instance().DirectQuery("SELECT * FROM player.gaya_convert_shop"));
	if (pConvertMsg->Get()->uiNumRows != 0)
	{
		MYSQL_ROW row = NULL;
		TGemConvertItem convertItem;
		BYTE bPos = 0;
		while (NULL != (row = mysql_fetch_row(pConvertMsg->Get()->pSQLResult)))
		{
			convertItem.bPos = bPos++;
			str_to_number(convertItem.dwVnum, row[0]);
			str_to_number(convertItem.dwCount, row[1]);
			str_to_number(convertItem.dwPrice, row[2]);
			m_vecConvertItems.emplace_back(convertItem);
		}
	}

	OpenConvertShop(NULL);

	sys_err("Gem shop: %u - convert shop: %u", m_vecItems.size(), m_vecConvertItems.size());
	return true;
}
#endif