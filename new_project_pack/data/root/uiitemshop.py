import ui
import uiToolTip
import uiCommon
import localeInfo
import wndMgr
import constInfo
import dbg
import os
import snd
import chat
import chr
import player
import item
import net
import app
import background
import chrmgr
import wikiui

ITEM_SHOP_ITEM_VISIBLE_ROWS = 5
ITEM_SHOP_ROW_H = 110
ITEM_SHOP_ROW_GAP = 10
ITEM_SHOP_LIST_TOP = 10
ITEM_SHOP_ROW_START_X = 8
ITEM_SHOP_SCROLL_VIEW_H = (
	ITEM_SHOP_ITEM_VISIBLE_ROWS * ITEM_SHOP_ROW_H
	+ (ITEM_SHOP_ITEM_VISIBLE_ROWS - 1) * ITEM_SHOP_ROW_GAP
)
ITEM_SHOP_SCROLLBAR_W = 8
ITEM_SHOP_FONT = getattr(localeInfo, "UI_BOLD_FONT_LARGE", localeInfo.UI_DEF_FONT_LARGE)


FAKE_CATEGORY_DATA = {
	0 : {
		"categoryName" : "Genel",
		"subCategoryNameList" : [
			localeInfo.ITEMSHOP_SUBCATEGORY_CHARACTER_DEVELOPMENT,
			localeInfo.ITEMSHOP_SUBCATEGORY_SUPPORT_ITEMS,
			localeInfo.ITEMSHOP_SUBCATEGORY_EP_COUPONS,
			localeInfo.ITEMSHOP_SUBCATEGORY_TICKETS,
			localeInfo.ITEMSHOP_SUBCATEGORY_OTHER,
			"Sac Stilleri",
		],
	},
}

ITEM_SHOP_CATEGORY_LINE_HEIGHT = 34
ITEM_SHOP_NESNE_MARKET_ROOT = "d:/ymir work/nesne_market/"
ITEM_SHOP_CATEGORY_BTN_DEFAULT = ITEM_SHOP_NESNE_MARKET_ROOT + "kategori.png"
ITEM_SHOP_CATEGORY_BTN_ACTIVE = ITEM_SHOP_NESNE_MARKET_ROOT + "kategori2.png"


def _FormatItemShopPriceDisplay(price):
	try:
		n = int(price)
	except Exception:
		return str(price)
	try:
		if app.ENABLE_ITEM_SHOP_SYSTEM:
			return localeInfo.PrettyNumber(n)
	except Exception:
		pass
	return str(n)

ITEM_FLAG_STACKABLE = (1 << 2)
BLEND_AFFECT_UNLIMITED_DURATION = 100 * 60 * 60
def toLower(string):
	alphabetList = {
		"\xdd": "i",
		"I": "\xfd",
		"\xd6": "\xf6",
		"\xdc": "\xfc",
		"\xde": "\xfe",
		"\xd0": "\xf0",
		"\xc7": "\xe7",
	}
	for (key, item) in alphabetList.iteritems():
		string = string.replace(key, item)
	return string.lower()
class CategoryButton(ui.Window):
	ARROWIMAGE_FILE_NAME = {
		"SELECT" : "d:/ymir work/ui/privatesearch/private_next_btn_02.sub",
		"UNSELECT" : "d:/ymir work/ui/privatesearch/private_next_btn_01.sub",
	}

	def __init__(self, parent, x, y, isSubItem = False):
		ui.Window.__init__(self)
		self.getParent = parent
		self.key = None
		self.isSubItem = isSubItem

		self.SetParent(parent)
		self.AddFlag("float")
		self.SetSize(138, 32)
		self.SetPosition(x, y)
		
		categoryButton = ui.RadioButton()
		categoryButton.SetParent(self)
		categoryButton.AddFlag("not_pick")
		categoryButton.SetUpVisual(ITEM_SHOP_CATEGORY_BTN_DEFAULT)
		categoryButton.SetOverVisual(ITEM_SHOP_CATEGORY_BTN_DEFAULT)
		categoryButton.SetDownVisual(ITEM_SHOP_CATEGORY_BTN_ACTIVE)

		categoryButton.SetPosition(0, 0)
		categoryButton.SetEvent(ui.__mem_func__(self.OnMouseLeftButtonDown))
		categoryButton.Show()
		self.categoryButton = categoryButton

		image = ui.ImageBox()
		image.SetParent(self)
		image.AddFlag("not_pick")
		image.LoadImage(self.ARROWIMAGE_FILE_NAME["UNSELECT"])
		image.SetPosition(8, 8)
		image.Hide()
		self.image = image

		name = ui.TextLine()
		name.SetParent(self)
		name.SetPosition(26, 7)
		name.SetFontName(ITEM_SHOP_FONT)
		name.SetOutline()
		name.Show()
		self.name = name

	def IsSubItem(self):
		return self.isSubItem
		
	def SetName(self, name):
		if self.isSubItem:
			self.name.SetPosition(24 + (60 if localeInfo.IsARABIC() else 0), 7)
			#self.name.SetFontColor(0.63,0.91,1.00)
		else:
			self.name.SetPosition(24 + (60 if localeInfo.IsARABIC() else 0), 7)
			#self.name.SetFontColor(1.00,0.69,0.29)

		self.name.SetText(name)
		self.name.SetOutline()

	def SetKey(self, key):
		self.key = key
		
	def GetKey(self):
		return self.key

	def IsSameKey(self, key):
		return self.key == key

	def Select(self):
		self.categoryButton.Down()
		self.image.LoadImage(self.ARROWIMAGE_FILE_NAME["SELECT"])

	def UnSelect(self):
		self.categoryButton.SetUp()
		self.image.LoadImage(self.ARROWIMAGE_FILE_NAME["UNSELECT"])

	def OnMouseLeftButtonDown(self):
		if not self.isSubItem:
			self.getParent.OnSelectItem(self)
		else:
			self.getParent.OnSubSelectItem(self)


