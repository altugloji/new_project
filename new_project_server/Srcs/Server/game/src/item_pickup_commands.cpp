#include "stdafx.h"

#include "cmd.h"
#include "char.h"
#include "desc.h"
#include "config.h"
#include "questmanager.h"
#include "utils.h"

namespace
{
	constexpr const char* ITEM_PICKUP_AUTH_FLAG = "pickup_auth_enabled";
	constexpr const char* ITEM_PICKUP_BLOCK_FLAG = "pickup_auth_autoblock";

	bool ParseExplicitSwitch(const char* argument, bool& enabled)
	{
		if (!argument || !*argument)
			return false;

		if (!strcmp(argument, "1") || !strcasecmp(argument, "on"))
		{
			enabled = true;
			return true;
		}

		if (!strcmp(argument, "0") || !strcasecmp(argument, "off"))
		{
			enabled = false;
			return true;
		}

		return false;
	}

	bool CanManagePickupSecurity(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetGMLevel() >= GM_IMPLEMENTOR;
	}

	void ShowPickupSecurityStatus(LPCHARACTER ch)
	{
		ch->ChatPacket(CHAT_TYPE_INFO,
			"[PICKUP-SECURITY] auth=%s autoblock=%s",
			g_bItemPickupAuthEnabled ? "ON" : "OFF (legacy allowed)",
			g_bItemPickupAutoBlockEnabled ? "ON" : "OFF");
	}

	void AuditPickupSecurityRequest(LPCHARACTER ch, const char* setting, bool enabled)
	{
		const LPDESC desc = ch->GetDesc();
		sys_err("GM_PICKUP_SECURITY gm=%s pid=%u login=%s ip=%s core=%s channel=%u setting=%s requested=%u",
			ch->GetName(),
			ch->GetPlayerID(),
			desc ? desc->GetAccountTable().login : "",
			desc ? desc->GetHostName() : "",
			g_stHostname.c_str(),
			static_cast<unsigned int>(g_bChannel),
			setting,
			enabled ? 1U : 0U);
	}
}

ACMD(do_pickup_auth)
{
	if (!CanManagePickupSecurity(ch))
		return;

	char arg[32]{};
	one_argument(argument, arg, sizeof(arg));

	if (!*arg || !strcasecmp(arg, "status"))
	{
		ShowPickupSecurityStatus(ch);
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: /pickup_auth <0|1|off|on>");
		return;
	}

	bool enabled = false;
	if (!ParseExplicitSwitch(arg, enabled))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: /pickup_auth <0|1|off|on>");
		return;
	}

	quest::CQuestManager::instance().SetEventFlag(ITEM_PICKUP_AUTH_FLAG, enabled ? 1 : 0);
	quest::CQuestManager::instance().RequestSetEventFlag(ITEM_PICKUP_AUTH_FLAG, enabled ? 1 : 0);
	AuditPickupSecurityRequest(ch, "auth", enabled);
	ch->ChatPacket(CHAT_TYPE_INFO,
		"[PICKUP-SECURITY] auth=%s applied locally; sync sent to all cores.",
		enabled ? "ON" : "OFF (legacy allowed)");
}

ACMD(do_pickup_block)
{
	if (!CanManagePickupSecurity(ch))
		return;

	char arg[32]{};
	one_argument(argument, arg, sizeof(arg));

	if (!*arg || !strcasecmp(arg, "status"))
	{
		ShowPickupSecurityStatus(ch);
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: /pickup_block <0|1|off|on>");
		return;
	}

	bool enabled = false;
	if (!ParseExplicitSwitch(arg, enabled))
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Usage: /pickup_block <0|1|off|on>");
		return;
	}

	quest::CQuestManager::instance().SetEventFlag(ITEM_PICKUP_BLOCK_FLAG, enabled ? 1 : 0);
	quest::CQuestManager::instance().RequestSetEventFlag(ITEM_PICKUP_BLOCK_FLAG, enabled ? 1 : 0);
	AuditPickupSecurityRequest(ch, "autoblock", enabled);
	ch->ChatPacket(CHAT_TYPE_INFO,
		"[PICKUP-SECURITY] autoblock=%s applied locally; sync sent to all cores.",
		enabled ? "ON" : "OFF");
}
