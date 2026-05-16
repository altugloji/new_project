#ifndef __INC_CHAR_CHARACTER_CHEST_H__
#define __INC_CHAR_CHARACTER_CHEST_H__

#ifdef ENABLE_CHARACTER_CHEST

#include "../../common/character_chest.h"
#include "../../common/tables.h"

class CHARACTER;
class CItem;
class DESC;

namespace character_chest
{
	bool UseChestItem(CHARACTER* ch, CItem* item);
	void SendList(CHARACTER* ch, CItem* item);
	void SendPack(CHARACTER* ch, DWORD targetPid, const char* password, CItem* item);
	void SendUnpack(CHARACTER* ch, CItem* item);
	void SendPreview(CHARACTER* ch, DWORD packedPid, CItem* item);
	void SendRemotePreview(CHARACTER* ch, DWORD packedPid);
	void OnDBPacket(DESC* d, const TPacketDGCharacterChest* pack);
	void KickPID(DWORD pid);
	void RefreshSelectCharacterList(DESC* d);
}

#endif
#endif
