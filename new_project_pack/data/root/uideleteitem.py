import ui
import player
import mouseModule
import net
import app
import snd
import item
import chat
import uiScriptLocale
import uiCommon
import uiPickMoney
import localeInfo
import constInfo

from grid_delete import Grid

import ui
import player
import mouseModule
import net
import app
import snd
import item
import chat
import uiScriptLocale
import uiCommon
import uiPickMoney
import localeInfo
import constInfo

from grid_delete import Grid

toplamfiyat = 0

class DeleteItem(ui.ScriptWindow):
	def __init__(self):	
		ui.ScriptWindow.__init__(self)
		self.LoadWindow()
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		self.tooltipItem = None
		self.itemDropQuestionDialog = None
		self.DeleteGrid = None
		self.interface = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/DeleteItem.py")
		except:
			import exception
			exception.Abort("OfflineShopBuilderWindow.LoadWindow.LoadObject")
			
		try:
			self.itemSlot = self.GetChild("ItemSlot")
			self.btnOk = self.GetChild("OkButton")
			self.btnSat = self.GetChild("SatButton")
			self.board = self.GetChild("Board")
			self.fiyat = self.GetChild("fiyat")
		except:
			import exception
			exception.Abort("OfflineShopBuilderWindow.LoadWindow.BindObject")
			
		self.btnOk.SetEvent(ui.__mem_func__(self.OnOk))
		self.btnSat.SetEvent(ui.__mem_func__(self.OnSat))
		self.board.SetCloseEvent(ui.__mem_func__(self.OnClose))
		
		self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
	
	def Destroy(self):
		self.ClearDictionary()
		
		self.itemSlot = None
		self.btnOk = None
		self.btnSat = None
		self.board = None
		self.itemDropQuestionDialog = None
		self.DeleteGrid = None

	def BindInterface(self, interface):
		self.interface = interface

	def Open(self):
		self.Temizle()
		self.SetCenterPosition()
		self.Refresh()
		self.DeleteGrid = Grid(width=6, height=10)
		self.Show()

	def Close(self):
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		# Envanterdeki kirmizi overlay'i temizle (F5 sil/sat penceresi kapandi)
		if constInfo.ENABLE_ITEM_DELETE_HIGHLIGHT and self.interface:
			self.interface.RefreshInventory()
		self.Hide()

	def Temizle(self):
		global toplamfiyat
		toplamfiyat = 0
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		self.DeleteGrid = Grid(width=6, height=10)
		self.Refresh()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def __GetSlotSellGold(self, invenType, invenPos):
		itemVNum = player.GetItemIndex(invenType, invenPos)
		if 0 == itemVNum:
			return 0
		item.SelectItem(itemVNum)
		itemCount = player.GetItemCount(invenType, invenPos)
		itemPrice = item.GetISellItemPrice()
		if item.Is1GoldItem():
			if 0 == itemPrice:
				return 0
			itemPrice = itemCount / itemPrice
		else:
			itemPrice = itemPrice * itemCount
		if not app.ENABLE_NO_SELL_PRICE_DIVIDED_BY_5:
			# Seviye 40-59 ekipman /10; seviye 60+ silah /15, diger ekipman /10; gerisi /5
			sellDivisor = 5
			if item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
				itemLevelLimit = 0
				for limitIndex in xrange(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(limitIndex)
					if item.LIMIT_LEVEL == limitType:
						itemLevelLimit = limitValue
						break
				if itemLevelLimit >= 40:
					if item.GetItemType() == item.ITEM_TYPE_WEAPON and itemLevelLimit >= 50:
						sellDivisor = 15
					else:
						sellDivisor = 10
			itemPrice /= sellDivisor
		return itemPrice

	def Refresh(self):
		for i in xrange(60):
			if (not self.itemStock.has_key(i)):
				self.itemSlot.ClearSlot(i)
				continue

			pos = self.itemStock[i]
			itemCount = player.GetItemCount(*pos)
			if (itemCount <= 1):
				itemCount = 0
			self.itemSlot.SetItemSlot(i, player.GetItemIndex(*pos), itemCount)
		self.itemSlot.RefreshSlot()
		# Envanterdeki kirmizi overlay'i guncelle (F5 sil/sat isaretleri)
		if constInfo.ENABLE_ITEM_DELETE_HIGHLIGHT and self.interface:
			self.interface.RefreshInventory()

	def OnSelectEmptySlot(self, selectedSlotPos):

		isAttached = mouseModule.mouseController.isAttached()
		if (isAttached):
			global toplamfiyat
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if app.ENABLE_SPECIAL_STORAGE:
				if player.SLOT_TYPE_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_DRAGON_SOUL_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_UPGRADE_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_BOOK_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_ATTR_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_CHEST_INVENTORY != attachedSlotType:
					return

			if (selectedSlotPos in self.itemStock):
				return

			attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)

			itemVNum = player.GetItemIndex(attachedInvenType, attachedSlotPos)
			item.SelectItem(itemVNum)

			attrSlot = [player.GetItemAttribute(attachedSlotPos, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
			if int(attachedSlotPos) > 180:
				self.uyari2 = uiCommon.PopupDialog()
				self.uyari2.SetText("Giyili itemleri silemezsin.")
				self.uyari2.Open()
				return
			
			(width, height) = item.GetItemSize()
			
			for privatePos, (itemWindowType, itemSlotIndex) in self.itemStock.items():
				if itemWindowType == attachedInvenType and itemSlotIndex == attachedSlotPos:
					toplamfiyat -= self.__GetSlotSellGold(attachedInvenType, attachedSlotPos)
					del self.itemStock[privatePos]
					del constInfo.ITEM_DELETE_LIST[privatePos]
					self.DeleteGrid.clear(privatePos, width, height)
					break

			available_position = self.DeleteGrid.find_blank(width, height)
			if available_position != -1:
				self.DeleteGrid.put(selectedSlotPos, width, height)

			self.itemStock[selectedSlotPos] = (attachedInvenType, attachedSlotPos)
			constInfo.ITEM_DELETE_LIST[selectedSlotPos] = (attachedInvenType, attachedSlotPos)
			self.Refresh()
			fiyat = self.__GetSlotSellGold(attachedInvenType, attachedSlotPos)
			toplamfiyat += fiyat


	def OnSelectItemSlot(self, selectedSlotPos):
		isAttached = mouseModule.mouseController.isAttached()
		if (isAttached):
			snd.PlaySound("sound/ui/loginfail.wav")
			mouseModule.mouseController.DeattachObject()

		else:
			if (not selectedSlotPos in self.itemStock):
				return

			invenType, invenPos = self.itemStock[selectedSlotPos]
			del self.itemStock[selectedSlotPos]
			del constInfo.ITEM_DELETE_LIST[selectedSlotPos]
			
			itemVNum = player.GetItemIndex(invenType, invenPos)
			item.SelectItem(itemVNum)
			(width, height) = item.GetItemSize()
			fiyat = self.__GetSlotSellGold(invenType, invenPos)
			global toplamfiyat
			toplamfiyat -= fiyat
			self.DeleteGrid.clear(selectedSlotPos, width, height)
			
			self.Refresh()
	def AddItemWithoutMouse(self, inven_type, inven_pos):
		itemID = player.GetItemIndex(inven_type, inven_pos)
		item.SelectItem(itemID)
		
		(width, height) = item.GetItemSize()
		available_position = self.DeleteGrid.find_blank(width, height)
		
		if available_position == -1:
			chat.AppendChat(1,"Yeterli bosluk yok.")
			return
		
		fiyat = self.__GetSlotSellGold(inven_type, inven_pos)
		global toplamfiyat

		
		for privatePos, (itemWindowType, itemSlotIndex) in list(self.itemStock.iteritems()):
			if itemWindowType == inven_type and itemSlotIndex == inven_pos:
				del self.itemStock[privatePos]
				del constInfo.ITEM_DELETE_LIST[privatePos]
				self.DeleteGrid.clear(privatePos, width, height)

				toplamfiyat -= self.__GetSlotSellGold(inven_type, inven_pos)
		if available_position != -1:
			self.DeleteGrid.put(available_position, width, height)
			self.itemStock[available_position] = (inven_type, inven_pos)
			constInfo.ITEM_DELETE_LIST[available_position] = (inven_type, inven_pos)
			self.Refresh()
			
		toplamfiyat += fiyat

			
	def OnOk(self):
		if (len(self.itemStock) == 0):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Silinecek nesne yok.")
			return

		itemDropQuestionDialog = uiCommon.QuestionDialog()
		itemDropQuestionDialog.SetText("Secilen (|cffFDD017|h%d Adet|h|r) nesneyi silmek istiyor musun?" % (len(self.itemStock)))
		itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestDropItem(arg))
		itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestDropItem(arg))
		itemDropQuestionDialog.Open()
		self.itemDropQuestionDialog = itemDropQuestionDialog

	def OnSat(self):
		if (len(self.itemStock) == 0):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Satilacak nesne yok.")
			return

		itemDropQuestionDialog = uiCommon.QuestionDialog()
		itemDropQuestionDialog.SetText("Secilen (|cffFDD017|h%d Adet|h|r) nesneyi satmak istiyor musun?" % (len(self.itemStock)))
		itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestSellItem(arg))
		itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestSellItem(arg))
		itemDropQuestionDialog.Open()
		self.itemDropQuestionDialog = itemDropQuestionDialog

	def Sil(self):
		global toplamfiyat
		for privatePos, (itemWindowType, itemSlotIndex) in list(self.itemStock.iteritems()):
			net.SendItemDeletePacket(itemSlotIndex, itemWindowType)
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		self.DeleteGrid = Grid(width=6, height=10)
		toplamfiyat = 0
		self.Refresh()

	def Sat(self):
		global toplamfiyat
		for privatePos, (itemWindowType, itemSlotIndex) in list(self.itemStock.iteritems()):
			net.SendItemSellPacket(itemSlotIndex, itemWindowType)
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		self.DeleteGrid = Grid(width=6, height=10)
		toplamfiyat = 0
		self.Refresh()

	def RequestDropItem(self, answer):
		if not self.itemDropQuestionDialog:
			return

		if answer:
			self.Sil()

		self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None

	def RequestSellItem(self, answer):
		if not self.itemDropQuestionDialog:
			return

		if answer:
			self.Sat()

		self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None

	def OnUpdate(self):
		global toplamfiyat
		self.fiyat.SetText("%s" % localeInfo.NumberToMoneyString(toplamfiyat))

	def OnClose(self):
		global toplamfiyat
		toplamfiyat = 0
		self.Close()
		
	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnOverInItem(self, slotIndex):
		if (self.tooltipItem):
			if (self.itemStock.has_key(slotIndex)):
				self.tooltipItem.SetDeleteItem(*self.itemStock[slotIndex] + (slotIndex,))

	def OnOverOutItem(self):
		if (self.tooltipItem):
			self.tooltipItem.HideToolTip()


