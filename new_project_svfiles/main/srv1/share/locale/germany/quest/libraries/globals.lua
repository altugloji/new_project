-- https://metin2.dev/topic/29230-syreldars-useful-globals/
MAX_LEVEL = 120;
MAX_ITEM_COUNT = 200;
MAX_CONQUEROR_LEVEL = 30;
MAX_PARTY_MEMBERS_NUM = 8;
MAX_GUILD_MEMBERS_NUM = 16;
QUEST_WINDOW_WIDTH_MUL = 1;

APPLY_INFINITE_TIME = 60*60*24*365*60;

STATE = {
    DISABLED = 0,
    ENABLED = 1,
};

SKIN = {
    NOWINDOW  = 0,
    NORMAL    = 1,
    SCROLL    = 4,
    CINEMATIC = 5
};

SELECT = {
    YES = 1,
    NO  = 2
};
SELECT.ENTER = SELECT.YES;

CONFIRM = {
    NO      = 0,
    YES     = 1,
    TIMEOUT = 2
};
CONFIRM.OK = CONFIRM.YES;

DUNGEON_DATA = {
    EXPIRATION_TIME = 5*60, -- TODO: Change if needed.
    START_INDEX = 10000,
    ENTER_MODES = {
        SOLO       = 1,
        PARTY      = 2,
        GUILD      = 3,
        SOLO_PARTY = 4,
        ALL        = 5
    },
    AFFECT_CLEAR_MODES = {
        NEVER  = 0,
        JOIN   = 1,
        REJOIN = 2,
        ALWAYS = 3
    }
};
DUNGEON_DATA.ENTER_MODES.NEED_PARTY_MODES = {DUNGEON_DATA.ENTER_MODES.PARTY, DUNGEON_DATA.ENTER_MODES.GUILD};
DUNGEON_DATA.ENTER_MODES.NEED_GROUP_MODES = DUNGEON_DATA.ENTER_MODES.NEED_PARTY_MODES;

SKILL_GROUP = {
    NONE        = 0,
    FIRST_SPEC  = 1,
    SECOND_SPEC = 2
};

SKILL_LEVEL = {
    UNLEARNED      = 0,
    BASE           = 1,
    MASTER         = 20,
    GRAND_MASTER   = 30,
    PERFECT_MASTER = 40
};

SEX = {
    MALE   = 0,
    FEMALE = 1
};

EMPIRES = {
    SHINSOO = 1,
    CHUNJO  = 2,
    JINNO   = 3
};

SPECS = {
    BODY_FORCE    = SKILL_GROUP.FIRST_SPEC,
    MENTAL_FIGHT  = SKILL_GROUP.SECOND_SPEC,

    BLADE_FIGHT   = SKILL_GROUP.FIRST_SPEC,
    ARCHERY       = SKILL_GROUP.SECOND_SPEC,

    WEAPONRY      = SKILL_GROUP.FIRST_SPEC,
    BLACK_MAGIC   = SKILL_GROUP.SECOND_SPEC,

    DRAGON_FORCE  = SKILL_GROUP.FIRST_SPEC,
    HEALING_FORCE = SKILL_GROUP.SECOND_SPEC,

    INSTINCT      = SKILL_GROUP.FIRST_SPEC
};

HORSE_LEVEL = {
    NORMAL   = 1,
    ARMED    = 11,
    MILITARY = 21
};

HORSE_GRADE = {
    NORMAL   = 1,
    ARMED    = 2,
    MILITARY = 3
};

STATUS = {
    CON = 0,
    INT = 1,
    STR = 2,
    DEX = 3
};
STATUS.VIT = STATUS.CON;

-- pc.get_job()'s output.
JOB = {
    WARRIOR = 0,
    NINJA   = 1,
    SURA    = 2,
    SHAMAN  = 3,
    WOLFMAN = 4
};
JOB.ASSASSIN = JOB.NINJA;
JOB.LYCAN  = JOB.WOLFMAN;

-- pc.get_race()'s output.
RACE = {
    WARRIOR_M = 0,
    NINJA_W   = 1,
    SURA_M    = 2,
    SHAMAN_W  = 3,
    WARRIOR_W = 4,
    NINJA_M   = 5,
    SURA_W    = 6,
    SHAMAN_M  = 7,
    WOLFMAN_M = 8
};
RACE.ASSASSIN_W = RACE.NINJA_W;
RACE.ASSASSIN_M = RACE.NINJA_M;
RACE.LYCAN_M  = RACE.WOLFMAN_M;

PART = {
    MAIN        = 0,
    WEAPON      = 1,
    HEAD        = 2,
    WEAPON_LEFT = 3,
    HAIR        = 4,
    ACCE        = 5,
    AURA        = 6
};

ITEM_TYPES = {
    NONE   = 0,
    WEAPON = 1,
    ARMOR  = 2,
    USE = 3,
    AUTOUSE = 4,
    MATERIAL = 5,
    SPECIAL = 6,
    TOOL = 7,
    LOTTERY = 8,
    ELK = 9,
    METIN = 10,
    CONTAINER = 11,
    FISH = 12,
    ROD = 13,
    RESOURCE = 14,
    CAMPFIRE = 15,
    UNIQUE = 16,
    SKILLBOOK = 17,
    QUEST = 18,
    POLYMORPH = 19,
    TREASURE_BOX = 20,
    TREASURE_KEY = 21,
    SKILLFORGET = 22,
    GIFTBOX = 23,
    PICK = 24,
    HAIR = 25,
    TOTEM = 26,
    BLEND = 27,
    COSTUME = 28,
    DS = 29,
    SPECIAL_DS = 30,
    EXTRACT = 31,
    SECONDARY_COIN = 32,
    RING = 33,
    BELT = 34
};
ITEM_TYPES.ARMOUR = ITEM_TYPES.ARMOR;

ITEM_SUB_TYPES = {
    [ITEM_TYPES.WEAPON] = {
        SWORD       = 0,
        DAGGER      = 1,
        BOW         = 2,
        TWO_HANDED  = 3,
        BELL        = 4,
        FAN         = 5,
        ARROW       = 6,
        MOUNT_SPEAR = 7,
        CLAW        = 8,
        QUIVER      = 9
    },
    [ITEM_TYPES.ARMOR] = {
        BODY    = 0,
        HEAD    = 1,
        SHIELD  = 2,
        WRIST   = 3,
        FOOTS   = 4,
        NECK    = 5,
        EAR     = 6,
        PENDANT = 7,
        GLOVE   = 8
    }
};
ITEM_SUB_TYPES[ITEM_TYPES.ARMOUR] = ITEM_SUB_TYPES[ITEM_TYPES.ARMOR];

WEAR = {
    BODY = 0,
    HEAD = 1,
    FOOTS = 2,
    WRIST = 3,
    WEAPON= 4,
    NECK = 5,
    EAR = 6,
    UNIQUE1 = 7,
    UNIQUE2 = 8,
    ARROW = 9,
    SHIELD = 10,
    ABILITY1 = 11,
    ABILITY2 = 12,
    ABILITY3 = 13,
    ABILITY4 = 14,
    ABILITY5 = 15,
    ABILITY6 = 16,
    ABILITY7 = 17,
    ABILITY8 = 18,
    COSTUME_BODY = 19,
    COSTUME_HAIR = 20,
    COSTUME_MOUNT = 21,
    COSTUME_ACCE = 22,
    COSTUME_WEAPON = 23,
    RING1 = 24,
    RING2 = 25,
    BELT = 26,
    PENDANT = 27,
    PET = 28,

    MAX_NUM = 32
};

DAMAGE_TYPE = {
    NONE = 0,
    NORMAL = 1,
    NORMAL_RANGE = 2,
    MELEE = 3,
    RANGE = 4,
    FIRE = 5,
    ICE = 6,
    ELEC = 7,
    MAGIC = 8,
    POISON = 9,
    SPECIAL = 10,
    BLEEDING = 11,
};
DAMAGE_TYPE.TRUE = DAMAGE_TYPE.SPECIAL;

AFFECT = {
    --[[AFFECT]] NONE = 0,

    --[[AFFECT]] MOV_SPEED = 200,
    --[[AFFECT]] ATT_SPEED = 201,
    --[[AFFECT]] ATT_GRADE = 202,
    --[[AFFECT]] INVISIBILITY = 203,
    --[[AFFECT]] STR = 204,
    --[[AFFECT]] DEX = 205,
    --[[AFFECT]] CON = 206,
    --[[AFFECT]] INT = 207,
    --[[AFFECT]] FISH_MIND_PILL = 208,

    --[[AFFECT]] POISON = 209,
    --[[AFFECT]] STUN = 210,
    --[[AFFECT]] SLOW = 211,
    --[[AFFECT]] DUNGEON_READY = 212,
    --[[AFFECT]] DUNGEON_UNIQUE = 213, -- unused

    --[[AFFECT]] BUILDING = 214,
    --[[AFFECT]] REVIVE_INVISIBLE = 215,
    --[[AFFECT]] FIRE = 216,
    --[[AFFECT]] CAST_SPEED = 217,
    --[[AFFECT]] HP_RECOVER_CONTINUE = 218,
    --[[AFFECT]] SP_RECOVER_CONTINUE = 219,

    --[[AFFECT]] POLYMORPH = 220,
    --[[AFFECT]] MOUNT = 221,

    --[[AFFECT]] WAR_FLAG = 222,

    --[[AFFECT]] BLOCK_CHAT = 223,
    --[[AFFECT]] CHINA_FIREWORK = 224,

    --[[AFFECT]] BOW_DISTANCE = 225,
    --[[AFFECT]] DEF_GRADE = 226,
    --[[AFFECT]] BLEEDING = 227,

    --[[AFFECT]] PREMIUM_START = 500,
    --[[AFFECT]] EXP_BONUS = 500,
    --[[AFFECT]] ITEM_BONUS = 501,
    --[[AFFECT]] SAFEBOX = 502,
    --[[AFFECT]] AUTOLOOT = 503,
    --[[AFFECT]] FISH_MIND = 504,
    --[[AFFECT]] MARRIAGE_FAST = 505,
    --[[AFFECT]] GOLD_BONUS = 506,
    --[[AFFECT]] PREMIUM_END = 509,

    --[[AFFECT]] MALL = 510,
    --[[AFFECT]] NO_DEATH_PENALTY = 511,
    --[[AFFECT]] SKILL_BOOK_BONUS = 512,
    --[[AFFECT]] SKILL_NO_BOOK_DELAY = 513,

    --[[AFFECT]] HAIR = 514,
    --[[AFFECT]] COLLECT = 515,
    --[[AFFECT]] EXP_BONUS_EURO_FREE = 516,
    --[[AFFECT]] EXP_BONUS_EURO_FREE_UNDER_15 = 517,
    --[[AFFECT]] UNIQUE_ABILITY = 518,

    --[[AFFECT]] CUBE_1 = 519,
    --[[AFFECT]] CUBE_2 = 520,
    --[[AFFECT]] CUBE_3 = 521,
    --[[AFFECT]] CUBE_4 = 522,
    --[[AFFECT]] CUBE_5 = 523,
    --[[AFFECT]] CUBE_6 = 524,
    --[[AFFECT]] CUBE_7 = 525,
    --[[AFFECT]] CUBE_8 = 526,
    --[[AFFECT]] CUBE_9 = 527,
    --[[AFFECT]] CUBE_10 = 528,
    --[[AFFECT]] CUBE_11 = 529,
    --[[AFFECT]] CUBE_12 = 530,

    --[[AFFECT]] BLEND = 531,

    --[[AFFECT]] HORSE_NAME = 532,
    --[[AFFECT]] MOUNT_BONUS = 533,

    --[[AFFECT]] AUTO_HP_RECOVERY = 534,
    --[[AFFECT]] AUTO_SP_RECOVERY = 535,

    --[[AFFECT]] DRAGON_SOUL_QUALIFIED = 540,
    --[[AFFECT]] DRAGON_SOUL_DECK_0 = 541,
    --[[AFFECT]] DRAGON_SOUL_DECK_1 = 542,

    --[[AFFECT]] RAMADAN_ABILITY = 300,
    --[[AFFECT]] RAMADAN_RING = 301,

    --[[AFFECT]] NOG_ABILITY = 302,
    --[[AFFECT]] HOLLY_STONE_POWER = 303,

    --[[AFFECT]] STATUE = 700,

    --[[AFFECT]] QUEST_START_IDX = 1000,
};
AFFECT.PREMIUM_START = AFFECT.EXP_BONUS;
AFFECT.PREMIUM_END = AFFECT.MALL - 1;

