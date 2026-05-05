#include "StdAfx.h"
#include "Mutex.h"

Mutex::Mutex()
{
	InitializeCriticalSection(&lock);
}

Mutex::~Mutex()
{
	DeleteCriticalSection(&lock);
}

void Mutex::Lock()
{
	EnterCriticalSection(&lock);
}

void Mutex::Unlock()
{
	LeaveCriticalSection(&lock);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
