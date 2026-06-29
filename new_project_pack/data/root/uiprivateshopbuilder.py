import ui
import snd
import shop
import mouseModule
import player
import chr
import net
import uiCommon
import localeInfo
import chat
import item
import systemSetting
import player
import app
import grp
import wndMgr

g_isBuildingPrivateShop = False

g_itemPriceDict={}

if app.ENABLE_CHEQUE_SYSTEM:
	g_itemChequeDict={}

g_privateShopAdvertisementBoardDict={}

# Oyuncunun daha once tikladigi pazarlarin VID'leri. Tiklanan pazarin cercevesi
# kirmizi gosterilir. VID'ler harita degisiminde yeniden atandigi icin Clear()'da
# sifirlanir (yanlis kirmizi isareti olmasin).
g_clickedShopVIDs = {}

# Tum pazar basliklarini TEK noktadan gunceleyen merkezi yonetici (kasma onleme).
# Bkz. _ADBoardManager. Clear()'da sifirlanir.
g_adBoardManager = None

def Clear():
	global g_itemPriceDict
	global g_isBuildingPrivateShop
	if app.ENABLE_CHEQUE_SYSTEM:
		global g_itemChequeDict
		g_itemChequeDict={}
	g_itemPriceDict={}
	g_isBuildingPrivateShop = False
	# @fixme007 BEGIN
	global g_privateShopAdvertisementBoardDict
	g_privateShopAdvertisementBoardDict={}
	# @fixme007 END
	global g_clickedShopVIDs
	g_clickedShopVIDs = {}
	# Harita degisiminde VID'ler yeniden atandigi icin merkezi yoneticiyi de
	# sifirla; bir sonraki pazar gorununce EnsureADBoardManager yeniden olusturur.
	global g_adBoardManager
	g_adBoardManager = None

def IsPrivateShopItemPriceList():
	global g_itemPriceDict
	if g_itemPriceDict:
		return True
	else:
		return False

if app.ENABLE_CHEQUE_SYSTEM:
	def IsPrivateShopItemChequeList():
		global g_itemChequeDict
		if g_itemChequeDict:
			return True
		else:
			return False

def IsBuildingPrivateShop():
	global g_isBuildingPrivateShop
	if player.IsOpenPrivateShop() or g_isBuildingPrivateShop:
		return True
	else:
		return False

def SetPrivateShopItemPrice(itemVNum, itemPrice):
	global g_itemPriceDict
	g_itemPriceDict[int(itemVNum)]=itemPrice

def GetPrivateShopItemPrice(itemVNum):
	try:
		global g_itemPriceDict
		return g_itemPriceDict[itemVNum]
	except KeyError:
		return 0

if app.ENABLE_CHEQUE_SYSTEM:
	def SetPrivateShopItemCheque(itemVNum, itemPrice):
		global g_itemChequeDict
		g_itemChequeDict[int(itemVNum)]=itemPrice

	def GetPrivateShopItemCheque(itemVNum):
		try:
			global g_itemChequeDict
			return g_itemChequeDict[itemVNum]
		except KeyError:
			return 0

def UpdateADBoard():
	# Secenek (market ismi goster ac/kapa) degisince merkezi yoneticiyi olustur
	# ve throttle beklemeden hemen yeniden degerlendir.
	EnsureADBoardManager().ForceUpdate()

def DeleteADBoard(vid):
	if not g_privateShopAdvertisementBoardDict.has_key(vid):
		return

	del g_privateShopAdvertisementBoardDict[vid]