AFFECT_BITS = {
    --[[AFFECT_BITS]] NONE = 0,

    --[[AFFECT_BITS]] YMIR = 1,
    --[[AFFECT_BITS]] INVISIBILITY = 2,
    --[[AFFECT_BITS]] SPAWN = 3,

    --[[AFFECT_BITS]] POISON = 4,
    --[[AFFECT_BITS]] SLOW = 5,
    --[[AFFECT_BITS]] STUN = 6,

    --[[AFFECT_BITS]] DUNGEON_READY = 7,
    --[[AFFECT_BITS]] DUNGEON_UNIQUE = 8,

    --[[AFFECT_BITS]] BUILDING_CONSTRUCTION_SMALL = 9,
    --[[AFFECT_BITS]] BUILDING_CONSTRUCTION_LARGE = 10,
    --[[AFFECT_BITS]] BUILDING_UPGRADE = 11,

    --[[AFFECT_BITS]] MOV_SPEED_POTION = 12,
    --[[AFFECT_BITS]] ATT_SPEED_POTION = 13,

    --[[AFFECT_BITS]] FISH_MIND = 14,

    --[[AFFECT_BITS]] JEONGWIHON = 15,
    --[[AFFECT_BITS]] GEOMGYEONG = 16,
    --[[AFFECT_BITS]] CHEONGEUN = 17,
    --[[AFFECT_BITS]] GYEONGGONG = 18,
    --[[AFFECT_BITS]] EUNHYUNG = 19,
    --[[AFFECT_BITS]] GWIGUM = 20,
    --[[AFFECT_BITS]] TERROR = 21,
    --[[AFFECT_BITS]] JUMAGAP = 22,
    --[[AFFECT_BITS]] HOSIN = 23,
    --[[AFFECT_BITS]] BOHO = 24,
    --[[AFFECT_BITS]] KWAESOK = 25,
    --[[AFFECT_BITS]] MANASHIELD = 26,
    --[[AFFECT_BITS]] MUYEONG = 27,
    --[[AFFECT_BITS]] REVIVE_INVISIBLE = 28,
    --[[AFFECT_BITS]] FIRE = 29,
    --[[AFFECT_BITS]] GICHEON = 30,
    --[[AFFECT_BITS]] JEUNGRYEOK = 31,
    --[[AFFECT_BITS]] TANHWAN_DASH = 32,
    --[[AFFECT_BITS]] PABEOP = 33,
    --[[AFFECT_BITS]] CHEONGEUN_WITH_FALL = 34,
    --[[AFFECT_BITS]] POLYMORPH = 35,
    --[[AFFECT_BITS]] WAR_FLAG1 = 36,
    --[[AFFECT_BITS]] WAR_FLAG2 = 37,
    --[[AFFECT_BITS]] WAR_FLAG3 = 38,

    --[[AFFECT_BITS]] CHINA_FIREWORK = 39,
    --[[AFFECT_BITS]] HAIR = 40,
    --[[AFFECT_BITS]] GERMANY = 41,
    --[[AFFECT_BITS]] RAMADAN_RING = 42,

    --[[AFFECT_BITS]] BLEEDING = 43,
    --[[AFFECT_BITS]] RED_POSSESSION = 44,
    --[[AFFECT_BITS]] BLUE_POSSESSION = 45,

    --[[AFFECT_BITS]] DRAGONLAIR_STONE_UNBEATABLE_1 = 49,
    --[[AFFECT_BITS]] DRAGONLAIR_STONE_UNBEATABLE_2 = 51,
    --[[AFFECT_BITS]] DRAGONLAIR_STONE_UNBEATABLE_3 = 52,

    --[[AFFECT_BITS]] MAX_NUM = 64
};
AFFECT_BITS.FALLEN_CHEONGEUN = AFFECT_BITS.CHEONGEUN_WITH_FALL;
AFFECT_BITS.DASH = AFFECT_BITS.TANHWAN_DASH;
AFFECT_BITS.REVIVE_INVISIBILITY = AFFECT_BITS.REVIVE_INVISIBLE;
AFFECT_BITS.HEUKSIN = AFFECT_BITS.MANASHIELD;
AFFECT_BITS.GONGPO = AFFECT_BITS.TERROR;
AFFECT_BITS.GWIGEOM = AFFECT_BITS.GWIGUM;
AFFECT_BITS.JEONGWI = AFFECT_BITS.JEONGWIHON;
AFFECT_BITS.EUNHYEONG = AFFECT_BITS.EUNHYUNG;
AFFECT_BITS.HWAYEOM = AFFECT_BITS.GEOMGYEONG;
AFFECT_BITS.NUM = AFFECT_BITS.MAX_NUM;

APPLY = {
    --[[APPLY]] MAX_HP = 1,
    --[[APPLY]] MAX_SP = 2,
    --[[APPLY]] CON = 3,
    --[[APPLY]] INT = 4,
    --[[APPLY]] STR = 5,
    --[[APPLY]] DEX = 6,
    --[[APPLY]] ATT_SPEED = 7,
    --[[APPLY]] MOV_SPEED = 8,
    --[[APPLY]] CAST_SPEED = 9,
    --[[APPLY]] HP_REGEN = 10,
    --[[APPLY]] SP_REGEN = 11,
    --[[APPLY]] POISON_PCT = 12,
    --[[APPLY]] STUN_PCT = 13,
    --[[APPLY]] SLOW_PCT = 14,
    --[[APPLY]] CRITICAL_PCT = 15,
    --[[APPLY]] PENETRATE_PCT = 16,
    --[[APPLY]] ATTBONUS_HUMAN = 17,
    --[[APPLY]] ATTBONUS_ANIMAL = 18,
    --[[APPLY]] ATTBONUS_ORC = 19,
    --[[APPLY]] ATTBONUS_MILGYO = 20,
    --[[APPLY]] ATTBONUS_UNDEAD = 21,
    --[[APPLY]] ATTBONUS_DEVIL = 22,
    --[[APPLY]] STEAL_HP = 23,
    --[[APPLY]] STEAL_SP = 24,
    --[[APPLY]] MANA_BURN_PCT = 25,
    --[[APPLY]] DAMAGE_SP_RECOVER = 26,
    --[[APPLY]] BLOCK = 27,
    --[[APPLY]] DODGE = 28,
    --[[APPLY]] RESIST_SWORD = 29,
    --[[APPLY]] RESIST_TWOHAND = 30,
    --[[APPLY]] RESIST_DAGGER = 31,
    --[[APPLY]] RESIST_BELL = 32,
    --[[APPLY]] RESIST_FAN = 33,
    --[[APPLY]] RESIST_BOW = 34,
    --[[APPLY]] RESIST_FIRE = 35,
    --[[APPLY]] RESIST_ELEC = 36,
    --[[APPLY]] RESIST_MAGIC = 37,
    --[[APPLY]] RESIST_WIND = 38,
    --[[APPLY]] REFLECT_MELEE = 39,
    --[[APPLY]] REFLECT_CURSE = 40,
    --[[APPLY]] POISON_REDUCE = 41,
    --[[APPLY]] KILL_SP_RECOVER = 42,
    --[[APPLY]] EXP_DOUBLE_BONUS = 43,
    --[[APPLY]] GOLD_DOUBLE_BONUS = 44,
    --[[APPLY]] ITEM_DROP_BONUS = 45,
    --[[APPLY]] POTION_BONUS = 46,
    --[[APPLY]] KILL_HP_RECOVER = 47,
    --[[APPLY]] IMMUNE_STUN = 48,
    --[[APPLY]] IMMUNE_SLOW = 49,
    --[[APPLY]] IMMUNE_FALL = 50,
    --[[APPLY]] SKILL = 51,
    --[[APPLY]] BOW_DISTANCE = 52,
    --[[APPLY]] ATT_GRADE_BONUS = 53,
    --[[APPLY]] DEF_GRADE_BONUS = 54,
    --[[APPLY]] MAGIC_ATT_GRADE = 55,
    --[[APPLY]] MAGIC_DEF_GRADE = 56,
    --[[APPLY]] CURSE_PCT = 57,
    --[[APPLY]] MAX_STAMINA = 58,
    --[[APPLY]] ATTBONUS_WARRIOR = 59,
    --[[APPLY]] ATTBONUS_ASSASSIN = 60,
    --[[APPLY]] ATTBONUS_SURA = 61,
    --[[APPLY]] ATTBONUS_SHAMAN = 62,
    --[[APPLY]] ATTBONUS_MONSTER = 63,
    --[[APPLY]] MALL_ATTBONUS = 64,
    --[[APPLY]] MALL_DEFBONUS = 65,
    --[[APPLY]] MALL_EXPBONUS = 66,
    --[[APPLY]] MALL_ITEMBONUS = 67,
    --[[APPLY]] MALL_GOLDBONUS = 68,
    --[[APPLY]] MAX_HP_PCT = 69,
    --[[APPLY]] MAX_SP_PCT = 70,
    --[[APPLY]] SKILL_DAMAGE_BONUS = 71,
    --[[APPLY]] NORMAL_HIT_DAMAGE_BONUS = 72,
    --[[APPLY]] SKILL_DEFEND_BONUS = 73,
    --[[APPLY]] NORMAL_HIT_DEFEND_BONUS = 74,
    --[[APPLY]] PC_BANG_EXP_BONUS = 75,
    --[[APPLY]] PC_BANG_DROP_BONUS = 76,
    --[[APPLY]] EXTRACT_HP_PCT = 77,
    --[[APPLY]] RESIST_WARRIOR = 78,
    --[[APPLY]] RESIST_ASSASSIN = 79,
    --[[APPLY]] RESIST_SURA = 80,
    --[[APPLY]] RESIST_SHAMAN = 81,
    --[[APPLY]] ENERGY = 82,
    --[[APPLY]] DEF_GRADE = 83,
    --[[APPLY]] COSTUME_ATTR_BONUS = 84,
    --[[APPLY]] MAGIC_ATTBONUS_PER = 85,
    --[[APPLY]] MELEE_MAGIC_ATTBONUS_PER = 86,
    --[[APPLY]] RESIST_ICE = 87,
    --[[APPLY]] RESIST_EARTH = 88,
    --[[APPLY]] RESIST_DARK = 89,
    --[[APPLY]] ANTI_CRITICAL_PCT = 90,
    --[[APPLY]] ANTI_PENETRATE_PCT = 91,
    --[[APPLY]] BLEEDING_REDUCE = 92,
    --[[APPLY]] BLEEDING_PCT = 93,
    --[[APPLY]] ATTBONUS_WOLFMAN = 94,
    --[[APPLY]] RESIST_WOLFMAN = 95,
    --[[APPLY]] RESIST_CLAW = 96,
    --[[APPLY]] MOUNT = 97,
    --[[APPLY]] ACCEDRAIN_RATE = 98,
    --[[APPLY]] RESIST_MAGIC_REDUCTION = 99,

    --[[APPLY]] ENCHANT_ELECT = 100,
    --[[APPLY]] ENCHANT_FIRE = 101,
    --[[APPLY]] ENCHANT_ICE = 102,
    --[[APPLY]] ENCHANT_WIND = 103,
    --[[APPLY]] ENCHANT_EARTH = 104,
    --[[APPLY]] ENCHANT_DARK = 105,
    --[[APPLY]] ATTBONUS_CZ = 106,
    --[[APPLY]] ATTBONUS_INSECT = 107,
    --[[APPLY]] ATTBONUS_DESERT = 108,

    --[[APPLY]] ATTBONUS_SWORD = 109,
    --[[APPLY]] ATTBONUS_TWOHAND = 110,
    --[[APPLY]] ATTBONUS_DAGGER = 111,
    --[[APPLY]] ATTBONUS_BELL = 112,
    --[[APPLY]] ATTBONUS_FAN = 113,
    --[[APPLY]] ATTBONUS_BOW = 114,
    --[[APPLY]] ATTBONUS_CLAW = 115,

    --[[APPLY]] RESIST_HUMAN = 116,
    --[[APPLY]] ATTBONUS_STONE = 117,
    --[[APPLY]] SUNGMA_STR = 118,
    --[[APPLY]] SUNGMA_HP = 119,
    --[[APPLY]] SUNGMA_MOVE = 120,
    --[[APPLY]] SUNGMA_IMMUNE = 121,

    --[[APPLY]] RANDOM = 122,

    --[[APPLY]] SKILL_DEFEND_BONUS_BOSS_OR_MORE = 123,
    --[[APPLY]] SKILL_DAMAGE_BONUS_BOSS_OR_MORE = 124,
    --[[APPLY]] ATTBONUS_BOSS = 125,
    --[[APPLY]] NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE = 126,
    --[[APPLY]] FIRST_ATTRIBUTE_BONUS = 127,
    --[[APPLY]] SECOND_ATTRIBUTE_BONUS = 128,
    --[[APPLY]] THIRD_ATTRIBUTE_BONUS = 129,
    --[[APPLY]] FOURTH_ATTRIBUTE_BONUS = 130,
    --[[APPLY]] FIFTH_ATTRIBUTE_BONUS = 131,

    --[[APPLY]] FISHING_RARE = 132,

    --[[APPLY]] MAX_NUM = 255
};
APPLY.MAX_MP = APPLY.MAX_SP;
APPLY.VIT = APPLY.CON;
APPLY.MP_REGEN = APPLY.SP_REGEN;
APPLY.STEAL_MP = APPLY.STEAL_SP;
APPLY.DAMAGE_MP_RECOVER = APPLY.DAMAGE_SP_RECOVER;
APPLY.RESIST_ARROW = APPLY.RESIST_BOW;
APPLY.MAX_MP_PCT = APPLY.MAX_SP_PCT;
APPLY.NUM = APPLY.MAX_NUM;

