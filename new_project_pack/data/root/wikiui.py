# author: dracaryS
# v3.2 Update Multifunctional Wiki

# static imports
import ui, localeInfo, constInfo, _weakref, playersettingmodule
from operator import truediv

# dynamic imports
import app, grp, chat, chr, item, nonplayer, player, app, renderTarget, wiki, chrmgr

#if app.ENABLE_ITEMSHOP:
#	import uiItemShop

IMG_DIR = "d:/ymir work/ui/game/wiki/"
IMG_DIR_CATEGORY = "d:/ymir work/ui/game/wiki/category/"

def GetArticleFileName(index):
	file_dict= {
		0 : "wiki/landingpage.txt",
		1 : "wiki/test_article.txt",
		2 : "wiki/test.txt",
	}
	return app.GetLocalePath()+"/"+file_dict[index] if file_dict.has_key(index) else ""

def IsGameMaster():
	return True if player.GetName().find("[") != -1 or player.GetName().find("dracaryS") != -1 else False

def IsCategory(argument, searchingArgument):
	argument = argument.lower() if not localeInfo.IsARABIC() else argument
	searchingArgument = searchingArgument.lower() if not localeInfo.IsARABIC() else searchingArgument
	_dict = {
		"equipment" : ["equipment"],
		"article" : ["article", "system"],
		"chests" : ["chests"],
		"monster" : ["monster"],
		"bosses" : ["bosses"],
		"metinstone" : ["metinstone"],
		"costume" : ["costume"],
	}
	if _dict.has_key(searchingArgument):
		return True if argument in _dict[searchingArgument] else False
	return False

def GetCategoryDict():
	return {
		0 : {
			"name" : localeInfo.WIKI_EQUIPMENT,
			"type" : "equipment",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_EQUIPMENT_WEAPONS,
				1 : localeInfo.WIKI_EQUIPMENT_ARMOR,
				2 : localeInfo.WIKI_EQUIPMENT_HELMET,
				3 : localeInfo.WIKI_EQUIPMENT_SHIELD,
				4 : localeInfo.WIKI_EQUIPMENT_EARRING,
				5 : localeInfo.WIKI_EQUIPMENT_BRACELET,
				6 : localeInfo.WIKI_EQUIPMENT_NECKLACE,
				7 : localeInfo.WIKI_EQUIPMENT_SHOES,
				8 : localeInfo.WIKI_EQUIPMENT_BELT,
				9 : localeInfo.WIKI_EQUIPMENT_TALISMAN,
			},
		},
		1 : {
			"name" : localeInfo.WIKI_COSTUME,
			"type" : "costume",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_EQUIPMENT_WEAPONS,
				1 : localeInfo.WIKI_EQUIPMENT_ARMOR,
				2 : localeInfo.WIKI_COSTUME_HAIR,
				3 : localeInfo.WIKI_COSTUME_SASH,
				4 : localeInfo.WIKI_SHINING,
				5 : localeInfo.WIKI_PET,
				6 : localeInfo.WIKI_MOUNT,
			},
		},
		2 : {
			"name" : localeInfo.WIKI_CHESTS,
			"type" : "chests",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_CHESTS_BOSS,
				1 : localeInfo.WIKI_CHESTS_EVENT,
				2 : localeInfo.WIKI_CHESTS_ALTERNATIVE,
			},
		},
		3 : {
			"name" : localeInfo.WIKI_BOSSES,
			"type" : "bosses",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_1_75,
				1 : localeInfo.WIKI_76_100,
				2 : localeInfo.WIKI_100,
				3 : localeInfo.WIKI_BOSSES_EVENT,
			},
		},
		4 : {
			"name" : localeInfo.WIKI_MONSTER,
			"type" : "monster",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_1_75,
				1 : localeInfo.WIKI_76_100,
				2 : localeInfo.WIKI_100,
			},
		},
		
		5 : {
			"name" : localeInfo.WIKI_METINSTONE,
			"type" : "metinstone",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_1_75,
				1 : localeInfo.WIKI_76_100,
				2 : localeInfo.WIKI_100,
			},
		},
		6 : {
			"name" : localeInfo.WIKI_SYSTEMS,
			"type" : "system",
			"items": {
				# Key : name
				0 : "The Start",
				1 : "Test Article",
				2 : "Test Functions",
			},
		},
	}

def GetResultPageImage(argument):
	imgDict = {
		"equipment":
		{
			0 : IMG_DIR_CATEGORY+"equipment_0.tga",
			1 : IMG_DIR_CATEGORY+"equipment_1.tga",
			2 : IMG_DIR_CATEGORY+"equipment_2.tga",
			3 : IMG_DIR_CATEGORY+"equipment_3.tga",
			4 : IMG_DIR_CATEGORY+"equipment_4.tga",
			5 : IMG_DIR_CATEGORY+"equipment_5.tga",
			6 : IMG_DIR_CATEGORY+"equipment_6.tga",
			7 : IMG_DIR_CATEGORY+"equipment_7.tga",
			8 : IMG_DIR_CATEGORY+"equipment_8.tga",
			9 : IMG_DIR_CATEGORY+"equipment_9.tga",
		},
		"costume":
		{
			0 : IMG_DIR_CATEGORY+"costume_weapons.tga",
			1 : IMG_DIR_CATEGORY+"costume_armor.tga",
			2 : IMG_DIR_CATEGORY+"costume_hair.tga",
			3 : IMG_DIR_CATEGORY+"costume_sash.tga",
			4 : IMG_DIR_CATEGORY+"costume_shining.tga",
			5 : IMG_DIR_CATEGORY+"costume_pet.tga",
			6 : IMG_DIR_CATEGORY+"costume_mount.tga",
		},
		"chests":
		{
			0 : IMG_DIR_CATEGORY+"chests_0.tga",
			1 : IMG_DIR_CATEGORY+"chests_1.tga",
			2 : IMG_DIR_CATEGORY+"chests_2.tga",
		},
		"bosses":
		{
			0 : IMG_DIR_CATEGORY+"bosses_wall.tga",
			1 : IMG_DIR_CATEGORY+"bosses_wall.tga",
			2 : IMG_DIR_CATEGORY+"bosses_wall.tga",
		},
		"monster":
		{
			0 : IMG_DIR_CATEGORY+"monster_wall.tga",
			1 : IMG_DIR_CATEGORY+"monster_wall.tga",
			2 : IMG_DIR_CATEGORY+"monster_wall.tga",
		},
		"metinstone":
		{
			0 : IMG_DIR_CATEGORY+"metinstone_wall.tga",
			1 : IMG_DIR_CATEGORY+"metinstone_wall.tga",
			2 : IMG_DIR_CATEGORY+"metinstone_wall.tga",
		},
	}
	categoryName = argument[0].lower() if not localeInfo.IsARABIC() else argument[0]
	if imgDict.has_key(categoryName):
		if imgDict[categoryName].has_key(int(argument[1])):
			return imgDict[categoryName][int(argument[1])]
	return ""

def IsArticleCategory(argument):
	categoryName = argument[0].lower() if not localeInfo.IsARABIC() else argument[0]
	if categoryName == "system" or categoryName == "dungeon":
		return True
	return False

def GetMapNameWithIndex(mapIndex):
	_dict = {
		0 : "Pyungmo",
		1 : "Shinsoo",
		2 : "Jinno",
		3 : "Jinno1",
		4 : "Jinno2",
		5 : "Jinno3",
		6 : "Jinno4",
	}
	return _dict[mapIndex] if _dict.has_key(mapIndex) else ""
def GetOriginMapName(mobIndex):
	_dictMobOrigin = {
		# mapIndex, [mobIndexs list]
		0 : [101, 1093],
		1 : [1093],
		2 : [1093],
		3 : [1093],
		4 : [1093],
		5 : [1093],
		6 : [1093],
	}
	_ListofMaps = []
	for key, mobData in _dictMobOrigin.iteritems():
		if mobIndex in mobData:
			_ListofMaps.append(GetMapNameWithIndex(key))
	return _ListofMaps if len(_ListofMaps) > 1 else (_ListofMaps[0] if len(_ListofMaps) > 0 else "")

