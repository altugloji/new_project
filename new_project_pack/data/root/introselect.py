import chr
import grp
import app
import math
import wndMgr
import snd
import net
import systemSetting
import localeInfo
import chr

import ui
import uiScriptLocale
import networkModule
import musicInfo
import playerSettingModule

####################################
####################################
import uiCommon
import uiMapNameShower
import uiAffectShower
import uiPlayerGauge
import uiTarget
import consoleModule

import interfaceModule
import uiTaskBar
import uiInventory
import constInfo
###################################

LEAVE_BUTTON_FOR_POTAL = False
NOT_NEED_DELETE_CODE = False
ENABLE_ENGNUM_DELETE_CODE = True

###################################

# FAST_LOGIN_CHARACTER_SAVE:PORT file=introselect (grep FAST_LOGIN_CHARACTER_SAVE:PORT)

class SelectCharacterWindow(ui.Window):

	# SLOT4
	#SLOT_ROTATION = ( 140.0, 260.0, 20.0 )
	#SLOT_COUNT = 3
	if app.ENABLE_PLAYER_PER_ACCOUNT5:
		SLOT_ROTATION = [135.0, 207.0, 279.0, 351.0, 63.0]
		SLOT_COUNT = 5
		# SLOT_ROTATION = [135.0, 180.0, 225.0, 270.0, 315.0, 360.0, 45.0, 90.0]
		# SLOT_COUNT = 8
		# SLOT_ROTATION = [135.0, 157.5, 180.0, 202.5, 225.0, 247.5, 270.0, 292.5, 315.0, 337.5, 360.0, 382.5, 45.0, 67.5, 90.0, 112.5]
		# SLOT_COUNT = 16
	else:
		SLOT_ROTATION = [135.0, 225.0, 315.0, 45.0]
		SLOT_COUNT = 4
	if app.ENABLE_WOLFMAN_CHARACTER:
		CHARACTER_TYPE_COUNT = 5
	else:
		CHARACTER_TYPE_COUNT = 4

	if not app.__BL_MULTI_LANGUAGE__:
		EMPIRE_NAME = {
			net.EMPIRE_A : localeInfo.EMPIRE_A,
			net.EMPIRE_B : localeInfo.EMPIRE_B,
			net.EMPIRE_C : localeInfo.EMPIRE_C
		}

	class CharacterRenderer(ui.Window):
		def OnRender(self):
			grp.ClearDepthBuffer()

			grp.SetGameRenderState()
			grp.PushState()
			grp.SetOmniLight()

			screenWidth = wndMgr.GetScreenWidth()
			screenHeight = wndMgr.GetScreenHeight()
			newScreenWidth = float(screenWidth - 270)
			newScreenHeight = float(screenHeight)

			grp.SetViewport(270.0/screenWidth, 0.0, newScreenWidth/screenWidth, newScreenHeight/screenHeight)

			app.SetCenterPosition(0.0, 0.0, 0.0)
			app.SetCamera(1550.0, 15.0, 180.0, 95.0)
			grp.SetPerspective(10.0, newScreenWidth/newScreenHeight, 1000.0, 3000.0)

			(x, y) = app.GetCursorPosition()
			grp.SetCursorPosition(x, y)

			chr.Deform()
			chr.Render()

			grp.RestoreViewport()
			grp.PopState()
			grp.SetInterfaceRenderState()

	def __init__(self, stream):
		ui.Window.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_SELECT, self)

		self.stream=stream
		self.slot = self.stream.GetCharacterSlot()

		self.openLoadingFlag = False
		self.startIndex = -1
		self.startReservingTime = 0

		self.flagDict = {}
		self.curRotation = []
		self.destRotation = []
		for rot in self.SLOT_ROTATION:
			self.curRotation.append(rot)
			self.destRotation.append(rot)

		self.curNameAlpha = []
		self.destNameAlpha = []
		for i in xrange(self.CHARACTER_TYPE_COUNT):
			self.curNameAlpha.append(0.0)
			self.destNameAlpha.append(0.0)

		self.curGauge = [0.0, 0.0, 0.0, 0.0]
		self.destGauge = [0.0, 0.0, 0.0, 0.0]

		self.dlgBoard = 0
		self.changeNameFlag = False
		self.nameInputBoard = None
		self.sendedChangeNamePacket = False
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_init_quick_and_quiet_attrs ---
		if app.FAST_LOGIN_CHARACTER_SAVE:
			self.quickSaveButtons = []
			self.quickSaveBoard = None
			self.quickSaveBoardTitle = None
			self.quickSaveBoardLine = None
		self.quietLoadBar = None
		self.quietLoadText = None
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_init_quick_and_quiet_attrs ---

		self.startIndex = -1
		self.isLoad = 0
		if app.__BL_MULTI_LANGUAGE__:
			self.EMPIRE_NAME = {
				net.EMPIRE_A : localeInfo.EMPIRE_A,
				net.EMPIRE_B : localeInfo.EMPIRE_B,
				net.EMPIRE_C : localeInfo.EMPIRE_C
			}

	def __del__(self):
		ui.Window.__del__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_SELECT, 0)

	def Open(self):
		quiet_ui = getattr(self.stream, "hideSelectUiForAutoLogin", 0) and self.stream.isAutoSelect

		if not self.__LoadBoardDialog(uiScriptLocale.LOCALE_UISCRIPT_PATH + "selectcharacterwindow.py"):
			import dbg
			dbg.TraceError("SelectCharacterWindow.Open - __LoadScript Error")
			if quiet_ui:
				self.stream.hideSelectUiForAutoLogin = 0
			return

		if not self.__LoadQuestionDialog("uiscript/questiondialog.py"):
			if quiet_ui:
				self.stream.hideSelectUiForAutoLogin = 0
			return

		playerSettingModule.LoadGameData("INIT")

		self.InitCharacterBoard()

		self.btnStart.Enable()
		self.btnCreate.Enable()
		self.btnDelete.Enable()
		self.btnExit.Enable()
		self.btnLeft.Enable()
		self.btnRight.Enable()

		if quiet_ui:
			self.dlgBoard.Hide()
			self.dlgQuestion.Hide()
		else:
			self.dlgBoard.Show()
		self.SetWindowName("SelectCharacterWindow")
		self.Show()

		if self.slot>=0:
			self.SelectSlot(self.slot)

		if musicInfo.selectMusic != "" and not quiet_ui:
			snd.SetMusicVolume(systemSetting.GetMusicVolume())
			snd.FadeInMusic("BGM/"+musicInfo.selectMusic)

		app.SetCenterPosition(0.0, 0.0, 0.0)
		app.SetCamera(1550.0, 15.0, 180.0, 95.0)

		self.isLoad=1
		self.Refresh()

		if self.stream.isAutoSelect:
			chrSlot=self.stream.GetCharacterSlot()
			self.SelectSlot(chrSlot)
			self.StartGame()
			self.stream.isAutoSelect = 0

		self.HideAllFlag()
		self.SetEmpire(net.GetEmpireID())

		if quiet_ui:
			# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_open_quiet_quick_hide ---
			self.__ApplyQuietSelectOverlay()
			if app.FAST_LOGIN_CHARACTER_SAVE:
				for b in getattr(self, "quickSaveButtons", []):
					if b:
						b.Hide()
				qb = getattr(self, "quickSaveBoard", None)
				if qb:
					qb.Hide()
			app.HideCursor()
			# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_open_quiet_quick_hide ---
		else:
			app.ShowCursor()

		if getattr(self.stream, "hideSelectUiForAutoLogin", 0):
			self.stream.hideSelectUiForAutoLogin = 0

	# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_select_quiet_overlay_methods ---
	def __DestroyQuietSelectOverlay(self):
		if self.quietLoadText:
			self.quietLoadText.Hide()
			self.quietLoadText = None
		if self.quietLoadBar:
			self.quietLoadBar.Hide()
			self.quietLoadBar = None

	def __ApplyQuietSelectOverlay(self):
		self.__DestroyQuietSelectOverlay()
		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		self.SetSize(sw, sh)
		bar = ui.Bar("GAME")
		bar.SetParent(self)
		bar.AddFlag("not_pick")
		bar.SetPosition(0, 0)
		bar.SetSize(sw, sh)
		bar.SetColor(0xff101010)
		bar.Show()
		tx = ui.TextLine()
		tx.SetParent(self)
		tx.SetFontName(localeInfo.UI_DEF_FONT)
		tx.SetPackedFontColor(0xffffffff)
		tx.SetText(localeInfo.SELECT_QUIET_LOADING)
		tx.SetHorizontalAlignCenter()
		tx.SetVerticalAlignCenter()
		tx.SetPosition(sw / 2, sh / 2)
		tx.Show()
		bar.SetTop()
		tx.SetTop()
		self.quietLoadBar = bar
		self.quietLoadText = tx

	# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_select_quiet_overlay_methods ---

	def Close(self):
		self.__DestroyQuietSelectOverlay()
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_close_quick_save_destroy ---
		if app.FAST_LOGIN_CHARACTER_SAVE:
			self.__DestroyQuickCharacterSaveButtons()
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_close_quick_save_destroy ---
		if musicInfo.selectMusic != "":
			snd.FadeOutMusic("BGM/"+musicInfo.selectMusic)

		self.stream.popupWindow.Close()

		if self.dlgBoard:
			self.dlgBoard.ClearDictionary()

		self.empireName = None
		self.flagDict = {}
		self.dlgBoard = None
		self.btnStart = None
		self.btnCreate = None
		self.btnDelete = None
		self.btnExit = None
		self.btnLeft = None
		self.btnRight = None
		self.backGround = None

		self.dlgQuestion.ClearDictionary()
		self.dlgQuestion = None
		self.dlgQuestionText = None
		self.dlgQuestionAcceptButton = None
		self.dlgQuestionCancelButton = None
		self.privateInputBoard = None
		self.nameInputBoard = None

		for i in xrange(self.SLOT_COUNT):
			chr.DeleteInstance(i)

		self.Hide()
		self.KillFocus()

		app.HideCursor()

	def SetEmpire(self, id):
		self.empireName.SetText(self.EMPIRE_NAME.get(id, ""))
		if self.flagDict.has_key(id):
			self.flagDict[id].Show()

	def HideAllFlag(self):
		for flag in self.flagDict.values():
			flag.Hide()

	def Refresh(self):
		if not self.isLoad:
			return

		# SLOT4
		indexArray = range(self.SLOT_COUNT-1, -1, -1)
		for index in indexArray:
			id=net.GetAccountCharacterSlotDataInteger(index, net.ACCOUNT_CHARACTER_SLOT_ID)
			race=net.GetAccountCharacterSlotDataInteger(index, net.ACCOUNT_CHARACTER_SLOT_RACE)
			form=net.GetAccountCharacterSlotDataInteger(index, net.ACCOUNT_CHARACTER_SLOT_FORM)
			name=net.GetAccountCharacterSlotDataString(index, net.ACCOUNT_CHARACTER_SLOT_NAME)
			hair=net.GetAccountCharacterSlotDataInteger(index, net.ACCOUNT_CHARACTER_SLOT_HAIR)
			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				acce = net.GetAccountCharacterSlotDataInteger(index, net.ACCOUNT_CHARACTER_SLOT_ACCE)

			if id:
				if app.ENABLE_ACCE_COSTUME_SYSTEM:
					self.MakeCharacter(index, id, name, race, form, hair, acce)
				else:
					self.MakeCharacter(index, id, name, race, form, hair)
				self.SelectSlot(index)

		self.SelectSlot(self.slot)

	def GetCharacterSlotID(self, slotIndex):
		return net.GetAccountCharacterSlotDataInteger(slotIndex, net.ACCOUNT_CHARACTER_SLOT_ID)

	def __LoadQuestionDialog(self, fileName):
		self.dlgQuestion = ui.ScriptWindow()

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self.dlgQuestion, fileName)
		except:
			import exception
			exception.Abort("SelectCharacterWindow.LoadQuestionDialog.LoadScript")

		try:
			GetObject=self.dlgQuestion.GetChild
			self.dlgQuestionText=GetObject("message")
			self.dlgQuestionAcceptButton=GetObject("accept")
			self.dlgQuestionCancelButton=GetObject("cancel")
		except:
			import exception
			exception.Abort("SelectCharacterWindow.LoadQuestionDialog.BindObject")

		self.dlgQuestionText.SetText(localeInfo.SELECT_DO_YOU_DELETE_REALLY)
		self.dlgQuestionAcceptButton.SetEvent(ui.__mem_func__(self.RequestDeleteCharacter))
		self.dlgQuestionCancelButton.SetEvent(ui.__mem_func__(self.dlgQuestion.Hide))
		return 1

	def __LoadBoardDialog(self, fileName):
		self.dlgBoard = ui.ScriptWindow()

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self.dlgBoard, fileName)
		except:
			import exception
			exception.Abort("SelectCharacterWindow.LoadBoardDialog.LoadScript")

		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		self.SetSize(sw, sh)
		self.dlgBoard.SetParent(self)
		self.dlgBoard.SetPosition(0, 0)

		try:
			GetObject=self.dlgBoard.GetChild

			self.btnStart		= GetObject("start_button")
			self.btnCreate		= GetObject("create_button")
			self.btnDelete		= GetObject("delete_button")
			self.btnExit		= GetObject("exit_button")

			self.CharacterName	= GetObject("character_name_value")
			self.CharacterLevel = GetObject("character_level_value")
			self.PlayTime		= GetObject("character_play_time_value")
			self.CharacterHTH	= GetObject("character_hth_value")
			self.CharacterINT	= GetObject("character_int_value")
			self.CharacterSTR	= GetObject("character_str_value")
			self.CharacterDEX	= GetObject("character_dex_value")
			self.GuildName		= GetObject("GuildName")

			self.NameList = []
			self.NameList.append(GetObject("name_warrior"))
			self.NameList.append(GetObject("name_assassin"))
			self.NameList.append(GetObject("name_sura"))
			self.NameList.append(GetObject("name_shaman"))
			if app.ENABLE_WOLFMAN_CHARACTER:
				self.NameList.append(GetObject("name_wolfman"))

			self.GaugeList = []
			self.GaugeList.append(GetObject("gauge_hth"))
			self.GaugeList.append(GetObject("gauge_int"))
			self.GaugeList.append(GetObject("gauge_str"))
			self.GaugeList.append(GetObject("gauge_dex"))

			self.btnLeft = GetObject("left_button")
			self.btnRight = GetObject("right_button")

			self.empireName = GetObject("EmpireName")
			self.flagDict[net.EMPIRE_A] = GetObject("EmpireFlag_A")
			self.flagDict[net.EMPIRE_B] = GetObject("EmpireFlag_B")
			self.flagDict[net.EMPIRE_C] = GetObject("EmpireFlag_C")

			self.backGround = GetObject("BackGround")
			self.characterInfoBoard = GetObject("character_board")

		except:
			import exception
			exception.Abort("SelectCharacterWindow.LoadBoardDialog.BindObject")

		for name in self.NameList:
			name.SetAlpha(0.0)

		self.btnStart.SetEvent(ui.__mem_func__(self.StartGame))
		self.btnCreate.SetEvent(ui.__mem_func__(self.CreateCharacter))
		self.btnExit.SetEvent(ui.__mem_func__(self.ExitSelect))



		if NOT_NEED_DELETE_CODE:
			self.btnDelete.SetEvent(ui.__mem_func__(self.PopupDeleteQuestion))
		else:
			self.btnDelete.SetEvent(ui.__mem_func__(self.InputPrivateCode))

		self.btnLeft.SetEvent(ui.__mem_func__(self.DecreaseSlotIndex))
		self.btnRight.SetEvent(ui.__mem_func__(self.IncreaseSlotIndex))

		self.chrRenderer = self.CharacterRenderer()
		self.chrRenderer.SetParent(self.backGround)
		self.chrRenderer.Show()

		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_init_board_quick_save ---
		if app.FAST_LOGIN_CHARACTER_SAVE:
			self.__CreateQuickCharacterSaveButtons()
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_init_board_quick_save ---

		return 1

	# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_quick_save_panel_methods ---
	def __DestroyQuickCharacterSaveButtons(self):
		if not app.FAST_LOGIN_CHARACTER_SAVE:
			return
		for b in getattr(self, "quickSaveButtons", []):
			if b:
				b.Hide()
		self.quickSaveButtons = []
		brd = getattr(self, "quickSaveBoard", None)
		if brd:
			brd.Hide()
		self.quickSaveBoard = None
		self.quickSaveBoardTitle = None
		self.quickSaveBoardLine = None

	def __UpdateQuickSaveBoardPosition(self):
		if not app.FAST_LOGIN_CHARACTER_SAVE:
			return
		brd = getattr(self, "quickSaveBoard", None)
		if not brd:
			return

		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		try:
			self.SetSize(sw, sh)
		except:
			pass

		boardW = brd.GetWidth()
		boardH = brd.GetHeight()
		gap = 8
		margin = 4

		charBoard = getattr(self, "characterInfoBoard", None)
		if charBoard:
			bx, by = charBoard.GetGlobalPosition()
			bh = charBoard.GetHeight()
			posX = bx
			posYBelow = by + bh + gap
			if posYBelow + boardH <= sh - margin:
				posY = posYBelow
			else:
				posY = by - boardH - gap
				try:
					brd.SetTop()
				except:
					pass
		else:
			posX = max(0, int(sw * 65 / 800))
			posY = max(0, int(sh * 220 / 600) + 323 + gap)

		if posX + boardW > sw - margin:
			posX = sw - boardW - margin
		if posY + boardH > sh - margin:
			posY = max(0, sh - boardH - margin)
		if posX < margin:
			posX = margin
		if posY < margin:
			posY = margin

		brd.SetPosition(posX, posY)

	def __CreateQuickCharacterSaveButtons(self):
		if not app.FAST_LOGIN_CHARACTER_SAVE:
			self.quickSaveButtons = []
			return
		import quickcharacter

		self.__DestroyQuickCharacterSaveButtons()
		self.quickSaveButtons = []

		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		try:
			self.SetSize(sw, sh)
		except:
			pass

		ROOT_PATH = "d:/ymir work/ui/public/middle_button_%02d.sub"
		QC_HEADER = 24
		PAD = 6
		GAP = 5
		COL_GAP = 8
		max_fav = quickcharacter.MAX_FAVORITES
		COL_ROWS = (max_fav + 1) // 2
		COL_COUNT = 2
		BOARD_BG_W = 207
		BOARD_BG_H = 180

		_pb = ui.Button()
		_pb.SetParent(self)
		_pb.SetUpVisual(ROOT_PATH % 1)
		_pb.SetOverVisual(ROOT_PATH % 2)
		_pb.SetDownVisual(ROOT_PATH % 3)
		btn_w = _pb.GetWidth()
		btn_h = _pb.GetHeight()
		_pb.Hide()

		content_w = PAD * 2 + COL_COUNT * btn_w + (COL_COUNT - 1) * COL_GAP
		content_h = QC_HEADER + COL_ROWS * btn_h + max(0, COL_ROWS - 1) * GAP + 6
		offset_x = max(0, (BOARD_BG_W - content_w) // 2)
		offset_y = max(0, (BOARD_BG_H - content_h) // 2)

		self.quickSaveBoard = ui.ThinBoard()
		self.quickSaveBoard.SetParent(self)
		self.quickSaveBoard.SetSize(BOARD_BG_W, BOARD_BG_H)
		self.__UpdateQuickSaveBoardPosition()
		self.quickSaveBoard.Show()
		try:
			self.quickSaveBoard.SetTop()
		except:
			pass

		title = ui.TextLine()
		title.SetParent(self.quickSaveBoard)
		title.SetFontName(localeInfo.UI_DEF_FONT)
		title.SetHorizontalAlignCenter()
		title.SetVerticalAlignCenter()
		title.SetPackedFontColor(0xFFffbf00)
		title.SetOutline()
		try:
			title.SetText(localeInfo.LOGIN_QUICK_CHAR_BOARD_TITLE)
		except:
			title.SetText("Karakter kaydetme")
		title.SetPosition(BOARD_BG_W / 2, 12)
		title.Show()
		self.quickSaveBoardTitle = title

		line = ui.Line()
		line.SetParent(self.quickSaveBoard)
		line.SetColor(0xFF777777)
		line.SetSize(BOARD_BG_W - 10, 0)
		line.SetPosition(5, 20)
		line.Show()
		self.quickSaveBoardLine = line

		for idx in xrange(max_fav):
			if idx < COL_ROWS:
				col, row = 0, idx
			else:
				col, row = 1, idx - COL_ROWS
			x = offset_x + PAD + col * (btn_w + COL_GAP)
			y = offset_y + QC_HEADER + row * (btn_h + GAP)
			btn = ui.Button()
			btn.SetParent(self.quickSaveBoard)
			btn.SetUpVisual(ROOT_PATH % 1)
			btn.SetOverVisual(ROOT_PATH % 2)
			btn.SetDownVisual(ROOT_PATH % 3)
			btn.SetPosition(x, y)
			btn.SetText("%d" % (idx + 1))
			btn.SetToolTipText(localeInfo.SELECT_QUICK_CHAR_SAVE_TOOLTIP % (idx + 1))
			btn.SetEvent(ui.__mem_func__(self.__OnClickSaveQuickCharacter), idx)
			btn.Show()
			self.quickSaveButtons.append(btn)

		try:
			if self.quickSaveBoardTitle:
				self.quickSaveBoardTitle.SetTop()
			if self.quickSaveBoardLine:
				self.quickSaveBoardLine.SetTop()
		except:
			pass

	def __OnClickSaveQuickCharacter(self, fav_idx):
		if not app.FAST_LOGIN_CHARACTER_SAVE:
			return
		import quickcharacter

		pid = net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_ID)
		if not pid:
			self.PopupMessage(localeInfo.SELECT_EMPTY_SLOT)
			return
		name = net.GetAccountCharacterSlotDataString(self.slot, net.ACCOUNT_CHARACTER_SLOT_NAME)
		acc = self.stream.id
		if not acc:
			acc = net.GetLoginID()
		pwd = getattr(self.stream, "pwd", None)
		quickcharacter.SaveFavorite(fav_idx, acc, self.slot, name, pwd)
		self.PopupMessage(localeInfo.LOGIN_QUICK_CHAR_SAVED)
	# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_quick_save_panel_methods ---

	def MakeCharacter(self, index, id, name, race, form, hair, acce =0):
		if 0 == id:
			return

		chr.CreateInstance(index)
		chr.SelectInstance(index)
		chr.SetVirtualID(index)
		chr.SetNameString(name)

		chr.SetRace(race)
		chr.SetArmor(form)
		chr.SetHair(hair)

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			chr.SetAcce(acce)

		chr.Refresh()
		chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
		chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)

		chr.SetRotation(0.0)

	## Manage Character
	def StartGame(self):

		if self.sendedChangeNamePacket:
			return

		if self.changeNameFlag:
			self.OpenChangeNameDialog()
			return

		if -1 != self.startIndex:
			return

		if musicInfo.selectMusic != "":
			snd.FadeLimitOutMusic("BGM/"+musicInfo.selectMusic, systemSetting.GetMusicVolume()*0.05)

		self.btnStart.SetUp()
		self.btnCreate.SetUp()
		self.btnDelete.SetUp()
		self.btnExit.SetUp()
		self.btnLeft.SetUp()
		self.btnRight.SetUp()

		self.btnStart.Disable()
		self.btnCreate.Disable()
		self.btnDelete.Disable()
		self.btnExit.Disable()
		self.btnLeft.Disable()
		self.btnRight.Disable()
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_startgame_disable_quick_btns ---
		if app.FAST_LOGIN_CHARACTER_SAVE:
			for b in self.quickSaveButtons:
				if b:
					b.Disable()
		# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_startgame_disable_quick_btns ---
		self.dlgQuestion.Hide()

		self.stream.SetCharacterSlot(self.slot)

		self.startIndex = self.slot
		self.startReservingTime = app.GetTime()

		for i in xrange(self.SLOT_COUNT):

			if False == chr.HasInstance(i):
				continue

			chr.SelectInstance(i)

			if i == self.slot:
				self.slot=self.slot
				chr.PushOnceMotion(chr.MOTION_INTRO_SELECTED, 0.1)
				continue

			chr.PushOnceMotion(chr.MOTION_INTRO_NOT_SELECTED, 0.1)

	def OpenChangeNameDialog(self):
		import uiCommon
		nameInputBoard = uiCommon.InputDialogWithDescription()
		nameInputBoard.SetTitle(localeInfo.SELECT_CHANGE_NAME_TITLE)
		nameInputBoard.SetAcceptEvent(ui.__mem_func__(self.AcceptInputName))
		nameInputBoard.SetCancelEvent(ui.__mem_func__(self.CancelInputName))
		nameInputBoard.SetMaxLength(chr.PLAYER_NAME_MAX_LEN)
		nameInputBoard.SetBoardWidth(200)
		nameInputBoard.SetDescription(localeInfo.SELECT_INPUT_CHANGING_NAME)
		nameInputBoard.Open()
		nameInputBoard.slot = self.slot
		self.nameInputBoard = nameInputBoard

	def OnChangeName(self, id, name):
		self.SelectSlot(id)
		self.sendedChangeNamePacket = False
		self.PopupMessage(localeInfo.SELECT_CHANGED_NAME)

	def AcceptInputName(self):
		changeName = self.nameInputBoard.GetText()
		if not changeName:
			return

		self.sendedChangeNamePacket = True
		net.SendChangeNamePacket(self.nameInputBoard.slot, changeName)
		return self.CancelInputName()

	def CancelInputName(self):
		self.nameInputBoard.Close()
		self.nameInputBoard = None
		return True

	def OnCreateFailure(self, type):
		self.sendedChangeNamePacket = False
		if 0 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_STRANGE_NAME)
		elif 1 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_ALREADY_EXIST_NAME)
		elif 100 == type:
			self.PopupMessage(localeInfo.SELECT_CHANGE_FAILURE_STRANGE_INDEX)

	def CreateCharacter(self):
		id = self.GetCharacterSlotID(self.slot)
		if 0==id:
			self.stream.SetCharacterSlot(self.slot)

			EMPIRE_MODE = 1

			if EMPIRE_MODE:
				if self.__AreAllSlotEmpty():
					self.stream.SetReselectEmpirePhase()
				else:
					self.stream.SetCreateCharacterPhase()

			else:
				self.stream.SetCreateCharacterPhase()

	def __AreAllSlotEmpty(self):
		for iSlot in xrange(self.SLOT_COUNT):
			if 0!=net.GetAccountCharacterSlotDataInteger(iSlot, net.ACCOUNT_CHARACTER_SLOT_ID):
				return 0
		return 1

	def PopupDeleteQuestion(self):
		id = self.GetCharacterSlotID(self.slot)
		if 0 == id:
			return

		self.dlgQuestion.Show()
		self.dlgQuestion.SetTop()

	def RequestDeleteCharacter(self):
		self.dlgQuestion.Hide()

		id = self.GetCharacterSlotID(self.slot)
		if 0 == id:
			self.PopupMessage(localeInfo.SELECT_EMPTY_SLOT)
			return

		net.SendDestroyCharacterPacket(self.slot, "1234567")
		self.PopupMessage(localeInfo.SELECT_DELEING)

	def InputPrivateCode(self):

		import uiCommon
		privateInputBoard = uiCommon.InputDialogWithDescription()
		privateInputBoard.SetTitle(localeInfo.INPUT_PRIVATE_CODE_DIALOG_TITLE)
		privateInputBoard.SetAcceptEvent(ui.__mem_func__(self.AcceptInputPrivateCode))
		privateInputBoard.SetCancelEvent(ui.__mem_func__(self.CancelInputPrivateCode))

		if ENABLE_ENGNUM_DELETE_CODE:
			pass
		else:
			privateInputBoard.SetNumberMode()

		privateInputBoard.SetSecretMode()
		privateInputBoard.SetMaxLength(7)

		privateInputBoard.SetBoardWidth(250)
		privateInputBoard.SetDescription(localeInfo.INPUT_PRIVATE_CODE_DIALOG_DESCRIPTION)
		privateInputBoard.Open()
		self.privateInputBoard = privateInputBoard

	def AcceptInputPrivateCode(self):
		privateCode = self.privateInputBoard.GetText()
		if not privateCode:
			return

		id = self.GetCharacterSlotID(self.slot)
		if 0 == id:
			self.PopupMessage(localeInfo.SELECT_EMPTY_SLOT)
			return

		net.SendDestroyCharacterPacket(self.slot, privateCode)
		self.PopupMessage(localeInfo.SELECT_DELEING)

		self.CancelInputPrivateCode()
		return True

	def CancelInputPrivateCode(self):
		self.privateInputBoard = None
		return True

	def OnDeleteSuccess(self, slot):
		self.PopupMessage(localeInfo.SELECT_DELETED)
		self.DeleteCharacter(slot)

	def OnDeleteFailure(self):
		self.PopupMessage(localeInfo.SELECT_CAN_NOT_DELETE)

	def DeleteCharacter(self, index):
		chr.DeleteInstance(index)
		self.SelectSlot(self.slot)

	def ExitSelect(self):
		if self.stream:
			# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN introselect_exit_clear_quick_stream ---
			self.stream.hideSelectUiForAutoLogin = 0
			self.stream.quietLoadingUiForQuickLogin = 0
			# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END introselect_exit_clear_quick_stream ---
		self.dlgQuestion.Hide()

		if LEAVE_BUTTON_FOR_POTAL:
			if app.loggined:
				self.stream.SetPhaseWindow(0)
			else:
				self.stream.setloginphase()
		else:
			self.stream.SetLoginPhase()

		self.Hide()

	def GetSlotIndex(self):
		return self.slot

	def DecreaseSlotIndex(self):
		slotIndex = (self.GetSlotIndex() - 1 + self.SLOT_COUNT) % self.SLOT_COUNT
		self.SelectSlot(slotIndex)

	def IncreaseSlotIndex(self):
		slotIndex = (self.GetSlotIndex() + 1) % self.SLOT_COUNT
		self.SelectSlot(slotIndex)

	def SelectSlot(self, index):

		if index < 0:
			return
		if index >= self.SLOT_COUNT:
			return

		self.slot = index

		chr.SelectInstance(self.slot)

		for i in xrange(self.CHARACTER_TYPE_COUNT):
			self.destNameAlpha[i] = 0.0

		for i in xrange(self.SLOT_COUNT):
			self.destRotation[(i+self.slot)%self.SLOT_COUNT] = self.SLOT_ROTATION[i]

		self.destGauge = [0.0, 0.0, 0.0, 0.0]

		id=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_ID)
		if 0 != id:

			self.btnStart.Show()
			self.btnDelete.Show()
			self.btnCreate.Hide()

			playTime=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_PLAYTIME)
			level=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_LEVEL)
			race=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_RACE)
			valueHTH=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_HTH)
			valueINT=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_INT)
			valueSTR=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_STR)
			valueDEX=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_DEX)
			name=net.GetAccountCharacterSlotDataString(self.slot, net.ACCOUNT_CHARACTER_SLOT_NAME)
			guildID=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_GUILD_ID)
			guildName=net.GetAccountCharacterSlotDataString(self.slot, net.ACCOUNT_CHARACTER_SLOT_GUILD_NAME)
			self.changeNameFlag=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_CHANGE_NAME_FLAG)

			job = chr.RaceToJob(race)
			if job >= 0 and job < self.CHARACTER_TYPE_COUNT:
				self.destNameAlpha[job] = 1.0

			self.CharacterName.SetText(name)
			self.CharacterLevel.SetText(str(level))

			playHour = playTime / 60
			playMinute = playTime % 60
			self.PlayTime.SetText("%d saat %d dakika" % (playHour, playMinute))
			self.CharacterHTH.SetText(str(valueHTH))
			self.CharacterINT.SetText(str(valueINT))
			self.CharacterSTR.SetText(str(valueSTR))
			self.CharacterDEX.SetText(str(valueDEX))

			if guildName:
				self.GuildName.SetText(guildName)
			else:
				self.GuildName.SetText(localeInfo.SELECT_NOT_JOIN_GUILD)

			statesSummary = float(valueHTH + valueINT + valueSTR + valueDEX)
			if statesSummary > 0.0:
				self.destGauge =	[
										float(valueHTH) / statesSummary,
										float(valueINT) / statesSummary,
										float(valueSTR) / statesSummary,
										float(valueDEX) / statesSummary
									]

		else:

			self.InitCharacterBoard()

	def InitCharacterBoard(self):

		self.btnStart.Hide()
		self.btnDelete.Hide()
		self.btnCreate.Show()

		self.CharacterName.SetText("")
		self.CharacterLevel.SetText("")
		self.PlayTime.SetText("")
		self.CharacterHTH.SetText("")
		self.CharacterINT.SetText("")
		self.CharacterSTR.SetText("")
		self.CharacterDEX.SetText("")
		self.GuildName.SetText(localeInfo.SELECT_NOT_JOIN_GUILD)

	## Event
	def OnIMEReturn(self):
		id = net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_ID)
		if 0 == id:
			self.CreateCharacter()
		else:
			self.StartGame()
		return True

	def OnPressEscapeKey(self):
		self.ExitSelect()
		return True

	def OnKeyDown(self, key):

		for i in xrange(self.SLOT_COUNT):
			if 2+i == key:
				self.SelectSlot(i)

		if 203 == key:
			self.slot = (self.GetSlotIndex() - 1 + self.SLOT_COUNT) % self.SLOT_COUNT
			self.SelectSlot(self.slot)
		if 205 == key:
			self.slot = (self.GetSlotIndex() + 1) % self.SLOT_COUNT
			self.SelectSlot(self.slot)

		return True

	def OnUpdate(self):
		chr.Update()

		if app.FAST_LOGIN_CHARACTER_SAVE and getattr(self, "quickSaveBoard", None):
			sw = wndMgr.GetScreenWidth()
			sh = wndMgr.GetScreenHeight()
			last = getattr(self, "_quickSaveLastScreen", None)
			if last != (sw, sh):
				self._quickSaveLastScreen = (sw, sh)
				self.__UpdateQuickSaveBoardPosition()

		for i in xrange(4):
			self.curGauge[i] += (self.destGauge[i] - self.curGauge[i]) / 10.0
			if abs(self.curGauge[i] - self.destGauge[i]) < 0.005:
				self.curGauge[i] = self.destGauge[i]
			self.GaugeList[i].SetPercentage(self.curGauge[i], 1.0)

		for i in xrange(self.CHARACTER_TYPE_COUNT):
			self.curNameAlpha[i] += (self.destNameAlpha[i] - self.curNameAlpha[i]) / 10.0
			self.NameList[i].SetAlpha(self.curNameAlpha[i])

		for i in xrange(self.SLOT_COUNT):

			if False == chr.HasInstance(i):
				continue

			chr.SelectInstance(i)

			distance = 50.0
			rotRadian = self.curRotation[i] * (math.pi*2) / 360.0
			x = distance*math.sin(rotRadian) + distance*math.cos(rotRadian)
			y = distance*math.cos(rotRadian) - distance*math.sin(rotRadian)
			chr.SetPixelPosition(int(x), int(y), 30)

			#####

			dir = app.GetRotatingDirection(self.destRotation[i], self.curRotation[i])
			rot = app.GetDegreeDifference(self.destRotation[i], self.curRotation[i])

			if app.DEGREE_DIRECTION_RIGHT == dir:
				self.curRotation[i] += rot / 10.0
			elif app.DEGREE_DIRECTION_LEFT == dir:
				self.curRotation[i] -= rot / 10.0

			self.curRotation[i] = (self.curRotation[i] + 360.0) % 360.0

		#######################################################
		if -1 != self.startIndex:

			## Temporary
			if app.GetTime() - self.startReservingTime > constInfo.SELECT_CHAR_NO_DELAY:
				if False == self.openLoadingFlag:
					chrSlot=self.stream.GetCharacterSlot()
					net.DirectEnter(chrSlot)
					self.openLoadingFlag = True

					playTime=net.GetAccountCharacterSlotDataInteger(self.slot, net.ACCOUNT_CHARACTER_SLOT_PLAYTIME)

					import player
					player.SetPlayTime(playTime)
					import chat
					chat.Clear()
			## Temporary
		#######################################################

	def EmptyFunc(self):
		pass

	def PopupMessage(self, msg, func=0):
		if not func:
			func=self.EmptyFunc

		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)

	def OnPressExitKey(self):
		self.ExitSelect()
		return True
