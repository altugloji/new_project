#include "StdAfx.h"

#ifdef ENABLE_WIKI
#include "PythonWiki.h"
#include "PythonNetworkStream.h"
#include "PythonPlayer.h"
#include "../GameLib/ItemManager.h"
#include "../eterPack/EterPackManager.h"

bool printLocalDatainSysser = false;

//STATIC-FUNCTIONS
bool CompareLevel(const character_data i, const character_data j) { return (i.level > j.level); }
bool CompareLevelLow(const character_data i, const character_data j) { return (i.level < j.level); }
bool isFirstItem(DWORD itemVnum, const char* szname)
{
	const std::string str(szname);
	if (str.find("+0") != std::string::npos)
		return true;
	return false;
}
bool isLastItem(DWORD itemVnum, const char* szname, BYTE itemType)
{
	const std::string str(szname);
	std::string strrefine = "+";
	strrefine += std::to_string(CPythonWiki::Instance().GetRefineLevel(itemVnum, itemType, 0));
	if (str.find(strrefine.c_str()) != std::string::npos)
		return true;
	return false;
}

CPythonWiki::~CPythonWiki() {}
CPythonWiki::CPythonWiki() : m_bLoaded(false) {}

void CPythonWiki::ReadData(const char* localeFile)
{
	if (m_bLoaded)
		return;
	m_bLoaded = true;

	if (!LoadRefineTable("locale/common/refine_table.txt"))
		TraceError("CPythonApplication - CPythonWiki::LoadRefineTable(locale/common/refine_table.txt)");
	char szItemProto[256];
	snprintf(szItemProto, sizeof(szItemProto), "%s/item_proto", localeFile);
	if (!LoadItemTable(szItemProto))
		TraceError("CPythonWiki - LoadItemTable(%s) Error", szItemProto);
	ReadSpecialDropItemFile("locale/common/special_item_group.txt");
	ReadMobDropItemFile("locale/common/mob_drop_item.txt");
}

