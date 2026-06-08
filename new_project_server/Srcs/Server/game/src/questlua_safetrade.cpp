#include "stdafx.h"
#ifdef ENABLE_SAFE_TRADE_SYSTEM
#include "questmanager.h"
#include "questlua.h"
#include "char.h"
#include "safetrade.h"
#include "lua_incl.h"

namespace quest
{
	// safetrade.start(name) -> int kod (0=OK, 1..5 hata, bkz. ESafeTradeStartResult)
	ALUA(safetrade_start)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch)
		{
			lua_pushnumber(L, SAFETRADE_START_BUSY);
			return 1;
		}
		const char* name = lua_isstring(L, 1) ? lua_tostring(L, 1) : "";
		lua_pushnumber(L, CSafeTradeManager::instance().StartRequest(ch, name));
		return 1;
	}

	// safetrade.is_open() -> bool  (A'nın açık depo oturumu var mı)
	ALUA(safetrade_is_open)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		lua_pushboolean(L, (ch && ch->GetSafeTrade()) ? 1 : 0);
		return 1;
	}

	// safetrade.list_incoming()  (B: gelen READY_TO_CLAIM trade penceresi)
	ALUA(safetrade_list_incoming)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch)
			CSafeTradeManager::instance().RequestIncomingList(ch);
		return 0;
	}

	// safetrade.list_outgoing()  (A: gönderdiğim, B'yi bekleyen trade'ler)
	ALUA(safetrade_list_outgoing)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch)
			CSafeTradeManager::instance().RequestOutgoingList(ch);
		return 0;
	}

	void RegisterSafeTradeFunctionTable()
	{
		luaL_reg safetrade_functions[] =
		{
			{ "start",         safetrade_start         },
			{ "is_open",       safetrade_is_open       },
			{ "list_incoming", safetrade_list_incoming },
			{ "list_outgoing", safetrade_list_outgoing },
			{ nullptr, nullptr }
		};
		CQuestManager::instance().AddLuaFunctionTable("safetrade", safetrade_functions);
	}
}
#endif // ENABLE_SAFE_TRADE_SYSTEM
