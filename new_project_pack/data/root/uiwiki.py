# author: dracaryS
# v3.2 Update Multifunctional Wiki

# static imports
import ui, localeInfo, constInfo, WikiUI, os

# dynamics imports
import grp, app, wiki, renderTarget, item, nonplayer, skill, player, chat, dbg, net

# if false will be textline!
USE_ITEM_COUNT_NUMBER_LINE = False

# if this true item refine showing start index in +0 than +9 will be next item if have!
SHOW_NEXT_ITEM_REFINE = False

SHOW_ITEM_LOWER_TO_BIG = True
# category load speed
AUTOLOAD_SPEED = 0.010
AUTOLOAD_MONSTER_SPEED = 0.020

IMG_DIR = "d:/ymir work/ui/game/wiki/"

class EncyclopediaofGame(ui.BoardWithTitleBar):
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		if self.children.has_key("listBoxCube"):
			self.children["listBoxCube"].ClearItem()
			self.children["listBoxCube"]=None
			del self.children["listBoxCube"]

		if self.children.has_key("resultpageListbox"):
			self.children["resultpageListbox"].RemoveAllItems()
			self.children["resultpageListbox"]=None
			del self.children["resultpageListbox"]

		self.selectArg=""
		self.currentCharacterIdx=-1
		self.AIAppendAlgoritm = None

		if len(self.children) != 0:
			ui.BoardWithTitleBar.Destroy(self)

		self.children = {}

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.SetWindowName("EncyclopediaofGame")
		self.AddFlag("movable")
		self.AddFlag("float")
		#self.AddFlag("animate")
		self.SetCloseEvent(self.Close)
		self.children = {}

		self.Destroy()

		# Default variable
		self.children["characterIndex"]=0
		self.Initialize()

	def Initialize(self):
		self.SetSize(720, 480)
		self.SetTitleName(localeInfo.WIKI_TITLE)
		self.SetCenterPosition()

		self.LoadSearchInfos()
		self.LoadCategoryInfos()
		self.LoadBlock()
		self.LoadResultPage()

	def LoadResultPage(self):
		resultPageImage = WikiUI.CreateWindow(ui.ImageBox(), self, (150,104), IMG_DIR+"result_wall.tga")
		self.children["resultPageImage"] = resultPageImage

		for j in xrange(4):
			characterBtn =  WikiUI.CreateWindow(ui.RadioButton(), resultPageImage, (16+(132*j), 11))
			characterBtn.SetEvent(ui.__mem_func__(self.__SelectCharacters),j)
			characterBtn.SetUpVisual(IMG_DIR+"character/%d_0.tga"%j)
			characterBtn.SetOverVisual(IMG_DIR+"character/%d_1.tga"%j)
			characterBtn.SetDownVisual(IMG_DIR+"character/%d_2.tga"%j)
			characterBtn.Hide()
			self.children["job_%d_characterBtn"%j] = characterBtn

		resultpageListbox = WikiUI.ListBoxSpecial()
		resultpageListbox.SetParent(self)
		self.children["resultpageListbox"] = resultpageListbox

		resultpageListboxScrollbar = WikiUI.ScrollBarSpecial()
		resultpageListboxScrollbar.SetParent(resultpageListbox)
		resultpageListbox.SetScrollBar(resultpageListboxScrollbar)

		resultpagebtn = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (150, 32))
		resultpagebtn.SetEvent(ui.__mem_func__(self.LoadGuidePage),"mouse_click")
		self.children["resultpagebtn"] = resultpagebtn

	def LoadGuidePage(self, emptyArg = ""):
		self.__SelectType("system#0", False, False)

	def LoadBlock(self):
		self.children["blockImage"] =  WikiUI.CreateWindow(ui.ImageBox(), self, (140,32), IMG_DIR+"block.tga")

	def LoadSearchInfos(self):
		self.children["selectedMob"] = 0
		self.children["selectedItem"] = 0

		searchSlot = WikiUI.CreateWindow(ui.ImageBox(), self, (13, 32), IMG_DIR+"search_slot.tga")
		self.children["searchSlot"] = searchSlot

		searchButton = WikiUI.CreateWindow(ui.Button(), searchSlot, (91,3))
		searchButton.SetUpVisual(IMG_DIR+"button_0.tga")
		searchButton.SetOverVisual(IMG_DIR+"button_1.tga")
		searchButton.SetDownVisual(IMG_DIR+"button_2.tga")
		searchButton.SAFE_SetEvent(self.StartSearchItem)
		self.children["searchButton"] = searchButton

		searchItemName = WikiUI.CreateWindow(ui.EditLine(), searchSlot, (2,5), "", "", (91,26))
		searchItemName.SetInfoMessage(localeInfo.WIKI_ITEM_NAME)
		searchItemName.SetMax(30)
		searchItemName.isNeedEmpty = False
		searchItemName.OnPressEscapeKey = ui.__mem_func__(self.Close)
		searchItemName.SetOutline()
		searchItemName.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateItem)
		searchItemName.SetReturnEvent(ui.__mem_func__(self.StartSearchItem))
		self.children["searchItemName"] = searchItemName

		searchClearBtn = WikiUI.CreateWindow(ui.Button(), searchSlot, (75,5))
		searchClearBtn.SetUpVisual(IMG_DIR+"clear_button_1.tga")
		searchClearBtn.SetOverVisual(IMG_DIR+"clear_button_2.tga")
		searchClearBtn.SetDownVisual(IMG_DIR+"clear_button_1.tga")
		searchClearBtn.SAFE_SetEvent(self.ClearEditlineItem)
		searchClearBtn.Hide()
		self.children["searchClearBtn"] = searchClearBtn

		mobSlot = WikiUI.CreateWindow(ui.ImageBox(), self, (13,32+29), IMG_DIR+"search_slot.tga")
		self.children["mobSlot"] = mobSlot

		searchButtonMob = WikiUI.CreateWindow(ui.Button(), mobSlot, (91,2))
		searchButtonMob.SetUpVisual(IMG_DIR+"button_0.tga")
		searchButtonMob.SetOverVisual(IMG_DIR+"button_1.tga")
		searchButtonMob.SetDownVisual(IMG_DIR+"button_2.tga")
		searchButtonMob.SAFE_SetEvent(self.StartSearchMob)
		self.children["searchButtonMob"] = searchButtonMob

		searchMobName = WikiUI.CreateWindow(ui.EditLine(), mobSlot, (2,5), "", "", (91,26))
		searchMobName.SetInfoMessage(localeInfo.WIKI_MOB_NAME)
		searchMobName.isNeedEmpty = False
		searchMobName.SetMax(30)
		searchMobName.SetOutline()
		searchMobName.OnPressEscapeKey = ui.__mem_func__(self.Close)
		searchMobName.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateMob)
		searchMobName.SetReturnEvent(ui.__mem_func__(self.StartSearchMob))
		self.children["searchMobName"] = searchMobName

		searchClearBtnMob = WikiUI.CreateWindow(ui.Button(), mobSlot, (75,5))
		searchClearBtnMob.SetUpVisual(IMG_DIR+"clear_button_1.tga")
		searchClearBtnMob.SetOverVisual(IMG_DIR+"clear_button_2.tga")
		searchClearBtnMob.SetDownVisual(IMG_DIR+"clear_button_1.tga")
		searchClearBtnMob.SAFE_SetEvent(self.ClearEditlineMob)
		searchClearBtnMob.Hide()
		self.children["searchClearBtnMob"] = searchClearBtnMob
	
	def LoadCategoryInfos(self):
		self.children["categoryText"] = WikiUI.CreateWindow(ui.TextLine(), self, (13, 89), localeInfo.WIKI_CATEGORY)

		listBoxCube = WikiUI.CreateWindow(WikiUI.CategoryList(), self, (13, 105), "", "", (109, 335))
		self.children["listBoxCube"] = listBoxCube

		scrollBarListBoxCube = WikiUI.ScrollBarSpecial()
		scrollBarListBoxCube.SetParent(self)
		scrollBarListBoxCube.SetPosition(listBoxCube.GetLocalPosition()[0]+listBoxCube.GetWidth()+2,listBoxCube.GetLocalPosition()[1])
		scrollBarListBoxCube.Show()
		self.children["scrollBarListBoxCube"] = scrollBarListBoxCube

		listBoxCube.SetScrollBar(scrollBarListBoxCube)
		scrollBarListBoxCube.SetSize(8, listBoxCube.GetHeight())

		self.children["historySearch"] = []
		self.children["currentIndex"] = 0

		historyBack = WikiUI.CreateWindow(ui.Button(), self, (13,105+345))
		historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
		historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_normal.tga")
		historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_normal.tga")
		historyBack.SAFE_SetEvent(self.ClickBackHistory)
		self.children["historyBack"] = historyBack

		historyNext = WikiUI.CreateWindow(ui.Button(), self, (13+historyBack.GetWidth()+2,105+345))
		historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		historyNext.SAFE_SetEvent(self.ClickNextHistory)
		self.children["historyNext"] = historyNext

		categoryDict = WikiUI.GetCategoryDict()
		listBoxCubeItems = []
		for key, data in categoryDict.iteritems():
			newDict = {}
			newDict["item"] = WikiUI.CreateCategoryItem(data["name"] if data.has_key("name") else "Noname", None)
			newDict["children"] = []
			itemDict = data["items"] if data.has_key("items") else {}
			for categoryIdx, categoryName in itemDict.iteritems():
				categoryDict = {}
				categoryDict["item"] = WikiUI.CreateCategorySubItem(categoryName, lambda arg = ("{}#{}".format(data["type"] if data.has_key("type") else "article", categoryIdx)) : self.__SelectType(arg))
				newDict["children"].append(categoryDict)
			listBoxCubeItems.append(newDict)
		self.children["listBoxCube"].AppendItemList(listBoxCubeItems)

	def SetHistoryButtons(self):
		historyBack = self.children["historyBack"]
		historyNext = self.children["historyNext"]

		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]

		if len(historySearch) == 0:
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			return

		if currentIndex > 0:
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_hover.tga")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_down.tga")
		else:
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_normal.tga")

		if currentIndex+1 >= len(historySearch):
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		else:
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_hover.tga")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_down.tga")

	def RunHistoryArgument(self, argument):
		if argument.find("NEW") != -1:
			argumentList = argument.split("#")
			self.ShowItemInfo(int(argumentList[1]), int(argumentList[2]), False)
		else:
			self.__SelectType(argument, False, False)

	def ClickBackHistory(self):
		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]
		if currentIndex-1 < 0:
			return
		currentIndex-=1
		self.children["currentIndex"]=currentIndex
		self.RunHistoryArgument(historySearch[currentIndex])
		self.SetHistoryButtons()

	def ClickNextHistory(self):
		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]
		if currentIndex+1 >= len(historySearch):
			return
		currentIndex+=1
		self.children["currentIndex"]=currentIndex
		self.RunHistoryArgument(historySearch[currentIndex])
		self.SetHistoryButtons()

	def get_length(self, x):
		return len(x[0])

	def UpdateItemsList(self):
		input_text_real = self.children["searchItemName"].GetText()
		input_len = len(input_text_real)
		if input_len == 0:
			self.ClearEditlineItem()
			return False
		if localeInfo.IsARABIC():
			input_text = input_text_real
		else:
			input_text = input_text_real.lower()
		self.children["searchClearBtn"].Show()
		items_list = item.GetItemsByName(str(input_text))
		itemList = []
		namesList = []
		for i, itemVnum in enumerate(items_list, start=1):
			(realVnum, isRefineItem) = WikiUI.getRealVnum(itemVnum)
			if isRefineItem:
				realVnum += wiki.GetRefineMaxLevel(realVnum)
				if itemVnum != realVnum:
					continue
			item.SelectItem(itemVnum)
			itemName = item.GetItemName() if localeInfo.IsARABIC() else item.GetItemName().lower()
			if itemName.find("+") != -1:
				itemName = itemName[:itemName.find("+")]
			tempName = list(itemName)
			for i in xrange(input_len):
				tempName[i]=list(input_text_real)[i]
			itemName = ""
			for x in xrange(len(tempName)):
				itemName+=tempName[x]
			if itemName in namesList:
				continue
			namesList.append(itemName)
			itemList.append([itemName, realVnum])
		if len(itemList) > 0:
			if len(itemList) > 1:
				itemList = sorted(itemList, key=self.get_length,reverse=False)
			self.children["selectedItem"] = itemList[0][1]
			self.children["searchItemName"].SetInfoMessage(itemList[0][0])
		else:
			self.children["selectedItem"] = 0
			self.children["searchItemName"].SetInfoMessage("")
		return True

	def __OnValueUpdateItem(self):
		ui.EditLine.OnIMEUpdate(self.children["searchItemName"])
		if not self.UpdateItemsList():
			self.ClearEditlineItem()

		def OnKeyDown(self, key):
			if app.DIK_RETURN == key:
				self.StartSearchItem()
				return True
			return True

	def ClearEditlineItem(self):
		self.children["selectedItem"]=0
		self.children["searchItemName"].SetText("")
		self.children["searchItemName"].SetInfoMessage(localeInfo.WIKI_ITEM_NAME)
		self.children["searchClearBtn"].Hide()

	def StartSearchItem(self):
		if self.children["selectedItem"] != 0:
			self.ShowItemInfo(self.children["selectedItem"],0)

	def UpdateMobsList(self):
		input_text_real = self.children["searchMobName"].GetText()
		input_len = len(input_text_real)
		if input_len == 0:
			self.ClearEditlineMob()
			return False
		input_text = input_text_real if localeInfo.IsARABIC() else input_text_real.lower()
		self.children["searchClearBtnMob"].Show()
		mobs_list = nonplayer.GetMobsByName(str(input_text))
		mobList = []
		namesList = []
		for i, mobVnum in enumerate(mobs_list, start=1):
			if localeInfo.IsARABIC():
				mob_name = nonplayer.GetMonsterName(mobVnum)
			else:
				mob_name = nonplayer.GetMonsterName(mobVnum).lower()
			tempName = list(mob_name)
			for i in xrange(input_len):
				tempName[i]=list(input_text_real)[i]
			mob_name = ""
			for x in xrange(len(tempName)):
				mob_name+=tempName[x]
			if mob_name in namesList:
				continue
			namesList.append(mob_name)
			mobList.append([mob_name, mobVnum])
		if len(mobList) > 0:
			if len(mobList) > 1:
				mobList = sorted(mobList, key=self.get_length,reverse=False)
			self.children["selectedMob"] = mobList[0][1]
			self.children["searchMobName"].SetInfoMessage(mobList[0][0])
		else:
			self.children["selectedMob"] = 0
			self.children["searchMobName"].SetInfoMessage("")
		return True

	def __OnValueUpdateMob(self):
		ui.EditLine.OnIMEUpdate(self.children["searchMobName"])
		if not self.UpdateMobsList():
			self.ClearEditlineMob()
		def OnKeyDown(self, key):
			if app.DIK_RETURN == key:
				self.StartSearchMob()
				return True
			return True

	def ClearEditlineMob(self):
		self.children["selectedMob"]=0
		self.children["searchMobName"].SetText("")
		self.children["searchMobName"].SetInfoMessage(localeInfo.WIKI_MOB_NAME)
		self.children["searchClearBtnMob"].Hide()

	def StartSearchMob(self):
		if self.children["selectedMob"] != 0:
			self.ShowItemInfo(self.children["selectedMob"],1)

	def LoadData(self, arg):
		self.__SelectType(arg)

	def __SelectCharacters(self, buttonIndex):
		WikiUI.ClickRadioButton([self.children["job_%d_characterBtn"%j] for j in xrange(4)], buttonIndex)
		self.children["characterIndex"]=buttonIndex
		self.__SelectType(self.selectArg, True)

	def SetCharacterImagesStatus(self, showStatus):
		btnList = [self.children["job_%d_characterBtn"%j] for j in xrange(4)]
		map(lambda x : (x.Show() if showStatus else x.Hide()), btnList)
		if showStatus:
			WikiUI.ClickRadioButton(btnList, self.children["characterIndex"])

	def ClearResultListbox(self, argList, isSingleItem = False):
		self.AIAppendAlgoritm = None

		#try:
		resultpageListbox = self.children["resultpageListbox"]
		resultpageListbox.RemoveAllItems()
		resultpageListbox.Render(0)
		resultpageListbox.Show()

		if len(argList) == 0:
			return

		imageFile = WikiUI.GetResultPageImage(argList)
		if imageFile:
			self.children["resultpagebtn"].LoadImage(imageFile)
			self.children["resultpagebtn"].Show()

		isEquipmentPage = True if WikiUI.IsCategory(argList[0], "equipment") and isSingleItem == False else False

		self.SetCharacterImagesStatus(isEquipmentPage)
		resultpageListbox.SetPosition(152, 162 if isEquipmentPage else 105)
		resultpageListbox.SetSize(555, 297 if isEquipmentPage else 375 if WikiUI.IsCategory(argList[0], "article") else 360)

		resultpageListboxScrollbar = self.children["resultpageListbox"].scrollBar
		if resultpageListboxScrollbar:
			resultpageListboxScrollbar.SetPosition(resultpageListbox.GetWidth()-9, 1)
			resultpageListboxScrollbar.SetSize(8, resultpageListbox.GetHeight())
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in clear result listbox method.")

	def __SelectType(self, arg, isCharacterBtn = False, isHistory = True):
		#try:
		#if not isCharacterBtn and self.selectArg == arg:
		#	return
		self.selectArg = arg
		self.currentCharacterIdx = self.children["characterIndex"]

		if isHistory:
			self.children["historySearch"].append(arg)
			self.children["currentIndex"] = len(self.children["historySearch"])-1
			self.SetHistoryButtons()
		
		argList = arg.split("#")
		self.ClearResultListbox(argList)
		
		if WikiUI.IsArticleCategory(argList):
			resultpageListbox = self.children["resultpageListbox"]
			event_item = ArticleGUI(argList[1]+"#"+argList[2] if len(argList) == 3 else int(argList[1]))
			resultpageListbox.AppendItem(event_item)
			event_item.LoadItemInfos()
			if resultpageListbox.scrollBar:
				resultpageListbox.scrollBar.Hide()
		
		else:
			AIAppendAlgoritm = WikiUI.AutoLoad()
			(loadSpeed, maxSize, itemType) = (AUTOLOAD_SPEED, -1, int(argList[1]))
		
			categoryType = argList[0].lower() if not localeInfo.IsARABIC() else argList[0]
			if categoryType == "equipment":
				maxSize = wiki.GetCategorySize(self.children["characterIndex"], int(argList[1]))
				AIAppendAlgoritm.SetFlag("characterIndex", self.children["characterIndex"])
			else:
				_methodFunc = {
					"costume": wiki.GetCostumeSize,
					"chests": wiki.GetChestSize,
					"bosses": wiki.GetBossSize,
					"monster": wiki.GetMonsterSize,
					"metinstone": wiki.GetStoneSize,
				}
				maxSize = _methodFunc[categoryType](int(argList[1]))
				if categoryType == "monster":
					loadSpeed = AUTOLOAD_MONSTER_SPEED
		
			if maxSize <= 0:
				return
		
			AIAppendAlgoritm.SetFlag("maxSize", maxSize-1)
			AIAppendAlgoritm.SetFlag("loadTime", loadSpeed)
			AIAppendAlgoritm.SetFlag("loadType",argList[0])
			AIAppendAlgoritm.SetFlag("itemType",itemType)
			self.AIAppendAlgoritm = AIAppendAlgoritm
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in select type func ai method.")

	def GetHyperlinkData(self):
		hyperlink = ""
		historyLen = len(self.children["historySearch"])
		if historyLen:
			currendCommand = self.children["historySearch"][ historyLen - 1]
			hyperlink = "|cffffc700|Hwiki:"+currendCommand+"|h[Wiki-{}: {}]|h|r"
			currendCommandList = currendCommand.split("#")
			if currendCommand.find("NEW") != -1:
				selectedVnum = int(currendCommandList[1])
				argumentIndex = int(currendCommandList[2])
				if argumentIndex == 0:
					import item
					item.SelectItem(selectedVnum)
					hyperlink = hyperlink.format("Item", item.GetItemName())
				elif argumentIndex == 1:
					hyperlink = hyperlink.format("Monster", nonplayer.GetMonsterName(selectedVnum))
			else:
				categoryDict = WikiUI.GetCategoryDict()
				for key, data in categoryDict.iteritems():
					if data["type"] == currendCommandList[0]:
						if data["items"].has_key(int(currendCommandList[1])):
							hyperlink = hyperlink.format(data["name"], data["items"][int(currendCommandList[1])])
							break
			return hyperlink

	def ShowItemInfo(self, selectedVnum, argumentIndex, isHistory = True):
		self.children["listBoxCube"].Reset()
		#try:
		if isHistory:
			self.children["historySearch"].append("NEW#{}#{}".format(selectedVnum, argumentIndex))
			self.children["currentIndex"] = len(self.children["historySearch"])-1
			self.SetHistoryButtons()

		resultpageListbox = self.children["resultpageListbox"]

		if argumentIndex == 0:
			self.ClearResultListbox("equipment#0".split("#"), True)
			(selectedVnum, isRefineItem) = WikiUI.getRealVnum(selectedVnum)
			if isRefineItem:
				selectedVnum += wiki.GetRefineMaxLevel(selectedVnum)# add max refine on itemvnum. example: 10 + 9
				resultpageListbox.AppendItem(EquipmentItem(99, selectedVnum, True))

			item.SelectItem(selectedVnum)
			if item.GetItemType() == item.ITEM_TYPE_GIFTBOX:
				resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 3, True))
				resultpageListbox.AppendItem(MonsterStatics(selectedVnum, 3, True))
			else:
				resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 1, True))

		elif argumentIndex == 1:
			self.ClearResultListbox("monster#0".split("#"), True)
			resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 0, True))
			resultpageListbox.AppendItem(MonsterStatics(selectedVnum, 0, True))

		elif argumentIndex == 3:
			self.__SelectType(selectedVnum)
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in show item info.")

	def OnUpdate(self):
		self.CheckLoadProcess()

	def CheckLoadProcess(self):
		#try:
		__ai = self.AIAppendAlgoritm
		if __ai != None:
			if __ai.GetFlag("nexTime") > app.GetTime():
				return
			__ai.SetFlag("nexTime", app.GetTime()+__ai.GetFlag("loadTime"))
			(loadType, listIndex) = (__ai.GetFlag("loadType"), __ai.GetFlag("maxSize"))
			if WikiUI.IsCategory(loadType, "equipment"):
				equipItemPointer = EquipmentItem(listIndex, wiki.GetCategoryData(__ai.GetFlag("characterIndex"), __ai.GetFlag("itemType"), listIndex), True)
				equipItemPointer.sortIndex = listIndex
				self.children["resultpageListbox"].AppendItem(equipItemPointer, False)
			elif WikiUI.IsCategory(loadType, "costume"):
				createNewWindow = True
				ListBoxItems = self.children["resultpageListbox"].itemList
				if len(ListBoxItems) > 0:
					lastItem = ListBoxItems[len(ListBoxItems)-1]
					if lastItem.CanAddNewItem():
						lastItem.LoadItemInfos(wiki.GetCostumeData(__ai.GetFlag("itemType"), listIndex))
						createNewWindow = False
				if createNewWindow:
					equipItemPointer = SpecialClass(listIndex, 0)
					equipItemPointer.LoadItemInfos(wiki.GetCostumeData(__ai.GetFlag("itemType"), listIndex))
					equipItemPointer.sortIndex = listIndex
					self.children["resultpageListbox"].AppendItem(equipItemPointer, False)
			elif WikiUI.IsCategory(loadType, "chests"):
				(itemVnum, bossVnum) = wiki.GetChestData(__ai.GetFlag("itemType"), listIndex)
				if itemVnum == 0:
					return
				equipItemPointer = ListBoxItemSpecial(listIndex, itemVnum, bossVnum, 0, True)
				equipItemPointer.sortIndex = listIndex
				self.children["resultpageListbox"].AppendItem(equipItemPointer, False)
			elif WikiUI.IsCategory(loadType, "monster"):
				mobVnum = wiki.GetMonsterData(__ai.GetFlag("itemType"), listIndex)
				if mobVnum == 0:
					return
				equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True)
				equipItemPointer.sortIndex = listIndex
				self.children["resultpageListbox"].AppendItem(equipItemPointer, False)
			elif WikiUI.IsCategory(loadType, "bosses"):
				mobVnum = wiki.GetBossData(__ai.GetFlag("itemType"), listIndex)
				if mobVnum == 0:
					return
				equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True)
				equipItemPointer.sortIndex = listIndex
				self.children["resultpageListbox"].AppendItem(equipItemPointer, False)
			elif WikiUI.IsCategory(loadType, "metinstone"):
				mobVnum = wiki.GetStoneData(__ai.GetFlag("itemType"), listIndex)
				if mobVnum == 0:
					return
				equipItemPointer = ListBoxItemSpecial(listIndex, mobVnum, 0, 1, True)
				equipItemPointer.sortIndex = listIndex
				self.children["resultpageListbox"].AppendItem(equipItemPointer, False)
			self.SetPositionToSort(self.children["resultpageListbox"], loadType)
			__ai.SetFlag("maxSize", listIndex-1)
			if listIndex-1 < 0:
				self.AIAppendAlgoritm = None
				self.children["resultpageListbox"].CalculateScroll()
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in check load process")

	def get_key(self, data):
		return data.sortIndex

	def SetPositionToSort(self, listBox, loadType):
		(itemList, _y) = (listBox.itemList, 0)
		reverseMethod = True if WikiUI.IsCategory(loadType, "costume") else SHOW_ITEM_LOWER_TO_BIG
		if len(itemList) > 1:
			itemList = sorted(itemList, key=self.get_key,reverse=reverseMethod)
		for child in itemList:
			child.SetPosition(0, _y, True)
			_y += child.GetHeight()

	def SetWindowStatus(self, bShowStatus):
		if self.children.has_key("resultpageListbox"):
			resultpageListbox = self.children["resultpageListbox"].itemList
			for child in resultpageListbox:
				renderIndex = child._children["renderIndex"] if child._children.has_key("renderIndex") else -1
				if renderIndex != -1:
					renderTarget.SetVisibility(renderIndex, bShowStatus)

		__ai = self.AIAppendAlgoritm
		if __ai != None:
			__ai.SetFlag("nexTime",app.GetTime()+(0.15 if bShowStatus else 999999))

	def Open(self):
		self.SetWindowStatus(True)
		self.Show()
		self.SetTop()

	def Close(self):
		self.SetWindowStatus(False)
		self.Hide()

	def OnPressExitKey(self):
		self.Close()
		return TRUE
	def OnPressEscapeKey(self):
		self.Close()
		return TRUE

