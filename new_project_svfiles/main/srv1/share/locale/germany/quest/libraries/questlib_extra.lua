-- ########################################################################################
-- ### MARTY LUA LIBRARY FOR ASF_PROJECT
-- ########################################################################################
if QUESTLIB_EXTRA_LUA ~= nil then return end -- include_guard begin
QUESTLIB_EXTRA_LUA=2.3

ENABLE_AUTOSET_EVENT_FLAGS = false -- if true, set the event flags automatically at startup

-- POINT DECLARING BEGIN
POINT_RAMADAN_CANDY_BONUS_EXP = 127
POINT_ENERGY = 128
POINT_ENERGY_END_TIME = 129

POINT_COSTUME_ATTR_BONUS = 130
POINT_MAGIC_ATT_BONUS_PER = 131
POINT_MELEE_MAGIC_ATT_BONUS_PER = 132

POINT_RESIST_ICE = 133
POINT_RESIST_EARTH = 134
POINT_RESIST_DARK = 135

POINT_RESIST_CRITICAL = 136
POINT_RESIST_PENETRATE = 137

POINT_BLEEDING_REDUCE = 138
POINT_BLEEDING_PCT = 139

POINT_ATTBONUS_WOLFMAN = 140
POINT_RESIST_WOLFMAN = 141
POINT_RESIST_CLAW = 142

POINT_ACCEDRAIN_RATE = 143
POINT_RESIST_MAGIC_REDUCTION = 144
-- POINT DECLARING END

-- RACE DECLARING BEGIN
WARRIOR_M	= 0
NINJA_W		= 1
SURA_M		= 2
SHAMAN_W	= 3
WARRIOR_W	= 4
NINJA_M		= 5
SURA_W		= 6
SHAMAN_M	= 7
LYCAN_M	= 8
ASSASSIN_W	= NINJA_W
ASSASSIN_M	= NINJA_M
WOLFMAN_M	= LYCAN_M

WARRIOR = 0
NINJA = 1
SURA = 2
SHAMAN = 3
LYCAN = 4
ASSASSIN = NINJA
WOLFMAN = LYCAN
-- RACE DECLARING END
-- ########################################################################################

-- WEAPON_TYPE DECLARING BEGIN
WEAPON_SWORD		= 0
WEAPON_DAGGER		= 1
WEAPON_BOW			= 2
WEAPON_TWO_HANDED	= 3
WEAPON_BELL			= 4
WEAPON_FAN			= 5
WEAPON_ARROW		= 6
WEAPON_MOUNT_SPEAR	= 7
WEAPON_CLAW			= 8
WEAPON_QUIVER		= 9
WEAPON_BOUQUET		= 10
-- WEAPON_TYPE DECLARING END
-- ########################################################################################

-- ########################################################################################
-- AFF DECLARING BEGIN
AFF_NONE = 0

AFF_YMIR = 1
AFF_INVISIBILITY = 2
AFF_SPAWN = 3

AFF_POISON = 4
AFF_SLOW = 5
AFF_STUN = 6

AFF_DUNGEON_READY = 7
AFF_DUNGEON_UNIQUE = 8

AFF_BUILDING_CONSTRUCTION_SMALL = 9
AFF_BUILDING_CONSTRUCTION_LARGE = 10
AFF_BUILDING_UPGRADE = 11

AFF_MOV_SPEED_POTION = 12
AFF_ATT_SPEED_POTION = 13

AFF_FISH_MIND = 14

AFF_JEONGWIHON = 15
AFF_GEOMGYEONG = 16
AFF_CHEONGEUN = 17
AFF_GYEONGGONG = 18
AFF_EUNHYUNG = 19
AFF_GWIGUM = 20
AFF_TERROR = 21
AFF_JUMAGAP = 22
AFF_HOSIN = 23
AFF_BOHO = 24
AFF_KWAESOK = 25
AFF_MANASHIELD = 26
AFF_MUYEONG = 27
AFF_REVIVE_INVISIBLE = 28
AFF_FIRE = 29
AFF_GICHEON = 30
AFF_JEUNGRYEOK = 31
AFF_TANHWAN_DASH = 32
AFF_PABEOP = 33
AFF_CHEONGEUN_WITH_FALL = 34
AFF_POLYMORPH = 35
AFF_WAR_FLAG1 = 36
AFF_WAR_FLAG2 = 37
AFF_WAR_FLAG3 = 38

