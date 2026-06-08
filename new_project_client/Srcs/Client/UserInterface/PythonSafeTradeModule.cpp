#include "StdAfx.h"
#ifdef ENABLE_SAFE_TRADE_SYSTEM
#include "PythonSafeTrade.h"

PyObject* safetradeGetDepotItemID(PyObject* poSelf, PyObject* poArgs)
{
	int slot;
	if (!PyTuple_GetInteger(poArgs, 0, &slot))
		return Py_BuildException();
	return Py_BuildValue("i", CPythonSafeTrade::Instance().GetDepotItem((BYTE)slot).vnum);
}

PyObject* safetradeGetDepotItemCount(PyObject* poSelf, PyObject* poArgs)
{
	int slot;
	if (!PyTuple_GetInteger(poArgs, 0, &slot))
		return Py_BuildException();
	return Py_BuildValue("i", CPythonSafeTrade::Instance().GetDepotItem((BYTE)slot).count);
}

PyObject* safetradeGetDepotItemMetinSocket(PyObject* poSelf, PyObject* poArgs)
{
	int slot, idx;
	if (!PyTuple_GetInteger(poArgs, 0, &slot))  return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &idx))   return Py_BuildException();
	if (idx < 0 || idx >= ITEM_SOCKET_SLOT_MAX_NUM)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonSafeTrade::Instance().GetDepotItem((BYTE)slot).alSockets[idx]);
}

PyObject* safetradeGetDepotItemAttribute(PyObject* poSelf, PyObject* poArgs)
{
	int slot, idx;
	if (!PyTuple_GetInteger(poArgs, 0, &slot))  return Py_BuildException();
	if (!PyTuple_GetInteger(poArgs, 1, &idx))   return Py_BuildException();
	if (idx < 0 || idx >= ITEM_ATTRIBUTE_SLOT_MAX_NUM)
		return Py_BuildValue("(ii)", 0, 0);
	const TItemData& d = CPythonSafeTrade::Instance().GetDepotItem((BYTE)slot);
	return Py_BuildValue("(ii)", d.aAttr[idx].bType, d.aAttr[idx].sValue);
}

PyObject* safetradeGetListCount(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonSafeTrade::Instance().GetListCount());
}

PyObject* safetradeGetListTradeID(PyObject* poSelf, PyObject* poArgs)
{
	int i;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return Py_BuildException();
	const CPythonSafeTrade::TListEntry* e = CPythonSafeTrade::Instance().GetListEntry(i);
	return Py_BuildValue("i", e ? e->tradeID : 0);
}

PyObject* safetradeGetListSenderName(PyObject* poSelf, PyObject* poArgs)
{
	int i;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return Py_BuildException();
	const CPythonSafeTrade::TListEntry* e = CPythonSafeTrade::Instance().GetListEntry(i);
	return Py_BuildValue("s", e ? e->sender : "");
}

PyObject* safetradeGetListItemCount(PyObject* poSelf, PyObject* poArgs)
{
	int i;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return Py_BuildException();
	const CPythonSafeTrade::TListEntry* e = CPythonSafeTrade::Instance().GetListEntry(i);
	return Py_BuildValue("i", e ? e->itemCount : 0);
}

PyObject* safetradeGetListIsOwner(PyObject* poSelf, PyObject* poArgs)
{
	int i;
	if (!PyTuple_GetInteger(poArgs, 0, &i))
		return Py_BuildException();
	const CPythonSafeTrade::TListEntry* e = CPythonSafeTrade::Instance().GetListEntry(i);
	return Py_BuildValue("i", e ? e->isOwner : 0);
}

void initSafeTrade()
{
	static PyMethodDef s_methods[] =
	{
		{ "GetDepotItemID",          safetradeGetDepotItemID,          METH_VARARGS },
		{ "GetDepotItemCount",       safetradeGetDepotItemCount,       METH_VARARGS },
		{ "GetDepotItemMetinSocket", safetradeGetDepotItemMetinSocket, METH_VARARGS },
		{ "GetDepotItemAttribute",   safetradeGetDepotItemAttribute,   METH_VARARGS },
		{ "GetListCount",            safetradeGetListCount,            METH_VARARGS },
		{ "GetListTradeID",          safetradeGetListTradeID,          METH_VARARGS },
		{ "GetListSenderName",       safetradeGetListSenderName,       METH_VARARGS },
		{ "GetListItemCount",        safetradeGetListItemCount,        METH_VARARGS },
		{ "GetListIsOwner",          safetradeGetListIsOwner,          METH_VARARGS },
		{ nullptr, nullptr, 0 },
	};

	PyObject* poModule = Py_InitModule("safetrade", s_methods);
	PyModule_AddIntConstant(poModule, "SAFE_TRADE_MAX_ITEMS", CPythonSafeTrade::SAFE_TRADE_MAX_ITEMS);
}
#endif