class EquipmentItem(WikiUI.DefaultWikiImage):

	class RefineItem(WikiUI.DefaultWikiWindow):
		def LoadData(self, refine, itemVnum, refineCount, refineData):
			tooltipImage = WikiUI.CreateWindow(ui.ImageBox(), self, (0, 0), "", "",(45, 19))
			tooltipImage.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, (itemVnum-wiki.GetRefineMaxLevel(itemVnum))+refine)
			tooltipImage.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			self._children["tooltipImage"] = tooltipImage

			self._children["step_refine"] = WikiUI.CreateWindow(ui.TextLine(), self, (21, 5), "+{}".format(refine), "horizontal:center")
			self._children["step_refine"].AddFlag("not_pick")

			self._children["step_price"] = WikiUI.CreateWindow(ui.TextLine(), self, (21, [140, 140, 140, 180, 230, 275][refineCount]-21), (localeInfo.MoneyFormat(refineData["cost"]).replace(".000","k") if refineData.has_key("cost") else "0") if SHOW_NEXT_ITEM_REFINE or refine else "-", "horizontal:center")

			for i in xrange(refineCount):
				materialItem = refineData["item"][i] if refineData.has_key("item") else 0
				needInsertIcon = materialItem != 0
				if needInsertIcon == True and SHOW_NEXT_ITEM_REFINE == False and refine == 0:
					needInsertIcon = False
				if needInsertIcon:
					item.SelectItem(materialItem)
					refineItemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (5, 20+5+(i*(32+5+10))), item.GetIconImageFileName())
					refineItemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, materialItem)
					refineItemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					refineItemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click", 0, materialItem)
					self._children["refineItemIcon{}".format(i)] = refineItemIcon
					materialItemCount = refineData["count"][i] if refineData.has_key("count") else 0
					if materialItemCount > 0:
						self._children["refineItemCount{}".format(i)] = WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), self, (5+28, 20+5+(i*(32+5+10))+(32 if USE_ITEM_COUNT_NUMBER_LINE else 20)), str(materialItemCount))
				else:
					self._children["emptyRefine{}".format(i)] = WikiUI.CreateWindow(ui.TextLine(), self, (self.GetWidth()/2, 21+18+(i*44)), "-")

	def __init__(self, listIndex, itemVnum, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["itemVnum"] = itemVnum
		self._children["refineItems"] = {}
		self._children["refineCount"] = 2
		self._children["refineLevel"] = wiki.GetRefineMaxLevel(itemVnum)

		for j in xrange(self._children["refineLevel"]+1):
			if item.SelectItemWiki((itemVnum-self._children["refineLevel"])+j) == 1:
				argv = wiki.GetRefineItems(item.GetRefineSet())
				if argv != 0:
					self.InsertRefine(j, *argv)

		self.LoadImage(IMG_DIR+"slot/slot_{}.tga".format(self._children["refineCount"]))

		if self._children["refineLevel"] >= 11:
			self.SetSize(self.GetWidth(), self.GetHeight()+10)
		
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True
			(itemVnum, refineLevel, refineCount, listIndex, refineItems) = (self._children["itemVnum"], self._children["refineLevel"], self._children["refineCount"], self._children["listIndex"], self._children["refineItems"])
			(firstLevel, secondLevel) = WikiUI.FindItemLevelRange(itemVnum, refineLevel)

			itemName = item.GetItemName()
			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (5, 5), itemName[:itemName.find("+")] if itemName.find("+") != -1 else itemName)
			self._children["itemLevel"] = WikiUI.CreateWindow(ui.TextLine(), self, (355, 5), (localeInfo.WIKI_LEVEL_TEXT2%(firstLevel, secondLevel, 0, refineLevel)) if secondLevel != firstLevel else (localeInfo.WIKI_LEVEL_TEXT%(firstLevel, 0, refineLevel)))

			itemLevelCoordinates = [ [0,0],[0,0],[10,55],[10,70],[10,80],[10,115]]
			itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (itemLevelCoordinates[refineCount][0], itemLevelCoordinates[refineCount][1]),  item.GetIconImageFileName() if item.GetIconImageFileName().find("gr2") == -1 else "icon/item/27995.tga")
			if listIndex == 99:
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, itemVnum-refineLevel)
			else:
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, itemVnum)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			self._children["itemIcon"] = itemIcon

			self._children["upgradeItem"] = WikiUI.CreateWindow(ui.TextLine(), self, (50, 24), localeInfo.WIKI_UPGRADE_COSTS)
			self._children["yangCost"] = WikiUI.CreateWindow(ui.TextLine(), self, (58,  [140, 140, 140, 180, 230, 275][refineCount]), localeInfo.WIKI_YANG_COSTS)

			refinedVnum = item.GetRefinedVnum()
			if refinedVnum != 0:
				item.SelectItem(refinedVnum)

				nextItemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (75, itemLevelCoordinates[refineCount][1]), item.GetIconImageFileName() if item.GetIconImageFileName().find("gr2") == -1 else "icon/item/27995.tga")
				nextItemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,refinedVnum)
				nextItemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				nextItemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",refinedVnum)
				self._children["upgradeItem"] = nextItemIcon

			listboxSizes = [ [0,0], [0,0], [411,136], [411,180], [411,228], [411,276] ]

			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxEx(True), self, (130, 20), "", "", (listboxSizes[refineCount][0], listboxSizes[refineCount][1]))
			Listbox.SetItemStep(41)
			Listbox.SetItemSize(45, listboxSizes[refineCount][1])
			Listbox.SetViewItemCount(10)

			if refineLevel > 10:
				scrollbar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(True), self, (0, [156, 156, 156, 200, 255, 296][refineCount]), "", "", (540, 8))
				scrollbar.SetScale(540, 540+((refineLevel-10) * 45))
				Listbox.SetScrollBar(scrollbar)

			for i in xrange(refineLevel+1):
				refine_data = self.RefineItem()
				Listbox.AppendItem(refine_data)
				refine_data.LoadData(i, itemVnum, refineCount, refineItems[i if SHOW_NEXT_ITEM_REFINE or i == 0 else i-1] if refineItems.has_key(i if SHOW_NEXT_ITEM_REFINE or i == 0 else i-1) else {})

			Listbox.SetBasePos(0)
			Listbox.Show()
			self._children["Listbox"] = Listbox
			self.Show()

	def OnClickItem(self, arg, itemVnum = 0):
		self.OverOutItem()
		parent = constInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(itemVnum+wiki.GetRefineMaxLevel(itemVnum) if itemVnum != 0 else self._children["itemVnum"], 0)

	def InsertRefine(self, refineIndex, *refineData):
		refineMaterialCount = 5
		(refineItems, refineCount) = (self._children["refineItems"], self._children["refineCount"])
		refineItems[refineIndex] = {
			#"id" : int(refineData[0]), # unused
			"item" : [int(refineData[1+(j * 2)]) for j in xrange(refineMaterialCount)],
			"count" : [int(refineData[2+(j * 2)]) for j in xrange(refineMaterialCount)],
			"cost" : int(refineData[(refineMaterialCount * 2) + 1]),
			"prob" : int(refineData[(refineMaterialCount * 2) + 2]),
			#"refine_count" : int(refineData[(refineMaterialCount * 2) + 3]), #unused
		}
		if int(refineData[(refineMaterialCount * 2) + 3]) > refineCount:
			refineCount = int(refineData[(refineMaterialCount * 2) + 3])
		(self._children["refineItems"], self._children["refineCount"]) = (refineItems, refineCount)

