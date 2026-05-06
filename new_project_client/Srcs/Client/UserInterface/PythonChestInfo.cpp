#include "StdAfx.h"

#ifdef KYGN_CHEST_INFO
#include "InstanceBase.h"
#include "PythonChestInfo.h"
#include "PythonNetworkStream.h"
#include "PythonCharacterManager.h"

#include "../gamelib/ItemData.h"
#include "../gamelib/ItemManager.h"



void CPythonChestInfo::SetGameWindow(PyObject* ppyObject) { m_ppyGameWindow = ppyObject; }

void CPythonChestInfo::GetChestRewardInfo(DWORD dwVnum)
{
	if (SetChestRewardData(dwVnum))
		return;

	if (lastSendingVnum == dwVnum)
		return;

	lastSendingVnum = dwVnum;
	CPythonNetworkStream::Instance().SendCGGetChestRewards(dwVnum);
}

bool CPythonChestInfo::SetChestRewardData(DWORD dwVnum)
{
	auto it = map_ChestRewardInfo.find(dwVnum);
	if (it == map_ChestRewardInfo.end())
		return false;

	PyCallClassMemberFunc(m_ppyGameWindow, "ClearChestRewardData", Py_BuildValue("()"));
	for (const auto& data : it->second)
		PyCallClassMemberFunc(m_ppyGameWindow, "SetChestRewardData", Py_BuildValue("(ii)", data.dwVnum, data.iCount));

	PyCallClassMemberFunc(m_ppyGameWindow, "ShowChestRewardData", Py_BuildValue("()"));
	return true;
}

void CPythonChestInfo::SortChestRewardList(DWORD dwVnum)
{
	auto it = map_ChestRewardInfo.find(dwVnum);
	if (it == map_ChestRewardInfo.end())
		return;

	std::sort(it->second.begin(), it->second.end(), [](const TChestRewards& a, const TChestRewards& b) {
				CItemData* aData = nullptr, * bData = nullptr;
				if (!CItemManager::Instance().GetItemDataPointer(a.dwVnum, &aData)) return true;
				if (!CItemManager::Instance().GetItemDataPointer(b.dwVnum, &bData)) return false;
				return bData->GetSize() > aData->GetSize();
			}
		);
}

PyObject* criSetGameWindow(PyObject* poSelf, PyObject* poArgs)
{
	PyObject* pyHandle;
	if (!PyTuple_GetObject(poArgs, 0, &pyHandle))
		return Py_BadArgument();

	CPythonChestInfo::Instance().SetGameWindow(pyHandle);
	return Py_BuildNone();
}

PyObject* criGetChestRewardInfo(PyObject* poSelf, PyObject* poArgs)
{
	int dwVnum = 0;
	if (!PyTuple_GetInteger(poArgs, 0, &dwVnum))
		return Py_BuildException();

	CPythonChestInfo::Instance().GetChestRewardInfo(dwVnum);
	return Py_BuildNone();
}

void initChestRewardInfo()
{
	static PyMethodDef s_methods[] =
	{
		{ "SetGameWindow",			criSetGameWindow,				METH_VARARGS },
		{ "GetChestRewardInfo",		criGetChestRewardInfo,			METH_VARARGS },
		{ NULL,						NULL,							NULL },
	};

	Py_InitModule("cri", s_methods);
}
#endif
