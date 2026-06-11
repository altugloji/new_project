#include "stdafx.h"
#include "PythonShop.h"

#include "PythonNetworkStream.h"
#include "PythonBackground.h"
#include "PythonMiniMap.h"
#include "PythonCharacterManager.h"

// ---------------------------------------------------------------------------
// Pazar Arama (ShopSearch): bulunan dukkanlari harita + minimap uzerinde isaretle.
// Hedef-efekt id'leri normal quest/parti hedefleriyle cakismasin diye yuksek,
// ayrilmis bir araliktan secilir.
// ---------------------------------------------------------------------------
namespace
{
	const DWORD OFFLINESHOP_SEARCH_TARGET_BASE = 900000;
}

void CPythonShop::ShowFoundShopPosition(DWORD vid, long x, long y)
{
	const DWORD targetId = OFFLINESHOP_SEARCH_TARGET_BASE + GetFoundShopTargetCount();

	// Sahip/tezgah ekranda canliysa vid'e bagla (oyuncuyu takip eder),
	// degilse (gorus mesafesi disi offline dukkan) sabit konuma yerlestir.
	if (CPythonCharacterManager::Instance().GetInstancePtr(vid))
	{
		CPythonMiniMap::Instance().CreateTarget(targetId, "Shop", vid);
		CPythonBackground::Instance().CreateTargetEffect(targetId, vid);
	}
	else
	{
		CPythonMiniMap::Instance().CreateTarget(targetId, "Shop");
		CPythonMiniMap::Instance().UpdateTarget(targetId, x, y);
		CPythonBackground::Instance().CreateTargetEffect(targetId, x, y);
	}

	TFoundShop info;
	info.targetId = targetId;
	info.isViewed = false;
	m_foundShopMap[vid] = info;
}

void CPythonShop::ClearFoundShopMap()
{
	for (std::map<DWORD, TFoundShop>::iterator it = m_foundShopMap.begin(); it != m_foundShopMap.end(); ++it)
	{
		CPythonBackground::Instance().DeleteTargetEffect(it->second.targetId);
		CPythonMiniMap::Instance().DeleteTarget(it->second.targetId);
	}
	m_foundShopMap.clear();
}

DWORD CPythonShop::GetFoundShopFromSearchTargetId(DWORD vid)
{
	std::map<DWORD, TFoundShop>::iterator it = m_foundShopMap.find(vid);
	if (it != m_foundShopMap.end())
		return it->second.targetId;
	return 0;
}

bool CPythonShop::IsFoundShopFromSearchViewed(DWORD vid)
{
	std::map<DWORD, TFoundShop>::iterator it = m_foundShopMap.find(vid);
	if (it != m_foundShopMap.end())
		return it->second.isViewed;
	return false;
}

bool CPythonShop::IsFoundShopFromSearchItem(DWORD vid)
{
	return m_foundShopMap.find(vid) != m_foundShopMap.end();
}

void CPythonShop::SetFoundShopViewed(DWORD vid)
{
	std::map<DWORD, TFoundShop>::iterator it = m_foundShopMap.find(vid);
	if (it != m_foundShopMap.end())
		it->second.isViewed = true;
}

//BOOL CPythonShop::GetSlotItemID(DWORD dwSlotPos, DWORD* pdwItemID)
//{
//	if (!CheckSlotIndex(dwSlotPos))
//		return FALSE;
//	const TShopItemData * itemData;
//	if (!GetItemData(dwSlotPos, &itemData))
//		return FALSE;
//	*pdwItemID=itemData->vnum;
//	return TRUE;
//}
void CPythonShop::SetTabCoinType(BYTE tabIdx, BYTE coinType)
{
	if (tabIdx >= m_bTabCount)
	{
		TraceError("Out of Index. tabIdx(%d) must be less than %d.", tabIdx, SHOP_TAB_COUNT_MAX);
		return;
	}
	m_aShoptabs[tabIdx].coinType = coinType;
}

BYTE CPythonShop::GetTabCoinType(BYTE tabIdx) const
{
	if (tabIdx >= m_bTabCount)
	{
		TraceError("Out of Index. tabIdx(%d) must be less than %d.", tabIdx, SHOP_TAB_COUNT_MAX);
		return 0xff;
	}
	return m_aShoptabs[tabIdx].coinType;
}

void CPythonShop::SetTabName(BYTE tabIdx, const char* name)
{
	if (tabIdx >= m_bTabCount)
	{
		TraceError("Out of Index. tabIdx(%d) must be less than %d.", tabIdx, SHOP_TAB_COUNT_MAX);
		return;
	}
	m_aShoptabs[tabIdx].name = name;
}

