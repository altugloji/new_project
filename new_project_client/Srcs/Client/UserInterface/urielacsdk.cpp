#include "stdafx.h"
#include "PythonNetworkStream.h"
#include "PythonCharacterManager.h"
#include "urielacsdk.h"

void UrielAntiCheat::SendPacket(const char* buff, size_t size)
{
	CPythonNetworkStream::Instance().Send(size, buff);
}

void* UrielAntiCheat::GetMainCharacter()
{
	return CPythonCharacterManager::Instance().GetMainInstancePtr();
}