bool CPythonWiki::ReadSpecialDropItemFile(const char* c_pszFileName)
{
	CTextFileLoader loader;
	if (!loader.Load(c_pszFileName))
		return false;

	int iVnum;
	std::vector<special_data> vecSpecialData;
	std::string stName("");
	TTokenVector* pTok;

	for (DWORD i = 0; i < loader.GetChildNodeCount(); ++i)
	{
		loader.SetChildNode(i);
		loader.GetCurrentNodeName(&stName);
		if (!loader.GetTokenInteger("vnum", &iVnum))
		{
			TraceError("ReadSpecialDropItemFile:Syntax error %s : no vnum, node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			continue;
		}
		vecSpecialData.clear();

		for (int k = 1; k < 256; ++k)
		{
			char buf[4];
			snprintf(buf, sizeof(buf), "%d", k);
			if (loader.GetTokenVector(buf, &pTok))
			{
				vecSpecialData.emplace_back(special_data(std::stoi(pTok->at(0)), std::stoi(pTok->at(1))));
				continue;
			}
			break;
		}
		loader.SetParentNode();

		if (vecSpecialData.size())
		{
			if (printLocalDatainSysser)
			{
				TraceError("                ");
				TraceError("ChestIndex: %d", iVnum);
				for (DWORD j = 0; j < vecSpecialData.size(); ++j)
					TraceError("Chest Data - Index: %d  ItemVnum: %d ItemCount: %d", j, vecSpecialData[j].itemVnum, vecSpecialData[j].count);
			}
			m_vecSpecialDrop.emplace(iVnum, vecSpecialData);
		}
	}
	return true;
}

bool CPythonWiki::ReadMobDropItemFile(const char* c_pszFileName)
{
	CTextFileLoader loader;
	if (!loader.Load(c_pszFileName))
		return false;

	int iVnum;
	std::vector<special_data> vecSpecialData;
	std::string stName("");
	TTokenVector* pTok;

	for (DWORD i = 0; i < loader.GetChildNodeCount(); ++i)
	{
		loader.SetChildNode(i);
		loader.GetCurrentNodeName(&stName);
		if (!loader.GetTokenInteger("mob", &iVnum))
		{
			TraceError("ReadMobDropItemFile:Syntax error %s : no vnum, node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			continue;
		}
		vecSpecialData.clear();
		for (int k = 1; k < 256; ++k)
		{
			char buf[4];
			snprintf(buf, sizeof(buf), "%d", k);
			if (loader.GetTokenVector(buf, &pTok))
			{
				vecSpecialData.emplace_back(special_data(std::stoi(pTok->at(0)), std::stoi(pTok->at(1))));
				continue;
			}
			break;
		}
		loader.SetParentNode();
		if (vecSpecialData.size())
		{
			if (printLocalDatainSysser)
			{
				TraceError("                ");
				TraceError("MobIndex: %d", iVnum);
				for (DWORD j = 0; j < vecSpecialData.size(); ++j)
					TraceError("Mob Data - Index: %d  ItemVnum: %d ItemCount: %d", j, vecSpecialData[j].itemVnum, vecSpecialData[j].count);
			}
			// Ayni mob birden fazla grupta gecebilir (Type drop + Type kill + Type limit).
			// emplace var olan anahtari ezmedigi icin yalnizca ilk grup kaliyor, bu yuzden
			// "kill" gruplarindaki itemler wikide gozukmuyordu. Gruplari birlestirip ayni
			// item vnumunu tekillestiriyoruz ki tum dusen esyalar (kill dahil) listelensin.
			auto it = m_vecMobDrop.find(iVnum);
			if (it == m_vecMobDrop.end())
			{
				m_vecMobDrop.emplace(iVnum, vecSpecialData);
			}
			else
			{
				for (const auto& dataItem : vecSpecialData)
				{
					bool bAlreadyExists = false;
					for (const auto& existing : it->second)
					{
						if (existing.itemVnum == dataItem.itemVnum)
						{
							bAlreadyExists = true;
							break;
						}
					}
					if (!bAlreadyExists)
						it->second.emplace_back(dataItem);
				}
			}
		}
	}
	return true;
}

bool CPythonWiki::LoadItemTable(const char* c_szFileName)
{
	CMappedFile file;
	LPCVOID pvData;
	if (!CEterPackManager::Instance().Get(file, c_szFileName, &pvData))
		return false;
	DWORD dwFourCC, dwElements, dwDataSize, dwVersion = 0, dwStride = 0;
	DWORD s_adwItemProtoKey[4] = {173217, 72619434, 408587239, 27973291};
	file.Read(&dwFourCC, sizeof(DWORD));
	if (dwFourCC == MAKEFOURCC('M', 'I', 'P', 'X'))
	{
		file.Read(&dwVersion, sizeof(DWORD));
		file.Read(&dwStride, sizeof(DWORD));
		if (dwVersion != 1)
		{
			TraceError("CPythonItem::LoadItemTable: invalid item_proto[%s] VERSION[%d]", c_szFileName, dwVersion);
			return false;
		}
		if (dwStride != sizeof(CItemData::TItemTable))
		{
			TraceError("CPythonItem::LoadItemTable: invalid item_proto[%s] STRIDE[%d] != sizeof(SItemTable)", c_szFileName, dwStride, sizeof(CItemData::TItemTable));
			return false;
		}
	}
	else if (dwFourCC != MAKEFOURCC('M', 'I', 'P', 'T'))
	{
		TraceError("CPythonItem::LoadItemTable: invalid item proto type %s", c_szFileName);
		return false;
	}
	file.Read(&dwElements, sizeof(DWORD));
	file.Read(&dwDataSize, sizeof(DWORD));

#ifdef ENABLE_NEW_OPTIMIZATION
	std::unique_ptr<BYTE[]> pbData(new BYTE[dwDataSize]());
	file.Read(pbData.get(), dwDataSize);
	CLZObject zObj;
	if (!CLZO::Instance().Decompress(zObj, pbData.get(), s_adwItemProtoKey))
	{
#else
	BYTE* pbData = new BYTE[dwDataSize];
	file.Read(pbData, dwDataSize);
	CLZObject zObj;
	if (!CLZO::Instance().Decompress(zObj, pbData, s_adwItemProtoKey))
	{
		delete[] pbData;
#endif
		return false;
	}
	CItemData::TItemTable* table = (CItemData::TItemTable*)zObj.GetBuffer();
	for (DWORD i = 0; i < dwElements; ++i, ++table)
		CPythonWiki::Instance().LoadItem(table);
#ifndef ENABLE_NEW_OPTIMIZATION
	delete[] pbData;
#endif

	for (DWORD j = 0; j < CRaceData::JOB_MAX_NUM; j++)
	{
		std::stable_sort(m_vecWeapon[j].begin(), m_vecWeapon[j].end(), CompareLevel);
		std::stable_sort(m_vecArmor[j].begin(), m_vecArmor[j].end(), CompareLevel);
		std::stable_sort(m_vecHelmets[j].begin(), m_vecHelmets[j].end(), CompareLevel);
		std::stable_sort(m_vecShields[j].begin(), m_vecShields[j].end(), CompareLevel);
		std::stable_sort(m_vecEarrings[j].begin(), m_vecEarrings[j].end(), CompareLevel);
		std::stable_sort(m_vecBracelet[j].begin(), m_vecBracelet[j].end(), CompareLevel);
		std::stable_sort(m_vecNecklace[j].begin(), m_vecNecklace[j].end(), CompareLevel);
		std::stable_sort(m_vecShoes[j].begin(), m_vecShoes[j].end(), CompareLevel);
		std::stable_sort(m_vecBelt[j].begin(), m_vecBelt[j].end(), CompareLevel);
		std::stable_sort(m_vecTalisman[j].begin(), m_vecTalisman[j].end(), CompareLevel);
	}
	return true;
}


bool CPythonWiki::LoadRefineTable(const char* c_szFileName)
{
	CMappedFile File;
	LPCVOID pData;
	if (!CEterPackManager::Instance().Get(File, c_szFileName, &pData))
		return false;

	CMemoryTextFileLoader textFileLoader;
	textFileLoader.Bind(File.Size(), pData);

	CTokenVector TokenVector;
	for (DWORD i = 0; i < textFileLoader.GetLineCount(); ++i)
	{
		if (textFileLoader.GetLineString(i)[0] == '#')
			continue;
		if (!textFileLoader.SplitLine(i, &TokenVector, "\t"))
			continue;
		if (TokenVector.size() != 15)
		{
			TraceError("CPythonWiki::LoadRefineTable(%s) - StrangeLine in %d\n", c_szFileName, i);
			continue;
		}
		int row = 0;
		refineTable p;
		memset(&p, 0, sizeof(refineTable));

		p.id = (DWORD)atoi(TokenVector[row++].c_str());
		p.refine_count = 0;
		for (DWORD j = 0; j < MAX_REFINE_ITEM; ++j)
		{
			p.item_vnums[j] = (DWORD)atoi(TokenVector[row++].c_str());
			if (p.item_vnums[j] != 0)
				p.refine_count = j + 1;
			p.item_count[j] = (DWORD)atoi(TokenVector[row++].c_str());
		}
		p.cost = (long long)atoll(TokenVector[row++].c_str());
		row++;//src_num
		row++;//result_vnum
		p.prob = (DWORD)atoi(TokenVector[row++].c_str());
		m_vecRefineTable.emplace(p.id, p);
	}
	return true;
}

bool CPythonWiki::ItemBlackList(DWORD itemVnum, DWORD itemType, DWORD itemSubType)
{
	const std::vector<DWORD> m_BlockedItemVnumList = {
		// warrior & weapon blacklist
		9510, 9520, 3209, 219, 229, 239, 269, 3179, 3189, 7209,
		21970, 21960, 21950, 21940, 21930, 21920, 21910, 21900, 209,

		// ninja & weapon blacklist
		1149, 1159, 1169, 8000, 4039, 2199,

		// shaman & weapon blacklist
		5139, 5149, 5159, 7179, 7189,

		// armor blacklist
		11000, 11010, 11020, 11030, 13169, 13149, 13199, 13209,
		12699, 12709, 12719, 12729, 12739, 12749, 12759, 12769,

		// shield blacklist
		13189, 16509, 16529, 16579, 16549, 16569, 17579, 17549, 17529, 17509,
		15459, 14669, 14549, 14529, 14509, 14579, 15249, 17569, 14569,
		
		12679, 12549, 12409, 12289,
	};
	return std::find(m_BlockedItemVnumList.begin(), m_BlockedItemVnumList.end(), itemVnum) != m_BlockedItemVnumList.end() ? false : true;
}

BYTE CPythonWiki::GetRefineLevel(DWORD itemVnum, DWORD itemType, DWORD itemSubType)
{
	//if (itemType == CItemData::ITEM_TYPE_PENDANT) // Tilsim sistemi
	//	return 200;

	// ymir +15 items
	constexpr DWORD darkVnums[] = { 320,340,1190,2210,3230,5170,7310,12780,12800,12820,12840,12860,21210,21230,21250,21270,};
	for (UINT i = 0; i < _countof(darkVnums); i++)
	{
		if (itemVnum >= darkVnums[i] && itemVnum <= darkVnums[i] + 15)
			return 15;
	}
	return 9;
}

const refineTable* CPythonWiki::GetRefineItem(DWORD index)
{
	const auto it = m_vecRefineTable.find(index);
	return it != m_vecRefineTable.end() ? &it->second : NULL;
}

void CPythonWiki::ListReverse()
{
	for (DWORD j = 0; j < 3; j++)
	{
		std::stable_sort(m_vecStoneCategory[j].begin(), m_vecStoneCategory[j].end(), CompareLevelLow);
		std::stable_sort(m_vecBossCategory[j].begin(), m_vecBossCategory[j].end(), CompareLevelLow);
		std::stable_sort(m_vecMonsterCategory[j].begin(), m_vecMonsterCategory[j].end(), CompareLevelLow);
	}
}

bool CPythonWiki::BlackListMonster(DWORD mobVnum)
{
	const std::vector<DWORD> m_BlockedMonsterVnumList = {
		//monsters
		7022, 7023, 20464, 7046, 2432, 2433, 5004,
		//stones
		20437, 8060, 2900, 24000, 20399, 6209, 20500,
		6118, 20422, 20432, 20518, 20538, 8101,
		//boss
		5001, 5002, 692, 693, 2207, 7123, 7124, 1334, 2291, 2192, 5201, 8501, 7073, 7075,
		7079, 7080, 7092, 7093, 7019, 7020, 7027, 4147, 4149, 4151, 8506, 8511, 993, 2307,
		2495, 4209, 4210, 4289, 4290, 4265, 4345, 4272, 4352, 4200, 4280, 4261,
	};
	if (std::find(m_BlockedMonsterVnumList.begin(), m_BlockedMonsterVnumList.end(), mobVnum) != m_BlockedMonsterVnumList.end())
		return false;

	constexpr DWORD m_BlockedMonsterVnumRangeList[][2] = {
		// block {start, end},
		{4200, 4399},{7101, 7106},{11505, 11510},{2451, 2454},
		{11112, 11117},{8020, 8023},{20452, 20463},{8200, 8203},
		{8102, 8115},{2900, 2908},{8031, 8051},{7107, 7112},
		{8204, 8206},{8120, 8127},{8130, 8137},{4000, 4005},{1306, 1310},
		{1902, 1906},{2093, 2095},{2093, 2095},{8600, 8623},{793, 796},
		{1094, 1096},{3910, 3913},{6415, 6422},{6500, 6504},{3956, 3965},
		{11100, 11111},{4141, 4145},{4141, 4145}, {2233, 2235},{2750, 2752},
		{2760, 2762},{2770, 2772},{2770, 2772},{2780, 2782},{2790, 2792},{2790, 2792},
		{2800, 2802},{2800, 2802},{2810, 2812},{2820, 2822},{2830, 2832},{2840, 2842},
		{2850, 2852},{2860, 2862},{4400, 4403},{4410, 4413},{2600, 2692},{2700, 2737},
		{4101, 4112},{4121, 4132},
	};
	for (DWORD j = 0; j < _countof(m_BlockedMonsterVnumRangeList); ++j)
		if (mobVnum >= m_BlockedMonsterVnumRangeList[j][0] && mobVnum <= m_BlockedMonsterVnumRangeList[j][1])
			return false;

	return true;
}

void CPythonWiki::ClearMonsterData()
{
	// mob_proto karakter secim ekranina her donuste yeniden okunuyor;
	// temizlemeden eklenince Canavar/Boss/Metin listelerinde ayni vnumlar birikiyordu
	for (DWORD j = 0; j < 3; j++)
	{
		m_vecMonsterCategory[j].clear();
		m_vecBossCategory[j].clear();
		m_vecStoneCategory[j].clear();
	}
}

void CPythonWiki::LoadMonster(CPythonNonPlayer::TMobTable* monster)
{
	if (!BlackListMonster(monster->dwVnum))
		return;

	if (monster->bType == 0 || monster->bType == 2) // monster & stone
	{
		if (monster->bLevel >= 1 && monster->bLevel <= 75)
		{
			if (monster->bType == 2)
				m_vecStoneCategory[0].emplace_back(character_data(monster->dwVnum, monster->bLevel));
			else if (monster->bRank >= CPythonNonPlayer::MOB_RANK_BOSS)
				m_vecBossCategory[0].emplace_back(character_data(monster->dwVnum, monster->bLevel));
			else
				m_vecMonsterCategory[0].emplace_back(character_data(monster->dwVnum, monster->bLevel));
		}
		else if (monster->bLevel >= 76 && monster->bLevel <= 100)
		{
			if (monster->bType == 2)
				m_vecStoneCategory[1].emplace_back(character_data(monster->dwVnum, monster->bLevel));
			else if (monster->bRank >= CPythonNonPlayer::MOB_RANK_BOSS)
				m_vecBossCategory[1].emplace_back(character_data(monster->dwVnum, monster->bLevel));
			else
				m_vecMonsterCategory[1].emplace_back(character_data(monster->dwVnum, monster->bLevel));
		}
		else if (monster->bLevel >= 101)
		{
			if (monster->bType == 2)
				m_vecStoneCategory[2].emplace_back(character_data(monster->dwVnum, monster->bLevel));
			else if (monster->bRank >= CPythonNonPlayer::MOB_RANK_BOSS)
				m_vecBossCategory[2].emplace_back(character_data(monster->dwVnum, monster->bLevel));
			else
				m_vecMonsterCategory[2].emplace_back(character_data(monster->dwVnum, monster->bLevel));
		}
	}
}

void CPythonWiki::LoadItem(CItemData::TItemTable* item)
{
	constexpr BYTE flagList[CRaceData::JOB_MAX_NUM] = { CItemData::ITEM_ANTIFLAG_WARRIOR , CItemData::ITEM_ANTIFLAG_ASSASSIN ,CItemData::ITEM_ANTIFLAG_SHAMAN ,CItemData::ITEM_ANTIFLAG_SURA };

	if (isLastItem(item->dwVnum, item->szLocaleName, item->bType))
	{
		if (!ItemBlackList(item->dwVnum, item->bType, item->bSubType))
			return;
		DWORD itemLevel = 0;
		for (DWORD j = 0; j < CItemData::ITEM_LIMIT_MAX_NUM; j++)
		{
			if (item->aLimits[j].bType == CItemData::LIMIT_LEVEL)
			{
				itemLevel = item->aLimits[j].lValue;
				break;
			}
		}

		if (item->bType == CItemData::ITEM_TYPE_WEAPON)
		{
			for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
			{
				if (!(item->dwAntiFlags & flagList[j]))
					m_vecWeapon[j].emplace_back(character_data(item->dwVnum, itemLevel));
			}
		}
		else if (item->bType == CItemData::ITEM_TYPE_ARMOR)
		{
			if (item->bSubType == CItemData::ARMOR_BODY)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecArmor[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
			else if (item->bSubType == CItemData::ARMOR_HEAD)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecHelmets[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
			else if (item->bSubType == CItemData::ARMOR_SHIELD)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecShields[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
			else if (item->bSubType == CItemData::ARMOR_WRIST)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecBracelet[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
			else if (item->bSubType == CItemData::ARMOR_FOOTS)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecShoes[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
			else if (item->bSubType == CItemData::ARMOR_NECK)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecNecklace[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
			else if (item->bSubType == CItemData::ARMOR_EAR)
			{
				for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
				{
					if (!(item->dwAntiFlags & flagList[j]))
						m_vecEarrings[j].emplace_back(character_data(item->dwVnum, itemLevel));
				}
			}
		}
		else if (item->bType == CItemData::ITEM_TYPE_BELT)
		{
			for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
			{
				if (!(item->dwAntiFlags & flagList[j]))
					m_vecBelt[j].emplace_back(character_data(item->dwVnum, itemLevel));
			}
		}
		/*
		else if (item->bType == CItemData::ITEM_TYPE_PENDANT) // Tilsim sistemi
		{
			for (BYTE j = 0; j < CRaceData::JOB_MAX_NUM; ++j)
			{
				if (!(item->dwAntiFlags & flagList[j]))
					m_vecTalisman[j].emplace_back(character_data(item->dwVnum, itemLevel));
			}
		}
		*/
	}
}

PyObject* wikiGetRefineItems(PyObject* poSelf, PyObject* poArgs)
{
	int iRefineIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iRefineIndex))
		return Py_BadArgument();
	auto item = CPythonWiki::Instance().GetRefineItem(iRefineIndex);
	if (!item)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("iiiiiiiiiiiOii", item->id,item->item_vnums[0], item->item_count[0],item->item_vnums[1], item->item_count[1],item->item_vnums[2], item->item_count[2],item->item_vnums[3], item->item_count[3],item->item_vnums[4], item->item_count[4], PyLong_FromLongLong(item->cost), item->prob, item->refine_count);
}

PyObject* wikiIsBlackList(PyObject* poSelf, PyObject* poArgs)
{
	int iItemVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemVnum))
		return Py_BadArgument();
	int iType;
	if (!PyTuple_GetInteger(poArgs, 1, &iType))
		return Py_BadArgument();
	int iSubtype;
	if (!PyTuple_GetInteger(poArgs, 2, &iSubtype))
		return Py_BadArgument();
	if (iItemVnum < 0 || iType < 0 || iSubtype < 0)
		return Py_BadArgument();
	return Py_BuildValue("i", CPythonWiki::Instance().ItemBlackList((DWORD)iItemVnum, (DWORD)iType, (DWORD)iSubtype));
}

PyObject* wikiGetCategorySize(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iCategoryType;
	if (!PyTuple_GetInteger(poArgs, 1, &iCategoryType))
		return Py_BadArgument();
	if (iType >= 0 && iType <= 3)
	{
		if (iCategoryType == 0)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecWeapon[iType].size());
		else if (iCategoryType == 1)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecArmor[iType].size());
		else if (iCategoryType == 2)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecHelmets[iType].size());
		else if (iCategoryType == 3)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecShields[iType].size());
		else if (iCategoryType == 4)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecEarrings[iType].size());
		else if (iCategoryType == 5)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecBracelet[iType].size());
		else if (iCategoryType == 6)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecNecklace[iType].size());
		else if (iCategoryType == 7)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecShoes[iType].size());
		else if (iCategoryType == 8)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecBelt[iType].size());
		else if (iCategoryType == 9)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecTalisman[iType].size());
	}
	return Py_BuildValue("i", 0);
}

