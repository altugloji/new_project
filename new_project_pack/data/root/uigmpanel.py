import ui
import net
import grp
import localeInfo
import uiScriptLocale
import chr
import player
import wndMgr
import _weakref

GM_PLAYER_PANEL_MARGIN_X = 10
GM_PLAYER_PANEL_CONTENT_W = 488
GM_PLAYER_PANEL_ROW_HEIGHT = 22
GM_PLAYER_PANEL_ROW_WIDTH = GM_PLAYER_PANEL_CONTENT_W
GM_PLAYER_PANEL_VIEW_COUNT = 20
GM_PLAYER_PANEL_HEADER_H = 20

GM_PLAYER_PANEL_SEARCH_Y = 33
GM_PLAYER_PANEL_SEARCH_H = 18
GM_PLAYER_PANEL_SEARCH_LABEL_W = 40
GM_PLAYER_PANEL_COUNT_Y = GM_PLAYER_PANEL_SEARCH_Y + GM_PLAYER_PANEL_SEARCH_H + 10
GM_PLAYER_PANEL_COUNT_H = 17
GM_PLAYER_PANEL_LIST_X = GM_PLAYER_PANEL_MARGIN_X
GM_PLAYER_PANEL_LIST_Y = GM_PLAYER_PANEL_COUNT_Y + GM_PLAYER_PANEL_COUNT_H + 4
GM_PLAYER_PANEL_LIST_W = GM_PLAYER_PANEL_CONTENT_W
GM_PLAYER_PANEL_LISTBOX_H = GM_PLAYER_PANEL_VIEW_COUNT * GM_PLAYER_PANEL_ROW_HEIGHT
GM_PLAYER_PANEL_LIST_H = (GM_PLAYER_PANEL_HEADER_H + 2) + GM_PLAYER_PANEL_LISTBOX_H + 6
GM_PLAYER_PANEL_WINDOW_HEIGHT = GM_PLAYER_PANEL_LIST_Y + GM_PLAYER_PANEL_LIST_H + 10

GM_PLAYER_PANEL_COL_NAME_X = 10
GM_PLAYER_PANEL_COL_LEVEL_X = 148
GM_PLAYER_PANEL_COL_CH_X = 198
GM_PLAYER_PANEL_COL_MAP_X = 248

GM_PLAYER_PANEL_DC_BTN_W = 40
GM_PLAYER_PANEL_DC_BTN_H = 18
GM_PLAYER_PANEL_GO_BTN_W = 88
GM_PLAYER_PANEL_GO_BTN_H = 18
GM_PLAYER_PANEL_GO_BTN_RIGHT_INSET = 1
GM_PLAYER_PANEL_BTN_GAP = 5
GM_PLAYER_PANEL_SEARCH_PLACEHOLDER_COLOR = 0xFF888888

GM_PLAYER_PANEL_COUNT_CH_GAP = 50
GM_PLAYER_PANEL_COUNT_CH_TEXT_W = 52
GM_PLAYER_PANEL_COUNT_LABEL_X = 10
GM_PLAYER_PANEL_COUNT_VALUE_X = 58
GM_PLAYER_PANEL_COUNT_CH_X = 120

GM_PLAYER_PANEL_COLOR_ZEBRA_GRAY_A = grp.GenerateColor(0.24, 0.24, 0.24, 0.92)
GM_PLAYER_PANEL_COLOR_ZEBRA_GRAY_B = grp.GenerateColor(0.30, 0.30, 0.30, 0.92)
GM_PLAYER_PANEL_COLOR_ROW_SELECT = grp.GenerateColor(0.36, 0.36, 0.36, 0.78)
GM_PLAYER_PANEL_COLOR_WHITE = 0xFFFFFFFF
GM_PLAYER_PANEL_COLOR_COUNT_GREEN = 0xFF55DD55


def _GmLocale(key, default):
	try:
		val = getattr(uiScriptLocale, key)
	except:
		return default
	if not val or val == key:
		return default
	return val


def _GmApplyTextOutline(textLine):
	if textLine:
		textLine.SetOutline()


def _GmApplyButtonTextOutline(button):
	if button and button.ButtonText:
		button.ButtonText.SetOutline()


