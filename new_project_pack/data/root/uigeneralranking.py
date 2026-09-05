# -*- coding: ascii -*-
# Oyun ici siralama penceresi (ENABLE_PLAYER_STATISTICS)
# Eski_A_Src'den porte edildi. Uyarlamalar:
#  - ui.MakeTextLineNew / ui.MakeExpandedImageBox / ui.MakeThinBoard bu projede
#    olmadigindan yerel yardimcilar kullanilir.
#  - SAFE_SetOverInEvent/SAFE_SetOverOutEvent Window sinifinda olmadigindan
#    yerel HoverWindow alt sinifi kullanilir.
#  - SetButtonVisual yerine SetUpVisual/SetOverVisual/SetDownVisual.
#  - Yukleme animasyonu kareleri pakette yoksa sessizce atlanir.
import app
import ui
import dbg
import uiToolTip
import grp
import math
import constInfo
import localeInfo
import wndMgr
import net

SYSTEM_UI_PATH_27 = "d:/ymir work/ui/game/ranking/new/"


def MakeTextLineNew(parent, text, x, y):
	textLine = ui.TextLine()
	textLine.SetParent(parent)
	textLine.SetText(text)
	textLine.SetPosition(x, y)
	textLine.Show()
	return textLine


def MakeExpandedImageBox(parent, name, x, y):
	image = ui.ExpandedImageBox()
	image.SetParent(parent)
	if name != "":
		try:
			image.LoadImage(name)
		except:
			dbg.TraceError("uigeneralranking: resim yuklenemedi: %s" % name)
	image.SetPosition(x, y)
	image.Show()
	return image


def MakeThinBoardLocal(parent, x, y, width, height):
	thin = ui.ThinBoard()
	thin.SetParent(parent)
	thin.SetPosition(x, y)
	thin.SetSize(width, height)
	thin.Show()
	return thin