POINT = {
    --[[POINT]] NONE = 0,
    --[[POINT]] LEVEL = 1,
    --[[POINT]] VOICE = 2,
    --[[POINT]] EXP = 3,
    --[[POINT]] NEXT_EXP = 4,
    --[[POINT]] HP = 5,
    --[[POINT]] MAX_HP = 6,
    --[[POINT]] SP = 7,
    --[[POINT]] MAX_SP = 8,
    --[[POINT]] STAMINA = 9,
    --[[POINT]] MAX_STAMINA = 10,

    --[[POINT]] GOLD = 11,
    --[[POINT]] ST = 12,
    --[[POINT]] HT = 13,
    --[[POINT]] DX = 14,
    --[[POINT]] IQ = 15,
    --[[POINT]] DEF_GRADE = 16,
    --[[POINT]] ATT_SPEED = 17,
    --[[POINT]] ATT_GRADE = 18,
    --[[POINT]] MOV_SPEED = 19,
    --[[POINT]] CLIENT_DEF_GRADE = 20,
    --[[POINT]] CASTING_SPEED = 21,
    --[[POINT]] MAGIC_ATT_GRADE = 22,
    --[[POINT]] MAGIC_DEF_GRADE = 23,
    --[[POINT]] EMPIRE_POINT = 24,
    --[[POINT]] LEVEL_STEP = 25,
    --[[POINT]] STAT = 26,
    --[[POINT]] SUB_SKILL = 27,
    --[[POINT]] SKILL = 28,
    --[[POINT]] WEAPON_MIN = 29,
    --[[POINT]] WEAPON_MAX = 30,
    --[[POINT]] PLAYTIME = 31,
    --[[POINT]] HP_REGEN = 32,
    --[[POINT]] SP_REGEN = 33,

    --[[POINT]] BOW_DISTANCE = 34,

    --[[POINT]] HP_RECOVERY = 35,
    --[[POINT]] SP_RECOVERY = 36,

    --[[POINT]] POISON_PCT = 37,
    --[[POINT]] STUN_PCT = 38,
    --[[POINT]] SLOW_PCT = 39,
    --[[POINT]] CRITICAL_PCT = 40,
    --[[POINT]] PENETRATE_PCT = 41,
    --[[POINT]] CURSE_PCT = 42,

    --[[POINT]] ATTBONUS_HUMAN = 43,
    --[[POINT]] ATTBONUS_ANIMAL = 44,
    --[[POINT]] ATTBONUS_ORC = 45,
    --[[POINT]] ATTBONUS_MILGYO = 46,
    --[[POINT]] ATTBONUS_UNDEAD = 47,
    --[[POINT]] ATTBONUS_DEVIL = 48,
    --[[POINT]] ATTBONUS_INSECT = 49,
    --[[POINT]] ATTBONUS_FIRE = 50,
    --[[POINT]] ATTBONUS_ICE = 51,
    --[[POINT]] ATTBONUS_DESERT = 52,
    --[[POINT]] ATTBONUS_MONSTER = 53,
    --[[POINT]] ATTBONUS_WARRIOR = 54,
    --[[POINT]] ATTBONUS_ASSASSIN = 55,
    --[[POINT]] ATTBONUS_SURA = 56,
    --[[POINT]] ATTBONUS_SHAMAN = 57,
    --[[POINT]] ATTBONUS_TREE = 58,

    --[[POINT]] RESIST_WARRIOR = 59,
    --[[POINT]] RESIST_ASSASSIN = 60,
    --[[POINT]] RESIST_SURA = 61,
    --[[POINT]] RESIST_SHAMAN = 62,

    --[[POINT]] STEAL_HP = 63,
    --[[POINT]] STEAL_SP = 64,

    --[[POINT]] MANA_BURN_PCT = 65,

    --[[POINT]] DAMAGE_SP_RECOVER = 66,

    --[[POINT]] BLOCK = 67,
    --[[POINT]] DODGE = 68,

    --[[POINT]] RESIST_SWORD = 69,
    --[[POINT]] RESIST_TWOHAND = 70,
    --[[POINT]] RESIST_DAGGER = 71,
    --[[POINT]] RESIST_BELL = 72,
    --[[POINT]] RESIST_FAN = 73,
    --[[POINT]] RESIST_BOW = 74,
    --[[POINT]] RESIST_FIRE = 75,
    --[[POINT]] RESIST_ELEC = 76,
    --[[POINT]] RESIST_MAGIC = 77,
    --[[POINT]] RESIST_WIND = 78,

    --[[POINT]] REFLECT_MELEE = 79,

    --[[POINT]] REFLECT_CURSE = 80,
    --[[POINT]] POISON_REDUCE = 81,

    --[[POINT]] KILL_SP_RECOVER = 82,
    --[[POINT]] EXP_DOUBLE_BONUS = 83,
    --[[POINT]] GOLD_DOUBLE_BONUS = 84,
    --[[POINT]] ITEM_DROP_BONUS = 85,

    --[[POINT]] POTION_BONUS = 86,
    --[[POINT]] KILL_HP_RECOVERY = 87,

    --[[POINT]] IMMUNE_STUN = 88,
    --[[POINT]] IMMUNE_SLOW = 89,
    --[[POINT]] MMUNE_FALL = 90,

    --[[POINT]] PARTY_ATTACKER_BONUS = 91,
    --[[POINT]] PARTY_TANKER_BONUS = 92,

    --[[POINT]] ATT_BONUS = 93,
    --[[POINT]] DEF_BONUS = 94,

    --[[POINT]] ATT_GRADE_BONUS = 95,
    --[[POINT]] DEF_GRADE_BONUS = 96,
    --[[POINT]] MAGIC_ATT_GRADE_BONUS = 97,
    --[[POINT]] MAGIC_DEF_GRADE_BONUS = 98,

    --[[POINT]] RESIST_NORMAL_DAMAGE = 99,

    --[[POINT]] HIT_HP_RECOVERY = 100,
    --[[POINT]] HIT_SP_RECOVERY = 101,
    --[[POINT]] MANASHIELD = 102,

    --[[POINT]] PARTY_BUFFER_BONUS = 103,
    --[[POINT]] PARTY_SKILL_MASTER_BONUS = 104,

    --[[POINT]] HP_RECOVER_CONTINUE = 105,
    --[[POINT]] SP_RECOVER_CONTINUE = 106,

    --[[POINT]] STEAL_GOLD = 107,
    --[[POINT]] POLYMORPH = 108,
    --[[POINT]] MOUNT = 109,

    --[[POINT]] PARTY_HASTE_BONUS = 110,
    --[[POINT]] PARTY_DEFENDER_BONUS = 111,
    --[[POINT]] STAT_RESET_COUNT = 112,

    --[[POINT]] HORSE_SKILL = 113,

    --[[POINT]] MALL_ATTBONUS = 114,
    --[[POINT]] MALL_DEFBONUS = 115,
    --[[POINT]] MALL_EXPBONUS = 116,
    --[[POINT]] MALL_ITEMBONUS = 117,
    --[[POINT]] MALL_GOLDBONUS = 118,

    --[[POINT]] MAX_HP_PCT = 119,
    --[[POINT]] MAX_SP_PCT = 120,

    --[[POINT]] SKILL_DAMAGE_BONUS = 121,
    --[[POINT]] NORMAL_HIT_DAMAGE_BONUS = 122,

    --[[POINT]] SKILL_DEFEND_BONUS = 123,
    --[[POINT]] NORMAL_HIT_DEFEND_BONUS = 124,

    --[[POINT]] PC_BANG_EXP_BONUS = 125,
    --[[POINT]] PC_BANG_DROP_BONUS = 126,
    --[[POINT]] RAMADAN_CANDY_BONUS_EXP = 127,

    --[[POINT]] ENERGY = 128,
    --[[POINT]] ENERGY_END_TIME = 129,

    --[[POINT]] COSTUME_ATTR_BONUS = 130,
    --[[POINT]] MAGIC_ATT_BONUS_PER = 131,
    --[[POINT]] MELEE_MAGIC_ATT_BONUS_PER = 132,

    --[[POINT]] RESIST_ICE = 133,
    --[[POINT]] RESIST_EARTH = 134,
    --[[POINT]] RESIST_DARK = 135,

    --[[POINT]] RESIST_CRITICAL = 136,
    --[[POINT]] RESIST_PENETRATE = 137,

    --[[POINT]] BLEEDING_REDUCE = 138,
    --[[POINT]] BLEEDING_PCT = 139,
    --[[POINT]] ATTBONUS_WOLFMAN = 140,
    --[[POINT]] RESIST_WOLFMAN = 141,
    --[[POINT]] RESIST_CLAW = 142,

    --[[POINT]] ACCEDRAIN_RATE = 143,

    --[[POINT]] RESIST_MAGIC_REDUCTION = 144,

    --[[POINT]] ENCHANT_ELECT = 145,
    --[[POINT]] ENCHANT_FIRE = 146,
    --[[POINT]] ENCHANT_ICE = 147,
    --[[POINT]] ENCHANT_WIND = 148,
    --[[POINT]] ENCHANT_EARTH = 149,
    --[[POINT]] ENCHANT_DARK = 150,
    --[[POINT]] ATTBONUS_CZ = 151,
    --[[POINT]] ATTBONUS_SWORD = 152,
    --[[POINT]] ATTBONUS_TWOHAND = 153,
    --[[POINT]] ATTBONUS_DAGGER = 154,
    --[[POINT]] ATTBONUS_BELL = 155,
    --[[POINT]] ATTBONUS_FAN = 156,
    --[[POINT]] ATTBONUS_BOW = 157,
    --[[POINT]] ATTBONUS_CLAW = 158,
    --[[POINT]] RESIST_HUMAN = 159,

    --[[POINT]] MAX_NUM = 255
};
POINT.MAX_MP = POINT.MAX_SP;
POINT.VIT = POINT.CON;
POINT.MP_REGEN = POINT.SP_REGEN;
POINT.STEAL_MP = POINT.STEAL_SP;
POINT.DAMAGE_MP_RECOVER = POINT.DAMAGE_SP_RECOVER;
POINT.RESIST_ARROW = POINT.RESIST_BOW;
POINT.MAX_MP_PCT = POINT.MAX_SP_PCT;
POINT.NUM = POINT.MAX_NUM;

APPLY_NAME = {
    [APPLY.MAX_HP] = "Max HP",
    [APPLY.MAX_SP] = "Max MP",
    [APPLY.CON] = "Vitality",
    [APPLY.INT] = "Intelligence",
    [APPLY.STR] = "Strength",
    [APPLY.DEX] = "Dexterity",
    [APPLY.ATT_SPEED] = "Attack Speed",
    [APPLY.MOV_SPEED] = "Movement Speed",
    [APPLY.CAST_SPEED] = "Casting Speed",
    [APPLY.HP_REGEN] = "HP Regeneration",
    [APPLY.SP_REGEN] = "MP Regeneration",
    [APPLY.POISON_PCT] = "Poisoning chance",
    [APPLY.STUN_PCT] = "Blackout chance",
    [APPLY.SLOW_PCT] = "Slowing chance",
    [APPLY.CRITICAL_PCT] = "Chance of critical hit",
    [APPLY.PENETRATE_PCT] = "Chance of piercing hit",
    [APPLY.ATTBONUS_HUMAN] = "Strong against Half Humans",
    [APPLY.ATTBONUS_ANIMAL] = "Strong against Animals",
    [APPLY.ATTBONUS_ORC] = "Strong against Orcs",
    [APPLY.ATTBONUS_MILGYO] = "Strong against Mystics",
    [APPLY.ATTBONUS_UNDEAD] = "Strong against Undead",
    [APPLY.ATTBONUS_DEVIL] = "Strong against Devils",
    [APPLY.STEAL_HP] = "damage will be absorbed by HP",
    [APPLY.STEAL_SP] = "damage will be absorbed by MP",
    [APPLY.MANA_BURN_PCT] = "chance to rob SP",
    [APPLY.DAMAGE_SP_RECOVER] = "Chance to get back SP when hit",
    [APPLY.BLOCK] = "Chance to block a close-combat attack",
    [APPLY.DODGE] = "Chance to avoid Arrows",
    [APPLY.RESIST_SWORD] = "Sword Defence",
    [APPLY.RESIST_TWOHAND] = "Two-Handed Defence",
    [APPLY.RESIST_DAGGER] = "Dagger Defence",
    [APPLY.RESIST_BELL] = "Bell Defence",
    [APPLY.RESIST_FAN] = "Fan Defence",
    [APPLY.RESIST_BOW] = "Arrow Defence",
    [APPLY.RESIST_FIRE] = "Fire Resistance",
    [APPLY.RESIST_ELEC] = "Lightning Resistance",
    [APPLY.RESIST_MAGIC] = "Magic Resistance",
    [APPLY.RESIST_WIND] = "Wind Resistance",
    [APPLY.REFLECT_MELEE] = "Chance to reflect a close combat attack",
    [APPLY.REFLECT_CURSE] = "Chance to reflect Curse:",
    [APPLY.POISON_REDUCE] = "Poisoning Resistance",
    [APPLY.KILL_SP_RECOVER] = "Chance to restore SP",
    [APPLY.EXP_DOUBLE_BONUS] = "Chance for EXP Bonus",
    [APPLY.GOLD_DOUBLE_BONUS] = "Chance to drop double Yang",
    [APPLY.ITEM_DROP_BONUS] = "Chance to drop double the Items",
    [APPLY.POTION_BONUS] = "Potion effect raise",
    [APPLY.KILL_HP_RECOVER] = "Chance to restore HP",
    [APPLY.IMMUNE_STUN] = "Defence against blackouts",
    [APPLY.IMMUNE_SLOW] = "Defence against slowing",
    [APPLY.IMMUNE_FALL] = "Immune against falling down",
    [APPLY.SKILL] = "CODE:SKILL unk",
    [APPLY.BOW_DISTANCE] = "Range m",
    [APPLY.ATT_GRADE_BONUS] = "Attack Value",
    [APPLY.DEF_GRADE_BONUS] = "Defence",
    [APPLY.MAGIC_ATT_GRADE] = "Magical Attack Value",
    [APPLY.MAGIC_DEF_GRADE] = "Magical Defence",
    [APPLY.CURSE_PCT] = "CODE:CURSE_PCT unk",
    [APPLY.MAX_STAMINA] = "Max. Endurance",
    [APPLY.ATTBONUS_WARRIOR] = "Strong against Warriors",
    [APPLY.ATTBONUS_ASSASSIN] = "Strong against Ninjas",
    [APPLY.ATTBONUS_SURA] = "Strong against Sura",
    [APPLY.ATTBONUS_SHAMAN] = "Strong against Shamans",
    [APPLY.ATTBONUS_MONSTER] = "Strength against monsters",
    [APPLY.MALL_ATTBONUS] = "Attack Value",
    [APPLY.MALL_DEFBONUS] = "Defence",
    [APPLY.MALL_EXPBONUS] = "EXP",
    [APPLY.MALL_ITEMBONUS] = "Item drop chance increased",
    [APPLY.MALL_GOLDBONUS] = "Yang drop chance increased",
    [APPLY.MAX_HP_PCT] = "Max. HP",
    [APPLY.MAX_SP_PCT] = "Max. SP",
    [APPLY.SKILL_DAMAGE_BONUS] = "Skill Damage",
    [APPLY.NORMAL_HIT_DAMAGE_BONUS] = "Average Damage",
    [APPLY.SKILL_DEFEND_BONUS] = "Resistance against Skill Damage",
    [APPLY.NORMAL_HIT_DEFEND_BONUS] = "Average Damage Resistance",
    [APPLY.PC_BANG_EXP_BONUS] = "iCafe EXP Bonus",
    [APPLY.PC_BANG_DROP_BONUS] = "iCafe Chance of looting items",
    [APPLY.EXTRACT_HP_PCT] = "CODE:EXTRACT_HP_PCT unk",
    [APPLY.RESIST_WARRIOR] = "Defence chance against warrior attacks",
    [APPLY.RESIST_ASSASSIN] = "Defence chance against ninja attacks",
    [APPLY.RESIST_SURA] = "Defence chance against sura attacks",
    [APPLY.RESIST_SHAMAN] = "Defence chance against shaman attacks",
    [APPLY.ENERGY] = "Energy",
    [APPLY.DEF_GRADE] = "CODE:DEF_GRADE (unk)",
    [APPLY.COSTUME_ATTR_BONUS] = "Costume bonus",
    [APPLY.MAGIC_ATTBONUS_PER] = "Magic attack",
    [APPLY.MELEE_MAGIC_ATTBONUS_PER] = "Magic/melee attack",
    [APPLY.RESIST_ICE] = "Ice Resistance",
    [APPLY.RESIST_EARTH] = "Earth Resistance",
    [APPLY.RESIST_DARK] = "Resistance against darkness",
    [APPLY.ANTI_CRITICAL_PCT] = "Resistance against critical hits",
    [APPLY.ANTI_PENETRATE_PCT] = "Resistance against piercing hits",
    [APPLY.BLEEDING_REDUCE] = "Bleeding Attack Resistance",
    [APPLY.BLEEDING_PCT] = "Bleeding attack",
    [APPLY.ATTBONUS_WOLFMAN] = "Strong against Lycans",
    [APPLY.RESIST_WOLFMAN] = "Defence chance against lycan attacks",
    [APPLY.RESIST_CLAW] = "Claw Defence",
    [APPLY.MOUNT] = "CODE:MOUNT (unk)",
    [APPLY.ACCEDRAIN_RATE] = "Absorption rate",
    [APPLY.RESIST_MAGIC_REDUCTION] = "Magic penetration",
    [APPLY.ENCHANT_ELECT] = "Power of Lightning",
    [APPLY.ENCHANT_FIRE] = "Power of Fire",
    [APPLY.ENCHANT_ICE] = "Power of Ice",
    [APPLY.ENCHANT_WIND] = "Power of Wind",
    [APPLY.ENCHANT_EARTH] = "Power of Earth",
    [APPLY.ENCHANT_DARK] = "Power of Darkness",
    [APPLY.ATTBONUS_CZ] = "Strong against Zodiac Monsters",
    [APPLY.ATTBONUS_INSECT] = "Strong against Insects",
    [APPLY.ATTBONUS_DESERT] = "Strong against Desert Monsters",
    [APPLY.ATTBONUS_SWORD] = "Sword Defence Break",
    [APPLY.ATTBONUS_TWOHAND] = "Two-handed Defence Break",
    [APPLY.ATTBONUS_DAGGER] = "Dagger Defence Break",
    [APPLY.ATTBONUS_BELL] = "Bell Defence Break",
    [APPLY.ATTBONUS_FAN] = "Fan Defence Break",
    [APPLY.ATTBONUS_BOW] = "Arrow Defence Break",
    [APPLY.ATTBONUS_CLAW] = "Claw Defence Break",
    [APPLY.RESIST_HUMAN] = "Resistance to Half Humans"
};
APPLY_NAME[APPLY.MAX_MP] = APPLY_NAME[APPLY.MAX_SP];
APPLY_NAME[APPLY.VIT] = APPLY_NAME[APPLY.CON];
APPLY_NAME[APPLY.MP_REGEN] = APPLY_NAME[APPLY.SP_REGEN];
APPLY_NAME[APPLY.STEAL_MP] = APPLY_NAME[APPLY.STEAL_SP];
APPLY_NAME[APPLY.DAMAGE_MP_RECOVER] = APPLY_NAME[APPLY.DAMAGE_SP_RECOVER];
APPLY_NAME[APPLY.RESIST_ARROW] = APPLY_NAME[APPLY.RESIST_BOW];
APPLY_NAME[APPLY.MAX_MP_PCT] = APPLY_NAME[APPLY.MAX_SP_PCT];

