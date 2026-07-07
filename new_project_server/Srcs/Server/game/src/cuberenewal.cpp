
#define _cube_cpp_

#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "log.h"
#include "char.h"
#include "locale_service.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include <sstream>
#include "packet.h"
#include "desc_client.h"
#include "config.h"	// g_bItemCountLimit (gercek stack limiti; hardcoded 200 stack tasma-dupe bugfix)

static std::vector<CUBE_RENEWAL_DATA*>	s_cube_proto;

typedef std::vector<CUBE_RENEWAL_VALUE>	TCubeValueVector;

struct SCubeMaterialInfo
{
	SCubeMaterialInfo()
	{
		bHaveComplicateMaterial = false;
	};

	CUBE_RENEWAL_VALUE			reward;							// º¸»ó?? ¹¹³?
	TCubeValueVector	material;						// ?ç·áµé?º ¹¹³?
#ifdef ENABLE_YANG_LIMIT_SYSTEM
	long long				gold;							// µ·?º ¾ó¸¶µå³?
#else
	long long				gold;							// µ·?º ¾ó¸¶µå³?
#endif
	int 				percent;
	std::string		category;
#ifdef ENABLE_CUBE_ATTR_SOCKET
	bool	allowCopyAttr;
#endif
	TCubeValueVector	complicateMaterial;				// º¹?â??-_- ?ç·áµé

	std::string			infoText;		
	bool				bHaveComplicateMaterial;		//
};

struct SItemNameAndLevel
{
	SItemNameAndLevel() { level = 0; }

	std::string		name;
	int				level;
};


typedef std::vector<SCubeMaterialInfo>								TCubeResultList;
typedef std::unordered_map<DWORD, TCubeResultList>					TCubeMapByNPC;				// °¢°¢?? NPCº°·? ¾î¶² °? ¸¸µé ¼ö ??°í ?ç·á°¡ ¹º?ö...


TCubeMapByNPC cube_info_map;


static bool FN_check_valid_npc( WORD vnum )
{
	for ( std::vector<CUBE_RENEWAL_DATA*>::iterator iter = s_cube_proto.begin(); iter != s_cube_proto.end(); iter++ )
	{
		if ( std::find((*iter)->npc_vnum.begin(), (*iter)->npc_vnum.end(), vnum) != (*iter)->npc_vnum.end() )
			return true;
	}

	return false;
}


static bool FN_check_cube_data (CUBE_RENEWAL_DATA *cube_data)
{
	DWORD	i = 0;
	DWORD	end_index = 0;

	end_index = cube_data->npc_vnum.size();
	for (i=0; i<end_index; ++i)
	{
		if ( cube_data->npc_vnum[i] == 0 )	return false;
	}

	end_index = cube_data->item.size();
	for (i=0; i<end_index; ++i)
	{
		if ( cube_data->item[i].vnum == 0 )		return false;
		if ( cube_data->item[i].count == 0 )	return false;
	}

	end_index = cube_data->reward.size();
	for (i=0; i<end_index; ++i)
	{
		if ( cube_data->reward[i].vnum == 0 )	return false;
		if ( cube_data->reward[i].count == 0 )	return false;
	}
	return true;
}

static int FN_check_cube_item_vnum_material(const SCubeMaterialInfo& materialInfo, int index)
{
	if (index <= materialInfo.material.size()){
		return materialInfo.material[index-1].vnum;
	}
	return 0;
}

static int FN_check_cube_item_count_material(const SCubeMaterialInfo& materialInfo,int index)
{
	if (index <= materialInfo.material.size()){
		return materialInfo.material[index-1].count;
	}

	return 0;
}

// YENI: bir malzeme vnum'unun beceri kitabi (ITEM_SKILLBOOK) olup olmadigini proto tablosundan kontrol eder.
// Beceri kitabi malzemeleri sadece oyuncunun gridden sectigi slotlardan tuketilir (vnum-first-match degil).
static bool FN_is_skillbook_vnum(DWORD vnum)
{
	TItemTable* p = ITEM_MANAGER::instance().GetTable(vnum);
	return (p != NULL) && (p->bType == ITEM_SKILLBOOK);
}

CUBE_RENEWAL_DATA::CUBE_RENEWAL_DATA()
{
	this->gold = 0;
	this->category = "WORLDARD";
#ifdef ENABLE_CUBE_ATTR_SOCKET
	this->allowCopyAttr = false;
#endif
}

