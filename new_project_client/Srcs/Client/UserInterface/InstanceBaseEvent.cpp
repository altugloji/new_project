#include "StdAfx.h"
#include "InstanceBase.h"

CActorInstance::IEventHandler& CInstanceBase::GetEventHandlerRef()
{
	return M_GTI.__GetEventHandlerRef();
}

CActorInstance::IEventHandler* CInstanceBase::GetEventHandlerPtr()
{
	return M_GTI.__GetEventHandlerPtr();
}

void CInstanceBase::SetEventHandler(CActorInstance::IEventHandler* pkEventHandler)
{
	M_GTI.SetEventHandler(pkEventHandler);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