class ShopNameBoard(ui.Window):
	# Pazar basligi icin HAFIF tahta. Standart ui.ThinBoard pazar basina 8 adet
	# .tga resim kutusu (4 kose + 4 kenar) yukler; ekranda cok pazar olunca FPS
	# duser. Burada resim yerine sadece 2 cizili primitif kullaniliyor:
	#   Box  -> RenderBox2d  (cerceve / dis hat)
	#   Bar  -> RenderBar2d  (dolgu)
	# Boylece dokulu quad yerine 2 renkli dikdortgen cizilir.
	BOARD_COLOR        = grp.GenerateColor(0.0, 0.0, 0.0, 0.40)	# dolgu (Bar)  -> son sayi = opaklik (0.0 seffaf .. 1.0 tam opak)
	BOARD_BASE_COLOR   = grp.GenerateColor(0.0, 0.0, 0.0, 0.55)	# cerceve (Box) normal renk
	# BOARD_CLICKED_COLOR = grp.GenerateColor(0.9, 0.1, 0.1, 1.0)	# cerceve (Box) -> daha once tiklanan pazar (kirmizi)

	def __init__(self, layer = "UI"):
		ui.Window.__init__(self, layer)

		Box = ui.Box()
		Box.SetParent(self)
		Box.AddFlag("attach")
		Box.AddFlag("not_pick")
		Box.SetPosition(0, 0)
		Box.SetColor(self.BOARD_BASE_COLOR)
		Box.Show()
		self.Box = Box

		Base = ui.Bar()
		Base.SetParent(self.Box)
		Base.AddFlag("attach")
		Base.AddFlag("not_pick")
		Base.SetPosition(0, 0)
		Base.SetColor(self.BOARD_COLOR)
		Base.Show()
		self.Base = Base

	def __del__(self):
		ui.Window.__del__(self)

	def SetSize(self, width, height = 20):
		ui.Window.SetSize(self, width, height)
		self.Base.SetSize(width, height)
		self.Box.SetSize(width, height)

	def SetFrameColor(self, color):
		self.Box.SetColor(color)

	def ShowInternal(self):
		self.Base.Show()
		self.Box.Show()

	def HideInternal(self):
		self.Base.Hide()
		self.Box.Hide()

class PrivateShopAdvertisementBoard(ShopNameBoard):
	TEXT_NORMAL_COLOR  = (1.0, 1.0, 1.0)	# normal baslik (beyaz)
	TEXT_CLICKED_COLOR = (1.0, 0.55, 0.0)	# daha once tiklanan pazarin basligi (turuncu)

	def __init__(self):
		ShopNameBoard.__init__(self, "UI_BOTTOM")
		self.vid = None
		# Gorunurlugu merkezi _ADBoardManager yonetir.
		self.wantShow = False	# menzil/secenek gate'i (throttle'li hesaplanir)
		self.shown = False		# gercek Show durumu (gereksiz C++ cagrisini onler)
		self.boardW = 0
		self.boardH = 0
		self.__MakeTextLine()

	def __del__(self):
		ShopNameBoard.__del__(self)

	def __MakeTextLine(self):
		self.textLine = ui.TextLine()
		self.textLine.SetParent(self)
		self.textLine.SetWindowHorizontalAlignCenter()
		self.textLine.SetWindowVerticalAlignCenter()
		self.textLine.SetHorizontalAlignCenter()
		self.textLine.SetVerticalAlignCenter()
		self.textLine.Show()

	def Open(self, vid, text):
		self.vid = vid

		self.textLine.SetText(text)
		self.textLine.UpdateRect()
		self.boardW = len(text)*6 + 10*2
		self.boardH = 30
		self.SetSize(self.boardW, self.boardH)
		self.__RefreshTitleColor()
		# Gorunurlugu artik merkezi _ADBoardManager belirler. Tabelayi gizli
		# olustur ki manager ilk konumlandirmadan once sol ust kosede (0,0)
		# bir kare bile gorunmesin.
		self.Hide()
		self.shown = False

		g_privateShopAdvertisementBoardDict[vid] = self

	def __RefreshTitleColor(self):
		# Cerceve her zaman normal kalir; daha once tiklanan pazarin BASLIK YAZISI
		# turuncu, digerleri normal (beyaz).
		if self.vid in g_clickedShopVIDs:
			self.textLine.SetFontColor(*self.TEXT_CLICKED_COLOR)
		else:
			self.textLine.SetFontColor(*self.TEXT_NORMAL_COLOR)

	def OnMouseLeftButtonUp(self):
		if not self.vid:
			return
		net.SendOnClickPacket(self.vid)

		# Bu pazara tiklandi -> kaydet ve SADECE basligi turuncu yap (cerceve normal kalir)
		g_clickedShopVIDs[self.vid] = 1
		self.textLine.SetFontColor(*self.TEXT_CLICKED_COLOR)

		return True

	# NOT: Tabelalarin kendi OnUpdate'i KALDIRILDI. Eskiden her tabela kendi
	# OnUpdate'inde Show() kalip, gorus disinda olanlari Hide() etmek yerine
	# ekran disina (-10000,-10000) tasiyordu (cunku gizli pencere OnUpdate almaz).
	# Ancak engine, Show()'lu bir pencereyi -konum farketmeksizin- HER kare hem
	# OnUpdate hem OnRender (Box+Bar+TextLine cizimi, VB lock + DrawPrimitive) ile
	# isler. Yani ekran disindaki tabelalar da tam render maliyeti oduyordu ->
	# cok pazarda asiri kasma. Cozum: gorunurlugu tek bir surekli-acik
	# _ADBoardManager yonetir; gorus disi/kamera arkasi/ekran disi tabelalar
	# GERCEKTEN Hide() edilir (sifir maliyet) ve tekrar gorus icine girince
	# manager yeniden Show() eder.

