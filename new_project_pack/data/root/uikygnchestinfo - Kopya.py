import ui
import net
import app
import cri
import item
import player
import constInfo

EMPTY_FILL_VNUM = 8

class KygnChestInfo(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.__Initialize()
		self.__Ekran()

	def __Initialize(self):
		self.cell = 0
		self.chestVnum = 0
		self.chestCount = 0
		self.__Initialize2()

	def __Initialize2(self):
		self.slotList = []
		for i in range(5):
			self.slotList += [[[0, 0, [0, 0]]]]
			for j in range(1, 60):
				self.slotList[i] += [[0, 0]]
		self.curItemPage = 0
		self.maxPage = 0
		self.curPage = 0


	def __Ekran(self):
		KygnPyYukle = ui.PythonScriptLoader()
		KygnPyYukle.LoadScriptFile(self, "UIScript/kygnchestinfo.py")

		KygnObject = self.GetChild
		self.titleBar = KygnObject("titleBar")
		self.chestSlot = KygnObject("chestSlot")
		self.ItemSlot = KygnObject("ItemSlot")
		self.PrevButton = KygnObject("PrevButton")
		self.CurrentPage = KygnObject("CurrentPage")
		self.NextButton = KygnObject("NextButton")
		# self.x1Button = KygnObject("x1Button")
		# self.x20Button = KygnObject("x20Button")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.OnClose))
		self.chestSlot.SetOverInItemEvent(lambda slotNumber, arg = True: self.OverInItem(slotNumber, arg))
		self.chestSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.ItemSlot.SetOverInItemEvent(lambda slotNumber, arg = False: self.OverInItem(slotNumber, arg))
		self.ItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.PrevButton.SetEvent(ui.__mem_func__(self.OnClickPrevPage))
		self.NextButton.SetEvent(ui.__mem_func__(self.OnClickNextPage))
		# self.x1Button.SetEvent(ui.__mem_func__(self.OnClickUseChest), 1)

		# if app.OPEN_COLLECTIVE_CHEST:
			# self.x20Button.SetEvent(ui.__mem_func__(self.OnClickUseChest), 20)
		# else:
			# self.x20Button.Disable()

	# def OnClickUseChest(self, arg):
		# if arg == 1:
			# net.SendItemUsePacket(player.INVENTORY, self.cell)
		# elif app.OPEN_COLLECTIVE_CHEST:
			# net.SendOpenCollectiveChestPacket(self.cell)

	def OnClickPrevPage(self):
		if int(self.curPage) <= 0:
			return
		self.curPage-=1
		self.CurrentPage.SetText("%d" % (self.curPage+1))
		self.UpdateCurItemList(self.curPage)

	def OnClickNextPage(self):
		if int(self.curPage) >= int(self.maxPage):
			return
		self.curPage+=1
		self.CurrentPage.SetText("%d" % (self.curPage+1))
		self.UpdateCurItemList(self.curPage)

	def FindBlank(self, iSize):
		for page in xrange(5):
			for i in xrange(60):
				if self.slotList[page][i][0] == 0:
					if iSize == 3:
						if i + 10 > 59 or i + 20 > 59:## Bu eğer ki altında ki 3 slotta dolu ise bir diğer sayfaya yönlendiriyor!
							break
						self.slotList[page][i + 10][0] = EMPTY_FILL_VNUM
						self.slotList[page][i + 20][0] = EMPTY_FILL_VNUM
					elif iSize == 2:
						if i + 10 > 59:## Bu eğer ki altında ki 2 slotta dolu ise bir diğer sayfaya yönlendiriyor!
							break
						self.slotList[page][i + 10][0] = EMPTY_FILL_VNUM

					self.curItemPage = page
					if int(self.maxPage) < page:
						self.maxPage = page
					return i
		return -1

	def ClearChest(self):
		for i in xrange(60):
			self.ItemSlot.ClearSlot(i)
		self.__Initialize2()
		self.CurrentPage.SetText("1")

	def AddItem(self, iVnum, iCount):
		item.SelectItem(iVnum)
		sizeX, sizeY = item.GetItemSize()
		iPos = -1
		while iPos == -1:
			iPos = self.FindBlank(sizeY)
			self.slotList[int(self.curItemPage)][iPos][0] = int(iVnum)
			self.slotList[int(self.curItemPage)][iPos][1] = int(iCount)

	def UpdateCurItemList(self, page):
		for i in xrange(60):
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
		# self.x1Button.Enable()
		# self.x20Button.Enable()
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
		# self.x1Button.Disable()
		# self.x20Button.Disable()
		cri.GetChestRewardInfo(chestVnum)

	def CheckChestPos(self):
		if constInfo.CD_CUR_CHEST_CELL == 753:
			return

		self.chestCount = player.GetItemCount(player.INVENTORY, constInfo.CD_CUR_CHEST_CELL)
		if self.chestCount <= 0:
			self.OnClose()
		self.chestSlot.SetItemSlot(0, self.chestVnum, self.chestCount)

	def OverInItem(self, selectedSlotPos, arg):
		if self.tooltipItem:
			if arg == False:
				self.tooltipItem.SetItemToolTip(self.slotList[int(self.curPage)][selectedSlotPos][0])
			else:
				self.tooltipItem.SetItemToolTip(self.chestVnum)

	def OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip


	def Open(self):
		self.chestSlot.SetItemSlot(0, self.chestVnum, self.chestCount)
		self.UpdateCurItemList(0)
		self.SetTop()
		self.Show()

	def OnClose(self):
		self.__Initialize()
		self.CurrentPage.SetText("1")
		# constInfo.CD_CUR_CHEST_WINDOW = 753
		constInfo.CD_CUR_CHEST_CELL = 753
		self.Hide()

	def OnPressEscapeKey(self):
		self.OnClose()
		return True

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()
