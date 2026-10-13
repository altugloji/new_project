#include "StdAfx.h"
#include "../EffectLib/EffectManager.h"
#include "Packet.h"
#include "PythonCharacterManager.h"

PyObject * effectRegisterEffect(PyObject * poSelf, PyObject * poArgs)
{
	char * szFileName;
	if (!PyTuple_GetString(poArgs, 0, &szFileName))
		return Py_BuildException();

	CEffectManager::Instance().RegisterEffect(szFileName);
	return Py_BuildNone();
}

PyObject * effectUpdate(PyObject * poSelf, PyObject * poArgs)
{
	CEffectManager::Instance().Update();
	return Py_BuildNone();
}

PyObject * effectRender(PyObject * poSelf, PyObject * poArgs)
{
	CEffectManager::Instance().Render();
	return Py_BuildNone();
}

PyObject * effectCreateEffect(PyObject * poSelf, PyObject * poArgs)
{
	char * szEffectName;
	if (!PyTuple_GetString(poArgs, 0, &szEffectName))
		return Py_BuildException();

	CInstanceBase * pInstance = CPythonCharacterManager::Instance().GetSelectedInstancePtr();
	// ifdef'siz bugfix: secili karakter yokken (secim/yukleme fazi) null deref yerine -1 don
	if (!pInstance)
		return Py_BuildValue("i", -1);

	TPixelPosition PixelPosition;
	pInstance->NEW_GetPixelPosition(&PixelPosition);
	const int iIndex = CEffectManager::Instance().CreateEffect(szEffectName, PixelPosition, D3DXVECTOR3(0.0f, 0.0f, 0.0f));

	return Py_BuildValue("i", iIndex);
}

PyObject * effectDeleteEffect(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();

	CEffectManager::Instance().DestroyEffectInstance(iIndex);

	return Py_BuildNone();
}

PyObject * effectSetPosition(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	float fx;
	if (!PyTuple_GetFloat(poArgs, 1, &fx))
		return Py_BuildException();
	float fy;
	if (!PyTuple_GetFloat(poArgs, 2, &fy))
		return Py_BuildException();
	float fz;
	if (!PyTuple_GetFloat(poArgs, 3, &fz))
		return Py_BuildException();

	CEffectManager::Instance().SelectEffectInstance(iIndex);
	CEffectManager::Instance().SetEffectInstancePosition(D3DXVECTOR3(fx, fy, fz));

	return Py_BuildNone();
}

PyObject * effectRegisterIndexedFlyData(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	int iType;
	if (!PyTuple_GetInteger(poArgs, 1, &iType))
		return Py_BuildException();
	char * szFlyDataName;
	if (!PyTuple_GetString(poArgs, 2, &szFlyDataName))
		return Py_BuildException();

	CFlyingManager::Instance().RegisterIndexedFlyData(iIndex, iType, szFlyDataName);

	return Py_BuildNone();
}

#ifdef ENABLE_ORB_EVENT
// Kure Avi: dunya koordinatinda (local cm) serbest efekt olusturma / tasima / yasam kontrolu.
// Python pozitif local y gonderir; client dunyasi -y kullanir (bkz. PythonItem.cpp CreateEffect(D3DXVECTOR3(x, -y, z))).
// CreateEffect kayitsiz efektte bile indeks dondurur (CreateEffectInstance sessizce instance uretmez);
// bu yuzden once RegisterEffect (idempotent: kayitliysa TRUE) ve ardindan SelectEffectInstance ile dogrulama yapilir.
PyObject * effectCreateWorld(PyObject * poSelf, PyObject * poArgs)
{
	char * szFileName;
	if (!PyTuple_GetString(poArgs, 0, &szFileName))
		return Py_BuildException();
	float fx;
	if (!PyTuple_GetFloat(poArgs, 1, &fx))
		return Py_BuildException();
	float fy;
	if (!PyTuple_GetFloat(poArgs, 2, &fy))
		return Py_BuildException();
	float fz;
	if (!PyTuple_GetFloat(poArgs, 3, &fz))
		return Py_BuildException();

	CEffectManager & rkEftMgr = CEffectManager::Instance();
	if (!rkEftMgr.RegisterEffect(szFileName))
		return Py_BuildValue("i", -1);

	const int iIndex = rkEftMgr.CreateEffect(szFileName, D3DXVECTOR3(fx, -fy, fz), D3DXVECTOR3(0.0f, 0.0f, 0.0f));
	if (!rkEftMgr.SelectEffectInstance(iIndex))
		return Py_BuildValue("i", -1);

	return Py_BuildValue("i", iIndex);
}

