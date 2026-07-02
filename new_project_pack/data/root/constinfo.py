import app
import chrmgr
import item
import net
import player

if app.ENABLE_OFFLINE_SHOP:
	gift_items={}
	OFFLINE_SHOP_EDITING = 0		# pazar duzenleme modunda iken envanter eylemlerini kilitler
	OFFLINE_SHOP_ADDED_SLOTS = {}	# duzenlemede pazara eklenen envanter slotlari (kirmizi overlay) {globalSlot:1}

# Ticarete (exchange) konulan kendi item'lerimin envanter slotuna kirmizi overlay
ENABLE_EXCHANGE_ITEM_HIGHLIGHT = True	# pure-python ozellik anahtari (binary recompile gerektirmez)
EXCHANGE_SELF_SLOT_MAP = {}				# {tradeSlotIndex: globalInvSlot} -> item ekleme aninda kaydedilir

def EXCHANGE_RESET_SLOTS():
	EXCHANGE_SELF_SLOT_MAP.clear()

def EXCHANGE_RECORD_ADD_SLOT(tradeSlot, invSlot):
	EXCHANGE_SELF_SLOT_MAP[tradeSlot] = invSlot

def EXCHANGE_GET_ADDED_SLOTS():
	# canli ticaret verisine gore uzlastir: sadece o ticaret slotunda hala item varsa highlight et
	import exchange
	result = {}
	for tradeSlot in EXCHANGE_SELF_SLOT_MAP.keys():
		if 0 != exchange.GetItemVnumFromSelf(tradeSlot):
			result[EXCHANGE_SELF_SLOT_MAP[tradeSlot]] = 1
	return result

# F5 hizli sil/sat penceresine stage edilen kendi item'lerime envanterde kirmizi overlay
ENABLE_ITEM_DELETE_HIGHLIGHT = True

def ITEM_DELETE_GET_INVEN_SLOTS():
	# ITEM_DELETE_LIST = {privatePos: (invenType, invenPos)}; sadece normal envanter (player.INVENTORY) slotlari
	result = {}
	for value in globals().get("ITEM_DELETE_LIST", {}).values():
		invenType, invenPos = value
		if player.INVENTORY == invenType:
			result[invenPos] = 1
	return result

if app.ENABLE_ITEM_SHOP_SYSTEM:
	ITEM_SEARCH_DATA = []
	ITEM_DATA = {}#for item shop
	ITEM_SHOP_EM_BIND_ATTR_INDEX = 6
	ITEM_SHOP_EM_BIND_ATTR_VALUE = 31337
	ITEM_SHOP_EM_PURCHASE_BLOCKED_VNUMS = (80014, 80015, 80016, 80017)

if app.KYGN_CHEST_INFO:
	CD_CUR_CHEST_CELL = 753

if app.ENABLE_SEND_TARGET_INFO:
	MONSTER_INFO_DATA = {}

if app.ENABLE_CUBE_RENEWAL:
	CUBE_RENEWAL_IS_OPENED = 0
	cube_count_items = {}

if app.WJ_NEW_DROP_DIALOG:
	silme = 0
	ITEM_DELETE_LIST = {}

if app.ENABLE_REFINE_RENEWAL:
	IS_AUTO_REFINE = False
	AUTO_REFINE_TYPE = 0
	AUTO_REFINE_DATA = {
		"ITEM" : [-1, -1],
		"NPC" : [0, -1, -1, 0]
	}