class MonsterItemSpecial(WikiUI.DefaultWikiImage):

	def Destroy(self):
		if self._children.has_key("renderIndex"):
			renderTarget.SetVisibility(self._children["renderIndex"], False)
			renderTarget.ResetModel(self._children["renderIndex"])
		WikiUI.DefaultWikiImage.Destroy(self)

	def __init__(self, selectedVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["selectedVnum"] = selectedVnum
		self._children["isType"] = isType
		self.LoadImage(IMG_DIR+"slot/special_slot.tga")
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded = True

			renderIndex = renderTarget.GetFreeIndex(1000, 1000000)
			self._children["renderIndex"] = renderIndex

			(isType, selectedVnum) = (self._children["isType"],self._children["selectedVnum"])

			Listbox = None

			if isType == 0 or isType == 3:
				if isType == 0:
					renterTarget = WikiUI.CreateWindow(WikiUI.RenderTargetNew(), self, (1, 1), "", "", (187, 163))
					renterTarget.SetRenderTarget(renderIndex)
					renderTarget.SetRotation(renderIndex, False)
					self._children["renterTarget"] = renterTarget

					renderTarget.SelectModel(renderIndex, selectedVnum)
					renderTarget.SetVisibility(renderIndex, True)

				elif isType == 3:
					item.SelectItem(selectedVnum)

					itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (70, 45), item.GetIconImageFileName())
					itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, selectedVnum)
					itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					self._children["itemIcon"] = itemIcon


				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (190, 25), "", "", (350, 138))
				self._children["Listbox"] = Listbox

				self._children["dropList"] = WikiUI.CreateWindow(ui.TextLine(), self, (300, 6), localeInfo.WIKI_DROPLIST_INFO % nonplayer.GetMonsterName(selectedVnum) if isType == 0 else localeInfo.WIKI_CONTENT_INFO % item.GetItemName())
				self._children["monsterInfo"] = WikiUI.CreateWindow(ui.TextLine(), self, (245, 170), localeInfo.WIKI_STATICS_INFO % nonplayer.GetMonsterName(selectedVnum) if isType == 0 else localeInfo.WIKI_AVAIBLE_AT, "horizontal:center")

				grid = WikiUI.Grid(width = 10, height = 50)

				itemLen = (wiki.GetMobInfoSize if isType == 0 else wiki.GetSpecialInfoSize)(selectedVnum)
				getFunc = wiki.GetMobInfoData if isType == 0 else wiki.GetSpecialInfoData


				for j in xrange(itemLen):
					(vnum, count) = getFunc(selectedVnum, j)
					if vnum == 0:
						continue

					item.SelectItem(vnum)

					pos = grid.find_blank(*item.GetItemSize())
					if not len(item.GetItemName()) or pos == -1:
						continue

					grid.put(pos, *item.GetItemSize())

					(x, y) = WikiUI.calculatePos(pos, 9)

					item_new = WikiUI.CreateWindow(ui.ExpandedImageBox(), Listbox, (x, y, True), item.GetIconImageFileName())
					item_new.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, vnum)
					item_new.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					item_new.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0, vnum)
					Listbox.AppendItem(item_new)

					if count>1:
						itemNumberline = WikiUI.CreateWindow(ui.NumberLine(), Listbox, (x+15,y+item_new.GetHeight()-10, True), str(count))
						Listbox.AppendItem(itemNumberline)

				if Listbox.isNeedScrollBar():
					scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), Listbox, (Listbox.GetWidth()-10, 0), "", "", (8, 137))
					Listbox.SetScrollBar(scrollBar)
			else:

				item.SelectItem(selectedVnum)

				if WikiUI.IsCanModelPreview(selectedVnum):
					renterTarget = WikiUI.CreateWindow(WikiUI.RenderTargetNew(), self, (1, 1), "", "", (187, 163))
					renterTarget.SetRenderTarget(renderIndex)
					renderTarget.SetRotation(renderIndex, False)
					self._children["renterTarget"] = renterTarget
					WikiUI.SetItemToModelPreview(renderIndex, selectedVnum)

				itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (renterTarget.GetWidth()-33-3,3) if WikiUI.IsCanModelPreview(selectedVnum) else (70, 45), item.GetIconImageFileName())
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, selectedVnum)
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				self._children["itemIcon"] = itemIcon

				self._children["avaible"] = WikiUI.CreateWindow(ui.TextLine(), self, (350, 6), localeInfo.WIKI_AVAIBLE_AT)

				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (190, 25), "", "", (350, 138))
				self._children["Listbox"] = Listbox

				WikiUI.PrintDrop(selectedVnum, self, Listbox)

				if Listbox.isNeedScrollBar():
					scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), Listbox, (Listbox.GetWidth()-10, 0), "", "", (8, 137))
					Listbox.SetScrollBar(scrollBar)

			if Listbox != None:
				if len(Listbox.itemList) > 0:
					Listbox.SetBasePos(0, False)
			self.Show()

