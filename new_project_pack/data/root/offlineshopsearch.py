#
# Pazar Arama (ShopSearch) penceresi - bagimsiz modul (kucuk harf dosya adi).
# (encoding bildirimi YOK: dosya saf ASCII; client gomulu Python'u cp1254 codec'ini tanimaz.)
# Kaynak: mt2009 ikarus offlineshopsearch.py + shopsearchwindow.py.
# Kategori sabitleri sunucu common/length.h enum'u ile BIREBIR AYNI.
# interfaceModule 'import offlineshopsearch' ile yukler.
#
import shop
import item
import constInfo
import ui
import wndMgr
import player
import chat
import app
import localeInfo
from _weakref import proxy

# Pencere ici metinler (locale bagimliligi olmamasi icin dogrudan tanimli)
TXT_NO_CATEGORY = localeInfo.SHOP_SEARCH_NO_CATEGORY
TXT_CLEAR_INFO  = localeInfo.SHOP_SEARCH_CLEAR_INFO

# uiscript/shopsearchwindow.py ItemSlot grid'i ile ayni: x_count(6) * y_count(10)
ITEM_SLOT_COUNT = 6 * 10
GRID_COLS = 6
# Item ikonlari 1-3 hucre yuksekliginde (zirh 2, silah 3): yerlestirme hucre-doluluk
# hesabiyla yapilir ki ikonlar ust uste binmesin. Son satir (satir 9) sayfa
# kontrollerine ayrilmistir; yerlestirme ilk 9 satira yapilir, tasan itemler
# sonraki sayfaya gider.
GRID_PACK_ROWS = 9

# Ayni anda secilebilecek azami item sayisi (server/client packet SHOP_SEARCH_SELECT_MAX ile ayni)
SHOP_SEARCH_SELECT_MAX = 30

SHOP_CATEGORY_MAX_SUB = 20

SHOP_SEARCH_CATEGORY_BOOKS			= 0
SHOP_SEARCH_CATEGORY_REFINE			= 1
SHOP_SEARCH_CATEGORY_SOULSTONE		= 2
SHOP_SEARCH_CATEGORY_HERBALISM		= 3
SHOP_SEARCH_CATEGORY_FISHING		= 4
SHOP_SEARCH_CATEGORY_HORSE			= 5
SHOP_SEARCH_CATEGORY_SPECIAL		= 6
SHOP_SEARCH_CATEGORY_MINING			= 7
SHOP_SEARCH_CATEGORY_POLYMORPH		= 8
SHOP_SEARCH_CATEGORY_ARMOR			= 9
SHOP_SEARCH_CATEGORY_ARMOR_ATTR		= 10
SHOP_SEARCH_CATEGORY_WEAPON			= 11
SHOP_SEARCH_CATEGORY_WEAPON_ATTR	= 12
SHOP_SEARCH_CATEGORY_JEWELRY		= 13
SHOP_SEARCH_CATEGORY_JEWELRY_ATTR	= 14

SHOP_SEARCH_SUB_WARRIOR_0	= 0
SHOP_SEARCH_SUB_WARRIOR_1	= 1
SHOP_SEARCH_SUB_ASSASSIN_0	= 2
SHOP_SEARCH_SUB_ASSASSIN_1	= 3
SHOP_SEARCH_SUB_SURA_0		= 4
SHOP_SEARCH_SUB_SURA_1		= 5
SHOP_SEARCH_SUB_SHAMAN_0	= 6
SHOP_SEARCH_SUB_SHAMAN_1	= 7
SHOP_SEARCH_SUB_PASSIVE_SKILL	= 8

SHOP_SEARCH_SUB_REFINE_M1		= 0
SHOP_SEARCH_SUB_REFINE_OATH		= 1
SHOP_SEARCH_SUB_REFINE_M2		= 2
SHOP_SEARCH_SUB_REFINE_ORC		= 3
SHOP_SEARCH_SUB_REFINE_DESERT1	= 4
SHOP_SEARCH_SUB_REFINE_DESERT2	= 5
SHOP_SEARCH_SUB_REFINE_SNOW		= 6
SHOP_SEARCH_SUB_REFINE_HWANG	= 7
SHOP_SEARCH_SUB_REFINE_END		= 8
SHOP_SEARCH_SUB_REFINE_SPECIAL	= 9
SHOP_SEARCH_SUB_REFINE_PEARL	= 10

SHOP_SEARCH_SUB_SOULSTONE_0	= 0
SHOP_SEARCH_SUB_SOULSTONE_1	= 1
SHOP_SEARCH_SUB_SOULSTONE_2	= 2
SHOP_SEARCH_SUB_SOULSTONE_3	= 3
SHOP_SEARCH_SUB_SOULSTONE_4	= 4

SHOP_SEARCH_SUB_HERB_PRIMARY			= 0
SHOP_SEARCH_SUB_HERB_SPECIAL			= 1
SHOP_SEARCH_SUB_HERB_WATER_OFFENSIVE	= 2
SHOP_SEARCH_SUB_HERB_WATER_DEFENSIVE	= 3
SHOP_SEARCH_SUB_HERB_WATER_POWER		= 4
SHOP_SEARCH_SUB_HERB_JUICE_OFFENSIVE	= 5
SHOP_SEARCH_SUB_HERB_JUICE_DEFENSIVE	= 6
SHOP_SEARCH_SUB_HERB_JUICE_POWER		= 7
SHOP_SEARCH_SUB_HERB_DEW_OFFENSIVE		= 8
SHOP_SEARCH_SUB_HERB_DEW_DEFENSIVE		= 9
SHOP_SEARCH_SUB_HERB_DEW_POWER			= 10
SHOP_SEARCH_SUB_HERB_OTHER_POTION		= 11
SHOP_SEARCH_SUB_HERB_AUTOPOTION			= 12
SHOP_SEARCH_SUB_HERB_RECIPE_OFFENSIVE	= 13
SHOP_SEARCH_SUB_HERB_RECIPE_DEFENSIVE	= 14
SHOP_SEARCH_SUB_HERB_RECIPE_POWER		= 15
SHOP_SEARCH_SUB_HERB_RECIPE_OTHER		= 16

SHOP_SEARCH_SUB_FISHING_FISH		= 0
SHOP_SEARCH_SUB_FISHING_FISH_COOK	= 1
SHOP_SEARCH_SUB_FISHING_FISH_OTHER	= 2

SHOP_SEARCH_SUB_SPECIAL_REFINE			= 0
SHOP_SEARCH_SUB_SPECIAL_TOITEM			= 1
SHOP_SEARCH_SUB_SPECIAL_CHARACTER		= 2
SHOP_SEARCH_SUB_SPECIAL_OTHER			= 3
SHOP_SEARCH_SUB_SPECIAL_DRAGON_VOUCHER	= 4
SHOP_SEARCH_SUB_SPECIAL_QUEST			= 5
SHOP_SEARCH_SUB_SPECIAL_LOOTBOX			= 6

SHOP_SEARCH_SUB_MINING_ORE	= 0
SHOP_SEARCH_SUB_MINING_MELT	= 1

SHOP_SEARCH_SUB_ARMOR_BODY		= 0
SHOP_SEARCH_SUB_ARMOR_SHIELD	= 1
SHOP_SEARCH_SUB_ARMOR_HEAD		= 2

SHOP_SEARCH_SUB_WEAPON_ONEHAND	= 0
SHOP_SEARCH_SUB_WEAPON_TWOHAND	= 1
SHOP_SEARCH_SUB_WEAPON_DAGGER	= 2
SHOP_SEARCH_SUB_WEAPON_BOW		= 3
SHOP_SEARCH_SUB_WEAPON_BELL		= 4
SHOP_SEARCH_SUB_WEAPON_FAN		= 5

SHOP_SEARCH_SUB_JEWELRY_EAR		= 0
SHOP_SEARCH_SUB_JEWELRY_NECK	= 1
SHOP_SEARCH_SUB_JEWELRY_WRIST	= 2
SHOP_SEARCH_SUB_JEWELRY_BOOTS	= 3

SHOP_SEARCH_SUB_HORSE_LEARN	= 0
SHOP_SEARCH_SUB_HORSE_OTHER	= 1