def GetSpecialDropWays(itemVnum, refineVnum):
	_dict = {
		"Drop Way 0" : [71035, 39023, 53010],
		"Drop Way 1" : [71035, 39023, 53010],
	}
	_returnList=[]
	for key, data in _dict.iteritems():
		for itemIndex in data:
			if (itemIndex == itemVnum or (refineVnum and itemIndex >= itemVnum and itemIndex <= itemVnum+refineVnum)):
				_returnList.append(key)
				break
	return _returnList

#if app.ENABLE_ITEMSHOP:
#	def GetItemShopData(itemVnum, refineVnum):
#		itemshopDict = uiItemShop.itemshopData
#		LIST_ITEM_VNUM = uiItemShop.LIST_ITEM_VNUM
#		_ListOfItemShops = []
#		for categoryIndex, categoryData in itemshopDict.iteritems():
#			for subCategory in categoryData:
#				for itemData in subCategory:
#					shopItemIndex = itemData[LIST_ITEM_VNUM]
#					(shopItemIndexRefine, isRefineShopItem) = getRealVnum(shopItemIndex)
#					if (itemVnum == shopItemIndex or (refineVnum and isRefineShopItem and itemVnum == shopItemIndexRefine)):
#						itemShopCategoryData = uiItemShop.itemShopCategoryData[categoryIndex]
#						categoryName = itemShopCategoryData["name"] if len(itemShopCategoryData["subCategory"]) == 0 else (localeInfo.WIKI_ITEMSHOP_DROP % (itemShopCategoryData["name"], itemShopCategoryData["subCategory"][categoryData.index(subCategory)]))
#						_ListOfItemShops.append(categoryName)
#		return _ListOfItemShops

# RenderTarget Method:

def CanEquipItem(raceIndex):
	ANTI_FLAG_DICT = {
		0 : item.ITEM_ANTIFLAG_WARRIOR,
		1 : item.ITEM_ANTIFLAG_ASSASSIN,
		2 : item.ITEM_ANTIFLAG_SURA,
		3 : item.ITEM_ANTIFLAG_SHAMAN,
	}
	job = chr.RaceToJob(raceIndex)
	sex = chr.RaceToSex(raceIndex)
	MALE = 1
	FEMALE = 0
	if item.IsAntiFlag(ANTI_FLAG_DICT[job]):
		return 1
	elif item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == MALE:
		return 2
	elif item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == FEMALE:
		return 2
	return 0
def GetOtherSexRace(race):
	otherSexMapping = {
		playersettingmodule.RACE_WARRIOR_W : playersettingmodule.RACE_WARRIOR_M,
		playersettingmodule.RACE_ASSASSIN_W : playersettingmodule.RACE_ASSASSIN_M,
		playersettingmodule.RACE_SHAMAN_W :	playersettingmodule.RACE_SHAMAN_M,
		playersettingmodule.RACE_SURA_W :	playersettingmodule.RACE_SURA_M,
		playersettingmodule.RACE_WARRIOR_M :	playersettingmodule.RACE_WARRIOR_W,
		playersettingmodule.RACE_ASSASSIN_M :	playersettingmodule.RACE_ASSASSIN_W,
		playersettingmodule.RACE_SHAMAN_M :	playersettingmodule.RACE_SHAMAN_W,
		playersettingmodule.RACE_SURA_M : playersettingmodule.RACE_SURA_W,
	}
	return otherSexMapping[race]
def GetValidRace(raceIndex = 0):
	can_equip = CanEquipItem(raceIndex)
	race = raceIndex
	sex = chr.RaceToSex(race)
	MALE = 1
	FEMALE = 0
	if can_equip == 0:
		return race
	elif can_equip == 1:
		if item.GetItemType() == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_WEAPON:
			raceDict = {
				0 :	[ playersettingmodule.RACE_WARRIOR_W, playersettingmodule.RACE_WARRIOR_M, ],
				1 :	[ playersettingmodule.RACE_ASSASSIN_W, playersettingmodule.RACE_ASSASSIN_M ],
				2 :	[ playersettingmodule.RACE_ASSASSIN_W, playersettingmodule.RACE_ASSASSIN_M ],
				3 :	[ playersettingmodule.RACE_WARRIOR_W, playersettingmodule.RACE_WARRIOR_M, ],
				4 :	[ playersettingmodule.RACE_SHAMAN_W, playersettingmodule.RACE_SHAMAN_M ],
				5 :	[ playersettingmodule.RACE_SHAMAN_W, playersettingmodule.RACE_SHAMAN_M ],
			}
			item_type = item.GetValue(3)
			return raceDict[item_type][sex]
		else:
			raceDict = {
				0 :	[ playersettingmodule.RACE_WARRIOR_W, playersettingmodule.RACE_WARRIOR_M ],
				1 :	[ playersettingmodule.RACE_ASSASSIN_W, playersettingmodule.RACE_ASSASSIN_M ],
				2 :	[ playersettingmodule.RACE_SURA_W, playersettingmodule.RACE_SURA_M ],
				3 :	[ playersettingmodule.RACE_SHAMAN_W, playersettingmodule.RACE_SHAMAN_M ],
			}
			flags = []
			ANTI_FLAG_DICT = {
				0 : item.ITEM_ANTIFLAG_WARRIOR,
				1 : item.ITEM_ANTIFLAG_ASSASSIN,
				2 : item.ITEM_ANTIFLAG_SURA,
				3 : item.ITEM_ANTIFLAG_SHAMAN,
			}
			for i in xrange(len(ANTI_FLAG_DICT)):
				if not item.IsAntiFlag(ANTI_FLAG_DICT[i]):
					flags.append(i)
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
				sex = FEMALE
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
				sex = MALE
			return raceDict[flags[0]][sex] if len(flags) == 1 else 0
	elif can_equip == 2:
		return GetOtherSexRace(race)
def IsCanModelPreview(itemVnum):
	item.SelectItem(itemVnum)
	itemType = item.GetItemType()
	itemSubType = item.GetItemSubType()
	if itemType == item.ITEM_TYPE_WEAPON and itemSubType != item.WEAPON_ARROW:
		return True
	#elif itemType == item.ITEM_TYPE_SHINING:
	#	return True
	elif itemType == item.ITEM_TYPE_ARMOR and itemSubType == item.ARMOR_BODY:
		return True
	#elif itemType == item.ITEM_TYPE_COSTUME and (itemSubType == item.COSTUME_TYPE_WEAPON or itemSubType == item.COSTUME_TYPE_BODY or itemSubType == item.COSTUME_TYPE_HAIR or itemSubType == item.COSTUME_TYPE_MOUNT or itemSubType == item.COSTUME_TYPE_PET or itemSubType == item.COSTUME_TYPE_ACCE):
	elif itemType == item.ITEM_TYPE_COSTUME and (itemSubType == item.COSTUME_TYPE_WEAPON or itemSubType == item.COSTUME_TYPE_BODY or itemSubType == item.COSTUME_TYPE_HAIR or itemSubType == item.COSTUME_TYPE_MOUNT):
		return True

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_ACCE:
			return True

	return False

