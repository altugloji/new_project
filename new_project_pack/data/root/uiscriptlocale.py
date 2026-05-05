import app
import pack
import os

AUTOBAN_QUIZ_ANSWER = "ANSWER"
AUTOBAN_QUIZ_REFRESH = "REFRESH"
AUTOBAN_QUIZ_REST_TIME = "REST_TIME"

OPTION_SHADOW = "SHADOW"

CODEPAGE = str(app.GetDefaultCodePage())

if app.__BL_MULTI_LANGUAGE__:
	LOCALE_NAME_DICT = {}
	
	def LoadLocaleFile(srcFileName):
		localeDict = {}
		localeDict["CUBE_INFO_TITLE"] = "Recipe"
		localeDict["CUBE_REQUIRE_MATERIAL"] = "Requirements"
		localeDict["CUBE_REQUIRE_MATERIAL_OR"] = "or"
		
		try:
			lines = open(srcFileName, "r").readlines()
		except IOError:
			import dbg
			dbg.LogBox("LoadUIScriptLocaleError(%(srcFileName)s)" % localeDict)
			app.Abort()

		for line in lines:
			tokens = line[:-1].split("\t")
			
			if len(tokens) >= 2:
				localeDict[tokens[0]] = tokens[1]
				
			else:
				print len(tokens), lines.index(line), line

		globals().update(localeDict)
		
		global LOCALE_NAME_DICT
		LOCALE_NAME_DICT = {
			"ae" : globals()['LANGUAGE_AE'],
			"cz" : globals()['LANGUAGE_CZ'],
			"dk" : globals()['LANGUAGE_DK'],
			"nl" : globals()['LANGUAGE_NL'],
			"en" : globals()['LANGUAGE_EN'],
			"fr" : globals()['LANGUAGE_FR'],
			"de" : globals()['LANGUAGE_DE'],
			"gr" : globals()['LANGUAGE_GR'],
			"hu" : globals()['LANGUAGE_HU'],
			"it" : globals()['LANGUAGE_IT'],
			"pl" : globals()['LANGUAGE_PL'],
			"pt" : globals()['LANGUAGE_PT'],
			"ro" : globals()['LANGUAGE_RO'],
			"ru" : globals()['LANGUAGE_RU'],
			"es" : globals()['LANGUAGE_ES'],
			"tr" : globals()['LANGUAGE_TR'],
		}
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			LOCALE_NAME_DICT["eu"] = globals()['LANGUAGE_ANONYMOUS']

	def ReloadLocaleFile():
		global CODEPAGE
		CODEPAGE = str(app.GetDefaultCodePage())
		
		global __IS_ARABIC
		__IS_ARABIC	= "locale/ae" == app.GetLocalePath()
		
		global LOCALE_UISCRIPT_PATH, LOGIN_PATH, EMPIRE_PATH, GUILD_PATH, SELECT_PATH, WINDOWS_PATH, MAPNAME_PATH
		if app.ENABLE_LOCALE_COMMON and not __IS_ARABIC:
			LOCALE_UISCRIPT_PATH = "locale/common/ui/"
		else:
			LOCALE_UISCRIPT_PATH = "%s/ui/" % (app.GetLocalePath())
		LOGIN_PATH = "%s/ui/login/" % (app.GetLocalePath())
		EMPIRE_PATH = "%s/ui/empire/" % (app.GetLocalePath())
		if app.ENABLE_LOCALE_COMMON and not __IS_ARABIC:
			GUILD_PATH = "locale/common/ui/guild/"
		else:
			GUILD_PATH = "%s/ui/guild/" % (app.GetLocalePath())
		SELECT_PATH = "%s/ui/select/" % (app.GetLocalePath())
		WINDOWS_PATH = "%s/ui/windows/" % (app.GetLocalePath())
		MAPNAME_PATH = "%s/ui/mapname/" % (app.GetLocalePath())
		
		global JOBDESC_WARRIOR_PATH, JOBDESC_ASSASSIN_PATH, JOBDESC_SURA_PATH, JOBDESC_SHAMAN_PATH
		JOBDESC_WARRIOR_PATH = "%s/jobdesc_warrior.txt" % (app.GetLocalePath())
		JOBDESC_ASSASSIN_PATH = "%s/jobdesc_assassin.txt" % (app.GetLocalePath())
		JOBDESC_SURA_PATH = "%s/jobdesc_sura.txt" % (app.GetLocalePath())
		JOBDESC_SHAMAN_PATH = "%s/jobdesc_shaman.txt" % (app.GetLocalePath())
		
		global EMPIREDESC_A, EMPIREDESC_B, EMPIREDESC_C
		EMPIREDESC_A = "%s/empiredesc_a.txt" % (app.GetLocalePath())
		EMPIREDESC_B = "%s/empiredesc_b.txt" % (app.GetLocalePath())
		EMPIREDESC_C = "%s/empiredesc_c.txt" % (app.GetLocalePath())

		global LOCALE_INTERFACE_FILE_NAME
		LOCALE_INTERFACE_FILE_NAME = "%s/locale_interface.txt" % (app.GetLocalePath())
		
		LoadLocaleFile(LOCALE_INTERFACE_FILE_NAME)

		if app.ENABLE_LOCALE_COMMON:
			def TryLoadLocaleFile(filename):
				if pack.Exist(filename) or os.path.exists(filename):
					LoadLocaleFile(filename)
			TryLoadLocaleFile("locale/common/locale_interface_ex.txt")
			TryLoadLocaleFile("%s/locale_interface_ex.txt" % app.GetLocalePath())
