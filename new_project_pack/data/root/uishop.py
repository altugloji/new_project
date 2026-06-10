import net
import player
import item
import snd
import shop
import net
import wndMgr
import app
import chat

import ui
import uiCommon
import mouseModule
import localeInfo
import constInfo
from _weakref import proxy

###################################################################################################
## Shop
class ShopDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = 0
		self.xShopStart = 0
		self.yShopStart = 0
		self.questionDialog = None
		self.popup = None
		self.itemBuyQuestionDialog = None
		if app.ENABLE_OFFLINE_SHOP:
			self.interface = None
			self.btnEdit = None
			self.editMode = False
			self.shopVID = 0
			self.editAdded = {}			# display_pos -> {invType, invPos, vnum, count, price}
			self.editRemoved = []		# display_pos listesi (orijinal item'lar)
			self.editPriceUpdated = {}	# display_pos -> yeni fiyat (var olan item'ler)
			self.editPriceDialog = None
			self.editRemoveDialog = None
			self.editRemovePos = -1
			constInfo.OFFLINE_SHOP_EDITING = 0

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __GetRealIndex(self, i):
		return self.tabIdx * shop.SHOP_SLOT_COUNT + i

	def Refresh(self):
		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			self.__RefreshEdit()
			return

		getItemID=shop.GetItemID
		getItemCount=shop.GetItemCount
		setItemID=self.itemSlotWindow.SetItemSlot
		for i in xrange(shop.SHOP_SLOT_COUNT):
			idx = self.__GetRealIndex(i)
			itemCount = getItemCount(idx)
			if itemCount <= 1:
				itemCount = 0
			setItemID(i, getItemID(idx), itemCount)

		wndMgr.RefreshSlot(self.itemSlotWindow.GetWindowHandle())

	def SetItemData(self, pos, itemID, itemCount, itemPrice):
		shop.SetItemData(pos, itemID, itemCount, itemPrice)

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/shopdialog.py")
		except:
			import exception
			exception.Abort("ShopDialog.LoadDialog.LoadObject")

		smallTab1 = None
		smallTab2 = None
		smallTab3 = None
		middleTab1 = None
		middleTab2 = None

		try:
			GetObject = self.GetChild
			self.board = GetObject("board")
			self.itemSlotWindow = GetObject("ItemSlot")
			self.btnBuy = GetObject("BuyButton")
			self.btnSell = GetObject("SellButton")
			self.btnClose = GetObject("CloseButton")
			self.titleBar = GetObject("TitleBar")
			middleTab1 = GetObject("MiddleTab1")
			middleTab2 = GetObject("MiddleTab2")
			smallTab1 = GetObject("SmallTab1")
			smallTab2 = GetObject("SmallTab2")
			smallTab3 = GetObject("SmallTab3")
		except:
			import exception
			exception.Abort("ShopDialog.LoadDialog.BindObject")

		self.itemSlotWindow.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
		self.itemSlotWindow.SAFE_SetButtonEvent("LEFT", "EMPTY", self.SelectEmptySlot)
		self.itemSlotWindow.SAFE_SetButtonEvent("LEFT", "EXIST", self.SelectItemSlot)
		self.itemSlotWindow.SAFE_SetButtonEvent("RIGHT", "EXIST", self.UnselectItemSlot)

		self.itemSlotWindow.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.itemSlotWindow.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))

		self.btnBuy.SetToggleUpEvent(ui.__mem_func__(self.CancelShopping))
		self.btnBuy.SetToggleDownEvent(ui.__mem_func__(self.OnBuy))

		self.btnSell.SetToggleUpEvent(ui.__mem_func__(self.CancelShopping))
		self.btnSell.SetToggleDownEvent(ui.__mem_func__(self.OnSell))

		self.btnClose.SetEvent(ui.__mem_func__(self.AskClosePrivateShop))

		if app.ENABLE_OFFLINE_SHOP:
			try:
				self.btnEdit = GetObject("EditButton")
				self.btnEdit.SetEvent(ui.__mem_func__(self.__OnClickEditButton))
				self.btnEdit.Hide()
			except:
				self.btnEdit = None

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

		self.smallRadioButtonGroup = ui.RadioButtonGroup.Create([[smallTab1, lambda argSelf=proxy(self): argSelf.OnClickTabButton(0), None], [smallTab2, lambda argSelf=proxy(self): argSelf.OnClickTabButton(1), None], [smallTab3, lambda argSelf=proxy(self): argSelf.OnClickTabButton(2), None]])
		self.middleRadioButtonGroup = ui.RadioButtonGroup.Create([[middleTab1, lambda argSelf=proxy(self): argSelf.OnClickTabButton(0), None], [middleTab2, lambda argSelf=proxy(self): argSelf.OnClickTabButton(1), None]])

		self.__HideMiddleTabs()
		self.__HideSmallTabs()

		self.tabIdx = 0
		self.coinType = shop.SHOP_COIN_TYPE_GOLD

		self.Refresh()

	def __ShowBuySellButton(self):
		self.btnBuy.Show()
		self.btnSell.Show()

	def __ShowMiddleTabs(self):
		self.middleRadioButtonGroup.Show()

	def __ShowSmallTabs(self):
		self.smallRadioButtonGroup.Show()

	def __HideBuySellButton(self):
		self.btnBuy.Hide()
		self.btnSell.Hide()

	def __HideMiddleTabs(self):
		if self.middleRadioButtonGroup:
			self.middleRadioButtonGroup.Hide()

	def __HideSmallTabs(self):
		if self.smallRadioButtonGroup:
			self.smallRadioButtonGroup.Hide()

	def __SetTabNames(self):
		if shop.GetTabCount() == 2:
			self.middleRadioButtonGroup.SetText(0, shop.GetTabName(0))
			self.middleRadioButtonGroup.SetText(1, shop.GetTabName(1))
		elif shop.GetTabCount() == 3:
			self.smallRadioButtonGroup.SetText(0, shop.GetTabName(0))
			self.smallRadioButtonGroup.SetText(1, shop.GetTabName(1))
			self.smallRadioButtonGroup.SetText(2, shop.GetTabName(2))

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()

		self.tooltipItem = 0
		self.board = None
		self.itemSlotWindow = 0
		self.btnBuy = 0
		self.btnSell = 0
		self.btnClose = 0
		self.titleBar = 0
		self.questionDialog = None
		self.popup = None
		self.xShopStart = 0
		self.yShopStart = 0
		self.smallRadioButtonGroup = None
		self.middleRadioButtonGroup = None

	def Open(self, vid, isMyShop = 0):
		isPrivateShop = False
		isMainPlayerPrivateShop = False

		import chr
		isOfflineShop = False
		if app.ENABLE_OFFLINE_SHOP and chr.IsOfflineShop(vid):
			isPrivateShop = True
			isOfflineShop = True
		elif chr.IsNPC(vid):
			isPrivateShop = False
		else:
			isPrivateShop = True

		if app.ENABLE_OFFLINE_SHOP:
			self.shopVID = vid
			self.editMode = False
			self.editAdded = {}
			self.editRemoved = []
			self.editPriceUpdated = {}
			self.editRemovePos = -1
			shop.ClearOfflineShopEdit()
			constInfo.OFFLINE_SHOP_EDITING = 0
			constInfo.OFFLINE_SHOP_ADDED_SLOTS = {}
			self.itemSlotWindow.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			showEditButton = False
			if self.btnEdit:
				self.btnEdit.SetText("Dukkani Duzenle")
				# Sadece kendi offline dukkanini duzenleyebilir
				if isMyShop and isOfflineShop:
					self.btnEdit.Show()
					showEditButton = True
				else:
					self.btnEdit.Hide()

		SHOP_DIALOG_HEIGHT_NORMAL = 328
		SHOP_DIALOG_HEIGHT_EDIT   = 356
		h = SHOP_DIALOG_HEIGHT_EDIT if showEditButton else SHOP_DIALOG_HEIGHT_NORMAL
		self.SetSize(184, h)
		if self.board:
			self.board.SetSize(184, h)

		if (app.ENABLE_OFFLINE_SHOP and isMyShop) or player.IsMainCharacterIndex(vid):

			isMainPlayerPrivateShop = True

			self.btnBuy.Hide()
			self.btnSell.Hide()
			self.btnClose.Show()

		else:

			isMainPlayerPrivateShop = False
			self.btnBuy.Show()
			self.btnSell.Show()
			self.btnClose.Hide()
			if app.ENABLE_OFFLINE_SHOP and self.btnEdit:
				self.btnEdit.Hide()

		shop.Open(isPrivateShop, isMainPlayerPrivateShop)

		self.tabIdx = 0

		if isPrivateShop:
			self.__HideMiddleTabs()
			self.__HideSmallTabs()
		else:
			if shop.GetTabCount() == 1:
				self.__ShowBuySellButton()
				self.__HideMiddleTabs()
				self.__HideSmallTabs()
			elif shop.GetTabCount() == 2:
				self.__HideBuySellButton()
				self.__ShowMiddleTabs()
				self.__HideSmallTabs()
				self.__SetTabNames()
				self.middleRadioButtonGroup.OnClick(0)
			elif shop.GetTabCount() == 3:
				self.__HideBuySellButton()
				self.__HideMiddleTabs()
				self.__ShowSmallTabs()
				self.__SetTabNames()
				self.smallRadioButtonGroup.OnClick(0) # @fixme002 (middleRadioButtonGroup(1) -> smallRadioButtonGroup(0))

		self.Refresh()
		self.SetTop()

		self.Show()

		(self.xShopStart, self.yShopStart, z) = player.GetMainCharacterPosition()

	def Close(self):
		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			# Duzenleme modunda kapatma = iptal (son kayitli haline don)
			self.__OnCancelEdit()
		if self.itemBuyQuestionDialog:
			self.itemBuyQuestionDialog.Close()
			self.itemBuyQuestionDialog = None
			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)
		if self.questionDialog:
			self.OnCloseQuestionDialog()
		shop.Close()
		net.SendShopEndPacket()
		self.CancelShopping()
		self.tooltipItem.HideToolTip()
		self.Hide()

	def GetIndexFromSlotPos(self, slotPos):
		return self.tabIdx * shop.SHOP_SLOT_COUNT + slotPos

	def OnClickTabButton(self, idx):
		self.tabIdx = idx
		self.Refresh()

	def AskClosePrivateShop(self):
		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			# Duzenleme modunda Kapat = iptal
			self.__OnCancelEdit()
			self.Close()
			return True
		questionDialog = uiCommon.QuestionDialog()
		questionDialog.SetText(localeInfo.PRIVATE_SHOP_CLOSE_QUESTION)
		questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnClosePrivateShop))
		questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
		questionDialog.Open()
		self.questionDialog = questionDialog

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

		return True

	def OnClosePrivateShop(self):
		net.SendChatPacket("/close_shop")
		self.OnCloseQuestionDialog()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		self.Close()
		return True

	def OnBuy(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_BUY_INFO)
		app.SetCursor(app.BUY)
		self.btnSell.SetUp()

	def OnSell(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_SELL_INFO)
		app.SetCursor(app.SELL)
		self.btnBuy.SetUp()

	def CancelShopping(self):
		self.btnBuy.SetUp()
		self.btnSell.SetUp()
		app.SetCursor(app.NORMAL)

	def __OnClosePopupDialog(self):
		self.pop = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def SellAttachedItem(self):
		if shop.IsPrivateShop():
			mouseModule.mouseController.DeattachObject()
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedCount = mouseModule.mouseController.GetAttachedItemCount()
		attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

		if player.SLOT_TYPE_INVENTORY == attachedSlotType or player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedSlotType:

			item.SelectItem(attachedItemIndex)

			if item.IsAntiFlag(item.ANTIFLAG_SELL):
				popup = uiCommon.PopupDialog()
				popup.SetText(localeInfo.SHOP_CANNOT_SELL_ITEM)
				popup.SetAcceptEvent(self.__OnClosePopupDialog)
				popup.Open()
				self.popup = popup
				return

			itemtype = player.INVENTORY

			if player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedSlotType:
				itemtype = player.DRAGON_SOUL_INVENTORY

			if player.IsValuableItem(itemtype, attachedSlotPos):

				itemPrice = item.GetISellItemPrice()

				if item.Is1GoldItem():
					itemPrice = attachedCount / itemPrice
				else:
					itemPrice = itemPrice * max(1, attachedCount)

				if not app.ENABLE_NO_SELL_PRICE_DIVIDED_BY_5:
					itemPrice /= 5

				itemName = item.GetItemName()

				questionDialog = uiCommon.QuestionDialog()
				questionDialog.SetText(localeInfo.DO_YOU_SELL_ITEM(itemName, attachedCount, itemPrice))

				questionDialog.SetAcceptEvent(lambda arg1=attachedSlotPos, arg2=attachedCount, arg3 = itemtype: self.OnSellItem(arg1, arg2, arg3))
				questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
				questionDialog.Open()
				self.questionDialog = questionDialog

				constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

			else:
				self.OnSellItem(attachedSlotPos, attachedCount, itemtype)

		else:
			snd.PlaySound("sound/ui/loginfail.wav")

		mouseModule.mouseController.DeattachObject()

	def OnSellItem(self, slotPos, count, itemtype):
		net.SendShopSellPacketNew(slotPos, count, itemtype)
		snd.PlaySound("sound/ui/money.wav")
		self.OnCloseQuestionDialog()

	def OnCloseQuestionDialog(self):
		if not self.questionDialog:
			return

		self.questionDialog.Close()
		self.questionDialog = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	if app.ENABLE_OFFLINE_SHOP:
		# ---- Offline dukkan in-window duzenleme ----
		OFFLINE_SHOP_MAX_PRICE = 2000000000		# yang overflow korumasi (GOLD_MAX)

		def __OnClickEditButton(self):
			if self.editMode:
				self.__OnActivateShop()
			else:
				shop.OfflineShopEnter()		# paket ile giris (sunucu dogrular)

		def StartEditMode(self):
			if self.editMode:
				return
			self.editMode = True
			self.editAdded = {}
			self.editRemoved = []
			self.editPriceUpdated = {}
			shop.ClearOfflineShopEdit()
			constInfo.OFFLINE_SHOP_EDITING = 1
			constInfo.OFFLINE_SHOP_ADDED_SLOTS = {}
			# Edit modda slota surukleyince hover/highlight gozuksun (PICK_UP = varsayilan, cursor takipli highlight)
			self.itemSlotWindow.SetSlotStyle(wndMgr.SLOT_STYLE_PICK_UP)
			if self.btnEdit:
				self.btnEdit.SetText("Pazari Aktif Et")
				self.btnEdit.Show()
			self.btnBuy.Hide()
			self.btnSell.Hide()
			self.btnClose.Show()
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Duzenleme modu: sol-tik fiyat, sag-tik kaldir, bos slota surukle ekle.")
			self.Refresh()

		def __ExitEditModeUI(self):
			self.editMode = False
			self.editAdded = {}
			self.editRemoved = []
			self.editPriceUpdated = {}
			shop.ClearOfflineShopEdit()
			# Envanterdeki kirmizi overlay'leri temizle: once EDITING=1 iken bos setle refresh (hepsi deactivate),
			# sonra EDITING=0 + normal refresh (acce/highlight vb. geri gelir)
			constInfo.OFFLINE_SHOP_ADDED_SLOTS = {}
			if self.interface:
				self.interface.RefreshInventory()
			constInfo.OFFLINE_SHOP_EDITING = 0
			if self.interface:
				self.interface.RefreshInventory()
			self.itemSlotWindow.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)
			if self.editPriceDialog:
				self.editPriceDialog.Close()
				self.editPriceDialog = None
			if self.editRemoveDialog:
				self.editRemoveDialog.Close()
				self.editRemoveDialog = None
			if self.btnEdit:
				self.btnEdit.SetText("Dukkani Duzenle")

		def __ComputeEditTotal(self):
			total = 0
			for i in xrange(shop.SHOP_SLOT_COUNT):
				realPos = self.__GetRealIndex(i)
				if realPos in self.editAdded:
					total += self.editAdded[realPos]["price"]
				elif realPos in self.editRemoved:
					continue
				elif shop.GetItemID(realPos) != 0:
					total += self.editPriceUpdated.get(realPos, shop.GetItemPrice(realPos))
			return total

		def __OnActivateShop(self):
			# Pazardaki esyalarin toplam degeri 2 milyar yang'i gecemez
			if self.__ComputeEditTotal() > self.OFFLINE_SHOP_MAX_PRICE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Pazardaki esyalarin toplam degeri 2.000.000.000 yang'i gecemez! Fiyat dusurun veya esya kaldirin.")
				return		# edit modda kal, paket gonderme
			shop.SendOfflineShopEdit()			# APPLY paketi (remove + add + fiyat-guncelleme)
			self.__ExitEditModeUI()
			# Sunucu dukkani yeniden online yapip guest'i dusurur (SHOP_END) -> pencere kapanir

		def __OnCancelEdit(self):
			shop.OfflineShopCancel()			# CANCEL paketi (son kayitli haline don)
			self.__ExitEditModeUI()

		def __RefreshEdit(self):
			for i in xrange(shop.SHOP_SLOT_COUNT):
				realPos = self.__GetRealIndex(i)
				if realPos in self.editAdded:
					a = self.editAdded[realPos]
					cnt = a["count"]
					if cnt <= 1:
						cnt = 0
					self.itemSlotWindow.SetItemSlot(i, a["vnum"], cnt)
				elif realPos in self.editRemoved:
					self.itemSlotWindow.SetItemSlot(i, 0, 0)
				else:
					cnt = shop.GetItemCount(realPos)
					if cnt <= 1:
						cnt = 0
					self.itemSlotWindow.SetItemSlot(i, shop.GetItemID(realPos), cnt)
			wndMgr.RefreshSlot(self.itemSlotWindow.GetWindowHandle())

		# --- Edit modda tooltip: eklenen/fiyati degisen item icin dogru fiyati goster ---
		def __OverInEditItem(self, realPos):
			if realPos in self.editRemoved:
				self.tooltipItem.HideToolTip()
				return
			if realPos in self.editAdded:
				a = self.editAdded[realPos]
				metinSlot = [player.GetItemMetinSocket(a["invType"], a["invPos"], i) for i in xrange(player.METIN_SOCKET_MAX_NUM)]
				attrSlot = [player.GetItemAttribute(a["invType"], a["invPos"], i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
				self.tooltipItem.SetOfflineShopEditItem(a["vnum"], metinSlot, attrSlot, a["price"], a["count"])
				return
			vnum = shop.GetItemID(realPos)
			if vnum == 0:
				self.tooltipItem.HideToolTip()
				return
			metinSlot = [shop.GetItemMetinSocket(realPos, i) for i in xrange(player.METIN_SOCKET_MAX_NUM)]
			attrSlot = [shop.GetItemAttribute(realPos, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
			price = self.editPriceUpdated.get(realPos, shop.GetItemPrice(realPos))
			self.tooltipItem.SetOfflineShopEditItem(vnum, metinSlot, attrSlot, price, shop.GetItemCount(realPos))

		# --- Bos slota surukle: ekle ---
		def __EditAddItem(self, selectedSlotPos):
			if not mouseModule.mouseController.isAttached():
				return
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if player.SLOT_TYPE_INVENTORY != attachedSlotType:
				return

			attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)
			itemVNum = player.GetItemIndex(attachedInvenType, attachedSlotPos)
			if itemVNum == 0:
				return

			import item
			item.SelectItem(itemVNum)
			if item.IsAntiFlag(item.ANTIFLAG_GIVE) or item.IsAntiFlag(item.ANTIFLAG_MYSHOP):
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Bu esya pazara konulamaz.")
				return

			realPos = self.__GetRealIndex(selectedSlotPos)
			if realPos in self.editAdded:
				return
			if (realPos not in self.editRemoved) and shop.GetItemID(realPos) != 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Bu slot dolu. Bos bir slota birakin.")
				return

			self.__OpenPriceDialog("add", realPos, attachedInvenType, attachedSlotPos, itemVNum, player.GetItemCount(attachedInvenType, attachedSlotPos))

		# --- Sol-tik var olan/eklenen iteme: fiyat duzenle ---
		def __EditPriceItem(self, selectedSlotPos):
			realPos = self.__GetRealIndex(selectedSlotPos)
			if realPos in self.editRemoved:
				return
			if realPos in self.editAdded:
				a = self.editAdded[realPos]
				self.__OpenPriceDialog("update_added", realPos, a["invType"], a["invPos"], a["vnum"], a["count"])
			elif shop.GetItemID(realPos) != 0:
				self.__OpenPriceDialog("update_existing", realPos, 0, 0, shop.GetItemID(realPos), shop.GetItemCount(realPos))

		def __OpenPriceDialog(self, mode, realPos, invType, invPos, vnum, count = 1):
			if self.editPriceDialog:
				self.editPriceDialog.Close()
				self.editPriceDialog = None
			priceDialog = uiCommon.MoneyInputDialog()
			priceDialog.SetTitle(localeInfo.PRIVATE_SHOP_INPUT_PRICE_DIALOG_TITLE)
			priceDialog.SetPerUnitCount(count)		# fiyat yazarken adet (tekli) fiyatini canli goster
			priceDialog.SetAcceptEvent(ui.__mem_func__(self.__EditAcceptPrice))
			priceDialog.SetCancelEvent(ui.__mem_func__(self.__EditCancelPrice))
			priceDialog.Open()
			priceDialog.editMode = mode
			priceDialog.itemVNum = vnum
			priceDialog.sourceWindowType = invType
			priceDialog.sourceSlotPos = invPos
			priceDialog.targetSlotPos = realPos
			self.editPriceDialog = priceDialog

		def __EditAcceptPrice(self):
			if not self.editPriceDialog:
				return True
			text = self.editPriceDialog.GetText()
			if not text or not text.isdigit():
				return True
			try:
				price = int(text)
			except:
				return True
			if price <= 0:
				return True
			# Yang overflow korumasi (client)
			if price > self.OFFLINE_SHOP_MAX_PRICE:
				price = self.OFFLINE_SHOP_MAX_PRICE
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Fiyat cok yuksek, ust sinira ayarlandi.")

			mode = self.editPriceDialog.editMode
			invType = self.editPriceDialog.sourceWindowType
			srcPos = self.editPriceDialog.sourceSlotPos
			tgtPos = self.editPriceDialog.targetSlotPos
			vnum = self.editPriceDialog.itemVNum
			self.editPriceDialog = None

			if mode == "update_existing":
				shop.AddOfflineShopPriceUpdate(tgtPos, price)
				self.editPriceUpdated[tgtPos] = price
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Fiyat guncellendi (duzenleme bitince kaydedilecek).")
				return True

			# add veya update_added: stogu (yeniden) ekle
			count = player.GetItemCount(invType, srcPos)
			for dpos, a in self.editAdded.items():
				if a["invType"] == invType and a["invPos"] == srcPos:
					shop.DelPrivateShopItemStock(a["invType"], a["invPos"])
					del self.editAdded[dpos]

			if app.ENABLE_CHEQUE_SYSTEM:
				shop.AddPrivateShopItemStock(invType, srcPos, tgtPos, price, 0)
			else:
				shop.AddPrivateShopItemStock(invType, srcPos, tgtPos, price)

			self.editAdded[tgtPos] = { "invType" : invType, "invPos" : srcPos, "vnum" : vnum, "count" : count, "price" : price }
			# Envanterdeki kaynak slota kirmizi overlay
			constInfo.OFFLINE_SHOP_ADDED_SLOTS[srcPos] = 1
			self.Refresh()
			if self.interface:
				self.interface.RefreshInventory()
			return True

		def __EditCancelPrice(self):
			self.editPriceDialog = None
			return True

		# --- Sag-tik: kaldir (var olanlar icin onay) ---
		def __EditRemoveItem(self, selectedSlotPos):
			realPos = self.__GetRealIndex(selectedSlotPos)
			if realPos in self.editAdded:
				a = self.editAdded[realPos]
				shop.DelPrivateShopItemStock(a["invType"], a["invPos"])
				if a["invPos"] in constInfo.OFFLINE_SHOP_ADDED_SLOTS:
					del constInfo.OFFLINE_SHOP_ADDED_SLOTS[a["invPos"]]
				del self.editAdded[realPos]
				snd.PlaySound("sound/ui/drop.wav")
				self.Refresh()
				if self.interface:
					self.interface.RefreshInventory()
				return
			if shop.GetItemID(realPos) == 0:
				return
			if realPos in self.editRemoved:
				return

			self.editRemovePos = realPos
			if self.editRemoveDialog:
				self.editRemoveDialog.Close()
			questionDialog = uiCommon.QuestionDialog()
			questionDialog.SetText("Bu esyayi pazardan kaldirmak istiyor musunuz?")
			questionDialog.SetAcceptEvent(ui.__mem_func__(self.__EditConfirmRemove))
			questionDialog.SetCancelEvent(ui.__mem_func__(self.__EditCancelRemove))
			questionDialog.Open()
			self.editRemoveDialog = questionDialog

		def __EditConfirmRemove(self):
			realPos = self.editRemovePos
			if realPos >= 0 and (realPos not in self.editRemoved) and shop.GetItemID(realPos) != 0:
				self.editRemoved.append(realPos)
				shop.AddOfflineShopRemove(realPos)
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Bu esya duzenleme bitince envanterine gelecek (envanter doluysa hediye kutusuna).")
				snd.PlaySound("sound/ui/drop.wav")
			self.editRemovePos = -1
			if self.editRemoveDialog:
				self.editRemoveDialog.Close()
				self.editRemoveDialog = None
			self.Refresh()
			return True

		def __EditCancelRemove(self):
			self.editRemovePos = -1
			if self.editRemoveDialog:
				self.editRemoveDialog.Close()
				self.editRemoveDialog = None
			return True

	def SelectEmptySlot(self, selectedSlotPos):
		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			self.__EditAddItem(selectedSlotPos)
			return
		isAttached = mouseModule.mouseController.isAttached()
		if isAttached:
			self.SellAttachedItem()

	def UnselectItemSlot(self, selectedSlotPos):
		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			self.__EditRemoveItem(selectedSlotPos)
			return
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return
		if shop.IsPrivateShop():
			self.AskBuyItem(selectedSlotPos)
		else:
			net.SendShopBuyPacket(self.__GetRealIndex(selectedSlotPos))

	def SelectItemSlot(self, selectedSlotPos):
		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			# Duzenleme modu: bos slota surukle = ekle, dolu slota sol-tik = fiyat duzenle
			if mouseModule.mouseController.isAttached():
				self.__EditAddItem(selectedSlotPos)
			else:
				self.__EditPriceItem(selectedSlotPos)
			return
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		isAttached = mouseModule.mouseController.isAttached()
		selectedSlotPos = self.__GetRealIndex(selectedSlotPos)
		if isAttached:
			self.SellAttachedItem()

		else:
			if True == shop.IsMainPlayerPrivateShop():
				return

			curCursorNum = app.GetCursor()
			if app.BUY == curCursorNum:
				self.AskBuyItem(selectedSlotPos)

			elif app.SELL == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_SELL_INFO)

			else:
				selectedItemID = shop.GetItemID(selectedSlotPos)
				itemCount = shop.GetItemCount(selectedSlotPos)

				type = player.SLOT_TYPE_SHOP
				if shop.IsPrivateShop():
					type = player.SLOT_TYPE_PRIVATE_SHOP

				mouseModule.mouseController.AttachObject(self, type, selectedSlotPos, selectedItemID, itemCount)
				mouseModule.mouseController.SetCallBack("INVENTORY", ui.__mem_func__(self.DropToInventory))
				snd.PlaySound("sound/ui/pick.wav")

	def DropToInventory(self):
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		self.AskBuyItem(attachedSlotPos)

	def AskBuyItem(self, slotPos):
		slotPos = self.__GetRealIndex(slotPos)

		itemIndex = shop.GetItemID(slotPos)
		itemPrice = shop.GetItemPrice(slotPos)
		itemCount = shop.GetItemCount(slotPos)
		if app.ENABLE_CHEQUE_SYSTEM:
			itemCheque = shop.GetItemCheque(slotPos)

		item.SelectItem(itemIndex)
		itemName = item.GetItemName()

		itemBuyQuestionDialog = uiCommon.QuestionDialog()
		if app.ENABLE_MULTISHOP and shop.GetItemGemPrice(slotPos) > 0:
			itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM_GEM(itemName, itemCount, shop.GetItemGemPrice(slotPos)))
		elif app.ENABLE_CHEQUE_SYSTEM:
			if itemCheque > 0 and itemPrice <=0:
				itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM_CHEQUE_SIN_YANG(itemName, itemCount, localeInfo.NumberToCheque(itemCheque)))
			elif itemCheque <= 0 and itemPrice > 0:
				itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToGoldNotText(itemPrice)))
			elif itemCheque > 0 and itemPrice > 0:
				itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM_YANG_CHEQUE(itemName, itemCount, localeInfo.NumberToGoldNotText(itemPrice),localeInfo.NumberToGoldNotText(itemCheque) ))
		else:
			itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToMoneyString(itemPrice)))
		itemBuyQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerBuyItem(arg))
		itemBuyQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerBuyItem(arg))
		itemBuyQuestionDialog.Open()
		itemBuyQuestionDialog.pos = slotPos
		self.itemBuyQuestionDialog = itemBuyQuestionDialog

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def AnswerBuyItem(self, flag):
		if flag:
			pos = self.itemBuyQuestionDialog.pos
			net.SendShopBuyPacket(pos)

		self.itemBuyQuestionDialog.Close()
		self.itemBuyQuestionDialog = None

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def OverInItem(self, slotIndex):
		realPos = self.__GetRealIndex(slotIndex)
		if mouseModule.mouseController.isAttached():
			return

		if 0 == self.tooltipItem:
			return

		if app.ENABLE_OFFLINE_SHOP and self.editMode:
			self.__OverInEditItem(realPos)
			return

		if shop.SHOP_COIN_TYPE_GOLD == shop.GetTabCoinType(self.tabIdx):
			self.tooltipItem.SetShopItem(realPos)
		else:
			self.tooltipItem.SetShopItemBySecondaryCoin(realPos)

	def OverOutItem(self):
		if 0 != self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def OnUpdate(self):
		USE_SHOP_LIMIT_RANGE = 1000

		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xShopStart) > USE_SHOP_LIMIT_RANGE or abs(y - self.yShopStart) > USE_SHOP_LIMIT_RANGE:
			self.Close()


class MallPageDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()

	def Open(self):
		scriptLoader = ui.PythonScriptLoader()
		scriptLoader.LoadScriptFile(self, "uiscript/mallpagedialog.py")

		self.GetChild("titlebar").SetCloseEvent(ui.__mem_func__(self.Close))

		(x, y)=self.GetGlobalPosition()
		x+=10
		y+=30

		MALL_PAGE_WIDTH = 600
		MALL_PAGE_HEIGHT = 480

		app.ShowWebPage(
			"http://metin2.co.kr/08_mall/game_mall/login_fail.htm",
			(x, y, x+MALL_PAGE_WIDTH, y+MALL_PAGE_HEIGHT))

		self.Lock()
		self.Show()

	def Close(self):
		app.HideWebPage()
		self.Unlock()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def AskBuyItem(self, slotPos):
		itemIndex = shop.GetItemID(slotPos)
		itemPrice = shop.GetItemPrice(slotPos)
		itemCount = shop.GetItemCount(slotPos)

		item.SelectItem(itemIndex)
		itemName = item.GetItemName()

		itemBuyQuestionDialog = uiCommon.QuestionDialog()
		if app.ENABLE_MULTISHOP and shop.GetItemGemPrice(slotPos) > 0:
			itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM_GEM(itemName, itemCount, shop.GetItemGemPrice(slotPos)))
		elif app.ENABLE_MULTISHOP:
			if shop.GetBuyWithItem(slotPos) != 0:
				itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToWithItemString(shop.GetBuyWithItemCount(slotPos), item.GetItemName())))
			else:
				itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToMoneyString(itemPrice)))
		else:
			itemBuyQuestionDialog.SetText(localeInfo.DO_YOU_BUY_ITEM(itemName, itemCount, localeInfo.NumberToMoneyString(itemPrice)))
		itemBuyQuestionDialog.SetAcceptEvent(lambda arg=TRUE: self.AnswerBuyItem(arg))
		itemBuyQuestionDialog.SetCancelEvent(lambda arg=FALSE: self.AnswerBuyItem(arg))
		itemBuyQuestionDialog.Open()
		itemBuyQuestionDialog.pos = slotPos
		self.itemBuyQuestionDialog = itemBuyQuestionDialog