PyObject * effectMoveWorld(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	float fx;
	if (!PyTuple_GetFloat(poArgs, 1, &fx))
		return Py_BuildException();
	float fy;
	if (!PyTuple_GetFloat(poArgs, 2, &fy))
		return Py_BuildException();
	float fz;
	if (!PyTuple_GetFloat(poArgs, 3, &fz))
		return Py_BuildException();

	CEffectManager & rkEftMgr = CEffectManager::Instance();
	if (!rkEftMgr.SelectEffectInstance(iIndex))
		return Py_BuildValue("i", 0);

	D3DXMATRIX mat;
	D3DXMatrixTranslation(&mat, fx, -fy, fz);
	rkEftMgr.SetEffectInstanceGlobalMatrix(mat);

	return Py_BuildValue("i", 1);
}

PyObject * effectIsAlive(PyObject * poSelf, PyObject * poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();

	return Py_BuildValue("i", CEffectManager::Instance().IsAliveEffect(iIndex) ? 1 : 0);
}
#endif

void initeffect()
{
	static PyMethodDef s_methods[] =
	{
		{ "RegisterEffect",				effectRegisterEffect,			METH_VARARGS },
		{ "CreateEffect",				effectCreateEffect,				METH_VARARGS },
		{ "DeleteEffect",				effectDeleteEffect,				METH_VARARGS },
		{ "SetPosition",				effectSetPosition,				METH_VARARGS },
#ifdef ENABLE_ORB_EVENT
		{ "CreateWorld",				effectCreateWorld,				METH_VARARGS },
		{ "MoveWorld",					effectMoveWorld,					METH_VARARGS },
		{ "IsAlive",					effectIsAlive,					METH_VARARGS },
#endif

		{ "RegisterIndexedFlyData",		effectRegisterIndexedFlyData,	METH_VARARGS },

		{ "Update",						effectUpdate,					METH_VARARGS },
		{ "Render",						effectRender,					METH_VARARGS },

		{nullptr, nullptr},
	};

	PyObject * poModule = Py_InitModule("effect", s_methods);
	PyModule_AddIntConstant(poModule, "INDEX_FLY_TYPE_NORMAL",			CFlyingManager::INDEX_FLY_TYPE_NORMAL);
	PyModule_AddIntConstant(poModule, "INDEX_FLY_TYPE_FIRE_CRACKER",	CFlyingManager::INDEX_FLY_TYPE_FIRE_CRACKER);
	PyModule_AddIntConstant(poModule, "INDEX_FLY_TYPE_AUTO_FIRE",		CFlyingManager::INDEX_FLY_TYPE_AUTO_FIRE);

	PyModule_AddIntConstant(poModule, "FLY_NONE",				FLY_NONE);
	PyModule_AddIntConstant(poModule, "FLY_EXP",				FLY_EXP);
	PyModule_AddIntConstant(poModule, "FLY_HP_MEDIUM",			FLY_HP_MEDIUM);
	PyModule_AddIntConstant(poModule, "FLY_HP_BIG",				FLY_HP_BIG);
	PyModule_AddIntConstant(poModule, "FLY_SP_SMALL",			FLY_SP_SMALL);
	PyModule_AddIntConstant(poModule, "FLY_SP_MEDIUM",			FLY_SP_MEDIUM);
	PyModule_AddIntConstant(poModule, "FLY_SP_BIG",				FLY_SP_BIG);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK1",			FLY_FIREWORK1);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK2",			FLY_FIREWORK2);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK3",			FLY_FIREWORK3);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK4",			FLY_FIREWORK4);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK5",			FLY_FIREWORK5);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK6",			FLY_FIREWORK6);
	PyModule_AddIntConstant(poModule, "FLY_FIREWORK_XMAS",		FLY_FIREWORK_XMAS);
	PyModule_AddIntConstant(poModule, "FLY_CHAIN_LIGHTNING",	FLY_CHAIN_LIGHTNING);
	PyModule_AddIntConstant(poModule, "FLY_HP_SMALL",			FLY_HP_SMALL);
	PyModule_AddIntConstant(poModule, "FLY_SKILL_MUYEONG",		FLY_SKILL_MUYEONG);
#ifdef ENABLE_QUIVER_SYSTEM
	PyModule_AddIntConstant(poModule, "FLY_QUIVER_ATTACK_NORMAL",	FLY_QUIVER_ATTACK_NORMAL);
#endif
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