AFF_CHINA_FIREWORK = 39
AFF_HAIR = 40
AFF_GERMANY =  41

AFF_RAMADAN_RING =  42

AFF_BLEEDING =  43
AFF_RED_POSSESSION =  44
AFF_BLUE_POSSESSION =  45

AFF_BITS_MAX = 46
-- AFF DECLARING END
-- ########################################################################################

-- ########################################################################################
-- C3 NEMERE BEGIN
function SetDamageFromRaceFromTable(antiflagList, vid)
	for i,v in ipairs(antiflagList) do
		d.set_damage_from_race(v, vid)
	end
end
setDFR_from_table = SetDamageFromRaceFromTable

function SetDamageFromAffectFromTable(antiflagList, vid)
	for i,v in ipairs(antiflagList) do
		d.set_damage_from_affect(v, vid)
	end
end
setDFA_from_table = SetDamageFromAffectFromTable

-- 6151
Szel_4thfloor_affectlimit	= {AFF_HOSIN}
Szel_7thfloor_affectlimit	= {AFF_GICHEON}
-- 8058
IceMetin_racelimit			= {WARRIOR_M,WARRIOR_W,NINJA_W,NINJA_M,SURA_M,SURA_W}
-- 20399
IceStonePillar_racelimit	= {WARRIOR_M,WARRIOR_W,SURA_M,SURA_W}
-- C3 NEMERE END
-- ########################################################################################

-- ########################################################################################
-- AUTO CHECK EVENT FLAGS AT STARTUP BEGIN
function check_event_flags()
	local event_table = {
		{"gold_drop_limit_time", 1},
		{"item_drop_limit_time", 1},
		{"box_use_limit_time", 1},
		{"buysell_limit_time", 1},
		{"no_drop_metin_stone", 1},
		{"no_mount_at_guild_war", 1},
		{"no_potions_on_pvp", 1},
	}
	for num1,str1 in ipairs(event_table) do
		if game.get_event_flag(str1[1])~=str1[2] then
			game.set_event_flag(str1[1], str1[2])
		end
	end
end
if ENABLE_AUTOSET_EVENT_FLAGS then
	check_event_flags()
end
-- AUTO CHECK EVENT FLAGS AT STARTUP END
-- ########################################################################################

-- EXTENDED FUNCTIONS BEGIN

function TimeFormat(seconds)
	if seconds==nil then seconds = 0 end
	if seconds >= 3600 then
		return string.format("%dh %dm %ds", seconds/3600, math.floor(math.mod(seconds/60,60)), math.floor(math.mod(seconds,60)))
	elseif seconds >= 60 then
		return string.format("%dm %ds", seconds/60, math.floor(math.mod(seconds,60)))
	else
		return string.format("%ds", seconds)
	end
end

function TimeFormatDMHS(seconds)
	if seconds==nil then seconds = 0 end
	if seconds < 0 then seconds = 0 end
	local remaining_seconds = 0

	local days = math.floor(seconds / 86400) -- Calculate days
	remaining_seconds = math.mod(seconds, 86400)
	-- print("days " .. days .. " remaining_seconds " .. remaining_seconds)

	local hours = math.floor(remaining_seconds / 3600)
	remaining_seconds = math.mod(remaining_seconds, 3600)
	-- print("hours " .. hours .. " remaining_seconds " .. remaining_seconds)

	local minutes = math.floor(remaining_seconds / 60)
	seconds = math.mod(remaining_seconds, 60)
	-- print("minutes " .. minutes .. " seconds " .. seconds)

	if days >= 1 then
		return string.format("%dd %dh %dm %ds", days, hours, minutes, seconds)
	elseif hours >= 1 then
		return string.format("%dh %dm %ds", hours, minutes, seconds)
	elseif minutes >= 1 then
		return string.format("%dm %ds", minutes, seconds)
	else
		return string.format("%ds", seconds)
	end
end
-- print(TimeFormatDMHS(86405))

