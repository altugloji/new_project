#include "stdafx.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc_client.h"
#include "db.h"
#include "log.h"
#include "skill.h"
#include "text_file_loader.h"
#include "priv_manager.h"
#include "questmanager.h"
#include "unique_item.h"
#include "safebox.h"
#include "blend_item.h"
#include "locale_service.h"
#include "item.h"
#include "item_manager.h"
#include "item_manager_private_types.h"
#include "group_text_parse_tree.h"

std::vector<CItemDropInfo> g_vec_pkCommonDropItem[MOB_RANK_MAX_NUM];

bool ITEM_MANAGER::ReadCommonDropItemFile(const char * c_pszFileName) const
{
	FILE * fp = fopen(c_pszFileName, "r");

	if (!fp)
	{
		sys_err("Cannot open %s", c_pszFileName);
		return false;
	}

	char buf[1024];

	[[maybe_unused]] int lines = 0;

	while (fgets(buf, 1024, fp))
	{
		++lines;

		if (!*buf || *buf == '\n')
			continue;

		TDropItem d[MOB_RANK_MAX_NUM];
		char szTemp[64];

		memset(&d, 0, sizeof(d));

		char * p = buf;
		char * p2;

		for (int i = 0; i <= MOB_RANK_S_KNIGHT; ++i)
		{
			for (int j = 0; j < 6; ++j)
			{
				p2 = strchr(p, '\t');

				if (!p2)
					break;

				strlcpy(szTemp, p, MIN(sizeof(szTemp), (p2 - p) + 1));
				p = p2 + 1;

				switch (j)
				{
				case 0: break;
				case 1: str_to_number(d[i].iLvStart, szTemp);	break;
				case 2: str_to_number(d[i].iLvEnd, szTemp);	break;
				case 3: d[i].fPercent = atof(szTemp);	break;
				case 4: strlcpy(d[i].szItemName, szTemp, sizeof(d[i].szItemName));	break;
				case 5: str_to_number(d[i].iCount, szTemp);	break;
				}
			}

			const DWORD dwPct = (DWORD) (d[i].fPercent * 10000.0f);
			DWORD dwItemVnum = 0;

			if (!ITEM_MANAGER::instance().GetValidVnum(d[i].szItemName, dwItemVnum)
				&& !ITEM_MANAGER::instance().GetVnumByOriginalName(d[i].szItemName, dwItemVnum))
			{
				sys_err("No such an item (name: %s)", d[i].szItemName);
				fclose(fp);
				return false;
			}

			if (d[i].iLvStart == 0)
				continue;

			g_vec_pkCommonDropItem[i].emplace_back(CItemDropInfo(d[i].iLvStart, d[i].iLvEnd, dwPct, dwItemVnum));
		}
	}

	fclose(fp);

	for (int i = 0; i < MOB_RANK_MAX_NUM; ++i)
	{
		std::vector<CItemDropInfo> & v = g_vec_pkCommonDropItem[i];
		std::sort(v.begin(), v.end());

		auto it = v.begin();

		sys_log(1, "CommonItemDrop rank %d", i);

		while (it != v.end())
		{
			const CItemDropInfo & c = *(it++);
			sys_log(1, "CommonItemDrop %d %d %d %u", c.m_iLevelStart, c.m_iLevelEnd, c.m_iPercent, c.m_dwVnum);
		}
	}

	return true;
}