# --- Giyilebilir (Zirh/Silah/Taki) sinif-grup alt-kategorileri --------------------
# "Bonuslu Ara" bu kategorilerden kaldirildi; yerine sinif/grup + arti (+1..+9)
# secimi ve vnum grid'i geldi (kullanici istegi, 2026-08-02). searchIndex =
# kategori*20 + alt (10..14). Arti seviyesi shop.SendSearchItem'in 2. argumaniyla
# (paketin zaten var olan socket0 alani) sunucuya gider -> wire DEGISMEDI,
# client exe rebuild gerekmez. Server karsiligi: ENABLE_SHOP_SEARCH_CLASS_SUBCAT.
SHOP_SEARCH_SUB_GRID_WARRIOR	= 10
SHOP_SEARCH_SUB_GRID_ASSASSIN	= 11
SHOP_SEARCH_SUB_GRID_SURA		= 12
SHOP_SEARCH_SUB_GRID_SHAMAN		= 13
SHOP_SEARCH_SUB_GRID_SHIELD		= 14
SHOP_SEARCH_SUB_GRID_JEW_EAR	= 10
SHOP_SEARCH_SUB_GRID_JEW_NECK	= 11
SHOP_SEARCH_SUB_GRID_JEW_WRIST	= 12
SHOP_SEARCH_SUB_GRID_JEW_BOOTS	= 13
# Silah gruplari tur bazli (kullanici istegi 2026-08-02): sinif on-adi sadece etiket
SHOP_SEARCH_SUB_GRID_WPN_ONEHAND	= 10
SHOP_SEARCH_SUB_GRID_WPN_TWOHAND	= 11
SHOP_SEARCH_SUB_GRID_WPN_DAGGER		= 12
SHOP_SEARCH_SUB_GRID_WPN_BOW		= 13
SHOP_SEARCH_SUB_GRID_WPN_BELL		= 14
SHOP_SEARCH_SUB_GRID_WPN_FAN		= 15

# Secilebilir arti seviyeleri (kullanici istegi: +1..+9)
SHOP_SEARCH_PLUS_CHOICES = [1, 2, 3, 4, 5, 6, 7, 8, 9]

# DIKKAT: getattr(localeInfo, ...) fallback'i BU FORK'TA CALISMAZ: system.py
# LocaleInfoWrapper.__getattr__ eksik anahtarda syserr'e hata yazip anahtarin
# ADINI dondurur (AttributeError yukselmez) -> default hic devreye girmez.
# Bu yuzden duz ASCII literal kullanilir (yeni locale anahtari gerektirmez).
TXT_SELECT_PLUS = "Lutfen arti seviyesi secin (+1 / +9)."

# Aile tablolari: (taban_vnum, azami_arti). Uretec: _plan_shopsearch_subcat/gen_wearable_filters.py
# DIKKAT: server shop_manager.cpp PrepareShopSearchFilters tablolari ile BIREBIR ayni tutulmali.
SHOP_SEARCH_GRID_FAMILIES = {
	# Zirh > Savasci (govde) (searchIndex = 9*20+10 = 190)
	(SHOP_SEARCH_CATEGORY_ARMOR, 10): [
		(11200, 9), (11210, 9), (11220, 9), (11230, 9), (11240, 9), (11250, 9), (11260, 9), (11270, 9),
		(11280, 9), (11290, 9),
	],
	# Zirh > Ninja (govde) (searchIndex = 9*20+11 = 191)
	(SHOP_SEARCH_CATEGORY_ARMOR, 11): [
		(11400, 9), (11410, 9), (11420, 9), (11430, 9), (11440, 9), (11450, 9), (11460, 9), (11470, 9),
		(11480, 9), (11490, 9),
	],
	# Zirh > Sura (govde) (searchIndex = 9*20+12 = 192)
	(SHOP_SEARCH_CATEGORY_ARMOR, 12): [
		(11600, 9), (11610, 9), (11620, 9), (11630, 9), (11640, 9), (11650, 9), (11660, 9), (11670, 9),
		(11680, 9), (11690, 9),
	],
	# Zirh > Saman (govde) (searchIndex = 9*20+13 = 193)
	(SHOP_SEARCH_CATEGORY_ARMOR, 13): [
		(11800, 9), (11810, 9), (11820, 9), (11830, 9), (11840, 9), (11850, 9), (11860, 9), (11870, 9),
		(11880, 9), (11890, 9),
	],
	# Zirh > Kalkan (searchIndex = 9*20+14 = 194)
	(SHOP_SEARCH_CATEGORY_ARMOR, 14): [
		(13000, 9), (13020, 9), (13040, 9), (13060, 9), (13080, 9), (13100, 9), (13120, 9),
	],
	# Silah > Savasci Tek El (searchIndex = 11*20+10 = 230)
	(SHOP_SEARCH_CATEGORY_WEAPON, 10): [
		(10, 9), (20, 9), (30, 9), (40, 9), (50, 9), (60, 9), (70, 9), (80, 9), (90, 9), (100, 9),
		(110, 9), (120, 9), (130, 9), (140, 9), (150, 9), (160, 9), (170, 9), (240, 9), (250, 9),
		(290, 9),
	],
	# Silah > Savasci Cift El (searchIndex = 11*20+11 = 231)
	(SHOP_SEARCH_CATEGORY_WEAPON, 11): [
		(3000, 9), (3010, 9), (3020, 9), (3030, 9), (3040, 9), (3050, 9), (3060, 9), (3070, 9),
		(3080, 9), (3090, 9), (3100, 9), (3110, 9), (3120, 9), (3130, 9), (3140, 9), (3150, 9),
		(3210, 9),
	],
	# Silah > Ninja Hancer (searchIndex = 11*20+12 = 232)
	(SHOP_SEARCH_CATEGORY_WEAPON, 12): [
		(1000, 9), (1010, 9), (1020, 9), (1030, 9), (1040, 9), (1050, 9), (1060, 9), (1070, 9),
		(1080, 9), (1090, 9), (1100, 9), (1110, 9), (1120, 9), (1170, 9),
	],
	# Silah > Ninja Okcu (searchIndex = 11*20+13 = 233)
	(SHOP_SEARCH_CATEGORY_WEAPON, 13): [
		(2000, 9), (2010, 9), (2020, 9), (2030, 9), (2040, 9), (2050, 9), (2060, 9), (2070, 9),
		(2080, 9), (2090, 9), (2100, 9), (2110, 9), (2120, 9), (2130, 9), (2140, 9), (2150, 9),
		(2180, 9),
	],
	# Silah > Saman Can (searchIndex = 11*20+14 = 234)
	(SHOP_SEARCH_CATEGORY_WEAPON, 14): [
		(5000, 9), (5010, 9), (5020, 9), (5030, 9), (5040, 9), (5050, 9), (5060, 9), (5070, 9),
		(5080, 9), (5090, 9), (5100, 9), (5110, 9),
	],
	# Silah > Saman Yelpaze (searchIndex = 11*20+15 = 235)
	(SHOP_SEARCH_CATEGORY_WEAPON, 15): [
		(7000, 9), (7010, 9), (7020, 9), (7030, 9), (7040, 9), (7050, 9), (7060, 9), (7070, 9),
		(7080, 9), (7090, 9), (7100, 9), (7110, 9), (7120, 9), (7130, 9), (7140, 9), (7150, 9),
		(7160, 9),
	],
	# Taki > Kupe (searchIndex = 13*20+10 = 270)
	(SHOP_SEARCH_CATEGORY_JEWELRY, 10): [
		(17000, 9), (17020, 9), (17040, 9), (17060, 9), (17080, 9), (17100, 9), (17120, 9), (17140, 9),
		(17160, 9), (17180, 9), (17200, 9), (17220, 9),
	],
	# Taki > Kolye (searchIndex = 13*20+11 = 271)
	(SHOP_SEARCH_CATEGORY_JEWELRY, 11): [
		(16000, 9), (16020, 9), (16040, 9), (16060, 9), (16080, 9), (16100, 9), (16120, 9), (16140, 9),
		(16160, 9), (16180, 9), (16200, 9), (16220, 9),
	],
	# Taki > Bileklik (searchIndex = 13*20+12 = 272)
	(SHOP_SEARCH_CATEGORY_JEWELRY, 12): [
		(14000, 9), (14020, 9), (14040, 9), (14060, 9), (14080, 9), (14100, 9), (14120, 9), (14140, 9),
		(14160, 9), (14180, 9), (14200, 9), (14220, 9),
	],
	# Taki > Ayakkabi (searchIndex = 13*20+13 = 273)
	(SHOP_SEARCH_CATEGORY_JEWELRY, 13): [
		(15000, 9), (15020, 9), (15040, 9), (15060, 9), (15080, 9), (15100, 9), (15120, 9), (15140, 9),
		(15160, 9), (15180, 9), (15200, 9), (15220, 9),
	],
}

def _shopsearch_expand_families(famList):
	# (taban, azamiArti) ailelerini (vnum, socket0=0) cift listesine acar
	out = []
	for fam in famList:
		p = 0
		while p <= fam[1]:
			out.append((fam[0] + p, 0))
			p += 1
	return out