else:
	def LoadLocaleFile(srcFileName, localeDict):
		localeDict["CUBE_INFO_TITLE"] = "Recipe"
		localeDict["CUBE_REQUIRE_MATERIAL"] = "Requirements"
		localeDict["CUBE_REQUIRE_MATERIAL_OR"] = "or"

		try:
			lines = open(srcFileName, "r").readlines()
		except IOError:
			import dbg
			dbg.LogBox("LoadUIScriptLocaleError(%(srcFileName)s)" % locals())
			app.Abort()

		for line in lines:
			tokens = line[:-1].split("\t")

			if len(tokens) >= 2:
				localeDict[tokens[0]] = tokens[1]

			else:
				print(len(tokens), lines.index(line), line)

name = app.GetLocalePath()

__IS_ARABIC		= "locale/ae" == app.GetLocalePath()
if app.ENABLE_LOCALE_COMMON and not __IS_ARABIC:
	LOCALE_UISCRIPT_PATH = "locale/common/ui/"
else:
	LOCALE_UISCRIPT_PATH = "%s/ui/" % (name)
LOGIN_PATH = "%s/ui/login/" % (name)
EMPIRE_PATH = "%s/ui/empire/" % (name)
if app.ENABLE_LOCALE_COMMON and not __IS_ARABIC:
	GUILD_PATH = "locale/common/ui/guild/"
else:
	GUILD_PATH = "%s/ui/guild/" % (name)
SELECT_PATH = "%s/ui/select/" % (name)
WINDOWS_PATH = "%s/ui/windows/" % (name)
MAPNAME_PATH = "%s/ui/mapname/" % (name)

JOBDESC_WARRIOR_PATH = "%s/jobdesc_warrior.txt" % (name)
JOBDESC_ASSASSIN_PATH = "%s/jobdesc_assassin.txt" % (name)
JOBDESC_SURA_PATH = "%s/jobdesc_sura.txt" % (name)
JOBDESC_SHAMAN_PATH = "%s/jobdesc_shaman.txt" % (name)
if app.ENABLE_WOLFMAN_CHARACTER:
	JOBDESC_WOLFMAN_PATH = "%s/jobdesc_wolfman.txt" % (name)

EMPIREDESC_A = "%s/empiredesc_a.txt" % (name)
EMPIREDESC_B = "%s/empiredesc_b.txt" % (name)
EMPIREDESC_C = "%s/empiredesc_c.txt" % (name)

LOCALE_INTERFACE_FILE_NAME = "%s/locale_interface.txt" % (name)
if app.__BL_MULTI_LANGUAGE__:
	LoadLocaleFile(LOCALE_INTERFACE_FILE_NAME)
else:
	LoadLocaleFile(LOCALE_INTERFACE_FILE_NAME, locals())
if app.ENABLE_LOCALE_COMMON:
	def TryLoadLocaleFile(filename):
		if pack.Exist(filename) or os.path.exists(filename):
			if app.__BL_MULTI_LANGUAGE__:
				LoadLocaleFile(filename)
			else:
				LoadLocaleFile(filename, globals())
	TryLoadLocaleFile("locale/common/locale_interface_ex.txt")
	TryLoadLocaleFile("%s/locale_interface_ex.txt" % app.GetLocalePath())