#if defined(ENABLE_CUBE_RELOAD_FIX)
#include "desc.h"
#include "desc_manager.h"
static void CubeReload()
{
	cube_info_map.clear();
	//cube_result_info_map_by_npc.clear();
	Cube_InformationInitialize();
	for (DESC_MANAGER::DESC_SET::const_iterator it = DESC_MANAGER::instance().GetClientSet().begin(); it != DESC_MANAGER::instance().GetClientSet().end(); ++it) {
		LPCHARACTER ch = (*it)->GetCharacter();
		if (ch) {
			Cube_close(ch);
			ch->ChatPacket(CHAT_TYPE_COMMAND, "cube reload");
		}
	}
}
#endif

void Cube_init()
{
	CUBE_RENEWAL_DATA * p_cube = NULL;
	std::vector<CUBE_RENEWAL_DATA*>::iterator iter;

	char file_name[256+1];
	snprintf(file_name, sizeof(file_name), "%s/cube.txt", LocaleService_GetBasePath().c_str());

	sys_log(0, "Cube_Init %s", file_name);

	for (iter = s_cube_proto.begin(); iter!=s_cube_proto.end(); iter++)
	{
		p_cube = *iter;
		M2_DELETE(p_cube);
	}

	s_cube_proto.clear();

	if (false == Cube_load(file_name))
		sys_err("Cube_Init failed");

#if defined(ENABLE_CUBE_RELOAD_FIX)
	CubeReload();
#endif
}

bool Cube_load (const char *file)
{
	FILE	*fp;


	const char	*value_string;

	char	one_line[256];
#ifdef ENABLE_YANG_LIMIT_SYSTEM
	long long		value1, value2;
#else
	long long		value1, value2;
#endif
	const char	*delim = " \t\r\n";
	char	*v, *token_string;
//	char *v1;

	CUBE_RENEWAL_DATA	*cube_data = NULL;
	CUBE_RENEWAL_VALUE	cube_value = {0,0};

	if (0 == file || 0 == file[0])
		return false;

	if ((fp = fopen(file, "r")) == 0)
		return false;

	while (fgets(one_line, 256, fp))
	{
		value1 = value2 = 0;

		if (one_line[0] == '#')
			continue;

		token_string = strtok(one_line, delim);

		if (NULL == token_string)
			continue;

		// set value1, value2
		if ((v = strtok(NULL, delim)))
			str_to_number(value1, v);
		    value_string = v;

		if ((v = strtok(NULL, delim)))
			str_to_number(value2, v);

		TOKEN("section")
		{
			cube_data = M2_NEW CUBE_RENEWAL_DATA;
		}
		else TOKEN("npc")
		{
			cube_data->npc_vnum.push_back((WORD)value1);
		}
		else TOKEN("item")
		{
			cube_value.vnum		= value1;
			cube_value.count	= value2;

			cube_data->item.push_back(cube_value);
		}
		else TOKEN("reward")
		{
			cube_value.vnum		= value1;
			cube_value.count	= value2;

			cube_data->reward.push_back(cube_value);
		}
		else TOKEN("percent")
		{

			cube_data->percent = value1;
		}

		else TOKEN("category")
		{
			cube_data->category = value_string;
		}

		else TOKEN("gold")
		{
			// ?¦?¶¿¡ ??¿ä?? ±?¾?
			cube_data->gold = value1;
		}
#ifdef ENABLE_CUBE_ATTR_SOCKET
		else TOKEN("allow_copy")
		{
			cube_data->allowCopyAttr = (value1 == 1 ? true : false);
		}
#endif
		else TOKEN("end")
		{

			// TODO : check cube data
			if (false == FN_check_cube_data(cube_data))
			{
				if (test_server)
					sys_log(0, "something wrong");
				M2_DELETE(cube_data);
				continue;
			}
			s_cube_proto.push_back(cube_data);
		}
	}

	fclose(fp);
	return true;
}


SItemNameAndLevel SplitItemNameAndLevelFromName(const std::string& name)
{
	int level = 0;
	SItemNameAndLevel info;
	info.name = name;

	size_t pos = name.find("+");
	
	if (std::string::npos != pos)
	{
		const std::string levelStr = name.substr(pos + 1, name.size() - pos - 1);
		str_to_number(level, levelStr.c_str());

		info.name = name.substr(0, pos);
	}

	info.level = level;

	return info;
};