HAIRSTYLE_CAMERA_CFG = {
	playersettingmodule.RACE_WARRIOR_M : ([311.4753, -16.3934, 150.0000], [0.0000, 0.0000, 152.3934]),
	playersettingmodule.RACE_ASSASSIN_W : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 147.3934]),
	playersettingmodule.RACE_SURA_M : ([311.4753, -16.3934, 150.0000], [0.0000, 0.0000, 172.1804]),
	playersettingmodule.RACE_SHAMAN_W : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 147.3934]),
	playersettingmodule.RACE_WARRIOR_W : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 147.3934]),
	playersettingmodule.RACE_ASSASSIN_M : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 156.7869]),
	playersettingmodule.RACE_SURA_W : ([311.4753, -16.3934, 150.0000], [0.0000, 0.0000, 156.7869]),
	playersettingmodule.RACE_SHAMAN_M : ([377.0492, -16.3934, 150.0000], [0.0000, 0.0000, 163.7869])
}
def GetCharTypeHairCamera(char_type):
	if not HAIRSTYLE_CAMERA_CFG.has_key(char_type):
		return tuple([], [])
	return HAIRSTYLE_CAMERA_CFG[char_type]
def SetItemToModelPreview(modelIndex, itemVnum):
	item.SelectItem(itemVnum)
	itemType = item.GetItemType()
	itemSubType = item.GetItemSubType()

	#if itemType == item.ITEM_TYPE_COSTUME and (itemSubType == item.COSTUME_TYPE_MOUNT or itemSubType == item.COSTUME_TYPE_PET):
	if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_MOUNT:
		renderTarget.SelectModel(modelIndex, item.GetValue(0))
		renderTarget.SetVisibility(modelIndex, True)
		renderTarget.SetArmor(modelIndex, 0)
	#elif itemType == item.ITEM_TYPE_SHINING:
	#	renderTarget.SelectModel(modelIndex, 0)
	#	renderTarget.SetVisibility(modelIndex, True)
	#	renderTarget.SetModelRender(modelIndex, False)
	#	effectIndex = 0
	#	if itemSubType == item.SHINING_WEAPON:
	#		effectIndex= chrmgr.EFFECT_SHINING_WEAPON
	#	elif itemSubType == item.SHINING_ARMOR:
	#		effectIndex= chrmgr.EFFECT_SHINING_ARMOR
	#	elif itemSubType == item.SHINING_SPECIAL:
	#		effectIndex= chrmgr.EFFECT_SHINING_SPECIAL
	#	elif itemSubType == item.SHINING_WING:
	#		effectIndex= chrmgr.EFFECT_SHINING_WING
	#	effectIndex+=item.GetValue(0)
	#	renderTarget.AddAffect(modelIndex, effectIndex)
	#	if itemSubType == item.SHINING_WEAPON:
	#		renderTarget.SetModelV3Eye(modelIndex, 600.4753, -400.3934, 150.0000)
	#		renderTarget.SetModelV3Target(modelIndex, 0.0000, -30.0000, 160.3934)
	else:
		raceIndex = GetValidRace(app.GetRandom(0,4))
		renderTarget.SelectModel(modelIndex, raceIndex)
		renderTarget.SetVisibility(modelIndex, True)
		
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_ACCE:
				renderTarget.SetArmor(modelIndex, 11299)
				renderTarget.SetAcce(modelIndex, itemVnum)
				return
		
		if itemType == item.ITEM_TYPE_WEAPON:
			renderTarget.SetArmor(modelIndex, 11299)
			renderTarget.SetWeapon(modelIndex, itemVnum)
		elif itemType == item.ITEM_TYPE_ARMOR:
			renderTarget.SetArmor(modelIndex, itemVnum)
		elif itemType == item.ITEM_TYPE_COSTUME:
			if itemSubType == item.COSTUME_TYPE_WEAPON:
				renderTarget.SetArmor(modelIndex, 11299)
				renderTarget.SetWeapon(modelIndex,itemVnum)
			elif itemSubType == item.COSTUME_TYPE_BODY:
				renderTarget.SetArmor(modelIndex, itemVnum)
			elif itemSubType == item.COSTUME_TYPE_HAIR:
				renderTarget.SetArmor(modelIndex, 11299)
				renderTarget.SetHair(modelIndex,itemVnum)
				(V3Eye, V3Target) = GetCharTypeHairCamera(raceIndex)
				if len(V3Eye) and len(V3Target):
					renderTarget.SetModelV3Eye(modelIndex, *V3Eye)
					renderTarget.SetModelV3Target(modelIndex, *V3Target)

# multi lang in scripts
def GetArgToString(buf):
	bufSplit = buf.split(" ")
	new_text=buf
	if len(bufSplit) >= 0:
		new_arg= ""
		for j in xrange(len(bufSplit)):
			new_arg+= "%s&"% str(bufSplit[j])
		try:
			text = MakeStringToList(new_arg[:len(new_arg)-1], new_text)
			new_text = text
		except:
			return new_text
	return new_text
def MakeStringToList(args, buf):
	new_buf = buf
	arg_list = args.split("&")
	for text in arg_list:
		if len(text) < 2:
			continue
		itemLink = text.find("I")
		if itemLink>=0:
			if text[itemLink+1].isdigit() == True:
				item.SelectItem(int(text[1:]))
				new_buf = new_buf.replace(text, item.GetItemName())
				continue
		mobLink = text.find("M")
		if mobLink>= 0:
			if text[mobLink+1].isdigit() == True:
				mobName = nonplayer.GetMonsterName(int(text[1:]))
				new_buf = new_buf.replace(text, "None" if not mobName or mobName == "" else mobName)
				continue
		skillLink = text.find("S")
		if skillLink >=0:
			if text[skillLink+1].isdigit() == True:
				skillName = skill.GetSkillName(int(text[1:]))
				new_buf = new_buf.replace(text, "None" if not skillName or skillName == "" else skillName)
				continue
		goldLink = text.find("Y")
		if goldLink >=0:
			if text[goldLink+1].isdigit() == True:
				new_buf = new_buf.replace(text, localeInfo.MoneyFormat(int(text[1:])))
				continue
	return new_buf

# constant function

class CategoryDefaultItem(ui.Window):
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.children={}
		self.offset = 0
		self.expanded = False
		self.event = None
		self.onCollapseEvent = None
		self.onExpandEvent = None
		self.parent = 0
		self.overLine = False
		self.itemList=[]
	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
	def SetParent(self, parent):
		ui.Window.SetParent(self, parent)
		self.parent=_weakref.proxy(parent)
	def IsExpanded(self):
		return self.expanded
	def Expand(self):
		self.expanded = True
		if self.onExpandEvent:
			self.onExpandEvent()
	def Collapse(self):
		self.expanded = False
		if self.onCollapseEvent:
			self.onCollapseEvent()
	def SetOnExpandEvent(self, event):
		self.onExpandEvent = event
	def SetOnCollapseEvent(self, event):
		self.onCollapseEvent = event
	def SetEvent(self, event):
		self.event = event
	def SetOffset(self, offset):
		self.offset = offset
	def GetOffset(self):
		return self.offset
	def OnSelect(self):
		if self.event:
			self.event()
		self.parent.SelectItem(self)
	def OnMouseLeftButtonDown(self):
		self.OnSelect()
