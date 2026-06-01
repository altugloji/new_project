import ui
import grp
import chat
import wndMgr
import net
import app
import ime
import time
import localeInfo
import colorInfo
import constInfo
import systemSetting
import player
from _weakref import proxy
if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
	import uiScriptLocale
	import uiToolTip

ENABLE_CHAT_COMMAND = True
ENABLE_LAST_SENTENCE_STACK = True
ENABLE_INSULT_CHECK = True

if localeInfo.IsHONGKONG():
	ENABLE_LAST_SENTENCE_STACK = True

if localeInfo.IsEUROPE():
	ENABLE_CHAT_COMMAND = False

if localeInfo.IsCANADA():
	ENABLE_LAST_SENTENCE_STACK = False

chatInputSetList = []
def InsertChatInputSetWindow(wnd):
	global chatInputSetList
	chatInputSetList.append(wnd)
def RefreshChatMode():
	global chatInputSetList
	map(lambda wnd:wnd.OnRefreshChatMode(), chatInputSetList)
def DestroyChatInputSetWindow():
	global chatInputSetList
	chatInputSetList = []

## ChatModeButton
class ChatModeButton(ui.Window):

	OUTLINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)
	OVER_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 0.3)
	BUTTON_STATE_UP = 0
	BUTTON_STATE_OVER = 1
	BUTTON_STATE_DOWN = 2

	def __init__(self):
		ui.Window.__init__(self)
		self.state = None
		self.buttonText = None
		self.event = None
		self.SetWindowName("ChatModeButton")

		net.EnableChatInsultFilter(ENABLE_INSULT_CHECK)

	def __del__(self):
		ui.Window.__del__(self)

	def SAFE_SetEvent(self, event):
		self.event=ui.__mem_func__(event)

	def SetText(self, text):
		if None == self.buttonText:
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetWindowHorizontalAlignCenter()
			textLine.SetWindowVerticalAlignCenter()
			textLine.SetVerticalAlignCenter()
			textLine.SetHorizontalAlignCenter()
			textLine.SetPackedFontColor(self.OUTLINE_COLOR)
			textLine.Show()
			self.buttonText = textLine

		self.buttonText.SetText(text)

	def SetSize(self, width, height):
		self.width = width
		self.height = height
		ui.Window.SetSize(self, width, height)

	def OnMouseOverIn(self):
		self.state = self.BUTTON_STATE_OVER

	def OnMouseOverOut(self):
		self.state = self.BUTTON_STATE_UP

	def OnMouseLeftButtonDown(self):
		self.state = self.BUTTON_STATE_DOWN

	def OnMouseLeftButtonUp(self):
		self.state = self.BUTTON_STATE_UP
		if self.IsIn():
			self.state = self.BUTTON_STATE_OVER

		if None != self.event:
			self.event()

	def OnRender(self):
# keep branch order stable [root-on-render:13e99f1deef8]

		(x, y) = self.GetGlobalPosition()

		grp.SetColor(self.OUTLINE_COLOR)
		grp.RenderRoundBox(x, y, self.width, self.height)

		if self.state >= self.BUTTON_STATE_OVER:
			grp.RenderRoundBox(x+1, y, self.width-2, self.height)
			grp.RenderRoundBox(x, y+1, self.width, self.height-2)

			if self.BUTTON_STATE_DOWN == self.state:
				grp.SetColor(self.OVER_COLOR)
				grp.RenderBar(x+1, y+1, self.width-2, self.height-2)

## ChatLine
class ChatLine(ui.EditLine):

	CHAT_MODE_NAME = {	chat.CHAT_TYPE_TALKING : localeInfo.CHAT_NORMAL,
						chat.CHAT_TYPE_PARTY : localeInfo.CHAT_PARTY,
						chat.CHAT_TYPE_GUILD : localeInfo.CHAT_GUILD,
						chat.CHAT_TYPE_SHOUT : localeInfo.CHAT_SHOUT, }

	def __init__(self):
		ui.EditLine.__init__(self)
		self.SetWindowName("Chat Line")
		self.lastShoutTime = 0
		self.eventEscape = lambda *arg: None
		self.eventReturn = lambda *arg: None
		self.eventTab = None
		self.chatMode = chat.CHAT_TYPE_TALKING
		self.bCodePage = True

		self.overTextLine = ui.TextLine()
		self.overTextLine.SetParent(self)
		self.overTextLine.SetPosition(-1, 0)
		self.overTextLine.SetFontColor(1.0, 1.0, 0.0)
		self.overTextLine.SetOutline()
		self.overTextLine.Hide()

		self.lastSentenceStack = []
		self.lastSentencePos = 0

	def SetChatMode(self, mode):
		self.chatMode = mode

	def GetChatMode(self):
		return self.chatMode

	def ChangeChatMode(self):
		if chat.CHAT_TYPE_TALKING == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_PARTY)
			self.SetText("#")
			self.SetEndPosition()

		elif chat.CHAT_TYPE_PARTY == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_GUILD)
			self.SetText("%")
			self.SetEndPosition()

		elif chat.CHAT_TYPE_GUILD == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_SHOUT)
			self.SetText("!")
			self.SetEndPosition()

		elif chat.CHAT_TYPE_SHOUT == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_TALKING)
			self.SetText("")

		self.__CheckChatMark()

	def GetCurrentChatModeName(self):
		try:
			return self.CHAT_MODE_NAME[self.chatMode]
		except:
			import exception
			exception.Abort("ChatLine.GetCurrentChatModeName")

	def SAFE_SetEscapeEvent(self, event):
		self.eventReturn = ui.__mem_func__(event)

	def SAFE_SetReturnEvent(self, event):
		self.eventEscape = ui.__mem_func__(event)

	def SAFE_SetTabEvent(self, event):
		self.eventTab = ui.__mem_func__(event)

	def SetTabEvent(self, event):
		self.eventTab = event

	def OpenChat(self):
		self.SetFocus()
		self.__ResetChat()

	def __ClearChat(self):
		self.SetText("")
		self.lastSentencePos = 0

	def __ResetChat(self):
		if chat.CHAT_TYPE_PARTY == self.GetChatMode():
			self.SetText("#")
			self.SetEndPosition()
		elif chat.CHAT_TYPE_GUILD == self.GetChatMode():
			self.SetText("%")
			self.SetEndPosition()
		elif chat.CHAT_TYPE_SHOUT == self.GetChatMode():
			self.SetText("!")
			self.SetEndPosition()
		else:
			self.__ClearChat()

		self.__CheckChatMark()


	def __SendChatPacket(self, text, type):