SHOP_SEARCH_FILTERS = {
	SHOP_SEARCH_CATEGORY_BOOKS: {
		"name": localeInfo.SHOP_SEARCH_CAT_BOOKS,
		"sub": {
			SHOP_SEARCH_SUB_WARRIOR_0: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_WARRIOR_0,
				"itemList": [
					(50300, 1), (50300, 2), (50300, 3), (50300, 4), (50300, 5),
					# (50401, 0), (50402, 0), (50403, 0), (50404, 0), (50405, 0),
					# (70037, 1), (70037, 2), (70037, 3), (70037, 4), (70037, 5),
				]
			},
			SHOP_SEARCH_SUB_WARRIOR_1: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_WARRIOR_1,
				"itemList": [
					(50300, 16), (50300, 17), (50300, 18), (50300, 19), (50300, 20),
					# (50416, 0), (50417, 0), (50418, 0), (50419, 0), (50420, 0),
					# (70037, 16), (70037, 17), (70037, 18), (70037, 19), (70037, 20),
				]
			},
			SHOP_SEARCH_SUB_ASSASSIN_0: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_ASSASSIN_0,
				"itemList": [
					(50300, 31), (50300, 32), (50300, 33), (50300, 34), (50300, 35),
					# (50431, 0), (50432, 0), (50433, 0), (50434, 0), (50435, 0),
					# (70037, 31), (70037, 32), (70037, 33), (70037, 34), (70037, 35),
				]
			},
			SHOP_SEARCH_SUB_ASSASSIN_1: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_ASSASSIN_1,
				"itemList": [
					(50300, 46), (50300, 47), (50300, 48), (50300, 49), (50300, 50),
					# (50446, 0), (50447, 0), (50448, 0), (50449, 0), (50450, 0),
					# (70037, 46), (70037, 47), (70037, 48), (70037, 49), (70037, 50),
				]
			},
			SHOP_SEARCH_SUB_SURA_0: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SURA_0,
				"itemList": [
					(50300, 61), (50300, 62), (50300, 63), (50300, 64), (50300, 65), (50300, 66),
					# (50461, 0), (50462, 0), (50463, 0), (50464, 0), (50465, 0), (50466, 0),
					# (70037, 61), (70037, 62), (70037, 63), (70037, 64), (70037, 65), (70037, 66),
				]
			},
			SHOP_SEARCH_SUB_SURA_1: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SURA_1,
				"itemList": [
					(50300, 76), (50300, 77), (50300, 78), (50300, 79), (50300, 80), (50300, 81),
					# (50476, 0), (50477, 0), (50478, 0), (50479, 0), (50480, 0), (50481, 0),
					# (70037, 76), (70037, 77), (70037, 78), (70037, 79), (70037, 80), (70037, 81),
				]
			},
			SHOP_SEARCH_SUB_SHAMAN_0: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SHAMAN_0,
				"itemList": [
					(50300, 91), (50300, 92), (50300, 93), (50300, 94), (50300, 95), (50300, 96),
					# (50491, 0), (50492, 0), (50493, 0), (50494, 0), (50495, 0), (50496, 0),
					# (70037, 91), (70037, 92), (70037, 93), (70037, 94), (70037, 95), (70037, 96),
				]
			},
			SHOP_SEARCH_SUB_SHAMAN_1: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SHAMAN_1,
				"itemList": [
					(50300, 106), (50300, 107), (50300, 108), (50300, 109), (50300, 110), (50300, 111),
					# (50506, 0), (50507, 0), (50508, 0), (50509, 0), (50510, 0), (50511, 0),
					# (70037, 106), (70037, 107), (70037, 108), (70037, 109), (70037, 110), (70037, 111),
				]
			},
			SHOP_SEARCH_SUB_PASSIVE_SKILL: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_PASSIVE_SKILL,
				"itemList": [
					(50600, 0), (50301, 0), (50302, 0), (50303, 0), (50304, 0), (50305, 0), (50306, 0),
					(50311, 0), (50312, 0), (50313, 0), (50314, 0), (50315, 0), (50316, 0),
				]
			},
		},
	},

	SHOP_SEARCH_CATEGORY_REFINE: {
		"name": localeInfo.SHOP_SEARCH_CAT_REFINE,
		"sub_sort": [
		SHOP_SEARCH_SUB_REFINE_M1, SHOP_SEARCH_SUB_REFINE_M2, SHOP_SEARCH_SUB_REFINE_OATH,
		SHOP_SEARCH_SUB_REFINE_ORC, SHOP_SEARCH_SUB_REFINE_DESERT1, SHOP_SEARCH_SUB_REFINE_SNOW,
		SHOP_SEARCH_SUB_REFINE_SPECIAL, SHOP_SEARCH_SUB_REFINE_HWANG, SHOP_SEARCH_SUB_REFINE_DESERT2,
		SHOP_SEARCH_SUB_REFINE_END, SHOP_SEARCH_SUB_REFINE_PEARL,
		],
		"sub": {
			SHOP_SEARCH_SUB_REFINE_M1: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_M1,
				"itemList": [
					(30003, 0), (30004, 0), (30010, 0), (30023, 0), (30027, 0), (30028, 0), (30037, 0), (30038, 0), (30053, 0),
					(30069, 0), (30070, 0), (30071, 0), (30072, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_M2: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_M2,
				"itemList": [
					(30005, 0), (30021, 0), (30030, 0), (30032, 0), (30033, 0), (30041, 0), (30052, 0), (30074, 0), (30075, 0),
					(30092, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_OATH: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_OATH,
				"itemList": [
					(30011, 0), (30017, 0), (30018, 0), (30031, 0), (30034, 0), (30035, 0), (30073, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_ORC: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_ORC,
				"itemList": [
					(30007, 0), (30076, 0), (30006, 0), (30077, 0), (30008, 0), (30078, 0), (30051, 0), (30079, 0),
					(30047, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_DESERT1: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_DESERT1,
				"itemList": [
					(30022, 0), (30082, 0), (30025, 0), (30045, 0), (30046, 0), (30081, 0), (30055, 0), (30056, 0), (30057, 0), (30058, 0),
					(30059, 0), (30067, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_SNOW: { #Sohan
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_SNOW,
				"itemList": [
					(30009, 0), (30014, 0), (30039, 0), (30048, 0), (30049, 0), (30050, 0), (30083, 0), (30085, 0), (30088, 0),
					(30089, 0), (30090, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_SPECIAL: { #doyum
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_SPECIAL,
				"itemList": [
					(30019, 0), (30042, 0), (30091, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_HWANG: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_HWANG,
				"itemList": [
					(30040, 0), (30060, 0), (30061, 0), (30080, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_DESERT2: { #Seytan Kulesi
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_DESERT2,
				"itemList": [
					 (30015, 0), (30087, 0), (30016, 0), (30086, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_END: { #Surgun magara
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_END,
				"itemList": [
					(30192, 0), (30193, 0), (30194, 0), (30195, 0), (30196, 0), (30197, 0), (30198, 0), (30199, 0), (71123, 0), (71129, 0),
				]
			},
			SHOP_SEARCH_SUB_REFINE_PEARL: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_REFINE_PEARL,
				"itemList": [
					(27992, 0), (27993, 0), (27994, 0),
				]
			},
		},
	},

	SHOP_SEARCH_CATEGORY_SOULSTONE: {
		"name": localeInfo.SHOP_SEARCH_CAT_SOULSTONE,
		"sub": {
			SHOP_SEARCH_SUB_SOULSTONE_0: {
				"name": "+0",
				"itemList": [
					(28030, 0), (28031, 0), (28032, 0), (28033, 0), (28034, 0), (28035, 0), (28036, 0), (28037, 0), (28038, 0),
					(28039, 0), (28040, 0), (28041, 0), (28042, 0), (28043, 0),
				]
			},
			SHOP_SEARCH_SUB_SOULSTONE_1: {
				"name": "+1",
				"itemList": [
					(28130, 0), (28131, 0), (28132, 0), (28133, 0), (28134, 0), (28135, 0), (28136, 0), (28137, 0),
					(28138, 0), (28139, 0), (28140, 0), (28141, 0), (28142, 0), (28143, 0),
				]
			},
			SHOP_SEARCH_SUB_SOULSTONE_2: {
				"name": "+2",
				"itemList": [
					(28230, 0), (28231, 0), (28232, 0), (28233, 0), (28234, 0), (28235, 0), (28236, 0), (28237, 0),
					(28238, 0), (28239, 0), (28240, 0), (28241, 0), (28242, 0), (28243, 0),
				]
			},
			SHOP_SEARCH_SUB_SOULSTONE_3: {
				"name": "+3",
				"itemList": [
					(28330, 0), (28331, 0), (28332, 0), (28333, 0), (28334, 0), (28335, 0), (28336, 0), (28337, 0),
					(28338, 0), (28339, 0), (28340, 0), (28341, 0), (28342, 0), (28343, 0),
				]
			},
			SHOP_SEARCH_SUB_SOULSTONE_4: {
				"name": "+4",
				"itemList": [
					(28430, 0), (28431, 0), (28432, 0), (28433, 0), (28434, 0), (28435, 0), (28436, 0), (28437, 0),
					(28438, 0), (28439, 0), (28440, 0), (28441, 0), (28442, 0), (28443, 0),
				]
			},
		},
	},

	SHOP_SEARCH_CATEGORY_HERBALISM: {
		"name": localeInfo.SHOP_SEARCH_CAT_HERBALISM,
		"sub_sort": [
		SHOP_SEARCH_SUB_HERB_PRIMARY, SHOP_SEARCH_SUB_HERB_WATER_POWER, SHOP_SEARCH_SUB_HERB_JUICE_POWER,
		SHOP_SEARCH_SUB_HERB_DEW_POWER, SHOP_SEARCH_SUB_HERB_OTHER_POTION, SHOP_SEARCH_SUB_HERB_AUTOPOTION,
		SHOP_SEARCH_SUB_HERB_RECIPE_OFFENSIVE,
		],
		"sub": {
			SHOP_SEARCH_SUB_HERB_PRIMARY: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_PRIMARY,
				"itemList": [
					(50721, 0), (50722, 0), (50723, 0), (50724, 0), (50725, 0), (50726, 0), (50727, 0), (50728, 0),
				]
			},
			# SHOP_SEARCH_SUB_HERB_SPECIAL: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_SPECIAL,
				# "itemList": [
					# (50731, 0), (50732, 0), (50733, 0), (50734, 0), (50735, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_WATER_OFFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_WATER_OFFENSIVE,
				# "itemList": [
					# (51720, 0), (51725, 0), (51740, 0), (51745, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_JUICE_OFFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_JUICE_OFFENSIVE,
				# "itemList": [
					# (51721, 0), (51726, 0), (51741, 0), (51746, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_DEW_OFFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_DEW_OFFENSIVE,
				# "itemList": [
					# (51722, 0), (51727, 0), (51742, 0), (51747, 0), (51748, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_WATER_DEFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_WATER_DEFENSIVE,
				# "itemList": [
					# (51730, 0), (51750, 0), (51800, 0), (51805, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_JUICE_DEFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_JUICE_DEFENSIVE,
				# "itemList": [
					# (51731, 0), (51751, 0), (51801, 0), (51806, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_DEW_DEFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_DEW_DEFENSIVE,
				# "itemList": [
					# (51732, 0), (51752, 0), (51753, 0), (51802, 0), (51807, 0),
				# ]
			# },
			SHOP_SEARCH_SUB_HERB_WATER_POWER: { #markalar
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_WATER_POWER,
				"itemList": [
					(71027, 0), (71028, 0), (71029, 0), (71030, 0), (71044, 0), (71045, 0),
				]
			},
			SHOP_SEARCH_SUB_HERB_JUICE_POWER: { #sebnemler
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_JUICE_POWER,
				"itemList": [
					(50821, 0), (50822, 0), (50823, 0), (50824, 0), (50825, 0), (50826, 0), 
				]
			},
			SHOP_SEARCH_SUB_HERB_DEW_POWER: { #sular
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_DEW_POWER,
				"itemList": [
					(50801, 0), (50802, 0), (50803, 0), (50804, 0), (50813, 0), (50814, 0), (50815, 0),
					(50816, 0), (50817, 0), (50818, 0), (50819, 0), (50820, 0),
				]
			},
			SHOP_SEARCH_SUB_HERB_RECIPE_OFFENSIVE: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_RECIPE_OFFENSIVE,
				"itemList": [
					(27003, 0), (27006, 0), (27102, 0), (27105, 0),
				]
			},
			SHOP_SEARCH_SUB_HERB_AUTOPOTION: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_AUTOPOTION,
				"itemList": [
					(72723, 0), (72724, 0), (72725, 0), (72727, 0), (72728, 0), (72729, 0),
				]
			},
			# SHOP_SEARCH_SUB_HERB_RECIPE_DEFENSIVE: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_RECIPE_DEFENSIVE,
				# "itemList": [
					# (50919, 0), (50942, 0), (50943, 0), (50923, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_RECIPE_POWER: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_RECIPE_POWER,
				# "itemList": [
					# (50911, 0), (50912, 0), (50913, 0), (50914, 0), (50915, 0), (50916, 0),
					# (50920, 0), (50924, 0), (50925, 0), (50926, 0), (50927, 0), (50929, 0),
				# ]
			# },
			# SHOP_SEARCH_SUB_HERB_RECIPE_OTHER: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HERB_RECIPE_OTHER,
				# "itemList": [
					# (50930, 0), (50932, 0), (50933, 0), (50934, 0), (50935, 0),
				# ]
			# },
		},
	},

	SHOP_SEARCH_CATEGORY_FISHING: {
		"name": localeInfo.SHOP_SEARCH_CAT_FISHING,
		"sub_sort": [
		SHOP_SEARCH_SUB_FISHING_FISH,SHOP_SEARCH_SUB_FISHING_FISH_OTHER,
		],
		"sub": {
			SHOP_SEARCH_SUB_FISHING_FISH: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_FISHING_FISH,
				"itemList": [
					(27803, 0),
				]
			},
			# SHOP_SEARCH_SUB_FISHING_FISH_COOK: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_FISHING_FISH_COOK,
				# "itemList": [
					# (27866, 0), (27868, 0), (27869, 0), (27870, 0), (27871, 0), (27872, 0), (27873, 0), (27875, 0),
					# (27879, 0), (27880, 0), (27881, 0), (27882, 0), (27883, 0),
				# ]
			# },
			SHOP_SEARCH_SUB_FISHING_FISH_OTHER: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_FISHING_FISH_OTHER,
				"itemList": [
					(27799, 0), (27987, 0), (27991, 0),
				]
			},
		},
	},

	SHOP_SEARCH_CATEGORY_MINING: {
		"name": localeInfo.SHOP_SEARCH_CAT_MINING,
		"sub": {
			SHOP_SEARCH_SUB_MINING_ORE: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_MINING_ORE,
				"itemList": [
					(50601, 0), (50603, 0), (50604, 0), (50605, 0), (50606, 0), (50607, 0), (50608, 0), (50609, 0), (50610, 0),
					(50611, 0), (50612, 0), (50613, 0),
				]
			},
			SHOP_SEARCH_SUB_MINING_MELT: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_MINING_MELT,
				"itemList": [
					(50621, 0), (50623, 0), (50624, 0), (50625, 0), (50626, 0), (50627, 0),
					(50628, 0), (50629, 0), (50630, 0), (50631, 0), (50632, 0), (50633, 0),
				]
			},
		},
	},

	SHOP_SEARCH_CATEGORY_HORSE: {
		"name": localeInfo.SHOP_SEARCH_CAT_HORSE,
		"sub": {
			SHOP_SEARCH_SUB_HORSE_LEARN: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_HORSE_LEARN,
				"itemList": [
					(50050, 0),
				]
			},
			# SHOP_SEARCH_SUB_HORSE_OTHER: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_HORSE_OTHER,
				# "itemList": [
					# (50054, 0), (50055, 0), (50056, 0), (50083, 0), (30378, 0),
				# ]
			# },
		},
	},

	SHOP_SEARCH_CATEGORY_POLYMORPH: {
		"name": localeInfo.SHOP_SEARCH_CAT_POLYMORPH,
		"itemList": [
			(70104, 0),
		]
	},

	SHOP_SEARCH_CATEGORY_SPECIAL: {
		"name": localeInfo.SHOP_SEARCH_CAT_SPECIAL,
		"sub": {
			SHOP_SEARCH_SUB_SPECIAL_REFINE: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SPECIAL_REFINE,
				"itemList": [
					(25040, 0), (70039, 0),
				]
			},
			SHOP_SEARCH_SUB_SPECIAL_TOITEM: { #craft malzemeleri
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SPECIAL_TOITEM,
				"itemList": [
					(31035, 0), (30602, 0), (30603, 0), (30604, 0), (30610, 0), (30156, 0), (27991, 0), (51001, 0),
				]
			},
			SHOP_SEARCH_SUB_SPECIAL_CHARACTER: { #efsunlar
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SPECIAL_CHARACTER,
				"itemList": [
					(71084, 0), (71085, 0), (70024, 0), (50904, 0), (50903, 0),
				]
			},
			SHOP_SEARCH_SUB_SPECIAL_OTHER: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SPECIAL_OTHER,
				"itemList": [
					(50513, 0), (71001, 0), (71094, 0), (70102, 0), (70043, 0), (70005, 0),
				]
			},
			SHOP_SEARCH_SUB_SPECIAL_DRAGON_VOUCHER: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_SPECIAL_DRAGON_VOUCHER,
				"itemList": [
					(80014, 0), (80015, 0), (80016, 0), (30403, 0), (30404, 0),
				]
			},
			# SHOP_SEARCH_SUB_SPECIAL_LOOTBOX: {
				# "name": localeInfo.SHOP_SEARCH_SUBCAT_SPECIAL_LOOTBOX,
				# "itemList": [
					# (50011, 0), (50096, 0), (50037, 0), (50024, 0), (50025, 0),
					# (50070, 0), (50071, 0), (50073, 0), (50076, 0), (50077, 0),
					# (50078, 0), (50079, 0), (50081, 0), (50082, 0),
				# ]
			# },
		},
	},

	# Giyilebilir kategoriler: eski tip-bazli altlar (Govde/Baslik, Kilic/Yay...)
	# UI'dan kaldirildi; yerine sinif/grup altlari (10..14) geldi. Grid, sinif VE
	# arti (+1..+9) secilince SHOP_SEARCH_GRID_FAMILIES'ten suzulerek dolar.
	SHOP_SEARCH_CATEGORY_ARMOR: {
		"name": localeInfo.SHOP_SEARCH_CAT_ARMOR,
		"sub_sort": [
		SHOP_SEARCH_SUB_GRID_WARRIOR, SHOP_SEARCH_SUB_GRID_ASSASSIN, SHOP_SEARCH_SUB_GRID_SURA,
		SHOP_SEARCH_SUB_GRID_SHAMAN, SHOP_SEARCH_SUB_GRID_SHIELD,
		],
		"sub": {
			SHOP_SEARCH_SUB_GRID_WARRIOR: {
				"name": getattr(localeInfo, "JOB_WARRIOR", "Savasci"),
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_ARMOR, SHOP_SEARCH_SUB_GRID_WARRIOR)]),
			},
			SHOP_SEARCH_SUB_GRID_ASSASSIN: {
				"name": getattr(localeInfo, "JOB_ASSASSIN", "Ninja"),
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_ARMOR, SHOP_SEARCH_SUB_GRID_ASSASSIN)]),
			},
			SHOP_SEARCH_SUB_GRID_SURA: {
				"name": getattr(localeInfo, "JOB_SURA", "Sura"),
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_ARMOR, SHOP_SEARCH_SUB_GRID_SURA)]),
			},
			SHOP_SEARCH_SUB_GRID_SHAMAN: {
				"name": getattr(localeInfo, "JOB_SHAMAN", "Saman"),
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_ARMOR, SHOP_SEARCH_SUB_GRID_SHAMAN)]),
			},
			SHOP_SEARCH_SUB_GRID_SHIELD: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_ARMOR_SHIELD,
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_ARMOR, SHOP_SEARCH_SUB_GRID_SHIELD)]),
			},
		}
	},

	SHOP_SEARCH_CATEGORY_WEAPON: {
		"name": localeInfo.SHOP_SEARCH_CAT_WEAPON,
		# Silah gruplari tur bazli (kullanici istegi 2026-08-02); Sura kiliclari da
		# "Savasci Tek El" altindadir (tum tek-el kiliclar). Buton adlari cp1254 \x
		# kacislariyla gomulu (LocaleInfoWrapper eksik-anahtar tuzagi + locale repack
		# gerektirmemek icin): \xfe=s(cengelli) \xe7=c(cengelli) \xfd=i(noktasiz)
		# \xde=S(cengelli) \xc7=C(cengelli).
		"sub_sort": [
		SHOP_SEARCH_SUB_GRID_WPN_ONEHAND, SHOP_SEARCH_SUB_GRID_WPN_TWOHAND, SHOP_SEARCH_SUB_GRID_WPN_DAGGER,
		SHOP_SEARCH_SUB_GRID_WPN_BOW, SHOP_SEARCH_SUB_GRID_WPN_BELL, SHOP_SEARCH_SUB_GRID_WPN_FAN,
		],
		"sub": {
			SHOP_SEARCH_SUB_GRID_WPN_ONEHAND: {
				"name": "Sava\xfe\xe7\xfd Tek El",
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_SUB_GRID_WPN_ONEHAND)]),
			},
			SHOP_SEARCH_SUB_GRID_WPN_TWOHAND: {
				"name": "Sava\xfe\xe7\xfd \xc7ift El",
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_SUB_GRID_WPN_TWOHAND)]),
			},
			SHOP_SEARCH_SUB_GRID_WPN_DAGGER: {
				"name": "Ninja Han\xe7er",
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_SUB_GRID_WPN_DAGGER)]),
			},
			SHOP_SEARCH_SUB_GRID_WPN_BOW: {
				"name": "Ninja Ok\xe7u",
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_SUB_GRID_WPN_BOW)]),
			},
			SHOP_SEARCH_SUB_GRID_WPN_BELL: {
				"name": "\xdeaman \xc7an",
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_SUB_GRID_WPN_BELL)]),
			},
			SHOP_SEARCH_SUB_GRID_WPN_FAN: {
				"name": "\xdeaman Yelpaze",
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_SUB_GRID_WPN_FAN)]),
			},
		}
	},

	SHOP_SEARCH_CATEGORY_JEWELRY: {
		"name": localeInfo.SHOP_SEARCH_CAT_JEWELRY,
		# Taki bu protoda sinifsiz (herkes takar); alt gruplar tur bazinda kalir,
		# arti secimi + grid akisi digerleriyle ayni.
		"sub_sort": [
		SHOP_SEARCH_SUB_GRID_JEW_EAR, SHOP_SEARCH_SUB_GRID_JEW_NECK, SHOP_SEARCH_SUB_GRID_JEW_WRIST,
		SHOP_SEARCH_SUB_GRID_JEW_BOOTS,
		],
		"sub": {
			SHOP_SEARCH_SUB_GRID_JEW_EAR: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_JEWELRY_EAR,
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_JEWELRY, SHOP_SEARCH_SUB_GRID_JEW_EAR)]),
			},
			SHOP_SEARCH_SUB_GRID_JEW_NECK: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_JEWELRY_NECK,
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_JEWELRY, SHOP_SEARCH_SUB_GRID_JEW_NECK)]),
			},
			SHOP_SEARCH_SUB_GRID_JEW_WRIST: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_JEWELRY_WRIST,
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_JEWELRY, SHOP_SEARCH_SUB_GRID_JEW_WRIST)]),
			},
			SHOP_SEARCH_SUB_GRID_JEW_BOOTS: {
				"name": localeInfo.SHOP_SEARCH_SUBCAT_JEWELRY_BOOTS,
				"itemList": _shopsearch_expand_families(SHOP_SEARCH_GRID_FAMILIES[(SHOP_SEARCH_CATEGORY_JEWELRY, SHOP_SEARCH_SUB_GRID_JEW_BOOTS)]),
			},
		}
	},
}