APPLY_NAME_ARG = {
    [APPLY.MAX_HP] = "Max HP %d",
    [APPLY.MAX_SP] = "Max MP %d",
    [APPLY.CON] = "Vitality %d",
    [APPLY.INT] = "Intelligence %d",
    [APPLY.STR] = "Strength %d",
    [APPLY.DEX] = "Dexterity %d",
    [APPLY.ATT_SPEED] = "Attack Speed %d%%",
    [APPLY.MOV_SPEED] = "Movement Speed %d%%",
    [APPLY.CAST_SPEED] = "Casting Speed %d%%",
    [APPLY.HP_REGEN] = "HP Regeneration %d%%",
    [APPLY.SP_REGEN] = "MP Regeneration %d%%",
    [APPLY.POISON_PCT] = "Poisoning chance %d%%",
    [APPLY.STUN_PCT] = "Blackout chance %d%%",
    [APPLY.SLOW_PCT] = "Slowing chance %d%%",
    [APPLY.CRITICAL_PCT] = "Chance of critical hit %d%%",
    [APPLY.PENETRATE_PCT] = "Chance of piercing hit %d%%",
    [APPLY.ATTBONUS_HUMAN] = "Strong against Half Humans %d%%",
    [APPLY.ATTBONUS_ANIMAL] = "Strong against Animals %d%%",
    [APPLY.ATTBONUS_ORC] = "Strong against Orcs %d%%",
    [APPLY.ATTBONUS_MILGYO] = "Strong against Mystics %d%%",
    [APPLY.ATTBONUS_UNDEAD] = "Strong against Undead %d%%",
    [APPLY.ATTBONUS_DEVIL] = "Strong against Devils %d%%",
    [APPLY.STEAL_HP] = "%d%% damage will be absorbed by HP",
    [APPLY.STEAL_SP] = "%d%% damage will be absorbed by MP",
    [APPLY.MANA_BURN_PCT] = "%d%% chance to rob SP",
    [APPLY.DAMAGE_SP_RECOVER] = "%d%% Chance to get back SP when hit",
    [APPLY.BLOCK] = "Chance to block a close-combat attack %d%%",
    [APPLY.DODGE] = "Chance to avoid Arrows %d%%",
    [APPLY.RESIST_SWORD] = "Sword Defence %d%%",
    [APPLY.RESIST_TWOHAND] = "Two-Handed Defence %d%%",
    [APPLY.RESIST_DAGGER] = "Dagger Defence %d%%",
    [APPLY.RESIST_BELL] = "Bell Defence %d%%",
    [APPLY.RESIST_BELL] = "Fan Defence %d%%",
    [APPLY.RESIST_BOW] = "Arrow Defence %d%%",
    [APPLY.RESIST_FIRE] = "Fire Resistance %d%%",
    [APPLY.RESIST_ELEC] = "Lightning Resistance %d%%",
    [APPLY.RESIST_MAGIC] = "Magic Resistance %d%%",
    [APPLY.RESIST_WIND] = "Wind Resistance %d%%",
    [APPLY.REFLECT_MELEE] = "Chance to reflect a close combat attack: %d%%",
    [APPLY.REFLECT_CURSE] = "Chance to reflect Curse: %d%%",
    [APPLY.POISON_REDUCE] = "Poisoning Resistance %d%%",
    [APPLY.KILL_SP_RECOVER] = "%d%% Chance to restore SP",
    [APPLY.EXP_DOUBLE_BONUS] = "%d%% Chance for EXP Bonus",
    [APPLY.GOLD_DOUBLE_BONUS] = "%d%% Chance to drop double Yang",
    [APPLY.ITEM_DROP_BONUS] = "%d%% Chance to drop double the Items",
    [APPLY.POTION_BONUS] = "Potion %d%% effect raise",
    [APPLY.KILL_HP_RECOVER] = "%d%% Chance to restore HP",
    [APPLY.IMMUNE_STUN] = "Defence against blackouts",
    [APPLY.IMMUNE_SLOW] = "Defence against slowing",
    [APPLY.IMMUNE_FALL] = "Immune against falling down",
    [APPLY.SKILL] = "CODE:SKILL (unk) %d",
    [APPLY.BOW_DISTANCE] = "Range %d m",
    [APPLY.ATT_GRADE_BONUS] = "Attack Value %d",
    [APPLY.DEF_GRADE_BONUS] = "Defence %d",
    [APPLY.MAGIC_ATT_GRADE] = "Magical Attack Value %d",
    [APPLY.MAGIC_DEF_GRADE] = "Magical Defence %d",
    [APPLY.CURSE_PCT] = "CODE:CURSE_PCT unk %d",
    [APPLY.MAX_STAMINA] = "Max. Endurance %d",
    [APPLY.ATTBONUS_WARRIOR] = "Strong against Warriors %d%%",
    [APPLY.ATTBONUS_ASSASSIN] = "Strong against Ninjas %d%%",
    [APPLY.ATTBONUS_SURA] = "Strong against Sura %d%%",
    [APPLY.ATTBONUS_SHAMAN] = "Strong against Shamans %d%%",
    [APPLY.ATTBONUS_MONSTER] = "Strength against monsters %d%%",
    [APPLY.MALL_ATTBONUS] = "Attack Value %d%%",
    [APPLY.MALL_DEFBONUS] = "Defence %d%%",
    [APPLY.MALL_EXPBONUS] = "EXP %d%%",
    [APPLY.MALL_ITEMBONUS] = "Item drop chance %d%%",
    [APPLY.MALL_GOLDBONUS] = "Yang drop chance %d%%",
    [APPLY.MAX_HP_PCT] = "Max. HP %d%%",
    [APPLY.MAX_SP_PCT] = "Max. SP %d%%",
    [APPLY.SKILL_DAMAGE_BONUS] = "Skill Damage %d%%",
    [APPLY.NORMAL_HIT_DAMAGE_BONUS] = "Average Damage %d%%",
    [APPLY.SKILL_DEFEND_BONUS] = "Resistance against Skill Damage %d%%",
    [APPLY.NORMAL_HIT_DEFEND_BONUS] = "Average Damage Resistance %d%%",
    [APPLY.PC_BANG_EXP_BONUS] = "iCafe EXP Bonus %d%%",
    [APPLY.PC_BANG_DROP_BONUS] = "iCafe Chance of looting items %d%%",
    [APPLY.EXTRACT_HP_PCT] = "CODE:EXTRACT_HP_PCT (unk) %d",
    [APPLY.RESIST_WARRIOR] = "Defence chance against warrior attacks: %d%%",
    [APPLY.RESIST_ASSASSIN] = "Defence chance against ninja attacks: %d%%",
    [APPLY.RESIST_SURA] = "Defence chance against sura attacks: %d%%",
    [APPLY.RESIST_SHAMAN] = "Defence chance against shaman attacks: %d%%",
    [APPLY.ENERGY] = "Energy %d",
    [APPLY.DEF_GRADE] = "CODE:DEF_GRADE (unk) %d",
    [APPLY.COSTUME_ATTR_BONUS] = "Costume bonus %d%%",
    [APPLY.MAGIC_ATTBONUS_PER] = "Magic attack %d%%",
    [APPLY.MELEE_MAGIC_ATTBONUS_PER] = "Magic/melee attack %d%%",
    [APPLY.RESIST_ICE] = "Ice Resistance %d%%",
    [APPLY.RESIST_EARTH] = "Earth Resistance %d%%",
    [APPLY.RESIST_DARK] = "Resistance against darkness %d%%",
    [APPLY.ANTI_CRITICAL_PCT] = "Resistance against critical hits %d%%",
    [APPLY.ANTI_PENETRATE_PCT] = "Resistance against piercing hits %d%%",
    [APPLY.BLEEDING_REDUCE] = "Bleeding Attack Resistance: %d%%",
    [APPLY.BLEEDING_PCT] = "Bleeding attack %d%%",
    [APPLY.ATTBONUS_WOLFMAN] = "Strong against Lycans %d%%",
    [APPLY.RESIST_WOLFMAN] = "Defence chance against Lycan attacks: %d%%",
    [APPLY.RESIST_CLAW] = "Claw Defence %d%%",
    [APPLY.MOUNT] = "CODE:MOUNT (unk)",
    [APPLY.ACCEDRAIN_RATE] = "Absorption rate: %d%%",
    [APPLY.RESIST_MAGIC_REDUCTION] = "Magic penetration of %d%%",
    [APPLY.ENCHANT_ELECT] = "Power of Lightning %d%%",
    [APPLY.ENCHANT_FIRE] = "Power of Fire %d%%",
    [APPLY.ENCHANT_ICE] = "Power of Ice %d%%",
    [APPLY.ENCHANT_WIND] = "Power of Wind %d%%",
    [APPLY.ENCHANT_EARTH] = "Power of Earth %d%%",
    [APPLY.ENCHANT_DARK] = "Power of Darkness %d%%",
    [APPLY.ATTBONUS_CZ] = "Strong against Zodiac Monsters %d%%",
    [APPLY.ATTBONUS_INSECT] = "Strong against Insects %d%%",
    [APPLY.ATTBONUS_DESERT] = "Strong against Desert Monsters %d%%",
    [APPLY.ATTBONUS_SWORD] = "Sword Defence Break %d%%",
    [APPLY.ATTBONUS_TWOHAND] = "Two-handed Defence Break %d%%",
    [APPLY.ATTBONUS_DAGGER] = "Dagger Defence Break %d%%",
    [APPLY.ATTBONUS_BELL] = "Bell Defence Break %d%%",
    [APPLY.ATTBONUS_FAN] = "Fan Defence Break %d%%",
    [APPLY.ATTBONUS_BOW] = "Arrow Defence Break %d%%",
    [APPLY.ATTBONUS_CLAW] = "Claw Defence Break %d%%",
    [APPLY.RESIST_HUMAN] = "Resistance to Half Humans %d%%"
};
APPLY_NAME_ARG[APPLY.MAX_MP] = APPLY_NAME_ARG[APPLY.MAX_SP];
APPLY_NAME_ARG[APPLY.VIT] = APPLY_NAME_ARG[APPLY.CON];
APPLY_NAME_ARG[APPLY.MP_REGEN] = APPLY_NAME_ARG[APPLY.SP_REGEN];
APPLY_NAME_ARG[APPLY.STEAL_MP] = APPLY_NAME_ARG[APPLY.STEAL_SP];
APPLY_NAME_ARG[APPLY.DAMAGE_MP_RECOVER] = APPLY_NAME_ARG[APPLY.DAMAGE_SP_RECOVER];
APPLY_NAME_ARG[APPLY.RESIST_ARROW] = APPLY_NAME_ARG[APPLY.RESIST_BOW];
APPLY_NAME_ARG[APPLY.MAX_MP_PCT] = APPLY_NAME_ARG[APPLY.MAX_SP_PCT];