class MonsterStatics(WikiUI.DefaultWikiImage):
	def __init__(self, mobVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["mobVnum"] = mobVnum
		self._children["isType"] = isType
		self.LoadImage(IMG_DIR+"slot/big_empty.tga")
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True
			ListBox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (0, 0), "", "", (self.GetWidth(), self.GetHeight()-3))
			self._children["ListBox"] = ListBox
			(mobVnum, isType) = (self._children["mobVnum"], self._children["isType"])
			if isType == 3:
				WikiUI.PrintDrop(mobVnum, self, ListBox)
			elif isType == 0:
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3, True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_LEVEL_MOB_TEXT%nonplayer.GetMonsterLevel(mobVnum)))
				RACE_FLAG_TO_NAME = {
					1 << 0  : localeInfo.TARGET_INFO_RACE_ANIMAL,
					1 << 1 	: localeInfo.TARGET_INFO_RACE_UNDEAD,
					1 << 2  : localeInfo.TARGET_INFO_RACE_DEVIL,
					1 << 3  : localeInfo.TARGET_INFO_RACE_HUMAN,
					1 << 4  : localeInfo.TARGET_INFO_RACE_ORC,
					1 << 5  : localeInfo.TARGET_INFO_RACE_MILGYO,
				}
				SUB_RACE_FLAG_TO_NAME = {
					1 << 11 : localeInfo.TARGET_INFO_RACE_ELEC,
					1 << 12 : localeInfo.TARGET_INFO_RACE_FIRE,
					1 << 13 : localeInfo.TARGET_INFO_RACE_ICE,
					1 << 14 : localeInfo.TARGET_INFO_RACE_WIND,
					1 << 15 : localeInfo.TARGET_INFO_RACE_EARTH,
					1 << 16 : localeInfo.TARGET_INFO_RACE_DARK,
					1 << 17 : localeInfo.TARGET_INFO_RACE_ZODIAC,
				}
				(mainrace, subrace, dwRaceFlag) = ("", "", nonplayer.GetMonsterRaceFlag(mobVnum))

				for i in xrange(18):
					curFlag = 1 << i
					if WikiUI.IS_SET(dwRaceFlag, curFlag):
						if RACE_FLAG_TO_NAME.has_key(curFlag):
							mainrace += RACE_FLAG_TO_NAME[curFlag] + ", "
						elif SUB_RACE_FLAG_TO_NAME.has_key(curFlag):
							subrace += SUB_RACE_FLAG_TO_NAME[curFlag] + ", "

				if nonplayer.IsMonsterStone(mobVnum):
					mainrace += localeInfo.TARGET_INFO_RACE_METIN + ", "

				mainrace = localeInfo.TARGET_INFO_NO_RACE if mainrace == "" else mainrace[:-2]
				subrace = localeInfo.TARGET_INFO_NO_RACE if subrace == "" else subrace[:-2]

				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*1), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_TYPE%(mainrace, subrace)))

				(mindmg, maxdmg) = nonplayer.GetMonsterDamage(mobVnum)
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*2), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_DMG%(mindmg,maxdmg,nonplayer.GetMonsterMaxHP(mobVnum))))

				(minyang, maxyang) = nonplayer.GetMonsterPrice(mobVnum)
				exp = nonplayer.GetMonsterExp(mobVnum)
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*3), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_YNG%(minyang, maxyang, exp)))

				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*4), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_DEFENSES))
				resists = {
					nonplayer.MOB_RESIST_SWORD : localeInfo.TARGET_INFO_RESIST_SWORD,
					nonplayer.MOB_RESIST_TWOHAND : localeInfo.TARGET_INFO_RESIST_TWOHAND,
					nonplayer.MOB_RESIST_DAGGER : localeInfo.TARGET_INFO_RESIST_DAGGER,
					nonplayer.MOB_RESIST_BELL : localeInfo.TARGET_INFO_RESIST_BELL,
					nonplayer.MOB_RESIST_FAN : localeInfo.TARGET_INFO_RESIST_FAN,
					nonplayer.MOB_RESIST_BOW : localeInfo.TARGET_INFO_RESIST_BOW,
					nonplayer.MOB_RESIST_MAGIC : localeInfo.TARGET_INFO_RESIST_MAGIC,
				}
				c = 0
				for resist, label in resists.items():
					ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (20, 3*(7*(5+c)), True), label % nonplayer.GetMonsterResist(mobVnum, resist)))
					c+=1
			if ListBox.isNeedScrollBar():
				ListBox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), ListBox, (ListBox.GetWidth()-10, 0, True), "", "", (8, ListBox.GetHeight()+5)))
			ListBox.Show()
			self._children["ListBox"] = ListBox
			self.Show()

