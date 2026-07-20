import ui
import net
import chat
import player
import app
import localeInfo
import ime
import chr
import wndMgr
import messenger

class WhisperButton(ui.Button):
	def __init__(self):
		ui.Button.__init__(self, "TOP_MOST")

	def __del__(self):
		ui.Button.__del__(self)

	def SetToolTipText(self, text, x=0, y = 32):
		ui.Button.SetToolTipText(self, text, x, y)
		self.ToolTipText.Show()

	def SetToolTipTextWithColor(self, text, color, x=0, y = 32):
		ui.Button.SetToolTipText(self, text, x, y)
		self.ToolTipText.SetPackedFontColor(color)
		self.ToolTipText.Show()

	def ShowToolTip(self):
		if 0 != self.ToolTipText:
			self.ToolTipText.Show()

	def HideToolTip(self):
		if 0 != self.ToolTipText:
			self.ToolTipText.Show()

class WhisperDialog(ui.ScriptWindow):

	class TextRenderer(ui.Window):
		def SetTargetName(self, targetName):
			self.targetName = targetName

		def OnRender(self):
			(x, y) = self.GetGlobalPosition()
			chat.RenderWhisper(self.targetName, x, y)

	class ResizeButton(ui.DragButton):

		def __init__(self):
			ui.DragButton.__init__(self)

		def __del__(self):
			ui.DragButton.__del__(self)

		def OnMouseOverIn(self):
			app.SetCursor(app.HVSIZE)

		def OnMouseOverOut(self):
			app.SetCursor(app.NORMAL)

	def __init__(self, eventMinimize, eventClose):
		print("NEW WHISPER DIALOG  ----------------------------------------------------------------------------")
		ui.ScriptWindow.__init__(self)
		self.targetName = ""
		self.eventMinimize = eventMinimize
		self.eventClose = eventClose
		self.eventAcceptTarget = None
	def __del__(self):
		print("---------------------------------------------------------------------------- DELETE WHISPER DIALOG")
		ui.ScriptWindow.__del__(self)

	def LoadDialog(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/WhisperDialog.py")
		except:
			import exception
			exception.Abort("WhisperDialog.LoadDialog.LoadScript")

		try:
			GetObject=self.GetChild
			self.titleName = GetObject("titlename")
			self.titleNameEdit = GetObject("titlename_edit")
			self.closeButton = GetObject("closebutton")
			self.scrollBar = GetObject("scrollbar")
			self.chatLine = GetObject("chatline")
			self.minimizeButton = GetObject("minimizebutton")
			self.ignoreButton = GetObject("ignorebutton")
			self.reportViolentWhisperButton = GetObject("reportviolentwhisperbutton")
			self.acceptButton = GetObject("acceptbutton")
			self.sendButton = GetObject("sendbutton")
			self.transferButton = GetObject("transferbutton")
			self.board = GetObject("board")
			self.editBar = GetObject("editbar")
			self.gamemasterMark = GetObject("gamemastermark")
		except:
			import exception
			exception.Abort("DialogWindow.LoadDialog.BindObject")

		self.gamemasterMark.Hide()
		self.titleName.SetText("")
		self.titleNameEdit.SetText("")
		self.minimizeButton.SetEvent(ui.__mem_func__(self.Minimize))
		self.closeButton.SetEvent(ui.__mem_func__(self.Close))
		self.scrollBar.SetPos(1.0)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.chatLine.SetReturnEvent(ui.__mem_func__(self.SendWhisper))
		self.chatLine.SetEscapeEvent(ui.__mem_func__(self.Minimize))
		if app.ENABLE_WIKI:
			self.chatLine.OnIMEKeyDown = ui.__mem_func__(self.OnIMEKeyDown)
		self.chatLine.SetMultiLine()
		self.sendButton.SetEvent(ui.__mem_func__(self.SendWhisper))
		self.transferButton.SetText(localeInfo.WHISPER_GM_TRANSFER)
		self.transferButton.SetEvent(ui.__mem_func__(self.__OnClickGmTransfer))
		self.transferButton.Hide()
		self.titleNameEdit.SetReturnEvent(ui.__mem_func__(self.AcceptTarget))
		self.titleNameEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.ignoreButton.SetToggleDownEvent(ui.__mem_func__(self.IgnoreTarget))
		self.ignoreButton.SetToggleUpEvent(ui.__mem_func__(self.IgnoreTarget))
		self.reportViolentWhisperButton.SetEvent(ui.__mem_func__(self.ReportViolentWhisper))
		self.acceptButton.SetEvent(ui.__mem_func__(self.AcceptTarget))

		self.textRenderer = self.TextRenderer()
		self.textRenderer.SetParent(self)
		self.textRenderer.SetPosition(20, 28)
		self.textRenderer.SetTargetName("")
		self.textRenderer.Show()

		self.resizeButton = self.ResizeButton()
		self.resizeButton.SetParent(self)
		self.resizeButton.SetSize(20, 20)
		self.resizeButton.SetPosition(280, 180)
		self.resizeButton.SetMoveEvent(ui.__mem_func__(self.ResizeWhisperDialog))
		self.resizeButton.Show()

		self.ResizeWhisperDialog()

	if app.ENABLE_WIKI:
		def OnIMEKeyDown(self, key):
			if 88 == key and app.IsPressed(app.DIK_LCONTROL):
				interface = constInfo.GetInterfaceInstance()
				if interface:
					result = interface.wndWiki.GetHyperlinkData() if interface.wndWiki else ""
					if result != "":
						ime.PasteString(result)
					return TRUE
			return ui.EditLine.OnIMEKeyDown(self.chatLine, key)

	@ui.WindowDestroy
	def Destroy(self):
		self.eventMinimize = None
		self.eventClose = None
		self.eventAcceptTarget = None

		self.ClearDictionary()
		if self.scrollBar:
			self.scrollBar.Destroy()
		self.titleName = None
		self.titleNameEdit = None
		self.closeButton = None
		self.scrollBar = None
		self.chatLine = None
		self.sendButton = None
		self.ignoreButton = None
		self.reportViolentWhisperButton = None
		self.acceptButton = None
		self.transferButton = None
		self.minimizeButton = None
		self.textRenderer = None
		self.board = None
		self.editBar = None
		self.resizeButton = None

	def ResizeWhisperDialog(self):
		(xPos, yPos) = self.resizeButton.GetLocalPosition()
		if xPos < 280:
			self.resizeButton.SetPosition(280, yPos)
			return
		if yPos < 150:
			self.resizeButton.SetPosition(xPos, 150)
			return
		self.SetWhisperDialogSize(xPos + 20, yPos + 20)

	def SetWhisperDialogSize(self, width, height):
		try:

			max = int((width-90)/6) * 3 - 6

			self.board.SetSize(width, height)
			self.scrollBar.SetPosition(width-25, 35)
			self.scrollBar.SetScrollBarSize(height-100)
			self.scrollBar.SetPos(1.0)
			self.editBar.SetSize(width-18, 50)
			self.chatLine.SetSize(width-90, 40)
			self.chatLine.SetLimitWidth(width-90)
			self.SetSize(width, height)

			if 0 != self.targetName:
				chat.SetWhisperBoxSize(self.targetName, width - 50, height - 90)

			if localeInfo.IsARABIC():
				self.textRenderer.SetPosition(width-20, 28)
				self.scrollBar.SetPosition(width-25+self.scrollBar.GetWidth(), 35)
				self.editBar.SetPosition(10 + self.editBar.GetWidth(), height-60)
				self.transferButton.SetPosition(width - 145 + self.transferButton.GetWidth(), 10)
				self.sendButton.SetPosition(width - 80 + self.sendButton.GetWidth(), 10)
				self.minimizeButton.SetPosition(width-42 + self.minimizeButton.GetWidth(), 12)
				self.closeButton.SetPosition(width-24+self.closeButton.GetWidth(), 12)
				self.chatLine.SetPosition(5 + self.chatLine.GetWidth(), 5)
				self.board.SetPosition(self.board.GetWidth(), 0)
			else:
				self.textRenderer.SetPosition(20, 28)
				self.scrollBar.SetPosition(width-25, 35)
				self.editBar.SetPosition(10, height-60)
				self.transferButton.SetPosition(width - 145, 10)
				self.sendButton.SetPosition(width-80, 10)
				self.minimizeButton.SetPosition(width-42, 12)
				self.closeButton.SetPosition(width-24, 12)

			self.SetChatLineMax(max)

		except:
			import exception
			exception.Abort("WhisperDialog.SetWhisperDialogSize.BindObject")

	def SetChatLineMax(self, max):
		self.chatLine.SetMax(max)

		from grpText import GetSplitingTextLine

		text = self.chatLine.GetText()
		if text:
			self.chatLine.SetText(GetSplitingTextLine(text, max, 0))

	def __RefreshGmTransferButton(self):
		if self.transferButton:
			if chr.IsGameMaster(player.GetMainCharacterIndex()) and self.targetName and self.targetName != 0:
				self.transferButton.Show()
			else:
				self.transferButton.Hide()

	def __OnClickGmTransfer(self):
		if not self.targetName or self.targetName == 0:
			return
		net.SendChatPacket("/warp " + str(self.targetName))

	def OpenWithTarget(self, targetName):
		chat.CreateWhisper(targetName)
		chat.SetWhisperBoxSize(targetName, self.GetWidth() - 60, self.GetHeight() - 90)
		self.chatLine.SetFocus()
		self.titleName.SetText(targetName)
		self.targetName = targetName
		self.textRenderer.SetTargetName(targetName)
		self.titleNameEdit.Hide()
		if app.IsDevStage():
			self.reportViolentWhisperButton.Show()
		else:
			self.reportViolentWhisperButton.Hide()
		# Engelle butonu ayni yuvayi kullanan report butonu (sadece DevStage) acikken gizli kalir
		if app.ENABLE_MESSENGER_BLOCK and not app.IsDevStage():
			self.__RefreshIgnoreButton()
		else:
			self.ignoreButton.Hide()
		self.acceptButton.Hide()
		self.gamemasterMark.Hide()
		self.minimizeButton.Show()
		self.__RefreshGmTransferButton()

	def OpenWithoutTarget(self, event):
		self.eventAcceptTarget = event
		self.titleName.SetText("")
		self.titleNameEdit.SetText("")
		self.titleNameEdit.SetFocus()
		self.targetName = 0
		self.titleNameEdit.Show()
		self.ignoreButton.Hide()
		self.reportViolentWhisperButton.Hide()
		self.acceptButton.Show()
		self.minimizeButton.Hide()
		self.gamemasterMark.Hide()
		if self.transferButton:
			self.transferButton.Hide()

	def SetGameMasterLook(self):
		self.gamemasterMark.Show()
		self.reportViolentWhisperButton.Hide()
		self.__RefreshGmTransferButton()

	def Minimize(self):
		self.titleNameEdit.KillFocus()
		self.chatLine.KillFocus()
		self.Hide()

		if None != self.eventMinimize:
			self.eventMinimize(self.targetName)

	def Close(self):
		chat.ClearWhisper(self.targetName)
		self.titleNameEdit.KillFocus()
		self.chatLine.KillFocus()
		self.Hide()

		if None != self.eventClose:
			self.eventClose(self.targetName)

	def ReportViolentWhisper(self):
		net.SendChatPacket("/reportviolentwhisper " + self.targetName)

	if app.ENABLE_MESSENGER_BLOCK:
		def IgnoreTarget(self):
			# donordeki olu /ignore komutu yerine ENABLE_MESSENGER_BLOCK sistemi (toggle)
			if not self.targetName or self.targetName == 0:
				return
			if messenger.IsBlockByName(self.targetName):
				messenger.RemoveBlock(self.targetName)
				net.SendMessengerRemoveBlockPacket(self.targetName, self.targetName)
			else:
				net.SendMessengerAddBlockByNamePacket(self.targetName)
			self.__RefreshIgnoreButton()

		def __RefreshIgnoreButton(self):
			if not self.ignoreButton:
				return
			if not self.targetName or self.targetName == 0:
				self.ignoreButton.Hide()
				return
			self.ignoreButton.SetUp()
			if messenger.IsBlockByName(self.targetName):
				self.ignoreButton.SetText("Engeli Kaldir")
			else:
				self.ignoreButton.SetText(localeInfo.TARGET_BUTTON_BLOCK)
			self.ignoreButton.Show()
	else:
		def IgnoreTarget(self):
			net.SendChatPacket("/ignore " + self.targetName)

	def AcceptTarget(self):
		name = self.titleNameEdit.GetText()
		if len(name) <= 0:
			self.Close()
			return

		if None != self.eventAcceptTarget:
			self.titleNameEdit.KillFocus()
			self.eventAcceptTarget(name)

	def OnScroll(self):
		chat.SetWhisperPosition(self.targetName, self.scrollBar.GetPos())

	def SendWhisper(self):

		text = self.chatLine.GetText()
		textLength = len(text)

		if textLength > 0:
			if net.IsInsultIn(text):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHAT_INSULT_STRING)
				return

			net.SendWhisperPacket(self.targetName, text)
			self.chatLine.SetText("")

			chat.AppendWhisper(chat.WHISPER_TYPE_CHAT, self.targetName, player.GetName() + " : " + text)

	def OnTop(self):
		self.chatLine.SetFocus()

	def BindInterface(self, interface):
		self.interface = interface

	def OnMouseLeftButtonDown(self):
		hyperlink = ui.GetHyperlink()
		if hyperlink:
			if app.IsPressed(app.DIK_LALT):
				link = chat.GetLinkFromHyperlink(hyperlink)
				ime.PasteString(link)
			else:
				self.interface.MakeHyperlinkTooltip(hyperlink)
		elif app.ENABLE_WHISPER_COPY:
			self.__CopyWhisperLineUnderCursor()

	if app.ENABLE_WHISPER_COPY:
		def __CopyWhisperLineUnderCursor(self):
			# Tiklanan fisilti satirinin metnini panoya kopyala.
			if not self.targetName or self.targetName == 0:
				return
			if not self.textRenderer:
				return

			(gx, gy) = self.textRenderer.GetGlobalPosition()
			(mx, my) = wndMgr.GetMousePosition()

			text = chat.CopyWhisperLineAtPos(self.targetName, gx, gy, mx, my)
			if text:
				chat.AppendChat(chat.CHAT_TYPE_INFO, "Mesaj panoya kopyalandi.")
