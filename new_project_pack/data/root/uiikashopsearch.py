#
# IKASHOP tarzi global Pazar Arama penceresi - SADE surum.
# Filtre: SADECE item adi. Arama kutusu ustte, sonuc listesi altta; kompakt pencere.
# Isim yazinca cikan oneri listesi buyutulmus satirlar (yukseklik +15px, arasi +5px).
# Saf ASCII (gomulu Python cp1254 tanimaz); metinler localeInfo'dan getattr fallback'li.
# Gorseller IKASHOP'un kendi PNG'leri: "d:/ymir work/ikarus/...".
# Ag trafigi 'ikashop' binary modulu (server CG 84 / GC 139). Uzak alim destekli.
#
import app
import ui
import item
import wndMgr
import chat
import player
import localeInfo
import uitooltip
import uiCommon
from _weakref import proxy

try:
	import ikashop
except ImportError:
	ikashop = None


IKA = "d:/ymir work/ikarus/"
SS = IKA + "search_shop/"
SLOT_SIZE = 32

RESULT_VIEW_COUNT = 4
NAME_SUGGEST_COUNT = 12

# Pencere / yerlesim (PNG: result_box 378x494, result_item_box 339x111, input_name 165x26)
WINDOW_WIDTH = 396
WINDOW_HEIGHT = 556
RESULT_BOX_Y = 74

# Oneri (autocomplete) satirlari: gorsel 186x14 -> yukseklik +15px (=29), arasi +5px bosluk
SUGGEST_ROW_H = 14 + 15		# satir gorunur yuksekligi
SUGGEST_ROW_GAP = 5			# satirlar arasi ekstra bosluk
SUGGEST_STRIDE = SUGGEST_ROW_H + SUGGEST_ROW_GAP


def _L(name, fallback):
	return getattr(localeInfo, name, fallback)


# ============================================================================
# IkarusShopWindow tabani
# ============================================================================
class IkarusShopWindow(ui.Window):
	def _RegisterDialog(self, dialog):
		if not hasattr(self, "_dialogs"):
			self._dialogs = []
		self._dialogs.append(dialog)

	def SetTop(self):
		ui.Window.SetTop(self)
		if hasattr(self, "_dialogs"):
			for dialog in self._dialogs:
				dialog.SetTop()

	def Hide(self):
		ui.Window.Hide(self)
		if hasattr(self, "_dialogs"):
			for w in self._dialogs:
				w.Hide()

	def CreateWidget(self, cls, x = 0, y = 0, show = True, pos = None, size = None, parent = None):
		child = cls()
		child.SetParent(parent if parent else self)
		if show:
			child.Show()
		if size:
			child.SetSize(*size)
		if pos:
			x, y = pos
		child.SetPosition(x, y)
		return child

	def GetToolTip(self):
		if getattr(self, "itemToolTip", None) is None:
			self.itemToolTip = uitooltip.ItemToolTip()
			self.itemToolTip.itemVnum = 1
			self._RegisterDialog(self.itemToolTip)
		return self.itemToolTip

	def SetToolTip(self, tooltip):
		self.itemToolTip = tooltip

	def OpenQuestionDialog(self, question, acceptEvent, denyEvent = None):
		if getattr(self, "questionDialog", None) is None:
			self.questionDialog = uiCommon.QuestionDialog()
			self._RegisterDialog(self.questionDialog)
		self.questionDialog.SetText(question)
		self.questionDialog.SetAcceptEvent(acceptEvent)
		self.questionDialog.SetCancelEvent(denyEvent if denyEvent else ui.__mem_func__(self.questionDialog.Close))
		self.questionDialog.Open()

	def OpenPopupDialog(self, message):
		if getattr(self, "popupDialog", None) is None:
			self.popupDialog = uiCommon.PopupDialog()
			self._RegisterDialog(self.popupDialog)
		self.popupDialog.SetText(message)
		self.popupDialog.Open()