toplamfiyat = 0

class DeleteItem(ui.ScriptWindow):
	def __init__(self):	
		ui.ScriptWindow.__init__(self)
		self.LoadWindow()
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		self.tooltipItem = None
		self.itemDropQuestionDialog = None
		self.DeleteGrid = None
		self.interface = None
		self.addAttrWarningDialog = None
		self.pendingAddItem = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/DeleteItem.py")
		except:
			import exception
			exception.Abort("OfflineShopBuilderWindow.LoadWindow.LoadObject")
			
		try:
			self.itemSlot = self.GetChild("ItemSlot")
			self.btnOk = self.GetChild("OkButton")
			self.btnSat = self.GetChild("SatButton")
			self.board = self.GetChild("Board")
			self.fiyat = self.GetChild("fiyat")
		except:
			import exception
			exception.Abort("OfflineShopBuilderWindow.LoadWindow.BindObject")
			
		self.btnOk.SetEvent(ui.__mem_func__(self.OnOk))
		self.btnSat.SetEvent(ui.__mem_func__(self.OnSat))
		self.board.SetCloseEvent(ui.__mem_func__(self.OnClose))
		
		self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
	
	def Destroy(self):
		self.ClearDictionary()
		
		self.itemSlot = None
		self.btnOk = None
		self.btnSat = None
		self.board = None
		self.itemDropQuestionDialog = None
		self.DeleteGrid = None
		self.addAttrWarningDialog = None
		self.pendingAddItem = None

	def BindInterface(self, interface):
		self.interface = interface

	def Open(self):
		self.Temizle()
		self.SetCenterPosition()
		self.Refresh()
		self.DeleteGrid = Grid(width=6, height=10)
		self.Show()

	def Close(self):
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		# Envanterdeki kirmizi overlay'i temizle (F5 sil/sat penceresi kapandi)
		if constInfo.ENABLE_ITEM_DELETE_HIGHLIGHT and self.interface:
			self.interface.RefreshInventory()
		# Acik efsun uyarisi varsa kapat (pencere kapaniyor)
		if self.addAttrWarningDialog:
			self.addAttrWarningDialog.Close()
			self.addAttrWarningDialog = None
		self.pendingAddItem = None
		self.Hide()

	def Temizle(self):
		global toplamfiyat
		toplamfiyat = 0
		self.itemStock = {}
		constInfo.ITEM_DELETE_LIST = {}
		self.DeleteGrid = Grid(width=6, height=10)
		self.Refresh()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def __GetSlotSellGold(self, invenType, invenPos):
		itemVNum = player.GetItemIndex(invenType, invenPos)
		if 0 == itemVNum:
			return 0
		item.SelectItem(itemVNum)
		itemCount = player.GetItemCount(invenType, invenPos)
		itemPrice = item.GetISellItemPrice()
		if item.Is1GoldItem():
			if 0 == itemPrice:
				return 0
			itemPrice = itemCount / itemPrice
		else:
			itemPrice = itemPrice * itemCount
		if not app.ENABLE_NO_SELL_PRICE_DIVIDED_BY_5:
			# Seviye 40-59 ekipman /10; seviye 60+ silah /15, diger ekipman /10; gerisi /5
			sellDivisor = 5
			if item.GetItemType() in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR):
				itemLevelLimit = 0
				for limitIndex in xrange(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(limitIndex)
					if item.LIMIT_LEVEL == limitType:
						itemLevelLimit = limitValue
						break
				if itemLevelLimit >= 40:
					if item.GetItemType() == item.ITEM_TYPE_WEAPON and itemLevelLimit >= 50:
						sellDivisor = 15
					else:
						sellDivisor = 10
			itemPrice /= sellDivisor
		return itemPrice

	def Refresh(self):
		for i in xrange(60):
			if (not self.itemStock.has_key(i)):
				self.itemSlot.ClearSlot(i)
				continue

			pos = self.itemStock[i]
			itemCount = player.GetItemCount(*pos)
			if (itemCount <= 1):
				itemCount = 0
			self.itemSlot.SetItemSlot(i, player.GetItemIndex(*pos), itemCount)
		self.itemSlot.RefreshSlot()
		# Envanterdeki kirmizi overlay'i guncelle (F5 sil/sat isaretleri)
		if constInfo.ENABLE_ITEM_DELETE_HIGHLIGHT and self.interface:
			self.interface.RefreshInventory()

	def OnSelectEmptySlot(self, selectedSlotPos):

		isAttached = mouseModule.mouseController.isAttached()
		if (isAttached):
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()

			if app.ENABLE_SPECIAL_STORAGE:
				if player.SLOT_TYPE_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_DRAGON_SOUL_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_UPGRADE_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_BOOK_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_STONE_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_ATTR_INVENTORY != attachedSlotType and \
					player.SLOT_TYPE_CHEST_INVENTORY != attachedSlotType:
					return

			if (selectedSlotPos in self.itemStock):
				return

			attachedInvenType = player.SlotTypeToInvenType(attachedSlotType)

			itemVNum = player.GetItemIndex(attachedInvenType, attachedSlotPos)
			item.SelectItem(itemVNum)

			attrSlot = [player.GetItemAttribute(attachedSlotPos, i) for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]
			if int(attachedSlotPos) > 180:
				self.uyari2 = uiCommon.PopupDialog()
				self.uyari2.SetText("Giyili itemleri silemezsin.")
				self.uyari2.Open()
				return
			
			# Efsun uyarisi artik EKLEME aninda: esikten fazla efsunlu nesne once kirmizi onaydan gecer
			attrCount = self.__GetItemAttrCount(attachedInvenType, attachedSlotPos)
			if attrCount > constInfo.ITEM_DELETE_ATTR_WARNING_THRESHOLD:
				self.__OpenAddAttrWarning(selectedSlotPos, attachedInvenType, attachedSlotPos, attrCount)
				return

			self.__AddStagedItem(selectedSlotPos, attachedInvenType, attachedSlotPos)


	def OnSelectItemSlot(self, selectedSlotPos):
		isAttached = mouseModule.mouseController.isAttached()
		if (isAttached):
			snd.PlaySound("sound/ui/loginfail.wav")
			mouseModule.mouseController.DeattachObject()

		else:
			if (not selectedSlotPos in self.itemStock):
				return

			invenType, invenPos = self.itemStock[selectedSlotPos]
			del self.itemStock[selectedSlotPos]
			del constInfo.ITEM_DELETE_LIST[selectedSlotPos]
			
			itemVNum = player.GetItemIndex(invenType, invenPos)
			item.SelectItem(itemVNum)
			(width, height) = item.GetItemSize()
			fiyat = self.__GetSlotSellGold(invenType, invenPos)
			global toplamfiyat
			toplamfiyat -= fiyat
			self.DeleteGrid.clear(selectedSlotPos, width, height)
			
			self.Refresh()
	def AddItemWithoutMouse(self, inven_type, inven_pos):
		# Efsun uyarisi artik EKLEME aninda (cift-tik / fare olmadan ekleme yolu)
		attrCount = self.__GetItemAttrCount(inven_type, inven_pos)
		if attrCount > constInfo.ITEM_DELETE_ATTR_WARNING_THRESHOLD:
			self.__OpenAddAttrWarning(None, inven_type, inven_pos, attrCount)
			return
		self.__AddStagedItemAuto(inven_type, inven_pos)

	def __AddStagedItemAuto(self, inven_type, inven_pos):
		# Bos hucre otomatik secilerek ekleme (eski AddItemWithoutMouse govdesi)
		global toplamfiyat
		itemID = player.GetItemIndex(inven_type, inven_pos)
		if 0 == itemID:
			return
		item.SelectItem(itemID)

		(width, height) = item.GetItemSize()
		available_position = self.DeleteGrid.find_blank(width, height)

		if available_position == -1:
			chat.AppendChat(1,"Yeterli bosluk yok.")
			return

		fiyat = self.__GetSlotSellGold(inven_type, inven_pos)

		for privatePos, (itemWindowType, itemSlotIndex) in self.itemStock.items():
			if itemWindowType == inven_type and itemSlotIndex == inven_pos:
				del self.itemStock[privatePos]
				del constInfo.ITEM_DELETE_LIST[privatePos]
				self.DeleteGrid.clear(privatePos, width, height)
				toplamfiyat -= self.__GetSlotSellGold(inven_type, inven_pos)

		self.DeleteGrid.put(available_position, width, height)
		self.itemStock[available_position] = (inven_type, inven_pos)
		constInfo.ITEM_DELETE_LIST[available_position] = (inven_type, inven_pos)
		self.Refresh()
		toplamfiyat += fiyat

	def __AddStagedItem(self, selectedSlotPos, attachedInvenType, attachedSlotPos):
		# Kullanicinin biraktigi hucreye ekleme (eski OnSelectEmptySlot kuyrugu)
		global toplamfiyat
		if (selectedSlotPos in self.itemStock):
			return

		itemVNum = player.GetItemIndex(attachedInvenType, attachedSlotPos)
		if 0 == itemVNum:
			return
		item.SelectItem(itemVNum)

		(width, height) = item.GetItemSize()

		for privatePos, (itemWindowType, itemSlotIndex) in self.itemStock.items():
			if itemWindowType == attachedInvenType and itemSlotIndex == attachedSlotPos:
				toplamfiyat -= self.__GetSlotSellGold(attachedInvenType, attachedSlotPos)
				del self.itemStock[privatePos]
				del constInfo.ITEM_DELETE_LIST[privatePos]
				self.DeleteGrid.clear(privatePos, width, height)
				break

		available_position = self.DeleteGrid.find_blank(width, height)
		if available_position != -1:
			self.DeleteGrid.put(selectedSlotPos, width, height)

		self.itemStock[selectedSlotPos] = (attachedInvenType, attachedSlotPos)
		constInfo.ITEM_DELETE_LIST[selectedSlotPos] = (attachedInvenType, attachedSlotPos)
		self.Refresh()
		fiyat = self.__GetSlotSellGold(attachedInvenType, attachedSlotPos)
		toplamfiyat += fiyat

			
	def __GetItemAttrCount(self, invenType, invenPos):
		# Nesnenin dolu efsun (attribute) sayisi; ozellik kapaliysa 0 doner
		if not constInfo.ENABLE_ITEM_DELETE_ATTR_WARNING:
			return 0
		attrCount = 0
		for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM):
			(attrType, attrValue) = player.GetItemAttribute(invenType, invenPos, i)
			if 0 != attrType:
				attrCount += 1
		return attrCount

	def __OpenAddAttrWarning(self, targetSlotPos, invenType, invenPos, attrCount):
		# Efsunlu nesne pencereye EKLENIRKEN cikan kirmizi onay (silme onayindan buraya tasindi)
		if self.addAttrWarningDialog:
			self.addAttrWarningDialog.Close()
		dlg = uiCommon.QuestionDialog2()
		dlg.SetText1("|cffFF3333|hDIKKAT!|h|r Bu nesnede |cffFDD017|h%d|h|r efsun var!" % attrCount)
		dlg.SetText2("Yine de sil/sat penceresine eklemek istiyor musun?")
		dlg.SetWidth(420)
		dlg.SetAcceptEvent(lambda arg=True: self.__AnswerAddAttrWarning(arg))
		dlg.SetCancelEvent(lambda arg=False: self.__AnswerAddAttrWarning(arg))
		dlg.Open()
		self.addAttrWarningDialog = dlg
		self.pendingAddItem = (targetSlotPos, invenType, invenPos)

	def __AnswerAddAttrWarning(self, answer):
		dlg = self.addAttrWarningDialog
		pending = self.pendingAddItem
		self.addAttrWarningDialog = None
		self.pendingAddItem = None
		if dlg:
			dlg.Close()
		if not answer:
			return
		if not pending:
			return
		(targetSlotPos, invenType, invenPos) = pending
		if targetSlotPos is None:
			self.__AddStagedItemAuto(invenType, invenPos)
		else:
			self.__AddStagedItem(targetSlotPos, invenType, invenPos)

	def OnOk(self):
		if (len(self.itemStock) == 0):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Silinecek nesne yok.")
			return

		itemDropQuestionDialog = uiCommon.QuestionDialog()
		itemDropQuestionDialog.SetText("Secilen (|cffFDD017|h%d Adet|h|r) nesneyi silmek istiyor musun?" % (len(self.itemStock)))
		itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestDropItem(arg))
		itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestDropItem(arg))
		itemDropQuestionDialog.Open()
		self.itemDropQuestionDialog = itemDropQuestionDialog

	def OnSat(self):
		if (len(self.itemStock) == 0):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Satilacak nesne yok.")
			return

		itemDropQuestionDialog = uiCommon.QuestionDialog()
		itemDropQuestionDialog.SetText("Secilen (|cffFDD017|h%d Adet|h|r) nesneyi satmak istiyor musun?" % (len(self.itemStock)))
		itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestSellItem(arg))
		itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestSellItem(arg))
		itemDropQuestionDialog.Open()
		self.itemDropQuestionDialog = itemDropQuestionDialog

	def Sil(self):
		for privatePos, (itemWindowType, itemSlotIndex) in self.itemStock.items():

			net.SendItemDeletePacket(itemSlotIndex, itemWindowType)
			del self.itemStock[privatePos]
			del constInfo.ITEM_DELETE_LIST[privatePos]

			self.DeleteGrid = Grid(width=6, height=10)

			global toplamfiyat
			toplamfiyat = 0
			
			self.Refresh()

	def Sat(self):
		for privatePos, (itemWindowType, itemSlotIndex) in self.itemStock.items():

			net.SendItemSellPacket(itemSlotIndex, itemWindowType)
			del self.itemStock[privatePos]
			del constInfo.ITEM_DELETE_LIST[privatePos]
			
			global toplamfiyat
			toplamfiyat = 0
			
			self.DeleteGrid = Grid(width=6, height=10)
			
			self.Refresh()

	def RequestDropItem(self, answer):
		if not self.itemDropQuestionDialog:
			return

		if answer:
			self.Sil()

		self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None

	def RequestSellItem(self, answer):
		if not self.itemDropQuestionDialog:
			return

		if answer:
			self.Sat()

		self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None

	def OnUpdate(self):
		global toplamfiyat
		self.fiyat.SetText("%s" % localeInfo.NumberToMoneyString(toplamfiyat))

	def OnClose(self):
		global toplamfiyat
		toplamfiyat = 0
		self.Close()
		
	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnOverInItem(self, slotIndex):
		if (self.tooltipItem):
			if (self.itemStock.has_key(slotIndex)):
				self.tooltipItem.SetDeleteItem(*self.itemStock[slotIndex] + (slotIndex,))

	def OnOverOutItem(self):
		if (self.tooltipItem):
			self.tooltipItem.HideToolTip()
