# -*- coding: utf-8 -*-
#
# Attribute name resolver for the player bonus (AttributeList) window.
#
# Maps a player.POINT_* type to its display string. The strings are taken from
# the already-translated localeInfo.TOOLTIP_* entries whenever they exist, so the
# bonus window is localized for free. A short ASCII fallback is used only when a
# given locale is missing that TOOLTIP key, and POINT types that do not exist in
# this client build are simply skipped (so the module can never fail to import).
#
import player
import localeInfo


def _P(name):
	return getattr(player, name, None)


def _S(name, fallback):
	return getattr(localeInfo, name, fallback)


# (player point name, localeInfo tooltip name, ascii fallback)
_RAW = (
	("POINT_CRITICAL_PCT",			"TOOLTIP_APPLY_CRITICAL_PCT",		"Kritik Vurus Sansi: +%d%%"),
	("POINT_PENETRATE_PCT",			"TOOLTIP_APPLY_PENETRATE_PCT",		"Delici Vurus Sansi: +%d%%"),
	("POINT_POISON_PCT",			"TOOLTIP_APPLY_POISON_PCT",			"Zehirleme Sansi: +%d%%"),
	("POINT_STUN_PCT",				"TOOLTIP_APPLY_STUN_PCT",			"Sersemletme Sansi: +%d%%"),
	("POINT_SLOW_PCT",				"TOOLTIP_APPLY_SLOW_PCT",			"Yavaslatma Sansi: +%d%%"),
	("POINT_SKILL_DAMAGE_BONUS",	"TOOLTIP_SKILL_DAMAGE_BONUS",		"Yetenek Hasari: +%d%%"),
	("POINT_NORMAL_HIT_DAMAGE_BONUS","TOOLTIP_NORMAL_HIT_DAMAGE_BONUS",	"Normal Vurus Hasari: +%d%%"),
	("POINT_REFLECT_MELEE",			"TOOLTIP_APPLY_REFLECT_MELEE",		"Saldiriyi Yansitma: +%d%%"),
	("POINT_REFLECT_ARROW",			"TOOLTIP_APPLY_REFLECT_ARROW",		"Oku Yansitma: +%d%%"),

	("POINT_ATTBONUS_ANIMAL",		"TOOLTIP_APPLY_ATTBONUS_ANIMAL",	"Hayvanlara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_ORC",			"TOOLTIP_APPLY_ATTBONUS_ORC",		"Orklara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_MILGYO",		"TOOLTIP_APPLY_ATTBONUS_MILGYO",	"Mistiklere Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_UNDEAD",		"TOOLTIP_APPLY_ATTBONUS_UNDEAD",	"Olulere Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_DEVIL",		"TOOLTIP_APPLY_ATTBONUS_DEVIL",		"Seytanlara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_STONE",		"TOOLTIP_APPLY_ATTBONUS_STONE",		"Taslara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_BOSS",			"TOOLTIP_APPLY_ATTBONUS_BOSS",		"Patronlara Karsi Guc: +%d%%"),

	("POINT_ATTBONUS_HUMAN",		"TOOLTIP_APPLY_ATTBONUS_HUMAN",		"Insanlara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_WARRIOR",		"TOOLTIP_APPLY_ATTBONUS_WARRIOR",	"Savascilara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_ASSASSIN",		"TOOLTIP_APPLY_ATTBONUS_ASSASSIN",	"Suikastcilara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_SURA",			"TOOLTIP_APPLY_ATTBONUS_SURA",		"Suralara Karsi Guc: +%d%%"),
	("POINT_ATTBONUS_SHAMAN",		"TOOLTIP_APPLY_ATTBONUS_SHAMAN",	"Samanlara Karsi Guc: +%d%%"),

	("POINT_SKILL_DEFEND_BONUS",	"TOOLTIP_SKILL_DEFEND_BONUS",		"Yetenek Savunmasi: +%d%%"),
	("POINT_NORMAL_HIT_DEFEND_BONUS","TOOLTIP_NORMAL_HIT_DEFEND_BONUS",	"Normal Vurus Savunmasi: +%d%%"),
	("POINT_RESIST_CRITICAL",		"TOOLTIP_ANTI_CRITICAL_PCT",		"Kritik Vurusa Direnc: +%d%%"),
	("POINT_RESIST_PENETRATE",		"TOOLTIP_ANTI_PENETRATE_PCT",		"Delici Vurusa Direnc: +%d%%"),
	("POINT_BLOCK",					"TOOLTIP_APPLY_BLOCK",				"Blok Sansi: +%d%%"),
	("POINT_DODGE",					"TOOLTIP_APPLY_DODGE",				"Kacma Sansi: +%d%%"),
	("POINT_POISON_REDUCE",			"TOOLTIP_APPLY_POISON_REDUCE",		"Zehre Direnc: +%d%%"),

	("POINT_RESIST_HUMAN",			"TOOLTIP_APPLY_RESIST_HUMAN",		"Insanlara Karsi Direnc: +%d%%"),
	("POINT_RESIST_WARRIOR",		"TOOLTIP_APPLY_RESIST_WARRIOR",		"Savascilara Karsi Direnc: +%d%%"),
	("POINT_RESIST_ASSASSIN",		"TOOLTIP_APPLY_RESIST_ASSASSIN",	"Suikastcilara Karsi Direnc: +%d%%"),
	("POINT_RESIST_SURA",			"TOOLTIP_APPLY_RESIST_SURA",		"Suralara Karsi Direnc: +%d%%"),
	("POINT_RESIST_SHAMAN",			"TOOLTIP_APPLY_RESIST_SHAMAN",		"Samanlara Karsi Direnc: +%d%%"),
	("POINT_RESIST_SWORD",			"TOOLTIP_APPLY_RESIST_SWORD",		"Kilica Karsi Direnc: +%d%%"),
	("POINT_RESIST_TWOHAND",		"TOOLTIP_APPLY_RESIST_TWOHAND",		"Cift Ele Karsi Direnc: +%d%%"),
	("POINT_RESIST_DAGGER",			"TOOLTIP_APPLY_RESIST_DAGGER",		"Hancere Karsi Direnc: +%d%%"),
	("POINT_RESIST_BELL",			"TOOLTIP_APPLY_RESIST_BELL",		"Zile Karsi Direnc: +%d%%"),
	("POINT_RESIST_FAN",			"TOOLTIP_APPLY_RESIST_FAN",			"Yelpazeye Karsi Direnc: +%d%%"),
	("POINT_RESIST_BOW",			"TOOLTIP_RESIST_BOW",				"Oka Karsi Direnc: +%d%%"),
	("POINT_RESIST_MAGIC",			"TOOLTIP_RESIST_MAGIC",				"Sihire Karsi Direnc: +%d%%"),

	("POINT_STEAL_HP",				"TOOLTIP_APPLY_STEAL_HP",			"CP Calma: +%d%%"),
	("POINT_STEAL_SP",				"TOOLTIP_APPLY_STEAL_SP",			"MP Calma: +%d%%"),
	("POINT_MANA_BURN_PCT",			"TOOLTIP_APPLY_MANA_BURN_PCT",		"MP Yakma Sansi: +%d%%"),
	("POINT_HP_REGEN",				"TOOLTIP_HP_REGEN",					"CP Yenileme: +%d%%"),
	("POINT_SP_REGEN",				"TOOLTIP_SP_REGEN",					"MP Yenileme: +%d%%"),
	("POINT_ST_REGEN",				"TOOLTIP_ST_REGEN",					"Dayaniklilik Yenileme: +%d%%"),
	("POINT_SKILL_DURATION",		"TOOLTIP_APPLY_SKILL_DURATION",		"Yetenek Suresi: +%d%%"),
	("POINT_ATTBONUS_CZ",		"TOOLTIP_APPLY_ATTBONUS_CZ",		"Surgune Karsi Guc: +%d%%"),
	("POINT_ENCHANT_DARK",		"TOOLTIP_RESIST_DARK",		"Surgune Karsi Direnc: +%d%%"),
	("POINT_RESIST_FIRE",		"TOOLTIP_RESIST_FIRE",		"Ates direnci: +%d%%"),
	("POINT_RESIST_WIND",		"TOOLTIP_APPLY_RESIST_WIND",		"Ruzgar direnci: +%d%%"),
	("POINT_RESIST_ELEC",		"TOOLTIP_RESIST_ELEC",		"Simsek direnci: +%d%%"),
)

AFFECT_DICT = {}
for _pname, _sname, _fb in _RAW:
	_pid = _P(_pname)
	if _pid is not None:
		AFFECT_DICT[_pid] = _S(_sname, _fb)


def GetApplyString(affectType, affectValue):
	if 0 == affectType:
		return None

	if 0 == affectValue:
		return None

	fmt = AFFECT_DICT.get(affectType)
	if fmt is None:
		return "UNKNOWN_TYPE[%s] %s" % (affectType, affectValue)

	# Locale values may be wrapped into callables (SA/SNA/... pluralisation
	# helpers) by LoadLocaleFile, or be plain printf-style strings/fallbacks.
	if callable(fmt):
		try:
			return fmt(affectValue)
		except:
			return fmt

	try:
		return fmt % (affectValue)
	except (TypeError, ValueError):
		return fmt
