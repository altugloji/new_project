#include "StdAfx.h"
#ifdef ENABLE_IKASHOP_SEARCH
#include "PythonIkaShopSearch.h"
#include "PythonNetworkStream.h"
#include "../GameLib/ItemManager.h"

// ============================================================================
// 'ikashop' python modulu - uiikashopsearch.py bu API ile konusur.
// Sonuc verisi binary'de durur; getter'larla okunur (safetrade kalibi).
// ============================================================================

PyObject * ikashopSendFilterRequest(PyObject * poSelf, PyObject * poArgs)
{
	char * szName;
	int iType, iSubType, iPriceMin, iPriceMax, iLevelMin, iLevelMax;

	if (!PyTuple_GetString(poArgs, 0, &szName))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &iType))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 2, &iSubType))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 3, &iPriceMin))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 4, &iPriceMax))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 5, &iLevelMin))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 6, &iLevelMax))
		return Py_BuildException();

	CPythonNetworkStream::Instance().SendIkaShopFilterRequest(szName, iType, iSubType,
		(DWORD) MAX(0, iPriceMin), (DWORD) MAX(0, iPriceMax), iLevelMin, iLevelMax);

	return Py_BuildNone();
}

PyObject * ikashopClearFilterAttrs(PyObject * poSelf, PyObject * poArgs)
{
	CPythonIkaShopSearch::Instance().ClearFilterAttrs();
	return Py_BuildNone();
}

PyObject * ikashopSetFilterAttr(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex, iAttrType, iValue;

	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &iAttrType))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 2, &iValue))
		return Py_BuildException();

	CPythonIkaShopSearch::Instance().SetFilterAttr(iIndex, (BYTE) iAttrType, (short) iValue);
	return Py_BuildNone();
}

PyObject * ikashopSendFillRequest(PyObject * poSelf, PyObject * poArgs)
{
	CPythonNetworkStream::Instance().SendIkaShopFillRequest();
	return Py_BuildNone();
}

PyObject * ikashopSendBuyItem(PyObject * poSelf, PyObject * poArgs)
{
	int iOwnerPID, iItemDBID, iSeenPrice;

	if (!PyTuple_GetInteger(poArgs, 0, &iOwnerPID))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &iItemDBID))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 2, &iSeenPrice))
		return Py_BuildException();

	CPythonNetworkStream::Instance().SendIkaShopBuyPacket((DWORD) iOwnerPID, (DWORD) iItemDBID, (DWORD) iSeenPrice);
	return Py_BuildNone();
}

PyObject * ikashopSendViewShop(PyObject * poSelf, PyObject * poArgs)
{
	int iOwnerPID;

	if (!PyTuple_GetInteger(poArgs, 0, &iOwnerPID))
		return Py_BuildException();

	CPythonNetworkStream::Instance().SendIkaShopViewShopPacket((DWORD) iOwnerPID);
	return Py_BuildNone();
}

// ---------------------------------------------------------------------------
// Sonuc getter'lari
// ---------------------------------------------------------------------------

PyObject * ikashopGetResultCount(PyObject * poSelf, PyObject * poArgs)
{
	return Py_BuildValue("i", CPythonIkaShopSearch::Instance().GetResultCount());
}

static const SIkaSearchResult * __GetResultArg(PyObject * poArgs)
{
	int i;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return NULL;
	return CPythonIkaShopSearch::Instance().GetResult(i);
}

PyObject * ikashopGetResultItemDBID(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? (int) p->dwItemDBID : 0);
}

PyObject * ikashopGetResultOwnerPID(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? (int) p->dwOwnerPID : 0);
}

PyObject * ikashopGetResultShopName(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("s", p ? p->szShopName : "");
}

PyObject * ikashopGetResultChannel(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? (int) p->bChannel : 0);
}

PyObject * ikashopGetResultMapIndex(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? p->iMapIndex : 0);
}

PyObject * ikashopGetResultVnum(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? (int) p->dwVnum : 0);
}

PyObject * ikashopGetResultItemCount(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? (int) p->bCount : 0);
}

PyObject * ikashopGetResultPrice(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? (int) p->dwPrice : 0);
}

PyObject * ikashopGetResultDurationMin(PyObject * poSelf, PyObject * poArgs)
{
	const SIkaSearchResult * p = __GetResultArg(poArgs);
	return Py_BuildValue("i", p ? p->iDurationMin : 0);
}