bool ITEM_MANAGER::ReadSpecialDropItemFile(const char * c_pszFileName)
{
	CTextFileLoader loader;

	if (!loader.Load(c_pszFileName))
		return false;

	std::string stName;

	for (DWORD i = 0; i < loader.GetChildNodeCount(); ++i)
	{
		loader.SetChildNode(i);

		loader.GetCurrentNodeName(&stName);

		int iVnum;

		if (!loader.GetTokenInteger("vnum", &iVnum))
		{
			sys_err("ReadSpecialDropItemFile : Syntax error %s : no vnum, node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			return false;
		}

		sys_log(0,"DROP_ITEM_GROUP %s %d", stName.c_str(), iVnum);

		TTokenVector * pTok;

		std::string stType;
		int type = CSpecialItemGroup::NORMAL;
		if (loader.GetTokenString("type", &stType))
		{
			stl_lowers(stType);
			if (stType == "pct")
			{
				type = CSpecialItemGroup::PCT;
			}
			else if (stType == "quest")
			{
				type = CSpecialItemGroup::QUEST;
				quest::CQuestManager::instance().RegisterNPCVnum(iVnum);
			}
			else if (stType == "special")
			{
				type = CSpecialItemGroup::SPECIAL;
			}
		}

		if ("attr" == stType)
		{
			auto pkGroup = M2_NEW CSpecialAttrGroup(iVnum);
			for (int k = 1; k < 1024; ++k) // @fixme148 256 -> 1024
			{
				char buf[4];
				snprintf(buf, sizeof(buf), "%d", k);

				if (loader.GetTokenVector(buf, &pTok))
				{
					DWORD apply_type = 0;
					int	apply_value = 0;
					str_to_number(apply_type, pTok->at(0).c_str());
					if (0 == apply_type)
					{
						apply_type = FN_get_apply_type(pTok->at(0).c_str());
						if (0 == apply_type)
						{
							sys_err ("Invalid APPLY_TYPE %s in Special Item Group Vnum %d", pTok->at(0).c_str(), iVnum);
							M2_DELETE(pkGroup); // @fixme340
							return false;
						}
					}
					str_to_number(apply_value, pTok->at(1).c_str());
					if (apply_type > MAX_APPLY_NUM)
					{
						sys_err ("Invalid APPLY_TYPE %u in Special Item Group Vnum %d", apply_type, iVnum);
						M2_DELETE(pkGroup);
						return false;
					}
					pkGroup->m_vecAttrs.emplace_back(CSpecialAttrGroup::CSpecialAttrInfo(apply_type, apply_value));
				}
				else
				{
					break;
				}
			}
			if (loader.GetTokenVector("effect", &pTok))
			{
				pkGroup->m_stEffectFileName = pTok->at(0);
			}
			loader.SetParentNode();
			m_map_pkSpecialAttrGroup.emplace(iVnum, pkGroup);
		}
		else
		{
			auto pkGroup = M2_NEW CSpecialItemGroup(iVnum, type);
			for (int k = 1; k < 1024; ++k) // @fixme148 256 -> 1024
			{
				char buf[4];
				snprintf(buf, sizeof(buf), "%d", k);

				if (loader.GetTokenVector(buf, &pTok))
				{
					const std::string& name = pTok->at(0);
					DWORD dwVnum = 0;

					if (!GetValidVnum(name.c_str(), dwVnum)
						&& !GetVnumByOriginalName(name.c_str(), dwVnum))
					{
						if (name == "경험치" || name == "exp")
						{
							dwVnum = CSpecialItemGroup::EXP;
						}
						else if (name == "mob")
						{
							dwVnum = CSpecialItemGroup::MOB;
						}
						else if (name == "slow")
						{
							dwVnum = CSpecialItemGroup::SLOW;
						}
						else if (name == "drain_hp")
						{
							dwVnum = CSpecialItemGroup::DRAIN_HP;
						}
						else if (name == "poison")
						{
							dwVnum = CSpecialItemGroup::POISON;
						}
#ifdef ENABLE_WOLFMAN_CHARACTER
						else if (name == "bleeding")
						{
							dwVnum = CSpecialItemGroup::BLEEDING;
						}
#endif
						#ifdef ENABLE_MOB_DROP_POLY
						else if (name == "poly")
						{
							dwVnum = CSpecialItemGroup::POLY;
						}
						#endif
						else if (name == "group")
						{
							dwVnum = CSpecialItemGroup::MOB_GROUP;
						}
						else
						{
							sys_err("ReadSpecialDropItemFile : there is no item %s : node %s", name.c_str(), stName.c_str());
							M2_DELETE(pkGroup);
							return false;
						}
					}

					int iCount = 0;
					str_to_number(iCount, pTok->at(1).c_str());
					int iProb = 0;
					str_to_number(iProb, pTok->at(2).c_str());

					int iRarePct = 0;
					if (pTok->size() > 3)
					{
						str_to_number(iRarePct, pTok->at(3).c_str());
					}

					sys_log(0,"        name %s count %d prob %d rare %d", name.c_str(), iCount, iProb, iRarePct);
					pkGroup->AddItem(dwVnum, iCount, iProb, iRarePct);

					// CHECK_UNIQUE_GROUP
					if (iVnum < 30000)
					{
						m_ItemToSpecialGroup[dwVnum] = iVnum;
					}
					// END_OF_CHECK_UNIQUE_GROUP

					continue;
				}

				break;
			}
			loader.SetParentNode();
			if (CSpecialItemGroup::QUEST == type)
			{
				m_map_pkQuestItemGroup.emplace(iVnum, pkGroup);
			}
			else
			{
				m_map_pkSpecialItemGroup.emplace(iVnum, pkGroup);
			}
		}
	}

	return true;
}

bool ITEM_MANAGER::ConvSpecialDropItemFile()
{
	char szSpecialItemGroupFileName[256];
	snprintf(szSpecialItemGroupFileName, sizeof(szSpecialItemGroupFileName),
		"%s/special_item_group.txt", LocaleService_GetBasePath().c_str());

	FILE *fp = fopen("special_item_group_vnum.txt", "w");
	if (!fp)
	{
		sys_err("could not open file (%s)", "special_item_group_vnum.txt");
		return false;
	}

	CTextFileLoader loader;

	if (!loader.Load(szSpecialItemGroupFileName))
	{
		fclose(fp);
		return false;
	}

	std::string stName;

	for (DWORD i = 0; i < loader.GetChildNodeCount(); ++i)
	{
		loader.SetChildNode(i);

		loader.GetCurrentNodeName(&stName);

		int iVnum;

		if (!loader.GetTokenInteger("vnum", &iVnum))
		{
			sys_err("ConvSpecialDropItemFile : Syntax error %s : no vnum, node %s", szSpecialItemGroupFileName, stName.c_str());
			loader.SetParentNode();
			fclose(fp);
			return false;
		}

		std::string str;
		int type = 0;
		if (loader.GetTokenString("type", &str))
		{
			stl_lowers(str);
			if (str == "pct")
				type = 1;
			// @fixme148 BEGIN
			else if (str == "quest")
				type = 2;
			else if (str == "special")
				type = 3;
			else if (str == "attr")
				type = 4;
			// @fixme148 END
		}

		TTokenVector * pTok;

		fprintf(fp, "Group	%s\n", stName.c_str());
		fprintf(fp, "{\n");
		fprintf(fp, "	Vnum	%i\n", iVnum);
		if (type==1)
			fprintf(fp, "	Type	Pct\n");
			// @fixme148 BEGIN
		else if (type==2)
			fprintf(fp, "	Type	Quest\n");
		else if (type==3)
			fprintf(fp, "	Type	special\n");
		else if (type==4)
			fprintf(fp, "	Type	ATTR\n");
			// @fixme148 END

		for (int k = 1; k < 1024; ++k) // @fixme148 256 -> 1024
		{
			char buf[4];
			snprintf(buf, sizeof(buf), "%d", k);

			if (loader.GetTokenVector(buf, &pTok))
			{
				std::string& name = pTok->at(0);
				DWORD dwVnum = 0;

				if (!GetValidVnum(name.c_str(), dwVnum)
					&& !GetVnumByOriginalName(name.c_str(), dwVnum))
				{
					if (
						name == "exp" ||
						name == "mob" ||
						name == "slow" ||
						name == "drain_hp" ||
						name == "poison" ||
#ifdef ENABLE_WOLFMAN_CHARACTER
						name == "bleeding" ||
#endif
						name == "group")
					{
						dwVnum = 0;
					}
					// @fixme148 BEGIN
					else if (name == "경험치")
					{
						dwVnum = 0;
						name = "exp";
					}
					// @fixme148 END
					else
					{
						sys_err("ReadSpecialDropItemFile : there is no item %s : node %s", name.c_str(), stName.c_str());
						fclose(fp);
						return false;
					}
				}

				int iCount = 0;
				str_to_number(iCount, pTok->at(1).c_str());
				int iProb = 0;
				// @fixme148 BEGIN
				if (pTok->size() > 2)
					str_to_number(iProb, pTok->at(2).c_str());
				// @fixme148 END

				int iRarePct = 0;
				if (pTok->size() > 3)
					str_to_number(iRarePct, pTok->at(3).c_str());

				// @fixme148 BEGIN
				if (type==4)
					fprintf(fp, "	%d	%u	%d\n", k, dwVnum, iCount);
				// @fixme148 END
				else
				{
					if (0 == dwVnum)
						fprintf(fp, "	%d	%s	%d	%d\n", k, name.c_str(), iCount, iProb);
					else
						fprintf(fp, "	%d	%u	%d	%d\n", k, dwVnum, iCount, iProb);
				}

				continue;
			}

			break;
		}
		std::string effect;
		if (loader.GetTokenString("effect", &effect))
			fprintf(fp, "	effect	\"%s\"\n", effect.c_str());
		fprintf(fp, "}\n");
		fprintf(fp, "\n");

		loader.SetParentNode();
	}

	fclose(fp);
	return true;
}

bool ITEM_MANAGER::ReadEtcDropItemFile(const char * c_pszFileName)
{
	FILE * fp = fopen(c_pszFileName, "r");

	if (!fp)
	{
		sys_err("Cannot open %s", c_pszFileName);
		return false;
	}

	char buf[512];

	int lines = 0;

#ifdef ENABLE_RELOAD_ETC_DROP_ITEM
	std::map<DWORD, DWORD> map_dwNewProb;
#endif

	while (fgets(buf, 512, fp))
	{
		++lines;

		if (!*buf || *buf == '\n')
			continue;

		char szItemName[256];
		float fProb = 0.0f;

		strlcpy(szItemName, buf, sizeof(szItemName));
		char * cpTab = strrchr(szItemName, '\t');

		if (!cpTab)
			continue;

		*cpTab = '\0';
		fProb = atof(cpTab + 1);

		if (!*szItemName || fProb == 0.0f)
			continue;

		DWORD dwItemVnum = 0;

		if (!ITEM_MANAGER::instance().GetValidVnum(szItemName, dwItemVnum)
			&& !ITEM_MANAGER::instance().GetVnumByOriginalName(szItemName, dwItemVnum))
		{
			sys_err("No such an item (name: %s, line: %d)", szItemName, lines);
			fclose(fp);
			return false;
		}

#ifdef ENABLE_RELOAD_ETC_DROP_ITEM
		map_dwNewProb[dwItemVnum] = (DWORD) (fProb * 10000.0f);
#else
		m_map_dwEtcItemDropProb[dwItemVnum] = (DWORD) (fProb * 10000.0f);
#endif
		sys_log(0, "ETC_DROP_ITEM: %s prob %f", szItemName, fProb);
	}

	fclose(fp);

#ifdef ENABLE_RELOAD_ETC_DROP_ITEM
	m_map_dwEtcItemDropProb.swap(map_dwNewProb);
#endif
	return true;
}

#ifdef ENABLE_RELOAD_ETC_DROP_ITEM
bool ITEM_MANAGER::ReloadEtcDropItemFile()
{
	char szFileName[256];
	snprintf(szFileName, sizeof(szFileName), "%s/etc_drop_item.txt", LocaleService_GetBasePath().c_str());

	if (!ReadEtcDropItemFile(szFileName))
	{
		sys_err("cannot reload ETCDropItem: %s", szFileName);
		return false;
	}

	return true;
}
#endif

// canli /reload m sirasinda satir-basi tablo loglari susturulur (boot ciktisi degismez);
// binlerce sys_log+fflush tum core'larda ayni anda calisip oyun dongusunu takltir
static bool s_bQuietDropLog = false;

bool ITEM_MANAGER::ReadMonsterDropItemGroup(const char * c_pszFileName)
{
	CTextFileLoader loader;

	if (!loader.Load(c_pszFileName))
		return false;

	for (DWORD i = 0; i < loader.GetChildNodeCount(); ++i)
	{
		std::string stName("");

		// node adi ancak child node'a inince okunabiliyor; ust node'da hep bos donuyordu
		// (bos ad = tum hata loglari isimsiz + kr_ atlama hic calismiyordu)
		loader.SetChildNode(i);

		loader.GetCurrentNodeName(&stName);

		if (strncmp (stName.c_str(), "kr_", 3) == 0)
		{
			loader.SetParentNode();
			continue;
		}

		int iMobVnum = 0;
		int iKillDrop = 0;
		int iLevelLimit = 0;

		std::string strType("");

		if (!loader.GetTokenString("type", &strType))
		{
			sys_err("ReadMonsterDropItemGroup : Syntax error %s : no type (kill|drop), node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			return false;
		}

		if (!loader.GetTokenInteger("mob", &iMobVnum))
		{
			sys_err("ReadMonsterDropItemGroup : Syntax error %s : no mob vnum, node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			return false;
		}

		if (strType == "kill")
		{
			if (!loader.GetTokenInteger("kill_drop", &iKillDrop))
			{
				sys_err("ReadMonsterDropItemGroup : Syntax error %s : no kill drop count, node %s", c_pszFileName, stName.c_str());
				loader.SetParentNode();
				return false;
			}
		}
		else
		{
			iKillDrop = 1;
		}

		if ( strType == "limit" )
		{
			if ( !loader.GetTokenInteger("level_limit", &iLevelLimit) )
			{
				sys_err("ReadmonsterDropItemGroup : Syntax error %s : no level_limit, node %s", c_pszFileName, stName.c_str());
				loader.SetParentNode();
				return false;
			}
		}
		else
		{
			iLevelLimit = 0;
		}

		if (!s_bQuietDropLog)
			sys_log(0,"MOB_ITEM_GROUP %s [%s] %d %d", stName.c_str(), strType.c_str(), iMobVnum, iKillDrop);

		if (iKillDrop == 0)
		{
			loader.SetParentNode();
			continue;
		}

		TTokenVector* pTok = nullptr;

		if (strType == "kill")
		{
			auto pkGroup = M2_NEW CMobItemGroup(iMobVnum, iKillDrop, stName);

			for (int k = 1; k < 256; ++k)
			{
				char buf[4];
				snprintf(buf, sizeof(buf), "%d", k);

				if (loader.GetTokenVector(buf, &pTok))
				{
					//sys_log(1, "               %s %s", pTok->at(0).c_str(), pTok->at(1).c_str());
					std::string& name = pTok->at(0);
					DWORD dwVnum = 0;

					// eksik kolonlu satirda at() exception atar; canli reload'da core yerine temiz hata
					if (pTok->size() < 3)
					{
						sys_err("ReadMonsterDropItemGroup : missing count/pct column for item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkGroup);
						return false;
					}

					if (!GetValidVnum(name.c_str(), dwVnum)
						&& !GetVnumByOriginalName(name.c_str(), dwVnum))
					{
						sys_err("ReadMonsterDropItemGroup : there is no item %s : node %s : vnum %d", name.c_str(), stName.c_str(), dwVnum);
						M2_DELETE(pkGroup); // @fixme340
						return false;
					}

					int iCount = 0;
					str_to_number(iCount, pTok->at(1).c_str());

					if (iCount<1)
					{
						sys_err("ReadMonsterDropItemGroup : there is no count for item %s : node %s : vnum %d, count %d", name.c_str(), stName.c_str(), dwVnum, iCount);
						M2_DELETE(pkGroup); // @fixme340
						return false;
					}

					int iPartPct = 0;
					str_to_number(iPartPct, pTok->at(2).c_str());

					if (iPartPct == 0)
					{
						sys_err("ReadMonsterDropItemGroup : there is no drop percent for item %s : node %s : vnum %d, count %d, pct %d", name.c_str(), stName.c_str(), dwVnum, iCount, iPartPct);
						M2_DELETE(pkGroup); // @fixme340
						return false;
					}

					int iRarePct = 0;
					if (pTok->size() > 3)
						str_to_number(iRarePct, pTok->at(3).c_str());
					iRarePct = MINMAX(0, iRarePct, 100);

					if (!s_bQuietDropLog)
						sys_log(0,"        %s count %d rare %d", name.c_str(), iCount, iRarePct);
					pkGroup->AddItem(dwVnum, iCount, iPartPct, iRarePct);
					continue;
				}

				break;
			}
			// ayni mob vnum ikinci kez tanimliysa ilk grup gecerli kalir, kopya birikmesin diye silinir
			if (!m_map_pkMobItemGroup.emplace(iMobVnum, pkGroup).second)
			{
				sys_err("ReadMonsterDropItemGroup : duplicate kill group for mob %d, node %s", iMobVnum, stName.c_str());
				M2_DELETE(pkGroup);
			}

		}
		else if (strType == "drop")
		{
			CDropItemGroup* pkGroup;
			bool bNew = true;
			itertype(m_map_pkDropItemGroup) it = m_map_pkDropItemGroup.find (iMobVnum);
			if (it == m_map_pkDropItemGroup.end())
			{
				pkGroup = M2_NEW CDropItemGroup(0, iMobVnum, stName);
			}
			else
			{
				bNew = false;
				pkGroup = it->second;
			}

			for (int k = 1; k < 256; ++k)
			{
				char buf[4];
				snprintf(buf, sizeof(buf), "%d", k);

				if (loader.GetTokenVector(buf, &pTok))
				{
					std::string& name = pTok->at(0);
					DWORD dwVnum = 0;

					// eksik kolonlu satirda at() exception atar; canli reload'da core yerine temiz hata
					if (pTok->size() < 3)
					{
						sys_err("ReadMonsterDropItemGroup : missing count/pct column for item %s : node %s", name.c_str(), stName.c_str());
						if (bNew)
							M2_DELETE(pkGroup);
						return false;
					}

					if (!GetValidVnum(name.c_str(), dwVnum)
						&& !GetVnumByOriginalName(name.c_str(), dwVnum))
					{
						sys_err("ReadDropItemGroup : there is no item %s : node %s", name.c_str(), stName.c_str());
						if (bNew)
							M2_DELETE(pkGroup);
						return false;
					}

					int iCount = 0;
					str_to_number(iCount, pTok->at(1).c_str());

					if (iCount < 1)
					{
						sys_err("ReadMonsterDropItemGroup : there is no count for item %s : node %s", name.c_str(), stName.c_str());
						if (bNew)
							M2_DELETE(pkGroup);

						return false;
					}

					float fPercent = atof(pTok->at(2).c_str());

					DWORD dwPct = (DWORD)(10000.0f * fPercent);

					if (!s_bQuietDropLog)
						sys_log(0,"        name %s pct %d count %d", name.c_str(), dwPct, iCount);
					pkGroup->AddItem(dwVnum, dwPct, iCount);

					continue;
				}

				break;
			}
			if (bNew)
				m_map_pkDropItemGroup.emplace(iMobVnum, pkGroup);

		}
		else if ( strType == "limit" )
		{
			auto pkLevelItemGroup = M2_NEW CLevelItemGroup(iLevelLimit);

			for ( int k=1; k < 256; k++ )
			{
				char buf[4];
				snprintf(buf, sizeof(buf), "%d", k);

				if ( loader.GetTokenVector(buf, &pTok) )
				{
					std::string& name = pTok->at(0);
					DWORD dwItemVnum = 0;

					// eksik kolonlu satirda at() exception atar; canli reload'da core yerine temiz hata
					if (pTok->size() < 3)
					{
						sys_err("ReadMonsterDropItemGroup : missing count/pct column for item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkLevelItemGroup);
						return false;
					}

					if (!GetValidVnum(name.c_str(), dwItemVnum)
						&& !GetVnumByOriginalName(name.c_str(), dwItemVnum))
					{
						sys_err("ReadDropItemGroup : there is no item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkLevelItemGroup);
						return false;
					}

					int iCount = 0;
					str_to_number(iCount, pTok->at(1).c_str());

					if (iCount < 1)
					{
						sys_err("ReadMonsterDropItemGroup : there is no count for item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkLevelItemGroup);
						return false;
					}

					float fPct = atof(pTok->at(2).c_str());
					DWORD dwPct = (DWORD)(10000.0f * fPct);

					if (!s_bQuietDropLog)
						sys_log(0,"        name %s pct %d count %d", name.c_str(), dwPct, iCount);
					pkLevelItemGroup->AddItem(dwItemVnum, dwPct, iCount);

					continue;
				}

				break;
			}

			if (!m_map_pkLevelItemGroup.emplace(iMobVnum, pkLevelItemGroup).second)
			{
				sys_err("ReadMonsterDropItemGroup : duplicate limit group for mob %d, node %s", iMobVnum, stName.c_str());
				M2_DELETE(pkLevelItemGroup);
			}
		}
		else if (strType == "thiefgloves")
		{
			auto pkGroup = M2_NEW CBuyerThiefGlovesItemGroup(0, iMobVnum, stName);

			for (int k = 1; k < 256; ++k)
			{
				char buf[4];
				snprintf(buf, sizeof(buf), "%d", k);

				if (loader.GetTokenVector(buf, &pTok))
				{
					std::string& name = pTok->at(0);
					DWORD dwVnum = 0;

					// eksik kolonlu satirda at() exception atar; canli reload'da core yerine temiz hata
					if (pTok->size() < 3)
					{
						sys_err("ReadMonsterDropItemGroup : missing count/pct column for item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkGroup);
						return false;
					}

					if (!GetValidVnum(name.c_str(), dwVnum)
						&& !GetVnumByOriginalName(name.c_str(), dwVnum))
					{
						sys_err("ReadDropItemGroup : there is no item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkGroup);
						return false;
					}

					int iCount = 0;
					str_to_number(iCount, pTok->at(1).c_str());

					if (iCount < 1)
					{
						sys_err("ReadMonsterDropItemGroup : there is no count for item %s : node %s", name.c_str(), stName.c_str());
						M2_DELETE(pkGroup);

						return false;
					}

					float fPercent = atof(pTok->at(2).c_str());

					DWORD dwPct = (DWORD)(10000.0f * fPercent);

					if (!s_bQuietDropLog)
						sys_log(0,"        name %s pct %d count %d", name.c_str(), dwPct, iCount);
					pkGroup->AddItem(dwVnum, dwPct, iCount);

					continue;
				}

				break;
			}

			if (!m_map_pkGloveItemGroup.emplace(iMobVnum, pkGroup).second)
			{
				sys_err("ReadMonsterDropItemGroup : duplicate thiefgloves group for mob %d, node %s", iMobVnum, stName.c_str());
				M2_DELETE(pkGroup);
			}
		}
		else
		{
			sys_err("ReadMonsterDropItemGroup : Syntax error %s : invalid type %s (kill|drop), node %s", c_pszFileName, strType.c_str(), stName.c_str());
			loader.SetParentNode();
			return false;
		}

		loader.SetParentNode();
	}

	return true;
}

#ifdef ENABLE_RELOAD_MOB_DROP_ITEM
bool ITEM_MANAGER::ReloadMobDropItemFile()
{
	// drop_item_group.txt ile mob_drop_item.txt ayni m_map_pkDropItemGroup tablosunu
	// besledigi icin ikisi boot sirasiyla birlikte okunur. Mevcut tablolar kenara alinir;
	// parse hata verirse eskiler geri konur, yarim yuklu tablo hicbir an olusmaz.
	std::map<DWORD, CMobItemGroup*> map_pkOldMobItemGroup;
	std::map<DWORD, CDropItemGroup*> map_pkOldDropItemGroup;
	std::map<DWORD, CLevelItemGroup*> map_pkOldLevelItemGroup;
	std::map<DWORD, CBuyerThiefGlovesItemGroup*> map_pkOldGloveItemGroup;

	m_map_pkMobItemGroup.swap(map_pkOldMobItemGroup);
	m_map_pkDropItemGroup.swap(map_pkOldDropItemGroup);
	m_map_pkLevelItemGroup.swap(map_pkOldLevelItemGroup);
	m_map_pkGloveItemGroup.swap(map_pkOldGloveItemGroup);

	char szDropItemGroupFileName[256];
	char szMobDropItemFileName[256];
	snprintf(szDropItemGroupFileName, sizeof(szDropItemGroupFileName), "%s/drop_item_group.txt", LocaleService_GetBasePath().c_str());
	snprintf(szMobDropItemFileName, sizeof(szMobDropItemFileName), "%s/mob_drop_item.txt", LocaleService_GetBasePath().c_str());

	bool bOk = false;
	s_bQuietDropLog = true;

	// beklenmedik bir parse exception'i canli sunucuyu dusurmesin: rollback yolu calisir
	try
	{
		bOk = ReadDropItemGroup(szDropItemGroupFileName) && ReadMonsterDropItemGroup(szMobDropItemFileName);
	}
	catch (...)
	{
		sys_err("ReloadMobDropItemFile: exception during parse");
		bOk = false;
	}

	s_bQuietDropLog = false;

	std::map<DWORD, CMobItemGroup*> * pMapDeleteMob = &map_pkOldMobItemGroup;
	std::map<DWORD, CDropItemGroup*> * pMapDeleteDrop = &map_pkOldDropItemGroup;
	std::map<DWORD, CLevelItemGroup*> * pMapDeleteLevel = &map_pkOldLevelItemGroup;
	std::map<DWORD, CBuyerThiefGlovesItemGroup*> * pMapDeleteGlove = &map_pkOldGloveItemGroup;

	if (!bOk)
	{
		sys_err("ReloadMobDropItemFile: parse failed, keeping previous drop tables");

		// yarim yuklenen yeni gruplar silinecek, eski tablolar geri gelecek
		m_map_pkMobItemGroup.swap(map_pkOldMobItemGroup);
		m_map_pkDropItemGroup.swap(map_pkOldDropItemGroup);
		m_map_pkLevelItemGroup.swap(map_pkOldLevelItemGroup);
		m_map_pkGloveItemGroup.swap(map_pkOldGloveItemGroup);
	}

	for (itertype(*pMapDeleteMob) it = pMapDeleteMob->begin(); it != pMapDeleteMob->end(); ++it)
		M2_DELETE(it->second);
	for (itertype(*pMapDeleteDrop) it = pMapDeleteDrop->begin(); it != pMapDeleteDrop->end(); ++it)
		M2_DELETE(it->second);
	for (itertype(*pMapDeleteLevel) it = pMapDeleteLevel->begin(); it != pMapDeleteLevel->end(); ++it)
		M2_DELETE(it->second);
	for (itertype(*pMapDeleteGlove) it = pMapDeleteGlove->begin(); it != pMapDeleteGlove->end(); ++it)
		M2_DELETE(it->second);

	return bOk;
}
#endif

bool ITEM_MANAGER::ReadDropItemGroup(const char * c_pszFileName)
{
	CTextFileLoader loader;

	if (!loader.Load(c_pszFileName))
		return false;

	std::string stName;

	for (DWORD i = 0; i < loader.GetChildNodeCount(); ++i)
	{
		loader.SetChildNode(i);

		loader.GetCurrentNodeName(&stName);

		int iVnum;
		int iMobVnum;

		if (!loader.GetTokenInteger("vnum", &iVnum))
		{
			sys_err("ReadDropItemGroup : Syntax error %s : no vnum, node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			return false;
		}

		if (!loader.GetTokenInteger("mob", &iMobVnum))
		{
			sys_err("ReadDropItemGroup : Syntax error %s : no mob vnum, node %s", c_pszFileName, stName.c_str());
			loader.SetParentNode();
			return false;
		}

		if (!s_bQuietDropLog)
			sys_log(0,"DROP_ITEM_GROUP %s %d", stName.c_str(), iMobVnum);

		TTokenVector * pTok;

		itertype(m_map_pkDropItemGroup) it = m_map_pkDropItemGroup.find(iMobVnum);

		CDropItemGroup* pkGroup;

		if (it == m_map_pkDropItemGroup.end())
			pkGroup = M2_NEW CDropItemGroup(iVnum, iMobVnum, stName);
		else
			pkGroup = it->second;

		for (int k = 1; k < 256; ++k)
		{
			char buf[4];
			snprintf(buf, sizeof(buf), "%d", k);

			if (loader.GetTokenVector(buf, &pTok))
			{
				std::string& name = pTok->at(0);
				DWORD dwVnum = 0;

				// eksik kolonlu satirda at() exception atar; canli reload'da core yerine temiz hata
				if (pTok->size() < 2)
				{
					sys_err("ReadDropItemGroup : missing percent column for item %s : node %s", name.c_str(), stName.c_str());
					if (it == m_map_pkDropItemGroup.end())
						M2_DELETE(pkGroup);
					return false;
				}

				if (!GetValidVnum(name.c_str(), dwVnum)
					&& !GetVnumByOriginalName(name.c_str(), dwVnum))
				{
					sys_err("ReadDropItemGroup : there is no item %s : node %s", name.c_str(), stName.c_str());
					if (it == m_map_pkDropItemGroup.end())
						M2_DELETE(pkGroup);
					return false;
				}

				const float fPercent = atof(pTok->at(1).c_str());

				const DWORD dwPct = (DWORD)(10000.0f * fPercent);

				int iCount = 1;
				if (pTok->size() > 2)
					str_to_number(iCount, pTok->at(2).c_str());

				if (iCount < 1)
				{
					sys_err("ReadDropItemGroup : there is no count for item %s : node %s", name.c_str(), stName.c_str());

					if (it == m_map_pkDropItemGroup.end())
						M2_DELETE(pkGroup);

					return false;
				}

				if (!s_bQuietDropLog)
					sys_log(0,"        %s %d %d", name.c_str(), dwPct, iCount);
				pkGroup->AddItem(dwVnum, dwPct, iCount);
				continue;
			}

			break;
		}

		if (it == m_map_pkDropItemGroup.end())
			m_map_pkDropItemGroup.emplace(iMobVnum, pkGroup);

		loader.SetParentNode();
	}

	return true;
}

bool ITEM_MANAGER::ReadItemVnumMaskTable(const char * c_pszFileName)
{
	FILE *fp = fopen(c_pszFileName, "r");
	if (!fp)
	{
		return false;
	}

	int ori_vnum, new_vnum;
	while (fscanf(fp, "%u %u", &ori_vnum, &new_vnum) != EOF)
	{
		m_map_new_to_ori.emplace(new_vnum, ori_vnum);
	}
	fclose(fp);
	return true;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