# ============================================================================
# Baslikli board (ic ui.BoardWithTitleBar)
# ============================================================================
class IkashopBoardWithTitleBar(IkarusShopWindow):
	def __init__(self):
		ui.Window.__init__(self)
		self._internalBoard = self.CreateWidget(ui.BoardWithTitleBar, pos = (-2, -2))

	def _UpdateView(self):
		if hasattr(self, "_internalBoard"):
			self._internalBoard.SetSize(self.GetWidth() + 6, self.GetHeight() + 4)

	def SetSize(self, w, h):
		ui.Window.SetSize(self, w, h)
		self._UpdateView()

	def SetTitleName(self, title):
		self._internalBoard.SetTitleName(title)

	def SetCloseEvent(self, event):
		self._internalBoard.SetCloseEvent(ui.__mem_func__(event))

	def OnPressEscapeKey(self):
		if self.IsShow():
			self.Close()
			return True
		return False


# ============================================================================
# Oneri satiri (yuksek satir; ExpandedImageBox + text, tiklanabilir)
# ============================================================================
class IkaComboRow(IkarusShopWindow):
	def __init__(self):
		ui.Window.__init__(self)
		self.owner = None
		self.rowIndex = -1
		self.rowWidth = 0
		self.defImg = ""
		self.hovImg = ""

		self.bg = self.CreateWidget(ui.ExpandedImageBox)
		self.bg.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self._OnClick))
		self.bg.SetEvent(ui.__mem_func__(self._OnOverIn), "mouse_over_in")
		self.bg.SetEvent(ui.__mem_func__(self._OnOverOut), "mouse_over_out")

		# text bg'nin child'i (tiklama bg'ye ulassin; Button.ButtonText kalibi)
		self.text = self.CreateWidget(ui.TextLine, parent = self.bg)
		self.text.SetHorizontalAlignCenter()
		self.text.SetVerticalAlignCenter()

	def Init(self, owner, defImg, hovImg):
		self.owner = owner
		self.defImg = defImg
		self.hovImg = hovImg
		self._LoadBg(defImg)
		self.SetSize(self.rowWidth, SUGGEST_ROW_H)
		self.text.SetPosition(self.rowWidth / 2, SUGGEST_ROW_H / 2)

	def _LoadBg(self, img):
		self.bg.LoadImage(img)
		nw = float(self.bg.GetWidth()) or 1.0
		nh = float(self.bg.GetHeight()) or 1.0
		self.rowWidth = int(nw)
		self.bg.SetScale(1.0, float(SUGGEST_ROW_H) / nh)	# gorseli +15px uzat
		self.bg.SetSize(int(nw), SUGGEST_ROW_H)				# tiklama alanini da uzat

	def GetRowWidth(self):
		return self.rowWidth

	def SetRow(self, index, text, selected):
		self.rowIndex = index
		self.text.SetText(text)
		self.text.SetPackedFontColor(0xFFFFFF88 if selected else 0xFFFFFFFF)

	def _OnClick(self):
		if self.owner and self.rowIndex >= 0:
			self.owner.SelectItem(self.rowIndex)

	def _OnOverIn(self):
		self._LoadBg(self.hovImg)

	def _OnOverOut(self):
		self._LoadBg(self.defImg)


