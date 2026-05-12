#include "stdafx.h"

#ifdef __GEM_SYSTEM__
#include "char.h"
#include "gaya.h"
#include "utils.h"
#include "locale_service.h"
#include "buffer_manager.h"
#include "desc.h"
#include "log.h"

int CHARACTER::GetGemSlotCount()
{
	return GetQuestFlag("gem.open_slot");
}

void CHARACTER::SetGemSlotCount(int iVal)
{
	SetQuestFlag("gem.open_slot", iVal);
}

int CHARACTER::GetGemTime()
{
	return GetQuestFlag("gem.left_time");
}

void CHARACTER::SetGemTime(int iVal)
{
	SetQuestFlag("gem.left_time", iVal);
}

void CHARACTER::OpenGemSlot()
{
	LPDESC d = GetDesc();
	if (!d)
		return;

	if (!GetGemShop())
		return;

	if (CountSpecifyItem(GEM_OPEN_SLOT_ITEM) < 1)
	{
		ChatPacket(CHAT_TYPE_INFO, "You don't has enought open gem slot item!");
		return;
	}

	int iSlotCount = GetGemSlotCount();
	if (iSlotCount >= GEM_PREMUM_SLOT_COUNT)
		return;

	iSlotCount += 1;
	SetGemSlotCount(iSlotCount);
	RemoveSpecifyItem(GEM_OPEN_SLOT_ITEM, 1);

	TPacketGCGem pack;
	pack.header = HEADER_GC_GEM;
	pack.sub_header = GEM_SUBHEADER_GC_SLOT_COUNT;
	pack.size = sizeof(TPacketGCGem) + sizeof(int);
	d->BufferedPacket(&pack, sizeof(TPacketGCGem));
	d->Packet(&iSlotCount, sizeof(int));
}

void CHARACTER::SendGemData()
{
	if (!GetDesc())
		return;

	if (IsHack() || !CanHandleItem())
	{
		ChatPacket(CHAT_TYPE_INFO, "You can't open gem window.");
		return;
	}

	SetGemData(false);

	int iTime = GetGemTime() - time(0);

	if (iTime <= 0)
	{
		SetQuestFlag("gem.left_time", time(0) + GEM_REFRESH_TIME);
		CGayaManager::Instance().ResetPlayerShop(this, m_vecGemItems);
		SetGemData(true);
		SendGemData();
		return;
	}

	SetGemShop(true);

	TPacketGCGem pack;
	pack.header = HEADER_GC_GEM;
	pack.sub_header = GEM_SUBHEADER_GC_LOAD;
	
	BYTE bItemCount = m_vecGemItems.size();

	pack.size = sizeof(TPacketGCGem) + sizeof(int) + sizeof(int) + sizeof(BYTE) + (bItemCount * sizeof(TGemItem));

	int iSlotCount = GetGemSlotCount();

	TEMP_BUFFER buf;
	buf.write(&pack, sizeof(TPacketGCGem));
	buf.write(&iSlotCount, sizeof(int));
	buf.write(&iTime, sizeof(int));
	buf.write(&bItemCount, sizeof(BYTE));
	if (bItemCount > 0)
		buf.write(m_vecGemItems.data(), bItemCount * sizeof(TGemItem));
	GetDesc()->Packet(buf.read_peek(), buf.size());
}

bool CHARACTER::IsGemSlotOpened(BYTE bPos)
{
	if (bPos >= GEM_SLOT_COUNT)
	{
		if (GetGemSlotCount() < ((bPos - GEM_SLOT_COUNT) + 1))
			return false;
	}
	return true;
}

TGemItem* CHARACTER::GetGemItem(BYTE bPos)
{
	for (auto& item : m_vecGemItems)
	{
		if (item.bPos == bPos)
			return &item;
	}
	return NULL;
}
void CHARACTER::BuyGemItem(BYTE bPos)
{
	LPDESC d = GetDesc();
	if (!d)
		return;

	TGemItem* pItem = GetGemItem(bPos);
	if (!pItem || !IsGemSlotOpened(bPos))
		return;
	else if (pItem->bBuyed)
		return;
	
	int llCurGem = GetGem();

	if (pItem->dwPrice > llCurGem)
	{
		ChatPacket(CHAT_TYPE_INFO, "You don't have enough gem point.");
		return;
	}

	TPacketGCGem pack;
	pack.header = HEADER_GC_GEM;
	pack.sub_header = GEM_SUBHEADER_GC_BUYED_SLOT;
	pack.size = sizeof(TPacketGCGem) + sizeof(BYTE);
	d->BufferedPacket(&pack, sizeof(TPacketGCGem));
	d->Packet(&bPos, sizeof(BYTE));

	pItem->bBuyed = true;

	char szReason[256];
	snprintf(szReason, sizeof(szReason),
		"vnum: %u item_count: %u gem_price: %u "
		"current_gem: %d after_gem: %d pos: %u",
		pItem->dwVnum,
		pItem->dwCount,
		pItem->dwPrice,
		llCurGem,
		llCurGem - static_cast<int>(pItem->dwPrice),
		bPos);

	LogManager::Instance().GemLog(GetPlayerID(), GetName(), "SHOP", szReason);

	PointChange(POINT_GEM, -static_cast<int>(pItem->dwPrice));
	AutoGiveItem(pItem->dwVnum, pItem->dwCount);

	SetGemData(true);
}

void CHARACTER::SetGemData(bool bSave)
{
	char szBuf[256];
	snprintf(szBuf, sizeof(szBuf), "%s/gem/%u", LocaleService_GetBasePath().c_str(), GetPlayerID());

	if (bSave)
	{
		FILE* fp = fopen(szBuf, "w+");
		if (!fp)
			return;

		fprintf(fp, "index-vnum-count-price-buyed\n");
		for (const auto& item : m_vecGemItems)
			fprintf(fp, "%u %u %u %d %u\n", item.bPos, item.dwVnum, item.dwCount, item.dwPrice, item.bBuyed);
		fclose(fp);
	}
	else
	{
		if (m_bGemShopLoaded)
			return;
		m_bGemShopLoaded = true;

		m_vecGemItems.clear();

		FILE* fp = fopen(szBuf, "r");
		if (!fp)
			return;

		TGemItem item;
		std::vector<std::string> m_vec;

		while (fgets(szBuf, sizeof(szBuf), fp))
		{
			m_vec.clear();
			split_argument_ex(szBuf, m_vec);
			if (m_vec.size() != 5)
				continue;
			str_to_number(item.bPos, m_vec[0].c_str());
			str_to_number(item.dwVnum, m_vec[1].c_str());
			str_to_number(item.dwCount, m_vec[2].c_str());
			str_to_number(item.dwPrice, m_vec[3].c_str());
			str_to_number(item.bBuyed, m_vec[4].c_str());
			m_vecGemItems.emplace_back(item);
		}
		fclose(fp);
	}
}
#endif
