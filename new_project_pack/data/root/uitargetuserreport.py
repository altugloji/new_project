import ui
import chat
import net
import uiCommon
import localeInfo
import dbg

class ReportConfirmDialog(ui.Board):
	def __init__(self):
		ui.Board.__init__(self)
		self.SetSize(350, 150)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")

		self.title = ui.TextLine()
		self.title.SetParent(self)
		self.title.SetPosition(self.GetWidth() // 2, 15)
		self.title.SetHorizontalAlignCenter()
		# self.title.SetFontName("Arial:16")
		self.title.SetText(localeInfo.USER_REPORT_SYSTEM_DIALOG_TITLE)
		self.title.Show()

		self.nameLine = ui.TextLine()
		self.nameLine.SetParent(self)
		self.nameLine.SetPosition(self.GetWidth() // 2, 40)
		self.nameLine.SetHorizontalAlignCenter()
		self.nameLine.SetPackedFontColor(0xFFFFFF00)
		self.nameLine.Show()

		self.confirmLine = ui.TextLine()
		self.confirmLine.SetParent(self)
		self.confirmLine.SetPosition(self.GetWidth() // 2, 60)
		self.confirmLine.SetHorizontalAlignCenter()
		self.confirmLine.SetText(localeInfo.USER_REPORT_SYSTEM_DIALOG_REPORT_SURE)
		self.confirmLine.Show()

		self.warningLine = ui.TextLine()
		self.warningLine.SetParent(self)
		self.warningLine.SetPosition(self.GetWidth() // 2, 80)
		self.warningLine.SetHorizontalAlignCenter()
		self.warningLine.SetText(localeInfo.USER_REPORT_SYSTEM_DIALOG_WARN_SANCTIONS)
		self.warningLine.Show()

		self.acceptButton = ui.Button()
		self.acceptButton.SetParent(self)
		self.acceptButton.SetPosition(60, 110)
		self.acceptButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		self.acceptButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		self.acceptButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		self.acceptButton.SetText(localeInfo.UI_ACCEPT)
		self.acceptButton.Show()

		self.cancelButton = ui.Button()
		self.cancelButton.SetParent(self)
		self.cancelButton.SetPosition(180, 110)
		self.cancelButton.SetUpVisual("d:/ymir work/ui/public/middle_button_01.sub")
		self.cancelButton.SetOverVisual("d:/ymir work/ui/public/middle_button_02.sub")
		self.cancelButton.SetDownVisual("d:/ymir work/ui/public/middle_button_03.sub")
		self.cancelButton.SetText(localeInfo.UI_CANCEL)
		self.cancelButton.Show()

	def SetTargetName(self, name):
		self.nameLine.SetText(localeInfo.CHARACTER_NAME + ": " + name)

	def SetAcceptEvent(self, func):
		self.acceptButton.SetEvent(func)

	def SetCancelEvent(self, func):
		self.cancelButton.SetEvent(func)

	def Close(self):
		self.Hide()

class UserReportWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.reason = None
		self.questionDialog = None
		self.popup = None
		self.LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/userreportwindow.py")
		except:
			dbg.TraceError("UserReportWindow.LoadWindow - Failed to load script")
			return

		try:
			self.targetLabel = self.GetChild("target_label")
			self.reasonLabel = self.GetChild("reason_label")
			self.buttonFishBot = self.GetChild("button_fish_bot")
			self.buttonYangSell = self.GetChild("button_yang_sell")
			self.buttonFarmBot = self.GetChild("button_farm_bot")
			self.buttonReklam = self.GetChild("button_reklam")
			self.buttonDiger = self.GetChild("button_diger")
			self.reasonYangSellText = self.GetChild("reason_yang_sell_text")
			self.reasonFarmText = self.GetChild("reason_farm_text")
			self.reasonFishText = self.GetChild("reason_fish_text")
			self.reasonReklamText = self.GetChild("reason_reklam_text")
			self.reasonDigerText = self.GetChild("reason_diger_text")

			self.sendButton = self.GetChild("send_button")
			self.closeButton = self.GetChild("close_button")
			self.nameSlot = self.GetChild("name_slot")
		except:
			dbg.TraceError("UserReportWindow.LoadWindow - Child not found")
			return

		self.buttonYangSell.SetToggleDownEvent(ui.__mem_func__(self.OnSelectYangSell))
		self.buttonYangSell.SetToggleUpEvent(ui.__mem_func__(self.OnUnselectReason))
		self.buttonFarmBot.SetToggleDownEvent(ui.__mem_func__(self.OnSelectFarmBot))
		self.buttonFarmBot.SetToggleUpEvent(ui.__mem_func__(self.OnUnselectReason))
		self.buttonFishBot.SetToggleDownEvent(ui.__mem_func__(self.OnSelectFishBot))
		self.buttonFishBot.SetToggleUpEvent(ui.__mem_func__(self.OnUnselectReason))
		self.buttonReklam.SetToggleDownEvent(ui.__mem_func__(self.OnSelectReklam))
		self.buttonReklam.SetToggleUpEvent(ui.__mem_func__(self.OnUnselectReason))
		self.buttonDiger.SetToggleDownEvent(ui.__mem_func__(self.OnSelectDiger))
		self.buttonDiger.SetToggleUpEvent(ui.__mem_func__(self.OnUnselectReason))

		self.sendButton.SetEvent(ui.__mem_func__(self.OnSend))
		self.closeButton.SetEvent(ui.__mem_func__(self.Close))

		yangSellText = localeInfo.USER_REPORT_SYSTEM_TOOLTIP_YANG_SELL
		farmBotText = localeInfo.USER_REPORT_SYSTEM_TOOLTIP_FARM_BOT
		fishBotText = localeInfo.USER_REPORT_SYSTEM_TOOLTIP_FISH_BOT
		reklamText = localeInfo.USER_REPORT_SYSTEM_TOOLTIP_REKLAM
		digerText = localeInfo.USER_REPORT_SYSTEM_TOOLTIP_DIGER

		self.reasonYangSellText.SetText(yangSellText)
		self.reasonFarmText.SetText(farmBotText)
		self.reasonFishText.SetText(fishBotText)
		self.reasonReklamText.SetText(reklamText)
		self.reasonDigerText.SetText(digerText)

		for textLine in [self.reasonYangSellText, self.reasonFarmText, self.reasonFishText, self.reasonReklamText, self.reasonDigerText]:
			textLine.SetFontName(localeInfo.UI_DEF_FONT)

		self.buttonYangSell.SetToolTipText(yangSellText)
		self.buttonFarmBot.SetToolTipText(farmBotText)
		self.buttonFishBot.SetToolTipText(fishBotText)
		self.buttonReklam.SetToolTipText(reklamText)
		self.buttonDiger.SetToolTipText(digerText)
		self.nameSlot.SetPackedFontColor(0xFFFFFF00)
		self.reason = None

	def SetTargetName(self, name):
		if self.nameSlot:
			self.nameSlot.SetText(name)

	def UnpressAll(self, exceptButton=None):
		for button in [self.buttonYangSell, self.buttonFarmBot, self.buttonFishBot, self.buttonReklam, self.buttonDiger]:
			if button != exceptButton:
				button.SetUp()

	def OnSelectYangSell(self):
		self.UnpressAll(self.buttonYangSell)
		self.reason = "yang_sell"

	def OnSelectFishBot(self):
		self.UnpressAll(self.buttonFishBot)
		self.reason = "fish_bot"

	def OnSelectFarmBot(self):
		self.UnpressAll(self.buttonFarmBot)
		self.reason = "farm_bot"

	def OnSelectReklam(self):
		self.UnpressAll(self.buttonReklam)
		self.reason = "reklam"

	def OnSelectDiger(self):
		self.UnpressAll(self.buttonDiger)
		self.reason = "diger"

	def OnUnselectReason(self):
		self.reason = None

	def OnSend(self):
		if not self.reason:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.USER_REPORT_SYSTEM_FAIL_MESSAGE_NOT_SELECTED)
			return
		self.AskConfirmDialog()

	def AskConfirmDialog(self):
		if self.questionDialog:
			self.questionDialog.Hide()

		self.questionDialog = ReportConfirmDialog()
		if self.nameSlot:
			self.questionDialog.SetTargetName(self.nameSlot.GetText())
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.ConfirmSendReport))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.CancelSendReport))
		self.questionDialog.Show()

	def ConfirmSendReport(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

			name = self.nameSlot.GetText()
			net.SendChatPacket("/report_user {} {}".format(name, self.reason))

			self.popup = uiCommon.PopupDialog()
			self.popup.SetText(localeInfo.USER_REPORT_SYSTEM_MESSAGE_REPORT_SUCCESS)
			self.popup.SetButtonName(localeInfo.UI_OK)
			self.popup.Open()

			self.Close()

	def CancelSendReport(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

	def Open(self):
		self.Show()

	def Close(self):
		self.Hide()

	def Destroy(self):
		self.ClearDictionary()

		self.targetLabel = None
		self.reasonLabel = None
		self.buttonFishBot = None
		self.buttonYangSell = None
		self.buttonFarmBot = None
		self.buttonReklam = None
		self.buttonDiger = None
		self.reasonYangSellText = None
		self.reasonFarmText = None
		self.reasonFishText = None
		self.reasonReklamText = None
		self.reasonDigerText = None
		self.sendButton = None
		self.closeButton = None
		self.nameSlot = None

		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		if self.popup:
			self.popup.Close()
			self.popup = None

	def OnPressEscapeKey(self):
		self.Close()
		return True