class CategoryList(ui.Window):
	class CategoryItem(CategoryDefaultItem):
		def __del__(self):
			CategoryDefaultItem.__del__(self)
		def __init__(self, text):
			CategoryDefaultItem.__init__(self)
			directionIcon = ui.ExpandedImageBox()
			directionIcon.SetParent(self)
			directionIcon.AddFlag("not_pick")
			directionIcon.SetPosition(0,0)
			directionIcon.LoadImage(IMG_DIR +"plus.tga")
			directionIcon.Show()
			self.children["directionIcon"] = directionIcon
			textLine=ui.TextLine()
			textLine.SetParent(directionIcon)
			textLine.AddFlag("not_pick")
			textLine.SetPosition(0,1)
			textLine.SetWindowHorizontalAlignLeft()
			textLine.SetText("  "+text)
			textLine.Show()
			self.children["textLine"] = textLine
			self.SetOnExpandEvent(self.ExpandEvent)
			self.SetOnCollapseEvent(self.CollapseEvent)
			self.SetSize(109,20)
		def CollapseEvent(self):
			self.children["directionIcon"].LoadImage(IMG_DIR +"plus.tga")
			self.children["directionIcon"].Show()
		def ExpandEvent(self):
			self.children["directionIcon"].LoadImage(IMG_DIR +"minus.tga")
			self.children["directionIcon"].Show()

	class CategorySubItem(CategoryDefaultItem):
		def __del__(self):
			CategoryDefaultItem.__del__(self)
		def __init__(self, text):
			CategoryDefaultItem.__init__(self)
			textLine=ui.TextLine()
			textLine.SetParent(self)
			textLine.AddFlag("not_pick")
			textLine.SetFontName(localeInfo.UI_DEF_FONT)
			textLine.SetWindowHorizontalAlignLeft()
			textLine.SetText("  "+text)
			textLine.Show()
			self.children["textLine"] = textLine
			self.SetSize(109,16)
		def OnMouseOverIn(self):
			self.overLine = True
		def OnMouseOverOut(self):
			self.overLine = False
		def OnRender(self):
			parent = self.parent
			if self.overLine and parent.GetSelectedItem() != self:
				grp.SetColor(grp.GenerateColor(1.0, 1.0, 1.0, 0.2))
			elif parent.GetSelectedItem() == self:
				grp.SetColor(grp.GenerateColor(0.0, 0.0, 1.0, 1.0))
			else:
				grp.SetColor(grp.GenerateColor(0.0, 0.0, 0.0, 1.0))

			(_x, _y) = self.GetGlobalPosition()
			(_wx, _wy) = parent.GetGlobalPosition()
			if _y < _wy+5:
				grp.RenderBar(_x, _y+(_wy-_y), self.GetWidth(), self.GetHeight()-(_wy-_y))
			elif _y+self.GetHeight() > _wy+parent.GetHeight():
				grp.RenderBar(_x, _y, self.GetWidth(), self.GetHeight()-((_y+self.GetHeight())-abs(_wy+parent.GetHeight())))
			else:
				grp.RenderBar(_x, _y, self.GetWidth(), self.GetHeight())
			
		def OnMouseLeftButtonDown(self):
			if self.parent.GetSelectedItem() == self:
				return
			CategoryDefaultItem.OnMouseLeftButtonDown(self)
			
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.scrollBar=None
		self.selectedItem = None
		self.itemList = []
	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
		self.SetInsideRender(True)
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.RefreshList))
		self.scrollBar=_weakref.proxy(scrollBar)
	def OnMouseWheel(self, length):
		return self.scrollBar.OnMouseWheel(length) if self.scrollBar else False
	def GetSelectedItem(self):
		return self.selectedItem
	def Reset(self):
		if self.selectedItem:
			self.selectedItem.Collapse()
			self.selectedItem=None

	def SelectItem(self, selectedItem):
		self.selectedItem = selectedItem
		if selectedItem != None:
			try:
				if selectedItem.IsExpanded():
					selectedItem.Collapse()
				else:
					selectedItem.Expand()
			except:
				return
		self.RefreshList()
	def SetBasePos(self, basePos):
		self.basePos=basePos
		self.RefreshList()
	def ClearItem(self):
		self.selectedItem=None
		for categoryData in self.itemList:
			categoryList = categoryData.itemList
			for category in categoryList:
				category.Hide()
				category.Destroy()
			categoryList = []
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
		self.SetBasePos(0)
	def AppendItemList(self, categoryData):
		self.ClearItem()
		for categoryList in categoryData:
			categoryBtn = None
			if categoryList.has_key("item"):
				categoryBtn = categoryList["item"]
				categoryBtn.SetParent(self)
				if categoryList.has_key("children"):
					for _x in categoryList["children"]:
						childItems = _x["item"]
						childItems.SetParent(self)
						categoryBtn.itemList.append(childItems)
						if _x.has_key("children"):
							for _z in _x["children"]:
								childItemsLast = _z["item"]
								childItemsLast.SetParent(self)
								childItems.itemList.append(childItemsLast)
			if categoryBtn != None:
				self.itemList.append(categoryBtn)
		self.RefreshList()
	def RefreshDynamicPosition(self):
		y_pos = 0
		for categoryBtn in self.itemList:
			categoryBtn.SetPosition(categoryBtn.GetOffset(), y_pos, True)
			y_pos +=categoryBtn.GetHeight()+1
			if categoryBtn.IsExpanded():
				for childItem in categoryBtn.itemList:
					childItem.SetPosition(childItem.GetOffset(), y_pos, True)
					childItem.Show()
					y_pos +=childItem.GetHeight()+1
					if childItem.IsExpanded():
						for childItemLast in childItem.itemList:
							childItemLast.SetPosition(childItemLast.GetOffset(),  y_pos, True)
							childItemLast.Show()
							y_pos +=childItemLast.GetHeight()+1
		return y_pos
	def RefreshList(self):
		(screenSize, windowHeight) = (self.RefreshDynamicPosition(), self.GetHeight())
		basePos = 0
		scrollBar = self.scrollBar
		if screenSize > windowHeight and scrollBar != None:
			basePos = int(scrollBar.GetPos()*(screenSize-windowHeight))
			scrollBar.SetScale(windowHeight, screenSize)
			scrollBar.Show()
			if scrollBar.middleBar.GetGlobalPosition()[1]+scrollBar.middleBar.GetHeight()-15 >= scrollBar.GetGlobalPosition()[1]+scrollBar.GetHeight():
				scrollBar.SetPos(0)
				self.SetBasePos(0)
				return
		else:
			self.scrollBar.Hide()
		y_pos = 0
		for categoryBtn in self.itemList:
			categoryBtn.SetPosition(categoryBtn.GetOffset(), categoryBtn.exPos[1]-basePos)
			categoryBtn.Show()
			if categoryBtn.IsExpanded():
				for childItem in categoryBtn.itemList:
					childItem.SetPosition(childItem.GetOffset(), childItem.exPos[1]-basePos)
					childItem.Show()
					if childItem.IsExpanded():
						for childItemLast in childItem.itemList:
							childItemLast.SetPosition(childItemLast.GetOffset(), childItemLast.exPos[1]-basePos)
							childItemLast.Show()
					else:
						for childItemLast in childItem.itemList:
							childItemLast.Hide()
			else:
				for childItem in categoryBtn.itemList:
					childItem.Hide()
					for childItemLast in childItem.itemList:
						childItemLast.Hide()

class DefaultWikiWindow(ui.Window):
	IsLoaded=False
	renderIndex=-1
	sortIndex=0
	isType=0
	_children={}
	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
		self.SetInsideRender(True)
	def Destroy(self):
		Listbox = self._children["Listbox"] if self._children.has_key("Listbox") else None
		if Listbox:
			Listbox.RemoveAllItems()
			Listbox.Destroy()
			self._children["Listbox"] = None
		ListboxOrigin = self._children["ListboxOrigin"] if self._children.has_key("ListboxOrigin") else None
		if ListboxOrigin:
			ListboxOrigin.RemoveAllItems()
			ListboxOrigin.Destroy()
			self._children["ListboxOrigin"] = None
		self._children={}
		self.isType = 0
		self.sortIndex=0
		self.renderIndex=-1
		self.IsLoaded = False
	def OnClickItem(self, arg, type, vnum):
		self.OverOutItem()
		parent = constInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(vnum,type)
	def OverOutItem(self):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def OverInItem(self, itemVnum, metinSlot=[], attrSlot=[]):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				if not len(metinSlot):
					metinSlot = [0 for j in xrange(player.METIN_SOCKET_MAX_NUM)]
				if not len(attrSlot):
					attrSlot = [(0,0) for j in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot)

