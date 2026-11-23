#pragma once

enum Protect
{
    ATTACK,
    ATTACKSPEED,
    SETATTACKKEY,
    MOVE,
    ATTACKINIT,
    ATTACKKEYINIT,
    GETUSERNAME,
    NOTHING,
    GETUNIQUEVALUE,
    GETLOGFILENAME,
    GETCRC,
    MODULE
};

#pragma pack(push)
#pragma pack(1)

typedef struct command_attack1
{
	BYTE	header;
	BYTE	bType;
	DWORD	dwVictimVID;
}TPacketAttack;
#pragma pack(pop)
#define ATTACK_HEADER 0x01

namespace rascalsvd {
	static std::map<uint32_t, std::chrono::steady_clock::time_point> client_attack_map;
}

struct RascalInitConfig
{
    const char* server_ip;
    int max_client;
    const char* license_key;
};