PyObject* wikiGetCategoryData(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iCategoryType;
	if (!PyTuple_GetInteger(poArgs, 1, &iCategoryType))
		return Py_BadArgument();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 2, &iIndex))
		return Py_BadArgument();
	if (iType >= 0 && iType <= 3)
	{
		if (iCategoryType == 0)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecWeapon[iType][iIndex].itemVnum);
		else if (iCategoryType == 1)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecArmor[iType][iIndex].itemVnum);
		else if (iCategoryType == 2)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecHelmets[iType][iIndex].itemVnum);
		else if (iCategoryType == 3)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecShields[iType][iIndex].itemVnum);
		else if (iCategoryType == 4)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecEarrings[iType][iIndex].itemVnum);
		else if (iCategoryType == 5)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecBracelet[iType][iIndex].itemVnum);
		else if (iCategoryType == 6)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecNecklace[iType][iIndex].itemVnum);
		else if (iCategoryType == 7)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecShoes[iType][iIndex].itemVnum);
		else if (iCategoryType == 8)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecBelt[iType][iIndex].itemVnum);
		else if (iCategoryType == 9)
			return Py_BuildValue("i", CPythonWiki::Instance().m_vecTalisman[iType][iIndex].itemVnum);
	}
	return Py_BuildValue("i", 0);
}