class ListBoxItemSpecial(WikiUI.DefaultWikiImage):

	def __init__(self, listIndex, itemVnum, mobVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["isType"] = isType
		self._children["itemVnum"] = itemVnum
		self._children["mobVnum"] = mobVnum
		self.LoadImage(IMG_DIR+"slot/slot.tga")
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True

			(listIndex, isType, itemVnum, mobVnum) = (self._children["listIndex"], self._children["isType"], self._children["itemVnum"], self._children["mobVnum"])

			name = nonplayer.GetMonsterName(mobVnum if isType == 0 else itemVnum)

			if isType == 0:
				item.SelectItem(itemVnum)

			setItemName = localeInfo.WIKI_CONTENT_INFO%item.GetItemName()
			if isType != 0:
				setItemName = localeInfo.WIKI_DROPLIST_INFO%name
				setItemName += " - Level {}".format(nonplayer.GetMonsterLevel(itemVnum))
				if WikiUI.IsGameMaster():
					setItemName += " - Mob Vnum {}".format(itemVnum)

			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (230, 5), setItemName, "horizontal:center")
			self._children["origin"] = WikiUI.CreateWindow(ui.TextLine(), self, (480, 5), localeInfo.WIKI_ORIGIN)

			needOriginListBox = True if not (isType == 0 and mobVnum != 0) and isinstance(WikiUI.GetOriginMapName(itemVnum), list) and len(WikiUI.GetOriginMapName(itemVnum)) > 4 else False 

			needAppendNames = []
			if needOriginListBox:
				nameList = WikiUI.GetOriginMapName(itemVnum)
				for originName in nameList:
					needAppendNames.append(originName)
			else:
				if isType == 0 and mobVnum != 0:
					needAppendNames.append(name[:12] + "..." if len(name) > 15 else name)
				else:
					name = WikiUI.GetOriginMapName(itemVnum)
					if isinstance(name, list):
						for originName in name:
							needAppendNames.append(originName)
					else:
						needAppendNames.append(name if name != "" else "-")

			if len(needAppendNames):
				ListboxOrigin = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (450, 25), "", "", (90, 66))
				for originName in needAppendNames:
					textPtr = WikiUI.CreateWindow(ui.TextLine(), ListboxOrigin, (0, 0), originName[:12] + "..." if len(originName) > 15 else originName, "", (-1, -1), "Tahoma:11")
					if len(needAppendNames) <= 4:
						textPtr.SetPosition(45 - (textPtr.GetTextSize()[0]/2), [25, 15, 10, 5][len(needAppendNames)-1] + ( needAppendNames.index(originName) * 13))
					else:
						textPtr.SetPosition(5, needAppendNames.index(originName) * 16, True)
					ListboxOrigin.AppendItem(textPtr)
				if ListboxOrigin.isNeedScrollBar():
					ListboxOrigin.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (450+83, 22), "", "", (8, ListboxOrigin.GetHeight())))
				self._children["ListboxOrigin"] = ListboxOrigin

			#if needOriginListBox:
			#	yPos = 0
			#	ListboxOrigin = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (450, 25), "", "", (90, 66))
			#	nameList = WikiUI.GetOriginMapName(itemVnum)
			#	for originName in nameList:
			#		ListboxOrigin.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListboxOrigin, (5, yPos, True), originName[:12] + "..." if len(originName) > 15 else originName, "horizontal:left", (-1, -1), "Tahoma:11"))
			#		yPos+=13
			#	if ListboxOrigin.isNeedScrollBar():
			#		ListboxOrigin.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (450+83, 22), "", "", (8, ListboxOrigin.GetHeight())))
			#	self._children["ListboxOrigin"] = ListboxOrigin
			#else:
			#
			#	bossVnum = WikiUI.CreateWindow(WikiUI.MultiTextLine(), self, (450, 23), "", "", (90, 66))
			#	bossVnum.SetTextRange(13)
			#	bossVnum.SetTextType("all_align#1")
			#	if isType == 0 and mobVnum != 0:
			#		bossVnum.SetText(name[:12] + "..." if len(name) > 15 else name)
			#	else:
			#		name = WikiUI.GetOriginMapName(itemVnum)
			#		if isinstance(name, list):
			#			newText = ""
			#			for tr in name:
			#				newText+=tr+"#"
			#			bossVnum.SetText(newText if newText != "" else "-")
			#			bossVnum.SetPosition(450, 22-(len(name)*4))
			#		else:
			#			bossVnum.SetText(name if name != "" else "-")
			#	self._children["bossVnum"] = bossVnum

			if isType == 0:
				itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (10, 25), item.GetIconImageFileName())
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,itemVnum)
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
				self._children["itemIcon"] = itemIcon

			else:
				renterTarget = WikiUI.CreateWindow(ui.RenderTarget(), self, (1, 1), "", "", (47,87))
				renterTarget.SetRenderTarget(20+listIndex)
				renterTarget.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 1, itemVnum)
				self._children["renterTarget"] = renterTarget

				renderTarget.SelectModel(20+listIndex, itemVnum)
				renderTarget.SetVisibility(20+listIndex, True)
				self._children["renderIndex"] = 20+listIndex
			whileSize = wiki.GetSpecialInfoSize(itemVnum) if isType == 0 else wiki.GetMobInfoSize(itemVnum)

			if whileSize != 0:
				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (48, 22), "", "", (403, 65))

				gridCalculate = WikiUI.Grid(width = 12, height = 50)

				for j in xrange(whileSize):
					(vnum, count) = wiki.GetSpecialInfoData(itemVnum, j) if isType == 0 else wiki.GetMobInfoData(itemVnum, j)
					if vnum == 0 or count == 0:
						continue
					item.SelectItem(vnum)
					(width, height) = item.GetItemSize()
					if width == 0 or height == 0:
						continue
					pos = gridCalculate.find_blank(width, height)
					gridCalculate.put(pos, width, height)
					(x, y) = WikiUI.calculatePos(pos, 11)

					item_new = WikiUI.CreateWindow(ui.ExpandedImageBox(), Listbox, (x, y, True), item.GetIconImageFileName())
					item_new.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,vnum)
					item_new.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					item_new.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,vnum)
					Listbox.AppendItem(item_new)

					if count>1:
						Listbox.AppendItem(WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), Listbox, (x+15,y+item_new.GetHeight()-10,True) if USE_ITEM_COUNT_NUMBER_LINE else (x+item_new.GetWidth()-5,y+item_new.GetHeight()-10,True), str(count)))
				if Listbox.isNeedScrollBar():
					Listbox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (443, 23), "", "", (8, 63)))
				self._children["Listbox"] = Listbox
			self.Show()

