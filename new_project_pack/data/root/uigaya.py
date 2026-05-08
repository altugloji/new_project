import app
import chat
import item
import localeInfo
import net
import ui


class GayaWindow(ui.ScriptWindow):
	SLOT_COUNT = 80
	PREVIEW_ITEMS = (
		(25040, 1, 12),
		(25041, 2, 8),
		(25043, 3, 4),
		(25045, 4, 2),
		(25050, 5, 1),
		(25051, 6, 0),
	)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.itemMap = {}
		self.selected = set()
		self.quantity = 1
		self.gayaPoints = 0

	def LoadWindow(self):
		try:
			loader = ui.PythonScriptLoader()
			loader.LoadScriptFile(self, "UIScript/GayaWindow.py")
		except:
			import exception
			exception.Abort("GayaWindow.LoadWindow.LoadScript")

		try:
			get_child = self.GetChild
			self.board = get_child("board")
			self.titleBar = get_child("TitleBar")
			self.descText = get_child("DescText")
			self.slotWnd = get_child("GayaItemSlot")
			self.pointsText = get_child("GayaPoints")
			self.quantityText = get_child("QuantityText")
			self.minusButton = get_child("MinusButton")
			self.plusButton = get_child("PlusButton")
			self.convertButton = get_child("ConvertButton")
		except:
			import exception
			exception.Abort("GayaWindow.LoadWindow.BindObject")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.slotWnd.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSelectSlot))
		self.slotWnd.SetOverInItemEvent(ui.__mem_func__(self.__OnOverInItem))
		self.slotWnd.SetOverOutItemEvent(ui.__mem_func__(self.__OnOverOutItem))
		self.minusButton.SetEvent(ui.__mem_func__(self.__OnDecreaseQuantity))
		self.plusButton.SetEvent(ui.__mem_func__(self.__OnIncreaseQuantity))
		self.convertButton.SetEvent(ui.__mem_func__(self.__OnConvert))
		self.__RefreshTexts()

	def Destroy(self):
		self.ClearDictionary()
		self.tooltipItem = None
		self.itemMap = {}
		self.selected = set()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def Open(self):
		self.itemMap = {}
		self.selected = set()
		self.__RefreshSlots()
		self.Show()
		self.SetTop()
		net.SendChatPacket("/gaya refresh")

	def OpenPreview(self):
		self.itemMap = {}
		self.selected = set()
		self.gayaPoints = 12345
		self.quantity = 1
		self.__LoadPreviewItems()
		self.__RefreshTexts()
		self.__RefreshSlots()
		self.Show()
		self.SetTop()

	def Close(self):
		self.__OnOverOutItem()
		self.Hide()

	def SetGayaPoints(self, points):
		self.gayaPoints = max(0, int(points))
		self.__RefreshTexts()

	def AppendItems(self, entries):
		for vnum, point, owned in entries:
			self.itemMap[int(vnum)] = (int(point), int(owned))
		self.__RefreshSlots()

	def __LoadPreviewItems(self):
		for vnum, point, owned in self.PREVIEW_ITEMS:
			self.itemMap[int(vnum)] = (int(point), int(owned))

	def __RefreshTexts(self):
		if self.pointsText:
			self.pointsText.SetText("Gaya: %s" % localeInfo.NumberToString(self.gayaPoints))
		if self.quantityText:
			self.quantityText.SetText(str(self.quantity))
		if self.convertButton:
			self.convertButton.SetText("Secileni Cevir x%d" % self.quantity)

	def __RefreshSlots(self):
		ordered = sorted(self.itemMap.items())
		for i in xrange(self.SLOT_COUNT):
			self.slotWnd.ClearSlot(i)
			self.slotWnd.DeactivateSlot(i)

		for idx, (vnum, data) in enumerate(ordered[:self.SLOT_COUNT]):
			point, owned = data
			count = owned if owned > 1 else 0
			self.slotWnd.SetItemSlot(idx, vnum, count)
			if idx in self.selected:
				self.slotWnd.ActivateSlot(idx, 0.95, 0.85, 0.35, 1.0)
			elif owned <= 0:
				self.slotWnd.ActivateSlot(idx, 0.45, 0.45, 0.45, 1.0)

		self.slotWnd.RefreshSlot()

	def __OnSelectSlot(self, slotIndex):
		ordered = sorted(self.itemMap.items())
		if slotIndex >= len(ordered):
			return

		vnum, data = ordered[slotIndex]
		_point, owned = data
		if owned <= 0:
			return

		if slotIndex in self.selected:
			self.selected.remove(slotIndex)
		else:
			self.selected.add(slotIndex)
		self.__RefreshSlots()

	def __OnOverInItem(self, slotIndex):
		if not self.tooltipItem:
			return
		ordered = sorted(self.itemMap.items())
		if slotIndex >= len(ordered):
			return
		vnum, data = ordered[slotIndex]
		point, _owned = data
		self.tooltipItem.SetItemToolTip(vnum)
		self.tooltipItem.AppendSpace(5)
		self.tooltipItem.AppendTextLine("Gaya Degeri: %d" % point, 0xFFe6c84c)
		self.tooltipItem.ResizeToolTip()
		self.tooltipItem.ShowToolTip()

	def __OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __OnDecreaseQuantity(self):
		self.quantity = max(1, self.quantity - 1)
		self.__RefreshTexts()

	def __OnIncreaseQuantity(self):
		self.quantity = min(200, self.quantity + 1)
		self.__RefreshTexts()

	def __OnConvert(self):
		ordered = sorted(self.itemMap.items())
		converted = 0
		for slotIndex in list(self.selected):
			if slotIndex >= len(ordered):
				continue
			vnum, data = ordered[slotIndex]
			_point, owned = data
			if owned < self.quantity:
				continue
			net.SendChatPacket("/gaya convert %d %d" % (vnum, self.quantity))
			converted += 1

		if converted <= 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Donusturme icin secili ve yeterli adette esya yok.")