SHOP_SEARCH_CATEGORY_SORT = [
	SHOP_SEARCH_CATEGORY_BOOKS,
	SHOP_SEARCH_CATEGORY_REFINE,
	SHOP_SEARCH_CATEGORY_SOULSTONE,
	SHOP_SEARCH_CATEGORY_HERBALISM,
	SHOP_SEARCH_CATEGORY_FISHING,
	SHOP_SEARCH_CATEGORY_MINING,
	SHOP_SEARCH_CATEGORY_HORSE,
	SHOP_SEARCH_CATEGORY_POLYMORPH,
	SHOP_SEARCH_CATEGORY_SPECIAL,
	SHOP_SEARCH_CATEGORY_ARMOR,
	SHOP_SEARCH_CATEGORY_WEAPON,
	SHOP_SEARCH_CATEGORY_JEWELRY,
]

def shopsearch_is_wearable(category):
	return category in (SHOP_SEARCH_CATEGORY_ARMOR, SHOP_SEARCH_CATEGORY_WEAPON, SHOP_SEARCH_CATEGORY_JEWELRY)

def shopsearch_wearable_spec(category, sub_category):
	# Giyilebilir kategoriler (Zirh/Silah/Taki) sunucuda tipe gore eslestirilir;
	# burada (itemType, itemSubType) cozumu yapilir (sunucu SearchItemsByCategory ile ayni).
	# Giyilebilir degilse None doner.
	if category == SHOP_SEARCH_CATEGORY_WEAPON:
		m = {
			SHOP_SEARCH_SUB_WEAPON_ONEHAND: item.WEAPON_SWORD,
			SHOP_SEARCH_SUB_WEAPON_TWOHAND: item.WEAPON_TWO_HANDED,
			SHOP_SEARCH_SUB_WEAPON_DAGGER:  item.WEAPON_DAGGER,
			SHOP_SEARCH_SUB_WEAPON_BOW:     item.WEAPON_BOW,
			SHOP_SEARCH_SUB_WEAPON_BELL:    item.WEAPON_BELL,
			SHOP_SEARCH_SUB_WEAPON_FAN:     item.WEAPON_FAN,
		}
		if sub_category in m:
			return (item.ITEM_TYPE_WEAPON, m[sub_category])
	elif category == SHOP_SEARCH_CATEGORY_ARMOR:
		m = {
			SHOP_SEARCH_SUB_ARMOR_BODY:   item.ARMOR_BODY,
			SHOP_SEARCH_SUB_ARMOR_SHIELD: item.ARMOR_SHIELD,
			SHOP_SEARCH_SUB_ARMOR_HEAD:   item.ARMOR_HEAD,
		}
		if sub_category in m:
			return (item.ITEM_TYPE_ARMOR, m[sub_category])
	elif category == SHOP_SEARCH_CATEGORY_JEWELRY:
		m = {
			SHOP_SEARCH_SUB_JEWELRY_EAR:   item.ARMOR_EAR,
			SHOP_SEARCH_SUB_JEWELRY_NECK:  item.ARMOR_NECK,
			SHOP_SEARCH_SUB_JEWELRY_WRIST: item.ARMOR_WRIST,
			SHOP_SEARCH_SUB_JEWELRY_BOOTS: item.ARMOR_FOOTS,
		}
		if sub_category in m:
			return (item.ITEM_TYPE_ARMOR, m[sub_category])
	return None