PyObject* wikiReadData(PyObject* poSelf, PyObject* poArgs)
{
	char* locale;
	if (!PyTuple_GetString(poArgs, 0, &locale))
		return Py_BuildException();
	CPythonWiki::Instance().ReadData(locale);
	return Py_BuildNone();
}

PyObject* wikiGetRefineMaxLevel(PyObject* poSelf, PyObject* poArgs)
{
	int iItemVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemVnum))
		return Py_BuildException();
	CItemManager::Instance().SelectItemData(iItemVnum);
	CItemData* pItemData = CItemManager::Instance().GetSelectedItemDataPointer();
	if (!pItemData)
		return Py_BuildValue("i", CPythonWiki::Instance().GetRefineLevel(iItemVnum, 0, 0));
	return Py_BuildValue("i", CPythonWiki::Instance().GetRefineLevel(iItemVnum, pItemData->GetType(), pItemData->GetSubType()));
}

PyObject* wikiGetChestSize(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BuildException();
	if (iType == 0)
		return Py_BuildValue("i", _countof(bossChests));
	else if (iType == 1)
		return Py_BuildValue("i", _countof(eventChests));
	else if (iType == 2)
		return Py_BuildValue("i", _countof(alternativeChests));
	return Py_BuildValue("i", 0);
}