bool Cube_InformationInitialize()
{
	for (int i = 0; i < s_cube_proto.size(); ++i)
	{
		CUBE_RENEWAL_DATA* cubeData = s_cube_proto[i];

		const std::vector<CUBE_RENEWAL_VALUE>& rewards = cubeData->reward;

		if (1 != rewards.size())
		{
			sys_err("[CubeInfo] WARNING! Does not support multiple rewards (count: %d)", rewards.size());			
			continue;
		}

		const CUBE_RENEWAL_VALUE& reward = rewards.at(0);

		TCubeMapByNPC& cubeMap = cube_info_map;
		SCubeMaterialInfo materialInfo;

		materialInfo.reward = reward;
		materialInfo.gold = cubeData->gold;
		materialInfo.percent = cubeData->percent;
		materialInfo.material = cubeData->item;
		materialInfo.category = cubeData->category;

		// Register this recipe under every NPC line in the section (not only npc_vnum[0]).
		// Otherwise / cube open <vnum> works for FN_check_valid_npc but cube_info_map has no rows for secondary NPCs.
		for (size_t ni = 0; ni < cubeData->npc_vnum.size(); ++ni)
		{
			const WORD npcVNUM = cubeData->npc_vnum.at(ni);
			TCubeResultList& resultList = cubeMap[npcVNUM];
			resultList.push_back(materialInfo);
		}
	}

	//s_isInitializedCubeMaterialInformation = true;
	return true;
}


void Cube_open (LPCHARACTER ch, DWORD dwRecipeNpcRace)
{
	if (!ch)
		return;

	LPCHARACTER	npc= ch->GetQuestNPC();

	if (!npc)
		return;

	DWORD npcVNUM = (dwRecipeNpcRace != 0) ? dwRecipeNpcRace : npc->GetRaceNum();

	if ( FN_check_valid_npc(npcVNUM) == false )
	{
		if ( test_server == true )
		{
			sys_log(0, "cube not valid NPC (recipe race %u)", npcVNUM);
		}
		return;
	}


	if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen()
#ifdef OFFLINE_SHOP
		|| ch->IsEditingShop()
#endif
#ifdef ENABLE_SAFE_TRADE_SYSTEM
		|| ch->GetSafeTrade() || ch->IsSafeTradeClaiming()
#endif
		)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("Cannot open refinement window"));
		return;
	}

#ifdef ENABLE_ACCE_SYSTEM
	if (ch->isAcceOpened(true) || ch->isAcceOpened(false))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("´Ù¸¥ °Å·¡Þß(Ã¢°í,±³È¯,»óÞ¡)¿¡´Â »ç¿ëÇÒ ¼ö ¾ø½À´Þ´Ù."));
		return;
	}
#endif

#ifdef ENABLE_AURA_SYSTEM
	if (ch->isAuraOpened(true) || ch->isAuraOpened(false))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("´Ù¸¥ °Å·¡Þß(Ã¢°í,±³È¯,»óÞ¡)¿¡´Â »ç¿ëÇÒ ¼ö ¾ø½À´Þ´Ù."));
		return;
	}
#endif

#ifdef ENABLE_CHANGELOOK_SYSTEM
	if (ch->isChangeLookOpened())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("´Ù¸¥ °Å·¡Þß(Ã¢°í,±³È¯,»óÞ¡)¿¡´Â »ç¿ëÇÒ ¼ö ¾ø½À´Þ´Ù."));
		return;
	}
#endif

#ifdef ENABLE_ITEM_COMBINATION_SYSTEM
	if (ch->IsCombOpen())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("´Ù¸¥ °Å·¡Þß(Ã¢°í,±³È¯,»óÞ¡)¿¡´Â »ç¿ëÇÒ ¼ö ¾ø½À´Þ´Ù."));
		return;
	}
#endif

	long distance = DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY());

	if (distance >= CUBE_MAX_DISTANCE)
	{
		sys_log(1, "CUBE: TOO_FAR: %s distance %d", ch->GetName(), distance);
		return;
	}


	SendDateCubeRenewalPackets(ch,CUBE_RENEWAL_SUB_HEADER_CLEAR_DATES_RECEIVE);
	SendDateCubeRenewalPackets(ch,CUBE_RENEWAL_SUB_HEADER_DATES_RECEIVE,npcVNUM);
	SendDateCubeRenewalPackets(ch,CUBE_RENEWAL_SUB_HEADER_DATES_LOADING);
	SendDateCubeRenewalPackets(ch,CUBE_RENEWAL_SUB_HEADER_OPEN_RECEIVE);

	ch->SetCubeRenewalRecipeNpc(npcVNUM);
	ch->SetCubeNpc(npc);
	ch->ClearCubeSkillSlots(); // YENI: yeni acilista bayat secim kalmasin

	// YENI: beceri kitabi grid'i SADECE CUBE_SKILL_GRID_NPC icin gorunsun.
	// Make paketine alan ekleyemedigimiz icin client'a server->client komutuyla bildiriyoruz.
	ch->ChatPacket(CHAT_TYPE_COMMAND, "cube_skill_grid %d", (npcVNUM == CUBE_SKILL_GRID_NPC) ? 1 : 0);
}

void Cube_close(LPCHARACTER ch)
{
	ch->SetCubeNpc(NULL);
	ch->SetCubeRenewalRecipeNpc(0);
	ch->ClearCubeSkillSlots(); // YENI: pencere kapaninca secili beceri kitabi slotlari temizlensin
}