def shopsearch_send(category, sub_category=-1, isSearchAttr=False, selectedItems=None, plusLevel=0):
	# Eski-binary korumalari constInfo yazimlarindan ONCE calisir: paket hic
	# gonderilmeyecekse yesil vurgu durumu da dolmamali (inceleme bulgusu 2026-08-02).
	# istemci binary'si yeniden derlenmemisse net mesaj ver (cokme yerine)
	if not hasattr(shop, "SendSearchItem"):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_SEARCH_NEED_UPDATE)
		return

	# Wire korumasi: TPacketCGShopSearch'e selCount+sel[] alanlari KOSULSUZ eklendi (250 bayt).
	# app.ENABLE_SHOP_SEARCH_ITEM_SELECT sabiti HIC yoksa binary ESKI 9-baytlik wire ile
	# derlenmis demektir; gonderim framing'i kaydirir ve oyuncu dusurulur -> hic gonderme.
	if not hasattr(app, "ENABLE_SHOP_SEARCH_ITEM_SELECT"):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_SEARCH_NEED_UPDATE)
		return

	constInfo.OFFLINESHOP_LAST_SEARCHED_CATEGORY = category
	constInfo.OFFLINESHOP_LAST_SEARCHED_SUBCATEGORY = sub_category
	constInfo.OFFLINESHOP_LAST_SEARCH_IS_ATTR = isSearchAttr

	constInfo.OFFLINESHOP_LAST_SEARCHED_ITEMS = []
	# Giyilebilir kategoriler artik vnum-listeli grid ile aranir; tip/alt-tip vurgusu
	# yalnizca eski tip-bazli altlarda dolu doner, yeni grid altlarinda None kalir.
	constInfo.OFFLINESHOP_LAST_SEARCH_WEARABLE = shopsearch_wearable_spec(category, sub_category)

	searchCategory = category
	if shopsearch_is_wearable(category) and isSearchAttr:
		searchCategory += 1
	searchIndex = searchCategory * SHOP_CATEGORY_MAX_SUB
	search_data = SHOP_SEARCH_FILTERS[category]
	if sub_category >= 0:
		search_data = search_data["sub"][sub_category]
		searchIndex += sub_category

	# Giyilebilir grid: arti secimi zorunlu; arti seviyesi paketin socket0 alaninda gider
	sendSocket0 = 0
	if shopsearch_is_wearable(category):
		if plusLevel < 1 or plusLevel > 9:
			chat.AppendChat(chat.CHAT_TYPE_INFO, TXT_SELECT_PLUS)
			return
		sendSocket0 = plusLevel

	# Item-secmeli arama: grid'de secim yapildiysa SADECE secilenler aranir ve
	# pazar penceresindeki yesil vurgu da sadece secilenlerle eslesir.
	# Eski binary'de (app sabiti yok/0) secim sunucuya gonderilemez -> tum liste aranir.
	useSelection = False
	if selectedItems:
		if getattr(app, "ENABLE_SHOP_SEARCH_ITEM_SELECT", 0):
			useSelection = True
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Secili arama icin istemci guncellemesi gerekli; tum liste araniyor.")

	if useSelection:
		for data in selectedItems:
			constInfo.OFFLINESHOP_LAST_SEARCHED_ITEMS.append(data)
	elif shopsearch_is_wearable(category):
		# Yesil vurgu yalnizca secilen artinin itemlarina uygulanir
		for data in shopsearch_get_item_list(category, sub_category, plusLevel):
			constInfo.OFFLINESHOP_LAST_SEARCHED_ITEMS.append(data)
	else:
		for data in search_data["itemList"]:
			constInfo.OFFLINESHOP_LAST_SEARCHED_ITEMS.append(data)

	if useSelection:
		shop.SendSearchItem(searchIndex, sendSocket0, list(selectedItems))
	else:
		shop.SendSearchItem(searchIndex, sendSocket0)