POINT = {
    LEVEL    = 1,
    VOICE    = 2,
    EXP      = 3,
    NEXT_EXP = 4,
    HP       = 5,
    MAX_HP   = 6,
    SP       = 7,
    MAX_SP   = 8,
    STAMINA  = 9,
    MAX_STAMINA = 10,

    GOLD      = 11,
    ST        = 12,
    HT        = 13,
    DX        = 14,
    IQ        = 15,
    DEF_GRADE = 16,
    ATT_SPEED = 17,
    ATT_GRADE = 18,
    MOV_SPEED = 19,
    CLIENT_DEF_GRADE = 20,
    CASTING_SPEED    = 21,
    MAGIC_ATT_GRADE  = 22,
    MAGIC_DEF_GRADE  = 23,
    EMPIRE_POINT     = 24,
    LEVEL_STEP       = 25,
    STAT             = 26,
    SUB_SKILL        = 27,
    SKILL            = 28,
    WEAPON_MIN       = 29,
    WEAPON_MAX       = 30,
    PLAYTIME         = 31,
    HP_REGEN         = 32,
    SP_REGEN         = 33,

    BOW_DISTANCE     = 34,

    HP_RECOVERY = 35,
    SP_RECOVERY = 36,

    POISON_PCT    = 37,
    STUN_PCT      = 38,
    SLOW_PCT      = 39,
    CRITICAL_PCT  = 40,
    PENETRATE_PCT = 41,
    CURSE_PCT     = 42,

    ATTBONUS_HUMAN  = 43,
    ATTBONUS_ANIMAL = 44,
    ATTBONUS_ORC    = 45,
    ATTBONUS_MILGYO = 46,
    ATTBONUS_UNDEAD = 47,
    ATTBONUS_DEVIL  = 48,
    ATTBONUS_INSECT = 49,
    ATTBONUS_FIRE   = 50,
    ATTBONUS_ICE    = 51,
    ATTBONUS_DESERT = 52,
    ATTBONUS_MONSTER   = 53,
    ATTBONUS_WARRIOR   = 54,
    ATTBONUS_ASSASSIN  = 55,
    ATTBONUS_SURA      = 56,
    ATTBONUS_SHAMAN    = 57,
    ATTBONUS_TREE      = 58,

    RESIST_WARRIOR  = 59,
    RESIST_ASSASSIN = 60,
    RESIST_SURA     = 61,
    RESIST_SHAMAN   = 62,

    STEAL_HP = 63,
    STEAL_SP = 64,

    MANA_BURN_PCT     = 65,
    DAMAGE_SP_RECOVER = 66,

    BLOCK = 67,
    DODGE = 68,

    RESIST_SWORD   = 69,
    RESIST_TWOHAND = 70,
    RESIST_DAGGER  = 71,
    RESIST_BELL    = 72,
    RESIST_FAN     = 73,
    RESIST_BOW     = 74,
    RESIST_FIRE    = 75,
    RESIST_ELEC    = 76,
    RESIST_MAGIC   = 77,
    RESIST_WIND    = 78,

    REFLECT_MELEE = 79,
    REFLECT_CURSE = 80,
    POISON_REDUCE = 81,

    KILL_SP_RECOVER   = 82,
    EXP_DOUBLE_BONUS  = 83,
    GOLD_DOUBLE_BONUS = 84,
    ITEM_DROP_BONUS   = 85,

    POTION_BONUS     = 86,
    KILL_HP_RECOVERY = 87,

    IMMUNE_STUN      = 88,
    IMMUNE_SLOW      = 89,
    IMMUNE_FALL      = 90,

    PARTY_ATTACKER_BONUS = 91,
    PARTY_TANKER_BONUS   = 92,

    ATT_BONUS = 93,
    DEF_BONUS = 94,

    ATT_GRADE_BONUS = 95,
    DEF_GRADE_BONUS = 96,
    MAGIC_ATT_GRADE_BONUS = 97,
    MAGIC_DEF_GRADE_BONUS = 98,

    RESIST_NORMAL_DAMAGE = 99,

    HIT_HP_RECOVERY = 100,
    HIT_SP_RECOVERY = 101,
    MANASHIELD      = 102,

    PARTY_BUFFER_BONUS       = 103,
    PARTY_SKILL_MASTER_BONUS = 104,

    HP_RECOVER_CONTINUE = 105,
    SP_RECOVER_CONTINUE = 106,

    STEAL_GOLD  = 107,
    POLYMORPH   = 108,
    MOUNT       = 109,

    PARTY_HASTE_BONUS    = 110,
    PARTY_DEFENDER_BONUS = 111,
    STAT_RESET_COUNT     = 112,

    HORSE_SKILL = 113,

    MALL_ATTBONUS  = 114,
    MALL_DEFBONUS  = 115,
    MALL_EXPBONUS  = 116,
    MALL_ITEMBONUS = 117,
    MALL_GOLDBONUS = 118,

    MAX_HP_PCT = 119,
    MAX_SP_PCT = 120,

    SKILL_DAMAGE_BONUS      = 121,
    NORMAL_HIT_DAMAGE_BONUS = 122,

    SKILL_DEFEND_BONUS      = 123,
    NORMAL_HIT_DEFEND_BONUS = 124,

    PC_BANG_EXP_BONUS  = 125,
    PC_BANG_DROP_BONUS = 126,

    RAMADAN_CANDY_BONUS_EXP = 127,

    ENERGY = 128,

    ENERGY_END_TIME = 129,

    COSTUME_ATTR_BONUS = 130,
    MAGIC_ATT_BONUS_PER = 131,
    MELEE_MAGIC_ATT_BONUS_PER = 132,

    RESIST_ICE = 133,
    RESIST_EARTH = 134,
    RESIST_DARK = 135,

    RESIST_CRITICAL = 136,
    RESIST_PENETRATE = 137,

    BLEEDING_REDUCE = 138,
    BLEEDING_PCT = 139,

    ATTBONUS_WOLFMAN = 140,
    RESIST_WOLFMAN = 141,
    RESIST_CLAW = 142,

    ACCEDRAIN_RATE = 143,

    RESIST_MAGIC_REDUCTION = 144,

    ENCHANT_ELECT = 145,
    ENCHANT_FIRE = 146,
    ENCHANT_ICE = 147,
    ENCHANT_WIND = 148,
    ENCHANT_EARTH = 149,
    ENCHANT_DARK = 150,

    MAX = 151,
};

POINT_NAME = {
    [POINT.LEVEL] = "Level",
    [POINT.VOICE] = "Voice",
    [POINT.EXP] = "Exp.",
    [POINT.NEXT_EXP] = "Needed Exp.",
    [POINT.HP] = "HP",
    [POINT.MAX_HP] = "Max. HP",
    [POINT.SP] = "SP",
    [POINT.MAX_SP] = "Max. SP",
    [POINT.STAMINA] = "ST",
    [POINT.MAX_STAMINA] = "Max. ST",

    [POINT.GOLD] = "Gold",

    --[[
    ST        = 12,
    HT        = 13,
    DX        = 14,
    IQ        = 15,
    DEF_GRADE = 16,
    ATT_SPEED = 17,
    ATT_GRADE = 18,
    MOV_SPEED = 19,
    CLIENT_DEF_GRADE = 20,
    CASTING_SPEED    = 21,
    MAGIC_ATT_GRADE  = 22,
    MAGIC_DEF_GRADE  = 23,
    EMPIRE_POINT     = 24,
    LEVEL_STEP       = 25,
    STAT             = 26,
    SUB_SKILL        = 27,
    SKILL            = 28,
    WEAPON_MIN       = 29,
    WEAPON_MAX       = 30,
    PLAYTIME         = 31,
    HP_REGEN         = 32,
    SP_REGEN         = 33,

    BOW_DISTANCE     = 34,

    HP_RECOVERY = 35,
    SP_RECOVERY = 36,

    POISON_PCT    = 37,
    STUN_PCT      = 38,
    SLOW_PCT      = 39,
    CRITICAL_PCT  = 40,
    PENETRATE_PCT = 41,
    CURSE_PCT     = 42,

    ATTBONUS_HUMAN  = 43,
    ATTBONUS_ANIMAL = 44,
    ATTBONUS_ORC    = 45,
    ATTBONUS_MILGYO = 46,
    ATTBONUS_UNDEAD = 47,
    ATTBONUS_DEVIL  = 48,
    ATTBONUS_INSECT = 49,
    ATTBONUS_FIRE   = 50,
    ATTBONUS_ICE    = 51,
    ATTBONUS_DESERT = 52,
    ATTBONUS_MONSTER   = 53,
    ]]
    [POINT.ATTBONUS_WARRIOR]  = "Strong against Warriors",
    [POINT.ATTBONUS_ASSASSIN] = "Strong against Ninjas",
    [POINT.ATTBONUS_SURA]     = "Strong against Sura",
    [POINT.ATTBONUS_SHAMAN]   = "Strong against Shamans",
    --ATTBONUS_TREE      = 58,

    [POINT.RESIST_WARRIOR]  = "Defence chance against warrior attacks",
    [POINT.RESIST_ASSASSIN] = "Defence chance against ninja attacks",
    [POINT.RESIST_SURA]     = "Defence chance against sura attacks",
    [POINT.RESIST_SHAMAN]   = "Defence chance against shaman attacks",

    --[[
    STEAL_HP = 63,
    STEAL_SP = 64,

    MANA_BURN_PCT     = 65,
    DAMAGE_SP_RECOVER = 66,

    BLOCK = 67,
    DODGE = 68,

    RESIST_SWORD   = 69,
    RESIST_TWOHAND = 70,
    RESIST_DAGGER  = 71,
    RESIST_BELL    = 72,
    RESIST_FAN     = 73,
    RESIST_BOW     = 74,
    RESIST_FIRE    = 75,
    RESIST_ELEC    = 76,
    RESIST_MAGIC   = 77,
    RESIST_WIND    = 78,

    REFLECT_MELEE = 79,
    REFLECT_CURSE = 80,
    POISON_REDUCE = 81,

    KILL_SP_RECOVER   = 82,
    EXP_DOUBLE_BONUS  = 83,
    GOLD_DOUBLE_BONUS = 84,
    ITEM_DROP_BONUS   = 85,

    POTION_BONUS     = 86,
    KILL_HP_RECOVERY = 87,

    IMMUNE_STUN      = 88,
    IMMUNE_SLOW      = 89,
    IMMUNE_FALL      = 90,

    PARTY_ATTACKER_BONUS = 91,
    PARTY_TANKER_BONUS   = 92,
    ]]

    [POINT.ATT_BONUS] = "Damage",
    [POINT.DEF_BONUS] = "Defence",

    --[[
    ATT_GRADE_BONUS = 95,
    DEF_GRADE_BONUS = 96,
    MAGIC_ATT_GRADE_BONUS = 97,
    MAGIC_DEF_GRADE_BONUS = 98,

    RESIST_NORMAL_DAMAGE = 99,

    HIT_HP_RECOVERY = 100,
    HIT_SP_RECOVERY = 101,
    MANASHIELD      = 102,

    PARTY_BUFFER_BONUS       = 103,
    PARTY_SKILL_MASTER_BONUS = 104,

    HP_RECOVER_CONTINUE = 105,
    SP_RECOVER_CONTINUE = 106,

    STEAL_GOLD  = 107,
    POLYMORPH   = 108,
    MOUNT       = 109,

    PARTY_HASTE_BONUS    = 110,
    PARTY_DEFENDER_BONUS = 111,
    STAT_RESET_COUNT     = 112,

    HORSE_SKILL = 113,

    MALL_ATTBONUS  = 114,
    MALL_DEFBONUS  = 115,
    MALL_EXPBONUS  = 116,
    MALL_ITEMBONUS = 117,
    MALL_GOLDBONUS = 118,

    MAX_HP_PCT = 119,
    MAX_SP_PCT = 120,

    SKILL_DAMAGE_BONUS      = 121,
    NORMAL_HIT_DAMAGE_BONUS = 122,

    SKILL_DEFEND_BONUS      = 123,
    NORMAL_HIT_DEFEND_BONUS = 124,

    PC_BANG_EXP_BONUS  = 125,
    PC_BANG_DROP_BONUS = 126,

    RAMADAN_CANDY_BONUS_EXP = 127,

    ENERGY = 128,

    ENERGY_END_TIME = 129,

    COSTUME_ATTR_BONUS = 130,
    MAGIC_ATT_BONUS_PER = 131,
    MELEE_MAGIC_ATT_BONUS_PER = 132,

    RESIST_ICE = 133,
    RESIST_EARTH = 134,
    RESIST_DARK = 135,

    RESIST_CRITICAL = 136,
    RESIST_PENETRATE = 137,

    BLEEDING_REDUCE = 138,
    BLEEDING_PCT = 139,

    ATTBONUS_WOLFMAN = 140,
    RESIST_WOLFMAN = 141,
    RESIST_CLAW = 142,

    ACCEDRAIN_RATE = 143,

    RESIST_MAGIC_REDUCTION = 144,

    ENCHANT_ELECT = 145,
    ENCHANT_FIRE = 146,
    ENCHANT_ICE = 147,
    ENCHANT_WIND = 148,
    ENCHANT_EARTH = 149,
    ENCHANT_DARK = 150,

    MAX = 151,
    ]]
};