PyObject * ikashopGetResultSocket(PyObject * poSelf, PyObject * poArgs)
{
	int i, idx;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &idx))
		return Py_BuildException();

	const SIkaSearchResult * p = CPythonIkaShopSearch::Instance().GetResult(i);
	if (!p || idx < 0 || idx >= ITEM_SOCKET_SLOT_MAX_NUM)
		return Py_BuildValue("i", 0);

	return Py_BuildValue("i", p->aiSockets[idx]);
}

PyObject * ikashopGetResultAttr(PyObject * poSelf, PyObject * poArgs)
{
	int i, idx;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &idx))
		return Py_BuildException();

	const SIkaSearchResult * p = CPythonIkaShopSearch::Instance().GetResult(i);
	if (!p || idx < 0 || idx >= ITEM_ATTRIBUTE_SLOT_MAX_NUM)
		return Py_BuildValue("(ii)", 0, 0);

	return Py_BuildValue("(ii)", (int) p->aAttrs[idx].bType, (int) p->aAttrs[idx].sValue);
}

PyObject * ikashopFindResultByDBID(PyObject * poSelf, PyObject * poArgs)
{
	int iItemDBID;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemDBID))
		return Py_BuildException();

	return Py_BuildValue("i", CPythonIkaShopSearch::Instance().FindResultByDBID((DWORD) iItemDBID));
}

// ---------------------------------------------------------------------------
// Isim onerileri (arama kutusu combobox'u)
// ---------------------------------------------------------------------------

PyObject * ikashopGetNameSuggestions(PyObject * poSelf, PyObject * poArgs)
{
	char * szKeyword;
	int iMaxCount;

	if (!PyTuple_GetString(poArgs, 0, &szKeyword))
		return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &iMaxCount))
		return Py_BuildException();

	if (iMaxCount <= 0 || iMaxCount > 50)
		iMaxCount = 10;

	std::vector<std::string> vecNames;
	CItemManager::Instance().CollectNamesByKeyword(szKeyword, (DWORD) iMaxCount, vecNames);

	PyObject * poTuple = PyTuple_New((int) vecNames.size());
	for (int i = 0; i < (int) vecNames.size(); ++i)
		PyTuple_SetItem(poTuple, i, PyString_FromString(vecNames[i].c_str()));

	return poTuple;
}

void initikashop()
{
	static PyMethodDef s_methods[] =
	{
		{ "SendFilterRequest",		ikashopSendFilterRequest,		METH_VARARGS },
		{ "SendFillRequest",		ikashopSendFillRequest,			METH_VARARGS },
		{ "ClearFilterAttrs",		ikashopClearFilterAttrs,		METH_VARARGS },
		{ "SetFilterAttr",			ikashopSetFilterAttr,			METH_VARARGS },
		{ "SendBuyItem",			ikashopSendBuyItem,				METH_VARARGS },
		{ "SendViewShop",			ikashopSendViewShop,			METH_VARARGS },
		{ "GetResultCount",			ikashopGetResultCount,			METH_VARARGS },
		{ "GetResultItemDBID",		ikashopGetResultItemDBID,		METH_VARARGS },
		{ "GetResultOwnerPID",		ikashopGetResultOwnerPID,		METH_VARARGS },
		{ "GetResultShopName",		ikashopGetResultShopName,		METH_VARARGS },
		{ "GetResultChannel",		ikashopGetResultChannel,		METH_VARARGS },
		{ "GetResultMapIndex",		ikashopGetResultMapIndex,		METH_VARARGS },
		{ "GetResultVnum",			ikashopGetResultVnum,			METH_VARARGS },
		{ "GetResultItemCount",		ikashopGetResultItemCount,		METH_VARARGS },
		{ "GetResultPrice",			ikashopGetResultPrice,			METH_VARARGS },
		{ "GetResultDurationMin",	ikashopGetResultDurationMin,	METH_VARARGS },
		{ "GetResultSocket",		ikashopGetResultSocket,			METH_VARARGS },
		{ "GetResultAttr",			ikashopGetResultAttr,			METH_VARARGS },
		{ "FindResultByDBID",		ikashopFindResultByDBID,		METH_VARARGS },
		{ "GetNameSuggestions",		ikashopGetNameSuggestions,		METH_VARARGS },
		{ nullptr, nullptr, 0 },
	};

	PyObject * poModule = Py_InitModule("ikashop", s_methods);
	PyModule_AddIntConstant(poModule, "FILTER_ATTR_NUM", IKASEARCH_FILTER_ATTR_NUM);
	PyModule_AddIntConstant(poModule, "FILTER_NAME_MAX_LEN", IKASEARCH_FILTER_NAME_LEN - 1);
	PyModule_AddIntConstant(poModule, "MAX_RESULTS", IKASEARCH_MAX_RESULTS);
}
#endif