# ============================================================================
# IkarusShopComboBox (isim onerisi acilir listesi; buyutulmus satirlar)
# ============================================================================
class IkarusShopComboBox(IkarusShopWindow):
	DEFAULT_VIEW_COUNT = 5
	ELEMENT_HEIGHT = SUGGEST_STRIDE

	def __init__(self):
		ui.Window.__init__(self)
		self.viewCount = self.DEFAULT_VIEW_COUNT
		self.elementWidth = 0
		self.selectItemEvent = None
		self.views = []
		self.items = []
		self.elementImages = (
			SS + "attribute_element/default.png",
			SS + "attribute_element/hover.png")
		self.selectedItem = 0
		if hasattr(self, "SetMouseWheelEvent"):
			self.SetMouseWheelEvent(ui.__mem_func__(self._MouseWheelScrollView))

		self.background = self.CreateWidget(ui.Bar3D)
		self.background.SetColor(0xFF999999, 0xFF000000, 0xFF777777)

		self.scrollbar = self.CreateWidget(ui.ScrollBar, show = False, parent = self.background)
		self.scrollbar.SetScrollEvent(ui.__mem_func__(self._ScrollView))

	def _MakeViews(self):
		for view in self.views:
			view.Hide()
		self.views = []
		for i in xrange(self.viewCount):
			view = self.CreateWidget(IkaComboRow, pos = (0, i * self.ELEMENT_HEIGHT), parent = self.background)
			view.Init(self, self.elementImages[0], self.elementImages[1])
			self.elementWidth = max(self.elementWidth, view.GetRowWidth())
			self.views.append(view)

	def _MouseWheelScrollView(self, delta):
		if self.scrollbar.IsShow():
			self.scrollbar.OnDown() if delta < 0 else self.scrollbar.OnUp()
		return True

	def _ScrollView(self):
		if self.scrollbar.IsShow():
			self._RefreshView()

	def _RefreshView(self):
		if not self.views:
			self._MakeViews()
		pos = self.scrollbar.GetPos() if self.scrollbar.IsShow() else 0.0
		diff = max(len(self.items) - self.viewCount, 0)
		sindex = int(diff * pos)
		eindex = sindex + min(len(self.items), self.viewCount)

		for view in self.views:
			view.Hide()

		for i in xrange(sindex, eindex):
			ri = i - sindex
			view = self.views[ri]
			view.SetRow(i, self.items[i], i == self.selectedItem)
			view.Show()

		self.scrollbar.UpdateScrollbarLenght(len(self.items) * self.ELEMENT_HEIGHT)

	def _UpdateSize(self):
		viewHeight = self.ELEMENT_HEIGHT * min(len(self.items), self.viewCount)
		self.SetSize(self.GetWidth(), viewHeight)
		self.scrollbar.SetScrollBarSize(viewHeight)
		self.background.SetSize(self.GetWidth(), self.GetHeight())

	def _UpdateScrollbar(self):
		if len(self.items) > self.viewCount:
			self.scrollbar.Show()
			self.scrollbar.SetPos(0)
			self.scrollbar.SetPosition(self.elementWidth + 1, 0)
			self.SetSize(self.elementWidth + 1 + self.scrollbar.GetWidth(), self.GetHeight())
			self.background.SetSize(self.GetWidth(), self.GetHeight())
		else:
			self.scrollbar.Hide()
			self.SetSize(self.elementWidth, self.GetHeight())
			self.background.SetSize(self.GetWidth(), self.GetHeight())

	def Open(self):
		self.Show()

	def Close(self):
		self.Hide()

	def Toggle(self):
		self.Close() if self.IsShow() else self.Open()

	def GetSelectedItem(self):
		return self.selectedItem

	def SelectItem(self, index):
		self.selectedItem = index
		self._RefreshView()
		self.Close()
		if self.selectItemEvent and 0 <= index < len(self.items):
			self.selectItemEvent(index, self.items[index])

	def SetSelectItemEvent(self, event):
		self.selectItemEvent = event

	def SetItems(self, items):
		self.items = items
		if not self.views:
			self._MakeViews()
		self._UpdateSize()
		self._UpdateScrollbar()
		self._RefreshView()

	def SetViewCount(self, count):
		self.viewCount = count
		self._UpdateSize()
		self._UpdateScrollbar()
		self._MakeViews()
		self._RefreshView()

	def IsMe(self, combobox):
		return self is combobox