class FlatCategoryLeafRow(CategoryButton):
	def __init__(self, parent, x, y):
		self.categoryKey = None
		self.subCategoryKey = None
		CategoryButton.__init__(self, parent, x, y, False)

	def SetCategoryKey(self, k):
		self.categoryKey = k

	def SetSubCategoryKey(self, k):
		self.subCategoryKey = k

	def GetCategoryKey(self):
		return self.categoryKey

	def GetSubCategoryKey(self):
		return self.subCategoryKey

	def OnMouseLeftButtonDown(self):
		self.getParent.OnLeafSelect(self)


class CategoryBoard(ui.Window):
	def __init__(self, parentFirst, parentSecond, scrollBar):
		ui.Window.__init__(self)
		
		self.SetParent(parentSecond)
		self.getParent = parentFirst

		self.scrollBar = scrollBar
		# self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.selectLeaf = None
		self.categoryListItems = []
		self.showingItemList = []
		self.startLine = 0

	def OnScroll(self):
		scrollLineCount = len(self.showingItemList) - 13
		startLine = int(scrollLineCount * self.scrollBar.GetPos())

		if startLine != self.startLine:
			self.startLine = startLine
			self.__LocateMember()

	def OnLeafSelect(self, item):
		if self.selectLeaf:
			self.selectLeaf.UnSelect()
			self.getParent.ClearItemBoard()

		self.selectLeaf = item

		if self.selectLeaf:
			self.selectLeaf.Select()
			self.getParent.ChangeCategory(self.selectLeaf.GetCategoryKey(), self.selectLeaf.GetSubCategoryKey())

	def __LocateMember(self):

		if self.showingItemList:
			stepSize = 1.0 / (len(self.showingItemList) - 12)
			# self.scrollBar.SetScrollStep(stepSize)

			if stepSize <= 0.8:
				stepSize += 0.2

			# self.scrollBar.SetMiddleBarSize(stepSize)

		self.scrollBar.Show()

		#####

		yPos = 52
		heightLimit = self.GetHeight() - 30

		map(ui.Window.Hide, self.showingItemList)

		for item in self.showingItemList[self.startLine:]:
			item.SetPosition(8, yPos)
			item.SetTop()
			item.Show()

			yPos += ITEM_SHOP_CATEGORY_LINE_HEIGHT
			if yPos > heightLimit:
				break
				
		
	
	def OnRefreshList(self):
		self.showingItemList = list(self.categoryListItems)
		self.__LocateMember()

	def firstOpenBoard(self):
		if self.categoryListItems:
			self.OnLeafSelect(self.categoryListItems[0])

	def RefreshProcess(self):
		self.categoryListItems = []
		idx = 0
		for i in xrange(len(FAKE_CATEGORY_DATA)):
			categoryData = FAKE_CATEGORY_DATA[i]
			for j in xrange(len(categoryData["subCategoryNameList"])):
				name = categoryData["subCategoryNameList"][j]
				row = FlatCategoryLeafRow(self, 8, 52 + idx * ITEM_SHOP_CATEGORY_LINE_HEIGHT)
				row.SetCategoryKey(i)
				row.SetSubCategoryKey(j)
				row.SetName(name)
				row.Show()
				self.categoryListItems.append(row)
				idx += 1

		self.OnRefreshList()


