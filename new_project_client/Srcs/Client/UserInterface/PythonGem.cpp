#include "StdAfx.h"

#ifdef __GEM_SHOP__
#include "PythonGem.h"

CPythonGem::CPythonGem()
{
	Clear();
}

void CPythonGem::Clear()
{
	m_bSlotCount = 0;
	m_iRefreshTime = 0;
	m_vecGemItems.clear();
}

bool CPythonGem::IsSlotOpened(BYTE bPos)
{
	if (bPos >= GEM_SLOT_COUNT)
	{
		if (m_bSlotCount < ((bPos - GEM_SLOT_COUNT) + 1))
			return false;
	}
	return true;
}
TGemItem* CPythonGem::GetItem(BYTE bPos)
{
	for (auto& item : m_vecGemItems)
	{
		if (item.bPos == bPos)
			return &item;
	}
	return NULL;
}

TGemConvertItem* CPythonGem::GetConvertItem(BYTE bPos)
{
	for (auto& item : m_vecGemConvertItems)
	{
		if (item.bPos == bPos)
			return &item;
	}
	return NULL;
}

PyObject* gemClear(PyObject* poSelf, PyObject* poArgs)
{
	CPythonGem::Instance().Clear();
	return Py_BuildNone();
}

PyObject* gemGetItem(PyObject* poSelf, PyObject* poArgs)
{
	int iSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iSlotIndex))
		return Py_BuildException();
	const TGemItem* pItem = CPythonGem::Instance().GetItem(static_cast<BYTE>(iSlotIndex));
	if (pItem)
	{
		return Py_BuildValue("iiii", pItem->dwVnum, pItem->dwCount, pItem->dwPrice, pItem->bBuyed);
	}
	return Py_BuildValue("iiii", 0, 0, 0, 0);
}

PyObject* gemGetSlotCount(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonGem::Instance().GetSlotCount());
}

PyObject* gemGetRefreshTime(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonGem::Instance().GetRefreshTime());
}

PyObject* gemSetRefreshTime(PyObject* poSelf, PyObject* poArgs)
{
	int iTime;
	if (!PyTuple_GetInteger(poArgs, 0, &iTime))
		return Py_BuildException();
	CPythonGem::Instance().SetRefreshTime(iTime);
	return Py_BuildNone();
}

PyObject* gemIsSlotOpened(PyObject* poSelf, PyObject* poArgs)
{
	int iSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iSlotIndex))
		return Py_BuildException();
	return Py_BuildValue("i", CPythonGem::Instance().IsSlotOpened(static_cast<BYTE>(iSlotIndex)));
}

PyObject* gemGetConvertItem(PyObject* poSelf, PyObject* poArgs)
{
	int iSlotIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iSlotIndex))
		return Py_BuildException();
	const TGemConvertItem* pItem = CPythonGem::Instance().GetConvertItem(static_cast<BYTE>(iSlotIndex));
	if (pItem)
	{
		return Py_BuildValue("iii", pItem->dwVnum, pItem->dwCount, pItem->dwPrice);
	}
	return Py_BuildValue("iii", 0, 0, 0);
}

PyObject* gemGetIconPtr(PyObject* poSelf, PyObject* poArgs)
{
	char* szIconFile;
	if (!PyTuple_GetString(poArgs, 0, &szIconFile))
		return Py_BadArgument();
	CGraphicImage* pImage = (CGraphicImage*)CResourceManager::Instance().GetResourcePointer(szIconFile);
	if (!pImage)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", pImage);
}

void initgem()
{
	static PyMethodDef s_methods[] =
	{
		{ "Clear", gemClear, METH_VARARGS },
		{ "GetItem", gemGetItem, METH_VARARGS },
		{ "GetSlotCount", gemGetSlotCount, METH_VARARGS },
		{ "GetRefreshTime", gemGetRefreshTime, METH_VARARGS },
		{ "SetRefreshTime", gemSetRefreshTime, METH_VARARGS },
		{ "IsSlotOpened", gemIsSlotOpened, METH_VARARGS },
		{ "GetConvertItem", gemGetConvertItem, METH_VARARGS },
		{ "GetIconPtr", gemGetIconPtr, METH_VARARGS },
		{ NULL, NULL, NULL },
	};
	PyObject* poModule = Py_InitModule("gem", s_methods);

	PyModule_AddIntConstant(poModule, "X_GRID", GEM_X_GRID);
	PyModule_AddIntConstant(poModule, "Y_GRID", GEM_Y_GRID);
	PyModule_AddIntConstant(poModule, "SLOT_COUNT", GEM_SLOT_COUNT);
	PyModule_AddIntConstant(poModule, "PAGE_COUNT", GEM_PAGE_COUNT);
	PyModule_AddIntConstant(poModule, "CONVERT_X_GRID", GEM_CONVERT_X_GRID);
	PyModule_AddIntConstant(poModule, "CONVERT_Y_GRID", GEM_CONVERT_Y_GRID);
}
#endif