def shopsearch_get_item_list(category, sub_category=-1, plusLevel=0):
	data = SHOP_SEARCH_FILTERS[category]
	if "sub" in data:
		itemList = data["sub"][sub_category]["itemList"]
	else:
		itemList = data["itemList"]
	# Giyilebilir grid: arti secildiyse yalnizca son hanesi artiya esit vnumlar
	# gosterilir/aranir (11204 = +4 kaligi)
	if plusLevel >= 1 and shopsearch_is_wearable(category):
		filtered = []
		for d in itemList:
			if d[0] % 10 == plusLevel:
				filtered.append(d)
		return filtered
	return itemList

class ShopSearchWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def SetToolTip(self, itemToolTip):
		self.itemToolTip = proxy(itemToolTip)

	def __Initialize(self):
		self.categoryButtons = []
		self.subCategoryButtons = {}
		# Giyilebilir grid: kategori -> [(spacer/buton, artiDegeri), ...] arti secim butonlari
		self.plusButtons = {}
		self.category = -1
		self.subCategory = -1
		# Giyilebilir grid: secili arti seviyesi (0 = henuz secilmedi)
		self.selectedPlus = 0
		self.itemToolTip = None
		self.isSearchAttr = False
		# Item-secmeli arama: secili (vnum, socket0) ciftleri (aktif alt-kategori icin)
		self.selectedItems = []
		# Grid sayfalama: sayfa listesi [(slotIndex, itemData), ...] listeleri,
		# aktif sayfa no ve gorunen slot -> itemData eslemesi
		self.gridPages = []
		self.gridPage = 0
		self.gridSlotMap = {}
		self.pagePrevButton = None
		self.pageNextButton = None
		self.pageLabel = None
		# LoadDialog'da atanan widget referanslari (Destroy -> __Initialize ile sifirlanir)
		self.titleBar = None
		self.categoryMask = None
		self.categoryContent = None
		self.scrollbar = None
		self.subCategoryMask = None
		self.subCategoryContent = None
		self.subScrollbar = None
		self.itemSlot = None
		self.searchButton = None
		self.clearButton = None
		self.infoLabel = None
		self.searchAttrToggle = None

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/shopsearchwindow.py")

			self.titleBar = self.GetChild("TitleBar")

			self.categoryMask = self.GetChild("CategoryMask")
			self.categoryContent = self.GetChild("CategoryContent")
			self.scrollbar = self.GetChild("Scrollbar")

			self.subCategoryMask = self.GetChild("SubCategoryMask")
			self.subCategoryContent = self.GetChild("SubCategoryContent")
			self.subScrollbar = self.GetChild("SubScrollbar")

			self.itemSlot = self.GetChild("ItemSlot")
			self.searchButton = self.GetChild("SearchButton")
			self.clearButton = self.GetChild("ClearButton")
			self.infoLabel = self.GetChild("InfoLabel")
			self.searchAttrToggle = self.GetChild("SearchAttrToggle")

			self.itemSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.__ShowToolTip))
			self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__HideToolTip))
			self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnClickItemSlot))

			# Grid sayfa kontrolleri (ItemList board'un ayrilan son satirinda;
			# yalnizca liste tek sayfaya sigmayinca gosterilir)
			itemListBoard = self.GetChild("ItemList")
			self.pagePrevButton = ui.Button()
			self.pagePrevButton.SetParent(itemListBoard)
			self.pagePrevButton.SetPosition(10, 302)
			self.pagePrevButton.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
			self.pagePrevButton.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
			self.pagePrevButton.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
			self.pagePrevButton.SetText("<")
			self.pagePrevButton.SAFE_SetEvent(self.__OnPrevGridPage)
			self.pagePrevButton.Hide()

			self.pageNextButton = ui.Button()
			self.pageNextButton.SetParent(itemListBoard)
			self.pageNextButton.SetPosition(151, 302)
			self.pageNextButton.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
			self.pageNextButton.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
			self.pageNextButton.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
			self.pageNextButton.SetText(">")
			self.pageNextButton.SAFE_SetEvent(self.__OnNextGridPage)
			self.pageNextButton.Hide()

			self.pageLabel = ui.TextLine()
			self.pageLabel.SetParent(itemListBoard)
			self.pageLabel.SetPosition(102, 306)
			self.pageLabel.SetHorizontalAlignCenter()
			self.pageLabel.SetText("")
			self.pageLabel.Hide()

			self.searchButton.SAFE_SetEvent(self.__OnSearch)
			self.clearButton.SAFE_SetEvent(self.__OnClear)

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

			self.scrollbar.SetScrollContent(self.categoryMask, self.categoryContent)
			self.scrollbar.SAFE_SetOnWheelEvent(self.categoryContent)

			self.subScrollbar.SetScrollContent(self.subCategoryMask, self.subCategoryContent)
			self.subScrollbar.SAFE_SetOnWheelEvent(self.subCategoryContent)

			for category in SHOP_SEARCH_CATEGORY_SORT:
				self.__CreateCategory(category)

			self.RefreshCategoryContentHeight(self.categoryButtons, self.categoryContent, self.scrollbar)
			self.subScrollbar.Hide()
			self.__OnClickCategory(-1)

			self.searchAttrToggle.SetToggleDownEvent(ui.__mem_func__(self.__OnToggleAttrSearch), True)
			self.searchAttrToggle.SetToggleUpEvent(ui.__mem_func__(self.__OnToggleAttrSearch), False)

		except Exception:
			import exception
			exception.Abort("ShopSearchWindow.LoadDialog.BindObject")

	def __OnToggleAttrSearch(self, isSearch):
		self.isSearchAttr = isSearch

	def __RefreshCategory(self):
		if self.category < 0:
			self.itemSlot.Hide()
			self.searchAttrToggle.Hide()
			self.infoLabel.Show()
			self.infoLabel.SetText(TXT_NO_CATEGORY)

			self.searchButton.Down()
			self.searchButton.Disable()
			self.__UpdateGridPageControls()
			return

		self.searchButton.SetUp()
		self.searchButton.Enable()
		self.infoLabel.Hide()
		self.itemSlot.Hide()
		self.searchAttrToggle.Hide()
		self.itemSlot.Show()

		hasSubCategories = "sub" in SHOP_SEARCH_FILTERS[self.category]
		if not hasSubCategories or hasSubCategories and self.subCategory >= 0:
			self.searchButton.SetUp()
			self.searchButton.Enable()
			self.itemSlot.Show()
			self.infoLabel.Hide()

			self.__RefreshCategoryItems()
		else:
			self.itemSlot.Hide()
			self.infoLabel.Show()
			self.infoLabel.SetText(TXT_NO_CATEGORY)
			self.searchButton.Down()
			self.searchButton.Disable()

		if shopsearch_is_wearable(self.category):
			# "Bonuslu Ara" toggle'i kaldirildi (bir daha gosterilmez). Grid, sinif/grup
			# VE arti secilmeden dolmaz; arti eksikse kullanici bilgilendirilir.
			if self.subCategory >= 0 and self.selectedPlus < 1:
				self.itemSlot.Hide()
				self.infoLabel.Show()
				self.infoLabel.SetText(TXT_SELECT_PLUS)
				self.searchButton.Down()
				self.searchButton.Disable()

		# Sayfa kontrolleri en son: grid gercekten gorunuyorsa ve 1'den fazla sayfa varsa
		self.__UpdateGridPageControls()

	def __RefreshCategoryItems(self):
		self.__BuildGridPages()
		self.__RenderGridPage()

	def __GetItemYSize(self, vnum):
		# Ikonun kaplayacagi dikey hucre sayisi (1-3); proto okunamazsa 1 varsay
		try:
			item.SelectItem(vnum)
			ySize = item.GetItemSize()[1]
		except Exception:
			ySize = 1
		if ySize < 1:
			ySize = 1
		elif ySize > GRID_PACK_ROWS:
			ySize = GRID_PACK_ROWS
		return ySize

	def __FindFreeGridSlot(self, occupied, ySize):
		# Soldan saga, yukaridan asagi ilk bos yuva: ySize hucre alt alta bos olmali
		for index in xrange(GRID_COLS * GRID_PACK_ROWS):
			row = index // GRID_COLS
			if row + ySize > GRID_PACK_ROWS:
				continue
			fits = True
			for k in xrange(ySize):
				if (index + GRID_COLS * k) in occupied:
					fits = False
					break
			if fits:
				return index
		return -1

	def __BuildGridPages(self):
		# Gosterilecek listeyi gercek ikon boyutlariyla sayfalara yerlestir
		self.gridPages = []
		page = []
		occupied = {}
		for itemData in self.__GetDisplayItemList():
			ySize = self.__GetItemYSize(itemData[0])
			slotIndex = self.__FindFreeGridSlot(occupied, ySize)
			if slotIndex < 0:
				self.gridPages.append(page)
				page = []
				occupied = {}
				slotIndex = self.__FindFreeGridSlot(occupied, ySize)
				if slotIndex < 0:
					continue
			for k in xrange(ySize):
				occupied[slotIndex + GRID_COLS * k] = 1
			page.append((slotIndex, itemData))
		if page or not self.gridPages:
			self.gridPages.append(page)
		if self.gridPage >= len(self.gridPages):
			self.gridPage = 0

	def __RenderGridPage(self):
		for index in range(ITEM_SLOT_COUNT):
			self.itemSlot.SetItemSlot(index, 0, 0)
			self.itemSlot.ClearSlot(index)

		self.gridSlotMap = {}
		if self.gridPages and self.gridPage < len(self.gridPages):
			for slotIndex, itemData in self.gridPages[self.gridPage]:
				self.itemSlot.SetItemSlot(slotIndex, itemData[0], 0)
				self.gridSlotMap[slotIndex] = itemData

		# Secim isaretlerini yeniden uygula (kategori/alt-kategori degisiminde secim sifirlanir)
		self.__RefreshSelectionMarks()

	def __UpdateGridPageControls(self):
		if not self.pagePrevButton:
			return
		pageCount = len(self.gridPages)
		if pageCount <= 1 or not self.itemSlot.IsShow():
			self.pagePrevButton.Hide()
			self.pageNextButton.Hide()
			self.pageLabel.Hide()
			return
		self.pageLabel.SetText("%d / %d" % (self.gridPage + 1, pageCount))
		self.pagePrevButton.Show()
		self.pageNextButton.Show()
		self.pageLabel.Show()

	def __OnPrevGridPage(self):
		if len(self.gridPages) <= 1:
			return
		self.gridPage = (self.gridPage - 1) % len(self.gridPages)
		self.__RenderGridPage()
		self.__UpdateGridPageControls()

	def __OnNextGridPage(self):
		if len(self.gridPages) <= 1:
			return
		self.gridPage = (self.gridPage + 1) % len(self.gridPages)
		self.__RenderGridPage()
		self.__UpdateGridPageControls()

	def __GetDisplayItemList(self):
		# Grid'de o an gosterilen liste. Giyilebilirlerde sinif/grup + arti secilmeden
		# bos doner; secilince liste artiya gore suzulur. Diger kategorilerde tam liste.
		if self.category < 0:
			return []
		if shopsearch_is_wearable(self.category):
			if self.subCategory < 0 or self.selectedPlus < 1:
				return []
		try:
			return shopsearch_get_item_list(self.category, self.subCategory, self.selectedPlus)
		except Exception:
			return []

	def __CreateCategory(self, categoryIndex):
		if categoryIndex == "break":
			step = ui.Window()
			step.SetParent(self.categoryContent)
			step.SetSize(1, 8)
			step.Show()
			self.categoryButtons.append((step, categoryIndex))
		else:
			data = SHOP_SEARCH_FILTERS[categoryIndex]
			categoryBtn = self.__CreateCategoryButton(self.categoryContent, data["name"])
			categoryBtn.SAFE_SetEvent(self.__OnClickCategory, categoryIndex)
			categoryBtn.SetClippingMaskWindow(self.categoryMask)
			self.categoryButtons.append((categoryBtn, categoryIndex))
			self.subCategoryButtons[categoryIndex] = []

			if "sub" in data:
				subCategories = data["sub"]
				# Goruntulenme sirasi: kategoride "sub_sort" verilmisse o sirayla,
				# yoksa sayisal index sirasiyla (0,1,2...). Buton index'i (i) her zaman
				# gercek alt-kategori degeridir; bu yuzden searchIndex/arama DEGISMEZ.
				order = data["sub_sort"] if "sub_sort" in data else range(len(subCategories))
				for i in order:
					if i in subCategories:
						subData = subCategories[i]
						subBtn = self.__CreateCategoryButton(self.subCategoryContent, subData["name"])
						subBtn.SetClippingMaskWindow(self.subCategoryMask)
						subBtn.SAFE_SetEvent(self.__OnClickSubCategory, i)
						self.subCategoryButtons[categoryIndex].append((subBtn, i))

			# Giyilebilir kategorilerde sinif/grup listesinin altina arti (+1..+9)
			# secim butonlari eklenir (ayrik durum: self.selectedPlus)
			if shopsearch_is_wearable(categoryIndex):
				spacer = ui.Window()
				spacer.SetParent(self.subCategoryContent)
				spacer.SetSize(1, 8)
				spacer.Show()
				plusList = [(spacer, None)]
				for plusVal in SHOP_SEARCH_PLUS_CHOICES:
					plusBtn = self.__CreateCategoryButton(self.subCategoryContent, "+%d" % plusVal)
					plusBtn.SetClippingMaskWindow(self.subCategoryMask)
					plusBtn.SAFE_SetEvent(self.__OnClickPlus, plusVal)
					plusList.append((plusBtn, plusVal))
				self.plusButtons[categoryIndex] = plusList

	def __CreateCategoryButton(self, parent, name):
		btn = ui.Button()
		btn.SetParent(parent)
		btn.SetUpVisual("d:/ymir work/ui/flamewind/public/big_button_01.sub")
		btn.SetOverVisual("d:/ymir work/ui/flamewind/public/big_button_02.sub")
		btn.SetDownVisual("d:/ymir work/ui/flamewind/public/big_button_03.sub")
		btn.SetText(name)

		btn.ButtonText.SetHorizontalAlignLeft()
		btn.ButtonText.SetWindowVerticalAlignCenter()
		btn.ButtonText.SetPosition(7, 0)

		btn.SetWindowHorizontalAlignCenter()
		btn.Show()
		return btn

	def RefreshCategoryContentHeight(self, buttonList, contentWindow, scrollBar):
		start_y_pos = 10

		total_height = start_y_pos
		for data in buttonList:
			btn = data[0]
			btn.SetPosition(0, total_height)
			height = btn.GetHeight()
			height_offset = 5
			total_height += height + height_offset

		# new_project Window sinifinda SetHeight yok; SetSize ile (genisligi koruyarak) ayarla
		contentWindow.SetSize(contentWindow.GetWidth(), total_height)
		scrollBar.ResizeScrollBar()

	def __OnClickCategory(self, category):
		for data in self.categoryButtons:
			btn = data[0]
			if type(btn) is not ui.Button:
				continue

			if data[1] == category:
				btn.Down()
				btn.Disable()
			else:
				btn.SetUp()
				btn.Enable()

		self.category = category
		self.subCategory = -1
		self.selectedItems = []
		self.selectedPlus = 0
		self.gridPage = 0
		self.__RefreshSubCategoryButtons()
		self.__RefreshCategory()
		if category >= 0:
			# Giyilebilirlerde arti butonlari sinif listesinin altina dizilir
			buttonList = self.subCategoryButtons[self.category]
			if self.category in self.plusButtons:
				buttonList = buttonList + self.plusButtons[self.category]
			self.RefreshCategoryContentHeight(buttonList, self.subCategoryContent, self.subScrollbar)

	def __RefreshSubCategoryButtons(self):
		for i, buttonList in self.subCategoryButtons.iteritems():
			for data in buttonList:
				btn = data[0]
				if i != self.category:
					btn.Hide()
					continue

				if type(btn) is not ui.Button:
					continue

				btn.Show()
				if data[1] == self.subCategory:
					btn.Down()
					btn.Disable()
				else:
					btn.SetUp()
					btn.Enable()

		# Arti (+N) butonlari: yalnizca aktif giyilebilir kategoride gorunur;
		# secili arti basili (Down) tutulur
		for i, buttonList in self.plusButtons.iteritems():
			for data in buttonList:
				btn = data[0]
				if i != self.category:
					btn.Hide()
					continue

				btn.Show()
				if type(btn) is not ui.Button:
					continue

				if data[1] == self.selectedPlus:
					btn.Down()
					btn.Disable()
				else:
					btn.SetUp()
					btn.Enable()

	def __OnClickSubCategory(self, index):
		self.subCategory = index
		self.selectedItems = []
		self.gridPage = 0
		self.__RefreshSubCategoryButtons()
		self.__RefreshCategory()

	def __OnClickPlus(self, plusVal):
		# Arti seviyesi secimi; grid ancak sinif/grup + arti birlikte secilince dolar.
		# Sinif degistirilse de arti secimi korunur (ayni artida sinif kiyasi kolay olsun).
		self.selectedPlus = plusVal
		self.selectedItems = []
		self.gridPage = 0
		self.__RefreshSubCategoryButtons()
		self.__RefreshCategory()

	def __OnClickItemSlot(self, index):
		# Grid'deki iteme tiklayinca sec/birak: yesil isaretli itemler aranir.
		# Secim yoksa arama tum listeyi (giyilebilirde: sinif+arti listesini) tarar.
		# index = slot indexi; sayfali yerlesimde itemData eslemesi gridSlotMap'ten gelir.
		if self.category < 0:
			return
		itemData = self.gridSlotMap.get(index)
		if itemData is None:
			return
		if itemData in self.selectedItems:
			self.selectedItems.remove(itemData)
		elif len(self.selectedItems) < SHOP_SEARCH_SELECT_MAX:
			self.selectedItems.append(itemData)
		self.__RefreshSelectionMarks()

	def __RefreshSelectionMarks(self):
		# Secili slotlara pazar penceresindeki arama vurgusuyla ayni yesil overlay
		# (sayfali yerlesim: slot -> itemData eslemesi gridSlotMap'ten)
		for idx in range(ITEM_SLOT_COUNT):
			itemData = self.gridSlotMap.get(idx)
			if itemData is not None and itemData in self.selectedItems:
				self.itemSlot.ActivateSlot(idx, 0.0, 1.0, 0.0, 0.6)
			else:
				self.itemSlot.DeactivateSlot(idx)
		wndMgr.RefreshSlot(self.itemSlot.GetWindowHandle())

	def __ShowToolTip(self, index):
		if self.itemToolTip:
			itemData = self.gridSlotMap.get(index)
			if itemData is None:
				return
			itemVnum = itemData[0]
			metinSlot = [0 for i in xrange(player.METIN_SOCKET_MAX_NUM)]
			metinSlot[0] = itemData[1]

			self.itemToolTip.ClearToolTip()
			self.itemToolTip.AddItemData(itemVnum, metinSlot)
			self.itemToolTip.ShowToolTip()

	def __HideToolTip(self):
		if self.itemToolTip:
			self.itemToolTip.HideToolTip()

	def __OnSearch(self):
		if self.category < 0:
			return
		# Giyilebilir grid: sinif/grup ve arti secilmeden arama yapilamaz
		if shopsearch_is_wearable(self.category):
			if self.subCategory < 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TXT_NO_CATEGORY)
				return
			if self.selectedPlus < 1:
				chat.AppendChat(chat.CHAT_TYPE_INFO, TXT_SELECT_PLUS)
				return
		self.__OnClear()
		shopsearch_send(self.category, self.subCategory, self.isSearchAttr, self.selectedItems, self.selectedPlus)

	def __OnClear(self):
		if hasattr(shop, "ClearFoundShopMap"):
			shop.ClearFoundShopMap()
		# Pazar penceresindeki esya vurgusu da kalksin
		constInfo.OFFLINESHOP_LAST_SEARCHED_ITEMS = []
		constInfo.OFFLINESHOP_LAST_SEARCH_WEARABLE = None
		chat.AppendChat(chat.CHAT_TYPE_INFO, TXT_CLEAR_INFO)

	def Open(self):
		if self.IsShow():
			self.Close()
			return

		self.Show()
		self.SetTop()
		self.SetCenterPosition()

	def Close(self):
		self.Hide()
		self.__HideToolTip()

	def OnPressEscapeKey(self):
		self.Close()
		return True