void Cube_Make(LPCHARACTER ch, int index, int count_item, int index_item_improve)
{
	LPCHARACTER	npc;

	npc = ch->GetQuestNPC();

	if (!ch->IsCubeOpen())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("To create an item you have to have the refinement window open"));
		return;
	}

	if (NULL == npc)
	{
		return;
	}

	DWORD recipeNpcRace = ch->GetCubeRenewalRecipeNpc();
	if (recipeNpcRace == 0)
		recipeNpcRace = npc->GetRaceNum();

	const auto cube_it = cube_info_map.find(recipeNpcRace);
	if (cube_it == cube_info_map.end())
	{
		sys_log(1, "CUBE_RENEWAL Make: no recipe table for npc race %u (%s)", recipeNpcRace, ch->GetName());
		return;
	}
	const TCubeResultList& resultList = cube_it->second;

	if (index < 0 || static_cast<size_t>(index) >= resultList.size())
	{
		sys_log(1, "CUBE_RENEWAL Make: invalid recipe index %d (size %zu) char %s", index, resultList.size(), ch->GetName());
		return;
	}

	if (count_item < 1)
		return;

	// Kosulsuz ust sinir (define'dan BAGIMSIZ): need = material.count * count_item int carpimi
	// tasarsa negatif need malzeme kontrolunu atlatir (dupe) ve roll dongusu DoS olur.
	if (count_item > CUBE_RENEWAL_MAX_MAKE_COUNT)
		count_item = CUBE_RENEWAL_MAX_MAKE_COUNT;

#ifdef ENABLE_CUBE_RENEWAL_DISABLE_BULK
	// Toplu uretim kapali: istemci kac parti isterse istesin tek parti uretilir.
	if (count_item > 1)
		count_item = 1;
#endif

	{
		const long distMk = DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY());
		if (distMk >= CUBE_MAX_DISTANCE)
		{
			sys_log(1, "CUBE_RENEWAL Make: TOO_FAR %s dist %ld", ch->GetName(), distMk);
			return;
		}
	}

	if (index_item_improve != -1)
	{
		if (index_item_improve < 0 || index_item_improve >= INVENTORY_AND_EQUIP_SLOT_MAX)
		{
			sys_log(1, "CUBE_RENEWAL Make: invalid improve slot %d (%s)", index_item_improve, ch->GetName());
			index_item_improve = -1;
		}
	}

	// YENI: oyuncunun cube grid'inden sectigi beceri kitabi slotlarini al ve hemen temizle (tek seferlik secim).
	// Boylece her uretim icin client'in slot listesini tekrar gondermesi gerekir; bayat secim kalmaz.
	std::vector<WORD> vSkillSlots = ch->GetCubeSkillSlots();
	ch->ClearCubeSkillSlots();
	// YENI: slot-hassas beceri kitabi tuketimi SADECE bu NPC'de; diger NPC'lerde eski davranis korunur.
	const bool bUseSkillGrid = (recipeNpcRace == CUBE_SKILL_GRID_NPC);

#ifdef ENABLE_CUBE_ATTR_SOCKET
	bool canCopy = false;
#endif
	int index_value = 0;
	bool material_check = true;
	LPITEM pItem;
	int iEmptyPos;
#ifdef ENABLE_CUBE_ATTR_SOCKET
    DWORD copyAttr[ITEM_ATTRIBUTE_MAX_NUM][2];
    long copySockets[ITEM_SOCKET_MAX_NUM];

	
	memset(copyAttr, 0, sizeof(copyAttr));
	memset(copySockets, 0, sizeof(copySockets));