class GmPlayerSearchEdit(ui.EditLine):
	def __init__(self, panel):
		ui.EditLine.__init__(self)
		self.panel = panel

	def OnIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self)
		if self.panel:
			self.panel.OnSearchUpdate()


class GmPlayerPanelRow(ui.ListBoxEx.Item):
	def __init__(self, name, level, channel, mapIndex, pid, rowIndex):
		ui.ListBoxEx.Item.__init__(self)
		self.name = name
		self.pid = pid
		self.rowIndex = rowIndex

		self.bgBar = ui.Bar()
		self.bgBar.SetParent(self)
		self.bgBar.SetPosition(0, 0)
		self.bgBar.SetSize(GM_PLAYER_PANEL_ROW_WIDTH, GM_PLAYER_PANEL_ROW_HEIGHT)
		if rowIndex % 2 == 0:
			self.bgBar.SetColor(GM_PLAYER_PANEL_COLOR_ZEBRA_GRAY_A)
		else:
			self.bgBar.SetColor(GM_PLAYER_PANEL_COLOR_ZEBRA_GRAY_B)
		self.bgBar.Show()

		self.goBtnX = GM_PLAYER_PANEL_ROW_WIDTH - GM_PLAYER_PANEL_GO_BTN_W - GM_PLAYER_PANEL_GO_BTN_RIGHT_INSET
		self.dcBtnX = self.goBtnX - GM_PLAYER_PANEL_DC_BTN_W - GM_PLAYER_PANEL_BTN_GAP

		self.nameText = ui.TextLine()
		self.nameText.SetParent(self)
		self.nameText.SetPosition(GM_PLAYER_PANEL_COL_NAME_X, 4)
		self.nameText.SetText(name)
		_GmApplyTextOutline(self.nameText)
		self.nameText.Show()

		self.levelText = ui.TextLine()
		self.levelText.SetParent(self)
		self.levelText.SetPosition(GM_PLAYER_PANEL_COL_LEVEL_X, 4)
		self.levelText.SetText(str(level))
		_GmApplyTextOutline(self.levelText)
		self.levelText.Show()

		self.channelText = ui.TextLine()
		self.channelText.SetParent(self)
		self.channelText.SetPosition(GM_PLAYER_PANEL_COL_CH_X, 4)
		self.channelText.SetText("CH%d" % channel)
		_GmApplyTextOutline(self.channelText)
		self.channelText.Show()

		self.mapText = ui.TextLine()
		self.mapText.SetParent(self)
		self.mapText.SetPosition(GM_PLAYER_PANEL_COL_MAP_X, 4)
		self.mapText.SetText("Map %d" % mapIndex)
		_GmApplyTextOutline(self.mapText)
		self.mapText.Show()

		self.dcButton = ui.Button()
		self.dcButton.SetParent(self)
		self.dcButton.SetPosition(self.dcBtnX, 2)
		self.dcButton.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
		self.dcButton.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
		self.dcButton.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
		self.dcButton.SetText(_GmLocale("GM_PLAYER_PANEL_DC", "DC"))
		_GmApplyButtonTextOutline(self.dcButton)
		self.dcButton.SAFE_SetEvent(self.__OnDc)
		self.dcButton.Show()

		self.goButton = ui.Button()
		self.goButton.SetParent(self)
		self.goButton.SetPosition(self.goBtnX, 2)
		self.goButton.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
		self.goButton.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
		self.goButton.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
		self.goButton.SetText(_GmLocale("GM_PLAYER_PANEL_GO", "WARP"))
		_GmApplyButtonTextOutline(self.goButton)
		self.goButton.SAFE_SetEvent(self.__OnGo)
		self.goButton.Show()

		self.SetSize(GM_PLAYER_PANEL_ROW_WIDTH, GM_PLAYER_PANEL_ROW_HEIGHT)

	def __del__(self):
		ui.ListBoxEx.Item.__del__(self)

	def OnSelectedRender(self):
		x, y = self.GetGlobalPosition()
		grp.SetColor(GM_PLAYER_PANEL_COLOR_ROW_SELECT)
		grp.RenderBar(x, y, self.GetWidth(), self.GetHeight())

	def __IsDcButtonClick(self):
		mx, my = wndMgr.GetMousePosition()
		bx, by = self.dcButton.GetGlobalPosition()
		return (bx <= mx < bx + GM_PLAYER_PANEL_DC_BTN_W and
			by <= my < by + GM_PLAYER_PANEL_DC_BTN_H)

	def __IsGoButtonClick(self):
		mx, my = wndMgr.GetMousePosition()
		bx, by = self.goButton.GetGlobalPosition()
		return (bx <= mx < bx + GM_PLAYER_PANEL_GO_BTN_W and
			by <= my < by + GM_PLAYER_PANEL_GO_BTN_H)

	def OnMouseLeftButtonDown(self):
		if self.__IsDcButtonClick():
			self.__OnDc()
			return
		if self.__IsGoButtonClick():
			self.__OnGo()
			return
		ui.ListBoxEx.Item.OnMouseLeftButtonDown(self)

	def OnMouseLeftButtonDoubleClick(self):
		self.__OnGo()

	def __OnGo(self):
		if self.name:
			net.SendGmPlayerPanelWarpPacket(self.name)

	def __OnDc(self):
		if self.name:
			net.SendChatPacket("/dc " + self.name)


class GmPlayerPanelWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.board = None
		self.searchEdit = None
		self.searchPlaceholder = None
		self.searchLabel = None
		self.listArea = None
		self.listBox = None
		self.scrollBar = None
		self.countSlot = None
		self.countText = None
		self.countTotalLabel = None
		self.countTotalValue = None
		self.countChTexts = []
		self.headerTexts = []
		self.selectedName = ""
		self.playerList = []
		self.onlineTotal = 0
		self.onlineCh = [0, 0, 0, 0]
		self.filterText = ""
		self.IsLoaded = False
		self.Initialize()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Initialize(self):
		self.board = None
		self.searchEdit = None
		self.searchPlaceholder = None
		self.searchLabel = None
		self.listArea = None
		self.listBox = None
		self.scrollBar = None
		self.countSlot = None
		self.countText = None
		self.countTotalLabel = None
		self.countTotalValue = None
		self.countChTexts = []
		self.headerTexts = []
		self.selectedName = ""
		self.playerList = []
		self.onlineTotal = 0
		self.onlineCh = [0, 0, 0, 0]
		self.filterText = ""

	@ui.WindowDestroy
	def Destroy(self):
		self.__ClearHeaders()
		self.__ClearCountTexts()
		self.Initialize()
		self.ClearDictionary()
		self.Hide()

	def __ClearHeaders(self):
		for txt in self.headerTexts:
			txt.Hide()
		self.headerTexts = []

	def __ClearCountTexts(self):
		if self.countTotalLabel:
			self.countTotalLabel.Hide()
		if self.countTotalValue:
			self.countTotalValue.Hide()
		for txt in self.countChTexts:
			txt.Hide()
		self.countChTexts = []

	def __BuildCountTexts(self, countSlot):
		self.__ClearCountTexts()
		if self.countText:
			self.countText.Hide()

		self.countTotalLabel = ui.TextLine()
		self.countTotalLabel.SetParent(countSlot)
		self.countTotalLabel.SetPosition(GM_PLAYER_PANEL_COUNT_LABEL_X, 2)
		self.countTotalLabel.SetText("Toplam:")
		self.countTotalLabel.SetPackedFontColor(GM_PLAYER_PANEL_COLOR_WHITE)
		_GmApplyTextOutline(self.countTotalLabel)
		self.countTotalLabel.Show()

		self.countTotalValue = ui.TextLine()
		self.countTotalValue.SetParent(countSlot)
		self.countTotalValue.SetPosition(GM_PLAYER_PANEL_COUNT_VALUE_X, 2)
		self.countTotalValue.SetPackedFontColor(GM_PLAYER_PANEL_COLOR_COUNT_GREEN)
		_GmApplyTextOutline(self.countTotalValue)
		self.countTotalValue.Show()

		x = GM_PLAYER_PANEL_COUNT_CH_X
		for i in xrange(4):
			txt = ui.TextLine()
			txt.SetParent(countSlot)
			txt.SetPosition(x, 1)
			txt.SetPackedFontColor(GM_PLAYER_PANEL_COLOR_WHITE)
			_GmApplyTextOutline(txt)
			txt.Show()
			self.countChTexts.append(txt)
			x += GM_PLAYER_PANEL_COUNT_CH_TEXT_W + GM_PLAYER_PANEL_COUNT_CH_GAP

	def __BuildColumnHeaders(self, parent):
		self.__ClearHeaders()
		headers = (
			(GM_PLAYER_PANEL_COL_NAME_X, _GmLocale("GM_PLAYER_PANEL_COL_NAME", "Oyuncu Adi")),
			(GM_PLAYER_PANEL_COL_LEVEL_X, _GmLocale("GM_PLAYER_PANEL_COL_LEVEL", "Lv.")),
			(GM_PLAYER_PANEL_COL_CH_X, _GmLocale("GM_PLAYER_PANEL_COL_CH", "CH")),
			(GM_PLAYER_PANEL_COL_MAP_X, _GmLocale("GM_PLAYER_PANEL_COL_MAP", "Map")),
		)
		for x, label in headers:
			txt = ui.TextLine()
			txt.SetParent(parent)
			txt.SetPosition(x, 4)
			txt.SetText(label)
			txt.SetPackedFontColor(GM_PLAYER_PANEL_COLOR_WHITE)
			_GmApplyTextOutline(txt)
			txt.Show()
			self.headerTexts.append(txt)

	def __LoadWindow(self):
		if self.IsLoaded:
			return

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/gmpanelwindow.py")
		except:
			import exception
			exception.Abort("GmPlayerPanelWindow.__LoadWindow")

		try:
			self.board = self.GetChild("Board")
			self.searchLabel = self.GetChild("SearchLabel")
			searchSlot = self.GetChild("SearchSlot")
			self.countSlot = self.GetChild("CountSlot")
			self.countText = self.GetChild("CountText")
		except:
			import exception
			exception.Abort("GmPlayerPanelWindow.BindObject")

		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.SetTitleName(_GmLocale("GM_PLAYER_PANEL_TITLE", "GM Oyuncu Paneli"))
		self.searchLabel.SetText(_GmLocale("GM_PLAYER_PANEL_SEARCH", "Ara:"))
		_GmApplyTextOutline(self.searchLabel)

		editX = GM_PLAYER_PANEL_SEARCH_LABEL_W + 2
		editY = 2

		self.searchPlaceholder = ui.TextLine()
		self.searchPlaceholder.SetParent(searchSlot)
		self.searchPlaceholder.SetPosition(editX, editY)
		self.searchPlaceholder.SetText(_GmLocale("GM_PLAYER_PANEL_SEARCH_HINT", "Oyuncu ara..."))
		self.searchPlaceholder.SetPackedFontColor(GM_PLAYER_PANEL_SEARCH_PLACEHOLDER_COLOR)
		_GmApplyTextOutline(self.searchPlaceholder)
		self.searchPlaceholder.Show()

		self.searchEdit = GmPlayerSearchEdit(self)
		self.searchEdit.SetParent(searchSlot)
		self.searchEdit.SetPosition(editX, editY)
		self.searchEdit.SetSize(searchSlot.GetWidth() - GM_PLAYER_PANEL_SEARCH_LABEL_W - 6, 14)
		self.searchEdit.SetMax(24)
		_GmApplyTextOutline(self.searchEdit)
		self.searchEdit.Show()

		self.__BuildCountTexts(self.countSlot)

		self.listArea = ui.Window()
		self.listArea.SetParent(self.board)
		self.listArea.SetPosition(GM_PLAYER_PANEL_LIST_X, GM_PLAYER_PANEL_LIST_Y)
		self.listArea.SetSize(GM_PLAYER_PANEL_LIST_W, GM_PLAYER_PANEL_LIST_H)
		self.listArea.Show()

		self.__BuildColumnHeaders(self.listArea)

		listY = GM_PLAYER_PANEL_HEADER_H + 2
		listH = GM_PLAYER_PANEL_LISTBOX_H

		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(self.listArea)
		self.listBox.SetPosition(0, listY)
		# SetViewItemCount before SetItemSize/SetItemStep: __UpdateSize uses viewItemCount.
		self.listBox.SetViewItemCount(GM_PLAYER_PANEL_VIEW_COUNT)
		self.listBox.SetItemSize(GM_PLAYER_PANEL_ROW_WIDTH, GM_PLAYER_PANEL_ROW_HEIGHT)
		self.listBox.SetItemStep(GM_PLAYER_PANEL_ROW_HEIGHT)
		self.listBox.SetSize(GM_PLAYER_PANEL_LIST_W - 20, listH)
		self.listBox.SetSelectEvent(ui.__mem_func__(self.__OnSelectRow))
		self.listBox.Show()

		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self.listArea)
		self.scrollBar.SetPosition(GM_PLAYER_PANEL_LIST_W - 16, listY)
		self.scrollBar.SetScrollBarSize(listH)
		self.scrollBar.Show()
		self.listBox.SetScrollBar(_weakref.proxy(self.scrollBar))

		self.IsLoaded = True

	def Open(self):
		if not chr.IsGameMaster(player.GetMainCharacterIndex()):
			return

		self.__LoadWindow()
		if not self.IsLoaded:
			return

		self.filterText = ""
		self.selectedName = ""
		self.onlineTotal = 0
		self.onlineCh = [0, 0, 0, 0]
		if self.searchEdit:
			self.searchEdit.SetText("")
		self.__RefreshSearchPlaceholder()
		self.__RefreshCountText()

		self.SetCenterPosition()
		self.Show()
		self.SetTop()
		net.SendGmPlayerPanelRequestListPacket()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnMouseWheel(self, nLen):
		if self.listBox:
			return self.listBox.OnMouseWheel(nLen)
		return False

	def SetPlayerList(self, playerList, total=0, ch1=0, ch2=0, ch3=0, ch4=0):
		self.playerList = []
		if playerList:
			for entry in playerList:
				if len(entry) < 5:
					continue
				name, level, channel, mapIndex, pid = entry[0], entry[1], entry[2], entry[3], entry[4]
				self.playerList.append((name, level, channel, mapIndex, pid))

		self.onlineTotal = int(total)
		self.onlineCh = [int(ch1), int(ch2), int(ch3), int(ch4)]
		if self.onlineTotal <= 0 and not sum(self.onlineCh) and self.playerList:
			self.__ComputeOnlineCountsFromList()
		self.__RefreshCountText()
		self.__RefreshList()

	def __ComputeOnlineCountsFromList(self):
		chCounts = [0, 0, 0, 0]
		for entry in self.playerList:
			channel = int(entry[2])
			if 1 <= channel <= 4:
				chCounts[channel - 1] += 1
		self.onlineCh = chCounts
		self.onlineTotal = len(self.playerList)

	def __RefreshCountText(self):
		if not self.countTotalValue:
			return
		self.countTotalValue.SetText(str(self.onlineTotal))
		for i in xrange(4):
			if i < len(self.countChTexts):
				self.countChTexts[i].SetText("CH%d: %d" % (i + 1, self.onlineCh[i]))

	def __RefreshSearchPlaceholder(self):
		if not self.searchPlaceholder or not self.searchEdit:
			return
		if self.searchEdit.GetText():
			self.searchPlaceholder.Hide()
		else:
			self.searchPlaceholder.Show()

	def OnSearchUpdate(self):
		if not self.searchEdit:
			return
		self.filterText = self.searchEdit.GetText().lower()
		self.__RefreshSearchPlaceholder()
		self.__RefreshList()

	def __OnSelectRow(self, rowItem):
		if rowItem:
			self.selectedName = rowItem.name

	def __GetFilteredList(self):
		if not self.filterText:
			return self.playerList

		out = []
		for entry in self.playerList:
			name = entry[0]
			if self.filterText in name.lower():
				out.append(entry)
		return out

	def __RefreshList(self):
		if not self.listBox:
			return

		self.listBox.RemoveAllItems()
		self.selectedName = ""
		filtered = self.__GetFilteredList()

		for idx, entry in enumerate(filtered):
			name, level, channel, mapIndex, pid = entry
			self.listBox.AppendItem(
				GmPlayerPanelRow(name, level, channel, mapIndex, pid, idx))

		if self.scrollBar:
			if len(filtered) > GM_PLAYER_PANEL_VIEW_COUNT:
				self.scrollBar.SetMiddleBarSize(
					float(GM_PLAYER_PANEL_VIEW_COUNT) / float(len(filtered)))
				self.scrollBar.Show()
			else:
				self.scrollBar.SetPos(0)
				self.scrollBar.Hide()

		self.listBox.SetBasePos(0)