# retain fallback path for parity [root-send-chat:f480970ee5f4]
		if net.IsChatInsultIn(text):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHAT_INSULT_STRING)
		else:
			if app.AUTO_CHAT_ENABLE:
				if type == chat.CHAT_TYPE_SHOUT:
					global autoChatLastText
					autoChatLastText = text
					RefreshAutoChat()
			net.SendChatPacket(text, type)

	def __SendPartyChatPacket(self, text):

		if 1 == len(text):
			self.RunCloseEvent()
			return

		self.__SendChatPacket(text[1:], chat.CHAT_TYPE_PARTY)
		self.__ResetChat()

	def __SendGuildChatPacket(self, text):

		if 1 == len(text):
			self.RunCloseEvent()
			return

		self.__SendChatPacket(text[1:], chat.CHAT_TYPE_GUILD)
		self.__ResetChat()

	def __SendShoutChatPacket(self, text):

		if 1 == len(text):
			self.RunCloseEvent()
			return

		if self.lastShoutTime and app.GetTime() < self.lastShoutTime + 15: #@fixme013
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHAT_SHOUT_LIMIT)
			self.__ResetChat()
			return

		self.__SendChatPacket(text[1:], chat.CHAT_TYPE_SHOUT)
		self.__ResetChat()

		self.lastShoutTime = app.GetTime()

	def __SendTalkingChatPacket(self, text):
		self.__SendChatPacket(text, chat.CHAT_TYPE_TALKING)
		self.__ResetChat()

	def OnIMETab(self):
		#if None != self.eventTab:
		#	self.eventTab()
		#return True
		return False

	def OnIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self)
		self.__CheckChatMark()

	def __CheckChatMark(self):

		self.overTextLine.Hide()

		text = self.GetText()
		if len(text) > 0:
			if '#' == text[0]:
				self.overTextLine.SetText("#")
				self.overTextLine.Show()
			elif '%' == text[0]:
				self.overTextLine.SetText("%")
				self.overTextLine.Show()
			elif '!' == text[0]:
				self.overTextLine.SetText("!")
				self.overTextLine.Show()

	def OnIMEKeyDown(self, key):
		# LAST_SENTENCE_STACK
		if app.VK_UP == key:
			self.__PrevLastSentenceStack()
			return True

		if app.VK_DOWN == key:
			self.__NextLastSentenceStack()
			return True
		# END_OF_LAST_SENTENCE_STACK
		
		if app.ENABLE_WIKI:
			if 88 == key and app.IsPressed(app.DIK_LCONTROL):
				result = self.interface.wndWiki.GetHyperlinkData() if self.interface.wndWiki else ""
				if result != "":
					ime.PasteString(result)
				return TRUE

		ui.EditLine.OnIMEKeyDown(self, key)

	# LAST_SENTENCE_STACK
	def __PrevLastSentenceStack(self):
		global ENABLE_LAST_SENTENCE_STACK
		if not ENABLE_LAST_SENTENCE_STACK:
			return

		if self.lastSentenceStack and self.lastSentencePos < len(self.lastSentenceStack):
			self.lastSentencePos += 1
			lastSentence = self.lastSentenceStack[-self.lastSentencePos]
			self.SetText(lastSentence)
			self.SetEndPosition()

	def __NextLastSentenceStack(self):
		global ENABLE_LAST_SENTENCE_STACK
		if not ENABLE_LAST_SENTENCE_STACK:
			return

		if self.lastSentenceStack and self.lastSentencePos > 1:
			self.lastSentencePos -= 1
			lastSentence = self.lastSentenceStack[-self.lastSentencePos]
			self.SetText(lastSentence)
			self.SetEndPosition()

	def __PushLastSentenceStack(self, text):
		global ENABLE_LAST_SENTENCE_STACK
		if not ENABLE_LAST_SENTENCE_STACK:
			return

		if len(text) <= 0:
			return

		LAST_SENTENCE_STACK_SIZE = 32
		if len(self.lastSentenceStack) > LAST_SENTENCE_STACK_SIZE:
			self.lastSentenceStack.pop(0)

		self.lastSentenceStack.append(text)
	# END_OF_LAST_SENTENCE_STACK

	def OnIMEReturn(self):
		text = self.GetText()
		textLen=len(text)

		# LAST_SENTENCE_STACK
		self.__PushLastSentenceStack(text)
		# END_OF_LAST_SENTENCE_STACK

		textSpaceCount=text.count(' ')

		if (textLen > 0) and (textLen != textSpaceCount):
			if '#' == text[0]:
				self.__SendPartyChatPacket(text)
			elif '%' == text[0]:
				self.__SendGuildChatPacket(text)
			elif '!' == text[0]:
				self.__SendShoutChatPacket(text)
			else:
				self.__SendTalkingChatPacket(text)
		else:
			self.__ClearChat()
			self.eventReturn()

		return True

	def OnPressEscapeKey(self):
		self.__ClearChat()
		self.eventEscape()
		return True

	def RunCloseEvent(self):
		self.eventEscape()

	def BindInterface(self, interface):
		self.interface = interface

	def OnMouseLeftButtonDown(self):
		hyperlink = ui.GetHyperlink()
		if app.__BL_MULTI_LANGUAGE_PREMIUM__:
			country = chat.GetCountry()
			empire = chat.GetEmpire()
			if hyperlink:
				if app.IsPressed(app.DIK_LALT):
					link = chat.GetLinkFromHyperlink(hyperlink)
					ime.PasteString(link)
				else:
					self.interface.MakeHyperlinkTooltip(hyperlink)
			elif country:
				self.interface.MakeCountryTooltip(country)
			elif empire:
				self.interface.MakeEmpireTooltip(empire)
			else:
				ui.EditLine.OnMouseLeftButtonDown(self)
		else:
			if hyperlink:
				if app.IsPressed(app.DIK_LALT):
					link = chat.GetLinkFromHyperlink(hyperlink)
					ime.PasteString(link)
				else:
					self.interface.MakeHyperlinkTooltip(hyperlink)
			else:
				ui.EditLine.OnMouseLeftButtonDown(self)