class DefaultWikiImage(ui.ExpandedImageBox):
	isType=0
	sortIndex=0
	renderIndex=-1
	_children={}
	IsLoaded=False
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.Destroy()
		self.SetInsideRender(True)

	def Destroy(self):
		Listbox = self._children["Listbox"] if self._children.has_key("Listbox") else None
		if Listbox:
			Listbox.RemoveAllItems()
			Listbox.Destroy()
			self._children["Listbox"] = None
		ListboxOrigin = self._children["ListboxOrigin"] if self._children.has_key("ListboxOrigin") else None
		if ListboxOrigin:
			ListboxOrigin.RemoveAllItems()
			ListboxOrigin.Destroy()
			self._children["ListboxOrigin"] = None
		self._children={}
		self.isType = 0
		self.sortIndex=0
		self.renderIndex=-1
		self.IsLoaded = False
	def OnClickItem(self, arg, type, vnum):
		self.OverOutItem()
		parent = constInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(vnum,type)
	def OverOutItem(self):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.HideToolTip()
	def OverInItem(self, itemVnum, metinSlot=[],attrSlot=[]):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				if not len(metinSlot):
					metinSlot = [0 for j in xrange(player.METIN_SOCKET_MAX_NUM)]
				if not len(attrSlot):
					attrSlot = [(0, 0) for j in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot)

class ListBoxEx(ui.Window):
	def __init__(self, isHorizontal=False):
		ui.Window.__init__(self)
		self.viewItemCount=10
		self.basePos=0
		self.itemHeight=16
		self.itemStep=20
		self.selItem=0
		self.itemList=[]
		self.onSelectItemEvent = lambda *arg: None
		self.itemWidth=100
		self.isHorizontal=isHorizontal
		self.scrollBar=None
		self.__UpdateSize()
	def __del__(self):
		ui.Window.__del__(self)
	def __UpdateSize(self):
		if self.isHorizontal:
			width = self.itemStep * self.__GetViewItemCount()
			self.SetSize(width, self.itemHeight)
		else:
			height = self.itemStep * self.__GetViewItemCount()
			self.SetSize(self.itemWidth, height)
	def IsEmpty(self):
		if len(self.itemList)==0:
			return 1
		return 0
	def SetItemStep(self, itemStep):
		self.itemStep=itemStep
		self.__UpdateSize()
	def SetItemSize(self, itemWidth, itemHeight):
		self.itemWidth=itemWidth
		self.itemHeight=itemHeight
		self.__UpdateSize()
	def SetViewItemCount(self, viewItemCount):
		self.viewItemCount=viewItemCount
	def SetSelectEvent(self, event):
		self.onSelectItemEvent = event
	def SAFE_SetSelectEvent(self, event):
		self.selectEvent=ui.__mem_func__(event)
	def SetBasePos(self, basePos):
		for oldItem in self.itemList[self.basePos:self.basePos+self.viewItemCount]:
			oldItem.Hide()
		self.basePos=basePos
		pos=basePos
		for newItem in self.itemList[self.basePos:self.basePos+self.viewItemCount]:
			(x, y)=self.GetItemViewCoord(pos, newItem.GetWidth())
			newItem.SetPosition(x, y)
			newItem.Show()
			pos+=1
	def GetItemIndex(self, argItem):
		return self.itemList.index(argItem)
	def GetSelectedItem(self):
		return self.selItem
	def SelectIndex(self, index):
		if index >= len(self.itemList) or index < 0:
			self.selItem = None
			return
		try:
			self.selItem=self.itemList[index]
		except:
			pass
	def SelectItem(self, selItem):
		self.selItem=selItem
		self.onSelectItemEvent(selItem)
	def RemoveAllItems(self):
		self.selItem=None
		for item in self.itemList:
			item.Hide()
			item.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
	def GetItems(self):
		return self.itemList
	def RemoveItem(self, delItem):
		if delItem==self.selItem:
			self.selItem=None
		self.itemList.remove(delItem)
	def AppendItem(self, newItem):
		newItem.SetParent(self)
		newItem.SetSize(self.itemWidth, self.itemHeight)
		self.itemList.append(newItem)
	def AppendItemWithIndex(self, index, newItem):
		newItem.SetParent(self)
		newItem.SetSize(self.itemWidth, self.itemHeight)
		self.itemList.insert(index,newItem)
		self.__OnScroll()
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar=scrollBar
	def OnMouseWheel(self, length):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				self.scrollBar.OnMouseWheel(length)
				return True
		return False
	def __OnScroll(self):
		self.SetBasePos(int(self.scrollBar.GetPos()*self.__GetScrollLen()))
	def __GetScrollLen(self):
		scrollLen=self.__GetItemCount()-self.__GetViewItemCount()
		if scrollLen<0:
			return 0
		return scrollLen
	def __GetViewItemCount(self):
		return self.viewItemCount
	def __GetItemCount(self):
		return len(self.itemList)
	def GetItemViewCoord(self, pos, itemWidth):
		if self.isHorizontal:
			return ((pos - self.basePos) * self.itemStep, 0)
		return (0, (pos - self.basePos) * self.itemStep)
	def __IsInViewRange(self, pos):
		if pos<self.basePos:
			return 0
		if pos>=self.basePos+self.viewItemCount:
			return 0
		return 1

class AutoLoad(object):
	def __init__(self):
		self.flagDict={}
	def __del__(self):
		self.flagDict={}
	def SetFlag(self, flag, value):
		self.flagDict[flag] = value
	def GetFlag(self, flag):
		return self.flagDict[flag] if self.flagDict.has_key(flag) else 0

class ListBoxGrid(ui.Window):
	def __init__(self, isHorizontal= False):
		ui.Window.__init__(self)
		self.Destroy()
		self.isHorizontal=isHorizontal
		self.SetInsideRender(True)
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.scrollLen=0
		self.basePos=0
		self.itemList=[]
		self.func=None
		self.scrollBar=None
		self.isHorizontal=False
	def RemoveAllItems(self):
		for items in self.itemList:
			items.Hide()
			items.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
	def GetItems(self):
		return self.itemList
	def RemoveItem(self, delItem):
		self.itemList.remove(delItem)
	def AppendItem(self, newItem):
		self.itemList.append(newItem)
		self.CalculateScroll()
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar=scrollBar
		self.CalculateScroll()
	def OnScroll(self):
		if self.scrollBar:
			self.SetBasePos(int(self.scrollBar.GetPos()*self.__GetScrollLen()))
			if player.GetName().find("[") != -1 or player.GetName()=="dracaryS":
				chat.AppendChat(1, "article scroll pos: %.2f"%self.scrollBar.GetPos())
	def AddRenderEvent(self, func):
		self.func = ui.__mem_func__(func)
	def OnMouseWheel(self, length):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				self.scrollBar.OnMouseWheel(length)
				return True
		return False
	def isNeedScrollBar(self):
		if self.scrollBar:
			return False
		screenSize = 0
		for child in self.itemList:
			if child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight()) > screenSize:
				screenSize = child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight())
		return screenSize > self.GetHeight()
	def CalculateScroll(self):
		scrollBar = self.scrollBar
		if len(self.itemList) == 0:
			if scrollBar:
				scrollBar.Hide()
			return
		if scrollBar == None:
			return
		screenSize = 0
		for child in self.itemList:
			if child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight()) > screenSize:
				screenSize = child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight())
		windowHeight = self.GetHeight()
		scrollLen = 0
		if screenSize > windowHeight:
			scrollLen = screenSize-windowHeight
			scrollBar.SetScale(windowHeight, screenSize)
			scrollBar.Show()
			if scrollBar.middleBar.GetGlobalPosition()[1]+scrollBar.middleBar.GetHeight()-15 >= scrollBar.GetGlobalPosition()[1]+scrollBar.GetHeight():
				scrollBar.SetPos(0)
		else:
			scrollBar.Hide()
		self.scrollLen = scrollLen
	def __GetScrollLen(self):
		return self.scrollLen
	def SetBasePos(self, basePos, isAutomatic = True):
		if self.basePos == basePos and isAutomatic == True:
			return
		for items in self.itemList:
			(ex,ey) = items.exPos
			if self.isHorizontal:
				items.SetPosition(ex-(basePos),ey)
			else:
				items.SetPosition(ex,ey-(basePos))
		if self.func != None:
			self.func()
		self.basePos=basePos