PyObject* wikiGetChestData(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BuildException();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BuildException();
	if (iType == 0)
		return Py_BuildValue("ii", bossChests[iIndex][0], bossChests[iIndex][1]);
	else if (iType == 1)
		return Py_BuildValue("ii", eventChests[iIndex][0], eventChests[iIndex][1]);
	else if (iType == 2)
		return Py_BuildValue("ii", alternativeChests[iIndex][0], alternativeChests[iIndex][1]);
	return Py_BuildValue("ii", 0,0);
}

PyObject* wikiGetSpecialInfoSize(PyObject* poSelf, PyObject* poArgs)
{
	int iItemVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemVnum))
		return Py_BuildException();
	const auto it = CPythonWiki::Instance().m_vecSpecialDrop.find(iItemVnum);
	if (it != CPythonWiki::Instance().m_vecSpecialDrop.end())
		return Py_BuildValue("i", it->second.size());
	return Py_BuildValue("i", 0);
}

PyObject* wikiGetSpecialInfoData(PyObject* poSelf, PyObject* poArgs)
{
	int iItemVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemVnum))
		return Py_BuildException();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BuildException();
	const auto it = CPythonWiki::Instance().m_vecSpecialDrop.find(iItemVnum);
	if (it != CPythonWiki::Instance().m_vecSpecialDrop.end())
		return Py_BuildValue("ii", it->second[iIndex].itemVnum, it->second[iIndex].count);
	return Py_BuildValue("ii", 0, 0);
}

