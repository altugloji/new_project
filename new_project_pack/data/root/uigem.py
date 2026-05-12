#author: dracaryS

import ui, constInfo, uiCommon, localeInfo

import gem, app, net, item, player, wndMgr

def SendCommand(str):
	net.SendChatPacket("/gem " + str)

IMG_DIR = "d:/ymir work/ui/gemshop/"

class ShopWindow(ui.ScriptWindow):
	__children = {}
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadWindow()

	def Destroy(self):
		self.ClearDictionary()
		self.__CloseQuestionDialog()
		self.__children = {}
		self.Hide()

	def __LoadWindow(self):
		self.Destroy()

		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "uiscript/gemshopwindow.py")
		except:
			import exception
			exception.Abort("uiGem.ShopWindow.LoadDialog.LoadObject")

		GetObject = self.GetChild

		GetObject("refresh_button").SetEvent(ui.__mem_func__(self.__ClickRefreshButton))
		GetObject("back_btn").SetEvent(ui.__mem_func__(self.__PageFormula), -1)
		GetObject("next_btn").SetEvent(ui.__mem_func__(self.__PageFormula), 1)
		GetObject("board").SetCloseEvent(ui.__mem_func__(self.Close))

		board = GetObject("bg_slots")

		itemSlot = self.ElementDictionary["itemSlot"] = ui.GridSlotWindow()
		itemSlot.SetParent(board)
		itemSlot.SetPosition(8, 28)
		itemSlot.ArrangeSlot(0, 3, 3, 32, 32, 13, 26)
		itemSlot.SAFE_SetButtonEvent("LEFT", "EXIST", self.__SelectItemSlot)
		itemSlot.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
		itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		itemSlot.Show()

		i = 0
		for j in xrange(gem.X_GRID):
			for x in xrange(gem.Y_GRID):
				icon = self.ElementDictionary["icon_{}".format(i)] = ui.ImageBox()
				icon.SetParent(board)
				icon.SetPosition((8+(x*45))-2, (28+(j*58))+40)
				icon.LoadImage("d:/ymir work/ui/gemshop/gemshop_gemicon.sub")

				price = self.ElementDictionary["price_{}".format(i)] = ui.TextLine()
				price.SetParent(board)
				price.SetPosition((8+(x*45))+14, (28+(j*58))+39)
				i+=1
	
	def __PageFormula(self, value):
		self.__GoToPage(self.__children["pageIndex"] + value)

	def __GoToPage(self, pageIndex):
		if pageIndex < 0 or pageIndex >= gem.PAGE_COUNT:
			return
		self.__children["pageIndex"] = pageIndex
		self.Refresh()

	def __GetRealSlotIndex(self, slotIndex):
		return slotIndex + self.__children["pageIndex"] * gem.SLOT_COUNT

	def Refresh(self):
		pageIndex = self.__children["pageIndex"]
		self.GetChild("page_text").SetText("{}/{}".format(pageIndex + 1, gem.PAGE_COUNT))

		itemSlot = self.GetChild("itemSlot")

		opened_slot_count = gem.GetSlotCount()
		for i in xrange(gem.SLOT_COUNT):
			slotIndex = self.__GetRealSlotIndex(i)

			itemSlot.ClearSlot(i)

			vnum, count, price, buyed = gem.GetItem(slotIndex)
			if not vnum:
				continue

			if not gem.IsSlotOpened(slotIndex):
				block_icon = gem.GetIconPtr(IMG_DIR+"block.tga")
				if not block_icon:
					continue
				itemSlot.SetSlot(i, vnum, 32, 32, block_icon)
				self.GetChild("icon_{}".format(i)).Hide()
				self.GetChild("price_{}".format(i)).Hide()
				continue

			itemSlot.SetItemSlot(i, vnum, count)
			if buyed:
				itemSlot.DisableSlot(i)

			self.GetChild("price_{}".format(i)).SetText(str(price))
			self.GetChild("icon_{}".format(i)).Show()
			self.GetChild("price_{}".format(i)).Show()

		itemSlot.RefreshSlot()

	def __RefreshTime(self):
		cur_time = app.GetGlobalTimeStamp()
		if cur_time < self.__children.get("last_last_refresh", 0):
			return
		self.__children["last_last_refresh"] = cur_time + 1

		left_time = gem.GetRefreshTime() - cur_time

		if left_time < 0:
			left_time = 30
			gem.SetRefreshTime(cur_time + left_time)
			SendCommand("time")
		
		m, s = divmod(left_time, 60)
		h, m = divmod(m, 60)
		self.GetChild("time_gaya").SetText("%02d:%02d:%02d" % (h, m, s))

	def OnUpdate(self):
		self.__RefreshTime()

	def __EmptyFunc(self):
		return

	def __PopupNotifyMessage(self, msg):
		game = constInfo.GetGameInstance()
		if game:
			game.stream.popupWindow.Close()
			game.stream.popupWindow.Open(msg, ui.__mem_func__(self.__EmptyFunc), localeInfo.UI_OK)

	def __CloseQuestionDialog(self):
		questionDialog = self.__children.get("questionDialog", None)
		if questionDialog:
			questionDialog.Close()
			del self.__children["questionDialog"]

	def __SelectItemSlot(self, slotNumber):
		slotIndex = self.__GetRealSlotIndex(slotNumber)
		vnum, count, price, buyed = gem.GetItem(slotIndex)
		if not vnum:
			return

		if buyed:
			self.__PopupNotifyMessage(localeInfo.GEMSHOP_YOU_ALREADY_BUYED)
			return

		self.__CloseQuestionDialog()
		questionDialog = self.__children["questionDialog"] = uiCommon.QuestionDialog()
		questionDialog.SetCancelEvent(ui.__mem_func__(self.__CloseQuestionDialog))

		if not gem.IsSlotOpened(slotIndex):
			questionDialog.SetText(localeInfo.GEMSHOP_OPEN_SLOT_QUESTION)
			questionDialog.SetAcceptEvent(ui.__mem_func__(self.__SendOpenSlotRequest))
		else:
			item.SelectItem(vnum)
			questionDialog.SetText(localeInfo.GEMSHOP_BUY_QUESTION.format(item.GetItemName(), price))
			questionDialog.SetAcceptEvent(ui.__mem_func__(self.__SendBuyRequest))
			questionDialog.slotIndex = slotIndex
		questionDialog.Open()

	def __SendOpenSlotRequest(self):
		SendCommand("slot")
		self.__CloseQuestionDialog()

	def __SendBuyRequest(self):
		questionDialog = self.__children.get("questionDialog", None)
		if not questionDialog:
			return
		SendCommand("buy " + str(questionDialog.slotIndex))
		self.__CloseQuestionDialog()

	def __ClickRefreshButton(self):
		self.__CloseQuestionDialog()
		questionDialog = self.__children["questionDialog"] = uiCommon.QuestionDialog()
		questionDialog.SetText(localeInfo.GEMSHOP_REFRESH_QUESTION)
		questionDialog.SetAcceptEvent(ui.__mem_func__(self.__SendRefreshRequest))
		questionDialog.SetCancelEvent(ui.__mem_func__(self.__CloseQuestionDialog))
		questionDialog.Open()

	def __SendRefreshRequest(self):
		SendCommand("refresh")
		self.__CloseQuestionDialog()

	def __OverInItem(self, slotNumber):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			vnum, count, price, buyed = gem.GetItem(self.__GetRealSlotIndex(slotNumber))
			interface.tooltipItem.SetItemToolTip(vnum)

	def __OverOutItem(self):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			interface.tooltipItem.HideToolTip()

	def Open(self):
		self.SetCenterPosition()
		if not self.IsShow():
			self.__GoToPage(0)
		self.Show()
		self.SetTop()

	def Close(self):
		self.__CloseQuestionDialog()
		SendCommand("close")
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class ConvertWindow(ui.BoardWithTitleBar):
	__children = {}
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.__LoadWindow()

	def Destroy(self):
		self.__CloseQuestionDialog()
		self.__children = {}
		self.Hide()

	def __LoadWindow(self):
		self.Destroy()

		self.SetTitleName(localeInfo.GEMSHOP_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag("float")
		self.AddFlag("movable")
		self.AddFlag("attach")

		bg = self.__children["bg"] = ui.ImageBox()
		bg.SetParent(self)
		bg.AddFlag("not_pick")
		bg.LoadImage(IMG_DIR + "bg.tga")
		bg.SetPosition(8, 30)
		bg.Show()

		title = self.__children["title"] = ui.TextLine()
		title.SetParent(bg)
		title.SetWindowHorizontalAlignCenter()
		title.SetHorizontalAlignCenter()
		title.SetFontName("Tahoma:14b")
		title.SetText(localeInfo.GEMSHOP_SECOND_TITLE)
		title.SetPosition(0, 6)
		title.Show()

		wndItem = self.__children["wndItem"] = ui.GridSlotWindow()
		wndItem.SetParent(bg)
		wndItem.SetPosition(13, 35)
		wndItem.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
		wndItem.SAFE_SetButtonEvent("RIGHT", "EXIST", self.__SelectItem)
		wndItem.SAFE_SetButtonEvent("LEFT", "EXIST", self.__SelectItem)
		wndItem.SetOverInItemEvent(ui.__mem_func__(self.__OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
		wndItem.ArrangeSlot(0, gem.CONVERT_X_GRID, gem.CONVERT_Y_GRID, 32, 32, 0, 0)
		wndItem.RefreshSlot()
		wndItem.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		wndItem.Show()

		minusBtn = self.__children["minusBtn"] = ui.Button()
		minusBtn.SetParent(self)
		minusBtn.SetUpVisual(IMG_DIR + "minus_0.tga")
		minusBtn.SetOverVisual(IMG_DIR + "minus_1.tga")
		minusBtn.SetDownVisual(IMG_DIR + "minus_2.tga")
		minusBtn.SetPosition(10, bg.GetLocalPosition()[1] + bg.GetHeight() + 8)
		minusBtn.SetEvent(ui.__mem_func__(self.__ClickFormulaCount), -1)
		minusBtn.Show()

		count_slot = self.__children["count_slot"] = ui.ImageBox()
		count_slot.SetParent(self)
		count_slot.AddFlag("not_pick")
		count_slot.LoadImage(IMG_DIR + "count_slot.tga")
		count_slot.SetPosition(30, bg.GetLocalPosition()[1] + bg.GetHeight() + 5)
		count_slot.Show()

		count_text = self.__children["count_text"] = ui.TextLine()
		count_text.SetParent(count_slot)
		count_text.SetFontName("Tahoma:12b")
		count_text.SetHorizontalAlignCenter()
		count_text.SetVerticalAlignCenter()
		count_text.SetWindowHorizontalAlignCenter()
		count_text.SetWindowVerticalAlignCenter()
		count_text.SetText("1")
		count_text.Show()

		plusBtn = self.__children["plusBtn"] = ui.Button()
		plusBtn.SetParent(self)
		plusBtn.SetUpVisual(IMG_DIR + "plus_0.tga")
		plusBtn.SetOverVisual(IMG_DIR + "plus_1.tga")
		plusBtn.SetDownVisual(IMG_DIR + "plus_2.tga")
		plusBtn.SetPosition(85, bg.GetLocalPosition()[1] + bg.GetHeight() + 8)
		plusBtn.SetEvent(ui.__mem_func__(self.__ClickFormulaCount), 1)
		plusBtn.Show()

		convertBtn = self.__children["convertBtn"] = ui.Button()
		convertBtn.SetParent(self)
		convertBtn.SetUpVisual("d:/ymir work/ui/public/xlarge_button_01.sub")
		convertBtn.SetOverVisual("d:/ymir work/ui/public/xlarge_button_02.sub")
		convertBtn.SetDownVisual("d:/ymir work/ui/public/xlarge_button_03.sub")
		convertBtn.SetDisableVisual("d:/ymir work/ui/public/xlarge_button_03.sub")
		convertBtn.SetEvent(ui.__mem_func__(self.__ClickConvert))
		convertBtn.SetPosition(490, bg.GetLocalPosition()[1] + bg.GetHeight() + 3)
		convertBtn.Show()

		self.SetSize(8 + bg.GetWidth() + 8, 30 + bg.GetHeight() + 30 + 8)
		self.Clear()

	def __GetTotalCount(self, cur_select_index):
		if cur_select_index == -1:
			return 0

		vnum, count, price = gem.GetConvertItem(self.__GetRealIndex(cur_select_index))

		result_count = 0
		try:
			result_count = player.GetItemCountByVnum(vnum) / count
		except:
			result_count = 0
		return result_count

	def __GetRealIndex(self, slot_idx):
		return self.__children["real_slot_dict"].get(slot_idx, 255)

	def Refresh(self):
		cur_select_index = self.__children["cur_select_index"]

		total_count = self.__GetTotalCount(cur_select_index)

		self.__CheckCount(cur_select_index, total_count)
		cur_count = self.__children["count"]

		if cur_count == 0:
			self.__children["convertBtn"].Disable()
		else:
			self.__children["convertBtn"].Enable()

		self.__children["count_text"].SetText("%d / %d" % (cur_count, total_count))
		self.__children["convertBtn"].SetText(localeInfo.GEMSHOP_CONVERT_SELECTED.format(cur_count))

		grid = Grid(gem.CONVERT_X_GRID, gem.CONVERT_Y_GRID)

		real_slot_dict = {}
		wndItem = self.__children["wndItem"]
		for j in xrange(gem.CONVERT_X_GRID * gem.CONVERT_Y_GRID):
			wndItem.ClearSlot(j)
		
		for j in xrange(gem.CONVERT_X_GRID * gem.CONVERT_Y_GRID):
			vnum, count, price = gem.GetConvertItem(j)
			if not vnum:
				continue
			item.SelectItem(vnum)
			(width, height) = item.GetItemSize()
			cell = grid.find_blank(width, height)
			if cell != -1:
				grid.put(cell, width, height)
				real_slot_dict[cell] = j
				wndItem.SetItemSlot(cell, vnum, count)
				if cur_select_index == cell:
					wndItem.ActivateSlot(cell)
				else:
					wndItem.DeactivateSlot(cell)
		self.__children["real_slot_dict"] = real_slot_dict
		wndItem.RefreshSlot()

	def __ClickFormulaCount(self, val):
		if self.__children["cur_select_index"] == -1:
			return
		self.__children["count"] += val
		self.Refresh()
	
	def __CheckCount(self, cur_select_index, total_count):
		cur_count = self.__children["count"]
		if cur_count < 0:
			cur_count = 0
		if cur_count > total_count:
			cur_count = total_count
		self.__children["count"] = cur_count

	def Clear(self):
		self.__children["cur_select_index"] = -1
		self.__children["count"] = 0
		self.Refresh()

	def __SelectItem(self, slotIndex):
		if slotIndex == self.__children["cur_select_index"]:
			self.Clear()
			return
		self.__children["cur_select_index"] = slotIndex
		self.__children["count"] = 0
		self.Refresh()

	def __ClickConvert(self):
		self.__CloseQuestionDialog()
		cur_select_index = self.__children["cur_select_index"]
		if cur_select_index == -1:
			return
		total_count = self.__GetTotalCount(cur_select_index)
		self.__CheckCount(cur_select_index, total_count)
		cur_count = self.__children["count"]
		
		real_index = self.__GetRealIndex(cur_select_index)
		vnum, count, price = gem.GetConvertItem(real_index)
		item.SelectItem(vnum)
		questionDialog = self.__children["questionDialog"] = uiCommon.QuestionDialog()
		questionDialog.SetText(localeInfo.GEMSHOP_CONVERT_QUESTION.format(item.GetItemName(), cur_count * count, cur_count * price))
		questionDialog.SetAcceptEvent(ui.__mem_func__(self.__SendConvertRequest))
		questionDialog.SetCancelEvent(ui.__mem_func__(self.__CloseQuestionDialog))
		questionDialog.real_index = real_index
		questionDialog.cur_count = cur_count
		questionDialog.Show()

	def __CloseQuestionDialog(self):
		questionDialog = self.__children.get("questionDialog", None)
		if questionDialog:
			questionDialog.Close()
			del self.__children["questionDialog"]

	def __SendConvertRequest(self):
		questionDialog = self.__children.get("questionDialog", None)
		if questionDialog:
			SendCommand("convert {} {}".format(questionDialog.real_index, questionDialog.cur_count))
			self.Clear()
			self.__CloseQuestionDialog()

	def __OverInItem(self, slotIndex):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			vnum, count, price = gem.GetConvertItem(self.__GetRealIndex(slotIndex))
			tooltipItem = interface.tooltipItem
			tooltipItem.SetItemToolTip(vnum)
			tooltipItem.AppendSpace(5)
			tooltipItem.AutoAppendNewTextLineResize(localeInfo.GEMSHOP_HAS_TOOLTIP.format(player.GetItemCountByVnum(vnum)))
			tooltipItem.AppendSpace(5)
			tooltipItem.AutoAppendNewTextLineResize(localeInfo.GEMSHOP_POINT_TOOLTIP.format(price), 0xFF08DEFB)
			tooltipItem.AppendSpace(5)
			tooltipItem.ResizeToolTip()

	def __OverOutItem(self):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			interface.tooltipItem.HideToolTip()

	def Open(self):
		self.SetCenterPosition()
		if not self.IsShow():
			self.Clear()
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		SendCommand("close_convert")
		self.__CloseQuestionDialog()
		self.Hide()
	
	def OnPressEscapeKey(self):
		self.Close()
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
