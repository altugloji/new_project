#include "stdafx.h"
#include "NetBase.h"
#include "Config.h"
#include "ClientManager.h"

LPFDWATCH CNetBase::m_fdWatcher = nullptr;

CNetBase::CNetBase()
{
}

CNetBase::~CNetBase()
{
}

CNetPoller::CNetPoller()
{
}

CNetPoller::~CNetPoller()
{
	Destroy();
}

bool CNetPoller::Create()
{
	sys_log(1, "NetPoller::Create()");

	if (m_fdWatcher)
		return true;

	m_fdWatcher = fdwatch_new(512);

	if (!m_fdWatcher)
	{
		Destroy();
		return false;
	}

	return true;
}

void CNetPoller::Destroy() const
{
	sys_log(1, "NetPoller::Destroy()");

	if (m_fdWatcher)
	{
		fdwatch_delete(m_fdWatcher);
		m_fdWatcher = nullptr;
	}

	thecore_destroy();
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