PyObject* wikiGetMobInfoSize(PyObject* poSelf, PyObject* poArgs)
{
	int iItemVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemVnum))
		return Py_BuildException();
	const auto it = CPythonWiki::Instance().m_vecMobDrop.find(iItemVnum);
	if (it != CPythonWiki::Instance().m_vecMobDrop.end())
		return Py_BuildValue("i", it->second.size());
	return Py_BuildValue("i", 0);
}

PyObject* wikiGetMobInfoData(PyObject* poSelf, PyObject* poArgs)
{
	int iItemVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iItemVnum))
		return Py_BuildException();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BuildException();
	const auto it = CPythonWiki::Instance().m_vecMobDrop.find(iItemVnum);
	if (it == CPythonWiki::Instance().m_vecMobDrop.end())
		return Py_BuildValue("ii",0,0);
	return Py_BuildValue("ii", it->second[iIndex].itemVnum, it->second[iIndex].count);
}

PyObject* wikiGetBossSize(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	if (iType == 3) // event boss
		return Py_BuildValue("i", (sizeof(eventBoss) / sizeof(eventBoss[0])));
	if (iType < 0 || iType > 2)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonWiki::Instance().m_vecBossCategory[iType].size());
}

PyObject* wikiGetBossData(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BadArgument();
	if (iType == 3) // event boss
		return Py_BuildValue("i", eventBoss[iIndex]);
	if (iType < 0 || iType > 2 || iIndex < 0 || iIndex >= (int)CPythonWiki::Instance().m_vecBossCategory[iType].size())
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonWiki::Instance().m_vecBossCategory[iType][iIndex].itemVnum);
}

