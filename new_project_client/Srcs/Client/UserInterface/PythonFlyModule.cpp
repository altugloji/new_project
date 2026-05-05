#include "stdafx.h"
#include "../gamelib/FlyingObjectManager.h"
PyObject * flyUpdate(PyObject * poSelf, PyObject * poArgs)
{
	CFlyingManager::Instance().Update();
	return Py_BuildNone();
}

PyObject * flyRender(PyObject * poSelf, PyObject * poArgs)
{
	CFlyingManager::Instance().Render();
	return Py_BuildNone();
}

void initfly()
{
	static PyMethodDef s_methods[] =
	{
		{ "Update",						flyUpdate,					METH_VARARGS },
		{ "Render",						flyRender,					METH_VARARGS },

		{nullptr, nullptr},
	};

	Py_InitModule("fly", s_methods);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