class ChatInputSet(ui.Window):

	CHAT_OUTLINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)

	def __init__(self):
		ui.Window.__init__(self)
		self.SetWindowName("ChatInputSet")

		InsertChatInputSetWindow(self)
		self.__Create()

	def __del__(self):
		ui.Window.__del__(self)

	def __Create(self):
		chatModeButton = ChatModeButton()
		chatModeButton.SetParent(self)
		chatModeButton.SetSize(40, 17)
		chatModeButton.SetText(localeInfo.CHAT_NORMAL)
		chatModeButton.SetPosition(7, 2)
		chatModeButton.SAFE_SetEvent(self.OnChangeChatMode)
		self.chatModeButton = chatModeButton

		chatLine = ChatLine()
		chatLine.SetParent(self)
		chatLine.SetMax(512)
		chatLine.SetUserMax(76)
		chatLine.SetText("")
		chatLine.SAFE_SetTabEvent(self.OnChangeChatMode)
		chatLine.x = 0
		chatLine.y = 0
		chatLine.width = 0
		chatLine.height = 0
		self.chatLine = chatLine

		btnSend = ChatModeButton()
		btnSend.SetParent(self)
		btnSend.SetSize(56, 17)
		btnSend.SetText(getattr(localeInfo, "USER_REPORT_SYSTEM_DIALOG_BUTTON_YES", localeInfo.CHAT_SEND_CHAT))
		btnSend.SAFE_SetEvent(self.chatLine.OnIMEReturn)
		self.btnSend = btnSend

	@ui.WindowDestroy
	def Destroy(self):
		self.chatModeButton = None
		self.chatLine = None
		self.btnSend = None
		self.lastShoutTime = 0

	def Open(self):
		self.chatLine.Show()
		self.chatLine.SetPosition(57, 5)
		self.chatLine.SetFocus()
		self.chatLine.OpenChat()

		self.chatModeButton.SetPosition(7, 2)
		self.chatModeButton.Show()

		self.btnSend.Show()
		self.Show()

		self.RefreshPosition()
		return True

	def Close(self):
		self.chatLine.KillFocus()
		self.chatLine.Hide()
		self.chatModeButton.Hide()
		self.btnSend.Hide()
		self.Hide()
		return True

	def SetEscapeEvent(self, event):
		self.chatLine.SetEscapeEvent(event)

	def SetReturnEvent(self, event):
		self.chatLine.SetReturnEvent(event)

	def OnChangeChatMode(self):
		RefreshChatMode()

	def OnRefreshChatMode(self):
		self.chatLine.ChangeChatMode()
		self.chatModeButton.SetText(self.chatLine.GetCurrentChatModeName())

	def SetChatFocus(self):
		self.chatLine.SetFocus()

	def KillChatFocus(self):
		self.chatLine.KillFocus()

	def SetChatMax(self, max):
		self.chatLine.SetUserMax(max)

	def RefreshPosition(self):
		h = self.GetHeight()
		lineH = 18 if localeInfo.IsARABIC() else 13

		lineY = (h - lineH) // 2
		if lineY < 2:
			lineY = 5

		btnH = max(17, h - 8)
		sendW = 56

		self.chatModeButton.SetSize(40, btnH)
		self.chatModeButton.SetPosition(7, (h - btnH) // 2)

		self.btnSend.SetSize(sendW, btnH)
		self.btnSend.SetPosition(self.GetWidth() - sendW - 6, (h - btnH) // 2)

		self.chatLine.SetPosition(57, lineY)
		self.chatLine.SetSize(self.GetWidth() - 57 - sendW - 16, lineH)

		(self.chatLine.x, self.chatLine.y, self.chatLine.width, self.chatLine.height) = self.chatLine.GetRect()

	def BindInterface(self, interface):
		self.chatLine.BindInterface(interface)

	def OnMouseLeftButtonDown(self):
		self.chatLine.SetFocus()
		return True

	def OnRender(self):
		(x, y, width, height) = self.chatLine.GetRect()
		boxH = self.GetHeight() - 8
		if boxH < height + 4:
			boxH = height + 4
		cy = y + height // 2
		boxTop = cy - boxH // 2
		ui.RenderRoundBox(x - 4, boxTop, width + 7, boxH, self.CHAT_OUTLINE_COLOR)

## ChatWindow
class ChatWindow(ui.Window):

	BOARD_START_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.0)
	BOARD_END_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.8)
	BOARD_MIDDLE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.5)
	CHAT_OUTLINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)
	CHAT_SIZING_HIT_HEIGHT = 20
	CHAT_FLAG_BAR_HEIGHT = 23
	CHAT_FLAG_BAR_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.75)
	CHAT_BAR_GAP_ABOVE = 0
	CHAT_FLAG_BAR_OFFSET_Y = 10
	CHAT_FLAG_STEP = 28
	CHAT_FLAG_LABEL_LEFT = 8
	CHAT_FLAG_LABEL_WIDTH = 95
	CHAT_FLAG_POS_OFFSET_X = -250
	CHAT_FLAG_POS_OFFSET_Y = 2
	CHAT_FLAG_CLOCK_RIGHT_PAD = 8

	EDIT_LINE_HEIGHT = 25
	CHAT_WINDOW_WIDTH = 700
	CHAT_INPUT_RIGHT_RESERVE = 50
	if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
		IMAGE_DISABLE_ALPHA = 0.5
		CHAT_FLAG_HIDDEN_LANGS = ("eu",)

	class ChatBackBoard(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
		def __del__(self):
			ui.Window.__del__(self)

	class ChatButton(ui.DragButton):

		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag("float")
			self.AddFlag("movable")
			self.AddFlag("restrict_x")
			self.topFlag = False
			self.SetWindowName("ChatWindow:ChatButton")


		def __del__(self):
			ui.DragButton.__del__(self)

		def SetOwner(self, owner):
			self.owner = owner

		def OnMouseOverIn(self):
			app.SetCursor(app.VSIZE)

		def OnMouseOverOut(self):
			app.SetCursor(app.NORMAL)

		def OnTop(self):
			if True == self.topFlag:
				return

			self.topFlag = True
			self.owner.SetTop()
			self.topFlag = False

	if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
		class ChatFlagBar(ui.DragButton):
			def __init__(self, owner):
				ui.DragButton.__init__(self)
				self.AddFlag("float")
				self.AddFlag("movable")
				self.AddFlag("restrict_x")
				self.owner = owner
				self.SetWindowName("ChatWindow:ChatFlagBar")
				self.SetMoveEvent(ui.__mem_func__(owner.OnMoveFlagBar))

			def __del__(self):
				ui.DragButton.__del__(self)

			def OnMouseOverIn(self):
				app.SetCursor(app.VSIZE)

			def OnMouseOverOut(self):
				app.SetCursor(app.NORMAL)

			def OnRender(self):
				if not self.IsShow():
					return
				(gx, gy) = self.GetGlobalPosition()
				width = self.GetWidth()
				height = self.GetHeight()
				if width <= 0 or height <= 0:
					return
				grp.SetColor(self.owner.CHAT_FLAG_BAR_COLOR)
				grp.RenderBar(gx, gy, width, height)

	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag("float")

		self.SetWindowName("ChatWindow")
		self.__RegisterChatColorDict()

		self.boardState = chat.BOARD_STATE_VIEW
		self.chatID = chat.CreateChatSet(chat.CHAT_SET_CHAT_WINDOW)
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_VIEW)

		self.xBar = 0
		self.yBar = 0
		self.widthBar = 0
		self.heightBar = 0
		self.curHeightBar = 0
		self.visibleLineCount = 0
		self.scrollBarPos = 1.0
		self.scrollLock = False
		chatInputSet = ChatInputSet()
		chatInputSet.SetParent(self)
		chatInputSet.SetEscapeEvent(ui.__mem_func__(self.CloseChat))
		chatInputSet.SetReturnEvent(ui.__mem_func__(self.CloseChat))
		chatInputSet.SetSize(self.CHAT_WINDOW_WIDTH - self.CHAT_INPUT_RIGHT_RESERVE, self.EDIT_LINE_HEIGHT)
		self.chatInputSet = chatInputSet

		btnSendWhisper = ui.Button()
		btnSendWhisper.SetParent(self)
		btnSendWhisper.SetUpVisual("d:/ymir work/ui/game/taskbar/Send_Whisper_Button_01.sub")
		btnSendWhisper.SetOverVisual("d:/ymir work/ui/game/taskbar/Send_Whisper_Button_02.sub")
		btnSendWhisper.SetDownVisual("d:/ymir work/ui/game/taskbar/Send_Whisper_Button_03.sub")
		btnSendWhisper.SetToolTipText(localeInfo.CHAT_SEND_MEMO)
		btnSendWhisper.Hide()
		self.btnSendWhisper = btnSendWhisper

		self.btnChatLog = None

		btnChatSizing = self.ChatButton()
		btnChatSizing.SetOwner(self)
		btnChatSizing.SetMoveEvent(ui.__mem_func__(self.Refresh))
		btnChatSizing.Hide()
		self.btnChatSizing = btnChatSizing

		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.flag_bar = self.ChatFlagBar(self)
			self.flag_bar.Hide()
			self.lang_image_dict = {}
			self.toolTip = uiToolTip.ToolTip()

			self.flag_bar_title = ui.TextLine()
			self.flag_bar_title.SetParent(self.flag_bar)
			self.flag_bar_title.AddFlag("not_pick")
			self.flag_bar_title.SetPosition(self.CHAT_FLAG_LABEL_LEFT, 5)
			self.flag_bar_title.SetFontName(localeInfo.UI_DEF_FONT)
			# self.flag_bar_title.SetFontName(localeInfo.UI_BOLD_FONT_LARGE)
			self.flag_bar_title.SetPackedFontColor(0xFFFFFFFF)
			self.flag_bar_title.SetOutline()
			self.flag_bar_title.SetText(localeInfo.CHAT_FLAG_BAR_TITLE)
			self.flag_bar_title.Show()

			self.flag_bar_clock = ui.TextLine()
			self.flag_bar_clock.SetParent(self.flag_bar)
			self.flag_bar_clock.AddFlag("not_pick")
			self.flag_bar_clock.SetWindowHorizontalAlignRight()
			self.flag_bar_clock.SetHorizontalAlignRight()
			self.flag_bar_clock.SetPosition(self.CHAT_FLAG_CLOCK_RIGHT_PAD, 5)
			self.flag_bar_clock.SetFontName(localeInfo.UI_DEF_FONT)
			# self.flag_bar_clock.SetFontName(localeInfo.UI_BOLD_FONT_LARGE)
			self.flag_bar_clock.SetPackedFontColor(0xFFFFFFFF)
			self.flag_bar_clock.SetOutline()
			self.flag_bar_clock.Show()

			for lang in sorted(uiScriptLocale.LOCALE_NAME_DICT.iterkeys()):
				if lang in self.CHAT_FLAG_HIDDEN_LANGS:
					continue
				image = ui.ImageBox()
				image.SetParent(self.flag_bar)
				flagPath = "d:/ymir work/flags/server_flag_{}.png".format(lang)
				if not app.IsExistFile(flagPath):
					flagPath = "d:/ymir work/flags/server_flag_tr.png"
				image.LoadImage(flagPath)
				image.SetEvent(ui.__mem_func__(self.__EventCountry), "mouse_click", lang)
				image.SetEvent(ui.__mem_func__(self.__EventCountry), "mouse_over_in", lang)
				image.SetEvent(ui.__mem_func__(self.__EventCountry), "mouse_over_out", 0)
				image.Show()
				self.lang_image_dict[lang] = image

			self.__LayoutFlagBar(self.CHAT_WINDOW_WIDTH)
			self.RefreshChatFilterSettings()

		scrollBar = ui.ScrollBar()
		scrollBar.AddFlag("float")
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar = scrollBar

		if app.AUTO_CHAT_ENABLE:
			autoChatBtn = ui.Button()
			autoChatBtn.SetParent(self)
			autoChatBtn.SetUpVisual("d:/ymir work/ui/chat/bot_0.tga")
			autoChatBtn.SetOverVisual("d:/ymir work/ui/chat/bot_1.tga")
			autoChatBtn.SetDownVisual("d:/ymir work/ui/chat/bot_2.tga")
			autoChatBtn.SetToolTipText(localeInfo.AUTO_CHAT_TITLE)
			autoChatBtn.SetEvent(ui.__mem_func__(self.OpenAutoChat))
			autoChatBtn.Hide()
			self.autoChatBtn = autoChatBtn

		self.Refresh()
		self.chatInputSet.RefreshPosition()

	def __del__(self):
		ui.Window.__del__(self)

	def __RegisterChatColorDict(self):
		CHAT_COLOR_DICT = {
			chat.CHAT_TYPE_TALKING : colorInfo.CHAT_RGB_TALK,
			chat.CHAT_TYPE_INFO : colorInfo.CHAT_RGB_INFO,
			chat.CHAT_TYPE_NOTICE : colorInfo.CHAT_RGB_NOTICE,
			chat.CHAT_TYPE_PARTY : colorInfo.CHAT_RGB_PARTY,
			chat.CHAT_TYPE_GUILD : colorInfo.CHAT_RGB_GUILD,
			chat.CHAT_TYPE_COMMAND : colorInfo.CHAT_RGB_COMMAND,
			chat.CHAT_TYPE_SHOUT : colorInfo.CHAT_RGB_SHOUT,
			chat.CHAT_TYPE_WHISPER : colorInfo.CHAT_RGB_WHISPER,
		}
		if app.ENABLE_DICE_SYSTEM:
			CHAT_COLOR_DICT.update({chat.CHAT_TYPE_DICE_INFO : colorInfo.CHAT_RGB_DICE_INFO,})

		for colorItem in CHAT_COLOR_DICT.items():
			type=colorItem[0]
			rgb=colorItem[1]
			chat.SetChatColor(type, rgb[0], rgb[1], rgb[2])

	@ui.WindowDestroy
	def Destroy(self):
		if self.chatInputSet:
			self.chatInputSet.Destroy()
			self.chatInputSet = None

		self.btnSendWhisper = 0
		self.btnChatLog = 0
		self.btnChatSizing = 0
		
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.flag_bar = None
			self.flag_bar_title = None
			self.flag_bar_clock = None
			self.lang_image_dict = {}
			self.toolTip = None

	if app.AUTO_CHAT_ENABLE:
		def OpenAutoChat(self):
			global wndAutoChatWindow
			if wndAutoChatWindow.IsShow():
				wndAutoChatWindow.Close()
			else:
				wndAutoChatWindow.Open()

	## Open & Close
	def OpenChat(self):
		self.SetSize(self.CHAT_WINDOW_WIDTH, 25)
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_EDIT)
		self.boardState = chat.BOARD_STATE_EDIT
		self.__RefreshChatInputLayout()

		(x, y, width, height) = self.GetRect()
		(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()

		if localeInfo.IsARABIC():
			chat.SetPosition(self.chatID, x + width - 10, y)
		else:
			chat.SetPosition(self.chatID, x + 10, y)

		chat.SetHeight(self.chatID, y - btnY - self.EDIT_LINE_HEIGHT + 100)

		if self.IsShow():
			self.btnChatSizing.Show()
			if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
				self.flag_bar.Hide()
				self.flag_bar.Show()

		self.Refresh()

		self.btnSendWhisper.Show()
		self.__RefreshChatInputLayout()

		self.chatInputSet.Open()
		self.chatInputSet.SetTop()
		self.SetTop()

	def CloseChat(self):
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_VIEW)
		self.boardState = chat.BOARD_STATE_VIEW

		(x, y, width, height) = self.GetRect()

		if localeInfo.IsARABIC():
			chat.SetPosition(self.chatID, x + width - 10, y + self.EDIT_LINE_HEIGHT)
		else:
			chat.SetPosition(self.chatID, x + 10, y + self.EDIT_LINE_HEIGHT)

		self.SetSize(self.CHAT_WINDOW_WIDTH, 0)

		self.chatInputSet.Close()
		self.btnSendWhisper.Hide()
		self.btnChatSizing.Hide()
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.flag_bar.Hide()
		if app.AUTO_CHAT_ENABLE:
			self.autoChatBtn.Hide()

		self.Refresh()

	def SetSendWhisperEvent(self, event):
		self.btnSendWhisper.SetEvent(event)

	def SetOpenChatLogEvent(self, event):
		if self.btnChatLog:
			self.btnChatLog.SetEvent(event)
	
	if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
		def __LayoutFlagBar(self, barWidth):
			langKeys = sorted(self.lang_image_dict.keys())
			if not langKeys:
				return

			flagIconH = 17
			for lang in langKeys:
				imgH = self.lang_image_dict[lang].GetHeight()
				if imgH > 0:
					flagIconH = max(flagIconH, imgH)
			flagIconY = max(0, (self.CHAT_FLAG_BAR_HEIGHT - flagIconH) // 2) + self.CHAT_FLAG_POS_OFFSET_Y

			labelEnd = self.CHAT_FLAG_LABEL_LEFT + self.CHAT_FLAG_LABEL_WIDTH + 8
			flagsWidth = len(langKeys) * self.CHAT_FLAG_STEP
			remainWidth = max(0, barWidth - labelEnd)
			startX = labelEnd + remainWidth // 2 + self.CHAT_FLAG_POS_OFFSET_X

			for i, lang in enumerate(langKeys):
				self.lang_image_dict[lang].SetPosition(startX + i * self.CHAT_FLAG_STEP, flagIconY)

			if self.flag_bar_clock:
				self.flag_bar_clock.SetPosition(self.CHAT_FLAG_CLOCK_RIGHT_PAD, 5)

		def OnMoveFlagBar(self):
			(btnX, btnY) = self.flag_bar.GetGlobalPosition()
			resizeY = btnY + self.CHAT_BAR_GAP_ABOVE + self.CHAT_FLAG_BAR_HEIGHT - self.CHAT_FLAG_BAR_OFFSET_Y
			self.btnChatSizing.SetPosition(btnX, resizeY)
			self.Refresh()

		def __EventCountry(self, event_type, lang):
			if "mouse_click" == event_type:
				if systemSetting.IsChatFilterCountry(lang):
					systemSetting.RemoveChatFilterCountry(lang)
				else:
					systemSetting.AddChatFilterCountry(lang)
				self.RefreshChatFilterSettings()
			elif "mouse_over_in" == event_type:
				langName = uiScriptLocale.LOCALE_NAME_DICT.get(lang, lang)
				if langName:
					pos_x, pos_y = wndMgr.GetMousePosition()
					self.toolTip.ClearToolTip()
					self.toolTip.SetThinBoardSize(max(80, 11 * len(langName)))
					self.toolTip.SetToolTipPosition(pos_x + 50, pos_y + 50)
					self.toolTip.AppendTextLine(langName, 0xffffff00)
					self.toolTip.ShowToolTip()
			elif "mouse_over_out" == event_type:
				self.toolTip.HideToolTip()

		def RefreshChatFilterSettings(self):
			for lang, btn in self.lang_image_dict.iteritems():
				if systemSetting.IsChatFilterCountry(lang):
					btn.SetAlpha(self.IMAGE_DISABLE_ALPHA)
				else:
					btn.SetAlpha(1.0)

	def IsEditMode(self):
		if chat.BOARD_STATE_EDIT == self.boardState:
			return True

		return False

	def __RefreshSizingBar(self):
		(x, y, width, height) = self.GetRect()
		gxChat, gyChat = self.btnChatSizing.GetGlobalPosition()
		self.btnChatSizing.SetPosition(x, gyChat)
		self.btnChatSizing.SetSize(width, self.CHAT_SIZING_HIT_HEIGHT)

	def SetPosition(self, x, y):
		ui.Window.SetPosition(self, x, y)
		self.__RefreshSizingBar()

	def __PositionChatChromeButtons(self):
		if app.AUTO_CHAT_ENABLE:
			if chat.BOARD_STATE_EDIT == self.boardState:
				self.autoChatBtn.SetPosition(self.GetWidth() - 50, 2)
				self.autoChatBtn.Show()
			else:
				self.autoChatBtn.Hide()
		if self.btnSendWhisper:
			self.btnSendWhisper.SetPosition(self.GetWidth() - 25, 2)

	def __RefreshChatInputLayout(self):
		if not self.chatInputSet:
			return
		inputWidth = max(120, self.GetWidth() - self.CHAT_INPUT_RIGHT_RESERVE)
		self.chatInputSet.SetSize(inputWidth, self.EDIT_LINE_HEIGHT)
		self.chatInputSet.RefreshPosition()
		self.__PositionChatChromeButtons()
		if self.chatInputSet.IsShow():
			self.chatInputSet.btnSend.Show()
			self.chatInputSet.SetTop()

	def SetSize(self, width, height):
		ui.Window.SetSize(self, width, height)
		self.__RefreshSizingBar()
		self.__RefreshChatInputLayout()

	def SetHeight(self, height):
		gxChat, gyChat = self.btnChatSizing.GetGlobalPosition()
		self.btnChatSizing.SetPosition(gxChat, wndMgr.GetScreenHeight() - height)

	###########
	## Refresh
	def Refresh(self):
		if self.boardState == chat.BOARD_STATE_EDIT:
			self.RefreshBoardEditState()
		elif self.boardState == chat.BOARD_STATE_VIEW:
			self.RefreshBoardViewState()

	def RefreshBoardEditState(self):

		(x, y, width, height) = self.GetRect()
		(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()

		self.xBar = x
		self.yBar = btnY
		self.widthBar = width
		self.heightBar = y - btnY + self.EDIT_LINE_HEIGHT
		self.curHeightBar = self.heightBar

		if localeInfo.IsARABIC():
			chat.SetPosition(self.chatID, x + width - 10, y)
		else:
			chat.SetPosition(self.chatID, x + 10, y)

		chat.SetHeight(self.chatID, y - btnY - self.EDIT_LINE_HEIGHT)
		chat.ArrangeShowingChat(self.chatID)

		if btnY > y:
			self.btnChatSizing.SetPosition(btnX, y)
			self.heightBar = self.EDIT_LINE_HEIGHT
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			flagY = btnY - self.CHAT_BAR_GAP_ABOVE - self.CHAT_FLAG_BAR_HEIGHT + self.CHAT_FLAG_BAR_OFFSET_Y
			self.flag_bar.SetSize(width, self.CHAT_FLAG_BAR_HEIGHT)
			self.flag_bar.SetPosition(btnX, flagY)
			self.__LayoutFlagBar(width)
			self.flag_bar.Show()
			self.flag_bar.SetTop()

	def RefreshBoardViewState(self):
		(x, y, width, height) = self.GetRect()
		(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()
		textAreaHeight = self.visibleLineCount * chat.GetLineStep(self.chatID)

		if localeInfo.IsARABIC():
			chat.SetPosition(self.chatID, x + width - 10, y + self.EDIT_LINE_HEIGHT)
		else:
			chat.SetPosition(self.chatID, x + 10, y + self.EDIT_LINE_HEIGHT)

		chat.SetHeight(self.chatID, y - btnY - self.EDIT_LINE_HEIGHT + 100)

		if self.boardState == chat.BOARD_STATE_EDIT:
			textAreaHeight += 45
		elif self.visibleLineCount != 0:
			textAreaHeight += 10 + 10

		self.xBar = x
		self.yBar = y + self.EDIT_LINE_HEIGHT - textAreaHeight
		self.widthBar = width
		self.heightBar = textAreaHeight

		self.scrollBar.Hide()

		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.flag_bar.Hide()

	##########
	## Render
	def OnUpdate(self):
		if self.boardState == chat.BOARD_STATE_EDIT:
			chat.Update(self.chatID)
		elif self.boardState == chat.BOARD_STATE_VIEW:
			if systemSetting.IsViewChat():
				chat.Update(self.chatID)

		if app.__BL_MULTI_LANGUAGE_ULTIMATE__ and self.flag_bar_clock:
			if self.flag_bar and self.flag_bar.IsShow():
				localtime = time.strftime("%d.%m.%Y / %H:%M:%S")
				self.flag_bar_clock.SetText(localtime)
				self.flag_bar_clock.Show()

	def OnRender(self):
		if chat.GetVisibleLineCount(self.chatID) != self.visibleLineCount:
			self.visibleLineCount = chat.GetVisibleLineCount(self.chatID)
			self.Refresh()

		if self.curHeightBar != self.heightBar:
			self.curHeightBar += (self.heightBar - self.curHeightBar) / 10

		if self.boardState == chat.BOARD_STATE_EDIT:
			grp.SetColor(self.BOARD_MIDDLE_COLOR)
			grp.RenderBar(self.xBar, self.yBar + (self.heightBar - self.curHeightBar) + 10, self.widthBar, self.curHeightBar)
			chat.Render(self.chatID)
		elif self.boardState == chat.BOARD_STATE_VIEW:
			if systemSetting.IsViewChat():
				grp.RenderGradationBar(self.xBar, self.yBar + (self.heightBar - self.curHeightBar), self.widthBar, self.curHeightBar, self.BOARD_START_COLOR, self.BOARD_END_COLOR)
				chat.Render(self.chatID)

	##########
	## Event
	def OnTop(self):
		self.btnChatSizing.SetTop()
		self.scrollBar.SetTop()
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__ and self.flag_bar:
			self.flag_bar.SetTop()

	def OnScroll(self):
		if not self.scrollLock:
			self.scrollBarPos = self.scrollBar.GetPos()

		lineCount = chat.GetLineCount(self.chatID)
		visibleLineCount = chat.GetVisibleLineCount(self.chatID)
		endLine = visibleLineCount + int(float(lineCount - visibleLineCount) * self.scrollBarPos)

		chat.SetEndPos(self.chatID, self.scrollBarPos)

	def OnChangeChatMode(self):
		self.chatInputSet.OnChangeChatMode()

	def SetChatFocus(self):
		self.chatInputSet.SetChatFocus()

	def BindInterface(self, interface):
		self.interface = interface
		self.chatInputSet.BindInterface(interface)

## ChatLogWindow
class ChatLogWindow(ui.Window):

	BLOCK_WIDTH = 32
	CHAT_MODE_NAME = [ localeInfo.CHAT_NORMAL, localeInfo.CHAT_PARTY, localeInfo.CHAT_GUILD, localeInfo.CHAT_SHOUT, localeInfo.CHAT_INFORMATION, localeInfo.CHAT_NOTICE, ]
	CHAT_MODE_INDEX = [ chat.CHAT_TYPE_TALKING,
						chat.CHAT_TYPE_PARTY,
						chat.CHAT_TYPE_GUILD,
						chat.CHAT_TYPE_SHOUT,
						chat.CHAT_TYPE_INFO,
						chat.CHAT_TYPE_NOTICE, ]

	if app.ENABLE_DICE_SYSTEM:
		CHAT_MODE_NAME.append(localeInfo.CHAT_DICE_INFO)
		CHAT_MODE_INDEX.append(chat.CHAT_TYPE_DICE_INFO)

	CHAT_LOG_WINDOW_MINIMUM_WIDTH = 450
	CHAT_LOG_WINDOW_MINIMUM_HEIGHT = 120

	# Mobile redesign layout
	MOBILE_WIDTH = 1000
	MOBILE_HEIGHT = 640
	HEADER_H = 50
	SIDEBAR_W = 295
	SIDE_BTN_X = 13
	SIDE_BTN_W = 270
	SIDE_BTN_H = 30
	SIDE_BTN_GAP = 16
	SIDE_BTN_TOP = 68
	COLLAPSE_SIZE = 46
	CLOSE_BTN_SIZE = 60
	BOTTOM_BTN_H = 34
	BOTTOM_MARGIN = 10
	SCROLLBAR_W = 14
	INPUT_H = 56
	RIGHT_TAB_W = 16
	RIGHT_TAB_H = 64
	POPUP_W = 200
	POPUP_PAD = 13
	POPUP_BTN_H = 34
	POPUP_BTN_GAP = 6
	POPUP_TITLE_H = 30

	COL_WINDOW_BG = 0xF01C1C1C
	COL_HEADER_BG = 0xF02C2C2C
	COL_SIDEBAR_BG = 0xF0232323
	COL_MAIN_BG = 0xC0141414
	# Enter chat window style background (transparent top -> dark bottom)
	COL_MAIN_GRAD_START = grp.GenerateColor(0.0, 0.0, 0.0, 0.0)
	COL_MAIN_GRAD_END = grp.GenerateColor(0.0, 0.0, 0.0, 0.8)
	COL_POPUP_BG = 0xF02B2B2B
	COL_POPUP_BORDER = 0xFF000000

	# Nesne market category buttons + thinboard background (ESC menu / Yetkili Cagir)
	BTN_UP = "d:/ymir work/nesne_market/kategori.png"
	BTN_OVER = "d:/ymir work/nesne_market/kategori.png"
	BTN_DOWN = "d:/ymir work/nesne_market/kategori2.png"
	BTN_MARGIN = 14
	TITLE_TEXT_COLOR = 0xffF8BF24
	MENU_FONT = localeInfo.UI_DEF_FONT
	# extra px added between chat lines in the log view
	CHAT_LINE_EXTRA_STEP = 15

	FLAT_FILL_NORMAL = grp.GenerateColor(0.42, 0.37, 0.23, 1.0)
	FLAT_FILL_OVER = grp.GenerateColor(0.53, 0.46, 0.29, 1.0)
	FLAT_FILL_SELECTED = grp.GenerateColor(0.62, 0.54, 0.35, 1.0)
	FLAT_BORDER = grp.GenerateColor(0.74, 0.66, 0.44, 1.0)
	FLAT_DARK_FILL = grp.GenerateColor(0.16, 0.16, 0.16, 1.0)
	FLAT_DARK_OVER = grp.GenerateColor(0.24, 0.24, 0.24, 1.0)
	FLAT_DARK_BORDER = grp.GenerateColor(0.45, 0.45, 0.45, 1.0)
	FLAT_TEXT_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)

	## Flat rounded button rendered via grp (no external asset needed)
	class FlatButton(ui.Window):
		BUTTON_STATE_UP = 0
		BUTTON_STATE_OVER = 1
		BUTTON_STATE_DOWN = 2

		def __init__(self):
			ui.Window.__init__(self)
			self.state = self.BUTTON_STATE_UP
			self.selected = False
			self.dark = False
			self.event = None
			self.buttonText = None
			self.btnWidth = 0
			self.btnHeight = 0
			self.SetWindowName("ChatLogFlatButton")

		def __del__(self):
			ui.Window.__del__(self)

		def SetEvent(self, event):
			self.event = event

		def SAFE_SetEvent(self, event):
			self.event = ui.__mem_func__(event)

		def SetDarkStyle(self, flag):
			self.dark = flag

		def SetSelected(self, flag):
			self.selected = flag

		def SetText(self, text):
			if None == self.buttonText:
				textLine = ui.TextLine()
				textLine.SetParent(self)
				textLine.AddFlag("not_pick")
				textLine.SetWindowHorizontalAlignCenter()
				textLine.SetWindowVerticalAlignCenter()
				textLine.SetVerticalAlignCenter()
				textLine.SetHorizontalAlignCenter()
				textLine.SetPackedFontColor(0xFFFFFFFF)
				textLine.SetOutline()
				textLine.Show()
				self.buttonText = textLine
			self.buttonText.SetText(text)

		def SetSize(self, width, height):
			self.btnWidth = width
			self.btnHeight = height
			ui.Window.SetSize(self, width, height)

		def OnMouseOverIn(self):
			self.state = self.BUTTON_STATE_OVER

		def OnMouseOverOut(self):
			self.state = self.BUTTON_STATE_UP

		def OnMouseLeftButtonDown(self):
			self.state = self.BUTTON_STATE_DOWN

		def OnMouseLeftButtonUp(self):
			self.state = self.BUTTON_STATE_UP
			if self.IsIn():
				self.state = self.BUTTON_STATE_OVER
			if None != self.event:
				self.event()

		def OnRender(self):
			if not self.IsShow():
				return
			(x, y) = self.GetGlobalPosition()
			owner = ChatLogWindow
			if self.dark:
				if self.selected or self.state == self.BUTTON_STATE_DOWN:
					fill = owner.FLAT_DARK_OVER
				elif self.state == self.BUTTON_STATE_OVER:
					fill = owner.FLAT_DARK_OVER
				else:
					fill = owner.FLAT_DARK_FILL
				border = owner.FLAT_DARK_BORDER
			else:
				if self.selected or self.state == self.BUTTON_STATE_DOWN:
					fill = owner.FLAT_FILL_SELECTED
				elif self.state == self.BUTTON_STATE_OVER:
					fill = owner.FLAT_FILL_OVER
				else:
					fill = owner.FLAT_FILL_NORMAL
				border = owner.FLAT_BORDER
			grp.SetColor(fill)
			grp.RenderBar(x, y, self.btnWidth, self.btnHeight)
			grp.SetColor(border)
			grp.RenderRoundBox(x, y, self.btnWidth, self.btnHeight)

	## Dark rounded board used as the name context-menu background
	class PopupBoard(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.SetWindowName("ChatLogPopupBoard")

		def __del__(self):
			ui.Window.__del__(self)

		def OnRender(self):
			if not self.IsShow():
				return
			(x, y) = self.GetGlobalPosition()
			w = self.GetWidth()
			h = self.GetHeight()
			grp.SetColor(ChatLogWindow.COL_POPUP_BG)
			grp.RenderBar(x, y, w, h)
			grp.SetColor(ChatLogWindow.COL_POPUP_BORDER)
			grp.RenderBox(x, y, w, h)

	## Renders the chat stream above the background board (drawn as a child so
	## it sits on top of the ThinBoard, unlike the parent OnRender which draws first)
	class ChatRenderer(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.SetWindowName("ChatLogRenderer")
			self.chatID = None
			self.gradStart = None
			self.gradEnd = None

		def __del__(self):
			ui.Window.__del__(self)

		def Bind(self, chatID, gradStart, gradEnd):
			self.chatID = chatID
			self.gradStart = gradStart
			self.gradEnd = gradEnd

		def OnRender(self):
			if None == self.chatID:
				return
			(x, y, width, height) = self.GetRect()
			grp.RenderGradationBar(x, y, width, height, self.gradStart, self.gradEnd)
			chat.ArrangeShowingChat(self.chatID)
			chat.SetPosition(self.chatID, x + 8, y + height - 6)
			chat.SetHeight(self.chatID, height - 12)
			chat.Update(self.chatID)
			chat.Render(self.chatID)

	class ResizeButton(ui.DragButton):

		def __init__(self):
			ui.DragButton.__init__(self)

		def __del__(self):
			ui.DragButton.__del__(self)

		def OnMouseOverIn(self):
			app.SetCursor(app.HVSIZE)

		def OnMouseOverOut(self):
			app.SetCursor(app.NORMAL)

	def __init__(self):

		self.allChatMode = True
		self.chatInputSet = None
		self.interface = None
		self.filterButtons = []
		self.sidebarCollapsed = False
		self.contextName = ""
		self.bg = None
		self.btnW = self.SIDE_BTN_W
		self.btnH = self.SIDE_BTN_H
		self.sidebarW = self.SIDEBAR_W
		self.mainX = self.SIDEBAR_W
		self.mainY = self.HEADER_H + 8
		self.mainW = 100
		self.mainH = 100

		ui.Window.__init__(self)
		self.AddFlag("float")
		self.AddFlag("movable")
		self.SetWindowName("ChatLogWindow")

		self.scrollBarPos = 1.0

		self.__CreateBackground()
		self.__CreateChatInputSet()
		self.__CreateSidebar()
		self.__CreateChrome()
		self.__CreatePopup()

		self.chatID = chat.CreateChatSet(chat.CHAT_SET_LOG_WINDOW)
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_LOG)
		for i in self.CHAT_MODE_INDEX:
			chat.EnableChatMode(self.chatID, i)

		chat.SetStep(self.chatID, chat.GetLineStep(self.chatID) + self.CHAT_LINE_EXTRA_STEP)

		self.chatRenderer.Bind(self.chatID, self.COL_MAIN_GRAD_START, self.COL_MAIN_GRAD_END)

		self.SetSize(self.MOBILE_WIDTH, self.MOBILE_HEIGHT)
		self.SetPosition((wndMgr.GetScreenWidth() - self.MOBILE_WIDTH) // 2, (wndMgr.GetScreenHeight() - self.MOBILE_HEIGHT) // 2)
		self.OnSelectFilter(None)
		self.__Layout()

	def __CreateBackground(self):
		bg = ui.ThinBoard()
		bg.SetParent(self)
		bg.AddFlag("not_pick")
		bg.SetPosition(0, 0)
		bg.Show()
		self.bg = bg

		chatRenderer = self.ChatRenderer()
		chatRenderer.SetParent(self)
		chatRenderer.AddFlag("not_pick")
		chatRenderer.Show()
		self.chatRenderer = chatRenderer

	def __CreateChatInputSet(self):
		chatInputSet = ChatInputSet()
		chatInputSet.SetParent(self)
		chatInputSet.SetEscapeEvent(ui.__mem_func__(self.Close))
		chatInputSet.Open()
		self.chatInputSet = chatInputSet

	def __MakeMenuButton(self, parent, text, radio=False, textColor=0xFFFFFFFF):
		btn = ui.RadioButton() if radio else ui.Button()
		btn.SetParent(parent)
		btn.SetUpVisual(self.BTN_UP)
		btn.SetOverVisual(self.BTN_OVER)
		btn.SetDownVisual(self.BTN_DOWN)
		btn.SetText(text)
		if btn.ButtonText:
			btn.ButtonText.SetFontName(self.MENU_FONT)
			btn.ButtonText.SetPosition(btn.GetWidth() // 2, btn.GetHeight() // 2)
		btn.SetTextColor(textColor)
		btn.Show()
		return btn

	def __CreateSidebar(self):
		entries = [ (None, localeInfo.CHAT_ALL),
					(chat.CHAT_TYPE_TALKING, localeInfo.CHAT_NORMAL),
					(chat.CHAT_TYPE_SHOUT, localeInfo.CHAT_SHOUT),
					(chat.CHAT_TYPE_INFO, localeInfo.CHAT_INFORMATION),
					(chat.CHAT_TYPE_NOTICE, localeInfo.CHAT_NOTICE),
					(chat.CHAT_TYPE_PARTY, localeInfo.CHAT_PARTY),
					(chat.CHAT_TYPE_GUILD, localeInfo.CHAT_GUILD), ]
		if app.ENABLE_DICE_SYSTEM:
			entries.append((chat.CHAT_TYPE_DICE_INFO, localeInfo.CHAT_DICE_INFO))

		self.filterButtons = []
		y = self.SIDE_BTN_TOP
		for mode, name in entries:
			btn = self.__MakeMenuButton(self, name, radio=True)
			if not self.btnW or self.btnW == self.SIDE_BTN_W:
				self.btnW = btn.GetWidth()
				self.btnH = btn.GetHeight()
			btn.SetPosition(self.BTN_MARGIN, y)
			btn.SetEvent(lambda m=mode, r=proxy(self): r.OnSelectFilter(m))
			self.filterButtons.append((mode, name, btn))
			y += self.btnH + self.SIDE_BTN_GAP

		self.sidebarW = self.btnW + 2 * self.BTN_MARGIN
		self.sidebarBottomY = y

	def __CreateChrome(self):
		headerText = ui.TextLine()
		headerText.SetParent(self)
		headerText.AddFlag("not_pick")
		headerText.SetPosition(18, (self.HEADER_H - 16) // 2)
		headerText.SetPackedFontColor(0xFFFFFFFF)
		headerText.SetOutline()
		headerText.SetText(localeInfo.CHAT_ALL)
		headerText.Show()
		self.headerText = headerText

		closeBtn = self.FlatButton()
		closeBtn.SetParent(self)
		closeBtn.SetDarkStyle(True)
		closeBtn.SetSize(self.CLOSE_BTN_SIZE, self.CLOSE_BTN_SIZE)
		closeBtn.SetText("X")
		closeBtn.SAFE_SetEvent(self.Close)
		closeBtn.Show()
		self.closeBtn = closeBtn

		titleBtn = self.__MakeMenuButton(self, localeInfo.AUTO_CHAT_TITLE, textColor=self.TITLE_TEXT_COLOR)
		titleBtn.SetEvent(ui.__mem_func__(self.__OpenAutoChat))
		self.titleBtn = titleBtn

	def __CreatePopup(self):
		btnH = self.btnH
		popupW = self.btnW + 2 * self.POPUP_PAD
		popupH = self.POPUP_TITLE_H + 3 * (btnH + self.POPUP_BTN_GAP) + self.POPUP_PAD

		popup = self.PopupBoard()
		popup.SetParent(self)
		popup.AddFlag("float")
		popup.SetSize(popupW, popupH)
		popup.Hide()

		popupTitle = ui.TextLine()
		popupTitle.SetParent(popup)
		popupTitle.AddFlag("not_pick")
		popupTitle.SetPosition(self.POPUP_PAD, 9)
		popupTitle.SetPackedFontColor(0xFFFFFFFF)
		popupTitle.SetOutline()
		popupTitle.Show()
		self.popupTitle = popupTitle

		py = self.POPUP_TITLE_H

		btnWhisper = self.__MakeMenuButton(popup, localeInfo.TARGET_BUTTON_WHISPER)
		btnWhisper.SetPosition(self.POPUP_PAD, py)
		btnWhisper.SAFE_SetEvent(self.__OnPopupWhisper)
		py += btnH + self.POPUP_BTN_GAP

		btnFriend = self.__MakeMenuButton(popup, localeInfo.TARGET_BUTTON_FRIEND)
		btnFriend.SetPosition(self.POPUP_PAD, py)
		btnFriend.SAFE_SetEvent(self.__OnPopupFriend)
		py += btnH + self.POPUP_BTN_GAP

		btnBlock = self.__MakeMenuButton(popup, localeInfo.TARGET_BUTTON_BLOCK)
		btnBlock.SetPosition(self.POPUP_PAD, py)
		btnBlock.SAFE_SetEvent(self.__OnPopupBlock)

		self.popup = popup
		self.popupBtnWhisper = btnWhisper
		self.popupBtnFriend = btnFriend
		self.popupBtnBlock = btnBlock

	def __del__(self):
		ui.Window.__del__(self)

	@ui.WindowDestroy
	def Destroy(self):
		self.bg = None
		self.chatRenderer = None
		self.headerText = None
		self.closeBtn = None
		self.titleBtn = None
		self.filterButtons = []
		self.popup = None
		self.popupTitle = None
		self.popupBtnWhisper = None
		self.popupBtnFriend = None
		self.popupBtnBlock = None
		self.chatInputSet = None
		self.interface = None

	def OnSelectFilter(self, mode):
		self.__HidePopup()
		if None == mode:
			self.allChatMode = True
			for i in self.CHAT_MODE_INDEX:
				chat.EnableChatMode(self.chatID, i)
			if self.headerText:
				self.headerText.SetText(localeInfo.CHAT_ALL)
		else:
			self.allChatMode = False
			for i in self.CHAT_MODE_INDEX:
				chat.DisableChatMode(self.chatID, i)
			chat.EnableChatMode(self.chatID, mode)
			if self.headerText:
				self.headerText.SetText(self.__GetModeName(mode))
		self.__RefreshFilterSelection(mode)

	def __GetModeName(self, mode):
		for entryMode, name, btn in self.filterButtons:
			if entryMode == mode:
				return name
		return localeInfo.CHAT_ALL

	def __RefreshFilterSelection(self, mode):
		for entryMode, name, btn in self.filterButtons:
			if entryMode == mode:
				btn.Down()
			else:
				btn.SetUp()

	def __HidePopup(self):
		if self.popup:
			self.popup.Hide()

	def __OpenAutoChat(self):
		self.__HidePopup()
		if not app.AUTO_CHAT_ENABLE:
			return
		if wndAutoChatWindow:
			if wndAutoChatWindow.IsShow():
				wndAutoChatWindow.Close()
			else:
				wndAutoChatWindow.Open()
				wndAutoChatWindow.SetTop()

	def OpenNameContextMenu(self, name, x=None, y=None):
		if not name or not self.popup:
			return
		self.contextName = name
		self.popupTitle.SetText(name)

		(gx, gy) = self.GetGlobalPosition()
		if None == x or None == y:
			(mx, my) = wndMgr.GetMousePosition()
			x = mx - gx
			y = my - gy

		popupW = self.popup.GetWidth()
		popupH = self.popup.GetHeight()
		maxX = self.GetWidth() - popupW
		maxY = self.GetHeight() - popupH
		if x > maxX:
			x = maxX
		if x < 0:
			x = 0
		if y > maxY:
			y = maxY
		if y < 0:
			y = 0

		self.popup.SetPosition(x, y)
		self.popup.Show()
		self.popup.SetTop()

	def __OnPopupWhisper(self):
		name = self.contextName
		self.__HidePopup()
		if name and self.interface:
			self.interface.OpenWhisperDialog(name)

	def __OnPopupFriend(self):
		name = self.contextName
		self.__HidePopup()
		if name:
			net.SendMessengerAddByNamePacket(name)

	def __OnPopupBlock(self):
		name = self.contextName
		self.__HidePopup()
		if name:
			net.SendChatPacket("/ignore " + name)

	def __Layout(self):
		width = self.GetWidth()
		height = self.GetHeight()
		sidebarW = self.sidebarW

		if self.bg:
			self.bg.SetSize(width, height)

		if self.closeBtn:
			self.closeBtn.SetPosition(width - self.CLOSE_BTN_SIZE - 8, 8)

		if self.titleBtn:
			self.titleBtn.SetPosition(self.BTN_MARGIN, height - self.btnH - self.BOTTOM_MARGIN)

		mainX = sidebarW + 8
		mainY = self.HEADER_H + 8
		mainW = width - mainX - 14
		mainH = height - mainY - self.INPUT_H - 14
		self.mainX = mainX
		self.mainY = mainY
		self.mainW = mainW
		self.mainH = mainH

		if self.chatRenderer:
			self.chatRenderer.SetPosition(mainX, mainY)
			self.chatRenderer.SetSize(mainW, mainH)

		if self.chatInputSet:
			self.chatInputSet.SetPosition(mainX, height - self.INPUT_H - 8)
			self.chatInputSet.SetSize(mainW, self.INPUT_H)
			self.chatInputSet.RefreshPosition()
			self.chatInputSet.SetChatMax(max(20, mainW // 8))

	def SetSize(self, width, height):
		ui.Window.SetSize(self, width, height)
		self.__Layout()

	def Open(self):
		self.__Layout()
		self.Show()

	def Close(self):
		self.__HidePopup()
		if self.chatInputSet:
			self.chatInputSet.KillChatFocus()
		self.Hide()

	def OnMouseWheel(self, nLen):
		lineCount = chat.GetLineCount(self.chatID)
		visibleLineCount = chat.GetVisibleLineCount(self.chatID)
		scrollableLines = lineCount - visibleLineCount
		if scrollableLines <= 0:
			return True

		step = 3.0 / float(scrollableLines)
		self.scrollBarPos = max(0.0, min(1.0, self.scrollBarPos - nLen * step))
		chat.SetEndPos(self.chatID, self.scrollBarPos)
		return True

	def OnPressEscapeKey(self):
		if self.popup and self.popup.IsShow():
			self.__HidePopup()
			return True
		self.Close()
		return True

	def BindInterface(self, interface):
		self.interface = interface

	def OnMouseLeftButtonDown(self):
		self.__HidePopup()
		hyperlink = ui.GetHyperlink()
		if hyperlink and hyperlink[:7] == "player:":
			self.OpenNameContextMenu(hyperlink[7:])
			return
		if app.__BL_MULTI_LANGUAGE_PREMIUM__:
			country = chat.GetCountry()
			empire = chat.GetEmpire()
			if hyperlink:
				if app.IsPressed(app.DIK_LALT):
					link = chat.GetLinkFromHyperlink(hyperlink)
					ime.PasteString(link)
				else:
					self.interface.MakeHyperlinkTooltip(hyperlink)
			elif country:
				self.interface.MakeCountryTooltip(country)
			elif empire:
				self.interface.MakeEmpireTooltip(empire)
		else:
			if hyperlink:
				if app.IsPressed(app.DIK_LALT):
					link = chat.GetLinkFromHyperlink(hyperlink)
					ime.PasteString(link)
				else:
					self.interface.MakeHyperlinkTooltip(hyperlink)

if app.AUTO_CHAT_ENABLE:
	autoChatLastText = ""
	from _weakref import proxy
	def RefreshAutoChat():
		if wndAutoChatWindow:
			wndAutoChatWindow.Refresh()
	def SetStatusAutoChat(status):
		if wndAutoChatWindow:
			wndAutoChatWindow.SetStatus(status)
	def UpdateAutoChat():
		if wndAutoChatWindow:
			wndAutoChatWindow.Update()
	class AutoChatWindow(ui.BoardWithTitleBar):
		def __init__(self):
			ui.BoardWithTitleBar.__init__(self)
			self.__LoadWindow()
		def Destroy(self):
			self.__children={}
		def __LoadWindow(self):
			self.Destroy()
			self.AddFlag("attach")
			self.AddFlag("movable")
			self.AddFlag("float")
			self.SetSize(495, 150)

			self.SetTitleName(localeInfo.AUTO_CHAT_TITLE)
			self.SetCloseEvent(self.Close)
			self.SetCenterPosition()

			text1 = ui.TextLine()
			text1.SetParent(self)
			text1.SetText(localeInfo.AUTO_CHAT_DESC)
			text1.SetPosition((self.GetWidth()/2)  - (text1.GetTextSize()[0] / 2), 41)
			text1.Show()
			self.__children["text1"] = text1

			text2 = ui.TextLine()
			text2.SetParent(self)
			text2.SetText(localeInfo.AUTO_CHAT_SAVED_MESSAGE)
			text2.SetPosition((self.GetWidth()/2)  - (text2.GetTextSize()[0] / 2), 76)
			text2.Show()
			self.__children["text2"] = text2

			shoutText = ui.TextLine()
			shoutText.SetParent(self)
			shoutText.SetPackedFontColor(0xFFFFC700)
			shoutText.Show()
			self.__children["shoutText"] = shoutText

			enableBtn = ui.RadioButton()
			enableBtn.SetParent(self)
			enableBtn.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
			enableBtn.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
			enableBtn.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
			enableBtn.SAFE_SetEvent(self.__SetStatus, 1)
			enableBtn.SetText(localeInfo.AUTO_CHAT_ENABLED)
			enableBtn.SetPosition( (self.GetWidth() / 2) - (27 + enableBtn.GetWidth()), 120)
			enableBtn.Show()
			self.__children["enableBtn"] = enableBtn

			disabledBtn = ui.RadioButton()
			disabledBtn.SetParent(self)
			disabledBtn.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
			disabledBtn.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
			disabledBtn.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
			disabledBtn.SAFE_SetEvent(self.__SetStatus, 0)
			disabledBtn.SetText(localeInfo.AUTO_CHAT_DISABLED)
			disabledBtn.SetPosition( (self.GetWidth() / 2) + 27, 120)
			disabledBtn.Show()
			self.__children["disabledBtn"] = disabledBtn

			self.Clear()

		def SetChatInstance(self, chatLine):
			self.__children["chatLine"] = chatLine

		def Update(self):
			self.Check()
			if not self.__children.get("status", 0):
				return
			global autoChatLastText
			if autoChatLastText == "":
				return
			chatLine = self.__children.get("chatLine")
			if not chatLine:
				return
			if app.GetTime() < chatLine.lastShoutTime + 10:
				return
			chatLine.lastShoutTime = app.GetTime()
			net.SendChatPacket(autoChatLastText, chat.CHAT_TYPE_SHOUT)

		def SetStatus(self, status):
			self.__children["status"] = int(status)
			self.Refresh()

		def __SetStatus(self, status):
			if self.__children.get("status", 0) == status:
				return
			net.SendChatPacket("/auto_chat status {}".format(status))
			self.SetStatus(status)

		def Clear(self):
			global autoChatLastText
			autoChatLastText = ""
			self.__children["status"] = 0
			self.__children["playerName"] = player.GetName()

		def Refresh(self):
			global autoChatLastText
			shoutText = self.__children["shoutText"]
			shoutText.SetText(autoChatLastText if autoChatLastText != "" else localeInfo.AUTO_CHAT_NO_MESSAGE)
			shoutText.SetPosition((self.GetWidth()/2)  - (shoutText.GetTextSize()[0] / 2), 97)

			self.__children["enableBtn" if self.__children["status"] == 1 else "disabledBtn"].Down()
			self.__children["enableBtn" if self.__children["status"] == 0 else "disabledBtn"].SetUp()

		def Check(self):
			playerName = self.__children["playerName"] if self.__children.has_key("playerName") else ""
			if playerName != player.GetName():
				self.Clear()
				self.Refresh()
		def Open(self):
			self.Check()
			self.Refresh()
			self.Show()
		def Close(self):
			self.Hide()
		def OnPressEscapeKey(self):
			self.Close()
			return True
	wndAutoChatWindow = AutoChatWindow()
