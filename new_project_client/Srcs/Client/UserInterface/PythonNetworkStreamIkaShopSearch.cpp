#include "StdAfx.h"
#ifdef ENABLE_IKASHOP_SEARCH
#include "PythonNetworkStream.h"
#include "PythonIkaShopSearch.h"

// ============================================================================
// IKASHOP tarzi global Pazar Arama - net katmani.
// CG 84 sabit 80 bayt (sequence'li); GC 139 dinamik zarf + subheader.
// Sonuclar CPythonIkaShopSearch'e yazilir; python'a yalnizca sinyal gider
// (SafeTrade kalibi): OnIkaShopSearchResult / OnIkaShopResultDelete / OnIkaShopPopup
// ============================================================================

bool CPythonNetworkStream::SendIkaShopFilterRequest(const char * c_szName, int iType, int iSubType, DWORD dwPriceMin, DWORD dwPriceMax, int iLevelMin, int iLevelMax)
{
	TPacketCGIkaShopSearch kPacket;
	memset(&kPacket, 0, sizeof(kPacket));
	kPacket.bHeader = HEADER_CG_NEW_OFFLINESHOP;
	kPacket.bSubheader = IKASEARCH_CG_FILTER;

	if (c_szName)
		strncpy(kPacket.szName, c_szName, sizeof(kPacket.szName) - 1);

	kPacket.bType = (BYTE) (iType < 0 ? 0xFF : iType);
	kPacket.bSubType = (BYTE) (iSubType < 0 ? 0xFF : iSubType);
	kPacket.dwPriceMin = dwPriceMin;
	kPacket.dwPriceMax = dwPriceMax;
	kPacket.iLevelMin = iLevelMin;
	kPacket.iLevelMax = iLevelMax;

	const TPlayerItemAttribute * c_pAttrs = CPythonIkaShopSearch::Instance().GetFilterAttrs();
	for (int i = 0; i < IKASEARCH_FILTER_ATTR_NUM; ++i)
		kPacket.aFilterAttrs[i] = c_pAttrs[i];

	if (!Send(sizeof(kPacket), &kPacket))
		return false;

	return SendSequence();
}

bool CPythonNetworkStream::SendIkaShopFillRequest()
{
	// IKASHOP SendRandomSearchFillRequest: pencere acilisinda filtresiz vitrin doldurma.
	// FILTER subheader + iReserved1=1 (server fill modu; filtre zorunlulugu atlanir).
	TPacketCGIkaShopSearch kPacket;
	memset(&kPacket, 0, sizeof(kPacket));
	kPacket.bHeader = HEADER_CG_NEW_OFFLINESHOP;
	kPacket.bSubheader = IKASEARCH_CG_FILTER;
	kPacket.bType = 0xFF;
	kPacket.bSubType = 0xFF;
	kPacket.iReserved1 = 1;

	if (!Send(sizeof(kPacket), &kPacket))
		return false;

	return SendSequence();
}

bool CPythonNetworkStream::SendIkaShopBuyPacket(DWORD dwOwnerPID, DWORD dwItemDBID, DWORD dwSeenPrice)
{
	TPacketCGIkaShopSearch kPacket;
	memset(&kPacket, 0, sizeof(kPacket));
	kPacket.bHeader = HEADER_CG_NEW_OFFLINESHOP;
	kPacket.bSubheader = IKASEARCH_CG_BUY;
	kPacket.dwOwnerPID = dwOwnerPID;
	kPacket.dwItemDBID = dwItemDBID;
	kPacket.dwSeenPrice = dwSeenPrice;

	if (!Send(sizeof(kPacket), &kPacket))
		return false;

	return SendSequence();
}

bool CPythonNetworkStream::SendIkaShopViewShopPacket(DWORD dwOwnerPID)
{
	TPacketCGIkaShopSearch kPacket;
	memset(&kPacket, 0, sizeof(kPacket));
	kPacket.bHeader = HEADER_CG_NEW_OFFLINESHOP;
	kPacket.bSubheader = IKASEARCH_CG_VIEW_SHOP;
	kPacket.dwOwnerPID = dwOwnerPID;

	if (!Send(sizeof(kPacket), &kPacket))
		return false;

	return SendSequence();
}

bool CPythonNetworkStream::RecvIkaShopSearchPacket()
{
	TPacketGCIkaShopSearch kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;

	switch (kPacket.bSubheader)
	{
		case IKASEARCH_GC_RESULT:
		{
			CPythonIkaShopSearch::Instance().ClearResults();

			// Zarf boyut tutarliligi (bozuk paket -> baglantiyi kes, desync tasima)
			const int iExpected = (int) sizeof(kPacket) + (int) kPacket.wCount * (int) sizeof(SIkaSearchResult);
			if ((int) kPacket.wSize != iExpected || kPacket.wCount > IKASEARCH_MAX_RESULTS)
			{
				TraceError("RecvIkaShopSearchPacket: RESULT boyut tutarsiz (size %d beklenen %d count %d)",
					(int) kPacket.wSize, iExpected, (int) kPacket.wCount);
				return false;
			}

			for (WORD i = 0; i < kPacket.wCount; ++i)
			{
				SIkaSearchResult kResult;
				if (!Recv(sizeof(kResult), &kResult))
					return false;

				kResult.szShopName[sizeof(kResult.szShopName) - 1] = '\0';
				CPythonIkaShopSearch::Instance().AddResult(kResult);
			}

			PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], "OnIkaShopSearchResult", Py_BuildValue("(i)", (int) kPacket.wCount));
			break;
		}

		case IKASEARCH_GC_RESULT_DELETE:
		{
			DWORD dwItemDBID = 0;
			if (!Recv(sizeof(DWORD), &dwItemDBID))
				return false;

			PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], "OnIkaShopResultDelete", Py_BuildValue("(i)", (int) dwItemDBID));
			break;
		}

		case IKASEARCH_GC_POPUP:
		{
			char szLocaleKey[IKASEARCH_POPUP_KEY_LEN];
			if (!Recv(sizeof(szLocaleKey), szLocaleKey))
				return false;

			szLocaleKey[sizeof(szLocaleKey) - 1] = '\0';
			PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], "OnIkaShopPopup", Py_BuildValue("(s)", szLocaleKey));
			break;
		}

		default:
			TraceError("RecvIkaShopSearchPacket: bilinmeyen subheader %d", (int) kPacket.bSubheader);
			return false;
	}

	return true;
}
#endif