const char* CPythonShop::GetTabName(BYTE tabIdx) const
{
	if (tabIdx >= m_bTabCount)
	{
		TraceError("Out of Index. tabIdx(%d) must be less than %d.", tabIdx, SHOP_TAB_COUNT_MAX);
		return nullptr;
	}

	return m_aShoptabs[tabIdx].name.c_str();
}

void CPythonShop::SetItemData(DWORD dwIndex, const TShopItemData & c_rShopItemData)
{
	BYTE tabIdx = dwIndex / SHOP_HOST_ITEM_MAX_NUM;
	const DWORD dwSlotPos = dwIndex % SHOP_HOST_ITEM_MAX_NUM;

	SetItemData(tabIdx, dwSlotPos, c_rShopItemData);
}

BOOL CPythonShop::GetItemData(DWORD dwIndex, const TShopItemData ** c_ppItemData) const
{
	BYTE tabIdx = dwIndex / SHOP_HOST_ITEM_MAX_NUM;
	const DWORD dwSlotPos = dwIndex % SHOP_HOST_ITEM_MAX_NUM;

	return GetItemData(tabIdx, dwSlotPos, c_ppItemData);
}

void CPythonShop::SetItemData(BYTE tabIdx, DWORD dwSlotPos, const TShopItemData & c_rShopItemData)
{
	if (tabIdx >= SHOP_TAB_COUNT_MAX || dwSlotPos >= SHOP_HOST_ITEM_MAX_NUM)
	{
		TraceError("Out of Index. tabIdx(%d) must be less than %d. dwSlotPos(%d) must be less than %d", tabIdx, SHOP_TAB_COUNT_MAX, dwSlotPos, SHOP_HOST_ITEM_MAX_NUM);
		return;
	}

	m_aShoptabs[tabIdx].items[dwSlotPos] = c_rShopItemData;
}

BOOL CPythonShop::GetItemData(BYTE tabIdx, DWORD dwSlotPos, const TShopItemData ** c_ppItemData) const
{
	if (tabIdx >= SHOP_TAB_COUNT_MAX || dwSlotPos >= SHOP_HOST_ITEM_MAX_NUM)
	{
		TraceError("Out of Index. tabIdx(%d) must be less than %d. dwSlotPos(%d) must be less than %d", tabIdx, SHOP_TAB_COUNT_MAX, dwSlotPos, SHOP_HOST_ITEM_MAX_NUM);
		return FALSE;
	}

	*c_ppItemData = &m_aShoptabs[tabIdx].items[dwSlotPos];

	return TRUE;
}
//
//BOOL CPythonShop::CheckSlotIndex(DWORD dwSlotPos)
//{
//	if (dwSlotPos >= SHOP_HOST_ITEM_MAX_NUM * SHOP_TAB_COUNT_MAX)
//		return FALSE;
//
//	return TRUE;
//}

void CPythonShop::ClearPrivateShopStock()
{
	m_PrivateShopItemStock.clear();
}
void CPythonShop::AddPrivateShopItemStock(TItemPos ItemPos, BYTE dwDisplayPos, DWORD dwPrice
	#ifdef ENABLE_CHEQUE_SYSTEM
	, DWORD dwCheque
	#endif
)
{
	DelPrivateShopItemStock(ItemPos);

	TShopItemTable SellingItem;
	SellingItem.vnum = 0;
	SellingItem.count = 0;
	SellingItem.pos = ItemPos;
	SellingItem.price = dwPrice;
	SellingItem.display_pos = dwDisplayPos;
#ifdef ENABLE_CHEQUE_SYSTEM
	SellingItem.cheque = dwCheque;
#endif
	m_PrivateShopItemStock.emplace(ItemPos, SellingItem);
}
void CPythonShop::DelPrivateShopItemStock(TItemPos ItemPos)
{
	if (!m_PrivateShopItemStock.contains(ItemPos))
		return;

	m_PrivateShopItemStock.erase(ItemPos);
}
int CPythonShop::GetPrivateShopItemPrice(TItemPos ItemPos)
{
	const auto itor = m_PrivateShopItemStock.find(ItemPos);

	if (m_PrivateShopItemStock.end() == itor)
		return 0;

	const TShopItemTable & rShopItemTable = itor->second;
	return rShopItemTable.price;
}

#ifdef ENABLE_CHEQUE_SYSTEM
int CPythonShop::GetPrivateShopItemCheque(TItemPos ItemPos)
{
	const auto itor = m_PrivateShopItemStock.find(ItemPos);
	if (m_PrivateShopItemStock.end() == itor)
		return 0;

	const auto& rShopItemTable = itor->second;
	return rShopItemTable.cheque;
}
#endif