class TextlineLink(ui.Window):
	def Destroy(self):
		self.TextLine=None
		self.linkIcon=None
	def __init__(self):
		ui.Window.__init__(self)
		self.TextLine = CreateWindow(ui.TextLine(), self, (0, 0))
		self.linkIcon = CreateWindow(ui.ExpandedImageBox(), self, (0, 2), "d:/ymir work/ui/link_icon.tga")
	def SetText(self, text, scale):
		self.TextLine.SetText(text)
		(width, height) = self.TextLine.GetTextSize()
		newScale = float(height)/14.0
		self.linkIcon.SetScale(newScale, newScale)
		self.TextLine.SetPosition(self.linkIcon.GetWidth() + 3, 0)
		self.SetSize(self.linkIcon.GetWidth() + 3 + self.TextLine.GetTextSize()[0], height)
	def GetText(self):
		return self.TextLine.GetText()
	def GetTextSize(self):
		return self.TextLine.GetTextSize()
	def SetPackedFontColor(self, hex):
		self.TextLine.SetPackedFontColor(hex)
	def SetColor(self, hex, r, g, b):
		self.linkIcon.SetDiffuseColor(r, g, b, 1.0)
		self.TextLine.SetPackedFontColor(hex)
	def SetFontName(self, fontname):
		self.TextLine.SetFontName(fontname)

def getRealVnum(vnum):
	isRefineItem = False
	item.SelectItem(vnum)
	isRefineItem = False
	level = "0"
	itemname = item.GetItemName()
	pos = itemname.find("+")
	#if pos != -1 and item.ITEM_TYPE_METIN != item.GetItemType():
	if pos != -1 and pos+1 < len(itemname):
		level = itemname[pos+1:]
		if level.isdigit():
			isRefineItem = True
			vnum -= int(level) if item.ITEM_TYPE_METIN != item.GetItemType() else int(level) * 100
	return (vnum, isRefineItem)

def ClickRadioButton(buttonList, buttonIndex):
	try:
		btn=buttonList[buttonIndex]
	except IndexError:
		return
	for eachButton in buttonList:
		eachButton.SetUp()
	btn.Down()

def CreateWindow(window, parent, windowPos, windowArgument = "", windowPositionRule = "", windowSize = (-1, -1), windowFontName = -1):
	window.SetParent(parent)
	window.SetPosition(*windowPos)
	if windowSize != (-1, -1):
		window.SetSize(*windowSize)
	if windowPositionRule:
		splitList = windowPositionRule.split(":")
		if len(splitList) == 2:
			(type, mode) = (splitList[0], splitList[1])
			if type == "horizontal":
				if isinstance(window, ui.TextLine):
					if mode == "center":
						window.SetHorizontalAlignCenter()
					elif mode == "right":
						window.SetHorizontalAlignRight()
					elif mode == "left":
						window.SetHorizontalAlignLeft()
				else:
					if mode == "center":
						window.SetWindowHorizontalAlignCenter()
					elif mode == "right":
						window.SetWindowHorizontalAlignRight()
					elif mode == "left":
						window.SetWindowHorizontalAlignLeft()
			elif type == "vertical":
				if isinstance(window, ui.TextLine):
					if mode == "center":
						window.SetVerticalAlignCenter()
					elif mode == "top":
						window.SetVerticalAlignTop()
					elif mode == "bottom":
						window.SetVerticalAlignBottom()
				else:
					if mode == "top":
						window.SetWindowVerticalAlignTop()
					elif mode == "center":
						window.SetWindowVerticalAlignCenter()
					elif mode == "bottom":
						window.SetWindowVerticalAlignBottom()
	if windowArgument:
		if isinstance(window, ui.TextLine):
			if windowFontName != -1:
				window.SetFontName(windowFontName)
			window.SetText(windowArgument)
		elif isinstance(window, ui.NumberLine):
			window.SetNumber(windowArgument)
		elif isinstance(window, ui.ExpandedImageBox) or isinstance(window, ui.ImageBox):
			window.LoadImage(windowArgument if windowArgument.find("gr2") == -1 else "icon/item/27995.tga")
	window.Show()
	return window

def calculatePos(pos, maxWidth):
	(x , y) = (0, 0)
	while True:
		if pos <= maxWidth:
			if pos < 0:
				pos = 0
			x = 32*pos
			break
		else:
			pos -= maxWidth+1
			y+=32
	return (x, y)

def IS_SET(value, flag):
	return (value & flag) == flag
def SET_BIT(value, bit):
	return value | (bit)
def REMOVE_BIT(value, bit):
	return value & ~(bit)
def getFlagValue(value):
	return 1 << value

def FindItemLevelRange(itemVnum, maxRefine):
	(firstLevel, secondLevel) = (0, 0)
	item.SelectItem(itemVnum-maxRefine)
	for i in xrange(item.LIMIT_MAX_NUM):
		(limitType, limitValue) = item.GetLimit(i)
		if item.LIMIT_LEVEL == limitType:
			if limitValue != 0:
				firstLevel=limitValue
			break

	item.SelectItem(itemVnum)
	for i in xrange(item.LIMIT_MAX_NUM):
		(limitType, limitValue) = item.GetLimit(i)
		if item.LIMIT_LEVEL == limitType:
			if limitValue != 0:
				secondLevel=limitValue
			break
	return (firstLevel, secondLevel)


def PrintDrop(selectedVnum, self, Listbox):
	item.SelectItem(60001)
	(itemVnum, isRefineItem) = getRealVnum(selectedVnum)
	(x, y, isHave, unknownItem) = (5, 5, False, item.GetItemName())

	chestList = wiki.GetItemDropFromChest(itemVnum, isRefineItem)
	if len(chestList)>0:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_CHESTS+":"))
		y += 14

	for chestVnum in chestList:
		item.SelectItem(chestVnum)
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Eemoji/e_wiki|e "+item.GetItemName() if unknownItem != item.GetItemName() else "|Eemoji/e_wiki|e "+localeInfo.WIKI_UNKOWN_ITEM%chestVnum))
		y+=14

	if len(chestList)>0:
		y+=28

	mobList = wiki.GetItemDropFromMonster(itemVnum, isRefineItem)

	if len(mobList) > 0:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_MONSTER+":"))
		y += 14

	for mobVnum in mobList:
		mobLevel = nonplayer.GetMonsterLevel(mobVnum)
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_UNKOWN_MOB%mobVnum  if mobLevel <= 0 else "|Eemoji/e_wiki|e "+nonplayer.GetMonsterName(mobVnum)+ " - Lv."+str(mobLevel)))
		y+=14

	if len(mobList)>0:
		y+=28

	specialData = GetSpecialDropWays(itemVnum, isRefineItem)
	if len(specialData) > 0:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_OTHER_DROP_WAY+":"))
		y += 14

	for dropWay in specialData:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Eemoji/e_wiki|e "+dropWay))
		y+=14

	#if app.ENABLE_ITEMSHOP:
	#	if len(specialData)>0:
	#		y+=28
	#	shopData = GetItemShopData(itemVnum, isRefineItem)
	#	if len(shopData) > 0:
	#		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_ITEMSHOP+":"))
	#		y += 14
	#	for categoryName in shopData:
	#		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Eemoji/e_wiki|e "+categoryName))
	#		y += 14

