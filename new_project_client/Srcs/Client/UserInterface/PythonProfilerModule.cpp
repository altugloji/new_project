#include "StdAfx.h"
#include "../eterLib/Profiler.h"

PyObject * profilerPush(PyObject * poSelf, PyObject * poArgs)
{
	char * szName;
	if (!PyTuple_GetString(poArgs, 0, &szName))
		return Py_BuildException();

	return Py_BuildNone();
}

PyObject * profilerPop(PyObject * poSelf, PyObject * poArgs)
{
	char * szName;
	if (!PyTuple_GetString(poArgs, 0, &szName))
		return Py_BuildException();

	return Py_BuildNone();
}

void initProfiler()
{
	static PyMethodDef s_methods[] =
	{
		{ "Push",				profilerPush,				METH_VARARGS },
		{ "Pop",				profilerPop,				METH_VARARGS },

		{nullptr, nullptr},
	};

	Py_InitModule("profiler", s_methods);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