struct ItemStockSortFunc
{
	bool operator() (TShopItemTable & rkLeft, TShopItemTable & rkRight) const
	{
		return rkLeft.display_pos < rkRight.display_pos;
	}
};
void CPythonShop::BuildPrivateShop(const char * c_szName)
{
	std::vector<TShopItemTable> ItemStock;
	ItemStock.reserve(m_PrivateShopItemStock.size());

	auto itor = m_PrivateShopItemStock.begin();
	for (; itor != m_PrivateShopItemStock.end(); ++itor)
	{
		ItemStock.push_back(itor->second);
	}

	std::sort(ItemStock.begin(), ItemStock.end(), ItemStockSortFunc());

	CPythonNetworkStream::Instance().SendBuildPrivateShopPacket(c_szName, ItemStock);
}

#ifdef ENABLE_OFFLINE_SHOP
void CPythonShop::ClearOfflineShopEdit()
{
	m_OfflineShopRemoveList.clear();
	m_OfflineShopPriceUpdateList.clear();
	ClearPrivateShopStock();
}

void CPythonShop::AddOfflineShopRemove(BYTE bDisplayPos)
{
	for (size_t i = 0; i < m_OfflineShopRemoveList.size(); ++i)
		if (m_OfflineShopRemoveList[i] == bDisplayPos)
			return;
	m_OfflineShopRemoveList.push_back(bDisplayPos);
}

void CPythonShop::AddOfflineShopPriceUpdate(BYTE bDisplayPos, DWORD dwPrice)
{
	// Ayni slot zaten varsa fiyati guncelle
	for (size_t i = 0; i < m_OfflineShopPriceUpdateList.size(); ++i)
	{
		if (m_OfflineShopPriceUpdateList[i].display_pos == bDisplayPos)
		{
			m_OfflineShopPriceUpdateList[i].price = dwPrice;
			return;
		}
	}
	TOfflineShopPriceUpdate upd;
	upd.display_pos = bDisplayPos;
	upd.price = dwPrice;
	m_OfflineShopPriceUpdateList.push_back(upd);
}

void CPythonShop::SendOfflineShopEdit(BYTE byAction)
{
	std::vector<TShopItemTable> ItemStock;
	ItemStock.reserve(m_PrivateShopItemStock.size());
	for (auto itor = m_PrivateShopItemStock.begin(); itor != m_PrivateShopItemStock.end(); ++itor)
		ItemStock.push_back(itor->second);
	std::sort(ItemStock.begin(), ItemStock.end(), ItemStockSortFunc());

	CPythonNetworkStream::Instance().SendOfflineShopEditPacket(byAction, m_OfflineShopRemoveList, ItemStock, m_OfflineShopPriceUpdateList);
}
#endif

void CPythonShop::Open(BOOL isPrivateShop, BOOL isMainPrivateShop)
{
	m_isShoping = TRUE;
	m_isPrivateShop = isPrivateShop;
	m_isMainPlayerPrivateShop = isMainPrivateShop;
}

void CPythonShop::Close()
{
	m_isShoping = FALSE;
	m_isPrivateShop = FALSE;
	m_isMainPlayerPrivateShop = FALSE;
}

BOOL CPythonShop::IsOpen() const
{
	return m_isShoping;
}

BOOL CPythonShop::IsPrivateShop() const
{
	return m_isPrivateShop;
}

BOOL CPythonShop::IsMainPlayerPrivateShop() const
{
	return m_isMainPlayerPrivateShop;
}

void CPythonShop::Clear()
{
	m_isShoping = FALSE;
	m_isPrivateShop = FALSE;
	m_isMainPlayerPrivateShop = FALSE;
	ClearPrivateShopStock();
	m_bTabCount = 1;

	for (int i = 0; i < SHOP_TAB_COUNT_MAX; i++)
	{
		// @fixme016 BEGIN
		m_aShoptabs[i].coinType = SHOP_COIN_TYPE_GOLD;
		m_aShoptabs[i].name = "";
		// @fixme016 END
		memset (m_aShoptabs[i].items, 0, sizeof(TShopItemData) * SHOP_HOST_ITEM_MAX_NUM);
	}
}

CPythonShop::CPythonShop(void)
{
	Clear();
}

CPythonShop::~CPythonShop(void)
{
}

