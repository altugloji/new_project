#include "StdAfx.h"
#include "NetDevice.h"

CNetworkDevice::CNetworkDevice()
{
	Initialize();
}

CNetworkDevice::~CNetworkDevice()
{
	Destroy();
}

void CNetworkDevice::Initialize()
{
	m_isWSA=false;
}

void CNetworkDevice::Destroy()
{
	if (m_isWSA)
	{
		WSACleanup();
		m_isWSA=false;
	}
}

bool CNetworkDevice::Create()
{
	Destroy();

	Initialize();

	WSADATA wsaData;
	if (WSAStartup(MAKEWORD(1, 1), &wsaData)!=0)
		return false;

	m_isWSA=true;

	return true;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