ENABLE_POTIONS_AFFECTSHOWER = 1
skillBoard = 0
# EXTRA BEGIN
ENABLE_NEW_LEVELSKILL_SYSTEM = False # loads 5 (B,M,G,P,F) skills .mse
ENABLE_RANDOM_CHANNEL_SEL = False # don't set a random channel when you open the client
ENABLE_CLEAN_DATA_IF_FAIL_LOGIN = False # don't remove id and password if the login attempt fails
ENABLE_PASTE_FEATURE = True # ctrl+v will now work
ENABLE_FULLSTONE_DETAILS = True # display all the bonuses added by a stone instead of the first one
ENABLE_REFINE_PCT = False # enable successfulness % in the refine dialog
EXTRA_UI_FEATURE = True # enable extra ui features
SELECT_CHAR_NO_DELAY = 0.5 # change the 3sec delay while choosing a character in the select phase
ENABLE_ACTIVE_PET_SEAL_EFFECT = True # enable active effect on pet seals
ENABLE_RECURSIVE_UI_DESTROY = True # force clears everything inside the UI components
ENABLE_CMDCHAT_VARIADIC_ARGS = True # enable variadic arguments in cmdchat functions
ENABLE_SELF_STACK_SCROLLS = True # enable self stack of scrolls, etc
ENABLE_UI_DEBUG_WINDOW = False # load DebugWindow.py from client folder instead of login window
ENABLE_SPECIAL_CAMERA_MODE = True # GM only: free camera Numpad / PgUp-PgDn (client rebuild required)
ENABLE_CENTER_SKILL_ERROR_NOTIFY = True # skill/shot errors: center screen bar instead of character tail
ENABLE_MAP_INTERACTIVE_LOGIN = True # load a list of maps in the login window
# EXTRA END

# enable save account
ENABLE_SAVE_ACCOUNT = True
if ENABLE_SAVE_ACCOUNT:
	class SAB:
		ST_CACHE, ST_FILE, ST_REGISTRY = xrange(3)
		slotCount = 5
		storeType = ST_REGISTRY # 0 cache, 1 file, 2 registry
		btnName = {
			"Save": "SaveAccountButton_Save_%02d",
			"Access": "SaveAccountButton_Access_%02d",
			"Remove": "SaveAccountButton_Remove_%02d",
		}
		accData = {}
		regPath = r"SOFTWARE\AyazMt2_Srv1"
		regName = "slot%02d_%s"
		regValueId = "id"
		regValuePwd = "pwd"
		fileExt = ".do.not.share.it.txt"
def CreateSABDataFolder(filePath):
	import os
	folderPath = os.path.split(filePath)[0]
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)
def IsExistSABDataFile(filePath):
	import os
	return os.path.exists(filePath)
def GetSABDataFile(idx):
	import os
	filePath = "%s\\AyazMt2_Srv1\\" % os.getenv('appdata')
	filePath += SAB.regName % (idx, SAB.regValueId)
	filePath += SAB.fileExt
	return filePath
def DelJsonSABData(idx):
	import os
	filePath = GetSABDataFile(idx)
	if IsExistSABDataFile(filePath):
		os.remove(filePath)
def GetJsonSABData(idx):
	(id, pwd) = ("", "")
	filePath = GetSABDataFile(idx)
	if not IsExistSABDataFile(filePath):
		return (id, pwd)
	with old_open(filePath) as data_file:
		try:
			import json
			(id, pwd) = json.load(data_file)
			id = str(id) # unicode to ascii
			pwd = str(pwd) # unicode to ascii
		except ValueError:
			pass
	return (id, pwd)
def SetJsonSABData(idx, slotData):
	filePath = GetSABDataFile(idx)
	CreateSABDataFolder(filePath)
	with old_open(filePath, "w") as data_file:
		import json
		json.dump(slotData, data_file)
def DelWinRegKeyValue(keyPath, keyName):
	try:
		import _winreg
		_winreg.CreateKey(_winreg.HKEY_CURRENT_USER, keyPath)
		_tmpKey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, keyPath, 0, _winreg.KEY_WRITE)
		_winreg.DeleteValue(_tmpKey, keyName)
		_winreg.CloseKey(_tmpKey)
		return True
	except WindowsError:
		return False
def GetWinRegKeyValue(keyPath, keyName):
	try:
		import _winreg
		_tmpKey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, keyPath, 0, _winreg.KEY_READ)
		keyValue, keyType = _winreg.QueryValueEx(_tmpKey, keyName)
		_winreg.CloseKey(_tmpKey)
		return str(keyValue) # unicode to ascii
	except WindowsError:
		return None
def SetWinRegKeyValue(keyPath, keyName, keyValue):
	try:
		import _winreg
		_winreg.CreateKey(_winreg.HKEY_CURRENT_USER, keyPath)
		_tmpKey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, keyPath, 0, _winreg.KEY_WRITE)
		_winreg.SetValueEx(_tmpKey, keyName, 0, _winreg.REG_SZ, keyValue)
		_winreg.CloseKey(_tmpKey)
		return True
	except WindowsError:
		return False

