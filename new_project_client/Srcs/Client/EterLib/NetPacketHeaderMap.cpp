#include "StdAfx.h"
#include "NetPacketHeaderMap.h"

void CNetworkPacketHeaderMap::Set(int header, const TPacketType & rPacketType)
{
	m_headerMap[header] = rPacketType;
}
bool CNetworkPacketHeaderMap::Get(int header, TPacketType * pPacketType)
{
	const auto f=m_headerMap.find(header);

	if (m_headerMap.end()==f)
		return false;

	*pPacketType = f->second;

	return true;
}

CNetworkPacketHeaderMap::CNetworkPacketHeaderMap()
{
}

CNetworkPacketHeaderMap::~CNetworkPacketHeaderMap()
{
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