class _ADBoardManager(ui.Window):
	# Tum pazar basliklarini TEK noktadan gunceller. Bu pencere HER ZAMAN Show()
	# kalir (boylece engine OnUpdate vermeye devam eder) ama boyutu 0 ve hic
	# cocugu yok -> kendi render maliyeti SIFIR. Asil tabelalari gorunurluge gore
	# Show()/Hide() eder.
	#
	# TITREME ONLEME: menzil/secenek karari (chr.CanRenderShop = mesafe hesabi)
	# pahali oldugu icin throttle'li yapilir; ama KONUM (GetProjectPosition +
	# SetPosition) gosterilen her tabela icin HER kare guncellenir. Boylece
	# baslik, hareket ederken dukkanin uzerine kilitli kalir (ziplama/titreme yok).
	# Ekran disina tasan tabelalar GERCEKTEN Hide() edilir -> render maliyeti yok.
	REEVAL_INTERVAL_MS = 150	# menzil/secenek gate'i ~7 Hz; konum zaten her kare

	def __init__(self):
		ui.Window.__init__(self, "UI")
		self.SetPosition(-10000, -10000)
		self.SetSize(0, 0)
		self.lastTime = 0
		self.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def ForceUpdate(self):
		# Bir sonraki OnUpdate'te menzil/secenek gate'ini hemen yeniden hesapla.
		self.lastTime = 0

	def OnUpdate(self):
		boards = g_privateShopAdvertisementBoardDict
		if not boards:
			return

		mainVID = player.GetMainCharacterIndex()

		# 1) Menzil/secenek gate'i: SADECE throttle aninda (mesafe hesabi pahali).
		#    Sonuc board.wantShow'da saklanir; konum dongusu bunu okur.
		now = app.GetGlobalTime()	# milisaniye
		if now - self.lastTime >= self.REEVAL_INTERVAL_MS:
			self.lastTime = now
			showText = systemSetting.IsShowSalesText()
			canCheck = hasattr(chr, "CanRenderShop")
			for vid in boards.keys():
				board = boards[vid]
				if vid == mainVID:
					board.wantShow = True	# kendi pazari her zaman (secenekten bagimsiz)
				elif not showText:
					board.wantShow = False
				elif canCheck and not chr.CanRenderShop(vid):
					board.wantShow = False
				else:
					board.wantShow = True

		# 2) Konum + ekran-disi kirpma: HER kare (titreme yok, off-screen render yok).
		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		for vid in boards.keys():
			board = boards[vid]

			# Menzil/secenek disi -> gizli kalmali (sadece gecis aninda Hide cagir).
			if not board.wantShow:
				if board.shown:
					board.Hide()
					board.shown = False
				continue

			x, y = chr.GetProjectPosition(vid, 220)
			w = board.boardW
			h = board.boardH
			px = x - w / 2
			py = y - h / 2

			# Kamera arkasi (-100,-100 sentinel) ya da tamamen ekran disi -> gizle.
			if (-100 == x and -100 == y) or px >= sw or py >= sh or (px + w) <= 0 or (py + h) <= 0:
				if board.shown:
					board.Hide()
					board.shown = False
			else:
				board.SetPosition(px, py)
				if not board.shown:
					board.Show()
					board.shown = True