# classic minmax def
def minmax(tmin, tmid, tmax):
	if tmid < tmin:
		return tmin
	elif tmid > tmax:
		return tmax
	return tmid
# EXTRA END

# TRADE_GOLD_WITH_THOUSANDS_SEPARATORS BEGIN
def intWithCommas(x, commasign='.'):
	# alternative of
	# return '{0:,}'.format(x).replace(',', commasign)
	if type(x) not in [type(0), type(0L)]:
		raise TypeError("Parameter must be an integer.")
	if x < 0:
		return '-' + intWithCommas(-x, commasign)
	result = ''
	while x >= 1000:
		x, r = divmod(x, 1000)
		result = "%s%03d%s" % (commasign, r, result)
	return "%d%s" % (x, result)
# TRADE_GOLD_WITH_THOUSANDS_SEPARATORS END

def Emoji(path):
	return "|E{}|e".format(path)

def Color(hexString):
	return "|cff{}|h".format(hexString)

def TextColor(text, hexString):
	return "|cff{}|h{}|r".format(hexString, text)

# option
IN_GAME_SHOP_ENABLE = 1
CONSOLE_ENABLE = 0

PVPMODE_ENABLE = 1
PVPMODE_TEST_ENABLE = 0
PVPMODE_ACCELKEY_ENABLE = 1
PVPMODE_ACCELKEY_DELAY = 0.5
PVPMODE_PROTECTED_LEVEL = 15

TEST_BUILD_WATERMARK_ENABLE = 0
TEST_BUILD_WATERMARK_TEXT = "AYAZMT2_TEST_BUILD_V50936"
TEST_BUILD_WATERMARK_TEXT2 = "Nihai surum degildir, Hatalar ve eksikler olabilir."

FOG_LEVEL0 = 4800.0
FOG_LEVEL1 = 9600.0
FOG_LEVEL2 = 12800.0
FOG_LEVEL = FOG_LEVEL0
FOG_LEVEL_LIST=[FOG_LEVEL0, FOG_LEVEL1, FOG_LEVEL2]

CAMERA_MAX_DISTANCE_SHORT = 2500.0
CAMERA_MAX_DISTANCE_LONG = 4375.0
CAMERA_MAX_DISTANCE_LIST=[CAMERA_MAX_DISTANCE_SHORT, CAMERA_MAX_DISTANCE_LONG]
CAMERA_MAX_DISTANCE = CAMERA_MAX_DISTANCE_SHORT

CHRNAME_COLOR_INDEX = 0

ENVIRONMENT_NIGHT="d:/ymir work/environment/moonlight04.msenv"

if app.ENABLE_NIGHT_MODE_OPTION:
	Night = 0

	def APPLY_NIGHT_MODE(level=None):
		global Night
		import background
		import systemSetting

		if level is None:
			level = systemSetting.GetNightModeVolume()

		if level < 0.0:
			level = 0.0
		elif level > 1.0:
			level = 1.0

		Night = 1 if level > 0.0 else 0

		background.RegisterEnvironmentData(1, ENVIRONMENT_NIGHT)
		background.SetNightModeBlend(level)
else:
	Night = 0

	def APPLY_NIGHT_MODE(level=None):
		pass

# constant
HIGH_PRICE = 500000
MIDDLE_PRICE = 50000
ERROR_METIN_STONE = 28960
SUB2_LOADING_ENABLE = 1
EXPANDED_COMBO_ENABLE = 1
CONVERT_EMPIRE_LANGUAGE_ENABLE = 0
USE_ITEM_WEAPON_TABLE_ATTACK_BONUS = 0
ADD_DEF_BONUS_ENABLE = 0
LOGIN_COUNT_LIMIT_ENABLE = 0

USE_SKILL_EFFECT_UPGRADE_ENABLE = 1

VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD = 1
GUILD_MONEY_PER_GSP = 100
GUILD_WAR_TYPE_SELECT_ENABLE = 1
TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE = 10

