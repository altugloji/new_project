#pragma once

#ifdef ENABLE_WIKI
#include "../gamelib/ItemManager.h"
#include "../gamelib/ItemData.h"
#include "../gamelib/RaceData.h"
#include "PythonNonPlayer.h"

enum {
	MAX_REFINE_ITEM = 5,
};

typedef struct r_table {
	DWORD id;
	DWORD item_vnums[MAX_REFINE_ITEM];
	DWORD item_count[MAX_REFINE_ITEM];
	long long cost;
	//DWORD src_num;
	//DWORD result_vnum;
	DWORD prob;
	DWORD refine_count;
} refineTable;

typedef struct refine_map {
	DWORD	itemVnum;
	DWORD	level;
	refine_map(DWORD _vnum, DWORD _level) :itemVnum(_vnum), level(_level) {}
} character_data;

typedef struct special_map {
	DWORD	itemVnum;
	DWORD	count;
	special_map(DWORD _vnum, DWORD _count):itemVnum(_vnum),count(_count){}
} special_data;

constexpr DWORD bossChests[][2] = {
	{50082,1093},
	{50082,1093},
	{50082,1093},
	{50082,1093},
	{50082,1093},
	{50082,1093},
	{50082,1093},
	{50082,1093},
};

constexpr DWORD eventChests[][2] = {
	{50082,0},
};

constexpr DWORD alternativeChests[][2] = {
	{50082,0},
};

constexpr DWORD eventBoss[] = {
	1093,
	2493
};

const std::map<BYTE, std::vector<DWORD>> m_CostumeData = {

	{0, //Weapon
		{
			40136,
		}
	},

	{1, //Armor
		{
			41324,
			41325,
			41326,
			41327,
		}
	},
	{2, //Hair
		{
			45162,
		}
	},

	{3, //Sash
		{
			85001,
		}
	},
	{4, //Shining
		{
			65000,
			65100,
		}
	},
	{5, //Pet
		{
			53002,
		}
	},
	{6, //Mount
		{
			71224,
		}
	},
};

class CPythonWiki : public CSingleton <CPythonWiki>
{
public:
	CPythonWiki();
	virtual ~CPythonWiki();

	void	ReadData(const char* localeFile);
	bool	LoadItemTable(const char* c_szFileName);
	bool	LoadRefineTable(const char* c_szFileName);
	void	LoadItem(CItemData::TItemTable* item);
	void	LoadMonster(CPythonNonPlayer::TMobTable* monster);
	void	ListReverse();

	bool	ReadSpecialDropItemFile(const char* c_pszFileName);
	bool	ReadMobDropItemFile(const char* c_pszFileName);

	const refineTable* GetRefineItem(DWORD index);

	BYTE	GetRefineLevel(DWORD itemVnum, DWORD itemType, DWORD itemSubType);
	bool	ItemBlackList(DWORD itemVnum, DWORD itemType, DWORD itemSubType);

	bool	BlackListMonster(DWORD mobVnum);

	const std::unordered_map<DWORD, std::vector<special_data>> GetSpecialDrop() {return m_vecSpecialDrop;}
	const std::unordered_map<DWORD, std::vector<special_data>> GetMobDrop() {return m_vecMobDrop;}

	std::vector<character_data> m_vecBossCategory[3];
	std::vector<character_data> m_vecMonsterCategory[3];
	std::vector<character_data> m_vecStoneCategory[3];

	std::vector<character_data> m_vecWeapon[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecArmor[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecHelmets[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecShields[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecEarrings[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecBracelet[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecNecklace[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecShoes[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecBelt[CRaceData::JOB_MAX_NUM];
	std::vector<character_data> m_vecTalisman[CRaceData::JOB_MAX_NUM];

	std::unordered_map<DWORD, std::vector<special_data>> m_vecSpecialDrop;
	std::unordered_map<DWORD, std::vector<special_data>> m_vecMobDrop;

	bool	m_bLoaded;
	std::unordered_map<DWORD, refineTable> m_vecRefineTable;	
};
#endif