class ItemStackableBuyDialog(ui.BoardWithTitleBar):

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		
		self.getParent = None
		self.itemID = 0
		self.itemVnum = 0
		self.itemPrice = -1
		self.maxCount = 0
		self.packSize = 1
		self.coins = 0
		self.payWithEp = True
		
		self.__LoadDialog()
	
	def __LoadDialog(self):
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(200, 160)
		self.SetCloseEvent(self.Close)

		countTextFirst = ui.TextLine()
		countTextFirst.SetParent(self)
		countTextFirst.SetFontName(ITEM_SHOP_FONT)
		countTextFirst.SetText("Alinacak toplam miktar: 1")
		countTextFirst.SetPosition(self.GetWidth() / 2, 40)
		countTextFirst.SetHorizontalAlignCenter()
		countTextFirst.Show()
		self.countTextFirst = countTextFirst
		
		countArrowUp = ui.Button()
		countArrowUp.SetParent(self)
		countArrowUp.SetPosition(self.GetWidth() / 2 - 44, self.GetHeight() / 2 - 9)
		countArrowUp.SetUpVisual("d:/ymir work/ui/itemshop/arrow_up_default.sub")
		countArrowUp.SetOverVisual("d:/ymir work/ui/itemshop/arrow_up_over.sub")
		countArrowUp.SetDownVisual("d:/ymir work/ui/itemshop/arrow_up_down.sub")
		countArrowUp.SetEvent(self.__ArrowButton, 0)
		countArrowUp.Show()
		self.countArrowUp = countArrowUp

		countArrowDown = ui.Button()
		countArrowDown.SetParent(self)
		countArrowDown.SetPosition(self.GetWidth() / 2 - 44, self.GetHeight() / 2 + 3)
		countArrowDown.SetUpVisual("d:/ymir work/ui/itemshop/arrow_down_default.sub")
		countArrowDown.SetOverVisual("d:/ymir work/ui/itemshop/arrow_down_over.sub")
		countArrowDown.SetDownVisual("d:/ymir work/ui/itemshop/arrow_down_down.sub")
		countArrowDown.SetEvent(self.__ArrowButton, 1)
		countArrowDown.Show()
		self.countArrowDown = countArrowDown

		countSlotBar = ui.SlotBar()
		countSlotBar.SetParent(self)
		countSlotBar.SetSize(50, 18)
		countSlotBar.SetPosition(self.GetWidth() / 2 - 30, self.GetHeight() / 2 - 10)
		countSlotBar.OnMouseLeftButtonDown = ui.__mem_func__(self.__ClickValueEditLine)
		countSlotBar.Show()
		self.countSlotBar = countSlotBar

		countEditline = ui.EditLine()
		countEditline.SetParent(countSlotBar)
		countEditline.SetSize(24, 18)
		countEditline.SetMax(3)
		countEditline.SetPosition(3, 2)
		countEditline.SetNumberMode()
		countEditline.SetText("1")
		countEditline.SetFocus()
		countEditline.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
		countEditline.OnIMEReturn = ui.__mem_func__(self.__OnValueReturn)
		countEditline.Show()
		self.countEditline = countEditline
		
		countTextSecond = ui.TextLine()
		countTextSecond.SetParent(countSlotBar)
		countTextSecond.SetFontName(ITEM_SHOP_FONT)
		countTextSecond.SetText("/0")
		countTextSecond.SetPosition(55, 0)
		countTextSecond.Show()
		self.countTextSecond = countTextSecond
		
		ammoutText = ui.TextLine()
		ammoutText.SetParent(self)
		ammoutText.SetFontName(ITEM_SHOP_FONT)
		ammoutText.SetText("Tutar : 0 Ep")
		ammoutText.SetPosition(self.GetWidth() / 2, self.GetHeight() / 2 + 15)
		ammoutText.SetHorizontalAlignCenter()
		ammoutText.Show()
		self.ammoutText = ammoutText
		
		acceptButton = ui.Button()
		acceptButton.SetParent(self)
		acceptButton.SetPosition(self.GetWidth() / 2 - 70, self.GetHeight() - 35)
		acceptButton.SetUpVisual("d:/ymir work/ui/Public/acceptbutton00.sub")
		acceptButton.SetOverVisual("d:/ymir work/ui/Public/acceptbutton01.sub")
		acceptButton.SetDownVisual("d:/ymir work/ui/Public/acceptbutton02.sub")
		acceptButton.SetToolTipText("Satin Al")
		acceptButton.SetEvent(ui.__mem_func__(self.acceptButtonEvent))
		acceptButton.Show()
		self.acceptButton = acceptButton
		
		cancelButton = ui.Button()
		cancelButton.SetParent(self)
		cancelButton.SetPosition(self.GetWidth() / 2 + 8, self.GetHeight() - 35)
		cancelButton.SetUpVisual("d:/ymir work/ui/Public/canclebutton00.sub")
		cancelButton.SetOverVisual("d:/ymir work/ui/Public/canclebutton01.sub")
		cancelButton.SetDownVisual("d:/ymir work/ui/Public/canclebutton02.sub")
		cancelButton.SetToolTipText("Iptal")
		cancelButton.SetEvent(ui.__mem_func__(self.Close))
		cancelButton.Show()
		self.cancelButton = cancelButton
	
	def SetParent2(self, parent):
		self.getParent = parent
	
	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		ui.BoardWithTitleBar.Show(self)

	def Close(self):
		self.itemPrice = -1
		self.maxCount = 0
		self.packSize = 1
		self.countEditline.SetText("1")
		self.__UpdateCountLabel(1)
		self.Hide()

	def SetPackSize(self, packSize):
		try:
			self.packSize = max(1, int(packSize))
		except:
			self.packSize = 1

	def __UpdateCountLabel(self, count):
		if self.packSize > 1:
			self.countTextFirst.SetText("Alinacak paket: %d (%d adet)" % (count, count * self.packSize))
		else:
			self.countTextFirst.SetText("Alinacak toplam miktar: %d" % count)

	def acceptButtonEvent(self):
		itemName = self.titleName.GetText()
		itemCount = self.countEditline.GetText()
		price = self.itemPrice * int(itemCount)

		if self.getParent:
			if self.payWithEp:
				self.getParent.buyQuestionDialog(self.itemID, self.itemVnum, itemName, int(itemCount), price)
			else:
				self.getParent.buyQuestionDialog2(self.itemID, self.itemVnum, itemName, int(itemCount), price)
		
		self.Close()

	def __ClickValueEditLine(self):
		self.countEditline.SetFocus()
	
	def __OnValueUpdate(self):
		ui.EditLine.OnIMEUpdate(self.countEditline)

		text = self.countEditline.GetText()

		count = 1
		if text and text.isdigit():
			try:
				count = int(text)
				
				if count <= 0:
					count = 1

				if count > self.maxCount:
					count = self.maxCount
					self.countEditline.SetText("%d" % count)

			except ValueError:
				pass

		self.__UpdateCountLabel(count)

		price = self.itemPrice * count
		self.SetItemPrice(price)

	def __OnValueReturn(self):
		self.countEditline.KillFocus()

		text = self.countEditline.GetText()

		count = 1
		if text and text.isdigit():
			try:
				count = int(text)

				if count <= 0:
					count = 1

			except ValueError:
				count = 1

		self.countEditline.SetText("%d" % count)
		self.__UpdateCountLabel(count)
		price = self.itemPrice * count
		self.SetItemPrice(price)

	def __ArrowButton(self, type):
		self.countEditline.KillFocus()

		text = self.countEditline.GetText()

		count = 0

		if not text or not text.isdigit():
			count = 1
		else:
			count = int(text)

		if type == 0:
			count += 1
		else:
			count -= 1

		if count <= 0:
			count = 1
		elif count >= self.maxCount:
			count = self.maxCount

		self.countEditline.SetText("%d" % count)
		self.__UpdateCountLabel(count)
		price = self.itemPrice * count
		self.SetItemPrice(price)

	def SetItemPrice(self, price):
		if self.payWithEp:
			text = "Tutar : %s EP" % _FormatItemShopPriceDisplay(price)
		else:
			text = "Tutar : %s EM" % _FormatItemShopPriceDisplay(price)
		self.ammoutText.SetText(text)

	def SetCountText(self, price, playerBalance, payWithEp=True):
		self.payWithEp = payWithEp
		self.itemPrice = price
		if price > 0:
			self.maxCount = playerBalance / price
		else:
			self.maxCount = 1

		if self.maxCount < 1:
			self.maxCount = 1

		self.countTextSecond.SetText("/%d" % self.maxCount)

		if self.maxCount > 200:
			self.maxCount = 200

		self.SetItemPrice(price)

	def SetItem(self, itemID, itemVnum):
		self.itemID = itemID
		self.itemVnum = itemVnum


