import ui
import net
import app
import localeInfo
import uiScriptLocale
import dbg
import player
import item
import skill
import constInfo
import playersettingmodule

CHARACTER_CHEST_CG_PACK = 1
CHARACTER_CHEST_CG_UNPACK = 2
CHARACTER_CHEST_CG_PREVIEW = 3

CHARACTER_CHEST_ITEM_VNUM = 72323
CHARACTER_CHEST_PREVIEW_READONLY_CELL = 65535

CHARACTER_CHEST_OP_LIST = 0
CHARACTER_CHEST_OP_PACK = 1
CHARACTER_CHEST_OP_UNPACK = 2
CHARACTER_CHEST_OP_PREVIEW = 3

CHARACTER_CHEST_BUSY = False
CHARACTER_CHEST_REMOTE_PREVIEW_PENDING = False


def GetChestLocale(key, default):
	try:
		val = getattr(localeInfo, key)
	except:
		return default
	if val == key:
		return default
	return val


def FormatChestLocale(key, default, *args):
	fmt = GetChestLocale(key, default)
	try:
		return fmt % args
	except:
		if args:
			return default % args
		return default


def SetCharacterChestBusy(busy):
	global CHARACTER_CHEST_BUSY
	CHARACTER_CHEST_BUSY = busy


def ResetCharacterChestState():
	global CHARACTER_CHEST_BUSY, CHARACTER_CHEST_REMOTE_PREVIEW_PENDING
	CHARACTER_CHEST_BUSY = False
	CHARACTER_CHEST_REMOTE_PREVIEW_PENDING = False


def _GetInterface():
	try:
		import constInfo
		if hasattr(constInfo, "GetInterfaceInstance"):
			return constInfo.GetInterfaceInstance()
	except:
		pass
	return None


def CanStartCharacterChestMutation():
	if CHARACTER_CHEST_BUSY:
		return False
	iface = _GetInterface()
	if iface and hasattr(iface, "IsCharacterChestBlockedByUI"):
		if iface.IsCharacterChestBlockedByUI():
			return False
	return True


def NotifyCharacterChestBlocked():
	import chat
	chat.AppendChat(chat.CHAT_TYPE_INFO, GetChestLocale("CHARACTER_CHEST_WINDOW_BLOCK", "Baska bir pencere acikken bu islemi yapamazsin."))


def IsCharacterChestInventoryLocked():
	# Do not use CHARACTER_CHEST_BUSY here: it stays True after pack/unpack until
	# the server replies (or disconnect), which locks inventory with no window.
	iface = constInfo.GetInterfaceInstance()
	if iface and hasattr(iface, "IsCharacterChestWindowOpen"):
		return iface.IsCharacterChestWindowOpen()
	return False


def NotifyCharacterChestInventoryLocked():
	import chat
	chat.AppendChat(chat.CHAT_TYPE_INFO, GetChestLocale("CHARACTER_CHEST_INVENTORY_BLOCK", "Karakter sandigi penceresi acikken envanter kullanamazsin."))


def IsCharacterChestPreviewShortcutPressed():
	return app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)


def IsCharacterChestPreviewReadOnlyCell(itemCell):
	return itemCell < 0 or itemCell >= CHARACTER_CHEST_PREVIEW_READONLY_CELL


def MarkRemoteCharacterChestPreview():
	global CHARACTER_CHEST_REMOTE_PREVIEW_PENDING
	CHARACTER_CHEST_REMOTE_PREVIEW_PENDING = True


def ConsumeRemoteCharacterChestPreview():
	global CHARACTER_CHEST_REMOTE_PREVIEW_PENDING
	if CHARACTER_CHEST_REMOTE_PREVIEW_PENDING:
		CHARACTER_CHEST_REMOTE_PREVIEW_PENDING = False
		return True
	return False


def ShouldOpenCharacterChestPreviewReadOnly(itemCell):
	if ConsumeRemoteCharacterChestPreview():
		return True
	if IsCharacterChestPreviewReadOnlyCell(itemCell):
		return True
	return False


def TryOpenCharacterChestPreviewFromItem(vnum, metinSlot):
	if not app.ENABLE_CHARACTER_CHEST:
		return False
	if vnum != CHARACTER_CHEST_ITEM_VNUM:
		return False
	if not metinSlot or len(metinSlot) < 2:
		return False
	packedPid = int(metinSlot[0])
	seal = int(metinSlot[1])
	if packedPid <= 0 or seal == 0:
		return False
	RequestCharacterChestPreview(packedPid)
	return True


def RequestCharacterChestPreview(packedPid):
	if packedPid <= 0:
		return
	MarkRemoteCharacterChestPreview()
	net.SendCharacterChestPacket(CHARACTER_CHEST_CG_PREVIEW, packedPid, 0, "")


class CharacterChestListItem(ui.ListBoxEx.Item):
	def __init__(self, pid, name, level):
		ui.ListBoxEx.Item.__init__(self)
		self.pid = pid
		self.textLine = ui.TextLine()
		self.textLine.SetParent(self)
		self.textLine.SetPosition(4, 1)
		self.textLine.SetText("%s (Lv %d)" % (name, level))
		self.textLine.Show()
		self.SetSize(230, 16)

	def __del__(self):
		ui.ListBoxEx.Item.__del__(self)


class CharacterChestPackDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.board = None
		self.listBox = None
		self.passwordEdit = None
		self.acceptButton = None
		self.cancelButton = None
		self.itemCell = -1
		self.selectedPid = 0
		self.entryList = []
		self.IsLoaded = False

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()
		self.Hide()

	def __LoadWindow(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/characterchestpack.py")
		except:
			dbg.TraceError("CharacterChestPackDialog.LoadScript failed")
			return

		self.board = self.GetChild("board")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.SetTitleName(GetChestLocale("CHARACTER_CHEST_TITLE", "Karakter Sandigi"))

		desc = self.GetChild("desc")
		desc.SetText(GetChestLocale("CHARACTER_CHEST_SELECT_HINT", "Paketlemek istedigin yan karakteri sec."))

		listSlot = self.GetChild("list_slot")
		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(listSlot)
		self.listBox.SetPosition(4, 4)
		self.listBox.SetSize(listSlot.GetWidth() - 8, listSlot.GetHeight() - 8)
		self.listBox.SetViewItemCount(8)
		self.listBox.SetSelectEvent(ui.__mem_func__(self.__OnSelectItem))
		self.listBox.Show()

		passwordSlot = self.GetChild("password_slot")
		self.passwordEdit = ui.EditLine()
		self.passwordEdit.SetParent(passwordSlot)
		self.passwordEdit.SetPosition(3, 2)
		self.passwordEdit.SetSize(passwordSlot.GetWidth() - 6, 14)
		self.passwordEdit.SetMax(7)
		self.passwordEdit.SetSecret(True)
		self.passwordEdit.Show()

		self.acceptButton = self.GetChild("accept_button")
		self.acceptButton.SetEvent(ui.__mem_func__(self.__OnAccept))
		self.cancelButton = self.GetChild("cancel_button")
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))

	def Open(self, entryList, itemCell):
		self.entryList = entryList
		self.itemCell = itemCell
		self.selectedPid = 0
		self.__LoadWindow()
		if not self.IsLoaded:
			return
		self.__RefreshList()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		dbg.TraceError("CharacterChestPackDialog.Open cell=%d entries=%d" % (itemCell, len(entryList)))

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __RefreshList(self):
		if not self.listBox:
			return
		self.listBox.RemoveAllItems()
		for entry in self.entryList:
			pid, name, level = entry
			self.listBox.AppendItem(CharacterChestListItem(pid, name, level))

	def __OnSelectItem(self, item):
		if item:
			self.selectedPid = item.pid

	def __OnAccept(self):
		if self.selectedPid <= 0:
			return
		if not CanStartCharacterChestMutation():
			NotifyCharacterChestBlocked()
			return
		password = self.passwordEdit.GetText()
		if len(password) < 7:
			return
		SetCharacterChestBusy(True)
		net.SendCharacterChestPacket(CHARACTER_CHEST_CG_PACK, self.selectedPid, self.itemCell, password)
		self.Close()


class CharacterChestUnpackDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.board = None
		self.nameText = None
		self.questionText = None
		self.acceptButton = None
		self.cancelButton = None
		self.itemCell = -1
		self.targetPid = 0
		self.IsLoaded = False

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()
		self.Hide()

	def __LoadWindow(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/characterchestunpack.py")
		except:
			dbg.TraceError("CharacterChestUnpackDialog.LoadScript failed")
			return

		self.board = self.GetChild("board")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.SetTitleName(GetChestLocale("CHARACTER_CHEST_TITLE", "Karakter Sandigi"))
		self.nameText = self.GetChild("name_text")
		self.questionText = self.GetChild("question_text")
		self.questionText.SetText(GetChestLocale("CHARACTER_CHEST_UNPACK_QUEST", "Bu karakteri hesabina aktarmak istiyor musun?"))
		self.acceptButton = self.GetChild("accept_button")
		self.acceptButton.SetEvent(ui.__mem_func__(self.__OnAccept))
		self.cancelButton = self.GetChild("cancel_button")
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))

	def Open(self, packedName, itemCell, targetPid):
		self.itemCell = itemCell
		self.targetPid = targetPid
		self.__LoadWindow()
		if not self.IsLoaded:
			return
		self.nameText.SetText(FormatChestLocale("CHARACTER_CHEST_PACKED_LABEL", "Paketli karakter: %s", packedName))
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		dbg.TraceError("CharacterChestUnpackDialog.Open pid=%d cell=%d name=%s" % (targetPid, itemCell, packedName))

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __OnAccept(self):
		if self.itemCell < 0 or self.targetPid <= 0:
			dbg.TraceError("CharacterChestUnpackDialog: invalid cell=%d pid=%d" % (self.itemCell, self.targetPid))
			return
		if not CanStartCharacterChestMutation():
			NotifyCharacterChestBlocked()
			return
		SetCharacterChestBusy(True)
		net.SendCharacterChestPacket(CHARACTER_CHEST_CG_UNPACK, self.targetPid, self.itemCell, "")
		self.Close()


FACE_IMAGE_DICT = {
	playersettingmodule.RACE_WARRIOR_M	: "icon/face/warrior_m.tga",
	playersettingmodule.RACE_ASSASSIN_W	: "icon/face/assassin_w.tga",
	playersettingmodule.RACE_SURA_M		: "icon/face/sura_m.tga",
	playersettingmodule.RACE_SHAMAN_W	: "icon/face/shaman_w.tga",
	playersettingmodule.RACE_WARRIOR_W	: "icon/face/warrior_w.tga",
	playersettingmodule.RACE_ASSASSIN_M	: "icon/face/assassin_m.tga",
	playersettingmodule.RACE_SURA_W		: "icon/face/sura_w.tga",
	playersettingmodule.RACE_SHAMAN_M	: "icon/face/shaman_m.tga",
}