def CreateCategoryItem(text, event, offset = 0):
	listboxItem = CategoryList.CategoryItem(text)
	listboxItem.Show()
	if event:
		listboxItem.SetEvent(event)
	if offset:
		listboxItem.SetOffset(offset)
	return listboxItem
def CreateCategorySubItem(text, event, offset = 0):
	listboxItem = CategoryList.CategorySubItem(text)
	listboxItem.SetEvent(event)
	listboxItem.SetOffset(offset)
	return listboxItem

class RenderTargetNew(ui.RenderTarget):
	def __init__(self):
		ui.RenderTarget.__init__(self)
		self.children = {}
		self.children["totalPos"] = [0, 0]
		self.children["lastPos"] = [0, 0]
		self.children["isDrag"] = False
		self.SetMouseRightButtonDownEvent(ui.__mem_func__(self.RenderMouseRightDown))
		self.SetMouseRightButtonUpEvent(ui.__mem_func__(self.RenderMouseRightUp))
	def GetRenderIndex(self):
		return self.renderIndex
	def CanCheckMouse(self):
		if renderTarget.IsShow(self.GetRenderIndex()) != 1:
			return False
		if self.children.has_key("isDrag"):
			return self.children["isDrag"]
	def OnUpdate(self):
		if self.CanCheckMouse():
			[currentMousePos, lastPos] = [app.GetCursorPosition(), self.children["lastPos"]]
			totalPos = self.children["totalPos"] if self.children.has_key("totalPos") else [0, 0]
			_x = (currentMousePos[0] - lastPos[0]) + totalPos[0]
			_y = (currentMousePos[1] - lastPos[1]) + totalPos[1]
			fNewPitchVelocity = _y * 0.3
			fNewRotationVelocity = _x * 0.3
			renderTarget.RotateEyeAroundTarget(self.GetRenderIndex(), fNewPitchVelocity, fNewRotationVelocity)
			self.children["totalPos"] = [_x, _y]
			self.children["lastPos"] = currentMousePos
	def RenderMouseRightUp(self):
		app.SetCursor(app.NORMAL)
		self.children["isDrag"] = False
		return True
	def RenderMouseRightDown(self):
		app.SetCursor(app.CAMERA_ROTATE)
		self.children["isDrag"] = True
		self.children["lastPos"] = app.GetCursorPosition()
		return True
	def OnMouseWheel(self, nLen):
		renderIndex = self.GetRenderIndex()
		if renderTarget.IsShow(renderIndex) != 1:
			return False
		renderTarget.Zoom(renderIndex, app.CAMERA_TO_NEGATIVE if nLen > 0 else app.CAMERA_TO_POSITIVE)
		return True
class Grid: # from KeN
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.reset()
	def find_blank(self, width, height):
		if width > self.width or height > self.height:
			return -1

		for row in range(self.height):
			for col in range(self.width):
				index = row * self.width + col
				if self.is_empty(index, width, height):
					return index
		return -1
	def put(self, pos, width, height):
		if not self.is_empty(pos, width, height):
			return False
		for row in range(height):
			start = pos + (row * self.width)
			self.grid[start] = True
			col = 1
			while col < width:
				self.grid[start + col] = True
				col += 1
		return True
	def clear(self, pos, width, height):
		if pos < 0 or pos >= (self.width * self.height):
			return
		for row in range(height):
			start = pos + (row * self.width)
			self.grid[start] = True
			col = 1
			while col < width:
				self.grid[start + col] = False
				col += 1
	def is_empty(self, pos, width, height):
		if pos < 0:
			return False
		row = pos // self.width
		if (row + height) > self.height:
			return False
		if (pos + width) > ((row * self.width) + self.width):
			return False
		for row in range(height):
			start = pos + (row * self.width)
			if self.grid[start]:
				return False
			col = 1
			while col < width:
				if self.grid[start + col]:
					return False
				col += 1
		return True
	def get_size(self):
		return self.width * self.height
	def reset(self):
		self.grid = [False] * (self.width * self.height)
		#self.put(self.width,1,1) # fix from dracaryS