class ItemShopWindow(ui.ScriptWindow):
	def __init__(self, interface):
		ui.ScriptWindow.__init__(self)
		
		self.searchEditline = None
		self.searchButton = None
		self.boardFirst = None
		self.boardSecond = None
		self.scrollBar = None
		self.itemScrollBar = None

		self.categoryGroupBoard = None
		self.wndItemList = {}
		self.itemList = []
		
		self.itemStackalbeBuyDialog = None
		
		self.itemToolTip = None
		self.questionDialog = None
		self.interface = interface
		self.coins = 0
		self.marks = 0
		self.dragonmark = None
		self.marksIcon = None
		self.marksSlot = None
		self._emCurrencyVisible = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		if self.itemScrollBar:
			self.itemScrollBar.Hide()
			self.itemScrollBar = None
		self.ClearDictionary()

	def __BindItemShopMouseWheel(self, wnd):
		if not getattr(app, "ENABLE_MOUSEWHEEL_EVENT", False):
			return
		if wnd:
			wnd.SetMouseWheelEvent(ui.__mem_func__(self.OnScrollWheel))

	def LoadWindow(self):
		try:
			# Arapça'da ui.py'deki genel RTL ayna kodu (AddFlag("rtl") + LoadDefaultData)
			# bu pencerenin çocuklarını sağa aynalayıp kaydırıyordu. Sadece bu pencere
			# EN/LTR düzeniyle yüklensin diye yükleme süresince IsARABIC'i geçici olarak
			# kapatıyoruz; metin yönü kod sayfasından geldiği için Arapça yazı etkilenmez.
			__origIsArabic = localeInfo.IsARABIC
			localeInfo.IsARABIC = lambda: False
			try:
				ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/item_shop.py")
			finally:
				localeInfo.IsARABIC = __origIsArabic
		except:
			import exception
			exception.Abort("ItemShopWindow.LoadDialog.LoadObject")
		try:
			self.GetChild("TitleBar").SetCloseEvent(self.Close)

			self.searchEditline = self.GetChild("search_editline")
			self.searchButton = self.GetChild("search_button")

			self.boardFirst = self.GetChild("board_first")
			self.boardSecond = self.GetChild("board_second")

			for i in xrange(1, ITEM_SHOP_ITEM_VISIBLE_ROWS + 1):
				num = "0%d" % i
				try:
					self.GetChild("item_row_bg_%s" % num).AddFlag("not_pick")
				except KeyError:
					pass
			self.scrollBar = self.GetChild("ScrollBar")

			self.itemScrollBar = wikiui.ScrollBarSpecial(False)
			self.itemScrollBar.SetParent(self.boardSecond)
			sb_x = self.boardSecond.GetWidth() - 8 - ITEM_SHOP_SCROLLBAR_W
			self.itemScrollBar.SetPosition(sb_x, ITEM_SHOP_LIST_TOP)
			self.itemScrollBar.SetSize(ITEM_SHOP_SCROLLBAR_W, ITEM_SHOP_SCROLL_VIEW_H)
			self.itemScrollBar.SetScrollEvent(ui.__mem_func__(self.__OnItemScrollBar))
			self.itemScrollBar.SetScrollSpeed(150)
			self.itemScrollBar.Hide()
			self.itemScrollBar.SetTop()

			self.dragoncoin = self.GetChild("dragon_coin_text")
			self.dragoncoin.SetFontName(ITEM_SHOP_FONT)
			self.dragoncoin.SetOutline()
			self.dragoncoin.SetHorizontalAlignCenter()
			self.dragoncoin.SetVerticalAlignCenter()
			self.dragonmark = self.GetChild("dragon_mark_text")
			self.dragonmark.SetFontName(ITEM_SHOP_FONT)
			self.dragonmark.SetOutline()
			self.dragonmark.SetHorizontalAlignCenter()
			self.dragonmark.SetVerticalAlignCenter()
			self.marksIcon = self.GetChild("marks_icon")
			self.marksSlot = self.GetChild("Marks_Slot")
			self.coinBuyButton = self.GetChild("coin_buy_button")
			if self.coinBuyButton.ButtonText:
				# self.coinBuyButton.ButtonText.SetFontName(ITEM_SHOP_FONT)
				self.coinBuyButton.ButtonText.SetOutline()

			for i in xrange(1, ITEM_SHOP_ITEM_VISIBLE_ROWS + 1):
				number = "0%d" % i

				itemBoard = self.GetChild("itemBoard_%s" % number)
				wndItemSlot = self.GetChild("itemSlot_%s" % number)
				wndItemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.selectItemSlotEvent))
				wndItemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.selectItemSlotEvent))
				wndItemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
				wndItemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))

				itemName = self.GetChild("itemName_%s" % number)
				itemName.SetMax(40)
				itemName.SetLimitWidth(240)
				itemName.SetMultiLine()
				itemName.SetFontName(ITEM_SHOP_FONT)
				itemName.SetPackedFontColor(0xFFFFFFFF)
				itemName.SetOutline()
				itemOldPrice = self.GetChild("itemOldPrice_%s" % number)
				itemOldPrice.SetMax(20)
				itemOldPrice.SetLimitWidth(80)
				itemOldPrice.SetMultiLine()
				itemOldPrice.SetFontColor(0.85, 0.85, 0.85)
				itemOldPrice.SetFontName(ITEM_SHOP_FONT)
				itemOldPrice.SetOutline()
				itemPreviewButton = self.GetChild("itemPreviewButton_%s" % number)
				itemPreviewButton.Hide()
				itemBuyButton = self.GetChild("itemBuyButton_%s" % number)
				itemBuyButton.ButtonText.SetFontName(ITEM_SHOP_FONT)
				itemBuyButton.ButtonText.SetOutline()
				itemBuyButton.Disable()
				itemBuyButtonMark = self.GetChild("itemBuyButtonMark_%s" % number)
				itemBuyButtonMark.ButtonText.SetFontName(ITEM_SHOP_FONT)
				itemBuyButtonMark.ButtonText.SetOutline()
				itemBuyButtonMark.Disable()
				
				self.wndItemList[i] = (itemBoard, wndItemSlot, itemName, itemOldPrice, itemPreviewButton, itemBuyButton, itemBuyButtonMark)
		except:
			import exception
			exception.Abort("ItemShopWindow.LoadDialog.BindObject")
		
		self.searchEditline.SetFontName(ITEM_SHOP_FONT)
		self.searchEditline.OnIMEReturn = ui.__mem_func__(self.searchButtonEvent)
		self.searchButton.SetEvent(ui.__mem_func__(self.searchButtonEvent))
		self.coinBuyButton.SetEvent(ui.__mem_func__(self.coinButtonEvent))

		categoryGroupBoard = CategoryBoard(self, self.boardFirst, self.scrollBar)
		categoryGroupBoard.SetSize(self.boardFirst.GetWidth() - 25, self.boardFirst.GetHeight())
		categoryGroupBoard.Show()
		self.categoryGroupBoard = categoryGroupBoard

		self.__BindItemShopMouseWheel(self)
		self.__BindItemShopMouseWheel(self.GetChild("board"))
		self.__BindItemShopMouseWheel(self.boardFirst)
		self.__BindItemShopMouseWheel(self.boardSecond)
		self.__BindItemShopMouseWheel(self.categoryGroupBoard)

		itemStackalbeBuyDialog = ItemStackableBuyDialog()
		itemStackalbeBuyDialog.SetParent2(self)
		itemStackalbeBuyDialog.SetCenterPosition()
		itemStackalbeBuyDialog.Hide()
		self.itemStackalbeBuyDialog = itemStackalbeBuyDialog
		
		self.questionDialog = uiCommon.QuestionDialog2()
		self.questionDialog.SetAcceptEvent(lambda arg = True: self.QuestionDialogEvent(arg))
		self.questionDialog.SetCancelEvent(lambda arg = False: self.QuestionDialogEvent(arg))
		self.questionDialog.Hide()
				
	def OnScrollWheel(self, nLen):
		if not self.IsShow():
			return False
		if not self.IsInPosition():
			return False

		if self.itemScrollBar and self.itemScrollBar.IsShow():
			self.itemScrollBar.OnMouseWheel(nLen)
			return True

		return True

	def SetItemToolTip(self, itemToolTip):
		self.itemToolTip = itemToolTip
		
	def __HasPlayerEm(self):
		return self.marks > 0

	def __CanBuyItemShopWithEm(self, itemVnum):
		try:
			if itemVnum in constInfo.ITEM_SHOP_EM_PURCHASE_BLOCKED_VNUMS:
				return False
		except AttributeError:
			if itemVnum in (80014, 80015, 80016, 80017):
				return False
		return True

	def __RefreshEmCurrencyVisibility(self):
		showEm = self.__HasPlayerEm()

		if self.marksIcon:
			if showEm:
				self.marksIcon.Show()
			else:
				self.marksIcon.Hide()

		if self.marksSlot:
			if showEm:
				self.marksSlot.Show()
			else:
				self.marksSlot.Hide()

		if self.dragonmark and showEm:
			self.dragonmark.SetText("%s EM" % _FormatItemShopPriceDisplay(self.marks))

	def OnUpdate(self):
		self.coins = int(player.GetDragonCoin())
		self.marks = int(player.GetDragonMark())
		self.dragoncoin.SetText("%s EP" % _FormatItemShopPriceDisplay(self.coins))

		emVisible = self.__HasPlayerEm()
		prevEmVisible = self._emCurrencyVisible
		self.__RefreshEmCurrencyVisibility()
		self._emCurrencyVisible = emVisible

		if prevEmVisible is not None and prevEmVisible != emVisible and self.itemList:
			self.__RefreshItemRowsFromScroll()


	def Open(self):
		self.max_pos_x = wndMgr.GetScreenWidth() - self.GetWidth()
		self.max_pos_y = wndMgr.GetScreenHeight() - self.GetHeight()
		self.SetCenterPosition()
		self.coins = int(player.GetDragonCoin())
		self.marks = int(player.GetDragonMark())
		self._emCurrencyVisible = None
		self.__RefreshEmCurrencyVisibility()
		self.categoryGroupBoard.RefreshProcess()
		self.categoryGroupBoard.firstOpenBoard()
		ui.ScriptWindow.Show(self)
		self.SetTop()

	def Close(self):
		ui.ScriptWindow.Hide(self)
		#renderTarget.SetVisibility(6, true) ##kapal?yd?
		if self.itemStackalbeBuyDialog:
			self.itemStackalbeBuyDialog.Close()
		
		if self.questionDialog:
			self.questionDialog.Close()
		
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def ClearItemBoard(self):
		for i in xrange(1, ITEM_SHOP_ITEM_VISIBLE_ROWS + 1):
			(itemBoard, wndItemSlot, itemName, itemOldPrice, itemPreviewButton, itemBuyButton, itemBuyButtonMark) = self.wndItemList[i]
			itemBoard.Hide()
			wndItemSlot.ClearSlot(i)
			wndItemSlot.RefreshSlot()

			itemName.SetText("")
			itemOldPrice.SetText("")
			itemPreviewButton.Hide()
			itemBuyButton.SetText("")
			itemBuyButton.Disable()
			itemBuyButtonMark.SetText("")
			itemBuyButtonMark.Disable()
			itemBuyButtonMark.Hide()

	def __TotalItemContentHeight(self, n):
		if n <= 0:
			return 0
		return n * ITEM_SHOP_ROW_H + (n - 1) * ITEM_SHOP_ROW_GAP

	def __UpdateItemScrollBarState(self):
		if not self.itemScrollBar:
			return
		n = len(self.itemList)
		if n <= ITEM_SHOP_ITEM_VISIBLE_ROWS:
			self.itemScrollBar.Hide()
			self.itemScrollBar.SetPos(0)
			return
		total = self.__TotalItemContentHeight(n)
		self.itemScrollBar.SetSize(ITEM_SHOP_SCROLLBAR_W, ITEM_SHOP_SCROLL_VIEW_H)
		self.itemScrollBar.SetScale(ITEM_SHOP_SCROLL_VIEW_H, total)
		self.itemScrollBar.Show()
		self.itemScrollBar.SetTop()

	def __OnItemScrollBar(self):
		self.__RefreshItemRowsFromScroll()

	def __GetScrollStartIndex(self):
		n = len(self.itemList)
		mx = max(0, n - ITEM_SHOP_ITEM_VISIBLE_ROWS)
		start = 0
		if self.itemScrollBar and self.itemScrollBar.IsShow() and mx > 0:
			start = int(self.itemScrollBar.GetPos() * mx + 1e-6)
		if start > mx:
			start = mx
		return start

	def __RefreshItemRowsFromScroll(self):
		n = len(self.itemList)
		start = self.__GetScrollStartIndex()
		visibleRow = 0
		for i in xrange(1, ITEM_SHOP_ITEM_VISIBLE_ROWS + 1):
			itemPos = start + (i - 1)
			(itemBoard, wndItemSlot, itemName, itemOldPrice, itemPreviewButton, itemBuyButton, itemBuyButtonMark) = self.wndItemList[i]

			if itemPos >= n:
				itemBoard.Hide()
				continue

			(empty, itemID, itemVnum, itemPrice, itemPriceOld, itemCount, itemSocketZero, itemMark, metinSlot, attrslot) = self.itemList[itemPos]
			itemBoard.SetPosition(
				ITEM_SHOP_ROW_START_X,
				ITEM_SHOP_LIST_TOP + visibleRow * (ITEM_SHOP_ROW_H + ITEM_SHOP_ROW_GAP),
			)
			visibleRow += 1
			itemBoard.Show()

			wndItemSlot.SetItemSlot(i, itemVnum, itemCount)
			wndItemSlot.RefreshSlot()

			item.SelectItem(itemVnum)

			itemType = item.GetItemType()
			itemSubType = item.GetItemSubType()
			itemValue = item.GetValue(0)
			itemHair = item.GetValue(3)
			(affectTypem, affectValuem) = item.GetAffect(0)
			race = player.GetRace()
			job = chr.RaceToJob(race)
			sex = chr.RaceToSex(race)
			MALE = 1
			FEMALE = 0

			ANTI_FLAG_DICT = {
				0 : item.ITEM_ANTIFLAG_WARRIOR,
				1 : item.ITEM_ANTIFLAG_ASSASSIN,
				2 : item.ITEM_ANTIFLAG_SURA,
				3 : item.ITEM_ANTIFLAG_SHAMAN,
			}

			isItemPreview = False
			if itemType == item.ITEM_TYPE_WEAPON:
				isItemPreview = True
			if itemType == item.ITEM_TYPE_ARMOR and itemSubType == item.ARMOR_BODY:
				isItemPreview = True
			if itemType == item.ITEM_TYPE_COSTUME:
				isItemPreview = True

			if not ANTI_FLAG_DICT.has_key(job):
				isItemPreview = False
			if item.IsAntiFlag(ANTI_FLAG_DICT[job]):
				isItemPreview = False
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == MALE:
				isItemPreview = False
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == FEMALE:
				isItemPreview = False

			# if isItemPreview:
				# itemPreviewButton.Show()

			itemName.SetText(item.GetItemName())
			itemOldPrice.SetText("%d adet." % int(itemCount))

			if itemPrice > 0:
				itemBuyButton.SetText("%s EP" % _FormatItemShopPriceDisplay(itemPrice))
				itemBuyButton.SetEvent(ui.__mem_func__(self.buyButtonEvent), itemID, itemVnum, itemPrice, itemCount, itemMark, True)
				itemBuyButton.Show()
				itemBuyButton.Enable()
			else:
				itemBuyButton.SetText("")
				itemBuyButton.Disable()
				itemBuyButton.Hide()

			if itemMark > 0 and self.__HasPlayerEm() and self.__CanBuyItemShopWithEm(itemVnum):
				itemBuyButtonMark.SetText("%s EM" % _FormatItemShopPriceDisplay(itemMark))
				itemBuyButtonMark.SetEvent(ui.__mem_func__(self.buyButtonEvent), itemID, itemVnum, itemPrice, itemCount, itemMark, False)
				itemBuyButtonMark.Show()
				itemBuyButtonMark.Enable()
			else:
				itemBuyButtonMark.SetText("")
				itemBuyButtonMark.Disable()
				itemBuyButtonMark.Hide()

	def ChangeCategory(self, categoryID, subCategoryID):
		self.ClearItemBoard()

		if not constInfo.ITEM_DATA.has_key(categoryID):
			return

		category = constInfo.ITEM_DATA[categoryID]

		if not category.has_key(subCategoryID):
			return

		category = category[subCategoryID]
		self.itemList = [item for item in category]
		if self.itemScrollBar:
			self.itemScrollBar.SetPos(0)
		self.RefreshProcess()

	def coinButtonEvent(self):
		if self.interface:
			os.startfile("https://www.ayazmt2.com/panel/ep-yukle")

	def RefreshProcess(self):
		self.ClearItemBoard()
		self.__UpdateItemScrollBarState()
		self.__RefreshItemRowsFromScroll()

	def searchButtonEvent(self):
		searchText = self.searchEditline.GetText()
		if len(searchText) < 3:
			chat.AppendChat(5, "Aranacak kelime cok kisa")
			return True
		
		self.SearchItem(searchText)
		return True

	def SearchItem(self, itemName):
		searchItemList = filter(lambda item: item[0].find(toLower(itemName)) != -1, constInfo.ITEM_SEARCH_DATA)
		
		if not searchItemList:
			chat.AppendChat(1, "%s iceren nesne bulunamadi." % itemName)
			return

		self.itemList = [item for item in searchItemList]
		if self.itemScrollBar:
			self.itemScrollBar.SetPos(0)

		self.RefreshProcess()

	def buyButtonEvent(self, itemID, itemVnum, itemPrice, itemCount, itemMark, payWithEp=True):
		if itemVnum == 0:
			return

		if not payWithEp and not self.__CanBuyItemShopWithEm(itemVnum):
			try:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.nesnemarketemilealinemez)
			except:
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Bu urun EM ile satin alinamaz.")
			return

		item.SelectItem(itemVnum)
		if payWithEp:
			if itemPrice <= 0:
				return
			payPrice = itemPrice
		else:
			if itemMark <= 0:
				return
			payPrice = itemMark

		if item.IsFlag(ITEM_FLAG_STACKABLE):
			self.itemStackalbeBuyDialog.SetItem(itemID, itemVnum)
			if payWithEp:
				self.itemStackalbeBuyDialog.SetCountText(itemPrice, self.coins, True)
			else:
				self.itemStackalbeBuyDialog.SetCountText(itemMark, self.marks, False)
			self.itemStackalbeBuyDialog.SetTitleName(item.GetItemName())
			self.itemStackalbeBuyDialog.SetPackSize(itemCount)
			self.itemStackalbeBuyDialog.Open()
		else:
			if payWithEp:
				self.buyQuestionDialog(itemID, itemVnum, item.GetItemName(), 1, payPrice)
			else:
				self.buyQuestionDialog2(itemID, itemVnum, item.GetItemName(), 1, payPrice)

	def buyQuestionDialog(self, itemID, itemVnum, itemName, itemCount, itemPrice):
		self.questionDialog.SetText1(localeInfo.ASK_BUY_ITEM_TEXT % itemName)
		self.questionDialog.SetText2(localeInfo.DO_YOU_BUY_ITEM_COINS(itemCount, itemPrice))
		self.questionDialog.itemID = itemID
		self.questionDialog.itemVnum = itemVnum
		self.questionDialog.itemCount = itemCount
		self.questionDialog.payType = 0
		self.questionDialog.SetWidth(385)
		self.questionDialog.SetTop()
		self.questionDialog.Open()
		
	def buyQuestionDialog2(self, itemID, itemVnum, itemName, itemCount, itemMark):
		self.questionDialog.SetText1(localeInfo.ASK_BUY_ITEM_TEXT % itemName)
		self.questionDialog.SetText2(localeInfo.DO_YOU_BUY_ITEM_MARK(itemCount, itemMark))
		self.questionDialog.itemID = itemID
		self.questionDialog.itemVnum = itemVnum
		self.questionDialog.itemCount = itemCount
		self.questionDialog.payType = 1
		self.questionDialog.SetWidth(385)
		self.questionDialog.SetTop()
		self.questionDialog.Open()

	def QuestionDialogEvent(self, arg):
		if not self.questionDialog:
			return
		
		if arg:
			itemID = self.questionDialog.itemID
			itemCount = self.questionDialog.itemCount
			payType = getattr(self.questionDialog, "payType", 2)
			net.SendChatPacket("/nesne_market %d %d %d" % (itemID, itemCount, payType))

		self.questionDialog.Close()
	
	def selectItemSlotEvent(self, itemIndex):
		start = self.__GetScrollStartIndex()
		itemPos = start + (itemIndex - 1)

		if len(self.itemList) <= itemPos:
				return

		(empty, itemID, itemVnum, itemPrice,itemPriceOld, itemCount, itemSocketZero, itemMark, metinSlot, attrslot) = self.itemList[itemPos]

		if itemVnum == 0:
			return

		self.buyButtonEvent(itemID, itemVnum, itemPrice, itemCount, itemMark, True)

	def OverInItem(self, itemIndex):
		if not self.itemToolTip:
			return

		self.itemToolTip.ClearToolTip()
		start = self.__GetScrollStartIndex()
		itemPos = start + (itemIndex - 1)

		if len(self.itemList) <= itemPos:
				return

		(empty, itemID, itemVnum, itemPrice,itemPriceOld, itemCount, itemSocketZero, itemMark, metinSlot, attrSlot) = self.itemList[itemPos]

		if itemVnum == 0:
			return

		item.SelectItem(itemVnum)

		if not item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR, item.ITEM_TYPE_BELT):
			# itemSocketZero = itemSocketZero+app.GetGlobalTimeStamp()
			# metinSlot = [itemSocketZero,0,0,0]
			if metinSlot[0] == 0:
				metinSlot[0] = itemSocketZero

		if item.GetItemType() == item.ITEM_TYPE_UNIQUE and item.GetValue(0) < (31 * 60 * 60 * 24):
			metinSlot[player.METIN_SOCKET_MAX_NUM-1] = item.GetValue(0)
		elif item.GetItemType() == item.ITEM_TYPE_USE and item.GetValue(3) < (31 * 60 * 60 * 24):
			metinSlot[0] = item.GetValue(3)

		self.itemToolTip.AddItemData(itemVnum, metinSlot, attrSlot)
		self.itemToolTip.Show()

	def OnOverOutItem(self):
		if not self.itemToolTip:
			return

		self.itemToolTip.ClearToolTip()
		self.itemToolTip.Hide()