WINDOW_INVENTORY = 1
WINDOW_EQUIPMENT = 2
WINDOW_DRAGON_SOUL_INVENTORY = 5
WINDOW_BELT_INVENTORY = 6


SHOW_LIMIT_SUPPORT_SKILL_LIST = [121, 122, 123, 124, 126, 127, 129, 128, 131, 137, 138, 139, 140]
if app.ENABLE_CONQUEROR_LEVEL:
	SHOW_LIMIT_SUPPORT_SKILL_LIST = SHOW_LIMIT_SUPPORT_SKILL_LIST + [132, 133, 134, 246]

CHAR_PANEL_X = 12
CHAR_PANEL_Y = 36
CHAR_PANEL_W = 253
CHAR_PANEL_H = 361
INV_PANEL_X = 277
INV_PANEL_Y = 36
INV_PANEL_W = 176
INV_PANEL_H = 565

BIOLOGIST_LEVELS = (30, 40, 50, 60, 70, 80, 85, 90, 92, 94)
BIOLOGIST_STATUS_NONE = 0
BIOLOGIST_STATUS_PROGRESS = 1
BIOLOGIST_STATUS_DONE = 2

BIO_PANEL_X = 12
BIO_PANEL_Y = CHAR_PANEL_Y + CHAR_PANEL_H + 6
BIO_PANEL_W = CHAR_PANEL_W
BIO_PANEL_H = 198
BIO_ROW_H = 16
BIO_ROW_GAP = 1
BIO_ROW_STEP = BIO_ROW_H + BIO_ROW_GAP
BIO_TEXT_Y = -8

COLOR_BIO_DONE = 0xff55ff55
COLOR_BIO_PROGRESS = 0xffffff55
COLOR_BIO_WAIT = 0xff888888
COLOR_BIO_NAME = 0xff88ff88

BIO_ROW_W = BIO_PANEL_W - 12


class CharacterChestBiologistRow(ui.Window):
	def __init__(self, level, status):
		ui.Window.__init__(self)
		self.SetSize(BIO_ROW_W, BIO_ROW_STEP)

		self.nameText = ui.TextLine()
		self.nameText.SetParent(self)
		self.nameText.SetPosition(4, BIO_TEXT_Y)
		self.nameText.SetText(FormatChestLocale("CHARACTER_CHEST_BIO_QUEST_NAME", "Biyolog Gorevi - (Lv %d)", level))
		self.nameText.AddFlag("not_pick")
		self.nameText.Show()

		self.statusText = ui.TextLine()
		self.statusText.SetParent(self)
		self.statusText.SetPosition(150, BIO_TEXT_Y)
		self.statusText.AddFlag("not_pick")

		if status == BIOLOGIST_STATUS_DONE:
			self.nameText.SetPackedFontColor(COLOR_BIO_NAME)
			self.statusText.SetText(GetChestLocale("CHARACTER_CHEST_BIO_DONE", "Tamamlandi") + " v")
			self.statusText.SetPackedFontColor(COLOR_BIO_DONE)
		elif status == BIOLOGIST_STATUS_PROGRESS:
			self.nameText.SetPackedFontColor(COLOR_BIO_NAME)
			self.statusText.SetText(GetChestLocale("CHARACTER_CHEST_BIO_PROGRESS", "Devam ediyor"))
			self.statusText.SetPackedFontColor(COLOR_BIO_PROGRESS)
		else:
			self.nameText.SetPackedFontColor(COLOR_BIO_WAIT)
			self.statusText.SetText(GetChestLocale("CHARACTER_CHEST_BIO_WAIT", "Beklemede"))
			self.statusText.SetPackedFontColor(COLOR_BIO_WAIT)

		self.statusText.Show()


class CharacterChestPreviewDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.board = None
		self.charWnd = None
		self.invWnd = None
		self.equipSlot = None
		self.invSlot = None
		self.wndMoney = None
		self.wndCheque = None
		self.wndGem = None
		self.acceptButton = None
		self.cancelButton = None
		self.invPageButtons = []
		self.charTabButtonDict = {}
		self.charTabDict = {}
		self.charPageDict = {}
		self.charTitleBarDict = {}
		self.charSkillGroupButtons = []
		self.charActiveSkillGroupName = None
		self.tooltipItem = None
		self.itemCell = -1
		self.readOnly = False
		self.targetPid = 0
		self.invPageIndex = 0
		self.charState = "STATUS"
		self.previewSkillGroup = 1
		self.previewJob = 0
		self.invItems = {}
		self.equipItems = {}
		self.skillList = []
		self.IsLoaded = False
		self.panelsLoaded = False
		self.biologistPanel = None
		self.biologistRowSlot = None
		self.biologistRows = []

	@ui.WindowDestroy
	def Destroy(self):
		if self.charWnd:
			self.charWnd.Hide()
		if self.invWnd:
			self.invWnd.Hide()
		self.__Initialize()
		self.ClearDictionary()
		self.Hide()

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def __LoadWindow(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/characterchestpreview.py")
		except:
			dbg.TraceError("CharacterChestPreviewDialog.LoadScript failed")
			return

		self.board = self.GetChild("board")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.SetTitleName(GetChestLocale("CHARACTER_CHEST_TITLE", "Karakter Sandigi"))
		self.acceptButton = self.GetChild("accept_button")
		self.cancelButton = self.GetChild("cancel_button")

		self.acceptButton.SetText(GetChestLocale("CHARACTER_CHEST_UNPACK_ACCEPT", "Aktar"))
		self.acceptButton.SetEvent(ui.__mem_func__(self.__OnAccept))
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))
		self.readOnly = False

		self.__LoadEmbeddedPanels()

	def __LoadEmbeddedPanels(self):
		if self.panelsLoaded:
			return
		self.panelsLoaded = True

		pyScrLoader = ui.PythonScriptLoader()

		self.charWnd = ui.ScriptWindow()
		self.charWnd.SetParent(self.board)
		self.charWnd.Show()

		try:
			pyScrLoader.LoadScriptFile(self.charWnd, "UIScript/characterwindow.py")
		except:
			dbg.TraceError("CharacterChestPreviewDialog char panel load failed")
			self.charWnd = None

		if self.charWnd:
			self.__FixEmbeddedPanel(self.charWnd, CHAR_PANEL_X, CHAR_PANEL_Y, CHAR_PANEL_W, CHAR_PANEL_H)

		self.invWnd = ui.ScriptWindow()
		self.invWnd.SetParent(self.board)
		self.invWnd.Show()

		try:
			if app.ENABLE_EXTEND_INVEN_SYSTEM:
				if localeInfo.IsARABIC():
					pyScrLoader.LoadScriptFile(self.invWnd, uiScriptLocale.LOCALE_UISCRIPT_PATH + "InventoryWindow.py")
				else:
					pyScrLoader.LoadScriptFile(self.invWnd, "UIScript/InventoryWindowEx.py")
			else:
				pyScrLoader.LoadScriptFile(self.invWnd, "UIScript/InventoryWindow.py")
		except:
			dbg.TraceError("CharacterChestPreviewDialog inv panel load failed")
			self.invWnd = None

		if self.invWnd:
			self.__FixEmbeddedPanel(self.invWnd, INV_PANEL_X, INV_PANEL_Y, INV_PANEL_W, INV_PANEL_H)

		self.__LoadBiologistPanel()
		if self.biologistPanel:
			self.biologistPanel.SetTop()

		if self.invWnd:
			self.invWnd.SetTop()

		if not self.charWnd:
			return

		self.__BindCharPanel()
		if self.invWnd:
			self.__BindInvPanel()

	def __FixEmbeddedPanel(self, wnd, x, y, width, height):
		# LoadScriptFile applies uiscript screen coords (e.g. SCREEN_WIDTH - 176); reset for embed.
		wnd.SetPosition(x, y)
		wnd.SetSize(width, height)
		wnd.Show()

	def __LoadBiologistPanel(self):
		if self.biologistPanel:
			return

		self.biologistPanel = ui.ThinBoard()
		self.biologistPanel.SetParent(self.board)
		self.biologistPanel.SetPosition(BIO_PANEL_X, BIO_PANEL_Y)
		self.biologistPanel.SetSize(BIO_PANEL_W, BIO_PANEL_H)
		self.biologistPanel.Show()

		titleBar = ui.Bar()
		titleBar.SetParent(self.biologistPanel)
		titleBar.SetPosition(2, 2)
		titleBar.SetSize(BIO_PANEL_W - 4, 20)
		titleBar.SetColor(0xff2a1f12)
		titleBar.Show()

		titleText = ui.TextLine()
		titleText.SetParent(titleBar)
		titleText.SetPosition(8, 3)
		titleText.SetText(GetChestLocale("CHARACTER_CHEST_BIO_TITLE", "Biyolog Gorevleri"))
		titleText.SetPackedFontColor(0xffffffff)
		titleText.Show()

		self.biologistRowSlot = ui.Window()
		self.biologistRowSlot.SetParent(self.biologistPanel)
		self.biologistRowSlot.SetPosition(4, 24)
		self.biologistRowSlot.SetSize(BIO_PANEL_W - 8, len(BIOLOGIST_LEVELS) * BIO_ROW_STEP)
		self.biologistRowSlot.Show()

	def __ClearBiologistRows(self):
		for row in self.biologistRows:
			row.Hide()
		self.biologistRows = []

	def __RefreshBiologistList(self, biologistList):
		if not self.biologistRowSlot:
			return

		self.__ClearBiologistRows()

		statusList = []
		if biologistList:
			try:
				statusList = [int(x) for x in biologistList]
			except:
				statusList = []

		while len(statusList) < len(BIOLOGIST_LEVELS):
			statusList.append(BIOLOGIST_STATUS_NONE)

		for i, level in enumerate(BIOLOGIST_LEVELS):
			status = statusList[i] if i < len(statusList) else BIOLOGIST_STATUS_NONE
			row = CharacterChestBiologistRow(level, status)
			row.SetParent(self.biologistRowSlot)
			row.SetPosition(0, i * BIO_ROW_STEP)
			row.Show()
			self.biologistRows.append(row)

		if self.biologistPanel:
			self.biologistPanel.Show()

	def __BindCharPanel(self):
		if not self.charWnd:
			return

		self.charTabDict = {
			"STATUS"	: self.charWnd.GetChild("Tab_01"),
			"SKILL"		: self.charWnd.GetChild("Tab_02"),
			"EMOTICON"	: self.charWnd.GetChild("Tab_03"),
			"QUEST"		: self.charWnd.GetChild("Tab_04"),
		}
		self.charTabButtonDict = {
			"STATUS"	: self.charWnd.GetChild("Tab_Button_01"),
			"SKILL"		: self.charWnd.GetChild("Tab_Button_02"),
			"EMOTICON"	: self.charWnd.GetChild("Tab_Button_03"),
			"QUEST"		: self.charWnd.GetChild("Tab_Button_04"),
		}
		self.charPageDict = {
			"STATUS"	: self.charWnd.GetChild("Character_Page"),
			"SKILL"		: self.charWnd.GetChild("Skill_Page"),
			"EMOTICON"	: self.charWnd.GetChild("Emoticon_Page"),
			"QUEST"		: self.charWnd.GetChild("Quest_Page"),
		}
		self.charTitleBarDict = {
			"STATUS"	: self.charWnd.GetChild("Character_TitleBar"),
			"SKILL"		: self.charWnd.GetChild("Skill_TitleBar"),
			"EMOTICON"	: self.charWnd.GetChild("Emoticon_TitleBar"),
			"QUEST"		: self.charWnd.GetChild("Quest_TitleBar"),
		}

		for tabKey in ("STATUS", "SKILL"):
			self.charTabButtonDict[tabKey].SetEvent(ui.__mem_func__(self.__OnCharTab), tabKey)

		self.charSkillGroupButtons = (
			self.charWnd.GetChild("Skill_Group_Button_1"),
			self.charWnd.GetChild("Skill_Group_Button_2"),
		)
		self.charActiveSkillGroupName = self.charWnd.GetChild("Active_Skill_Group_Name")
		for i in xrange(len(self.charSkillGroupButtons)):
			self.charSkillGroupButtons[i].SetEvent(ui.__mem_func__(self.__OnSkillGroup), i + 1)

		self.__HideCharInteractiveWidgets()
		self.__DisableCharPreviewTabs()
		self.__SetCharState("STATUS")

	def __DisableCharPreviewTabs(self):
		for tabKey in ("EMOTICON", "QUEST"):
			tabBtn = self.charTabButtonDict.get(tabKey)
			if tabBtn:
				tabBtn.Hide()
			tabImg = self.charTabDict.get(tabKey)
			if tabImg:
				tabImg.Hide()
			page = self.charPageDict.get(tabKey)
			if page:
				page.Hide()
			titleBar = self.charTitleBarDict.get(tabKey)
			if titleBar:
				titleBar.Hide()

	def __HideCharInteractiveWidgets(self):
		for name in (
			"HTH_Plus", "INT_Plus", "STR_Plus", "DEX_Plus",
			"HTH_Minus", "INT_Minus", "STR_Minus", "DEX_Minus",
		):
			wnd = self.charWnd.GetChild2(name)
			if wnd:
				wnd.Hide()

		for name in ("Lv_ToolTip", "Exp_ToolTip"):
			wnd = self.charWnd.GetChild2(name)
			if wnd:
				wnd.Hide()

	def __BindInvPanel(self):
		if not self.invWnd:
			return

		self.equipSlot = self.invWnd.GetChild("EquipmentSlot")
		self.invSlot = self.invWnd.GetChild("ItemSlot")
		self.wndMoney = self.invWnd.GetChild2("Money")
		self.wndCheque = self.invWnd.GetChild2("Cheque")
		self.wndGem = self.invWnd.GetChild2("Gem")

		titleBar = self.invWnd.GetChild2("TitleBar")
		if titleBar:
			titleBar.Show()
			if hasattr(titleBar, "CloseButtonHide"):
				titleBar.CloseButtonHide()
		titleName = self.invWnd.GetChild2("TitleName")
		if titleName:
			try:
				titleName.SetText(uiScriptLocale.INVENTORY_TITLE)
			except:
				titleName.SetText("Envanter")

		for name in ("MallButton", "CostumeButton", "DSSButton"):
			wnd = self.invWnd.GetChild2(name)
			if wnd:
				wnd.Hide()

		for i in xrange(player.INVENTORY_PAGE_COUNT):
			btn = self.invWnd.GetChild("Inventory_Tab_%02d" % (i + 1))
			btn.SetEvent(ui.__mem_func__(self.__OnSelectInvPage), i)
			self.invPageButtons.append(btn)
		if self.invPageButtons:
			self.invPageButtons[0].Down()

		for name in ("Equipment_Tab_01", "Equipment_Tab_02"):
			wnd = self.invWnd.GetChild2(name)
			if wnd:
				wnd.Hide()

		moneySlot = self.invWnd.GetChild2("Money_Slot")
		if moneySlot:
			moneySlot.SetEvent(lambda *args: None)

		chequeSlot = self.invWnd.GetChild2("Cheque_Slot")
		if chequeSlot:
			chequeSlot.SetEvent(lambda *args: None)

		gemSlot = self.invWnd.GetChild2("Gem_Slot")
		if gemSlot:
			gemSlot.SetEvent(lambda *args: None)

		self.equipSlot.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInEquip))
		self.equipSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutItem))
		self.invSlot.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInInv))
		self.invSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutItem))

	def __SetCharState(self, stateKey):
		self.charState = stateKey

		for tabKey, tabButton in self.charTabButtonDict.items():
			if stateKey != tabKey:
				tabButton.SetUp()

		for tabValue in self.charTabDict.itervalues():
			tabValue.Hide()
		for pageValue in self.charPageDict.itervalues():
			pageValue.Hide()
		for titleBarValue in self.charTitleBarDict.itervalues():
			titleBarValue.Hide()

		self.charTitleBarDict[stateKey].Show()
		self.charTabDict[stateKey].Show()
		self.charPageDict[stateKey].Show()

	def __OnCharTab(self, stateKey):
		if stateKey not in ("STATUS", "SKILL"):
			return
		self.__SetCharState(stateKey)

	def __OnSkillGroup(self, groupIndex):
		self.previewSkillGroup = groupIndex
		for i in xrange(len(self.charSkillGroupButtons)):
			if (i + 1) == groupIndex:
				self.charSkillGroupButtons[i].Down()
			else:
				self.charSkillGroupButtons[i].SetUp()
		self.__RefreshSkills(self.previewJob, self.previewSkillGroup)

	def __GetRealSkillSlot(self, skillGrade, skillSlot):
		return skillSlot + min(skill.SKILL_GRADE_COUNT - 1, skillGrade) * skill.SKILL_GRADE_STEP_COUNT

	def __GetETCSkillRealSlotIndex(self, skillSlot):
		activePageSlotCount = 8
		if app.ENABLE_CONQUEROR_LEVEL:
			activePageSlotCount = 9
		if skillSlot > 100:
			return skillSlot
		return skillSlot % activePageSlotCount

	def Open(self, itemCell, targetPid, packedName, playerData, skillList, itemList, biologistList=None, readOnly=False):
		if readOnly or ShouldOpenCharacterChestPreviewReadOnly(itemCell):
			self.itemCell = -1
			self.readOnly = True
		else:
			self.itemCell = itemCell
			self.readOnly = False
		self.targetPid = targetPid
		self.skillList = skillList if skillList else []

		if type(playerData) not in (list, tuple):
			dbg.TraceError("CharacterChestPreview: bad playerData type %s" % type(playerData))
			return
		if len(playerData) < 13:
			dbg.TraceError("CharacterChestPreview: playerData len=%d (need 13)" % len(playerData))
			return

		name = str(playerData[0])
		job = int(playerData[1])
		level = int(playerData[2])
		st = int(playerData[3])
		ht = int(playerData[4])
		dx = int(playerData[5])
		iq = int(playerData[6])
		exp = long(playerData[7])
		gold = long(playerData[8])
		playtime = int(playerData[9])
		partBase = int(playerData[10])
		parts = playerData[11]
		skillGroup = int(playerData[12])
		cheque = int(playerData[13]) if len(playerData) > 13 else 0
		gem = int(playerData[14]) if len(playerData) > 14 else 0

		self.__LoadWindow()
		if not self.IsLoaded:
			return
		if not self.charWnd:
			dbg.TraceError("CharacterChestPreview: character panel missing")
			return
		if not self.invWnd:
			dbg.TraceError("CharacterChestPreview: inventory panel missing")

		self.previewJob = job
		self.previewSkillGroup = skillGroup if skillGroup in (1, 2) else 1

		self.__ApplyFace(job)
		self.__RefreshCharInfo(name, job, level, st, ht, dx, iq, exp, playtime)
		if self.wndMoney:
			try:
				self.wndMoney.SetText(localeInfo.NumberToString(gold))
			except:
				self.wndMoney.SetText(constInfo.intWithCommas(gold))
		if self.wndCheque:
			try:
				self.wndCheque.SetText(localeInfo.NumberToGoldNotText(cheque))
			except:
				self.wndCheque.SetText(constInfo.intWithCommas(cheque))
		if self.wndGem:
			try:
				self.wndGem.SetText(localeInfo.NumberToString(gem))
			except:
				self.wndGem.SetText(constInfo.intWithCommas(gem))

		if itemList is None:
			itemList = []
		if skillList is None:
			skillList = []
		try:
			itemCount = len(itemList)
		except:
			itemCount = 0
		try:
			skillCount = len(skillList)
		except:
			skillCount = 0
		dbg.TraceError("CharacterChestPreview.Open skills=%d items=%d" % (skillCount, itemCount))

		self.__BuildItemMaps(itemList)
		self.__RefreshEquipSlots()
		self.__RefreshInvPage()
		self.__OnSkillGroup(self.previewSkillGroup)
		self.__RefreshBiologistList(biologistList)
		if self.biologistPanel:
			self.biologistPanel.SetTop()

		self.__ApplyReadOnlyMode()

		if self.charWnd:
			self.charWnd.Show()
		if self.invWnd:
			self.invWnd.Show()
		if self.biologistPanel:
			self.biologistPanel.Show()

		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def __ApplyReadOnlyMode(self):
		if not self.acceptButton:
			return
		if self.readOnly:
			self.acceptButton.Hide()
			self.acceptButton.Disable()
			if self.cancelButton:
				self.cancelButton.SetPosition(118, 601)
				self.cancelButton.SetText(GetChestLocale("CHARACTER_CHEST_PREVIEW_CLOSE", "Kapat"))
		else:
			self.acceptButton.Show()
			self.acceptButton.Enable()
			self.acceptButton.SetText(GetChestLocale("CHARACTER_CHEST_UNPACK_ACCEPT", "Aktar"))
			if self.cancelButton:
				self.cancelButton.SetPosition(156, 601)
				self.cancelButton.SetText(uiScriptLocale.CANCEL)

	def __GetJobName(self, job):
		nameMap = {
			playersettingmodule.RACE_WARRIOR_M : "Savasci - E",
			playersettingmodule.RACE_WARRIOR_W : "Savasci - K",
			playersettingmodule.RACE_ASSASSIN_W : "Ninja - K",
			playersettingmodule.RACE_ASSASSIN_M : "Ninja - E",
			playersettingmodule.RACE_SURA_M : "Sura - E",
			playersettingmodule.RACE_SURA_W : "Sura - K",
			playersettingmodule.RACE_SHAMAN_W : "Saman - K",
			playersettingmodule.RACE_SHAMAN_M : "Saman - E",
		}
		return nameMap.get(job, "Karakter")

	def __FormatPlaytime(self, minutes):
		if minutes < 60:
			return "%ddk" % minutes
		hours = minutes / 60
		mins = minutes % 60
		if hours < 24:
			return "%dsa %ddk" % (hours, mins)
		days = hours / 24
		hours = hours % 24
		return "%dg %dsa" % (days, hours)

	def __RefreshCharInfo(self, name, job, level, st, ht, dx, iq, exp, playtime):
		if not self.charWnd:
			return

		self.charWnd.GetChild("Character_Name").SetText(name)
		self.charWnd.GetChild("Guild_Name").SetText(self.__FormatPlaytime(playtime))
		self.charWnd.GetChild("Level_Value").SetText(str(level))

		expValue = self.charWnd.GetChild2("Exp_Value")
		if expValue:
			expValue.SetText(constInfo.intWithCommas(exp))

		restExpValue = self.charWnd.GetChild2("RestExp_Value")
		if restExpValue:
			restExpValue.SetText("-")

		self.charWnd.GetChild("HTH_Value").SetText(str(ht))
		self.charWnd.GetChild("INT_Value").SetText(str(iq))
		self.charWnd.GetChild("STR_Value").SetText(str(st))
		self.charWnd.GetChild("DEX_Value").SetText(str(dx))

		for name in ("HP_Value", "SP_Value", "ATT_Value", "DEF_Value"):
			wnd = self.charWnd.GetChild2(name)
			if wnd:
				wnd.SetText("-")

		for name in ("MSPD_Value", "ASPD_Value", "CSPD_Value", "MATT_Value", "MDEF_Value", "ER_Value"):
			wnd = self.charWnd.GetChild2(name)
			if wnd:
				wnd.SetText("-")

		activePoint = self.charWnd.GetChild2("Active_Skill_Point_Value")
		if activePoint:
			activePoint.SetText("0")
		supportPoint = self.charWnd.GetChild2("Support_Skill_Point_Value")
		if supportPoint:
			supportPoint.SetText("0")

		if self.charActiveSkillGroupName:
			jobKey = int(job) % 4
			try:
				import uicharacter
				label = uicharacter.CharacterWindow.SKILL_GROUP_NAME_DICT[jobKey][self.previewSkillGroup]
			except:
				label = self.__GetJobName(job)
			self.charActiveSkillGroupName.SetText(label)

	def __ApplyFace(self, job):
		if not self.charWnd:
			return
		path = FACE_IMAGE_DICT.get(job, "icon/face/warrior_m.tga")
		try:
			self.charWnd.GetChild("Face_Image").LoadImage(path)
		except:
			pass

	def __WearPosFromItem(self, window, pos):
		equipStart = player.EQUIPMENT_SLOT_START
		if window == WINDOW_EQUIPMENT:
			if pos >= equipStart:
				return pos - equipStart
			return pos
		if pos >= equipStart:
			return pos - equipStart
		return None

	def __BuildItemMaps(self, itemList):
		self.invItems = {}
		self.equipItems = {}
		invMax = player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT
		equipStart = player.EQUIPMENT_SLOT_START

		for entry in itemList:
			if len(entry) < 6:
				continue
			window = int(entry[0])
			pos = int(entry[1])
			vnum = int(entry[2])
			count = int(entry[3])
			sockets = entry[4]
			attrs = entry[5]
			if vnum <= 0:
				continue
			data = (vnum, count, sockets, attrs)

			wearPos = self.__WearPosFromItem(window, pos)
			if wearPos is not None:
				self.equipItems[wearPos] = data
				continue

			if pos < invMax:
				self.invItems[pos] = data

	def __RefreshEquipSlots(self):
		if not self.equipSlot:
			return
		for slotIndex in (
			item.EQUIPMENT_BODY, item.EQUIPMENT_HEAD, item.EQUIPMENT_SHOES,
			item.EQUIPMENT_WRIST, item.EQUIPMENT_WEAPON, item.EQUIPMENT_NECK,
			item.EQUIPMENT_EAR, item.EQUIPMENT_UNIQUE1, item.EQUIPMENT_UNIQUE2,
			item.EQUIPMENT_ARROW, item.EQUIPMENT_SHIELD,
		):
			self.equipSlot.ClearSlot(slotIndex)
		for wearPos, data in self.equipItems.items():
			if not data or len(data) < 2:
				continue
			vnum = data[0]
			count = data[1]
			if count <= 1:
				count = 0
			slotIndex = player.EQUIPMENT_SLOT_START + int(wearPos)
			self.equipSlot.SetItemSlot(slotIndex, vnum, count)
		self.equipSlot.RefreshSlot()

	def __RefreshInvPage(self):
		if not self.invSlot:
			return
		for i in xrange(player.INVENTORY_PAGE_SIZE):
			self.invSlot.ClearSlot(i)
		pageBase = self.invPageIndex * player.INVENTORY_PAGE_SIZE
		for local in xrange(player.INVENTORY_PAGE_SIZE):
			pos = pageBase + local
			if pos not in self.invItems:
				continue
			data = self.invItems[pos]
			if not data or len(data) < 2:
				continue
			vnum = data[0]
			count = data[1]
			if count <= 1:
				count = 0
			self.invSlot.SetItemSlot(local, vnum, count)
		self.invSlot.RefreshSlot()

	def __OnSelectInvPage(self, pageIndex):
		self.invPageIndex = pageIndex
		for i, btn in enumerate(self.invPageButtons):
			if i == pageIndex:
				btn.Down()
			else:
				btn.SetUp()
		self.__RefreshInvPage()

	def __RefreshSkills(self, job, skillGroup):
		if not self.charWnd:
			return

		activeSlot = self.charWnd.GetChild("Skill_Active_Slot")
		supportSlot = self.charWnd.GetChild("Skill_ETC_Slot")

		for i in xrange(50):
			activeSlot.ClearSlot(i)
		for i in xrange(120):
			supportSlot.ClearSlot(i)

		skillLevelMap = {}
		for entry in self.skillList:
			if type(entry) not in (list, tuple) or len(entry) < 3:
				continue
			vnum = int(entry[0])
			if int(entry[2]) <= 0:
				continue
			skillLevelMap[vnum] = (int(entry[1]), int(entry[2]))

		if type(playersettingmodule.SKILL_INDEX_DICT) != type({}):
			playersettingmodule.DefineSkillIndexDict()

		jobKey = int(job) % 4
		groupKey = skillGroup if skillGroup in (1, 2) else 1
		try:
			jobDict = playersettingmodule.SKILL_INDEX_DICT[jobKey]
			activeList = jobDict.get(groupKey, ())
			supportList = jobDict.get("SUPPORT", ())
		except:
			activeList = ()
			supportList = ()

		for slotInGroup, skillVnum in enumerate(activeList):
			if not skillVnum:
				continue
			skillInfo = skillLevelMap.get(skillVnum)
			if not skillInfo:
				continue
			masterType, level = skillInfo
			realSlot = self.__GetRealSkillSlot(masterType, slotInGroup)
			activeSlot.SetSkillSlotNew(realSlot, skillVnum, masterType, level)
			activeSlot.SetSlotCountNew(realSlot, masterType, level)

		for slotInGroup, skillVnum in enumerate(supportList):
			if not skillVnum:
				continue
			skillInfo = skillLevelMap.get(skillVnum)
			if not skillInfo:
				continue
			masterType, level = skillInfo
			supportSlotIndex = 101 + slotInGroup
			realSlot = self.__GetETCSkillRealSlotIndex(supportSlotIndex)
			supportSlot.SetSkillSlot(realSlot, skillVnum, level)
			supportSlot.SetSlotCountNew(realSlot, masterType, level)

		activeSlot.RefreshSlot()
		supportSlot.RefreshSlot()

	def __OnOverInEquip(self, slotIndex):
		wearPos = int(slotIndex) - player.EQUIPMENT_SLOT_START
		if wearPos < 0:
			wearPos = int(slotIndex)
		self.__ShowItemTooltip(self.equipItems.get(wearPos))

	def __OnOverInInv(self, localIndex):
		pos = self.invPageIndex * player.INVENTORY_PAGE_SIZE + localIndex
		self.__ShowItemTooltip(self.invItems.get(pos))

	def __ShowItemTooltip(self, data):
		if not self.tooltipItem or not data:
			return
		if len(data) < 4:
			return
		vnum = data[0]
		sockets = data[2]
		attrs = data[3]
		if vnum == 0:
			return
		self.tooltipItem.ClearToolTip()
		metinSlot = []
		for val in sockets:
			metinSlot.append(val)
		attrSlot = []
		for attr in attrs:
			if len(attr) >= 2:
				attrSlot.append((int(attr[0]), int(attr[1])))
			else:
				attrSlot.append((0, 0))
		self.tooltipItem.AddItemData(vnum, metinSlot, attrSlot)
		self.tooltipItem.ShowToolTip()

	def __OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def Close(self):
		if self.charWnd:
			self.charWnd.Hide()
		if self.invWnd:
			self.invWnd.Hide()
		if self.biologistPanel:
			self.biologistPanel.Hide()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __OnAccept(self):
		if self.readOnly:
			return
		if self.itemCell < 0 or self.targetPid <= 0:
			return
		if not CanStartCharacterChestMutation():
			NotifyCharacterChestBlocked()
			return
		SetCharacterChestBusy(True)
		net.SendCharacterChestPacket(CHARACTER_CHEST_CG_UNPACK, self.targetPid, self.itemCell, "")
		self.Close()