PyObject * shopOpen(PyObject * poSelf, PyObject * poArgs)
{
	int isPrivateShop = false;
	PyTuple_GetInteger(poArgs, 0, &isPrivateShop);
	int isMainPrivateShop = false;
	PyTuple_GetInteger(poArgs, 1, &isMainPrivateShop);

	CPythonShop& rkShop=CPythonShop::Instance();
	rkShop.Open(isPrivateShop, isMainPrivateShop);
	return Py_BuildNone();
}

PyObject * shopClose(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop& rkShop=CPythonShop::Instance();
	rkShop.Close();
	return Py_BuildNone();
}

PyObject * shopIsOpen(PyObject * poSelf, PyObject * poArgs)
{
	const CPythonShop& rkShop=CPythonShop::Instance();
	return Py_BuildValue("i", rkShop.IsOpen());
}

PyObject * shopIsPrviateShop(PyObject * poSelf, PyObject * poArgs)
{
	const CPythonShop& rkShop=CPythonShop::Instance();
	return Py_BuildValue("i", rkShop.IsPrivateShop());
}

PyObject * shopIsMainPlayerPrivateShop(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop& rkShop=CPythonShop::Instance();
	return Py_BuildValue("i", rkShop.IsMainPlayerPrivateShop());
}

PyObject * shopGetItemID(PyObject * poSelf, PyObject * poArgs)
{
	int nPos;
	if (!PyTuple_GetInteger(poArgs, 0, &nPos))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(nPos, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->vnum);

	return Py_BuildValue("i", 0);
}

PyObject * shopGetItemCount(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(iIndex, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->count);

	return Py_BuildValue("i", 0);
}

PyObject * shopGetItemPrice(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(iIndex, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->price);

	return Py_BuildValue("i", 0);
}

#ifdef ENABLE_CHEQUE_SYSTEM
PyObject* shopGetItemCheque(PyObject* poSelf, PyObject* poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();

	const TShopItemData* c_pItemData;
	if (CPythonShop::Instance().GetItemData(iIndex, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->cheque);

	return Py_BuildValue("i", 0);
}
#endif

#ifdef ENABLE_MULTISHOP
PyObject * shopGetBuyWithItem(PyObject * poSelf, PyObject * poArgs)
{
	int nPos;
	if (!PyTuple_GetInteger(poArgs, 0, &nPos))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(nPos, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->wPriceVnum);

	return Py_BuildValue("i", 0);
}

PyObject * shopGetBuyWithItemCount(PyObject * poSelf, PyObject * poArgs)
{
	int nPos;
	if (!PyTuple_GetInteger(poArgs, 0, &nPos))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(nPos, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->wPrice);

	return Py_BuildValue("i", 0);
}

PyObject * shopGetItemGemPrice(PyObject * poSelf, PyObject * poArgs)
{
	int nPos;
	if (!PyTuple_GetInteger(poArgs, 0, &nPos))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(nPos, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->gem_price);

	return Py_BuildValue("i", 0);
}
#endif

PyObject * shopGetItemMetinSocket(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	int iMetinSocketIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iMetinSocketIndex))
		return Py_BuildException();

	const TShopItemData * c_pItemData;
	if (CPythonShop::Instance().GetItemData(iIndex, &c_pItemData))
		return Py_BuildValue("i", c_pItemData->alSockets[iMetinSocketIndex]);

	return Py_BuildValue("i", 0);
}

PyObject * shopGetItemAttribute(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	int iAttrSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iAttrSlotIndex))
		return Py_BuildException();

	if (iAttrSlotIndex >= 0 && iAttrSlotIndex < ITEM_ATTRIBUTE_SLOT_MAX_NUM)
	{
		const TShopItemData * c_pItemData;
		if (CPythonShop::Instance().GetItemData(iIndex, &c_pItemData))
			return Py_BuildValue("ii", c_pItemData->aAttr[iAttrSlotIndex].bType, c_pItemData->aAttr[iAttrSlotIndex].sValue);
	}

	return Py_BuildValue("ii", 0, 0);
}

PyObject * shopClearPrivateShopStock(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop::Instance().ClearPrivateShopStock();
	return Py_BuildNone();
}
PyObject * shopAddPrivateShopItemStock(PyObject * poSelf, PyObject * poArgs)
{
	BYTE bItemWindowType;
	if (!PyTuple_GetInteger(poArgs, 0, &bItemWindowType))
		return Py_BuildException();
	WORD wItemSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &wItemSlotIndex))
		return Py_BuildException();
	int iDisplaySlotIndex;
	if (!PyTuple_GetInteger(poArgs, 2, &iDisplaySlotIndex))
		return Py_BuildException();
	int iPrice;
	if (!PyTuple_GetInteger(poArgs, 3, &iPrice))
		return Py_BuildException();