#endif

	for (TCubeResultList::const_iterator iter = resultList.begin(); resultList.end() != iter; ++iter)
	{
		if (index_value == index)
		{
			const SCubeMaterialInfo& materialInfo = *iter;

			for (int i = 0; i < materialInfo.material.size(); ++i)
			{
				const DWORD mvnum = materialInfo.material[i].vnum;
				const int need = materialInfo.material[i].count * count_item;
				if (bUseSkillGrid && FN_is_skillbook_vnum(mvnum))
				{
					// YENI: beceri kitaplari icin sadece gridden secilmis slotlardaki ayni vnum'lu kitaplar sayilir.
					// Envanterde secilmemis kitap olsa bile asla kullanilmaz.
					int got = 0;
					for (size_t s = 0; s < vSkillSlots.size(); ++s)
					{
						const WORD slot = vSkillSlots[s];
						if (slot >= INVENTORY_MAX_NUM)
							continue;
						LPITEM it = ch->GetInventoryItem(slot);
						if (!it || it->GetVnum() != mvnum)
							continue;
						got += it->GetCount();
					}
					if (got < need)
						material_check = false;
				}
				else
				{
					if (ch->CountSpecifyItem(mvnum) < need)
						material_check = false;
				}
			}

			if (materialInfo.gold != 0){
				if (ch->GetGold() < ((long long) materialInfo.gold*count_item))
				{
					ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("He doesn't have the necessary amount of yang."));
					return;
				}
			}
#ifdef ENABLE_CUBE_ATTR_SOCKET
			bool pAntiStack = false;
			TItemTable * p = ITEM_MANAGER::instance().GetTable(materialInfo.reward.vnum);
			if (p)
				if (p->dwFlags & ITEM_FLAG_STACKABLE)
					pAntiStack = true;
			if (pAntiStack == false)
				count_item = 1;
#endif
			if (material_check){
				
				int percent_number;
				int total_items_give = 0;

				int porcent_item_improve = 0;

				if (index_item_improve != -1)
				{

					LPITEM item = ch->GetInventoryItem(index_item_improve);
					if(item != NULL)
					{

						if(item->GetCount() <= 40){
							if (materialInfo.percent+item->GetCount() <= 100){
								porcent_item_improve = item->GetCount();
							}

							if(materialInfo.percent < 100)
							{
								if (materialInfo.percent+item->GetCount() > 100){
									porcent_item_improve = 100 - materialInfo.percent;
								}
							}
						}
					}

					if(porcent_item_improve != 0)
					{
						item->SetCount(item->GetCount()-porcent_item_improve);
					}
				}

				for (int i = 0; i < count_item; ++i)
				{
					percent_number = number(1,100);
					if ( percent_number<=materialInfo.percent+porcent_item_improve)
					{
						total_items_give++;
					}
				}

				pItem = ITEM_MANAGER::instance().CreateItem(materialInfo.reward.vnum,(materialInfo.reward.count*count_item));
				if (!pItem)
				{
					sys_err("CUBE_RENEWAL: CreateItem failed vnum %u count %d", materialInfo.reward.vnum, materialInfo.reward.count * count_item);
					return;
				}
				iEmptyPos = pItem->IsDragonSoul() ? ch->GetEmptyDragonSoulInventory(pItem) : ch->GetEmptyInventory(pItem->GetSize());

				if (pItem->IsDragonSoul())
				{
					iEmptyPos = ch->GetEmptyDragonSoulInventory(pItem);
				}

#ifdef ENABLE_SPECIAL_STORAGE
				else if (pItem->IsUpgradeItem())
				{
					iEmptyPos = ch->GetEmptyUpgradeInventory(pItem);
				}
				else if (pItem->IsBook())
				{
					iEmptyPos = ch->GetEmptyBookInventory(pItem);
				}
				else if (pItem->IsStone())
				{
					iEmptyPos = ch->GetEmptyStoneInventory(pItem);
				}
#endif
				else{
					iEmptyPos = ch->GetEmptyInventory(pItem->GetSize());
				}

				// BUGFIX: bos-yer kontrolu icin yaratilan gecici item hicbir yolda yok edilmiyordu (her uretimde item sizintisi).
				M2_DESTROY_ITEM(pItem);
				pItem = NULL;

				if (iEmptyPos < 0)
				{
					ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You do not have enough space in your inventory."));
					return;
				}

#ifdef ENABLE_CUBE_ATTR_SOCKET
				WORD objectSlot = -1; // Define -1 slot (inventory start from 0, not from 1)
				for (int i=0; i<INVENTORY_MAX_NUM; ++i)//Starting searchinf in inventory for Material Armor
				{
					LPITEM object = ch->GetInventoryItem(i);//Select Item via LPITEM
					if (NULL == object)
						continue; // Skip if is null to avoiding crashes
					if (object->GetType() == ITEM_WEAPON || object->GetType() == ITEM_ARMOR) // Check if is armor or weapon
					{
						if (object->GetVnum() == materialInfo.material[0].vnum) // Check if Select item is same item with crafting item
						{
							objectSlot = object->GetCell(); // Copy slot
								canCopy = true;
								break; //Stop loop if item is finded
						}
					}
				}
				if (canCopy)
				{
					if (objectSlot >= 0)
					{
						LPITEM BonusItem = ch->GetInventoryItem(objectSlot);//Select Finded slot above function
						//Coppy Attributes
						for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; a++)
						{
							if (BonusItem->GetAttributeType(a) != 0)
							{
								copyAttr[a][0] = BonusItem->GetAttributeType(a);
								copyAttr[a][1] = BonusItem->GetAttributeValue(a);
							}
						}
						
						//Copy Sockets
						if (BonusItem->GetType() == ITEM_WEAPON || BonusItem->GetType() == ITEM_ARMOR)
						{
							for(int a = 0; a < BonusItem->GetSocketCount(); a++)
							{
								copySockets[a] = BonusItem->GetSocket(a);
							}
						}
					}
				}
#endif
				
				for (int i = 0; i < materialInfo.material.size(); ++i)
				{
					const DWORD mvnum = materialInfo.material[i].vnum;
					int need = materialInfo.material[i].count * count_item;
					if (bUseSkillGrid && FN_is_skillbook_vnum(mvnum))
					{
						// YENI: beceri kitaplarini sadece gridden secilmis slotlardan, slot slot tuket.
						for (size_t s = 0; s < vSkillSlots.size() && need > 0; ++s)
						{
							const WORD slot = vSkillSlots[s];
							if (slot >= INVENTORY_MAX_NUM)
								continue;
							LPITEM it = ch->GetInventoryItem(slot);
							if (!it || it->GetVnum() != mvnum)
								continue;
							const int take = MIN(need, (int)it->GetCount());
							it->SetCount(it->GetCount() - take); // 0 olunca motor item'i yok eder
							need -= take;
						}
						if (need > 0) // guvenlik: secim degismis olabilir (dogrulama gecmisti)
							sys_err("CUBE_RENEWAL skillbook slot-consume short by %d vnum %u char %s", need, mvnum, ch->GetName());
					}
					else
					{
						ch->RemoveSpecifyItem(mvnum, need);
					}
				}

				if (materialInfo.gold != 0)
				{
					sys_err("[Cube_Make] PlayerName: %s - Old Money: %lld", ch->GetName(), ch->GetGold());
					ch->PointChange(POINT_GOLD, -static_cast<long long>(materialInfo.gold*count_item), false);
				}

#ifdef ENABLE_BATTLE_PASS
	if (!ch->v_counts.empty())
	{
		for (int i = 0; i<ch->missions_bp.size(); ++i)
		{
			if (ch->missions_bp[i].type == 5)
			{
				ch->DoMission(i, 1);
			}
		}
	}
#endif
				if(total_items_give <= 0)
				{
					ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("It has failed."));
#ifdef ENABLE_SMITH_EFFECT_SYSTEM
					ch->EffectPacket(SE_FR_FAIL);
#endif
					return;
				}

				pItem = ITEM_MANAGER::instance().CreateItem(materialInfo.reward.vnum,(materialInfo.reward.count*total_items_give));

				if (!pItem)
				{
					sys_err("CUBE_RENEWAL: CreateItem (after roll) failed vnum %u count %d char %s", materialInfo.reward.vnum, materialInfo.reward.count * total_items_give, ch->GetName());
					return;
				}

				if (pItem->IsStackable() && !IS_SET(pItem->GetAntiFlag(), ITEM_ANTIFLAG_STACK))
				{
#ifdef __EXTENDED_ITEM_COUNT__
					short bCount = pItem->GetCount();
#else
					BYTE bCount = pItem->GetCount();
#endif

					for (int i = 0; i < INVENTORY_MAX_NUM; ++i)
					{
						LPITEM item2 = ch->GetInventoryItem(i);

						if (!item2)
							continue;

						if (item2->GetVnum() == pItem->GetVnum())
						{
							int j;

							for (j = 0; j < ITEM_SOCKET_MAX_NUM; ++j)
								if (item2->GetSocket(j) != pItem->GetSocket(j))
									break;

							if (j != ITEM_SOCKET_MAX_NUM)
								continue;

#ifdef __EXTENDED_ITEM_COUNT__
							short bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#else
							BYTE bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#endif
							bCount -= bCount2;

							item2->SetCount(item2->GetCount() + bCount2);

							if (bCount == 0)
							{
								M2_DESTROY_ITEM(pItem);
								if (item2->GetType() == ITEM_QUEST)
									quest::CQuestManager::instance().PickupItem (ch->GetPlayerID(), item2);
								ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CUBE_RENEWAL_SUCCESS"));
								return;
							}
						}
					}

					pItem->SetCount(bCount);
				}
