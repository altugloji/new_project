#include "stdafx.h"

#include "questmanager.h"
#include "DragonLair.h"
#include "char.h"
#include "guild.h"
#ifdef BERAN_SETAOU
	#include "beran_setaou.h"
#endif

namespace quest
{
	ALUA(dl_startRaid)
	{
		const LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const long baseMapIndex = lua_tonumber(L, -1);

		CDragonLairManager::instance().Start(ch->GetMapIndex(), baseMapIndex, ch->GetGuild()->GetID());

		return 0;
	}
#ifdef BERAN_SETAOU
	int bs_canJoin(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			lua_pushnumber(L, CBeranSetaou::Instance().CanJoin(ch));
		}
		return 1;
	}
	int bs_startRequest(lua_State* L)
	{
		if (!lua_isnumber(L, 1)) {
			sys_err("bs_startRequest: invalid arguments");
			return 0;
		}
		uint32_t roomPasswd = (uint32_t)lua_tonumber(L, 1);

		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			lua_pushnumber(L, CBeranSetaou::Instance().StartRequest(ch, roomPasswd, ch->GetParty() != NULL));
		}
		return 1;
	}
	int bs_get_password(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			lua_pushnumber(L, CBeranSetaou::Instance().GetRoomPassword());
		}
		return 1;
	}
	int bs_get_room_state(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			lua_pushnumber(L, CBeranSetaou::Instance().GetRoomState());
		}
		return 1;
	}
	int bs_get_master_name(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			lua_pushstring(L, CBeranSetaou::Instance().GetMasterName());
		}
		return 1;
	}
	int bs_is_empty(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			lua_pushnumber(L, CBeranSetaou::Instance().IsCrystalRoomEmpty());
		}
		return 1;
	}
	int bs_join_player(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch) {
			CBeranSetaou::Instance().JoinPlayer(ch);
		}
		return 1;
	}
#endif

	void RegisterDragonLairFunctionTable()
	{
		luaL_reg dl_functions[] =
		{
			{	"startRaid",	dl_startRaid	},
#ifdef BERAN_SETAOU
			{ "can_join",			bs_canJoin },
			{ "start_request",		bs_startRequest },
			{ "get_password",		bs_get_password },
			{ "get_master_name",	bs_get_master_name },
			{ "is_empty",			bs_is_empty },
			{ "join_player",		bs_join_player },
#endif
			{nullptr, nullptr}
		};

		CQuestManager::instance(). AddLuaFunctionTable("DragonLair", dl_functions);
	}
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
