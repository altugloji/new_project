import ui
import cri
import item
import player
import constInfo
import uiScriptLocale

EMPTY_FILL_VNUM = 8
COLS = 5
ROWS = 8
SLOTS_PER_PAGE = COLS * ROWS


class KygnChestInfo(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.chestBoard = None
		self.__Initialize()
		self.__Ekran()

	def __Initialize(self):
		self.cell = 0
		self.chestVnum = 0
		self.chestCount = 0
		self.__Initialize2()

	def __Initialize2(self):
		self.slotList = []
		for i in xrange(5):
			self.slotList += [[[0, 0, [0, 0]]]]
			for j in xrange(1, SLOTS_PER_PAGE):
				self.slotList[i] += [[0, 0]]
		self.curItemPage = 0
		self.maxPage = 0
		self.curPage = 0

	def __Ekran(self):
		KygnPyYukle = ui.PythonScriptLoader()
		KygnPyYukle.LoadScriptFile(self, "UIScript/kygnchestinfo.py")

		KygnObject = self.GetChild
		self.chestBoard = KygnObject("ChestBoard")
		self.ItemSlot = KygnObject("ItemSlot")
		self.PrevButton = KygnObject("PrevButton")
		self.CurrentPage = KygnObject("CurrentPage")
		self.NextButton = KygnObject("NextButton")

		self.chestBoard.SetCloseEvent(ui.__mem_func__(self.OnClose))
		self.ItemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInRewardSlot))
		self.ItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.PrevButton.SetEvent(ui.__mem_func__(self.OnClickPrevPage))
		self.NextButton.SetEvent(ui.__mem_func__(self.OnClickNextPage))

	def __UpdatePageLabel(self):
		self.CurrentPage.SetText("Sayfa %d" % (self.curPage + 1))

	def __OverInRewardSlot(self, slotNumber):
		self.OverInRewardItem(slotNumber)

	def OnClickPrevPage(self):
		if int(self.curPage) <= 0:
			return
		self.curPage -= 1
		self.__UpdatePageLabel()
		self.UpdateCurItemList(self.curPage)

	def OnClickNextPage(self):
		if int(self.curPage) >= int(self.maxPage):
			return
		self.curPage += 1
		self.__UpdatePageLabel()
		self.UpdateCurItemList(self.curPage)

	def FindBlank(self, iSize):
		for page in xrange(5):
			for i in xrange(SLOTS_PER_PAGE):
				if self.slotList[page][i][0] != 0:
					continue

				if iSize <= 1:
					self.curItemPage = page
					if int(self.maxPage) < page:
						self.maxPage = page
					return i

				lastIdx = i + (int(iSize) - 1) * COLS
				if lastIdx > SLOTS_PER_PAGE - 1:
					continue

				valid = True
				for dy in xrange(int(iSize)):
					idx = i + dy * COLS
					if idx >= SLOTS_PER_PAGE or self.slotList[page][idx][0] != 0:
						valid = False
						break
				if not valid:
					continue

				for dy in xrange(1, int(iSize)):
					idx = i + dy * COLS
					self.slotList[page][idx][0] = EMPTY_FILL_VNUM
					self.slotList[page][idx][1] = 0

				self.curItemPage = page
				if int(self.maxPage) < page:
					self.maxPage = page
				return i
		return -1

	def ClearChest(self):
		for i in xrange(SLOTS_PER_PAGE):
			self.ItemSlot.ClearSlot(i)
		self.__Initialize2()
		self.curPage = 0
		self.__UpdatePageLabel()

	def AddItem(self, iVnum, iCount):
		item.SelectItem(iVnum)
		_sizeX, sizeY = item.GetItemSize()
		iPos = self.FindBlank(sizeY)
		if iPos == -1:
			return
		self.slotList[int(self.curItemPage)][iPos][0] = int(iVnum)
		self.slotList[int(self.curItemPage)][iPos][1] = int(iCount)

	def UpdateCurItemList(self, page):
		for i in xrange(SLOTS_PER_PAGE):
			self.ItemSlot.ClearSlot(i)
			if self.slotList[page][i][0] != EMPTY_FILL_VNUM:
				self.ItemSlot.SetItemSlot(i, self.slotList[page][i][0], self.slotList[page][i][1])

	def ShowChestRewards(self, chestCell):
		self.cell = chestCell
		chestVnum = player.GetItemIndex(player.INVENTORY, chestCell)
		chestCount = player.GetItemCount(player.INVENTORY, chestCell)
		if chestVnum <= 0 or chestCount <= 0:
			return
		self.chestVnum = chestVnum
		self.chestCount = chestCount
		constInfo.CD_CUR_CHEST_CELL = chestCell

		cri.GetChestRewardInfo(chestVnum)

	def ShowChestRewardsWithVnum(self, chestVnum):
		if chestVnum <= 0:
			self.OnClose()
			return
		self.cell = 753
		constInfo.CD_CUR_CHEST_CELL = 753

		self.chestVnum = chestVnum
		self.chestCount = 0
		cri.GetChestRewardInfo(chestVnum)

	def CheckChestPos(self):
		if constInfo.CD_CUR_CHEST_CELL == 753:
			return

		self.chestCount = player.GetItemCount(player.INVENTORY, constInfo.CD_CUR_CHEST_CELL)
		if self.chestCount <= 0:
			self.OnClose()

	def OverInRewardItem(self, selectedSlotPos):
		if not self.tooltipItem:
			return
		vnum = self.slotList[int(self.curPage)][selectedSlotPos][0]
		if vnum == EMPTY_FILL_VNUM or vnum == 0:
			return
		self.tooltipItem.SetItemToolTip(vnum)

	def OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	def Open(self):
		# if self.chestBoard:
			# self.chestBoard.SetTitleName(getattr(uiScriptLocale, "CHEST_INSPECTOR_TITLE", "Chest insight"))
		self.curPage = 0
		self.UpdateCurItemList(0)
		self.__UpdatePageLabel()
		self.SetTop()
		self.Show()

	def OnClose(self):
		self.__Initialize()
		self.curPage = 0
		if getattr(self, "CurrentPage", None):
			self.__UpdatePageLabel()
		constInfo.CD_CUR_CHEST_CELL = 753
		self.Hide()

	def OnPressEscapeKey(self):
		self.OnClose()
		return True

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()