HAIR_COLOR_ENABLE = 1
ARMOR_SPECULAR_ENABLE = 1
WEAPON_SPECULAR_ENABLE = 1
SEQUENCE_PACKET_ENABLE = 1
KEEP_ACCOUNT_CONNETION_ENABLE = 1
MINIMAP_POSITIONINFO_ENABLE = 0
MINIMAP_DATETIME_ENABLE = 1

isItemQuestionDialog = 0

def GET_ITEM_QUESTION_DIALOG_STATUS():
	global isItemQuestionDialog
	return isItemQuestionDialog

def SET_ITEM_QUESTION_DIALOG_STATUS(flag):
	global isItemQuestionDialog
	isItemQuestionDialog = flag

########################

def SET_DEFAULT_FOG_LEVEL():
	global FOG_LEVEL
	app.SetMinFog(FOG_LEVEL)

def SET_FOG_LEVEL_INDEX(index):
	global FOG_LEVEL
	global FOG_LEVEL_LIST
	try:
		FOG_LEVEL=FOG_LEVEL_LIST[index]
	except IndexError:
		FOG_LEVEL=FOG_LEVEL_LIST[0]
	app.SetMinFog(FOG_LEVEL)

def GET_FOG_LEVEL_INDEX():
	global FOG_LEVEL
	global FOG_LEVEL_LIST
	return FOG_LEVEL_LIST.index(FOG_LEVEL)

########################

def SET_DEFAULT_CAMERA_MAX_DISTANCE():
	global CAMERA_MAX_DISTANCE
	app.SetCameraMaxDistance(CAMERA_MAX_DISTANCE)

def SET_CAMERA_MAX_DISTANCE_INDEX(index):
	global CAMERA_MAX_DISTANCE
	global CAMERA_MAX_DISTANCE_LIST
	try:
		CAMERA_MAX_DISTANCE=CAMERA_MAX_DISTANCE_LIST[index]
	except:
		CAMERA_MAX_DISTANCE=CAMERA_MAX_DISTANCE_LIST[0]

	app.SetCameraMaxDistance(CAMERA_MAX_DISTANCE)

def GET_CAMERA_MAX_DISTANCE_INDEX():
	global CAMERA_MAX_DISTANCE
	global CAMERA_MAX_DISTANCE_LIST
	return CAMERA_MAX_DISTANCE_LIST.index(CAMERA_MAX_DISTANCE)

########################

def SET_DEFAULT_CHRNAME_COLOR():
	global CHRNAME_COLOR_INDEX
	chrmgr.SetEmpireNameMode(CHRNAME_COLOR_INDEX)

def SET_CHRNAME_COLOR_INDEX(index):
	global CHRNAME_COLOR_INDEX
	CHRNAME_COLOR_INDEX=index
	chrmgr.SetEmpireNameMode(index)

def GET_CHRNAME_COLOR_INDEX():
	global CHRNAME_COLOR_INDEX
	return CHRNAME_COLOR_INDEX

def SET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD(index):
	global VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD
	VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD = index

def GET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD():
	global VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD
	return VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD

def SET_DEFAULT_CONVERT_EMPIRE_LANGUAGE_ENABLE():
	global CONVERT_EMPIRE_LANGUAGE_ENABLE
	net.SetEmpireLanguageMode(CONVERT_EMPIRE_LANGUAGE_ENABLE)

def SET_DEFAULT_USE_ITEM_WEAPON_TABLE_ATTACK_BONUS():
	global USE_ITEM_WEAPON_TABLE_ATTACK_BONUS
	player.SetWeaponAttackBonusFlag(USE_ITEM_WEAPON_TABLE_ATTACK_BONUS)

def SET_DEFAULT_USE_SKILL_EFFECT_ENABLE():
	global USE_SKILL_EFFECT_UPGRADE_ENABLE
	app.SetSkillEffectUpgradeEnable(USE_SKILL_EFFECT_UPGRADE_ENABLE)

def SET_TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE():
	global TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE
	app.SetTwoHandedWeaponAttSpeedDecreaseValue(TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE)

########################