--[[
    The list of all the normal skills for each race and class.
]]
ACTIVE_SKILL_LIST = {
    [JOB.WARRIOR] = {
        [SPECS.BODY_FORCE] = {1, 2, 3, 4, 5, 6},
        [SPECS.MENTAL_FIGHT] = {16, 17, 18, 19, 20, 21}
    },
    [JOB.NINJA] = {
        [SPECS.BLADE_FIGHT] = {31, 32, 33, 34, 35, 36},
        [SPECS.ARCHERY] = {46, 47, 48, 49, 50, 51}
    },
    [JOB.SURA] = {
        [SPECS.WEAPONRY] = {61, 62, 63, 64, 65, 66},
        [SPECS.BLACK_MAGIC] = {76, 77, 78, 79, 80, 81}
    },
    [JOB.SHAMAN] = {
        [SPECS.DRAGON_FORCE] = {91, 92, 93, 94, 95, 96},
        [SPECS.HEALING_FORCE] = {106, 107, 108, 109, 110, 111}
    },
    [JOB.WOLFMAN] = {
        [SPECS.INSTINCT] = {170, 171, 172, 173, 174, 175}
    }
};
SPECS.ASSASSIN_BLADE_FIGHT = SPECS.NINJA_BLADE_FIGHT;
SPECS.ASSASSIN_ARCHERY = SPECS.NINJA_ARCHERY;
SPECS.LYCAN_INSTINCT = SPECS.WOLFMAN_INSTINCT;

--[[
    The list of all the yohara skills for each race and class.
]]
YOHARA_SKILL_BY_JOB_AND_SPEC = {
    [JOB.WARRIOR] = {
        [SPECS.BODY_FORCE] = 176,
        [SPECS.MENTAL_FIGHT] = 176
    },
    [JOB.NINJA] = {
        [SPECS.BLADE_FIGHT] = 177,
        [SPECS.ARCHERY] = 178
    },
    [JOB.SURA] = {
        [SPECS.WEAPONRY] = 179,
        [SPECS.BLACK_MAGIC] = 180
    },
    [JOB.SHAMAN] = {
        [SPECS.DRAGON_FORCE] = 181,
        [SPECS.HEALING_FORCE] = 182
    },
    [JOB.LYCAN] = {
        [SPECS.INSTINCT] = 183
    }
};

BOOST_SKILL_LIST = {236, 237, 238, 239, 240, 241, 242, 243, 244};
WARD_SKILL_LIST = {221, 222, 223, 224, 225, 226, 227, 228, 229};
BOOST_WARD_SKILL_LIST = {221, 222, 223, 224, 225, 226, 227, 228, 229, 236, 237, 238, 239, 240, 241, 242, 243, 244};

--[[
    The list of all the passive boost skills for each race and class.
]]
BOOST_SKILL_BY_JOB_AND_SPEC = {
    [JOB.WARRIOR] = {
        [SPECS.BODY_FORCE] = 236,
        [SPECS.MENTAL_FIGHT] = 240
    },
    [JOB.NINJA] = {
        [SPECS.BLADE_FIGHT] = 237,
        [SPECS.ARCHERY] = 241
    },
    [JOB.SURA] = {
        [SPECS.WEAPONRY] = 238,
        [SPECS.BLACK_MAGIC] = 242
    },
    [JOB.SHAMAN] = {
        [SPECS.DRAGON_FORCE] = 239,
        [SPECS.HEALING_FORCE] = 243
    },
    [JOB.WOLFMAN] = {
        [SPECS.INSTINCT] = 244
    }
};
BOOST_SKILL_BY_JOB_AND_SPEC[JOB.ASSASSIN] = BOOST_SKILL_BY_JOB_AND_SPEC[JOB.NINJA];
BOOST_SKILL_BY_JOB_AND_SPEC[JOB.LYCAN] = BOOST_SKILL_BY_JOB_AND_SPEC[JOB.WOLFMAN];