PyObject* wikiCostumeSize(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	const auto it = m_CostumeData.find(iType);
	if (it != m_CostumeData.end())
		return Py_BuildValue("i", it->second.size());
	return Py_BuildValue("i", 0);
}
PyObject* wikiCostumeData(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BadArgument();
	const auto it = m_CostumeData.find(iType);
	if (it != m_CostumeData.end())
		return Py_BuildValue("i", it->second[iIndex]);
	return Py_BuildValue("i", 0);
}

PyObject* wikiGetMonsterSize(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	if (iType < 0 || iType > 2)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonWiki::Instance().m_vecMonsterCategory[iType].size());
}

PyObject* wikiGetMonsterData(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BadArgument();
	if (iType < 0 || iType > 2 || iIndex < 0 || iIndex >= (int)CPythonWiki::Instance().m_vecMonsterCategory[iType].size())
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonWiki::Instance().m_vecMonsterCategory[iType][iIndex].itemVnum);
}

PyObject* wikiGetStoneSize(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	if (iType < 0 || iType > 2)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonWiki::Instance().m_vecStoneCategory[iType].size());
}

PyObject* wikiGetStoneData(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 1, &iIndex))
		return Py_BadArgument();
	if (iType < 0 || iType > 2 || iIndex < 0 || iIndex >= (int)CPythonWiki::Instance().m_vecStoneCategory[iType].size())
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CPythonWiki::Instance().m_vecStoneCategory[iType][iIndex].itemVnum);
}