#ifdef ENABLE_SPECIAL_STORAGE
				if (pItem->IsUpgradeItem() && pItem->IsStackable() && !IS_SET(pItem->GetAntiFlag(), ITEM_ANTIFLAG_STACK))
				{
#ifdef __EXTENDED_ITEM_COUNT__
					short bCount = pItem->GetCount();
#else
					BYTE bCount = pItem->GetCount();
#endif

					for (int i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
					{
						LPITEM item2 = ch->GetUpgradeInventoryItem(i);

						if (!item2)
							continue;

						if (item2->GetVnum() == pItem->GetVnum())
						{

#ifdef __EXTENDED_ITEM_COUNT__
							short bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#else
							BYTE bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#endif
							bCount -= bCount2;

							item2->SetCount(item2->GetCount() + bCount2);

							if (bCount == 0)
							{
								M2_DESTROY_ITEM(pItem);
								ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CUBE_RENEWAL_SUCCESS"));
								return;
							}
						}
					}

					pItem->SetCount(bCount);
				}
				else if (pItem->IsBook() && pItem->IsStackable() && !IS_SET(pItem->GetAntiFlag(), ITEM_ANTIFLAG_STACK))
				{
#ifdef __EXTENDED_ITEM_COUNT__
					short bCount = pItem->GetCount();
#else
					BYTE bCount = pItem->GetCount();
#endif

					for (int i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
					{
						LPITEM item2 = ch->GetBookInventoryItem(i);

						if (!item2)
							continue;

						if (item2->GetVnum() == pItem->GetVnum())
						{
							//SKILL BOOK FIX: ITEM_STACKABLE
							int j;

							for (j = 0; j < ITEM_SOCKET_MAX_NUM; ++j)
								if (item2->GetSocket(j) != pItem->GetSocket(j))
									break;

							if (j != ITEM_SOCKET_MAX_NUM)
								continue;
							/////////////////////////////////
#ifdef __EXTENDED_ITEM_COUNT__
							short bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#else
							BYTE bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#endif
							bCount -= bCount2;

							item2->SetCount(item2->GetCount() + bCount2);

							if (bCount == 0)
							{
								M2_DESTROY_ITEM(pItem);
								ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CUBE_RENEWAL_SUCCESS"));
								return;
							}
						}
					}

					pItem->SetCount(bCount);
				}
				else if (pItem->IsStone() && pItem->IsStackable() && !IS_SET(pItem->GetAntiFlag(), ITEM_ANTIFLAG_STACK))
				{
#ifdef __EXTENDED_ITEM_COUNT__
					short bCount = pItem->GetCount();
#else
					BYTE bCount = pItem->GetCount();
#endif

					for (int i = 0; i < SPECIAL_INVENTORY_MAX_NUM; ++i)
					{
						LPITEM item2 = ch->GetStoneInventoryItem(i);

						if (!item2)
							continue;

						if (item2->GetVnum() == pItem->GetVnum())
						{

#ifdef __EXTENDED_ITEM_COUNT__
							short bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#else
							BYTE bCount2 = MIN(g_bItemCountLimit - item2->GetCount(), bCount);
#endif
							bCount -= bCount2;

							item2->SetCount(item2->GetCount() + bCount2);

							if (bCount == 0)
							{
								M2_DESTROY_ITEM(pItem);
								ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CUBE_RENEWAL_SUCCESS"));
								return;
							}
						}
					}

					pItem->SetCount(bCount);
				}

#endif


				if (pItem->IsDragonSoul())
				{
					iEmptyPos = ch->GetEmptyDragonSoulInventory(pItem);
					pItem->AddToCharacter(ch, TItemPos(DRAGON_SOUL_INVENTORY, iEmptyPos));
				}

#ifdef ENABLE_SPECIAL_STORAGE
				else if (pItem->IsUpgradeItem())
				{
					iEmptyPos = ch->GetEmptyUpgradeInventory(pItem);
					pItem->AddToCharacter(ch, TItemPos(UPGRADE_INVENTORY, iEmptyPos));
				}
				else if (pItem->IsBook())
				{
					iEmptyPos = ch->GetEmptyBookInventory(pItem);
					pItem->AddToCharacter(ch, TItemPos(BOOK_INVENTORY, iEmptyPos));
				}
				else if (pItem->IsStone())
				{
					iEmptyPos = ch->GetEmptyStoneInventory(pItem);
					pItem->AddToCharacter(ch, TItemPos(STONE_INVENTORY, iEmptyPos));
				}
#endif
				else{
#ifdef ENABLE_CUBE_ATTR_SOCKET
				if (materialInfo.allowCopyAttr == true && copyAttr != NULL)
				{
					pItem->ClearAttribute();
					
					for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; a++)
					{
						if (copyAttr[a][0] > 0)
							pItem->SetForceAttribute(a, copyAttr[a][0], copyAttr[a][1]);
					}
					if (pItem->GetType() == ITEM_WEAPON || pItem->GetType() == ITEM_ARMOR)
					{
						for (int a = 0; a < ITEM_SOCKET_MAX_NUM; a++)
						{
							if(copySockets[a]){
								//pItem->AddSocket();
								pItem->SetSocket(a, copySockets[a]);
							}
						}
					}
				}
#endif		
					iEmptyPos = ch->GetEmptyInventory(pItem->GetSize());
					pItem->AddToCharacter(ch, TItemPos(INVENTORY, iEmptyPos));
				}
				ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("CUBE_RENEWAL_SUCCESS"));