#ifdef ENABLE_CHEQUE_SYSTEM
	int iCheque;
	if (!PyTuple_GetInteger(poArgs, 4, &iCheque))
		return Py_BuildException();
#endif

	CPythonShop::Instance().AddPrivateShopItemStock(TItemPos(bItemWindowType, wItemSlotIndex), iDisplaySlotIndex, iPrice
		#ifdef ENABLE_CHEQUE_SYSTEM
		, iCheque
		#endif
	);
	return Py_BuildNone();
}
PyObject * shopDelPrivateShopItemStock(PyObject * poSelf, PyObject * poArgs)
{
	BYTE bItemWindowType;
	if (!PyTuple_GetInteger(poArgs, 0, &bItemWindowType))
		return Py_BuildException();
	WORD wItemSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &wItemSlotIndex))
		return Py_BuildException();

	CPythonShop::Instance().DelPrivateShopItemStock(TItemPos(bItemWindowType, wItemSlotIndex));
	return Py_BuildNone();
}
PyObject * shopGetPrivateShopItemPrice(PyObject * poSelf, PyObject * poArgs)
{
	BYTE bItemWindowType;
	if (!PyTuple_GetInteger(poArgs, 0, &bItemWindowType))
		return Py_BuildException();
	WORD wItemSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &wItemSlotIndex))
		return Py_BuildException();

	const int iValue = CPythonShop::Instance().GetPrivateShopItemPrice(TItemPos(bItemWindowType, wItemSlotIndex));
	return Py_BuildValue("i", iValue);
}

#ifdef ENABLE_CHEQUE_SYSTEM
PyObject* shopGetPrivateShopItemCheque(PyObject* poSelf, PyObject* poArgs)
{
	BYTE bItemWindowType;
	if (!PyTuple_GetInteger(poArgs, 0, &bItemWindowType))
		return Py_BuildException();
	WORD wItemSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &wItemSlotIndex))
		return Py_BuildException();

	int iValue = CPythonShop::Instance().GetPrivateShopItemCheque(TItemPos(bItemWindowType, wItemSlotIndex));
	return Py_BuildValue("i", iValue);
}
#endif

PyObject * shopBuildPrivateShop(PyObject * poSelf, PyObject * poArgs)
{
	char * szName;
	if (!PyTuple_GetString(poArgs, 0, &szName))
		return Py_BuildException();

	CPythonShop::Instance().BuildPrivateShop(szName);
	return Py_BuildNone();
}

#ifdef ENABLE_OFFLINE_SHOP
PyObject * shopClearOfflineShopEdit(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop::Instance().ClearOfflineShopEdit();
	return Py_BuildNone();
}

PyObject * shopAddOfflineShopRemove(PyObject * poSelf, PyObject * poArgs)
{
	int iDisplayPos;
	if (!PyTuple_GetInteger(poArgs, 0, &iDisplayPos))
		return Py_BuildException();

	CPythonShop::Instance().AddOfflineShopRemove((BYTE)iDisplayPos);
	return Py_BuildNone();
}

PyObject * shopAddOfflineShopPriceUpdate(PyObject * poSelf, PyObject * poArgs)
{
	int iDisplayPos;
	if (!PyTuple_GetInteger(poArgs, 0, &iDisplayPos))
		return Py_BuildException();
	int iPrice;
	if (!PyTuple_GetInteger(poArgs, 1, &iPrice))
		return Py_BuildException();

	CPythonShop::Instance().AddOfflineShopPriceUpdate((BYTE)iDisplayPos, (DWORD)iPrice);
	return Py_BuildNone();
}

PyObject * shopOfflineShopEnter(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop::Instance().SendOfflineShopEdit(OFFLINE_SHOP_EDIT_ACTION_ENTER);
	return Py_BuildNone();
}

PyObject * shopOfflineShopCancel(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop::Instance().SendOfflineShopEdit(OFFLINE_SHOP_EDIT_ACTION_CANCEL);
	return Py_BuildNone();
}

PyObject * shopSendOfflineShopEdit(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop::Instance().SendOfflineShopEdit(OFFLINE_SHOP_EDIT_ACTION_APPLY);
	return Py_BuildNone();
}
#endif

PyObject * shopGetTabCount(PyObject * poSelf, PyObject * poArgs)
{
	return Py_BuildValue("i", CPythonShop::instance().GetTabCount());
}

PyObject * shopGetTabName(PyObject * poSelf, PyObject * poArgs)
{
	BYTE bTabIdx;
	if (!PyTuple_GetInteger(poArgs, 0, &bTabIdx))
		return Py_BuildException();

	return Py_BuildValue("s", CPythonShop::instance().GetTabName(bTabIdx));
}