class HoverWindow(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.overInEvent = None
		self.overInArgs = None
		self.overOutEvent = None
		self.overOutArgs = None
		self.leftDownEvent = None
		self.leftDownArgs = None

	def __del__(self):
		ui.Window.__del__(self)

	def SAFE_SetOverInEvent(self, func, *args):
		self.overInEvent = ui.__mem_func__(func)
		self.overInArgs = args

	def SAFE_SetOverOutEvent(self, func, *args):
		self.overOutEvent = ui.__mem_func__(func)
		self.overOutArgs = args

	# ui.Window.SetMouseLeftButtonDownEvent bazi derlemelerde ENABLE_WIKI'ye
	# bagli; bagimliligi kaldirmak icin kendi tiklama isleyicimiz var.
	def SetMouseLeftButtonDownEvent(self, func, *args):
		self.leftDownEvent = func
		self.leftDownArgs = args

	def OnMouseLeftButtonDown(self):
		if self.leftDownEvent:
			apply(self.leftDownEvent, self.leftDownArgs)

	def OnMouseOverIn(self):
		if self.overInEvent:
			apply(self.overInEvent, self.overInArgs)

	def OnMouseOverOut(self):
		if self.overOutEvent:
			apply(self.overOutEvent, self.overOutArgs)


class GeneralRankingWindow(ui.BoardWithTitleBar):
	class TextToolTip(ui.Window):
		def __init__(self):
			ui.Window.__init__(self, "TOP_MOST")

			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetHorizontalAlignCenter()
			textLine.SetOutline()
			textLine.Show()
			self.textLine = textLine

		def __del__(self):
			ui.Window.__del__(self)

		def SetText(self, text):
			self.textLine.SetText(text)

		def OnRender(self):
			(mouseX, mouseY) = wndMgr.GetMousePosition()
			self.textLine.SetPosition(mouseX, mouseY - 15)

	class GeneralRankingRankingButton(ui.RadioButton):
		def __init__(self):
			ui.RadioButton.__init__(self)
			self.__Initialize()

		def __del__(self):
			ui.RadioButton.__del__(self)

		def __Initialize(self):
			self.txtRankTypeName = MakeTextLineNew(self, "", 35, 6)
			self.iRBrofileImage = MakeExpandedImageBox(self, "", 5, 4)
			self.buttonType = None

		def BindInformations(self, text, image):
			self.txtRankTypeName.SetText(text)
			try:
				self.iRBrofileImage.LoadImage(image)
			except:
				pass

		def SetButtonType(self, bType):
			self.buttonType = bType

		def GetButtonType(self):
			return self.buttonType

	class RankingLine(ui.ExpandedImageBox):
		MY_LINE_COLOR = grp.GenerateColor(1.0, 0.0, 0.0, 1.0)
		RANKING_TEXT_COLORS = {
			1 : (1.0, 1.0, 0.0),	# Altin
			2 : (0.37, 0.37, 0.37),	# Gumus
			3 : (1.0, 0.7, 0.4),	# Bronz
		}

		def __init__(self):
			ui.ExpandedImageBox.__init__(self)
			self.__Initialize()

		def __del__(self):
			ui.ExpandedImageBox.__del__(self)

		def __Initialize(self):
			self.txtRankingPosition = MakeTextLineNew(self, "", 17, 2)
			self.txtRankingPosition.SetHorizontalAlignCenter()
			self.txtPlayerName = MakeTextLineNew(self, "", 95, 2)
			self.txtPlayerName.SetHorizontalAlignCenter()
			self.iPlayerJob = MakeExpandedImageBox(self, "", 161, 1)
			self.txtPlayerStatus = MakeTextLineNew(self, "", 243, 2)
			self.txtPlayerStatus.SetHorizontalAlignCenter()

		def BindInformations(self, position, name, pJob, status, image):
			try:
				self.LoadImage(image)
			except:
				pass
			self.txtRankingPosition.SetText(str(position))
			if (self.RANKING_TEXT_COLORS.has_key(int(position))):
				self.txtRankingPosition.SetFontColor(*self.RANKING_TEXT_COLORS[int(position)])
			self.txtPlayerName.SetText(name)
			try:
				self.iPlayerJob.LoadImage(pJob)
			except:
				pass
			if long(str(status)) == 0:
				self.txtPlayerStatus.SetText("*")
			else:
				self.txtPlayerStatus.SetText(self.DottedNumber(long(str(status))))

		def DottedNumber(self, n):
			if n <= 0:
				return "0"
			return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))

	# Sabitler (UI gorselleri bu boyutlara gore hazirlandi)
	MAXIMUM_RANKING_LINES = 10
	RANKING_WINDOW_SIZE = [550, 377]
	BUTTON_PEEK_WINDOW_SIZE = [140, 240]
	RANKING_LINES_WINDOW_SIZE = [298, 209]
	BUTTONS_CHANGE_RANKING_TYPE_SIZE = [122, 31]

	SCROLL_SPEED = 50

	GLOBAL_RANKING_IDENT = 0
	WEEKLY_RANKING_IDENT = 1

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)

		self.__Initialize()
		if self.__BuildBoard() is False:
			dbg.TraceError("GeneralRankingWindow yuklenemedi")

		self.__BuildLoadingFrame()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Initialize(self):
		self.d_ranking = {
			"select_button_images" : ["buttons/but_default.png", "buttons/but_hover.png", "buttons/but_down.png"],
			"global_ranking" : {
				"page_event_type" : self.GLOBAL_RANKING_IDENT,

				"ranking_type_order" : [
					localeInfo.GLOBAL_RANKING_MAX_STONE_DMG,
					localeInfo.GLOBAL_RANKING_MAX_BOSS_DMG,
					localeInfo.GLOBAL_RANKING_MAX_PLAYER_DMG,
					localeInfo.GLOBAL_RANKING_PLAYTIME_TYPE,
				],
				"ranking_type_config" : {
					localeInfo.GLOBAL_RANKING_MAX_STONE_DMG : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/metin_icon.png",
						"load_identifie_code" : "/request_ranking_list 1",
					},
					localeInfo.GLOBAL_RANKING_MAX_BOSS_DMG : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/boss_icon.png",
						"load_identifie_code" : "/request_ranking_list 2",
					},
					localeInfo.GLOBAL_RANKING_MAX_PLAYER_DMG : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/dojang_icon.png",
						"load_identifie_code" : "/request_ranking_list 3",
					},
					localeInfo.GLOBAL_RANKING_PLAYTIME_TYPE : {
						"header_image" : "global_ranking/playtime_header.png",
						"icon_image" : "icons/play_time_icon.png",
						"load_identifie_code" : "/request_ranking_list 7",
					},
				},

				"scroll_board" : None,
				"image_header_ranking" : None,
				"ranking_lines_window" : None,
				"ranking_lines" : [],
				"ranking_buttons" : [],
			},

			"weekly_ranking" : {
				"page_event_type" : self.WEEKLY_RANKING_IDENT,

				"ranking_type_order" : [
					localeInfo.GLOBAL_RANKING_LUSIFER_COUNT,
					localeInfo.GLOBAL_RANKING_AZRAIL_COUNT,
					localeInfo.GLOBAL_RANKING_GENERAL_COUNT,
					localeInfo.GLOBAL_RANKING_CADI_COUNT,
					localeInfo.GLOBAL_RANKING_EJDER_COUNT,
					localeInfo.GLOBAL_RANKING_STONE_COUNT,
				],
				"ranking_type_config" : {
					localeInfo.GLOBAL_RANKING_LUSIFER_COUNT : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/boss_icon.png",
						"load_identifie_code" : "/request_ranking_list 8",
					},

					localeInfo.GLOBAL_RANKING_AZRAIL_COUNT : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/hydra_icon.png",
						"load_identifie_code" : "/request_ranking_list 9",
					},

					localeInfo.GLOBAL_RANKING_GENERAL_COUNT : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/dojang_icon.png",
						"load_identifie_code" : "/request_ranking_list 10",
					},

					localeInfo.GLOBAL_RANKING_CADI_COUNT : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/malivore_icon.png",
						"load_identifie_code" : "/request_ranking_list 11",
					},

					localeInfo.GLOBAL_RANKING_EJDER_COUNT : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/cosmic_dragon_icon.png",
						"load_identifie_code" : "/request_ranking_list 12",
					},

					localeInfo.GLOBAL_RANKING_STONE_COUNT : {
						"header_image" : "global_ranking/pvp_header.png",
						"icon_image" : "icons/metin_icon.png",
						"load_identifie_code" : "/request_ranking_list 5",
					},
				},

				"scroll_board" : None,
				"image_header_ranking" : None,
				"ranking_lines_window" : None,
				"ranking_lines" : [],
				"ranking_buttons" : [],
			}
		}

		self.thinBoardBase = None
		self.background = None
		self.lastRefresh = None

		self.loadingBgFrame = None
		self.loadingFrame = None

		self.buttonsPeekWindow = None
		self.buttonsWindowSeparators = []

		self.imageRankingType = None

		self.buttonGlobal = None
		self.buttonWeekly = None

		self.scrollBar = None

		self.lastRefreshStr = ""

		self.selectedRankingType = -1
		self.selectedSubRankingType = {self.GLOBAL_RANKING_IDENT : "", self.WEEKLY_RANKING_IDENT : ""}

		self.toolTipRankingTypeButtons = self.TextToolTip()
		self.toolTipRankingTypeButtons.Hide()

		self.rankToolTip = uiToolTip.ToolTip(280)
		self.rankToolTip.Hide()

	def __BuildBoard(self):
		self.SetTitleName(localeInfo.GENERAL_RANKING_TITLE)
		self.SetSize(*self.RANKING_WINDOW_SIZE)
		self.SetCloseEvent(ui.__mem_func__(self.Hide))
		[self.AddFlag(flag) for flag in ["float", "movable"]]
		self.SetCenterPosition()
		try:
			self.thinBoardBase = MakeThinBoardLocal(self, 6, 28, *tuple(x-y for x,y in zip(self.RANKING_WINDOW_SIZE, [13, 35])))
			self.background = MakeExpandedImageBox(self.thinBoardBase, SYSTEM_UI_PATH_27 + "background.png", 5, 15)
			self.imageRankingType = MakeExpandedImageBox(self.background, SYSTEM_UI_PATH_27 + "global_ranking/global_ranking_type.png", 0, 4)
			self.lastRefresh = MakeTextLineNew(self.background, "", 17, 18)
			self.lastRefresh.SetWindowHorizontalAlignRight()
			self.lastRefresh.SetHorizontalAlignRight()
			self.lastRefresh.SetVerticalAlignCenter()
			self.buttonGlobal = HoverWindow()
			self.buttonGlobal.SetParent(self.background)
			self.buttonGlobal.SetPosition(0, 4)
			self.buttonGlobal.SetSize(self.BUTTONS_CHANGE_RANKING_TYPE_SIZE[0], self.BUTTONS_CHANGE_RANKING_TYPE_SIZE[1])
			self.buttonGlobal.SAFE_SetOverInEvent(self.__OverInRankingTypeButton, self.GLOBAL_RANKING_IDENT)
			self.buttonGlobal.SAFE_SetOverOutEvent(self.__OutOfRankingTypeButton)
			self.buttonGlobal.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.__ToggleRankingGeneralType), self.GLOBAL_RANKING_IDENT)
			self.buttonGlobal.Show()
			self.buttonWeekly = HoverWindow()
			self.buttonWeekly.SetParent(self.background)
			self.buttonWeekly.SetPosition(self.BUTTONS_CHANGE_RANKING_TYPE_SIZE[0], 4)
			self.buttonWeekly.SetSize(*self.BUTTONS_CHANGE_RANKING_TYPE_SIZE)
			self.buttonWeekly.SAFE_SetOverInEvent(self.__OverInRankingTypeButton, self.WEEKLY_RANKING_IDENT)
			self.buttonWeekly.SAFE_SetOverOutEvent(self.__OutOfRankingTypeButton)
			self.buttonWeekly.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.__ToggleRankingGeneralType), self.WEEKLY_RANKING_IDENT)
			self.buttonWeekly.Show()
			self.__BuildRankingWindow()

			self.buttonsWindowSeparators.append(MakeExpandedImageBox(self.background, SYSTEM_UI_PATH_27 + "separator.png", 7, 45))
			self.buttonsWindowSeparators.append(MakeExpandedImageBox(self.background, SYSTEM_UI_PATH_27 + "separator.png", 7, 284))

			self.Hide()
			return True
		except:
			return False

	def __BuildRankingWindow(self):
		self.buttonsPeekWindow = ui.Window()
		self.buttonsPeekWindow.SetParent(self.background)
		self.buttonsPeekWindow.AddFlag("attach")
		self.buttonsPeekWindow.SetPosition(27, 48)
		self.buttonsPeekWindow.SetSize(*self.BUTTON_PEEK_WINDOW_SIZE)
		self.buttonsPeekWindow.Show()
		for rankingType in ["global_ranking", "weekly_ranking"]:
			self.d_ranking[rankingType]["scroll_board"] = ui.Window()
			self.d_ranking[rankingType]["scroll_board"].SetParent(self.buttonsPeekWindow)
			self.d_ranking[rankingType]["scroll_board"].AddFlag("attach")
			self.d_ranking[rankingType]["scroll_board"].SetPosition(0, 0)
			self.d_ranking[rankingType]["scroll_board"].Show()
			self.d_ranking[rankingType]["ranking_lines_window"] = ui.Window()
			self.d_ranking[rankingType]["ranking_lines_window"].SetParent(self.background)
			self.d_ranking[rankingType]["ranking_lines_window"].AddFlag("attach")
			self.d_ranking[rankingType]["ranking_lines_window"].SetPosition(205, 72)
			self.d_ranking[rankingType]["ranking_lines_window"].SetSize(298, 209)
			self.d_ranking[rankingType]["ranking_lines_window"].Show()
			xIdx = 0
			self.d_ranking[rankingType]["image_header_ranking"] = MakeExpandedImageBox(self.background, "", 195, 53)
			# Deterministik buton sirasi (py2 dict sirasi rastgele)
			orderedTypes = self.d_ranking[rankingType].get("ranking_type_order")
			if not orderedTypes:
				orderedTypes = self.d_ranking[rankingType]["ranking_type_config"].keys()
			for buttonType in orderedTypes:
				xIdx += 1
				radioBtn = self.GeneralRankingRankingButton()
				self.d_ranking[rankingType]["ranking_buttons"].append(radioBtn)
				bIndex = int(len(self.d_ranking[rankingType]["ranking_buttons"]) - 1)
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SetParent(self.d_ranking[rankingType]["scroll_board"])
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SetUpVisual(SYSTEM_UI_PATH_27 + self.d_ranking["select_button_images"][0])
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SetOverVisual(SYSTEM_UI_PATH_27 + self.d_ranking["select_button_images"][1])
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SetDownVisual(SYSTEM_UI_PATH_27 + self.d_ranking["select_button_images"][2])
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SetPosition(0, 4 + (bIndex * self.d_ranking[rankingType]["ranking_buttons"][bIndex].GetHeight()))
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].BindInformations(buttonType, SYSTEM_UI_PATH_27 + self.d_ranking[rankingType]["ranking_type_config"][buttonType]["icon_image"])
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SAFE_SetEvent(self.__SelectRakingType, buttonType, bIndex)
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].SetButtonType(buttonType)
				self.d_ranking[rankingType]["ranking_buttons"][bIndex].Show()
				if xIdx >= len(self.d_ranking[rankingType]["ranking_type_config"].keys()):
					break
			if rankingType == "weekly_ranking":
				break

	def __BuildLoadingFrame(self):
		if not self.background:
			return
		self.loadingBgFrame = MakeExpandedImageBox(self.background, SYSTEM_UI_PATH_27 + "loading_frame/load_frame_background.png", 0, 0)
		self.loadingBgFrame.Hide()

		self.loadingFrame = ui.AniImageBox()
		self.loadingFrame.SetParent(self.loadingBgFrame)
		self.loadingFrame.SetPosition(329, 164)
		self.loadingFrame.SetDelay(2)
		self.loadingFrame.Show()

		# Animasyon kareleri pakette yoksa sessizce atla (eski pakette de yoktu)
		try:
			for imageIdx in xrange(33):
				self.loadingFrame.AppendImage("d:/ymir work/ui/achievement/new/loading_frame/%d.tga" % (imageIdx))
		except:
			self.loadingFrame.Hide()

	def __ConvertIdentToString(self):
		return ("global_ranking" if self.selectedRankingType == self.GLOBAL_RANKING_IDENT else "weekly_ranking")

	def __ConvertIdentifieCodeToType(self):
		try:
			strRankingType = self.__ConvertIdentToString()
			rankingSubType = self.selectedSubRankingType[self.selectedRankingType]
			return int(self.d_ranking[strRankingType]["ranking_type_config"][rankingSubType]["load_identifie_code"].split()[1])
		except:
			return -1

	def __ReloadScrollBoard(self):
		strRankingType = self.__ConvertIdentToString()
		for button in self.d_ranking[strRankingType]["ranking_buttons"]:
			mxSize = button.GetLocalPosition()[1] + button.GetHeight()
			if mxSize > self.d_ranking[strRankingType]["scroll_board"].GetHeight():
				self.d_ranking[strRankingType]["scroll_board"].SetSize(self.buttonsPeekWindow.GetWidth(), mxSize)

		self.__ChangeScrollbar()

	def __ChangeScrollbar(self):
		if not self.scrollBar:
			return

		strRankingType = self.__ConvertIdentToString()
		scrollBoard = self.d_ranking[strRankingType]["scroll_board"]

		if scrollBoard.GetHeight() <= self.buttonsPeekWindow.GetHeight():
			self.scrollBar.Hide()
		else:
			self.scrollBar.SetScale(self.buttonsPeekWindow.GetHeight(), scrollBoard.GetHeight())
			self.scrollBar.SetPosScale((float(1) * abs(scrollBoard.GetLocalPosition()[1])) / (scrollBoard.GetHeight() - self.buttonsPeekWindow.GetHeight()))
			self.scrollBar.Show()

	def __OnScroll(self, fScale):
		strRankingType = self.__ConvertIdentToString()
		scrollBoard = self.d_ranking[strRankingType]["scroll_board"]

		if not scrollBoard:
			return

		curr = min(0, max(math.ceil((scrollBoard.GetHeight() - self.buttonsPeekWindow.GetHeight()) * fScale * -1.0), -scrollBoard.GetHeight() + self.buttonsPeekWindow.GetHeight()))
		scrollBoard.SetPosition(0, curr)

	def __OverInRankingTypeButton(self, ident):
		if not self.toolTipRankingTypeButtons:
			return

		(x, y) = self.background.GetGlobalPosition()
		button_width = self.BUTTONS_CHANGE_RANKING_TYPE_SIZE[0]
		center_size = (button_width / 2)

		self.toolTipRankingTypeButtons.SetText(localeInfo.GENERAL_RANKING_TOOLTIP1 if ident == self.GLOBAL_RANKING_IDENT else localeInfo.GENERAL_RANKING_TOOLTIP2)
		self.toolTipRankingTypeButtons.textLine.SetPosition(x + (0 if ident == self.GLOBAL_RANKING_IDENT else button_width) + center_size, y - 10)
		self.toolTipRankingTypeButtons.Show()

	def __OutOfRankingTypeButton(self):
		if self.toolTipRankingTypeButtons:
			self.toolTipRankingTypeButtons.Hide()

	def __OnOverInWeeklyRankingLine(self, rank):
		try:
			aRewards = [50, 35, 20, 10, 5, 5, 5, 5, 5, 5]
			reward = aRewards[rank-1]

			if self.rankToolTip:
				self.rankToolTip.ClearToolTip()
				self.rankToolTip.AppendTextLine(localeInfo.RANKING_PRIZEDETAILS % (str(rank), str(reward)))
				self.rankToolTip.Show()
		except:
			pass

	def __OnOverOutWeeklyRankingLine(self):
		if self.rankToolTip:
			self.rankToolTip.Hide()

	def __ToggleRankingGeneralType(self, new_ranking_ident, checkRankingLine = True):
		if self.selectedRankingType == new_ranking_ident:
			return

		self.selectedRankingType = new_ranking_ident
		strRankingType = self.__ConvertIdentToString()

		if not self.selectedSubRankingType[self.selectedRankingType] and checkRankingLine:
			if self.d_ranking[strRankingType]["ranking_buttons"]:
				self.__SelectRakingType(self.d_ranking[strRankingType]["ranking_buttons"][0].GetButtonType(), 0, True)

		if self.imageRankingType:
			try:
				self.imageRankingType.LoadImage(SYSTEM_UI_PATH_27 + "global_ranking/global_ranking_type.png" if\
						self.selectedRankingType == self.GLOBAL_RANKING_IDENT else SYSTEM_UI_PATH_27 + "weekly_ranking/weekly_ranking_type.png")
			except:
				pass

		for rankingType in ["global_ranking", "weekly_ranking"]:
			canShow = (rankingType == strRankingType)
			for objs_keys in ["scroll_board", "ranking_lines_window", "image_header_ranking"]:
				self.d_ranking[rankingType][objs_keys].Hide() if not canShow else self.d_ranking[rankingType][objs_keys].Show()

		self.__ReloadScrollBoard()

	def __SelectRakingType(self, rankingSubType, bIndex, runEvent = True):
		self.selectedSubRankingType[self.selectedRankingType] = rankingSubType
		strRankingType = self.__ConvertIdentToString()
		for i in xrange(len(self.d_ranking[strRankingType]["ranking_buttons"])):
			tmpButton = self.d_ranking[strRankingType]["ranking_buttons"][i]
			tmpButton.Down() if i == bIndex else tmpButton.SetUp()
		if self.d_ranking[strRankingType]["image_header_ranking"]:
			try:
				self.d_ranking[strRankingType]["image_header_ranking"].LoadImage(SYSTEM_UI_PATH_27 + self.d_ranking[strRankingType]["ranking_type_config"][rankingSubType]["header_image"])
			except:
				pass
		if runEvent:
			subRankType = self.__ConvertIdentifieCodeToType()
			if subRankType in constInfo.RANKING_CACHE:
				self.__DestroyRanking()
				self.RefreshWeeklyRanking()
				return
			self.__DestroyRanking()
			self.StartLoading()
			net.SendChatPacket(self.d_ranking[strRankingType]["ranking_type_config"][rankingSubType]["load_identifie_code"])

	def StartLoading(self):
		if self.loadingBgFrame:
			self.loadingBgFrame.Show()

		if self.lastRefresh:
			self.lastRefresh.SetText("...")

	def StopLoading(self):
		if self.loadingBgFrame:
			self.loadingBgFrame.Hide()
		if self.lastRefresh:
			self.lastRefresh.SetText(localeInfo.GENERAL_RANKING_LAST_REFRESH_TIME % self.lastRefreshStr)
		self.RefreshWeeklyRanking(True)

	def ListIsEmpty(self):
		if self.loadingBgFrame:
			self.loadingBgFrame.Hide()
		if self.lastRefresh:
			self.lastRefresh.SetText(localeInfo.GENERAL_RANKING_LAST_REFRESH_TIME % self.lastRefreshStr)

	def __DestroyRanking(self):
		strRankingType = self.__ConvertIdentToString()
		for rankingLine in self.d_ranking[strRankingType]["ranking_lines"]:
			rankingLine.Hide()
		del self.d_ranking[strRankingType]["ranking_lines"][:]

	def ReloadRankingWindow(self):
		if self.selectedRankingType == -1:
			self.__ToggleRankingGeneralType(self.GLOBAL_RANKING_IDENT, False)

			if self.d_ranking["global_ranking"]["ranking_buttons"]:
				self.__SelectRakingType(self.d_ranking["global_ranking"]["ranking_buttons"][0].GetButtonType(), 0)

		self.SetCenterPosition()

	def AppendGlobalRank(self, rank, name, pJob, score):
		strRankingType = self.__ConvertIdentToString()

		lIndex = len(self.d_ranking[strRankingType]["ranking_lines"])
		if lIndex >= self.MAXIMUM_RANKING_LINES:
			return

		rLine = self.RankingLine()
		self.d_ranking[strRankingType]["ranking_lines"].append(rLine)
		self.d_ranking[strRankingType]["ranking_lines"][-1].SetParent(self.d_ranking[strRankingType]["ranking_lines_window"])
		self.d_ranking[strRankingType]["ranking_lines"][-1].BindInformations(rank, name, SYSTEM_UI_PATH_27 + "face/" + str(pJob) + ".tga", score, SYSTEM_UI_PATH_27 + "lines/ranking_line.png")
		self.d_ranking[strRankingType]["ranking_lines"][-1].SetPosition(0, (lIndex * self.d_ranking[strRankingType]["ranking_lines"][-1].GetHeight()))
		self.d_ranking[strRankingType]["ranking_lines"][-1].Show()

	def RefreshGlobalRanking(self):
		self.StopLoading()

	def RefreshWeeklyRanking(self, fromLoader = False):
		strRankingType = self.__ConvertIdentToString()
		subRankingType = self.__ConvertIdentifieCodeToType()

		# Cift cizim onlemi: canli yukleme sirasinda AppendRank zaten satir ekledi;
		# cache'ten yeniden kurmadan once mevcut satirlar temizlenir.
		self.__DestroyRanking()

		if subRankingType != -1 and (len(constInfo.RANKING_CACHE) and constInfo.RANKING_CACHE.has_key(subRankingType)):
			for rank in xrange(self.MAXIMUM_RANKING_LINES):
				if len(constInfo.RANKING_CACHE[subRankingType]) <= rank:
					break

				name = constInfo.RANKING_CACHE[subRankingType][rank][0]
				score = constInfo.RANKING_CACHE[subRankingType][rank][1]
				pJob = constInfo.RANKING_CACHE[subRankingType][rank][3]
				self.SetLastRefreshTime(constInfo.RANKING_CACHE[subRankingType][rank][4])

				self.d_ranking[strRankingType]["ranking_lines"].append(self.RankingLine())
				self.d_ranking[strRankingType]["ranking_lines"][-1].SetParent(self.d_ranking[strRankingType]["ranking_lines_window"])
				self.d_ranking[strRankingType]["ranking_lines"][-1].BindInformations(str(rank+1), name, SYSTEM_UI_PATH_27 + "face/" + str(pJob) + ".tga", score, SYSTEM_UI_PATH_27 + "lines/ranking_line.png")
				self.d_ranking[strRankingType]["ranking_lines"][-1].SetPosition(0, (rank * self.d_ranking[strRankingType]["ranking_lines"][-1].GetHeight()))
				self.d_ranking[strRankingType]["ranking_lines"][-1].Show()
		if not fromLoader:
			self.StopLoading()

	def OnRunMouseWheel(self, length):
		if self.scrollBar and self.scrollBar.IsShow():
			return self.scrollBar.OnRunMouseWheelEvent(length)

		return False

	def OnPressEscapeKey(self):
		self.Hide()
		return True

	def AppendRank(self, iRank, pName, iScore, timeStr, pJob):
		curRankType = self.__ConvertIdentifieCodeToType()
		if not curRankType in constInfo.RANKING_CACHE:
			constInfo.RANKING_CACHE.update({curRankType : {}})
		constInfo.RANKING_CACHE[curRankType][iRank - 1] = [pName, iScore, 0, pJob, timeStr]
		self.AppendGlobalRank(iRank, pName, pJob, iScore)

	def SetLastRefreshTime(self, refTimeStr):
		self.lastRefreshStr = refTimeStr

	def BindInterface(self, ifClass):
		pass

	def ToggleWindow(self):
		if not self.IsShow():
			self.__ToggleRankingGeneralType(self.GLOBAL_RANKING_IDENT)
			self.Show()
			self.SetTop()
		else:
			self.Hide()