# ============================================================================
# Sonuc karti (uzak alim)
# ============================================================================
class IkarusSearchShopItem(IkarusShopWindow):
	def __init__(self):
		ui.Window.__init__(self)
		self.data = {'id': -1}
		self.searchShopBoard = None
		self.buyItemInfo = None
		self._Load()

	def _Load(self):
		self.background = self.CreateWidget(ui.ExpandedImageBox)
		self.background.LoadImage(SS + "result_item_box.png")
		self.SetSize(self.background.GetWidth(), self.background.GetHeight())

		self.itemName = self.CreateWidget(ui.TextLine, pos = (60, 11))
		self.sellerName = self.CreateWidget(ui.TextLine, pos = (78, 35))
		self.price = self.CreateWidget(ui.TextLine, pos = (78, 58))

		self.buyButton = self.CreateWidget(ui.Button, pos = (261, 84))
		self.buyButton.SetUpVisual(SS + "buy_button/default.png")
		self.buyButton.SetDownVisual(SS + "buy_button/default.png")
		self.buyButton.SetOverVisual(SS + "buy_button/hover.png")
		self.buyButton.SAFE_SetEvent(self._OnClickBuyButton)
		self.buyButton.SetText(_L("IKASHOP_SEARCH_SHOP_BUY_BUTTON_TEXT", "Satin Al"))

		self.slot = self.CreateWidget(ui.GridSlotWindow, pos = (9, 7))
		self.slot.ArrangeSlot(0, 1, 1, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage(IKA + "common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetOverInItemEvent(ui.__mem_func__(self._OverInItem))
		self.slot.SetOverOutItemEvent(ui.__mem_func__(self._OverOutItem))

	def SetSearchShopBoard(self, board):
		self.searchShopBoard = proxy(board)

	def GetId(self):
		return self.data['id']

	def _OnClickBuyButton(self):
		if self.data['id'] < 0:
			return
		item.SelectItem(self.data['vnum'])
		itemName = item.GetItemName()
		if self.data['count'] > 1:
			itemName += "(%d)" % self.data['count']
		itemPrice = localeInfo.NumberToMoneyString(self.data['price'])
		self.buyItemInfo = self.data['owner'], self.data['id'], self.data['price']
		question = _L("IKASHOP_SHOP_GUEST_BUY_ITEM_QUESTION", "%s satin alinsin mi? Fiyat: %s")
		try:
			message = question % (itemName, itemPrice)
		except Exception:
			message = "%s satin alinsin mi? Fiyat: %s" % (itemName, itemPrice)
		self.OpenQuestionDialog(message, ui.__mem_func__(self._OnAcceptBuyItemQuestion))

	def _OnAcceptBuyItemQuestion(self):
		if self.buyItemInfo and ikashop is not None:
			ikashop.SendBuyItem(*self.buyItemInfo)
		if getattr(self, "questionDialog", None):
			self.questionDialog.Close()
		return True

	def _OverInItem(self, slot):
		if not self.searchShopBoard:
			return
		tooltip = self.searchShopBoard.GetToolTip()
		tooltip.SetOfflineShopEditItem(self.data['vnum'], self.data['sockets'], self.data['attrs'], self.data['price'], self.data['count'])
		tooltip.ShowToolTip()

	def _OverOutItem(self):
		if self.searchShopBoard:
			self.searchShopBoard.GetToolTip().HideToolTip()

	def SetNotAvailable(self):
		self.slot.DisableSlot(0)
		self.itemName.SetPackedFontColor(0xFFFF8888)
		self.buyButton.Hide()

	def SetAvailable(self):
		self.slot.EnableSlot(0)
		self.itemName.SetPackedFontColor(0xFFFFFFFF)
		self.buyButton.Show()

	def Setup(self, data):
		item.SelectItem(data['vnum'])
		itemName = item.GetItemName()
		self.itemName.SetText(itemName)
		self.sellerName.SetText(data['seller_name'])
		priceText = localeInfo.NumberToMoneyString(data['price'])
		if data.get('channel', 0) > 0:
			priceText += "  (Ch%d)" % data['channel']
		self.price.SetText(priceText)

		# Slot arka planini item yuksekligine (1/2/3 slot) gore ayarla
		itemcount = data['count'] if data['count'] > 1 else 0
		try:
			sizeY = item.GetItemSize()[1]
		except Exception:
			sizeY = 1
		if sizeY < 1:
			sizeY = 1
		self.slot.ArrangeSlot(0, 1, sizeY, SLOT_SIZE, SLOT_SIZE, 0, 0)
		self.slot.SetSlotBaseImage(IKA + "common/slot/default.png", 1.0, 1.0, 1.0, 1.0)
		self.slot.SetItemSlot(0, data['vnum'], itemcount)
		self.data = data


# ============================================================================
# Ana arama board'u (SADE: sadece item adi; arama ustte, liste altta)
# ============================================================================
class IkaShopSearchWindow(IkashopBoardWithTitleBar):
	RESULT_ITEM_VIEW_COUNT = RESULT_VIEW_COUNT

	def __init__(self):
		IkashopBoardWithTitleBar.__init__(self)
		if ikashop is not None and hasattr(ikashop, "SetSearchShopBoard"):
			ikashop.SetSearchShopBoard(self)
		self.items = []
		self.lastOpen = 0
		self.isRandomFilling = False
		self._SettingUpBoard()
		self._LoadSearchShopWindow()

	def __del__(self):
		ui.Window.__del__(self)

	def _SettingUpBoard(self):
		self.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)
		self.SetTitleName(_L("IKASHOP_SEARCH_SHOP_BOARD_TITLE", "Esya Ara"))
		self.SetCloseEvent(self.Close)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")

	def _LoadSearchShopWindow(self):
		getBottom = lambda win: win.GetLocalPosition()[1] + win.GetHeight()
		getRight = lambda win: win.GetLocalPosition()[0] + win.GetWidth()

		# --- USTTE: item adi + arama + sifirla ---
		self.inputNameBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, 40))
		self.inputNameBox.LoadImage(SS + "input_name.png")
		_inw = self.inputNameBox.GetWidth()
		if _inw > 0:	# PNG yuklenemezse sifira bolme crash'ini onle
			self.inputNameBox.SetScale(200.0 / _inw, 1.0)

		self.searchButton = self.CreateWidget(ui.Button, pos = (14 + self.inputNameBox.GetWidth() + 4, 42))
		self.searchButton.SetUpVisual(SS + "mini_search_button/default.png")
		self.searchButton.SetDownVisual(SS + "mini_search_button/default.png")
		self.searchButton.SetOverVisual(SS + "mini_search_button/hover.png")
		self.searchButton.SAFE_SetEvent(self._OnClickSearchButton)
		self.searchButton.SetToolTipText(_L("IKASHOP_SEARCH_SHOP_SEARCH_BUTTON_TEXT", "Ara"))

		iw = self.inputNameBox.GetWidth() - 12
		ih = self.inputNameBox.GetHeight() - 6
		self.inputNameEdit = self.CreateWidget(ui.EditLine, pos = (6, 6), size = (iw, ih), parent = self.inputNameBox)
		self.inputNameEdit.SetMax(24)
		self.inputNameEdit.SetEscapeEvent(ui.__mem_func__(self.inputNameEdit.KillFocus))
		self.inputNameEdit.SetReturnEvent(ui.__mem_func__(self._OnClickSearchButton))
		self.inputNameEdit.SetUpdateEvent(ui.__mem_func__(self._OnUpdateInputName))
		self.inputNameBox.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.inputNameEdit.SetFocus))

		# Placeholder: kutu bosken gri "Item ara..." (yazinca gizlenir)
		self.searchPlaceholder = self.CreateWidget(ui.TextLine, pos = (8, 6), parent = self.inputNameBox)
		self.searchPlaceholder.SetPackedFontColor(0xFF888888)
		self.searchPlaceholder.SetText(_L("IKASHOP_SEARCH_PLACEHOLDER", "Item ara..."))

		self.resetFilterButton = self.CreateWidget(ui.Button, pos = (getRight(self.searchButton) + 4, 42))
		self.resetFilterButton.SetUpVisual(SS + "reset_filter_button/default.png")
		self.resetFilterButton.SetDownVisual(SS + "reset_filter_button/default.png")
		self.resetFilterButton.SetOverVisual(SS + "reset_filter_button/hover.png")
		self.resetFilterButton.SAFE_SetEvent(self._OnClickResetFilters)
		self.resetFilterButton.SetToolTipText(_L("IKASHOP_SEARCH_SHOP_RESET_FILTER_BUTTON_TEXT", "Sifirla"))

		# oneri combobox'i (float; input kutusunun hemen altinda acilir)
		self.inputNameSuggestion = self.CreateWidget(IkarusShopComboBox, pos = (14, getBottom(self.inputNameBox) + 2))
		self.inputNameSuggestion.SetSelectItemEvent(self._OnSelectSuggestedItemName)
		self.inputNameSuggestion.SetViewCount(6)
		self.inputNameSuggestion.SetItems(["", ])

		# --- ALTTA: sonuc kutusu + kartlar ---
		self.resultBox = self.CreateWidget(ui.ExpandedImageBox, pos = (14, RESULT_BOX_Y))
		self.resultBox.LoadImage(SS + "result_box.png")
		if hasattr(self.resultBox, "SetMouseWheelEvent"):
			self.resultBox.SetMouseWheelEvent(ui.__mem_func__(self._OnScrollMouseWheelResultItems))
		_rbw = self.resultBox.GetWidth()
		_rbh = self.resultBox.GetHeight()
		if _rbw > 0 and _rbh > 0:	# PNG yuklenemezse sifira bolme crash'ini onle
			self.resultBox.SetScale(float(_rbw - 10) / _rbw, 469.0 / _rbh)

		self.resultItems = []
		for i in xrange(self.RESULT_ITEM_VIEW_COUNT):
			card = self.CreateWidget(IkarusSearchShopItem, pos = (5, 4 + 116 * i), parent = self.resultBox)
			card.SetSearchShopBoard(self)
			self.resultItems.append(card)

		self.resultItemScrollBar = self.CreateWidget(ui.ScrollBar, pos = (self.resultBox.GetWidth() - 19, 3), parent = self.resultBox)
		self.resultItemScrollBar.SetScrollEvent(ui.__mem_func__(self._OnScrollResultItems))
		self.resultItemScrollBar.SetScrollBarSize(self.resultBox.GetHeight() - 6)
		self.resultItemScrollBar.Hide()

		# oneri combosunu float + en uste + kayit
		self.inputNameSuggestion.AddFlag("float")
		self.inputNameSuggestion.SetTop()
		self.inputNameSuggestion.SelectItem(0)
		self._RegisterDialog(self.inputNameSuggestion)

		self._UpdatePlaceholder()

	# ----- olaylar -----
	def _OnClickSearchButton(self):
		if ikashop is None:
			return
		self.inputNameEdit.KillFocus()
		name = self.inputNameEdit.GetText()
		if not name:
			self.OpenPopupDialog(_L("IKASHOP_SEARCH_SHOP_NO_FILTER_USED", "Lutfen aranacak item adini gir."))
			return
		if hasattr(ikashop, "ClearFilterAttrs"):
			ikashop.ClearFilterAttrs()
		self.isRandomFilling = False
		ikashop.SendFilterRequest(name, -1, -1, 0, 0, 0, 0)

	def _UpdatePlaceholder(self):
		if hasattr(self, "searchPlaceholder"):
			self.searchPlaceholder.Hide() if self.inputNameEdit.GetText() else self.searchPlaceholder.Show()

	def _OnUpdateInputName(self):
		self._UpdatePlaceholder()
		text = self.inputNameEdit.GetText().lower()
		if len(text) < 3 or ikashop is None or not hasattr(ikashop, "GetNameSuggestions"):
			self.inputNameSuggestion.Close()
			return
		try:
			names = ikashop.GetNameSuggestions(self.inputNameEdit.GetText(), NAME_SUGGEST_COUNT)
		except Exception:
			names = ()
		suggestions = list(names)
		if suggestions:
			self.inputNameSuggestion.SetItems(suggestions)
			self.inputNameSuggestion.Open()
		else:
			self.inputNameSuggestion.Close()

	def _OnSelectSuggestedItemName(self, index, name):
		self.inputNameEdit.SetText(name)
		self.inputNameEdit.KillFocus()
		self._UpdatePlaceholder()

	def _OnClickResetFilters(self):
		self.inputNameEdit.SetText("")
		self.inputNameSuggestion.Close()
		self._UpdatePlaceholder()

	# ----- sonuc yenileme -----
	def _OnScrollResultItems(self):
		self._RefreshResultItem()

	def _OnScrollMouseWheelResultItems(self, delta):
		self.resultItemScrollBar.OnDown() if delta < 0 else self.resultItemScrollBar.OnUp()
		return True

	def _RefreshResultItem(self):
		pos = self.resultItemScrollBar.GetPos() if self.resultItemScrollBar.IsShow() else 0.0
		diff = max(len(self.items) - self.RESULT_ITEM_VIEW_COUNT, 0)
		sindex = int(diff * pos)
		eindex = sindex + min(len(self.items), self.RESULT_ITEM_VIEW_COUNT)

		for view in self.resultItems:
			view.Hide()

		for i in xrange(sindex, eindex):
			ri = i - sindex
			data = self.items[i]
			view = self.resultItems[ri]
			view.Setup(data)
			view.Show()
			view.SetAvailable() if data.get('deleted', 0) == 0 else view.SetNotAvailable()

		self.resultItemScrollBar.UpdateScrollbarLenght(4 + 116 * len(self.items))

	def _UpdateScrollbarState(self):
		self.resultItemScrollBar.Show() if self.RESULT_ITEM_VIEW_COUNT < len(self.items) else self.resultItemScrollBar.Hide()
		self.resultItemScrollBar.SetPos(0)

	# ----- binary callback'leri -----
	def OnIkaShopSearchResult(self, count):
		self.items = []
		if ikashop is not None:
			for i in xrange(count):
				sockets = [ikashop.GetResultSocket(i, s) for s in xrange(player.METIN_SOCKET_MAX_NUM)]
				attrs = [ikashop.GetResultAttr(i, a) for a in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
				self.items.append({
					'id': ikashop.GetResultItemDBID(i),
					'owner': ikashop.GetResultOwnerPID(i),
					'seller_name': ikashop.GetResultShopName(i),
					'vnum': ikashop.GetResultVnum(i),
					'count': ikashop.GetResultItemCount(i),
					'price': ikashop.GetResultPrice(i),
					'channel': ikashop.GetResultChannel(i),
					'sockets': sockets,
					'attrs': attrs,
					'deleted': 0,
				})
		self._UpdateScrollbarState()
		self._RefreshResultItem()
		if not self.IsShow():
			self.Show()
			self.SetTop()
			self.lastOpen = app.GetTime()
		self.isRandomFilling = False

	def OnIkaShopResultDelete(self, itemDBID):
		for data in self.items:
			if data['id'] == itemDBID:
				data['deleted'] = 1
		for view in self.resultItems:
			if view.GetId() == itemDBID:
				view.SetNotAvailable()

	def OnIkaShopPopup(self, localeKey):
		msg = _L(localeKey, localeKey)
		self.OpenPopupDialog(msg)
		chat.AppendChat(chat.CHAT_TYPE_INFO, msg)

	# ----- ac/kapat -----
	def Open(self):
		now = app.GetTime()
		# IKASHOP davranisi: acilisi vitrinle doldur (60 sn tazelik / bos liste).
		# hasattr guard: eski binary'de SendFillRequest yoksa crash yerine normal acilir.
		if ikashop is not None and hasattr(ikashop, "SendFillRequest") and \
				(self.lastOpen == 0 or now - self.lastOpen > 60 or len(self.items) == 0):
			self.isRandomFilling = True
			ikashop.SendFillRequest()
			return
		self.lastOpen = now
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()
		if hasattr(self, "inputNameEdit"):
			self.inputNameEdit.KillFocus()

	def Destroy(self):
		if ikashop is not None and hasattr(ikashop, "SetSearchShopBoard"):
			ikashop.SetSearchShopBoard(None)
		self.Hide()
		self.items = []
		self.resultItems = []