class ArticleGUI(WikiUI.DefaultWikiWindow):
	def __init__(self, index):
		WikiUI.DefaultWikiWindow.__init__(self)
		if isinstance(index, str):
			if index.find("#") != -1:
				indexList = index.split("#")
				if len(indexList) == 2:
					self._children["index"] = int(indexList[0])
					self._children["scrollPos"] = float(indexList[1])
		else:
			self._children["index"] = index
			self._children["scrollPos"] =  0.0
		mainParent = constInfo.GetWikiInterface()
		if mainParent != None:
			self.SetSize(mainParent.children["resultpageListbox"].GetWidth(),mainParent.children["resultpageListbox"].GetHeight())
	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded = True
			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (0,0), "", "", (self.GetWidth()-15, self.GetHeight()-15))
			self.ReadArticle(Listbox, self._children["index"])
			self.CheckScrollBarNeed(Listbox)
			self._children["Listbox"] = Listbox
			self.Show()
	def ParseToken(self, data):
		data = data.replace(chr(10), "").replace(chr(13), "")
		if not (len(data) and data[0] == "["):
			return (False, {}, data)
		fnd = data.find("]")
		if fnd <= 0:
			return (False, {}, data)
		content = data[1:fnd]
		data = data[fnd+1:]
		content = content.split(";")
		container = {}
		for i in content:
			i = i.strip()
			splt = i.split("=")
			if len(splt) == 1:
				container[splt[0].lower().strip()] = True
			else:
				#container[splt[0].lower().strip()] = splt[1].lower().strip()
				container[splt[0].lower().strip()] = splt[1].lower().strip() if splt[0].lower() != "linktext" else splt[1]
		return (True, container, data)
	def GetColorFromString(self, strCol):
		retData = []
		dNum = 4
		hCol = long(strCol, 16)
		if hCol <= 0xFFFFFF:
			retData.append(1.0)
			dNum = 3
		for i in xrange(dNum):
			retData.append(float((hCol >> (8 * i)) & 0xFF) / 255.0)
		retData.reverse()
		return retData
	def DirectionEvent(self, emptyArg, type, index, pos):
		parent = constInfo.GetWikiInterface()
		if parent != None:
			if "item" == type:
				parent.ShowItemInfo(int(index), 0)
			elif "mob" == type:
				parent.ShowItemInfo(int(index), 1)
			elif "article" == type:
				parent.ShowItemInfo("System#"+str(index)+"#"+str(pos),3)
			elif "article" == type:
				parent.ShowItemInfo("System#"+str(index)+"#"+str(pos),3)
			elif "warp" == type:
				net.SendChatPacket("/wiki_server warp {} {}".format(index, pos))
				mainParent = constInfo.GetWikiInterface()
				if mainParent:
					mainParent.Close()
			elif "website" == type:
				os.system("start \"\" {}".format(index))

	def ReadArticle(self, Listbox, index):
		fileName = WikiUI.GetArticleFileName(index)
		if fileName == "":
			return
		try:
			lines = open(fileName, "r").readlines()
		except:
			pass
		_y = 15
		for i in lines:
			(ret, tokenMap, i) = self.ParseToken(i)
			if ret:
				if tokenMap.has_key("banner_img"):
					mainParent = constInfo.GetWikiInterface()
					if mainParent != None:
						resultpagebtn = mainParent.children["resultpagebtn"]
						resultpagebtn.LoadImage(tokenMap["banner_img"])
						resultpagebtn.Show()
						tokenMap.pop("banner_img")

				if tokenMap.has_key("img"):
					cimg = ui.ExpandedImageBox()
					cimg.SetParent(Listbox)
					cimg.AddFlag("attach")
					cimg.AddFlag("not_pick")
					cimg.LoadImage(tokenMap["img"])
					cimg.Show()
					tokenMap.pop("img")
					x = 0
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					y = 0
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("center_align"):
						cimg.SetPosition(Listbox.GetWidth() / 2 - cimg.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						cimg.SetPosition(Listbox.GetWidth() - cimg.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						cimg.SetPosition(x, y, True)
					Listbox.AppendItem(cimg)

				if tokenMap.has_key("item"):
					itemVnum = int(tokenMap["item"])
					tokenMap.pop("item")

					metinSlot = [0 for j in xrange(player.METIN_SOCKET_MAX_NUM)]
					attrSlot = [[0,0] for j in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]

					if tokenMap.has_key("socket"):
						metinSlotData = tokenMap["socket"].split("#")  if tokenMap["socket"].find("#") else tokenMap["socket"]
						tokenMap.pop("socket")
						for metin in metinSlotData:
							metinSplit = metin.split(":")
							if len(metinSplit) != 2:
								continue
							metinSlot[int(metinSplit[0])] = int(metinSplit[1])

					if tokenMap.has_key("attr"):
						attrSlotData = tokenMap["attr"].split("#") if tokenMap["attr"].find("#") else tokenMap["attr"]
						tokenMap.pop("attr")

						for attr in attrSlotData:
							attrSplit = attr.split(":")
							if len(attrSplit) != 2:
								continue
							attrDataSplit = attrSplit[1].split("?")
							if len(attrDataSplit) != 2:
								continue
							attrSlot[int(attrSplit[0])] = [int(attrDataSplit[0]), int(attrDataSplit[1])]

					for k in xrange(player.ATTRIBUTE_SLOT_MAX_NUM):
						attrSlot[k] = tuple(attrSlot[k])

					item.SelectItem(itemVnum)
					cimg = ui.ExpandedImageBox()
					cimg.SetParent(Listbox)
					if item.GetIconImageFileName().find("gr2") == -1:
						cimg.LoadImage(item.GetIconImageFileName())
					else:
						cimg.LoadImage("icon/item/27995.tga")
					cimg.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, itemVnum, metinSlot, attrSlot)
					cimg.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					cimg.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
					cimg.Show()
					x = 0
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					y = 0
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("center_align"):
						cimg.SetPosition(Listbox.GetWidth() / 2 - cimg.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						cimg.SetPosition(Listbox.GetWidth() - cimg.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						cimg.SetPosition(x, y, True)

					Listbox.AppendItem(cimg)

				if tokenMap.has_key("link"):
					link = tokenMap["link"].split("#")
					tokenMap.pop("link")
					if len(link) != 3:
						continue

					if tokenMap.has_key("text"):
						#linkText = WikiUI.GetArgToString(tokenMap["text"])
						linkText =tokenMap["text"]
						tokenMap.pop("text")
					else:
						linkText = ""

					tmp = WikiUI.TextlineLink()
					tmp.SetParent(Listbox)
					if tokenMap.has_key("font_size"):
						splt = localeInfo.UI_DEF_FONT.split(":")
						tmp.SetFontName(splt[0]+":"+tokenMap["font_size"])
						tokenMap.pop("font_size")
					else:
						tmp.SetFontName(localeInfo.UI_DEF_FONT)

					linkText = linkText.replace("*", "|Eemoji/e_wiki|e")

					#tmp.SetText(WikiUI.GetArgToString(linkText), 1.2)
					tmp.SetText(linkText, 1.2)
					tmp.Show()
					if tokenMap.has_key("color"):
						fontColor = self.GetColorFromString(tokenMap["color"])
						tmp.SetColor(grp.GenerateColor(fontColor[0], fontColor[1], fontColor[2], fontColor[3]), fontColor[0], fontColor[1], fontColor[2])
						tokenMap.pop("color")
					tmp.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.DirectionEvent), "", link[0], link[1],link[2])
					tmp.linkIcon.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.DirectionEvent),"", link[0], link[1], link[2])
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")						
					if tokenMap.has_key("center_align"):
						tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

				if tokenMap.has_key("rendertarget"):
					mobVnum = int(tokenMap["rendertarget"])
					tokenMap.pop("rendertarget")

					(width, height) = (47, 87)

					if tokenMap.has_key("width"):
						width = int(tokenMap["width"])
						tokenMap.pop("width")

					if tokenMap.has_key("height"):
						height = int(tokenMap["height"])
						tokenMap.pop("height")

					targetIndex = renderTarget.GetFreeIndex(1000, 1000000)
					tmp = WikiUI.RenderTargetNew()
					tmp.SetParent(Listbox)
					tmp.SetSize(width, height)
					tmp.SetRenderTarget(targetIndex)
					renderTarget.SetRotation(targetIndex, False)
					tmp.SetEvent(ui.__mem_func__(self.DirectionEvent),"mouse_click", "mob", mobVnum, 0)
					tmp.Show()
					
					
					if tokenMap.has_key("movable"):
						if int(tokenMap["movable"]):
							tmp.AddFlag("movable")
						tokenMap.pop("movable")

					renderTarget.SelectModel(targetIndex, mobVnum)
					renderTarget.SetVisibility(targetIndex, True)
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")						
					if tokenMap.has_key("center_align"):
						tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)
				
				if tokenMap.has_key("button"):
					button = tokenMap["button"].split("#")
					tokenMap.pop("button")
					if len(button) != 3:
						continue

					tmp = ui.Button()
					tmp.SetParent(Listbox)
					tmp.SetUpVisual(button[0])
					tmp.SetOverVisual(button[1])
					tmp.SetDownVisual(button[2])
					tmp.Show()
					if tokenMap.has_key("linkindex"):
						try:
							linkindex = tokenMap["linkindex"].split("#")
							if len(linkindex) == 3:
								tmp.SAFE_SetEvent(self.DirectionEvent, "", linkindex[0], linkindex[1], linkindex[2])
						except:
							pass
						tokenMap.pop("linkindex")
					if tokenMap.has_key("text"):
						tmp.SetText(tokenMap["text"])
						tokenMap.pop("text")
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					if tokenMap.has_key("center_align"):
						tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

			if ret and not len(i):
				continue

			i = i.replace("*", "|Eemoji/e_wiki|e")
			tmp = ui.TextLine()
			tmp.SetParent(Listbox)
			if tokenMap.has_key("font_size"):
				splt = localeInfo.UI_DEF_FONT.split(":")
				tmp.SetFontName(splt[0]+":"+tokenMap["font_size"])
				tokenMap.pop("font_size")
			else:
				tmp.SetFontName(localeInfo.UI_DEF_FONT)
			tmp.SetText(WikiUI.GetArgToString(i))
			tmp.Show()
			tmp.SetSize(*tmp.GetTextSize())

			if tokenMap.has_key("color"):
				fontColor = self.GetColorFromString(tokenMap["color"])
				tmp.SetPackedFontColor(grp.GenerateColor(fontColor[0], fontColor[1], fontColor[2], fontColor[3]))
				tokenMap.pop("color")

			tmp.SetPosition(5, _y, True)
			_y+=tmp.GetHeight()

			if tokenMap.has_key("center_align"):
				tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, tmp.GetLocalPosition()[1], True)
				tokenMap.pop("center_align")
			elif tokenMap.has_key("right_align"):
				tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), tmp.GetLocalPosition()[1], True)
				tokenMap.pop("right_align")
			elif tokenMap.has_key("x_padding"):
				tmp.SetPosition(int(tokenMap["x_padding"]), tmp.GetLocalPosition()[1], True)
				tokenMap.pop("x_padding")
			tmp.Show()
			Listbox.AppendItem(tmp)

	def CheckScrollBarNeed(self, Listbox):
		if Listbox.isNeedScrollBar():
			scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (self.GetWidth()-8, 2), "", "", (8, self.GetHeight() - 15))
			scrollBar.SetPos(self._children["scrollPos"])
			Listbox.SetScrollBar(scrollBar)
			Listbox.OnScroll()

