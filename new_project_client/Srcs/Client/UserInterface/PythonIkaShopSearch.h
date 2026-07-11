#pragma once
#ifdef ENABLE_IKASHOP_SEARCH
#include "Packet.h"
#include "GameType.h"
#include <vector>
#include <string>

// IKASHOP tarzi global Pazar Arama - client tarafi durum deposu.
// Sonuc listesi binary'de tutulur; uiikashopsearch.py getter'larla okur
// (SafeTrade kalibi). Net callback'leri game window'a gider:
//   OnIkaShopSearchResult(count) / OnIkaShopResultDelete(itemDBID) / OnIkaShopPopup(localeKey)
class CPythonIkaShopSearch : public CSingleton<CPythonIkaShopSearch>
{
	public:
		CPythonIkaShopSearch();
		virtual ~CPythonIkaShopSearch();

		void	Clear();

		// Sonuc listesi (RecvIkaShopSearchPacket doldurur)
		void	ClearResults()								{ m_vecResults.clear(); }
		void	AddResult(const SIkaSearchResult & r)		{ m_vecResults.push_back(r); }
		int		GetResultCount() const						{ return (int) m_vecResults.size(); }
		const SIkaSearchResult *	GetResult(int i) const;
		// Uzak satista karti "SATILDI" isaretlemek icin index bul (-1 = yok)
		int		FindResultByDBID(DWORD dwItemDBID) const;

		// Filtre efsun secimleri (module setter'lari yazar; SendFilterRequest okur)
		void	ClearFilterAttrs();
		bool	SetFilterAttr(int iIndex, BYTE bType, short sValue);
		const TPlayerItemAttribute *	GetFilterAttrs() const	{ return m_aFilterAttrs; }

	private:
		std::vector<SIkaSearchResult>	m_vecResults;
		TPlayerItemAttribute			m_aFilterAttrs[IKASEARCH_FILTER_ATTR_NUM];
};

extern void initikashop();	// PythonIkaShopSearchModule.cpp
#endif