function TimeFormatN(seconds)
	-- check null
	if seconds==nil then seconds = 0 end
	-- check negative
	local is_negative = false
	if seconds < 0 then
		is_negative = true
		seconds = math.abs(seconds)
	end
	local remaining_seconds = 0

	local days = math.floor(seconds / 86400) -- Calculate days
	remaining_seconds = math.mod(seconds, 86400)
	-- print("days " .. days .. " remaining_seconds " .. remaining_seconds)

	local hours = math.floor(remaining_seconds / 3600)
	remaining_seconds = math.mod(remaining_seconds, 3600)
	-- print("hours " .. hours .. " remaining_seconds " .. remaining_seconds)

	local minutes = math.floor(remaining_seconds / 60)
	seconds = math.mod(remaining_seconds, 60)
	-- print("minutes " .. minutes .. " seconds " .. seconds)

	local formatted_string = ""
	if is_negative then
		formatted_string = formatted_string .. "-"
	end

	if days >= 1 then
		formatted_string = formatted_string .. days .. "d"
	end
	if hours >= 1 then
		-- add padding space (negative hyphen ignored)
		if string.len(formatted_string) >= 2 then
			formatted_string = formatted_string .. " "
		end
		formatted_string = formatted_string .. hours .. "h"
	end
	if minutes >= 1 then
		-- add padding space (negative hyphen ignored)
		if string.len(formatted_string) >= 2 then
			formatted_string = formatted_string .. " "
		end
		formatted_string = formatted_string .. minutes .. "m"
	end
	if seconds >= 1 then
		-- add padding space (negative hyphen ignored)
		if string.len(formatted_string) >= 2 then
			formatted_string = formatted_string .. " "
		end
		formatted_string = formatted_string .. seconds .. "s"
	end

	return formatted_string
end
-- print(TimeFormatN(86405))

-- from https://metin2.dev/topic/13247-colored-quest-scrolls-system-v2/
function send_letter_ex_new(name, icon_type, icon_name) make_quest_button_ex(name, icon_type, icon_name) set_skin(NOWINDOW) q.set_title(name) q.set_icon(icon_name) q.start() end
function resend_letter_ex(name, icon_type, icon_name) make_quest_button_ex(name, icon_type, icon_name) q.set_title(name) q.set_icon(icon_name) q.start() end
function resend_letter(title) makequestbutton(title) q.set_title(title) q.start() end

-- from https://metin2.dev/topic/4295-color-chat-text/?do=findComment&comment=27882
function say_blue(name) say(color256(0, 0, 255) .. name .. color256(0, 0, 255)) end
function say_red(name) say(color256(255, 0, 0) .. name .. color256(255, 0, 0)) end
function say_green(name) say(color256(0, 238, 0) .. name .. color256(0, 238, 0)) end
function say_gold(name) say(color256(255, 215, 0) .. name .. color256(255, 215, 0)) end
function say_black(name) say(color256(0, 0, 0) .. name .. color256(0, 0, 0)) end
function say_white(name) say(color256(255, 255, 255) .. name .. color256(255, 255, 255)) end
function say_yellow(name) say(color256(255, 255, 0) .. name .. color256(255, 255, 0)) end
function say_blue2(name) say(color256(0, 206, 209) .. name .. color256(0, 206, 209)) end

-- Locale tag helpers: LC(id, ...) -> "[LC;id;arg1;arg2;...]"
LC = LC or function(id, ...)
	local s = "[LC;" .. id
	for i = 1, arg.n do
		s = s .. ";" .. arg[i]
	end
	return s .. "]"
end

LF = LF or function(id, ...)
	local s = "[LF;" .. id
	for i = 1, arg.n do
		s = s .. ";" .. arg[i]
	end
	return s .. "]"
end

LOX = LOX or function(id, ...)
	local s = "[LOX;" .. id
	for i = 1, arg.n do
		s = s .. ";" .. arg[i]
	end
	return s .. "]"
end

LS = LS or function(id, ...)
	local s = "[LS;" .. id
	for i = 1, arg.n do
		s = s .. ";" .. arg[i]
	end
	return s .. "]"
end

IN = IN or function(vnum)
	return "[IN;" .. vnum .. "]"
end

MN = MN or function(vnum)
	return "[MN;" .. vnum .. "]"
end

-- EXTENDED FUNCTIONS END
