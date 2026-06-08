#pragma once
#ifdef ENABLE_SAFE_TRADE_SYSTEM
#include "Packet.h"
#include "GameType.h"
#include <vector>

// A oyuncusunun depo verisi + B'nin gelen/giden listesi. Python getter'larla okunur.
class CPythonSafeTrade : public CSingleton<CPythonSafeTrade>
{
	public:
		enum { SAFE_TRADE_MAX_ITEMS = 24 };   // 6x4 grid

		typedef struct SListEntry
		{
			DWORD tradeID;
			char  sender[CHARACTER_NAME_MAX_LEN + 1];
			BYTE  itemCount;
			DWORD time;
			BYTE  isOwner;
		} TListEntry;

	public:
		CPythonSafeTrade();
		virtual ~CPythonSafeTrade();

		void  Clear();

		// depo
		void  SetTradeID(DWORD id)                       { m_dwTradeID = id; }
		DWORD GetTradeID() const                         { return m_dwTradeID; }
		void  SetDepotItem(BYTE slot, const TItemData& d);
		void  DelDepotItem(BYTE slot);
		const TItemData& GetDepotItem(BYTE slot) const;

		// liste
		void  ClearList()                                { m_vecList.clear(); }
		void  AddListEntry(const TListEntry& e)          { m_vecList.push_back(e); }
		int   GetListCount() const                       { return (int)m_vecList.size(); }
		const TListEntry* GetListEntry(int i) const;

	private:
		DWORD                   m_dwTradeID;
		TItemData               m_aDepot[SAFE_TRADE_MAX_ITEMS];
		std::vector<TListEntry> m_vecList;
};

extern void initSafeTrade();   // PythonSafeTradeModule.cpp
#endif