--[[
    The list of race names based on sex. (In english they don't change)
]]
JOB_NAME_LIST = {
    [JOB.WARRIOR] = "Warrior",
    [JOB.NINJA] = "Ninja",
    [JOB.SURA] = "Sura",
    [JOB.SHAMAN] = "Shaman",
    [JOB.WOLFMAN] = "Lycan",
};
JOB_NAME_LIST[JOB.ASSASSIN] = JOB_NAME_LIST[JOB.NINJA];
JOB_NAME_LIST[JOB.LYCAN] = JOB_NAME_LIST[JOB.WOLFMAN];

--[[
    A list of sexes for each race.
]]
JOB_TO_RACE = {
    [JOB.WARRIOR] = {
        [SEX.MALE] = RACE.WARRIOR_M,
        [SEX.FEMALE] = RACE.WARRIOR_W
    },
    [JOB.NINJA] = {
        [SEX.MALE] = RACE.NINJA_M,
        [SEX.FEMALE] = RACE.NINJA_W
    },
    [JOB.SURA] = {
        [SEX.MALE] = RACE.SURA_M,
        [SEX.FEMALE] = RACE.SURA_W
    },
    [JOB.SHAMAN] = {
        [SEX.MALE] = RACE.SHAMAN_M,
        [SEX.FEMALE] = RACE.SHAMAN_W
    },
    [JOB.WOLFMAN] = {
        [SEX.MALE] = RACE.WOLFMAN_M
    }
};
JOB_TO_RACE[JOB.ASSASSIN] = JOB_NAME_LIST[JOB.NINJA];
JOB_TO_RACE[JOB.LYCAN] = JOB_NAME_LIST[JOB.WOLFMAN];

--[[
    The list of race names based on sex. (In english they don't change)
]]
RACE_NAME_LIST = {
    [RACE.WARRIOR_M] = "Warrior (M)",
    [RACE.NINJA_W] = "Ninja (W)",
    [RACE.SURA_M] = "Sura (M)",
    [RACE.SHAMAN_W] = "Shaman (W)",
    --
    [RACE.WARRIOR_W] = "Warrior (W)",
    [RACE.NINJA_M] = "Ninja (M)",
    [RACE.SURA_W] = "Sura (W)",
    [RACE.SHAMAN_M] = "Shaman (M)",
    --
    [RACE.WOLFMAN_M] = "Lycan (M)"
};
RACE_NAME_LIST[RACE.ASSASSIN_M] = RACE_NAME_LIST[RACE.NINJA_M];
RACE_NAME_LIST[RACE.ASSASSIN_W] = RACE_NAME_LIST[RACE.NINJA_W];
RACE_NAME_LIST[RACE.LYCAN_M] = RACE_NAME_LIST[RACE.WOLFMAN_M];

--[[
    A list of jobs for each race.
]]
RACE_TO_JOB = {
    [RACE.WARRIOR_M] = JOB.WARRIOR,
    [RACE.NINJA_W] = JOB.NINJA,
    [RACE.SURA_M] = JOB.SURA,
    [RACE.SHAMAN_W] = JOB.SHAMAN,
    --
    [RACE.WARRIOR_W] = JOB.WARRIOR,
    [RACE.NINJA_M] = JOB.NINJA,
    [RACE.SURA_W] = JOB.SURA,
    [RACE.SHAMAN_M] = JOB.SHAMAN,
    --
    [RACE.WOLFMAN_M] = JOB.WOLFMAN
};
RACE_TO_JOB[RACE.ASSASSIN_M] = RACE_TO_JOB[RACE.NINJA_M];
RACE_TO_JOB[RACE.ASSASSIN_W] = RACE_TO_JOB[RACE.NINJA_W];
RACE_TO_JOB[RACE.LYCAN_M] = RACE_TO_JOB[RACE.WOLFMAN_M];

--[[
    A list of sexes for each race.
]]
RACE_TO_SEX = {
    [RACE.WARRIOR_M] = SEX.MALE,
    [RACE.NINJA_W] = SEX.FEMALE,
    [RACE.SURA_M] = SEX.MALE,
    [RACE.SHAMAN_W] = SEX.FEMALE,
    --
    [RACE.WARRIOR_W] = SEX.FEMALE,
    [RACE.NINJA_M] = SEX.MALE,
    [RACE.SURA_W] = SEX.FEMALE,
    [RACE.SHAMAN_M] = SEX.MALE,
    --
    [RACE.WOLFMAN_M] = SEX.MALE
};
RACE_TO_SEX[RACE.ASSASSIN_M] = RACE_TO_JOB[RACE.NINJA_M];
RACE_TO_SEX[RACE.ASSASSIN_W] = RACE_TO_JOB[RACE.NINJA_W];
RACE_TO_SEX[RACE.LYCAN_M] = RACE_TO_JOB[RACE.WOLFMAN_M];

--[[
    The list of original races.
]]
PC_RACE_LIST = {RACE.WARRIOR_M, RACE.NINJA_W, RACE.SURA_M, RACE.SHAMAN_W};

--[[
    The list of season1 races.
]]
PC2_RACE_LIST = {RACE.WARRIOR_W, RACE.NINJA_M, RACE.SURA_W, RACE.SHAMAN_M};

--[[
    The list of wolfman update races.
]]
PC3_RACE_LIST = {RACE.WOLFMAN_M};

--[[
    The list of male races.
]]
MALE_RACE_LIST = {RACE.WARRIOR_M, RACE.NINJA_M, RACE.SURA_M, RACE.SHAMAN_M, RACE.WOLFMAN_M};

--[[
    The list of female races.
]]
FEMALE_RACE_LIST = {RACE.WARRIOR_W, RACE.NINJA_W, RACE.SURA_W, RACE.SHAMAN_W};

--[[
    The list of the names for each sex.
]]
SEX_NAME_LIST = {
    [SEX.MALE] = "Male",
    [SEX.FEMALE] = "Female"
};

--[[
    The list of the names for each status.
]]
STATUS_NAME_LIST = {
    [STATUS.CON] = {["str"] = "Vitality",     ["label"] = "VIT"},
    [STATUS.INT] = {["str"] = "Intelligence", ["label"] = "INT"},
    [STATUS.STR] = {["str"] = "Strength",     ["label"] = "STR"},
    [STATUS.DEX] = {["str"] = "Dexterity",    ["label"] = "DEX"}
};
STATUS_NAME_LIST[STATUS.VIT] = STATUS_NAME_LIST[STATUS.CON];

--[[
    The list of class names.
]]
DOCTRINE_NAME_LIST = {
    [JOB.WARRIOR] = {
        [SPECS.BODY_FORCE] = "Body-Force",
        [SPECS.MENTAL_FIGHT] = "Mental-Fight"
    },
    [JOB.NINJA] = {
        [SPECS.BLADE_FIGHT] = "Blade-Fight",
        [SPECS.ARCHERY] = "Archery"
    },
    [JOB.SURA] = {
        [SPECS.WEAPONRY] = "Weaponry",
        [SPECS.BLACK_MAGIC] = "Black Magic"
    },
    [JOB.SHAMAN] = {
        [SPECS.DRAGON_FORCE] = "Dragon Force",
        [SPECS.HEALING_FORCE] = "Healing Force"
    },
    [JOB.LYCAN] = {
        [SPECS.INSTINCT] = "Instinct"
    }
};

--[[
    The list of the names of the skills for each race and class.
]]
SKILL_NAME_TABLE = {
    --** Body Warrior
    [1] = "Three-Way Cut",
    [2] = "Sword Spin",
    [3] = "Berserk",
    [4] = "Aura of the Sword",
    [5] = "Dash",
    [6] = "Life Force",
    [176] = "Earthquake",

    --** Mental Warrior
    [16] = "Spirit Strike (W)",
    [17] = "Bash",
    [18] = "Stump",
    [19] = "Strong Body",
    [20] = "Sword Strike",
    [21] = "Sword Orb",
    --[176] = "Earthquake", -- duplicate, it's the same for both warrior classes

    --** Blade Fight Ninja
    [31] = "Ambush",
    [32] = "Fast Attack",
    [33] = "Rolling Dagger",
    [34] = "Stealth",
    [35] = "Poisonous Cloud",
    [36] = "Insidious Poison",
    [177] = "Astral Light",

    --** Archery Ninja
    [46] = "Repetitive Shot",
    [47] = "Arrow Shower",
    [48] = "Fire Arrow",
    [49] = "Feather Walk",
    [50] = "Poison Arrow",
    [51] = "Spark",
    [178] = "Storm Shot",

    --** Weaponry Sura
    [61] = "Finger Strike",
    [62] = "Dragon Swirl",
    [63] = "Enchanted Blade",
    [64] = "Fear",
    [65] = "Enchanted Armour",
    [66] = "Dispel",
    [179] = "Hell Strike",

    --** Black Magic Sura
    [76] = "Dark Strike",
    [77] = "Flame Strike",
    [78] = "Flame Spirit",
    [79] = "Dark Protection",
    [80] = "Spirit Strike (S)",
    [81] = "Dark Orb",
    [180] = "Death Wave",

    --** Dragon Force Shaman
    [91] = "Flying Talisman",
    [92] = "Shooting Dragon",
    [93] = "Dragon's Roar",
    [94] = "Blessing",
    [95] = "Reflect",
    [96] = "Dragon's Aid",
    [181] = "Meteor",

    --** Healing Force Shaman
    [106] = "Lightning Throw",
    [107] = "Summon Lightning",
    [108] = "Lightning Claw",
    [109] = "Cure",
    [110] = "Swiftness",
    [111] = "Attack Up",
    [182] = "Aether Ward",

    --** Instinct Lycan
    [170] = "Shred",
    [171] = "Wolf's Breath",
    [172] = "Wolf Pounce",
    [173] = "Wolf's Claw",
    [174] = "Crimson Wolf Soul",
    [175] = "Indigo Wolf Soul",
    [183] = "Talon Storm",

    --** Secondary Skills
    [121] = "Leadership",
    [122] = "Combo",
    [124] = "Mining",
    [126] = "Shinsoo Language",
    [127] = "Chunjo Language",
    [128] = "Jinno Language",
    [129] = "Polymorph",
    [130] = "Horse Riding",
    [131] = "Call Horse",

    --** Horse skills
    [137] = "Horseback Slash",
    [138] = "Horse Stump",
    [139] = "Power Wave",
    [140] = "Arrow Storm",

    -- Passives
    [221] = "Sword Spin Ward",
    [222] = "Ambush Ward",
    [223] = "Finger Strike Ward",
    [224] = "Shooting Dragon Ward",
    [225] = "Spirit Strike (W) Ward",
    [226] = "Fire Arrow Ward",
    [227] = "Dark Strike Ward",
    [228] = "Summon Lightning Ward",
    [229] = "Wolf's Breath Ward",

    -- Boosts
    [236] = "Sword Spin Boost",
    [237] = "Ambush Boost",
    [238] = "Finger Strike Boost",
    [239] = "Shooting Dragon Boost",
    [240] = "Spirit Strike (W) Boost",
    [241] = "Fire Arrow Boost",
    [242] = "Dark Strike Boost",
    [243] = "Summon Lightning Boost",
    [244] = "Wolf's Breath Boost",
};

--[[
    The list of the names for each empire.
]]
EMPIRE_NAME_LIST = {
    [EMPIRES.SHINSOO] = "Shinsoo",
    [EMPIRES.CHUNJO] = "Chunjo",
    [EMPIRES.JINNO] = "Jinno"
};

--[[
    A list of colors. You can use color_say from my quest_functions list to easily use it.
]]
COLORS = {
    ["aliceblue"] = {240, 248, 255},     ["antiquewhite"] = {250, 235, 215},    ["aqua"] = {0, 255, 255},                   ["aquamarine"] = {127, 255, 212},
    ["azure"] = {240, 255, 255},         ["beige"] = {245, 245, 220},           ["bisque"] = {255, 228, 196},               ["black"] = {0, 0, 0},
    ["bronze"] = {205, 127, 50},         ["nabb_blue"] = {63, 108, 191},        ["normal_say"] = {196, 196, 196},           ["peach"] = {254, 227, 174},
    ["blanchedalmond"] = {255, 235, 205},["blue"] = {0, 0, 255},                ["blueviolet"] = {138, 43, 226},            ["brown"] = {165, 42, 42},
    ["burlywood"] = {222, 184, 135},     ["cadetblue"] = {95, 158, 160},        ["chartreuse"] = {127, 255, 0},             ["chocolate"] = {210, 105, 30},
    ["coral"] = {255, 127, 80},          ["cornflowerblue"] = {100, 149, 237},  ["cornsilk"] = {255, 248, 220},             ["crimson"] = {220, 20, 60},
    ["cyan"] = {0, 255, 255},            ["darkblue"] = {0, 0, 139},            ["darkcyan"] = {0, 139, 139},               ["darkgoldenrod"] = {184, 134, 11},
    ["darkgray"] = {169, 169, 169},      ["darkgreen"] = {0, 100, 0},           ["darkkhaki"] = {189, 183, 107},            ["darkmagenta"] = {139, 0, 139},
    ["darkolivegreen"] = {85, 107, 47},  ["darkorange"] = {255, 140, 0},        ["darkorchid"] = {153, 50, 204},            ["darkred"] = {139, 0, 0},
    ["darksalmon"] = {233, 150, 122},    ["darkseagreen"] = {143, 188, 139},    ["darkslateblue"] = {72, 61, 139},          ["darkslategray"] = {47, 79, 79},
    ["darkturquoise"] = {0, 206, 209},   ["darkviolet"] = {148, 0, 211},        ["deeppink"] = {255, 20, 147},              ["deepskyblue"] = {0, 191, 255},
    ["dimgray"] = {105, 105, 105},       ["dodgerblue"] = {30, 144, 255},       ["firebrick"] = {178, 34, 34},              ["floralwhite"] = {255, 250, 240},
    ["forestgreen"] = {34, 139, 34},     ["fuchsia"] = {255, 0, 255},           ["gainsboro"] = {220, 220, 220},            ["ghostwhite"] = {248, 248, 255},
    ["gold"] = {255, 215, 0},            ["goldenrod"] = {218, 165, 32},        ["gray"] = {128, 128, 128},                 ["green"] = {0, 128, 0},
    ["greenyellow"] = {173, 255, 47},    ["honeydew"] = {240, 255, 240},        ["hotpink"] = {255, 105, 180},              ["indianred"] = {205, 92, 92},
    ["indigo"] = {75, 0, 130},           ["ivory"] = {255, 255, 240},           ["khaki"] = {240, 230, 140},                ["lavender"] = {230, 230, 250},
    ["lavenderblush"] = {255, 240, 245}, ["lawngreen"] = {124, 252, 0},         ["lemonchiffon"] = {255, 250, 205},         ["lightblue"] = {173, 216, 230},
    ["lightcoral"] = {240, 128, 128},    ["lightcyan"] = {224, 255, 255},       ["lightgoldenrodyellow"] = {250, 250, 210}, ["lightgray"] = {211, 211, 211},
    ["lightgreen"] = {144, 238, 144},    ["lightpink"] = {255, 182, 193},       ["lightsalmon"] = {255, 160, 122},          ["lightseagreen"] = {32, 178, 170},
    ["lightskyblue"] = {135, 206, 250},  ["lightslategray"] = {119, 136, 153},  ["lightsteelblue"] = {176, 196, 222},       ["lightyellow"] = {255, 255, 224},
    ["lime"] = {0, 255, 0},              ["limegreen"] = {50, 205, 50},         ["linen"] = {250, 240, 230},                ["magenta"] = {255, 0, 255},
    ["maroon"] = {128, 0, 0},            ["mediumaquamarine"] = {102, 205, 170},["mediumblue"] = {0, 0, 205},               ["mediumorchid"] = {186, 85, 211},
    ["mediumpurple"] = {147, 112, 219},  ["mediumseagreen"] = {60, 179, 113},   ["mediumslateblue"] = {123, 104, 238},      ["mediumspringgreen"] = {0, 250, 154},
    ["mediumturquoise"] = {72, 209, 204},["mediumvioletred"] = {199, 21, 133},  ["midnightblue"] = {25, 25, 112},           ["mintcream"] = {245, 255, 250},
    ["mistyrose"] = {255, 228, 225},     ["moccasin"] = {255, 228, 181},        ["navajowhite"] = {255, 222, 173},          ["navy"] = {0, 0, 128},
    ["oldlace"] = {253, 245, 230},       ["olive"] = {128, 128, 0},             ["olivedrab"] = {107, 142, 35},             ["orange"] = {255, 165, 0},
    ["orangered"] = {255, 69, 0},        ["orchid"] = {218, 112, 214},          ["palegoldenrod"] = {238, 232, 170},        ["palegreen"] = {152, 251, 152},
    ["paleturquoise"] = {175, 238, 238}, ["palevioletred"] = {219, 112, 147},   ["papayawhip"] = {255, 239, 213},           ["peachpuff"] = {255, 218, 185},
    ["peru"] = {205, 133, 63},           ["pink"] = {255, 192, 203},            ["plum"] = {221, 160, 221},                 ["powderblue"] = {176, 224, 230},
    ["purple"] = {128, 0, 128},          ["red"] = {255, 0, 0},                 ["rosybrown"] = {188, 143, 143},            ["royalblue"] = {65, 105, 225},
    ["saddlebrown"] = {139, 69, 19},     ["salmon"] = {250, 128, 114},          ["sandybrown"] = {244, 164, 96},            ["seagreen"] = {46, 139, 87},
    ["seashell"] = {255, 245, 238},      ["sienna"] = {160, 82, 45},            ["silver"] = {192, 192, 192},               ["skyblue"] = {135, 206, 235},
    ["slateblue"] = {106, 90, 205},      ["slategray"] = {112, 128, 144},       ["snow"] = {255, 250, 250},                 ["springgreen"] = {0, 255, 127},
    ["steelblue"] = {70, 130, 180},      ["tan"] = {210, 180, 140},             ["teal"] = {0, 128, 128},                   ["thistle"] = {216, 191, 216},
    ["tomato"] = {255, 99, 71},          ["turquoise"] = {64, 224, 208},        ["violet"] = {238, 130, 238},               ["wheat"] = {245, 222, 179},
    ["white"] = {255, 255, 255},         ["whitesmoke"] = {245, 245, 245},      ["yellow"] = {255, 255, 0},                 ["yellowgreen"] = {154, 205, 50}
};

--[[
    The list of the map_ids and names. (Taken from official locale_name.txt)
]]
MAP_NAME_TABLE = {
    -- TODO: Update with your maps, these are official indexes and names but may vary from server to server.

    [200] = {["id"] = "gm_guild_build",                  ["name"] = "GM Guild Map"}, -- Unofficial name, not present in the locale, but it's commonly known as GM Guild Map.
    [64]  = {["id"] = "map_a2",                          ["name"] = "Valley of Seungryong"},
    [61]  = {["id"] = "map_n_snowm_01",                  ["name"] = "Mount Sohan"},
    [355] = {["id"] = "metin2_12zi_stage",               ["name"] = "Zodiac Temple"},
    [372] = {["id"] = "metin2_guild_pve",                ["name"] = "Palace of the Dragon King"},
    [6]   = {["id"] = "metin2_guild_village_01",         ["name"] = "Miryang"},
    [26]  = {["id"] = "metin2_guild_village_02",         ["name"] = "Songpa"},
    [46]  = {["id"] = "metin2_guild_village_03",         ["name"] = "Daeyami"},
    [130] = {["id"] = "metin2_guild_war1",               ["name"] = "Guild War Area"},
    [131] = {["id"] = "metin2_guild_war2",               ["name"] = "Guild War Area"},
    [132] = {["id"] = "metin2_guild_war3",               ["name"] = "Guild War Area"},
    [133] = {["id"] = "metin2_guild_war4",               ["name"] = "Guild War Area"},
    [1]   = {["id"] = "metin2_map_a1",                   ["name"] = "Yongan Area"},
    [3]   = {["id"] = "metin2_map_a3",                   ["name"] = "Yayang Area"},
    [21]  = {["id"] = "metin2_map_b1",                   ["name"] = "Joan Area"},
    [23]  = {["id"] = "metin2_map_b3",                   ["name"] = "Bokjung Area"},
    [357] = {["id"] = "metin2_map_battlefied",           ["name"] = "Combat Zone"},
    [303] = {["id"] = "metin2_map_BayBlackSand",         ["name"] = "Nephrite Bay"},
    [371] = {["id"] = "metin2_map_boss_awaken_dawnmist", ["name"] = "RX: Enchanted Forest"},
    [369] = {["id"] = "metin2_map_boss_awaken_flame",    ["name"] = "RX: Red Dragon Fortress"},
    [368] = {["id"] = "metin2_map_boss_awaken_skipia",   ["name"] = "RX: Grotto of Exile"},
    [370] = {["id"] = "metin2_map_boss_awaken_snow",     ["name"] = "RX: Nemere's Watchtower"},
    [367] = {["id"] = "metin2_map_boss_crack_dawnmist",  ["name"] = "TR: Enchanted Forest"},
    [365] = {["id"] = "metin2_map_boss_crack_flame",     ["name"] = "TR: Red Dragon Fortress"},
    [364] = {["id"] = "metin2_map_boss_crack_skipia",    ["name"] = "TR: Grotto of Exile"},
    [366] = {["id"] = "metin2_map_boss_crack_snow",      ["name"] = "TR: Nemere's Watchtower"},
    [41]  = {["id"] = "metin2_map_c1",                   ["name"] = "Pyungmoo Area"},
    [43]  = {["id"] = "metin2_map_c3",                   ["name"] = "Bakra Area"},
    [301] = {["id"] = "Metin2_map_CapeDragonHead",       ["name"] = "Cape Dragon Fire"},
    [353] = {["id"] = "metin2_map_dawnmist_dungeon_01",  ["name"] = "Enchanted Forest"},
    [302] = {["id"] = "metin2_map_dawnmistwood",         ["name"] = "Gautama Cliff"},
    [358] = {["id"] = "metin2_map_defensewave",          ["name"] = "Ship Defence"},
    [359] = {["id"] = "metin2_map_defensewave_port",     ["name"] = "Harbour"},
    [216] = {["id"] = "metin2_map_devilsCatacomb",       ["name"] = "Devil's Catacomb"},
    [66]  = {["id"] = "metin2_map_deviltower1",          ["name"] = "Demon Tower"},
    [112] = {["id"] = "metin2_map_duel",                 ["name"] = "Training Fight Arena"},
    [91]  = {["id"] = "metin2_map_e1",                   ["name"] = "Colony - Shinsoo"},
    [92]  = {["id"] = "metin2_map_e1",                   ["name"] = "Colony - Chunjo"},
    [93]  = {["id"] = "metin2_map_e1",                   ["name"] = "Colony - Jinno"},
    [4]   = {["id"] = "metin2_map_guild_01",             ["name"] = "Jungrang"},
    [24]  = {["id"] = "metin2_map_guild_02",             ["name"] = "Waryong"},
    [44]  = {["id"] = "metin2_map_guild_03",             ["name"] = "Imha"},
    [363] = {["id"] = "metin2_map_labyrinth",            ["name"] = "Plateau of Illusions"},
    [65]  = {["id"] = "metin2_map_milgyo",               ["name"] = "Hwang Temple"},
    [361] = {["id"] = "metin2_map_miniboss_01",          ["name"] = "Blue Dungeon - Lvl 40-80"},
    [362] = {["id"] = "metin2_map_miniboss_02",          ["name"] = "Blue Dungeon - Lvl 81+"},
    [360] = {["id"] = "metin2_map_mists_of_island",      ["name"] = "Isle of Mist"},
    [5]   = {["id"] = "metin2_map_monkeydungeon",        ["name"] = "Hasun Dong - Shinsoo"},
    [25]  = {["id"] = "metin2_map_monkeydungeon",        ["name"] = "Hasun Dong - Chunjo"},
    [45]  = {["id"] = "metin2_map_monkeydungeon",        ["name"] = "Hasun Dong - Jinno"},
    [107] = {["id"] = "metin2_map_monkeydungeon",        ["name"] = "Hasun Dong"},
    [108] = {["id"] = "metin2_map_monkeydungeon_02",     ["name"] = "Jungsun Dong"},
    [109] = {["id"] = "metin2_map_monkeydungeon_03",     ["name"] = "Sangsun Dong"},
    [354] = {["id"] = "metin2_map_Mt_Th_dungeon_01",     ["name"] = "Temple of the Ochao"},
    [304] = {["id"] = "metin2_map_Mt_Thunder",           ["name"] = "Thunder Mountains"},
    [63]  = {["id"] = "metin2_map_n_desert_01",          ["name"] = "Yongbi Desert"},
    [62]  = {["id"] = "metin2_map_n_flame_01",           ["name"] = "Fireland"},
    [356] = {["id"] = "metin2_map_n_flame_dragon",       ["name"] = "Meley's Lair"},
    [351] = {["id"] = "metin2_map_n_flame_dungeon_01",   ["name"] = "Red Dragon Fortress"},
    [352] = {["id"] = "metin2_map_n_snow_dungeon_01",    ["name"] = "Nemere's Watchtower"},
    [201] = {["id"] = "metin2_map_pvp_arena",            ["name"] = "PvP Arena"}, -- Unofficial name, not present in the locale but should be obvious.
    [73]  = {["id"] = "metin2_map_skipia_dungeon_02",    ["name"] = "Grotto of Exile 2"},
    [208] = {["id"] = "metin2_map_skipia_dungeon_boss",  ["name"] = "Dragon's Temple"},
    [104] = {["id"] = "metin2_map_spiderdungeon",        ["name"] = "Spider Dungeon 1"},
    [71]  = {["id"] = "metin2_map_spiderdungeon_02",     ["name"] = "Spider Dungeon 2"},
    [217] = {["id"] = "metin2_map_spiderdungeon_03",     ["name"] = "Spider Dungeon 3"},
    [103] = {["id"] = "metin2_map_t1",                   ["name"] = "Guild War Area"},
    [105] = {["id"] = "metin2_map_t2",                   ["name"] = "Guild War Area"},
    [110] = {["id"] = "metin2_map_t3",                   ["name"] = "Guild War Area"},
    [111] = {["id"] = "metin2_map_t4",                   ["name"] = "Guild War Area"},
    [67]  = {["id"] = "metin2_map_trent",                ["name"] = "Ghost Forest"},
    [68]  = {["id"] = "metin2_map_trent02",              ["name"] = "Red Forest"},
    [81]  = {["id"] = "metin2_map_wedding_01",           ["name"] = "Wedding Map"},
    [70]  = {["id"] = "season1/metin2_map_nusluck01",             ["name"] = "Land of Giants"},
    [113] = {["id"] = "season1/metin2_map_oxevent",               ["name"] = "OX contest"},
    [114] = {["id"] = "season1/metin2_map_sungzi",                ["name"] = "Kingdom Battle"},
    [125] = {["id"] = "season1/metin2_map_sungzi_desert_01",      ["name"] = "Desert Land Kingdom Battle Arena"},
    [126] = {["id"] = "season1/metin2_map_sungzi_desert_hill_01", ["name"] = "Desert Land Kingdom Battle - Shinsoo"},
    [127] = {["id"] = "season1/metin2_map_sungzi_desert_hill_02", ["name"] = "Desert Land Kingdom Battle - Chunjo"},
    [128] = {["id"] = "season1/metin2_map_sungzi_desert_hill_03", ["name"] = "Desert Land Kingdom Battle - Jinno"},
    [118] = {["id"] = "season1/metin2_map_sungzi_flame_hill_01",  ["name"] = "Fireland Kingdom Battle - Shinsoo"},
    [119] = {["id"] = "season1/metin2_map_sungzi_flame_hill_02",  ["name"] = "Fireland Kingdom Battle - Chunjo"},
    [120] = {["id"] = "season1/metin2_map_sungzi_flame_hill_03",  ["name"] = "Fireland Kingdom Battle - Jinno"},
    [121] = {["id"] = "season1/metin2_map_sungzi_snow",           ["name"] = "Ice Land Kingdom Battle Arena"},
    [122] = {["id"] = "season1/metin2_map_sungzi_snow_pass_01",   ["name"] = "Ice Land Kingdom Battle - Shinsoo"},
    [123] = {["id"] = "season1/metin2_map_sungzi_snow_pass_02",   ["name"] = "Ice Land Kingdom Battle - Chunjo"},
    [124] = {["id"] = "season1/metin2_map_sungzi_snow_pass_03",   ["name"] = "Ice Land Kingdom Battle - Jinno"},
    [69]  = {["id"] = "season1/metin2_map_WL_01",                 ["name"] = "Snakefield"},
    [181] = {["id"] = "season2/metin2_map_empirewar01",           ["name"] = "Castle Battle - Shinsoo"},
    [182] = {["id"] = "season2/metin2_map_empirewar02",           ["name"] = "Castle Battle - Chunjo"},
    [183] = {["id"] = "season2/metin2_map_empirewar03",           ["name"] = "Castle Battle - Jinno"},
    [72]  = {["id"] = "season2/metin2_map_skipia_dungeon_01",     ["name"] = "Grotto of Exile"},
    [378] = {["id"] = "metin2_map_elemental_01",         ["name"] = "Elemental Realm"},
    [379] = {["id"] = "metin2_map_elemental_02",         ["name"] = "Elemental Realm"},
    [380] = {["id"] = "metin2_map_elemental_03",         ["name"] = "Elemental Realm"},
    [381] = {["id"] = "metin2_map_elemental_04",         ["name"] = "Elemental Realm"},
    [374] = {["id"] = "metin2_map_empirecastle",         ["name"] = "Abandoned Fortress"},
    [373] = {["id"] = "metin2_map_eastplain_01",         ["name"] = "Dong Gwang Plain"},
    [376] = {["id"] = "metin2_map_eastplain_02",         ["name"] = "Seo Gwang Wastelands"},
    [377] = {["id"] = "metin2_map_eastplain_03",         ["name"] = "Nam Gwang Chasm"},
    [382] = {["id"] = "metin2_map_maze_dungeon1",        ["name"] = "Gnoll Caves Level 1"},
    [383] = {["id"] = "metin2_map_maze_dungeon2",        ["name"] = "Gnoll Caves Level 2"},
    [384] = {["id"] = "metin2_map_maze_dungeon3",        ["name"] = "Gnoll Caves Level 3"},
    [386] = {["id"] = "metin2_map_smhdungeon_01",        ["name"] = "Entrance Hall"},
    [387] = {["id"] = "metin2_map_smhdungeon_02",        ["name"] = "Sung Mahi Tower"},
    [375] = {["id"] = "metin2_map_battleroyale",         ["name"] = "Battle Royale"},
    [392] = {["id"] = "metin2_map_privateshop",          ["name"] = "Bazaar"},
    [396] = {["id"] = "metin2_map_anglar_dungeon_01",    ["name"] = "Mysterious Dungeon"},
    [385] = {["id"] = "metin2_map_snakevalley",          ["name"] = "Yilad Pass"},
    [390] = {["id"] = "metin2_map_snake_temple_01",      ["name"] = "1st Level of the Serpent Temple"},
    [391] = {["id"] = "metin2_map_snake_temple_02",      ["name"] = "Serpent Temple"},
    [388] = {["id"] = "metin2_map_icecrystalcave",       ["name"] = "Northwind Canyon"},
    [389] = {["id"] = "metin2_map_whitdragonvalley",     ["name"] = "Soul Gorge"},
    [393] = {["id"] = "metin2_map_whitedragoncave_01",   ["name"] = "Northwind Shelter"},
    [394] = {["id"] = "metin2_map_whitedragoncave_02",   ["name"] = "Northwind Descent"},
    [395] = {["id"] = "metin2_map_whitedragoncave_boss", ["name"] = "Northwind Deeps"},
    [399] = {["id"] = "metin2_map_secretdungeon_01",     ["name"] = "Enigma Temple"},
    [400] = {["id"] = "metin2_map_otherworld_01",        ["name"] = "Salvation"},
    [401] = {["id"] = "metin2_map_otherworld_02",        ["name"] = "Otherworld"},
    [402] = {["id"] = "metin2_map_otherworld_03",        ["name"] = "Room of Trials"},
    [403] = {["id"] = "metin2_map_otherworld_04",        ["name"] = "Damnation"},

    -- [[Scrapped Maps]]

    -- Scrapped Chunjo Orc Valley
    --[0] = {["id"] = "map_b2",                                  ["name"] = "Valley of Imji"},
    -- Scrapped Jinno Orc Valley
    --[0] = {["id"] = "map_c2",                                  ["name"] = "Valley of Bangsan"},
    -- Scrapped Battlefield map
    --[0] = {["id"] = "metin2_map_bf",                           ["name"] = "Battlefield"},
    -- Scrapped Battlefield map
    --[0] = {["id"] = "metin2_map_bf_02",                        ["name"] = "Battlefield 2"},
    -- Scrapped Battlefield map
    --[0] = {["id"] = "metin2_map_bf_03",                        ["name"] = "Battlefield 3"},
    -- Scrapped Fireland Kingdom Battle Passage map
    --[0] = {["id"] = "metin2_map_sungzi_flame_pass01",          ["name"] = "Fireland Kingdom Battle - Shinsoo"},
    -- Scrapped Fireland Kingdom Battle Passage map
    --[0] = {["id"] = "metin2_map_sungzi_flame_pass02",          ["name"] = "Fireland Kingdom Battle - Chunjo"},
    -- Scrapped Fireland Kingdom Battle Passage map
    --[0] = {["id"] = "metin2_map_sungzi_flame_pass03",          ["name"] = "Fireland Kingdom Battle - Jinno"},
    -- Scrapped Temple Hwang-Themed Kingdom Battle Arena
    --[0] = {["id"] = "season1/metin2_map_sungzi_milgyo",        ["name"] = "Temple Hwang Kingdom Battle Arena"},
    -- Scrapped Temple Hwang-Themed Kingdom Passage map
    --[0] = {["id"] = "season1/metin2_map_sungzi_milgyo_pass01", ["name"] = "Temple Hwang Kingdom Battle - Shinsoo"},
    -- Scrapped Temple Hwang-Themed Kingdom Passage map
    --[0] = {["id"] = "season1/metin2_map_sungzi_milgyo_pass02", ["name"] = "Temple Hwang Kingdom Battle - Chunjo"},
    -- Scrapped Temple Hwang-Themed Kingdom Passage map
    --[0] = {["id"] = "season1/metin2_map_sungzi_milgyo_pass03", ["name"] = "Temple Hwang Kingdom Battle - Jinno"},
    -- Scrapped Castle Map
    --[0] = {["id"] = "season1/metin2_map_ew02",                 ["name"] = "Castle Battle"},
    -- Secondary Mount Sohan scrapped since Alpha
    --[0] = {["id"] = "season2/map_n_snowm_02",                  ["name"] = "Mount Sohan 2"},
    -- Secondary Temple Hwang scrapped since Alpha
    --[0] = {["id"] = "season2/metin2_map_milgyo_a",             ["name"] = "Temple Hwang 2"},
    -- Secondary Yongbi Desert scrapped since Alpha
    --[0] = {["id"] = "season2/metin2_map_n_desert_02",          ["name"] = "Yongbi Desert 2"},
    -- Secondary Fireland scrapped since Alpha
    --[0] = {["id"] = "season2/metin2_map_n_flame_02",           ["name"] = "Fireland 2"},
    -- Secondary Valley of Seungryong scrapped since Alpha
    --[0] = {["id"] = "season2/metin2_map_a2_1",                 ["name"] = "Valley of Seungryong 2"},
    -- Secondary Ghost Forest scrapped since Alpha
    --[0] = {["id"] = "season2/metin2_map_trent_a",              ["name"] = "Ghost Forest 2"},
    -- Secondary Red Forest scrapped since Alpha
    --[0] = {["id"] = "season2/metin2_map_trent02_a",            ["name"] = "Red Forest 2"},
};