ACCESSORY_MATERIAL_LIST = [50623, 50624, 50625, 50626, 50627, 50628, 50629, 50630, 50631, 50632, 50633, 50634, 50635, 50636, 50637, 50638, 50639]
JewelAccessoryInfos = [
		# jewel		wrist	neck	ear
		[ 50634,	14420,	16220,	17220 ],
		[ 50635,	14500,	16500,	17500 ],
		[ 50636,	14520,	16520,	17520 ],
		[ 50637,	14540,	16540,	17540 ],
		[ 50638,	14560,	16560,	17560 ],
		[ 50639,	14570,	16570,	17570 ],
	]
def GET_ACCESSORY_MATERIAL_VNUM(vnum, subType):
	ret = vnum
	item_base = (vnum / 10) * 10
	for info in JewelAccessoryInfos:
		if item.ARMOR_WRIST == subType:
			if info[1] == item_base:
				return info[0]
		elif item.ARMOR_NECK == subType:
			if info[2] == item_base:
				return info[0]
		elif item.ARMOR_EAR == subType:
			if info[3] == item_base:
				return info[0]

	if vnum >= 16210 and vnum <= 16219:
		return 50625

	if item.ARMOR_WRIST == subType:
		WRIST_ITEM_VNUM_BASE = 14000
		ret -= WRIST_ITEM_VNUM_BASE
	elif item.ARMOR_NECK == subType:
		NECK_ITEM_VNUM_BASE = 16000
		ret -= NECK_ITEM_VNUM_BASE
	elif item.ARMOR_EAR == subType:
		EAR_ITEM_VNUM_BASE = 17000
		ret -= EAR_ITEM_VNUM_BASE

	type = ret/20

	if type<0 or type>=len(ACCESSORY_MATERIAL_LIST):
		type = (ret-170) / 20
		if type<0 or type>=len(ACCESSORY_MATERIAL_LIST):
			return 0

	return ACCESSORY_MATERIAL_LIST[type]

##################################################################

def GET_BELT_MATERIAL_VNUM(vnum, subType = 0):
	return 18900

##################################################################

def IS_AUTO_POTION(itemVnum):
	return IS_AUTO_POTION_HP(itemVnum) or IS_AUTO_POTION_SP(itemVnum)

def IS_AUTO_POTION_HP(itemVnum):
	if 72723 <= itemVnum and 72726 >= itemVnum:
		return 1
	elif itemVnum >= 76021 and itemVnum <= 76022:
		return 1
	elif itemVnum == 79012:
		return 1

	return 0

def IS_AUTO_POTION_SP(itemVnum):
	if 72727 <= itemVnum and 72730 >= itemVnum:
		return 1
	elif itemVnum >= 76004 and itemVnum <= 76005:
		return 1
	elif itemVnum == 79013:
		return 1

	return 0

def IS_BULK_POTION_ALLOWED(itemVnum):
	if not itemVnum:
		return 0
	if IS_AUTO_POTION(itemVnum):
		return 0
	if 27001 <= itemVnum and itemVnum <= 27054:
		return 1
	if 27100 <= itemVnum and itemVnum <= 27127:
		return 1
	if 27863 <= itemVnum and itemVnum <= 27878:
		return 1
	if 39001 <= itemVnum and itemVnum <= 39012:
		return 1
	if 71027 <= itemVnum and itemVnum <= 71035:
		return 1
	if 71044 <= itemVnum and itemVnum <= 71049:
		return 1
	if 50801 <= itemVnum and itemVnum <= 50826:
		return 1
	return 0

def IS_PET_SEAL(itemVnum):
	if not app.ENABLE_PET_SYSTEM_EX:
		return False
	item.SelectItem(itemVnum)
	itemType = item.GetItemType()
	# itemSubType = item.GetItemSubType()
	return item.ITEM_TYPE_PET == itemType

if app.ENABLE_EXCHANGE_LOG or app.ENABLE_CHARACTER_CHEST:
	_game_instance = None
	def GetGameInstance():
		global _game_instance
		return _game_instance
	def SetGameInstance(instance):
		global _game_instance
		if _game_instance:
			del _game_instance
		_game_instance = instance
	def GetInterfaceInstance():
		global _game_instance
		if _game_instance:
			return _game_instance.interface
		return None

if app.ENABLE_WIKI:
	def GetWikiInterface():
		interface = GetInterfaceInstance()
		return interface.wndWiki if interface != None else None