class ScrollBarSpecial(ui.Window):
	BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
	CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3411, 0.3411, 0.3411, 1.0)
	BAR_NUMB = 9 #This is static value! Please dont touch in him.
	SCROLL_WIDTH= 8
	class MiddleBar(ui.DragButton):
		MIDDLE_BAR_COLOR = grp.GenerateColor(0.6470, 0.6470, 0.6470, 1.0)
		def __init__(self, horizontal_scroll):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			self.horizontal_scroll = horizontal_scroll
			self.middle = ui.Bar()
			self.middle.SetParent(self)
			self.middle.AddFlag("attach")
			self.middle.AddFlag("not_pick")
			self.middle.SetColor(self.MIDDLE_BAR_COLOR)
			self.middle.SetSize(1, 1)
			self.middle.Show()
		def SetStaticScale(self, size):
			(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, base_width, size)
				self.middle.SetSize(base_width, size)
			else:
				ui.DragButton.SetSize(self, size, base_height)
				self.middle.SetSize(size, base_height)
		def SetSize(self, selfSize, fullSize):
			(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
				self.middle.SetSize(base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
			else:
				ui.DragButton.SetSize(self, truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
				self.middle.SetSize(truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
		def SetStaticSize(self, size):
			size = max(2, size)
			
			if not self.horizontal_scroll:
				ui.DragButton.SetSize(self, size, self.middle.GetHeight())
				self.middle.SetSize(size, self.middle.GetHeight())
			else:
				ui.DragButton.SetSize(self, self.middle.GetWidth(), size)
				self.middle.SetSize(self.middle.GetWidth(), size)
	def __init__(self, horizontal_scroll = False):
		ui.Window.__init__(self)
		self.horizontal_scroll = horizontal_scroll
		self.scrollEvent = None
		self.scrollSpeed = 50
		self.sizeScale = 1.0
		self.bars = []
		for i in xrange(self.BAR_NUMB):
			br = ui.Bar()
			br.SetParent(self)
			br.AddFlag("attach")
			br.AddFlag("not_pick")
			br.SetColor([self.CORNERS_AND_LINES_COLOR, self.BASE_COLOR][i == (self.BAR_NUMB-1)])
			if not (i % 2 == 0): br.SetSize(1, 1)
			br.Show()
			self.bars.append(br)
		self.middleBar = self.MiddleBar(self.horizontal_scroll)
		self.middleBar.SetParent(self)
		self.middleBar.SetMoveEvent(ui.__mem_func__(self.OnScrollMove))
		self.middleBar.Show()
	def OnScrollMove(self):
		if not self.scrollEvent:
			return
		arg = float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else\
				float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
		self.scrollEvent(arg)
	def SetScrollEvent(self, func):
		self.scrollEvent = func
	def SetScrollSpeed(self, speed):
		self.scrollSpeed = speed
	def OnMouseWheel(self, length):
		if not self.IsShow():
			return False
		length = int((length * 0.01) * self.scrollSpeed)
		if not self.horizontal_scroll:
			val = min(max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale), self.GetHeight() - self.middleBar.GetHeight() - 1)
			self.middleBar.SetPosition(1, val)
		else:
			val = min(max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) *  self.scrollSpeed * self.sizeScale), self.GetWidth() - self.middleBar.GetWidth() - 1)
			self.middleBar.SetPosition(val, 1)
		self.OnScrollMove()
		return True
	def GetPos(self):
		return float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		if not self.horizontal_scroll:
			if xMouseLocalPosition == 0 or xMouseLocalPosition == self.GetWidth():
				return
			y_pos = (yMouseLocalPosition - self.middleBar.GetHeight() / 2)
			self.middleBar.SetPosition(1, y_pos)
		else:
			if yMouseLocalPosition == 0 or yMouseLocalPosition == self.GetHeight():
				return
			x_pos = (xMouseLocalPosition - self.middleBar.GetWidth() / 2)
			self.middleBar.SetPosition(x_pos, 1)
		self.OnScrollMove()
	def SetSize(self, w, h):
		(width, height) = (max(3, w), max(3, h))
		ui.Window.SetSize(self, width, height)
		self.bars[0].SetSize(1, (height - 2))
		self.bars[0].SetPosition(0, 1)
		self.bars[2].SetSize((width - 2), 1)
		self.bars[2].SetPosition(1, 0)
		self.bars[4].SetSize(1, (height - 2))
		self.bars[4].SetPosition((width - 1), 1)
		self.bars[6].SetSize((width - 2), 1)
		self.bars[6].SetPosition(1, (height - 1))
		self.bars[8].SetSize((width - 2), (height - 2))
		self.bars[8].SetPosition(1, 1)
		self.bars[1].SetPosition(0, 0)
		self.bars[3].SetPosition((width - 1), 0)
		self.bars[5].SetPosition((width - 1), (height - 1))
		self.bars[7].SetPosition(0, (height - 1))
		if not self.horizontal_scroll:
			self.middleBar.SetStaticSize(width - 2)
			self.middleBar.SetSize(12, self.GetHeight())
		else:
			self.middleBar.SetStaticSize(height - 2)
			self.middleBar.SetSize(12, self.GetWidth())
		self.middleBar.SetRestrictMovementArea(1, 1, width - 2, height - 2)
	def SetScale(self, selfSize, fullSize):
		self.sizeScale = float(selfSize)/float(fullSize)
		if self.sizeScale <= 0.0305:
			self.sizeScale = 0.05
		self.middleBar.SetSize(selfSize, fullSize)
	def SetStaticScale(self, r_size):
		self.middleBar.SetStaticScale(r_size)
	def SetPosScale(self, fScale):
		pos = (math.ceil((self.GetHeight() - 2 - self.middleBar.GetHeight()) * fScale) + 1) if not self.horizontal_scroll else (math.ceil((self.GetWidth() - 2 - self.middleBar.GetWidth()) * fScale) + 1)
		self.SetPos(pos)
	def SetPos(self, pos):
		wPos = (1, pos) if not self.horizontal_scroll else (pos, 1)
		self.middleBar.SetPosition(*wPos)

class MultiTextLine(ui.Window):
	def Destroy(self):
		self.textRules = {}
	def __init__(self):
		ui.Window.__init__(self)
		self.Destroy()
		self.AddFlag("not_pick")
		self.textRules["textRange"] = 15
		self.textRules["text"] = ""
		self.textRules["textType"] = ""
		self.textRules["fontName"] = ""
		self.textRules["hexColor"] = 0
		self.textRules["fontColor"] = 0
		self.textRules["outline"] = 0
	def SetTextType(self, textType):
		self.textRules["textType"] = textType
		self.Refresh()
	def SetTextRange(self, textRange):
		self.textRules["textRange"] = textRange
		self.Refresh()
	def SetOutline(self, outline):
		self.textRules["outline"] = outline
		self.Refresh()
	def SetPackedFontColor(self, hexColor):
		self.textRules["hexColor"] = hexColor
		self.Refresh()
	def SetFontColor(self, r, g, b):
		self.textRules["fontColor"] =[r, g, b]
		self.Refresh()
	def SetFontName(self, fontName):
		self.textRules["fontName"] = fontName
		self.Refresh()
	def SetText(self, newText):
		self.textRules["text"] = newText
		self.Refresh()
	def Refresh(self):
		textRules = self.textRules
		if textRules["text"] == "":
			return
		self.children=[]
		outline = textRules["outline"]
		fontColor = textRules["fontColor"]
		hexColor = textRules["hexColor"]
		yRange = textRules["textRange"]
		fontName = textRules["fontName"]
		textType = textRules["textType"].split("#")
		totalTextList = textRules["text"].split("#")

		(xPosition, yPosition) = (0, 0)
		width = 0
		for text in totalTextList:
			childText = ui.TextLine()
			childText.SetParent(self)
			childText.AddFlag("not_pick")
			childText.SetPosition(xPosition, yPosition)
			if fontName != "":
				childText.SetFontName(fontName)
			if hexColor != 0:
				childText.SetPackedFontColor(hexColor)
			if fontColor != 0:
				childText.SetFontColor(*fontColor)
			if outline:
				childText.SetOutline()
			self.AddTextType(childText, textType)
			childText.SetText(str(text))
			if childText.GetTextSize()[0] > width:
				width = childText.GetTextSize()[0]
			childText.Show()
			self.children.append(childText)
			yPosition+=yRange

	def AddTextType(self, text,  typeArg):
		if len(typeArg) != 2:
			return
		_typeDict = {
			"vertical": {
				"top":text.SetVerticalAlignTop,
				"bottom":text.SetVerticalAlignBottom,
				"center":text.SetVerticalAlignCenter,
			},
			"horizontal": {
				"left":text.SetHorizontalAlignLeft,
				"right":text.SetHorizontalAlignRight,
				"center":text.SetHorizontalAlignCenter,
			},
			"all_align": {
				"1" : [text.SetHorizontalAlignCenter,text.SetVerticalAlignCenter,text.SetWindowHorizontalAlignCenter,text.SetWindowVerticalAlignCenter],
			},
		}
		(firstToken, secondToken) = tuple(typeArg)
		if _typeDict.has_key(firstToken):
			textType = _typeDict[firstToken][secondToken] if _typeDict[firstToken].has_key(secondToken) else None
			if textType != None:
				if isinstance(textType, list):
					for rule in textType:
						rule()
				else:
					textType()

class ListBoxSpecial(ui.Window):
	def Destroy(self):
		self.basePos=0
		self.itemList=[]
		self.scrollBar=None
		self.scrollLen=0
		self.isHorizontal= False
	def __init__(self, isHorizontal = False):
		ui.Window.__init__(self)
		self.itemList=[]
		self.scrollBar=None
		self.Destroy()
		self.SetInsideRender(True)
	def RemoveAllItems(self):
		for item in self.itemList:
			item.Hide()
			item.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
		self.Render(0)
	def GetItems(self):
		return self.itemList
	def AppendItem(self, newItem, setPosition = True):
		newItem.SetParent(self)
		if setPosition:
			(_x,_y) = (0, 0)
			for child in self.itemList:
				if child.exPos[1]+child.GetHeight() > _y:
					_y = child.exPos[1]+child.GetHeight()
			newItem.SetPosition(_x, _y, True)
		self.itemList.append(newItem)
		self.CalculateScroll()
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar=scrollBar
	def OnMouseWheel(self, length):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				self.scrollBar.OnMouseWheel(length)
				return True
		return False
	def CalculateScroll(self):
		if len(self.itemList) == 0:
			return;
		screenSize = 0
		for child in self.itemList:
			if child.exPos[1]+child.GetHeight() > screenSize:
				screenSize = child.exPos[1]+child.GetHeight()
		#if screenSize != 0:
		#	screenSize+=30
		windowHeight = self.GetHeight()
		(scrollBar,scrollLen) = (self.scrollBar, 0)
		if scrollBar:
			scrollBar.SetPos(0)
			if screenSize > windowHeight:
				scrollLen = screenSize-windowHeight
				scrollBar.SetScale(windowHeight, screenSize)
			else:
				scrollBar.SetScale(windowHeight, windowHeight)
			scrollBar.Show()
		self.scrollLen = scrollLen
	def __OnScroll(self):
		if self.scrollBar:
			self.SetBasePos(int(self.scrollBar.GetPos()*self.scrollLen))
	def Render(self, basePos):
		for child in self.itemList:
			(ex,ey) = child.exPos
			if self.isHorizontal:
				child.SetPosition(ex-basePos,ey)
			else:
				child.SetPosition(ex,ey-basePos)
		self.basePos=basePos
	def SetBasePos(self, basePos):
		if self.basePos == basePos:
			return
		self.Render(basePos)