#ifdef ENABLE_SMITH_EFFECT_SYSTEM
				ch->EffectPacket(SE_FR_SUCCESS);
#endif
			}
			else
			{
				ch->ChatPacket(CHAT_TYPE_INFO,LC_TEXT("You don't have the necessary materials."));
			}
		}

		index_value++;
	}
}


void SendDateCubeRenewalPackets(LPCHARACTER ch, BYTE subheader, DWORD npcVNUM)
{
	
	TPacketGCCubeRenewalReceive pack;
	pack.subheader = subheader;

	if(subheader == CUBE_RENEWAL_SUB_HEADER_DATES_RECEIVE)
	{
		const TCubeResultList& resultList = cube_info_map[npcVNUM];
		for (TCubeResultList::const_iterator iter = resultList.begin(); resultList.end() != iter; ++iter)
		{

			const SCubeMaterialInfo& materialInfo = *iter;

			pack.date_cube_renewal.vnum_reward = materialInfo.reward.vnum;
			pack.date_cube_renewal.count_reward = materialInfo.reward.count;

			LPITEM item = ITEM_MANAGER::instance().CreateItem(materialInfo.reward.vnum, materialInfo.reward.count);
			if (item)
			{
				if (item->IsStackable() || !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_STACK)){
					pack.date_cube_renewal.item_reward_stackable = true;
				}else{
					pack.date_cube_renewal.item_reward_stackable = false;
				}
				// BUGFIX: stackable bilgisi icin yaratilan gecici item yok edilmiyordu (pencere acilisinda tarif basina 1 item sizintisi).
				M2_DESTROY_ITEM(item);
			}
			else
			{
				pack.date_cube_renewal.item_reward_stackable = false;
			}

			pack.date_cube_renewal.vnum_material_1 = FN_check_cube_item_vnum_material(materialInfo,1);
			pack.date_cube_renewal.count_material_1 = FN_check_cube_item_count_material(materialInfo,1);

			pack.date_cube_renewal.vnum_material_2 = FN_check_cube_item_vnum_material(materialInfo,2);
			pack.date_cube_renewal.count_material_2 = FN_check_cube_item_count_material(materialInfo,2);

			pack.date_cube_renewal.vnum_material_3 = FN_check_cube_item_vnum_material(materialInfo,3);
			pack.date_cube_renewal.count_material_3 = FN_check_cube_item_count_material(materialInfo,3);

			pack.date_cube_renewal.vnum_material_4 = FN_check_cube_item_vnum_material(materialInfo,4);
			pack.date_cube_renewal.count_material_4 = FN_check_cube_item_count_material(materialInfo,4);

			pack.date_cube_renewal.vnum_material_5 = FN_check_cube_item_vnum_material(materialInfo,5);
			pack.date_cube_renewal.count_material_5 = FN_check_cube_item_count_material(materialInfo,5);

			pack.date_cube_renewal.vnum_material_6 = FN_check_cube_item_vnum_material(materialInfo,6);
			pack.date_cube_renewal.count_material_6 = FN_check_cube_item_count_material(materialInfo,6);

			pack.date_cube_renewal.vnum_material_7 = FN_check_cube_item_vnum_material(materialInfo,7);
			pack.date_cube_renewal.count_material_7 = FN_check_cube_item_count_material(materialInfo,7);

			pack.date_cube_renewal.vnum_material_8 = FN_check_cube_item_vnum_material(materialInfo,8);
			pack.date_cube_renewal.count_material_8 = FN_check_cube_item_count_material(materialInfo,8);

			pack.date_cube_renewal.vnum_material_9 = FN_check_cube_item_vnum_material(materialInfo,9);
			pack.date_cube_renewal.count_material_9 = FN_check_cube_item_count_material(materialInfo,9);

			pack.date_cube_renewal.vnum_material_10 = FN_check_cube_item_vnum_material(materialInfo,10);
			pack.date_cube_renewal.count_material_10 = FN_check_cube_item_count_material(materialInfo,10);

			pack.date_cube_renewal.gold = materialInfo.gold;

			pack.date_cube_renewal.percent = materialInfo.percent;

			memcpy (pack.date_cube_renewal.category, 	materialInfo.category.c_str(), 		sizeof(pack.date_cube_renewal.category));

			LPDESC d = ch->GetDesc();

			if (NULL == d)
			{
				sys_err ("User SendDateCubeRenewalPackets (%s)'s DESC is NULL POINT.", ch->GetName());
				return ;
			}

			d->Packet(&pack, sizeof(pack));
		}
	}
	else{

		LPDESC d = ch->GetDesc();

		if (NULL == d)
		{
			sys_err ("User SendDateCubeRenewalPackets (%s)'s DESC is NULL POINT.", ch->GetName());
			return ;
		}

		d->Packet(&pack, sizeof(pack));
	}
}