class SpecialClass(WikiUI.DefaultWikiWindow):
	def __init__(self, listIndex, isMonster):
		WikiUI.DefaultWikiWindow.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["vnumList"] = []
		self._children["renderIndex"] = -1
		self.SetSize(540, 147)
	
	def CanAddNewItem(self):
		return len(self._children["vnumList"]) < 4

	def LoadItemInfos(self, data = -1):
		if data == -1:
			return
		xPos = len(self._children["vnumList"]) * (127+9)

		bg = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (xPos, 0), IMG_DIR+"slot/special_single.tga")
		self._children["bg{}".format(data)] = bg

		item.SelectItem(data)
		itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), bg, (-1, -1), item.GetIconImageFileName())
		itemIcon.SetPosition((bg.GetWidth()/2)-(itemIcon.GetWidth()/2), ((bg.GetHeight()-20)/2)-(itemIcon.GetHeight()/2))
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItemSpecial, data)
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
		itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click", 0, data)
		self._children["itemIcon{}".format(data)] = itemIcon
		self._children["itemName{}".format(data)] = WikiUI.CreateWindow(ui.TextLine(), self, (len(self._children["vnumList"]) * (127+9)+(bg.GetWidth()/2), bg.GetHeight()-18), item.GetItemName(), "horizontal:center")
		self._children["vnumList"].append(data)
		self.Show()

	def OverOutItem(self):
		renderIndex = self._children["renderIndex"]
		if renderIndex != -1:
			renderTarget.SetVisibility(renderIndex, False)
			renderTarget.ResetModel(renderIndex)
		WikiUI.DefaultWikiWindow.OverOutItem(self)

	def OverInItemSpecial(self, itemVnum):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			tooltipItem = interface.tooltipItem
			if tooltipItem:
				tooltipItem.ClearToolTip()

				renderIndex = renderTarget.GetFreeIndex(1000, 1000000)
				self._children["renderIndex"] = renderIndex

				tooltipItem.toolTipWidth -= 35

				renterTarget = WikiUI.CreateWindow(ui.RenderTarget(), tooltipItem, (10, 5), "", "", (tooltipItem.toolTipWidth-20, 150))
				renterTarget.SetRenderTarget(renderIndex)
				tooltipItem.childrenList.append(renterTarget)

				tooltipItem.toolTipHeight += 150
				tooltipItem.ResizeToolTip()
				tooltipItem.SetItemToolTipWiki(itemVnum)
				WikiUI.SetItemToModelPreview(renderIndex, itemVnum)
