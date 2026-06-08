import ui
import net
import player
import mouseModule
import chat
import uiCommon
import localeInfo
import exception

try:
	import safetrade
except ImportError:
	safetrade = None

MODE_CREATE = 0
MODE_CLAIM  = 1

# safetrade.status (ESafeTradeStatus)
STATUS_CREATING       = 0
STATUS_LOCKED         = 1
STATUS_READY_TO_CLAIM = 2


class SafeTradeConfirmDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Load(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/safetradeconfirmdialog.py")
		except:
			exception.Abort("SafeTradeConfirmDialog.__Load")
			return
		line1 = self.GetChild("line1")
		line2 = self.GetChild("line2")
		line3 = self.GetChild("line3")
		line1.SetText(localeInfo.SAFETRADE_CONFIRM_L1)
		line2.SetText(localeInfo.SAFETRADE_CONFIRM_L2)
		line3.SetText(localeInfo.SAFETRADE_CONFIRM_L3)
		line1.SetFontColor(1.0, 0.2, 0.2)   # kirmizi
		line2.SetFontColor(1.0, 0.2, 0.2)   # kirmizi
		line3.SetFontColor(0.2, 1.0, 0.2)   # yesil
		self.acceptButton = self.GetChild("accept")
		self.cancelButton = self.GetChild("cancel")

	def SetAcceptEvent(self, event):
		self.acceptButton.SetEvent(event)

	def SetCancelEvent(self, event):
		self.cancelButton.SetEvent(event)

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


class SafeTradeWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tradeID = 0
		self.mode = MODE_CREATE
		self.isLocked = False
		self.questionDialog = None
		self.tooltipItem = 0
		self.wndItem = None
		self.lockButton = None
		self.confirmButton = None
		self.claimButton = None
		self.closeButton = None
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/safetradewindow.py")
		except:
			exception.Abort("SafeTradeWindow.__LoadWindow.LoadScriptFile")
			return

		try:
			self.GetChild("TitleName").SetText(localeInfo.SAFETRADE_TITLE)
			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.OnClose))

			self.lockButton = self.GetChild("LockButton")
			self.lockButton.SetText(localeInfo.SAFETRADE_LOCK)
			self.lockButton.SetTextColor(0xFF00FF00)   # Kilitle yazisi yesil
			self.lockButton.SetEvent(ui.__mem_func__(self.OnLock))

			self.confirmButton = self.GetChild("ConfirmButton")
			self.confirmButton.SetText(localeInfo.SAFETRADE_CONFIRM)
			self.confirmButton.SetEvent(ui.__mem_func__(self.OnConfirm))

			self.claimButton = self.GetChild("ClaimButton")
			self.claimButton.SetText(localeInfo.SAFETRADE_CLAIM)
			self.claimButton.SetEvent(ui.__mem_func__(self.OnClaim))

			self.closeButton = self.GetChild("CloseButton")
			self.closeButton.SetText(localeInfo.SAFETRADE_CLOSE)
			self.closeButton.SetEvent(ui.__mem_func__(self.OnClose))
		except:
			exception.Abort("SafeTradeWindow.__LoadWindow.GetChild")
			return

		self.wndItem = ui.GridSlotWindow()
		self.wndItem.SetParent(self)
		self.wndItem.SetPosition(13, 38)
		self.wndItem.ArrangeSlot(0, 6, 4, 32, 32, 0, 0)
		self.wndItem.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
		self.wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.wndItem.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
		self.wndItem.Show()
		self.Hide()

	@ui.WindowDestroy
	def Destroy(self):
		self.wndItem = None
		self.lockButton = None
		self.confirmButton = None
		self.claimButton = None
		self.closeButton = None
		self.questionDialog = None

	# ---------- acilis modlari ----------
	def OpenForCreate(self, tradeID):
		self.tradeID = tradeID
		self.mode = MODE_CREATE
		self.isLocked = False
		self.lockButton.Show()
		self.lockButton.Enable()
		self.confirmButton.Hide()
		self.claimButton.Hide()
		self.RefreshItems()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def OpenForClaim(self, tradeID):
		self.tradeID = tradeID
		self.mode = MODE_CLAIM
		self.lockButton.Hide()
		self.confirmButton.Hide()
		self.claimButton.Show()
		self.claimButton.Enable()
		self.RefreshItems()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	# A: kilitli (LOCKED) bir trade'i "Devam Eden Islemlerim"den tekrar acip Son Onay verme
	def OpenForConfirm(self, tradeID):
		self.tradeID = tradeID
		self.mode = MODE_CREATE
		self.isLocked = True
		self.lockButton.Hide()
		self.confirmButton.Show()
		self.confirmButton.Enable()
		self.claimButton.Hide()
		self.RefreshItems()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	# B: kilitli trade'i salt-onizleme (aksiyon butonu yok)
	def OpenForPreview(self, tradeID):
		self.tradeID = tradeID
		self.mode = MODE_CLAIM
		self.isLocked = True
		self.lockButton.Hide()
		self.confirmButton.Hide()
		self.claimButton.Hide()
		self.RefreshItems()
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	# ---------- item yerlestir / cikar (yalniz CREATE + kilitsiz) ----------
	def OnSelectEmptySlot(self, slot):
		if self.mode != MODE_CREATE or self.isLocked:
			return
		if mouseModule.mouseController.isAttached():
			attachedType = mouseModule.mouseController.GetAttachedType()
			attachedSlot = mouseModule.mouseController.GetAttachedSlotNumber()
			if player.SLOT_TYPE_INVENTORY == attachedType:
				net.SendSafeTradeAddItemPacket(player.INVENTORY, attachedSlot, slot)
			mouseModule.mouseController.DeattachObject()

	def OnSelectItemSlot(self, slot):
		if self.mode != MODE_CREATE or self.isLocked:
			return
		net.SendSafeTradeRemoveItemPacket(slot)

	def RefreshItems(self):
		if not safetrade or not self.wndItem:
			return
		for i in xrange(safetrade.SAFE_TRADE_MAX_ITEMS):
			vnum = safetrade.GetDepotItemID(i)
			count = safetrade.GetDepotItemCount(i)
			if count <= 1:
				count = 0
			self.wndItem.SetItemSlot(i, vnum, count)
		self.wndItem.RefreshSlot()

	def ClearItems(self):
		if not self.wndItem:
			return
		maxItems = safetrade.SAFE_TRADE_MAX_ITEMS if safetrade else 24
		for i in xrange(maxItems):
			self.wndItem.SetItemSlot(i, 0, 0)
		self.wndItem.RefreshSlot()

	# Server CLOSE paketi (claim/confirm sonrasi): grid'i temizle + kapat
	def CloseFromServer(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		self.ClearItems()
		self.Hide()

	# ---------- butonlar ----------
	def OnLock(self):
		if self.mode == MODE_CREATE and not self.isLocked:
			net.SendSafeTradeLockPacket()

	def SetStatus(self, status):
		if status == STATUS_LOCKED:
			self.isLocked = True
			self.lockButton.Hide()
			self.confirmButton.Show()
			self.confirmButton.Enable()
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SAFETRADE_LOCKED_MSG)

	def OnConfirm(self):
		if self.mode != MODE_CREATE or not self.isLocked:
			return
		dlg = SafeTradeConfirmDialog()
		dlg.SetAcceptEvent(ui.__mem_func__(self.__DoConfirm))
		dlg.SetCancelEvent(ui.__mem_func__(self.__CloseDialog))
		dlg.Open()
		self.questionDialog = dlg

	def __DoConfirm(self):
		net.SendSafeTradeConfirmPacket(self.tradeID)
		self.__CloseDialog()
		return True

	def __CloseDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		return True

	def OnClaim(self):
		if self.mode == MODE_CLAIM:
			net.SendSafeTradeClaimPacket(self.tradeID)

	def OnClose(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		# Yalniz CREATING (kilitlenmemis) iken iptal/iade. Kilitliyse item'ler havuzda kalir.
		if self.mode == MODE_CREATE and not self.isLocked:
			net.SendSafeTradeCancelPacket()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		self.OnClose()
		return True

	def Close(self):
		self.OnClose()

	# ---------- tooltip ----------
	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def OnOverInItem(self, slot):
		if not self.tooltipItem or not safetrade:
			return
		vnum = safetrade.GetDepotItemID(slot)
		if 0 == vnum:
			return
		self.tooltipItem.ClearToolTip()
		metinSlot = []
		for i in xrange(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(safetrade.GetDepotItemMetinSocket(slot, i))
		attrSlot = []
		for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM):
			attrSlot.append(safetrade.GetDepotItemAttribute(slot, i))
		self.tooltipItem.AddItemData(vnum, metinSlot, attrSlot)
		self.tooltipItem.ShowToolTip()

	def OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
