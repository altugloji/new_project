#include "StdAfx.h"
#ifdef ENABLE_IKASHOP_SEARCH
#include "PythonIkaShopSearch.h"

CPythonIkaShopSearch::CPythonIkaShopSearch()
{
	Clear();
}

CPythonIkaShopSearch::~CPythonIkaShopSearch()
{
}

void CPythonIkaShopSearch::Clear()
{
	m_vecResults.clear();
	ClearFilterAttrs();
}

const SIkaSearchResult * CPythonIkaShopSearch::GetResult(int i) const
{
	if (i < 0 || i >= (int) m_vecResults.size())
		return NULL;

	return &m_vecResults[i];
}

int CPythonIkaShopSearch::FindResultByDBID(DWORD dwItemDBID) const
{
	for (int i = 0; i < (int) m_vecResults.size(); ++i)
		if (m_vecResults[i].dwItemDBID == dwItemDBID)
			return i;

	return -1;
}

void CPythonIkaShopSearch::ClearFilterAttrs()
{
	memset(m_aFilterAttrs, 0, sizeof(m_aFilterAttrs));
}

bool CPythonIkaShopSearch::SetFilterAttr(int iIndex, BYTE bType, short sValue)
{
	if (iIndex < 0 || iIndex >= IKASEARCH_FILTER_ATTR_NUM)
		return false;

	m_aFilterAttrs[iIndex].bType = bType;
	m_aFilterAttrs[iIndex].sValue = sValue;
	return true;
}
#endif
