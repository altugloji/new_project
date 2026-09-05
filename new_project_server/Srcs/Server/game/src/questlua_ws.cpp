#include "stdafx.h"

#ifdef ENABLE_WS_TOURNAMENT

#include "questmanager.h"
#include "char.h"
#include "char_manager.h"
#include "ws_tournament.h"

// ============================================================================
// WS 1v1 Turnuva quest API'si ("ws" tablosu)
// NPC 20082 map 112'de durdugu icin bu fonksiyonlar host core'da calisir;
// baska core'da cagrilirlarsa yerel (bos) durumu gorurler - quest tasarimi
// geregi yalniz 20082 diyaloglarinda kullanilmalidirlar.
// ============================================================================

namespace quest
{
	ALUA(ws_get_state)
	{
		lua_pushnumber(L, CWSTournamentManager::instance().GetState());
		return 1;
	}

	ALUA(ws_get_fee)
	{
		lua_pushnumber(L, (double) CWSTournamentManager::instance().GetFee());
		return 1;
	}

	ALUA(ws_get_count)
	{
		lua_pushnumber(L, CWSTournamentManager::instance().GetEntryCount());
		return 1;
	}

	ALUA(ws_is_registered)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushboolean(L, ch != nullptr && CWSTournamentManager::instance().IsRegistered(ch->GetPlayerID()));
		return 1;
	}

	ALUA(ws_register)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushnumber(L, (ch != nullptr) ? CWSTournamentManager::instance().QuestRegister(ch) : WS_REG_ERR_DB);
		return 1;
	}

	ALUA(ws_unregister)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushnumber(L, (ch != nullptr) ? CWSTournamentManager::instance().QuestUnregister(ch->GetPlayerID()) : 1);
		return 1;
	}

	ALUA(ws_show_participants)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch != nullptr)
			CWSTournamentManager::instance().ShowParticipants(ch);
		return 0;
	}

	// ws.create(ucret, set, mac_dk, minlv, maxlv, sinif, kayit_dk) -> 0 ok
	ALUA(ws_create)
	{
		TWSConfig kConfig;
		kConfig.llFee = (long long) lua_tonumber(L, 1);
		kConfig.iSetCount = (int) lua_tonumber(L, 2);
		kConfig.iMatchMinutes = (int) lua_tonumber(L, 3);
		kConfig.iMinLevel = (int) lua_tonumber(L, 4);
		kConfig.iMaxLevel = (int) lua_tonumber(L, 5);
		kConfig.iJobFilter = (int) lua_tonumber(L, 6);
		const int iRegMinutes = (int) lua_tonumber(L, 7);

		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushnumber(L, CWSTournamentManager::instance().QuestCreate(kConfig, iRegMinutes, (ch != nullptr) ? ch->GetName() : "quest"));
		return 1;
	}

	ALUA(ws_start_now)
	{
		CWSTournamentManager::instance().QuestStartNow();
		return 0;
	}

	ALUA(ws_cancel)
	{
		CWSTournamentManager::instance().QuestCancel();
		return 0;
	}

	void RegisterWSFunctionTable()
	{
		luaL_reg ws_functions[] =
		{
			{ "get_state",			ws_get_state			},
			{ "get_fee",			ws_get_fee				},
			{ "get_count",			ws_get_count			},
			{ "is_registered",		ws_is_registered		},
			{ "register",			ws_register				},
			{ "unregister",			ws_unregister			},
			{ "show_participants",	ws_show_participants	},
			{ "create",				ws_create				},
			{ "start_now",			ws_start_now			},
			{ "cancel",				ws_cancel				},

			{ nullptr,				nullptr					}
		};

		CQuestManager::instance().AddLuaFunctionTable("ws", ws_functions);
	}
}

#endif // ENABLE_WS_TOURNAMENT
