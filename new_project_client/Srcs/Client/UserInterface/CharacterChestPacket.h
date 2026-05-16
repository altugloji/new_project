#pragma once

// Client-only packet definitions (no ../../common). Keep wire layout in sync with
// common/character_chest.h on game/db when changing preview structs.

#pragma pack(push, 1)

#ifdef ENABLE_CHARACTER_CHEST

enum ECharacterChestCGSub
{
	CHARACTER_CHEST_CG_PACK = 1,
	CHARACTER_CHEST_CG_UNPACK = 2,
	CHARACTER_CHEST_CG_PREVIEW = 3,
};

enum { CHARACTER_CHEST_PREVIEW_READONLY_CELL = 0xFFFF };

enum ECharacterChestGCOp
{
	CHARACTER_CHEST_OP_LIST = 0,
	CHARACTER_CHEST_OP_PACK = 1,
	CHARACTER_CHEST_OP_UNPACK = 2,
	CHARACTER_CHEST_OP_PREVIEW = 3,
};

#ifdef ENABLE_PLAYER_PER_ACCOUNT5
enum { CHARACTER_CHEST_MAX_LIST = 5 };
#else
enum { CHARACTER_CHEST_MAX_LIST = 4 };
#endif

enum { CHARACTER_CHEST_PASSWORD_LEN = 8 };
enum { CHARACTER_CHEST_MAX_PREVIEW_ITEMS = 180 };
enum { CHARACTER_CHEST_MAX_PREVIEW_SKILLS = 64 };
enum { CHARACTER_CHEST_PREVIEW_PART_COUNT = 5 };
enum { CHARACTER_CHEST_PREVIEW_SOCKET_NUM = 3 };
enum { CHARACTER_CHEST_PREVIEW_ATTR_NUM = 7 };
enum { CHARACTER_CHEST_GC_MAX_SIZE = 16384 };
enum { CHARACTER_CHEST_PREVIEW_PLAYER_WIRE_SIZE = 78 };
enum { CHARACTER_CHEST_PREVIEW_PLAYER_LEGACY_SIZE = 76 };
enum { CHARACTER_CHEST_PREVIEW_PLAYER_WIRE_SIZE_V1 = 70 };
enum { CHARACTER_CHEST_BIOLOGIST_LEVEL_COUNT = 10 };

enum ECharacterChestBiologistStatus
{
	CHARACTER_CHEST_BIOLOGIST_NONE = 0,
	CHARACTER_CHEST_BIOLOGIST_PROGRESS = 1,
	CHARACTER_CHEST_BIOLOGIST_DONE = 2,
};

// Packed wire offsets for TCharacterChestPreviewPlayer (CHARACTER_NAME_MAX_LEN == 24).
enum ECharacterChestPreviewPlayerWireOff
{
	CHARACTER_CHEST_PREVIEW_OFF_NAME			= 0,
	CHARACTER_CHEST_PREVIEW_OFF_JOB				= 25,
	CHARACTER_CHEST_PREVIEW_OFF_LEVEL			= 26,
	CHARACTER_CHEST_PREVIEW_OFF_ST				= 27,
	CHARACTER_CHEST_PREVIEW_OFF_HT				= 29,
	CHARACTER_CHEST_PREVIEW_OFF_DX				= 31,
	CHARACTER_CHEST_PREVIEW_OFF_IQ				= 33,
	CHARACTER_CHEST_PREVIEW_OFF_EXP				= 35,
	CHARACTER_CHEST_PREVIEW_OFF_GOLD			= 39,
	CHARACTER_CHEST_PREVIEW_OFF_PLAYTIME		= 43,
	CHARACTER_CHEST_PREVIEW_OFF_PART_BASE		= 47,
	CHARACTER_CHEST_PREVIEW_OFF_PARTS			= 48,
	CHARACTER_CHEST_PREVIEW_OFF_SKILL_GROUP		= 68,
	CHARACTER_CHEST_PREVIEW_OFF_CHEQUE			= 69,
	CHARACTER_CHEST_PREVIEW_OFF_GEM				= 73,
	CHARACTER_CHEST_PREVIEW_OFF_SKILL_COUNT		= 77,
	CHARACTER_CHEST_PREVIEW_V1_OFF_SKILL_COUNT	= 69,
};

typedef struct SCharacterChestPreviewSkill
{
	WORD	wVnum;
	BYTE	bMasterType;
	BYTE	bLevel;
} TCharacterChestPreviewSkill;

typedef struct SCharacterChestPreviewItem
{
	BYTE	bWindow;
	WORD	wPos;
	DWORD	dwVnum;
	DWORD	dwCount;
	long	alSockets[CHARACTER_CHEST_PREVIEW_SOCKET_NUM];
	BYTE	aAttrType[CHARACTER_CHEST_PREVIEW_ATTR_NUM];
	short	aAttrValue[CHARACTER_CHEST_PREVIEW_ATTR_NUM];
} TCharacterChestPreviewItem;

typedef struct SCharacterChestPreviewPlayer
{
	char	szName[CHARACTER_NAME_MAX_LEN + 1];
	BYTE	bJob;
	BYTE	bLevel;
	short	sST;
	short	sHT;
	short	sDX;
	short	sIQ;
	DWORD	dwExp;
	INT		iGold;
	int		iPlaytime;
	BYTE	bPartBase;
	DWORD	adwParts[CHARACTER_CHEST_PREVIEW_PART_COUNT];
	BYTE	bSkillGroup;
	INT		iCheque;
	INT		iGem;
	BYTE	bSkillCount;
} TCharacterChestPreviewPlayer;

typedef struct SCharacterChestEntry
{
	DWORD	dwPID;
	char	szName[CHARACTER_NAME_MAX_LEN + 1];
	BYTE	byJob;
	BYTE	byLevel;
} TCharacterChestEntry;

typedef struct SPacketCGCharacterChest
{
	BYTE	bHeader;
	BYTE	bSubOp;
	DWORD	dwTargetPID;
	WORD	wItemCell;
	char	szPassword[CHARACTER_CHEST_PASSWORD_LEN];
} TPacketCGCharacterChest;

typedef struct SPacketGCCharacterChest
{
	BYTE	bHeader;
	WORD	wSize;
	BYTE	bOp;
	BYTE	bResult;
	DWORD	dwTargetPID;
	BYTE	bCount;
	WORD	wItemCell;
	char	szPackedName[CHARACTER_NAME_MAX_LEN + 1];
	union
	{
		TCharacterChestEntry entries[CHARACTER_CHEST_MAX_LIST];
		BYTE	abPayload[CHARACTER_CHEST_GC_MAX_SIZE];
	};
} TPacketGCCharacterChest;

#endif

#pragma pack(pop)