PyObject * shopGetTabCoinType(PyObject * poSelf, PyObject * poArgs)
{
	BYTE bTabIdx;
	if (!PyTuple_GetInteger(poArgs, 0, &bTabIdx))
		return Py_BuildException();

	return Py_BuildValue("i", CPythonShop::instance().GetTabCoinType(bTabIdx));
}

// ---- Pazar Arama (ShopSearch) python bag fonksiyonlari ----
PyObject * shopSendSearchItem(PyObject * poSelf, PyObject * poArgs)
{
	int iSearchIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iSearchIndex))
		return Py_BuildException();

	int iSocket0 = 0;
	PyTuple_GetInteger(poArgs, 1, &iSocket0);

	CPythonNetworkStream::Instance().SendShopSearchItem((DWORD)iSearchIndex, iSocket0);
	return Py_BuildNone();
}

PyObject * shopClearFoundShopMap(PyObject * poSelf, PyObject * poArgs)
{
	CPythonShop::Instance().ClearFoundShopMap();
	return Py_BuildNone();
}

PyObject * shopIsFoundShopFromSearchItem(PyObject * poSelf, PyObject * poArgs)
{
	int iVID;
	if (!PyTuple_GetInteger(poArgs, 0, &iVID))
		return Py_BuildException();

	return Py_BuildValue("i", CPythonShop::Instance().IsFoundShopFromSearchItem((DWORD)iVID));
}

