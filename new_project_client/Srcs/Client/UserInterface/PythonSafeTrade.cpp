#include "StdAfx.h"
#ifdef ENABLE_SAFE_TRADE_SYSTEM
#include "PythonSafeTrade.h"

CPythonSafeTrade::CPythonSafeTrade()
{
	Clear();
}

CPythonSafeTrade::~CPythonSafeTrade()
{
}

void CPythonSafeTrade::Clear()
{
	m_dwTradeID = 0;
	memset(m_aDepot, 0, sizeof(m_aDepot));
	m_vecList.clear();
}

void CPythonSafeTrade::SetDepotItem(BYTE slot, const TItemData& d)
{
	if (slot < SAFE_TRADE_MAX_ITEMS)
		m_aDepot[slot] = d;
}

void CPythonSafeTrade::DelDepotItem(BYTE slot)
{
	if (slot < SAFE_TRADE_MAX_ITEMS)
		memset(&m_aDepot[slot], 0, sizeof(TItemData));
}

const TItemData& CPythonSafeTrade::GetDepotItem(BYTE slot) const
{
	static TItemData s_empty;
	if (slot >= SAFE_TRADE_MAX_ITEMS)
	{
		memset(&s_empty, 0, sizeof(s_empty));
		return s_empty;
	}
	return m_aDepot[slot];
}

const CPythonSafeTrade::TListEntry* CPythonSafeTrade::GetListEntry(int i) const
{
	if (i < 0 || i >= (int)m_vecList.size())
		return nullptr;
	return &m_vecList[i];
}
#endif