def EnsureADBoardManager():
	global g_adBoardManager
	if g_adBoardManager is None:
		g_adBoardManager = _ADBoardManager()
	return g_adBoardManager


class PrivateShopBuilder(ui.ScriptWindow):

	def __init__(self):
		#print "NEW MAKE_PRIVATE_SHOP_WINDOW ----------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)

		self.__LoadWindow()
		self.itemStock = {}
		self.tooltipItem = None
		self.priceInputBoard = None
		self.title = ""
		if app.ENABLE_INVENTORY_SLOT_MARKING:
			self.interface = None
			self.wndInventory = None
			self.lockedItems = {i:(-1,-1) for i in range(shop.SHOP_SLOT_COUNT)}

	def __del__(self):
		#print "------------------------------------------------------------- DELETE MAKE_PRIVATE_SHOP_WINDOW"
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/PrivateShopBuilder.py")
		except:
			import exception
			exception.Abort("PrivateShopBuilderWindow.LoadWindow.LoadObject")

		try:
			GetObject = self.GetChild
			self.nameLine = GetObject("NameLine")
			self.itemSlot = GetObject("ItemSlot")
			self.btnOk = GetObject("OkButton")
			self.btnClose = GetObject("CloseButton")
			self.titleBar = GetObject("TitleBar")
		except:
			import exception
			exception.Abort("PrivateShopBuilderWindow.LoadWindow.BindObject")

		self.btnOk.SetEvent(ui.__mem_func__(self.OnOk))
		self.btnClose.SetEvent(ui.__mem_func__(self.OnClose))
		self.titleBar.SetCloseEvent(ui.__mem_func__(self.OnClose))

		self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()

		self.nameLine = None
		self.itemSlot = None
		self.btnOk = None
		self.btnClose = None
		self.titleBar = None
		self.priceInputBoard = None
		if app.ENABLE_INVENTORY_SLOT_MARKING:
			self.interface = None
			self.wndInventory = None
			self.lockedItems = {i:(-1,-1) for i in range(shop.SHOP_SLOT_COUNT)}

	def Open(self, title):

		self.title = title

		if len(title) > 25:
			title = title[:22] + "..."

		self.itemStock = {}
		shop.ClearPrivateShopStock()
		self.nameLine.SetText(title)
		self.SetCenterPosition()
		self.Refresh()
		self.Show()

		if app.ENABLE_INVENTORY_SLOT_MARKING:
			self.lockedItems = {i:(-1,-1) for i in range(shop.SHOP_SLOT_COUNT)}
			self.interface.SetOnTopWindow(player.ON_TOP_WND_PRIVATE_SHOP)
			self.interface.RefreshMarkInventoryBag()

		global g_isBuildingPrivateShop
		g_isBuildingPrivateShop = True

	def Close(self):
		global g_isBuildingPrivateShop
		g_isBuildingPrivateShop = False

		self.title = ""
		self.itemStock = {}
		shop.ClearPrivateShopStock()
		self.Hide()

		if app.ENABLE_INVENTORY_SLOT_MARKING:
			for privatePos, (itemInvenPage, itemSlotPos) in self.lockedItems.items():
				if itemInvenPage == self.wndInventory.GetInventoryPageIndex():
					self.wndInventory.wndItem.SetCanMouseEventSlot(itemSlotPos)

			self.lockedItems = {i:(-1,-1) for i in range(shop.SHOP_SLOT_COUNT)}
			self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
			self.interface.RefreshMarkInventoryBag()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def Refresh(self):
		getitemVNum=player.GetItemIndex
		getItemCount=player.GetItemCount
		setitemVNum=self.itemSlot.SetItemSlot
		delItem=self.itemSlot.ClearSlot

		for i in xrange(shop.SHOP_SLOT_COUNT):

			if not self.itemStock.has_key(i):
				delItem(i)
				continue

			pos = self.itemStock[i]

			itemCount = getItemCount(*pos)
			if itemCount <= 1:
				itemCount = 0
			setitemVNum(i, getitemVNum(*pos), itemCount)

		self.itemSlot.RefreshSlot()

		if app.ENABLE_INVENTORY_SLOT_MARKING:
			self.RefreshLockedSlot()

	def OnSelectEmptySlot(self, selectedSlotPos):

		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if player.SLOT_TYPE_INVENTORY != attachedSlotType and player.SLOT_TYPE_DRAGON_SOUL_INVENTORY != attachedSlotType:
				return
			attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)

			itemVNum = player.GetItemIndex(attachedInvenType, attachedSlotPos)
			item.SelectItem(itemVNum)

			if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PRIVATE_SHOP_CANNOT_SELL_ITEM)
				return

			if app.ENABLE_INVENTORY_SLOT_MARKING and player.SLOT_TYPE_INVENTORY == attachedSlotType:
				self.CantTradableItem(selectedSlotPos, attachedSlotPos)

			priceInputBoard = uiCommon.MoneyInputDialog()
			priceInputBoard.SetTitle(localeInfo.PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE)
			priceInputBoard.SetPerUnitCount(player.GetItemCount(attachedInvenType, attachedSlotPos))
			priceInputBoard.SetAcceptEvent(ui.__mem_func__(self.AcceptInputPrice))
			priceInputBoard.SetCancelEvent(ui.__mem_func__(self.CancelInputPrice))
			priceInputBoard.Open()

			itemPrice=GetPrivateShopItemPrice(itemVNum)

			if itemPrice>0:
				priceInputBoard.SetValue(itemPrice)

			if app.ENABLE_CHEQUE_SYSTEM:
				itemCheque=GetPrivateShopItemCheque(itemVNum)
				if itemCheque>0:
					priceInputBoard.SetValueCheque(itemCheque)

			self.priceInputBoard = priceInputBoard
			self.priceInputBoard.itemVNum = itemVNum
			self.priceInputBoard.sourceWindowType = attachedInvenType
			self.priceInputBoard.sourceSlotPos = attachedSlotPos
			self.priceInputBoard.targetSlotPos = selectedSlotPos

	def OnSelectItemSlot(self, selectedSlotPos):

		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			snd.PlaySound("sound/ui/loginfail.wav")
			mouseModule.mouseController.DeattachObject()

		else:
			if not selectedSlotPos in self.itemStock:
				return

			invenType, invenPos = self.itemStock[selectedSlotPos]
			shop.DelPrivateShopItemStock(invenType, invenPos)
			snd.PlaySound("sound/ui/drop.wav")

			if app.ENABLE_INVENTORY_SLOT_MARKING:
				(itemInvenPage, itemSlotPos) = self.lockedItems[selectedSlotPos]
				if itemInvenPage == self.wndInventory.GetInventoryPageIndex():
					self.wndInventory.wndItem.SetCanMouseEventSlot(itemSlotPos)

				self.lockedItems[selectedSlotPos] = (-1, -1)

			del self.itemStock[selectedSlotPos]

			self.Refresh()

	def AcceptInputPrice(self):

		if not self.priceInputBoard:
			return True

		if app.ENABLE_CHEQUE_SYSTEM:
			text = self.priceInputBoard.GetText()
			cheque = self.priceInputBoard.GetTextCheque()
			if not text:
				return
			if not text.isdigit():
				return

			if not cheque:
				return
			if not cheque.isdigit():
				return

			if int(cheque) <=0 and int(text)<=0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHEQUE_NO_ADD_SALE_PRICE)
				return
		else:
			text = self.priceInputBoard.GetText()

			if not text:
				return True

			if not text.isdigit():
				return True

			if int(text) <= 0:
				return True

		attachedInvenType = self.priceInputBoard.sourceWindowType
		sourceSlotPos = self.priceInputBoard.sourceSlotPos
		targetSlotPos = self.priceInputBoard.targetSlotPos

		for privatePos, (itemWindowType, itemSlotIndex) in self.itemStock.items():
			if itemWindowType == attachedInvenType and itemSlotIndex == sourceSlotPos:
				shop.DelPrivateShopItemStock(itemWindowType, itemSlotIndex)
				del self.itemStock[privatePos]

		price = int(self.priceInputBoard.GetText())

		if IsPrivateShopItemPriceList():
			SetPrivateShopItemPrice(self.priceInputBoard.itemVNum, price)

		if app.ENABLE_CHEQUE_SYSTEM:
			chequep = int(self.priceInputBoard.GetTextCheque())
			if IsPrivateShopItemChequeList():
				SetPrivateShopItemCheque(self.priceInputBoard.itemVNum, chequep)
			shop.AddPrivateShopItemStock(attachedInvenType, sourceSlotPos, targetSlotPos, price, chequep)
		else:
			shop.AddPrivateShopItemStock(attachedInvenType, sourceSlotPos, targetSlotPos, price)
		self.itemStock[targetSlotPos] = (attachedInvenType, sourceSlotPos)
		snd.PlaySound("sound/ui/drop.wav")

		self.Refresh()

		#####

		self.priceInputBoard = None
		return True

	def CancelInputPrice(self):
		if app.ENABLE_INVENTORY_SLOT_MARKING and self.priceInputBoard:
			itemInvenPage = self.priceInputBoard.sourceSlotPos / player.INVENTORY_PAGE_SIZE
			itemSlotPos = self.priceInputBoard.sourceSlotPos - (itemInvenPage * player.INVENTORY_PAGE_SIZE)
			if self.wndInventory.GetInventoryPageIndex() == itemInvenPage:
				self.wndInventory.wndItem.SetCanMouseEventSlot(itemSlotPos)

			self.lockedItems[self.priceInputBoard.targetSlotPos] = (-1, -1)

		self.priceInputBoard = None
		return True

	def OnOk(self):

		if not self.title:
			return

		if 0 == len(self.itemStock):
			return

		shop.BuildPrivateShop(self.title)
		self.Close()

	def OnClose(self):
		self.Close()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnOverInItem(self, slotIndex):

		if self.tooltipItem:
			if self.itemStock.has_key(slotIndex):
				self.tooltipItem.SetPrivateShopBuilderItem(*self.itemStock[slotIndex] + (slotIndex,))

	def OnOverOutItem(self):

		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	if app.ENABLE_INVENTORY_SLOT_MARKING:
		def CantTradableItem(self, destSlotIndex, srcSlotIndex):
			itemInvenPage = srcSlotIndex / player.INVENTORY_PAGE_SIZE
			localSlotPos = srcSlotIndex - (itemInvenPage * player.INVENTORY_PAGE_SIZE)
			self.lockedItems[destSlotIndex] = (itemInvenPage, localSlotPos)
			if self.wndInventory.GetInventoryPageIndex() == itemInvenPage:
				self.wndInventory.wndItem.SetCantMouseEventSlot(localSlotPos)

		def RefreshLockedSlot(self):
			if self.wndInventory:
				for privatePos, (itemInvenPage, itemSlotPos) in self.lockedItems.items():
					if self.wndInventory.GetInventoryPageIndex() == itemInvenPage:
						self.wndInventory.wndItem.SetCantMouseEventSlot(itemSlotPos)

				self.wndInventory.wndItem.RefreshSlot()

		def BindInterface(self, interface):
			self.interface = interface

		def OnTop(self):
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_PRIVATE_SHOP)
				self.interface.RefreshMarkInventoryBag()

		def SetInven(self, wndInventory):
			from _weakref import proxy
			self.wndInventory = proxy(wndInventory)