void initshop()
{
	static PyMethodDef s_methods[] =
	{
		// Shop
		{ "Open",						shopOpen,						METH_VARARGS },
		{ "Close",						shopClose,						METH_VARARGS },
		{ "IsOpen",						shopIsOpen,						METH_VARARGS },
		{ "IsPrivateShop",				shopIsPrviateShop,				METH_VARARGS },
		{ "IsMainPlayerPrivateShop",	shopIsMainPlayerPrivateShop,	METH_VARARGS },
		{ "GetItemID",					shopGetItemID,					METH_VARARGS },
		{ "GetItemCount",				shopGetItemCount,				METH_VARARGS },
		{ "GetItemPrice",				shopGetItemPrice,				METH_VARARGS },
		{ "GetItemMetinSocket",			shopGetItemMetinSocket,			METH_VARARGS },
		{ "GetItemAttribute",			shopGetItemAttribute,			METH_VARARGS },
		{ "GetTabCount",				shopGetTabCount,				METH_VARARGS },
		{ "GetTabName",					shopGetTabName,					METH_VARARGS },
		{ "GetTabCoinType",				shopGetTabCoinType,				METH_VARARGS },

		// Private Shop
		{ "ClearPrivateShopStock",		shopClearPrivateShopStock,		METH_VARARGS },
		{ "AddPrivateShopItemStock",	shopAddPrivateShopItemStock,	METH_VARARGS },
		{ "DelPrivateShopItemStock",	shopDelPrivateShopItemStock,	METH_VARARGS },
		{ "GetPrivateShopItemPrice",	shopGetPrivateShopItemPrice,	METH_VARARGS },
		{ "BuildPrivateShop",			shopBuildPrivateShop,			METH_VARARGS },
#ifdef ENABLE_OFFLINE_SHOP
		{ "ClearOfflineShopEdit",		shopClearOfflineShopEdit,		METH_VARARGS },
		{ "AddOfflineShopRemove",		shopAddOfflineShopRemove,		METH_VARARGS },
		{ "AddOfflineShopPriceUpdate",	shopAddOfflineShopPriceUpdate,	METH_VARARGS },
		{ "OfflineShopEnter",			shopOfflineShopEnter,			METH_VARARGS },
		{ "OfflineShopCancel",			shopOfflineShopCancel,			METH_VARARGS },
		{ "SendOfflineShopEdit",		shopSendOfflineShopEdit,		METH_VARARGS },
#endif
#ifdef ENABLE_CHEQUE_SYSTEM
		{ "GetItemCheque",				shopGetItemCheque,				METH_VARARGS },
		{ "GetPrivateShopItemCheque",	shopGetPrivateShopItemCheque,	METH_VARARGS },
#endif
#ifdef ENABLE_MULTISHOP
		{ "GetBuyWithItem",				shopGetBuyWithItem,				METH_VARARGS },
		{ "GetBuyWithItemCount",		shopGetBuyWithItemCount,		METH_VARARGS },
		{ "GetItemGemPrice",			shopGetItemGemPrice,				METH_VARARGS },
#endif
		// ---- Pazar Arama (ShopSearch) ----
		{ "SendSearchItem",				shopSendSearchItem,				METH_VARARGS },
		{ "ClearFoundShopMap",			shopClearFoundShopMap,			METH_VARARGS },
		{ "IsFoundShopFromSearchItem",	shopIsFoundShopFromSearchItem,	METH_VARARGS },

		{nullptr, nullptr},
	};
	PyObject * poModule = Py_InitModule("shop", s_methods);

	PyModule_AddIntConstant(poModule, "SHOP_SLOT_COUNT", SHOP_HOST_ITEM_MAX_NUM);
	PyModule_AddIntConstant(poModule, "SHOP_COIN_TYPE_GOLD", SHOP_COIN_TYPE_GOLD);
	PyModule_AddIntConstant(poModule, "SHOP_COIN_TYPE_SECONDARY_COIN", SHOP_COIN_TYPE_SECONDARY_COIN);

	// ---- Pazar Arama (ShopSearch) kategori sabitleri ----
	// BU degerler sunucudaki common/length.h EShopOfflineSearchCategories ile
	// BIREBIR AYNI olmak zorundadir (searchIndex = category*SHOP_CATEGORY_MAX_SUB + sub).
	PyModule_AddIntConstant(poModule, "SHOP_CATEGORY_MAX_SUB", SHOP_CATEGORY_MAX_SUB);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_BOOKS", SHOP_SEARCH_CATEGORY_BOOKS);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_REFINE", SHOP_SEARCH_CATEGORY_REFINE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_SOULSTONE", SHOP_SEARCH_CATEGORY_SOULSTONE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_HERBALISM", SHOP_SEARCH_CATEGORY_HERBALISM);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_FISHING", SHOP_SEARCH_CATEGORY_FISHING);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_HORSE", SHOP_SEARCH_CATEGORY_HORSE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_SPECIAL", SHOP_SEARCH_CATEGORY_SPECIAL);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_MINING", SHOP_SEARCH_CATEGORY_MINING);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_POLYMORPH", SHOP_SEARCH_CATEGORY_POLYMORPH);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_ARMOR", SHOP_SEARCH_CATEGORY_ARMOR);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_ARMOR_ATTR", SHOP_SEARCH_CATEGORY_ARMOR_ATTR);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_WEAPON", SHOP_SEARCH_CATEGORY_WEAPON);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_WEAPON_ATTR", SHOP_SEARCH_CATEGORY_WEAPON_ATTR);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_JEWELRY", SHOP_SEARCH_CATEGORY_JEWELRY);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_CATEGORY_JEWELRY_ATTR", SHOP_SEARCH_CATEGORY_JEWELRY_ATTR);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WARRIOR_0", SHOP_SEARCH_SUB_WARRIOR_0);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WARRIOR_1", SHOP_SEARCH_SUB_WARRIOR_1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_ASSASSIN_0", SHOP_SEARCH_SUB_ASSASSIN_0);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_ASSASSIN_1", SHOP_SEARCH_SUB_ASSASSIN_1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SURA_0", SHOP_SEARCH_SUB_SURA_0);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SURA_1", SHOP_SEARCH_SUB_SURA_1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SHAMAN_0", SHOP_SEARCH_SUB_SHAMAN_0);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SHAMAN_1", SHOP_SEARCH_SUB_SHAMAN_1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_PASSIVE_SKILL", SHOP_SEARCH_SUB_PASSIVE_SKILL);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_M1", SHOP_SEARCH_SUB_REFINE_M1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_OATH", SHOP_SEARCH_SUB_REFINE_OATH);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_M2", SHOP_SEARCH_SUB_REFINE_M2);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_ORC", SHOP_SEARCH_SUB_REFINE_ORC);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_DESERT1", SHOP_SEARCH_SUB_REFINE_DESERT1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_DESERT2", SHOP_SEARCH_SUB_REFINE_DESERT2);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_SNOW", SHOP_SEARCH_SUB_REFINE_SNOW);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_HWANG", SHOP_SEARCH_SUB_REFINE_HWANG);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_END", SHOP_SEARCH_SUB_REFINE_END);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_SPECIAL", SHOP_SEARCH_SUB_REFINE_SPECIAL);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_REFINE_PEARL", SHOP_SEARCH_SUB_REFINE_PEARL);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SOULSTONE_0", SHOP_SEARCH_SUB_SOULSTONE_0);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SOULSTONE_1", SHOP_SEARCH_SUB_SOULSTONE_1);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SOULSTONE_2", SHOP_SEARCH_SUB_SOULSTONE_2);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SOULSTONE_3", SHOP_SEARCH_SUB_SOULSTONE_3);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SOULSTONE_4", SHOP_SEARCH_SUB_SOULSTONE_4);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_PRIMARY", SHOP_SEARCH_SUB_HERB_PRIMARY);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_SPECIAL", SHOP_SEARCH_SUB_HERB_SPECIAL);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_WATER_OFFENSIVE", SHOP_SEARCH_SUB_HERB_WATER_OFFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_WATER_DEFENSIVE", SHOP_SEARCH_SUB_HERB_WATER_DEFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_WATER_POWER", SHOP_SEARCH_SUB_HERB_WATER_POWER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_JUICE_OFFENSIVE", SHOP_SEARCH_SUB_HERB_JUICE_OFFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_JUICE_DEFENSIVE", SHOP_SEARCH_SUB_HERB_JUICE_DEFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_JUICE_POWER", SHOP_SEARCH_SUB_HERB_JUICE_POWER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_DEW_OFFENSIVE", SHOP_SEARCH_SUB_HERB_DEW_OFFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_DEW_DEFENSIVE", SHOP_SEARCH_SUB_HERB_DEW_DEFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_DEW_POWER", SHOP_SEARCH_SUB_HERB_DEW_POWER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_OTHER_POTION", SHOP_SEARCH_SUB_HERB_OTHER_POTION);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_AUTOPOTION", SHOP_SEARCH_SUB_HERB_AUTOPOTION);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_RECIPE_OFFENSIVE", SHOP_SEARCH_SUB_HERB_RECIPE_OFFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_RECIPE_DEFENSIVE", SHOP_SEARCH_SUB_HERB_RECIPE_DEFENSIVE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_RECIPE_POWER", SHOP_SEARCH_SUB_HERB_RECIPE_POWER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HERB_RECIPE_OTHER", SHOP_SEARCH_SUB_HERB_RECIPE_OTHER);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_FISHING_FISH", SHOP_SEARCH_SUB_FISHING_FISH);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_FISHING_FISH_COOK", SHOP_SEARCH_SUB_FISHING_FISH_COOK);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_FISHING_FISH_OTHER", SHOP_SEARCH_SUB_FISHING_FISH_OTHER);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_REFINE", SHOP_SEARCH_SUB_SPECIAL_REFINE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_TOITEM", SHOP_SEARCH_SUB_SPECIAL_TOITEM);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_CHARACTER", SHOP_SEARCH_SUB_SPECIAL_CHARACTER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_OTHER", SHOP_SEARCH_SUB_SPECIAL_OTHER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_DRAGON_VOUCHER", SHOP_SEARCH_SUB_SPECIAL_DRAGON_VOUCHER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_QUEST", SHOP_SEARCH_SUB_SPECIAL_QUEST);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_SPECIAL_LOOTBOX", SHOP_SEARCH_SUB_SPECIAL_LOOTBOX);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_MINING_ORE", SHOP_SEARCH_SUB_MINING_ORE);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_MINING_MELT", SHOP_SEARCH_SUB_MINING_MELT);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_ARMOR_BODY", SHOP_SEARCH_SUB_ARMOR_BODY);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_ARMOR_SHIELD", SHOP_SEARCH_SUB_ARMOR_SHIELD);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_ARMOR_HEAD", SHOP_SEARCH_SUB_ARMOR_HEAD);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WEAPON_ONEHAND", SHOP_SEARCH_SUB_WEAPON_ONEHAND);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WEAPON_TWOHAND", SHOP_SEARCH_SUB_WEAPON_TWOHAND);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WEAPON_DAGGER", SHOP_SEARCH_SUB_WEAPON_DAGGER);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WEAPON_BOW", SHOP_SEARCH_SUB_WEAPON_BOW);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WEAPON_BELL", SHOP_SEARCH_SUB_WEAPON_BELL);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_WEAPON_FAN", SHOP_SEARCH_SUB_WEAPON_FAN);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_JEWELRY_EAR", SHOP_SEARCH_SUB_JEWELRY_EAR);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_JEWELRY_NECK", SHOP_SEARCH_SUB_JEWELRY_NECK);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_JEWELRY_WRIST", SHOP_SEARCH_SUB_JEWELRY_WRIST);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_JEWELRY_BOOTS", SHOP_SEARCH_SUB_JEWELRY_BOOTS);

	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HORSE_LEARN", SHOP_SEARCH_SUB_HORSE_LEARN);
	PyModule_AddIntConstant(poModule, "SHOP_SEARCH_SUB_HORSE_OTHER", SHOP_SEARCH_SUB_HORSE_OTHER);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