PyObject* wikiGetItemDropFromChest(PyObject* poSelf, PyObject* poArgs)
{
	int szItemVnum = 0;
	if (!PyTuple_GetInteger(poArgs, 0, &szItemVnum))
		return Py_BadArgument();
	bool szIsRefineItem = false;
	if (!PyTuple_GetBoolean(poArgs, 1, &szIsRefineItem))
		return Py_BadArgument();

	PyObject* poList = PyList_New(0);

	const BYTE refineLevel = szIsRefineItem ? CPythonWiki::Instance().GetRefineLevel(szItemVnum, 0, 0) : 0;
	const auto m_vec_ItemRange = CPythonWiki::Instance().GetSpecialDrop();

	for (const auto& [chestVnum, chestData] : m_vec_ItemRange)
	{
		if (chestData.size() > 0)
		{
			if (szIsRefineItem)
			{
				for (const auto& dataItem : chestData)
				{
					if (szItemVnum >= dataItem.itemVnum && szItemVnum <= dataItem.itemVnum + refineLevel)
					{
						const auto obj = Py_BuildValue("i", chestVnum);
						PyList_Append(poList, obj);
						break;
					}
				}
			}
			else
			{
				for (const auto& dataItem : chestData)
				{
					if (szItemVnum == dataItem.itemVnum)
					{
						const auto obj = Py_BuildValue("i", chestVnum);
						PyList_Append(poList, obj);
						break;
					}

				}
			}

		}
	}
	return Py_BuildValue("O", poList);
}

PyObject* wikiGetItemDropFromMonster(PyObject* poSelf, PyObject* poArgs)
{
	int szItemVnum = 0;
	if (!PyTuple_GetInteger(poArgs, 0, &szItemVnum))
		return Py_BadArgument();
	bool szIsRefineItem = false;
	if (!PyTuple_GetBoolean(poArgs, 1, &szIsRefineItem))
		return Py_BadArgument();

	PyObject* poList = PyList_New(0);
	const BYTE refineLevel = szIsRefineItem ? CPythonWiki::Instance().GetRefineLevel(szItemVnum, 0, 0) : 0;
	const auto m_vec_ItemRange = CPythonWiki::Instance().GetMobDrop();
	for (const auto& [mobVnum, mobData] : m_vec_ItemRange)
	{
		if (mobData.size() > 0)
		{
			if (szIsRefineItem)
			{
				for (const auto& dataItem : mobData)
				{
					if (szItemVnum >= dataItem.itemVnum && szItemVnum <= dataItem.itemVnum + refineLevel)
					{
						const auto obj = Py_BuildValue("i", mobVnum);
						PyList_Append(poList, obj);
						break;
					}
				}
			}
			else
			{
				for (const auto& dataItem : mobData)
				{
					if (szItemVnum == dataItem.itemVnum)
					{
						const auto obj = Py_BuildValue("i", mobVnum);
						PyList_Append(poList, obj);
						break;
					}

				}
			}
		}
	}
	return Py_BuildValue("O", poList);
}

void initWiki()
{
	static PyMethodDef s_methods[] =
	{
		{ "GetRefineItems",	wikiGetRefineItems,	METH_VARARGS },
		{ "IsBlackList",	wikiIsBlackList,	METH_VARARGS },

		{ "GetCategorySize",	wikiGetCategorySize,	METH_VARARGS },
		{ "GetCategoryData",	wikiGetCategoryData,	METH_VARARGS },

		{ "GetBossSize",	wikiGetBossSize,	METH_VARARGS },
		{ "GetBossData",	wikiGetBossData,	METH_VARARGS },

		{ "GetMonsterSize",	wikiGetMonsterSize,	METH_VARARGS },
		{ "GetMonsterData",	wikiGetMonsterData,	METH_VARARGS },

		{ "GetCostumeSize",	wikiCostumeSize,	METH_VARARGS },
		{ "GetCostumeData",	wikiCostumeData,	METH_VARARGS },

		{ "GetStoneSize",	wikiGetStoneSize,	METH_VARARGS },
		{ "GetStoneData",	wikiGetStoneData,	METH_VARARGS },

		{ "GetChestSize",	wikiGetChestSize,	METH_VARARGS },
		{ "GetChestData",	wikiGetChestData,	METH_VARARGS },

		{ "GetSpecialInfoSize",	wikiGetSpecialInfoSize,	METH_VARARGS },
		{ "GetSpecialInfoData",	wikiGetSpecialInfoData,	METH_VARARGS },

		{ "GetMobInfoSize",	wikiGetMobInfoSize,	METH_VARARGS },
		{ "GetMobInfoData",	wikiGetMobInfoData,	METH_VARARGS },

		{ "ReadData",	wikiReadData,	METH_VARARGS },

		{ "GetRefineMaxLevel",	wikiGetRefineMaxLevel,	METH_VARARGS },

		{ "GetItemDropFromChest",	wikiGetItemDropFromChest,	METH_VARARGS },
		{ "GetItemDropFromMonster",	wikiGetItemDropFromMonster,	METH_VARARGS },

		{ NULL, NULL, NULL },
	};
	PyObject* poModule = Py_InitModule("wiki", s_methods);
}
#endif

