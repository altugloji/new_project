import dbg
import app
import net
import ui
import ime
import snd
import wndMgr
import musicInfo
import serverInfo
import systemSetting
import ServerStateChecker
import localeInfo
import constInfo
import uiCommon
import time
import serverCommandParser
import ime
import uiScriptLocale

from constInfo import ENABLE_MAP_INTERACTIVE_LOGIN
if ENABLE_MAP_INTERACTIVE_LOGIN:
	import background
	import grp

LOGIN_DELAY_SEC = 0.0
SKIP_LOGIN_PHASE = False
SKIP_LOGIN_PHASE_SUPPORT_CHANNEL = False
FULL_BACK_IMAGE = False

LANG_DROPDOWN_LIST_PAD = 6
LANG_DROPDOWN_ROW_BTN_H = 22
LANG_DROPDOWN_ROW_GAP = 8

LOGIN_FOOTER_MARGIN_X = 30
LOGIN_FOOTER_MARGIN_BOTTOM = 30
LOGIN_FOOTER_BTN_GAP = 8

VIRTUAL_KEYBOARD_NUM_KEYS = 46
VIRTUAL_KEYBOARD_RAND_KEY = True

def Suffle(src):
	if VIRTUAL_KEYBOARD_RAND_KEY:
		items = [item for item in src]

		itemCount = len(items)
		for oldPos in xrange(itemCount):
			newPos = app.GetRandom(0, itemCount-1)
			items[newPos], items[oldPos] = items[oldPos], items[newPos]

		return "".join(items)
	else:
		return src

def IsFullBackImage():
	global FULL_BACK_IMAGE
	return FULL_BACK_IMAGE

def IsLoginDelay():
	global LOGIN_DELAY_SEC
	if LOGIN_DELAY_SEC > 0.0:
		return True
	else:
		return False

def GetLoginDelay():
	global LOGIN_DELAY_SEC
	return LOGIN_DELAY_SEC

app.SetGuildMarkPath("test")

class ConnectingDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadDialog()
		self.eventTimeOver = lambda *arg: None
		self.eventExit = lambda *arg: None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/ConnectingDialog.py")

			self.board = self.GetChild("board")
			self.message = self.GetChild("message")
			self.countdownMessage = self.GetChild("countdown_message")

		except:
			import exception
			exception.Abort("ConnectingDialog.LoadDialog.BindObject")

	def Open(self, waitTime):
		curTime = time.clock()
		self.endTime = curTime + waitTime

		self.Lock()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Unlock()
		self.Hide()

	@ui.WindowDestroy
	def Destroy(self):
		self.Hide()
		self.ClearDictionary()

	def SetText(self, text):
		self.message.SetText(text)

	def SetCountDownMessage(self, waitTime):
		self.countdownMessage.SetText("%.0f%s" % (waitTime, localeInfo.SECOND))

	def SAFE_SetTimeOverEvent(self, event):
		self.eventTimeOver = ui.__mem_func__(event)

	def SAFE_SetExitEvent(self, event):
		self.eventExit = ui.__mem_func__(event)

	def OnUpdate(self):
		lastTime = max(0, self.endTime - time.clock())
		if 0 == lastTime:
			self.Close()
			self.eventTimeOver()
		else:
			self.SetCountDownMessage(self.endTime - time.clock())

	def OnPressExitKey(self):
		#self.eventExit()
		return True

class LoginWindow(ui.ScriptWindow):

	IS_TEST = net.IsTest()

	if ENABLE_MAP_INTERACTIVE_LOGIN:
		# (base_x + off_x, base_y + off_y, dis, pit, rot, height, snow)
		MAP_ENVIRONMENTS = (
			(409600+60000, 896000+57500, 2500.0, 5.0, 105.0, 40.0, 0),		#a1
			(307200+53600, 819200+58400, 2500.0, 5.0, 255.0, 40.0, 0),		#a3
			(0+62400, 102400+65500, 2500.0, 5.0, 10.0, 40.0, 0),			#b1
			(102400+40600, 204800+32900, 2500.0, 5.0, 110.0, 40.0, 0),		#b3
			(921600+37000, 204800+58900, 2500.0, 5.0, 155.0, 40.0, 0),		#c1
			(819200+42000, 204800+39000, 2500.0, 5.0, 125.0, 40.0, 0),		#c3
			(870400+26000, 0+21500, 2500.0, 5.0, 225.0, 40.0, 0),			#oxevent
			(204800+27800, 486400+34800, 2500.0, 10.0, 30.0, 40.0, 0),		#n_desert_01
			(1049600+56600, 0+53600, 2500.0, 5.0, 90.0, 40.0, 0),			#trent02
			(256000+82900, 665600+88500, 2500.0, 5.0, 310.0, 40.0, 0),		#a2
			(358400+75400, 153600+17100, 2500.0, 10.0, 343.0, 40.0, 1),		#n_snowm_01
			(588800+12900, 614400+92900, 2500.0, 5.0, 90.0, 40.0, 0),		#n_flame_01
			(1024000+80800, 1664000+119900, 2500.0, 5.0, 175.0, 40.0, 0),	#CapeDragonHead
			(1049600+7600, 1510400+111700, 2500.0, 5.0, 12.0, 40.0, 0),		#BayBlackSand
			(1126400+49500, 1510400+73900, 2500.0, 5.0, 360.0, 40.0, 0),	#Mt_Thunder
			(1177600+100200, 1664000+77300, 2500.0, -15.0, 1.0, 40.0, 0),	#dawnmistwood
			(819200+66240, 51200+51200, 2500.0, 5.0, 300.0, 40.0, 0),		#monkeydungeon
		)

	def __init__(self, stream):
		print("NEW LOGIN WINDOW ----------------------------------------------------------------------------")
		ui.ScriptWindow.__init__(self)
		net.SetPhaseWindow(net.PHASE_WINDOW_LOGIN, self)
		net.SetAccountConnectorHandler(self)

		self.lastLoginTime = 0
		self.inputDialog = None
		self.connectingDialog = None
		self.stream=stream
		self.isNowCountDown=False
		self.isStartError=False

		self.xServerBoard = 0
		self.yServerBoard = 0

		self.loadingImage = None

		self.virtualKeyboard = None
		self.virtualKeyboardMode = "ALPHABET"
		self.virtualKeyboardIsUpper = False
		
		if app.__BL_MULTI_LANGUAGE_PREMIUM__:
			self.language_list = []
			self.language_board = None
			self.language_popup = None
			self.lang_drop_list_open = False
			self.lang_title_text = None
			self.lang_header_btn = None
			self.lang_header_flag = None
			self.lang_header_arrow = None
			self.lang_header_name_text = None
			self.lang_list_board = None
			self.lang_row_entries = []
			self.__LoadLocaleListFile()
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.anon_mode_board = None
			self.anon_mode_text = None
			self.anon_mode_checkbox_bg = None
			self.anon_mode_checkbox = None

		# @fixme001 BEGIN (timeOutMsg and timeOutOk undefined)
		self.timeOutMsg = False
		self.timeOutOk = False
		# @fixme001 END

		self.login_footer_buttons = []

	def __del__(self):
		net.ClearPhaseWindow(net.PHASE_WINDOW_LOGIN, self)
		net.SetAccountConnectorHandler(0)
		ui.ScriptWindow.__del__(self)
		print("---------------------------------------------------------------------------- DELETE LOGIN WINDOW")

	def Open(self):
		ServerStateChecker.Create(self)

		print("LOGIN WINDOW OPEN ----------------------------------------------------------------------------")

		self.loginFailureMsgDict={
			#"DEFAULT" : localeInfo.LOGIN_FAILURE_UNKNOWN,

			"ALREADY"	: localeInfo.LOGIN_FAILURE_ALREAY,
			"NOID"		: localeInfo.LOGIN_FAILURE_NOT_EXIST_ID,
			"WRONGPWD"	: localeInfo.LOGIN_FAILURE_WRONG_PASSWORD,
			"FULL"		: localeInfo.LOGIN_FAILURE_TOO_MANY_USER,
			"SHUTDOWN"	: localeInfo.LOGIN_FAILURE_SHUTDOWN,
			"REPAIR"	: localeInfo.LOGIN_FAILURE_REPAIR_ID,
			"BLOCK"		: localeInfo.LOGIN_FAILURE_BLOCK_ID,
			"WRONGMAT"	: localeInfo.LOGIN_FAILURE_WRONG_MATRIX_CARD_NUMBER,
			"QUIT"		: localeInfo.LOGIN_FAILURE_WRONG_MATRIX_CARD_NUMBER_TRIPLE,
			"BESAMEKEY"	: localeInfo.LOGIN_FAILURE_BE_SAME_KEY,
			"NOTAVAIL"	: localeInfo.LOGIN_FAILURE_NOT_AVAIL,
			"NOBILL"	: localeInfo.LOGIN_FAILURE_NOBILL,
			"BLKLOGIN"	: localeInfo.LOGIN_FAILURE_BLOCK_LOGIN,
			"WEBBLK"	: localeInfo.LOGIN_FAILURE_WEB_BLOCK,
			"BADSCLID"	: localeInfo.LOGIN_FAILURE_WRONG_SOCIALID,
			"AGELIMIT"	: localeInfo.LOGIN_FAILURE_SHUTDOWN_TIME,
		}

		self.loginFailureFuncDict = {
			"WRONGPWD"	: self.__DisconnectAndInputPassword,
			"QUIT"		: app.Exit,
		}

		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		self.SetWindowName("LoginWindow")

		if not self.__LoadScript(uiScriptLocale.LOCALE_UISCRIPT_PATH + "LoginWindow.py"):
			dbg.TraceError("LoginWindow.Open - __LoadScript Error")
			return

		self.__LoadLoginInfo("loginInfo.xml")

		if app.loggined:
			self.loginFailureFuncDict = {
			"WRONGPWD"	: app.Exit,
			"WRONGMAT"	: app.Exit,
			"QUIT"		: app.Exit,
			}

		if musicInfo.loginMusic != "":
			snd.SetMusicVolume(systemSetting.GetMusicVolume())
			snd.FadeInMusic("BGM/"+musicInfo.loginMusic)

		snd.SetSoundVolume(systemSetting.GetSoundVolume())

		# pevent key "[" "]"
		ime.AddExceptKey(91)
		ime.AddExceptKey(93)

		self.Show()

		global SKIP_LOGIN_PHASE
		if SKIP_LOGIN_PHASE:
			if self.isStartError:
				self.connectBoard.Hide()
				self.loginBoard.Hide()
				if constInfo.ENABLE_SAVE_ACCOUNT:
					self.saveAccountBoard.Hide()
				self.serverBoard.Hide()
				self.PopupNotifyMessage(localeInfo.LOGIN_CONNECT_FAILURE, self.__ExitGame)
				return

			if self.loginInfo:
				self.serverBoard.Hide()
			else:
				self.__RefreshServerList()
				self.__OpenServerBoard()
		else:
			connectingIP = self.stream.GetConnectAddr()
			if connectingIP:
				# @fixme021 BEGIN (instead of self.__OpenLoginBoard)
				self.__RefreshServerList()
				self.__OpenServerBoard()
				self.__OnClickSelectServerButton()
				# @fixme021 END
				if IsFullBackImage():
					self.GetChild("bg1").Hide()
					self.GetChild("bg2").Show()

			else:
				self.__RefreshServerList()
				self.__OpenServerBoard()

		if ENABLE_MAP_INTERACTIVE_LOGIN:
			self.LoadMap()

		app.ShowCursor()

	if ENABLE_MAP_INTERACTIVE_LOGIN:
		def LoadMap(self):
			env = self.MAP_ENVIRONMENTS[app.GetRandom(0, len(self.MAP_ENVIRONMENTS) - 1)]
			x, y, dis, pit, rot, height, snow = env
			app.SetCamera(dis, pit, rot, height)
			net.Warp(x, y)

			background.SetViewDistanceSet(background.DISTANCE0, 25600)
			background.SelectViewDistanceNum(background.DISTANCE0)

			if snow:
				background.EnableSnow(1)

			# From 21:00 to 5:59 the environment will set to night. Remove this part if you don't need it.
			h = time.localtime()[3]
			if h <= 5 or h >= 21:
				background.RegisterEnvironmentData(1, constInfo.ENVIRONMENT_NIGHT)
				background.SetEnvironmentData(1)
			else:
				background.SetEnvironmentData(0)

			self.GetChild("bg1").Hide()
			self.GetChild("bg2").Hide()

		def OnRender(self):
			if ENABLE_MAP_INTERACTIVE_LOGIN:
				app.RenderGame()
				grp.PopState()
				grp.SetInterfaceRenderState()

	def Close(self):

		if self.connectingDialog:
			self.connectingDialog.Close()
		self.connectingDialog = None

		ServerStateChecker.Initialize(self)

		print("---------------------------------------------------------------------------- CLOSE LOGIN WINDOW ")
		#
		#
		if musicInfo.loginMusic != "" and musicInfo.selectMusic != "":
			snd.FadeOutMusic("BGM/"+musicInfo.loginMusic)

		self.idEditLine.SetTabEvent(0)
		self.idEditLine.SetReturnEvent(0)
		self.pwdEditLine.SetReturnEvent(0)
		self.pwdEditLine.SetTabEvent(0)

		self.connectBoard = None
		self.loginBoard = None
		if constInfo.ENABLE_SAVE_ACCOUNT:
			self.saveAccountBoard = None
		self.idEditLine = None
		self.pwdEditLine = None
		self.inputDialog = None
		self.connectingDialog = None
		self.loadingImage = None
		self.login_footer_buttons = []
		if app.__BL_MULTI_LANGUAGE_PREMIUM__:
			self.language_list = []
			self.language_board = None
			self.language_popup = None
			self.lang_drop_list_open = False
			self.lang_title_text = None
			self.lang_header_btn = None
			self.lang_header_flag = None
			self.lang_header_arrow = None
			self.lang_header_name_text = None
			self.lang_list_board = None
			self.lang_row_entries = []
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.anon_mode_board = None
			self.anon_mode_text = None
			self.anon_mode_checkbox_bg = None
			self.anon_mode_checkbox = None
	
		self.serverBoard				= None
		self.serverList					= None
		self.channelList				= None

		self.VIRTUAL_KEY_ALPHABET_LOWERS = None
		self.VIRTUAL_KEY_ALPHABET_UPPERS = None
		self.VIRTUAL_KEY_SYMBOLS = None
		self.VIRTUAL_KEY_NUMBERS = None

		# VIRTUAL_KEYBOARD_BUG_FIX
		if self.virtualKeyboard:
			for keyIndex in xrange(0, VIRTUAL_KEYBOARD_NUM_KEYS+1):
				key = self.GetChild2("key_%d" % keyIndex)
				if key:
					key.SetEvent(None)

			self.GetChild("key_space").SetEvent(None)
			self.GetChild("key_backspace").SetEvent(None)
			self.GetChild("key_enter").SetEvent(None)
			self.GetChild("key_shift").SetToggleDownEvent(None)
			self.GetChild("key_shift").SetToggleUpEvent(None)
			self.GetChild("key_at").SetToggleDownEvent(None)
			self.GetChild("key_at").SetToggleUpEvent(None)

			self.virtualKeyboard = None

		self.KillFocus()
		self.Hide()

		self.stream.popupWindow.Close()
		self.loginFailureFuncDict=None

		ime.ClearExceptKey()

		app.HideCursor()
		if ENABLE_MAP_INTERACTIVE_LOGIN:
			background.Destroy()

	def __SaveChannelInfo(self):
		try:
			file=old_open("channel.inf", "w")
			file.write("%d %d %d" % (self.__GetServerID(), self.__GetChannelID(), self.__GetRegionID()))
		except:
			print("LoginWindow.__SaveChannelInfo - SaveError")

	def __LoadChannelInfo(self):
		try:
			file=old_open("channel.inf")
			lines=file.readlines()

			if len(lines)>0:
				tokens=lines[0].split()

				selServerID=int(tokens[0])
				selChannelID=int(tokens[1])

				if len(tokens) == 3:
					regionID = int(tokens[2])

				return regionID, selServerID, selChannelID

		except:
			print("LoginWindow.__LoadChannelInfo - OpenError")
			return -1, -1, -1

	def __ExitGame(self):
		app.Exit()

	def SetIDEditLineFocus(self):
		if self.idEditLine != None:
			self.idEditLine.SetFocus()

	def SetPasswordEditLineFocus(self):
		if constInfo.ENABLE_CLEAN_DATA_IF_FAIL_LOGIN:
			if self.idEditLine != None:
				self.idEditLine.SetText("")
				self.idEditLine.SetFocus()

			if self.pwdEditLine != None:
				self.pwdEditLine.SetText("")
		else:
			if self.pwdEditLine != None:
				self.pwdEditLine.SetFocus()

	def OnEndCountDown(self):
		self.isNowCountDown = False
		self.timeOutMsg = False
		self.OnConnectFailure()

	def OnConnectFailure(self):

		if self.isNowCountDown:
			return

		snd.PlaySound("sound/ui/loginfail.wav")

		if self.connectingDialog:
			self.connectingDialog.Close()
		self.connectingDialog = None

		if app.loggined:
			self.PopupNotifyMessage(localeInfo.LOGIN_CONNECT_FAILURE, self.__ExitGame)
		elif self.timeOutMsg:
			self.PopupNotifyMessage(localeInfo.LOGIN_FAILURE_TIMEOUT, self.SetPasswordEditLineFocus)
		else:
			self.PopupNotifyMessage(localeInfo.LOGIN_CONNECT_FAILURE, self.SetPasswordEditLineFocus)

	def OnHandShake(self):
		if not IsLoginDelay():
			snd.PlaySound("sound/ui/loginok.wav")
			self.PopupDisplayMessage(localeInfo.LOGIN_CONNECT_SUCCESS)

	def OnLoginStart(self):
		if not IsLoginDelay():
			self.PopupDisplayMessage(localeInfo.LOGIN_PROCESSING)

	def OnLoginFailure(self, error):
		if self.connectingDialog:
			self.connectingDialog.Close()
		self.connectingDialog = None

		try:
			loginFailureMsg = self.loginFailureMsgDict[error]
		except KeyError:
			loginFailureMsg = localeInfo.LOGIN_FAILURE_UNKNOWN + error


		loginFailureFunc=self.loginFailureFuncDict.get(error, self.SetPasswordEditLineFocus)

		if app.loggined:
			self.PopupNotifyMessage(loginFailureMsg, self.__ExitGame)
		else:
			self.PopupNotifyMessage(loginFailureMsg, loginFailureFunc)

		snd.PlaySound("sound/ui/loginfail.wav")

	def __DisconnectAndInputID(self):
		if self.connectingDialog:
			self.connectingDialog.Close()
		self.connectingDialog = None

		self.SetIDEditLineFocus()
		net.Disconnect()

	def __DisconnectAndInputPassword(self):
		if self.connectingDialog:
			self.connectingDialog.Close()
		self.connectingDialog = None

		self.SetPasswordEditLineFocus()
		net.Disconnect()

	if constInfo.ENABLE_SAVE_ACCOUNT:
		def SAB_LoadAccountData(self):
			if constInfo.SAB.storeType == constInfo.SAB.ST_CACHE:
				return
			for idx in xrange(constInfo.SAB.slotCount):
				if constInfo.SAB.storeType == constInfo.SAB.ST_REGISTRY:
					id = constInfo.GetWinRegKeyValue(constInfo.SAB.regPath, constInfo.SAB.regName % (idx, constInfo.SAB.regValueId))
					pwd = constInfo.GetWinRegKeyValue(constInfo.SAB.regPath, constInfo.SAB.regName % (idx, constInfo.SAB.regValuePwd))
					if id and pwd:
						self.SAB_SetAccountData(idx, (id, pwd))
				elif constInfo.SAB.storeType == constInfo.SAB.ST_FILE:
					(id, pwd) = constInfo.GetJsonSABData(idx)
					if id and pwd:
						self.SAB_SetAccountData(idx, (id, pwd))

		def SAB_SaveAccountData(self):
			if constInfo.SAB.storeType == constInfo.SAB.ST_CACHE:
				return
			for idx in xrange(constInfo.SAB.slotCount):
				if constInfo.SAB.storeType == constInfo.SAB.ST_REGISTRY:
					_tSlot = self.SAB_GetAccountData(idx)
					if _tSlot:
						(id, pwd) = _tSlot
						constInfo.SetWinRegKeyValue(constInfo.SAB.regPath, constInfo.SAB.regName % (idx, constInfo.SAB.regValueId), id)
						constInfo.SetWinRegKeyValue(constInfo.SAB.regPath, constInfo.SAB.regName % (idx, constInfo.SAB.regValuePwd), pwd)
					else:
						constInfo.DelWinRegKeyValue(constInfo.SAB.regPath, constInfo.SAB.regName % (idx, constInfo.SAB.regValueId))
						constInfo.DelWinRegKeyValue(constInfo.SAB.regPath, constInfo.SAB.regName % (idx, constInfo.SAB.regValuePwd))
				elif constInfo.SAB.storeType == constInfo.SAB.ST_FILE:
					_tSlot = self.SAB_GetAccountData(idx)
					if _tSlot:
						constInfo.SetJsonSABData(idx, _tSlot)
					else:
						constInfo.DelJsonSABData(idx)

		def SAB_DelAccountData(self, slot):
			if constInfo.SAB.accData.get(slot):
				del constInfo.SAB.accData[slot]

		def SAB_GetAccountData(self, slot):
			return constInfo.SAB.accData.get(slot)

		def SAB_SetAccountData(self, slot, data):
			constInfo.SAB.accData[slot] = data

		def SAB_BtnRearrange(self):
			def tooltipArrange(_btnObj):
				_tMexTip = "Account ID: %s" % id
				_btnObj.SetToolTipText(_tMexTip)
				if _btnObj.ToolTipText:
					_btnObj.ToolTipText.SetPackedFontColor(0xff66FFFF)
			## def code
			GetObject=self.GetChild
			SetObject=self.InsertChild
			## button names
			btnNameSave = constInfo.SAB.btnName["Save"]
			btnNameAccess = constInfo.SAB.btnName["Access"]
			btnNameRemove = constInfo.SAB.btnName["Remove"]
			## rearrange code
			for idx in xrange(constInfo.SAB.slotCount):
				_tSlot = self.SAB_GetAccountData(idx)
				# button objects
				btnObjSave = GetObject(btnNameSave % idx)
				btnObjAccess = GetObject(btnNameAccess % idx)
				btnObjRemove = GetObject(btnNameRemove % idx)
				if _tSlot:
					(id, pwd) = _tSlot
					btnObjSave.Hide()
					btnObjAccess.Show()
					btnObjRemove.Show()
					btnObjAccess.SetText(uiScriptLocale.SAVE_ACCOUNT_CONNECT2.format(idx+1, id))
				else:
					btnObjSave.Show()
					btnObjAccess.Hide()
					btnObjRemove.Hide()
			# done

		def SAB_Click_Save(self, slot):
			if slot >= constInfo.SAB.slotCount:
				return
			## def code
			GetObject=self.GetChild
			SetObject=self.InsertChild
			## button stuff
			_tmpName = constInfo.SAB.btnName["Save"] % slot
			_tmpObj = GetObject(_tmpName)
			## code stuff
			try:
				id = self.idEditLine.GetText()
				pwd = self.pwdEditLine.GetText()

				if len(id)==0:
					self.PopupNotifyMessage(localeInfo.LOGIN_INPUT_ID, self.SetIDEditLineFocus)
					return

				if len(pwd)==0:
					self.PopupNotifyMessage(localeInfo.LOGIN_INPUT_PASSWORD, self.SetPasswordEditLineFocus)
					return
			except:
				return
			self.SAB_SetAccountData(slot, (id,pwd))
			self.SAB_SaveAccountData()
			## rearrange stuff
			self.SAB_BtnRearrange()

		def SAB_Click_Access(self, slot):
			if slot >= constInfo.SAB.slotCount:
				return
			## def code
			GetObject=self.GetChild
			SetObject=self.InsertChild
			## button stuff
			_tmpName = constInfo.SAB.btnName["Access"] % slot
			_tmpObj = GetObject(_tmpName)
			## code stuff
			_tSlot = self.SAB_GetAccountData(slot)
			if _tSlot:
				(id, pwd) = _tSlot
				self.idEditLine.SetText(id)
				self.pwdEditLine.SetText(pwd)
				self.__OnClickSelectServerButton()
				self.__OnClickLoginButton()

		def SAB_Click_Remove(self, slot):
			if slot >= constInfo.SAB.slotCount:
				return
			## def code
			GetObject=self.GetChild
			SetObject=self.InsertChild
			## button stuff
			_tmpName = constInfo.SAB.btnName["Remove"] % slot
			_tmpObj = GetObject(_tmpName)
			## code stuff
			self.SAB_DelAccountData(slot)
			self.SAB_SaveAccountData()
			## rearrange stuff
			self.SAB_BtnRearrange()

		def __CreateSaveAccountBoard(self):
			### SAB INIT
			self.SAB_LoadAccountData()
			## def code
			GetObject=self.GetChild
			SetObject=self.InsertChild
			## gui stuff
			SCREEN_WIDTH = wndMgr.GetScreenWidth()
			SCREEN_HEIGHT = wndMgr.GetScreenHeight()
			## button space
			SPACE_FOR_BUTTON = 25+1
			ALL_BUTTON_SPACE = SPACE_FOR_BUTTON * constInfo.SAB.slotCount
			## board stuff
			BOARD_SIZE = (210+120, 28 + ALL_BUTTON_SPACE)
			BOARD_POS = ((SCREEN_WIDTH - 208) / 2 + 210, (SCREEN_HEIGHT - 410) - (10*constInfo.SAB.slotCount))
			## button stuff
			btnNameSave = constInfo.SAB.btnName["Save"]
			btnNameAccess = constInfo.SAB.btnName["Access"]
			btnNameRemove = constInfo.SAB.btnName["Remove"]
			btnPath = "d:/ymir work/ui/public/%s_button_%02d.sub" # xsmall small middle large xlarge big
			btnImage = {"default":1,"over":2,"down":3}
			## SAB BOARD
			try:
				## default init
				_tmpName = "SaveAccountBoard"
				SetObject(_tmpName, ui.ThinBoard())
				#
				_tmpObj = GetObject(_tmpName)
				_tmpObj.SetParent(self)
				## custom data
				_tmpObj.SetSize(*BOARD_SIZE)
				## default data
				_tmpObj.SetPosition(*BOARD_POS)
				_tmpObj.Show()
				self.saveAccountBoard = _tmpObj
			except:
				import exception; exception.Abort("__CreateSaveAccountBoard SAB BOARD")
			### SAB TITLE
			try:
				## default init
				_tmpName = "SaveAccountTitle"
				SetObject(_tmpName, ui.TextLine())
				_tmpObj = GetObject(_tmpName)
				_tmpObj.SetParent(self.saveAccountBoard)
				## custom data
				_tmpObj.SetHorizontalAlignCenter()
				_tmpObj.SetPackedFontColor(0xFFffbf00)
				_tmpObj.SetOutline()
				_tmpObj.SetText(uiScriptLocale.SAVE_ACCOUNT_TITLE)
				## default data
				_tmpObj.SetPosition(BOARD_SIZE[0]/2, 5)
				_tmpObj.Show()
			except:
				import exception; exception.Abort("__CreateSaveAccountBoard SAB TITLE")
			### SAB LINE
			try:
				## default init
				_tmpName = "SaveAccountLine"
				SetObject(_tmpName, ui.Line())
				_tmpObj = GetObject(_tmpName)
				_tmpObj.SetParent(self.saveAccountBoard)
				## custom data
				_tmpObj.SetColor(0xFF777777)
				_tmpObj.SetSize(BOARD_SIZE[0]-10, 0)
				## default data
				_tmpObj.SetPosition(5, 20)
				_tmpObj.Show()
			except:
				import exception; exception.Abort("__CreateSaveAccountBoard SAB LINE")
			## SaveAccountButtons
			for idx in xrange(constInfo.SAB.slotCount):
				### SAB SAVE
				try:
					## default init
					_tmpName = btnNameSave % (idx)
					SetObject(_tmpName, ui.Button())
					_tmpObj = GetObject(_tmpName)
					_tmpObj.SetParent(self.saveAccountBoard)
					## custom data
					_tmpBtnPath = "d:/ymir work/ui/public/xlarge_button_%02d.sub" # xsmall small middle large xlarge big
					_tmpObj.SetUpVisual(_tmpBtnPath % (btnImage["default"]))
					_tmpObj.SetOverVisual(_tmpBtnPath % (btnImage["over"]))
					_tmpObj.SetDownVisual(_tmpBtnPath % (btnImage["down"]))
					_tmpObj.SetText(uiScriptLocale.SAVE_ACCOUNT_SAVE)
					_tmpObj.SAFE_SetEvent(self.SAB_Click_Save, idx)
					## default data
					_tmpObj.SetPosition(15 + 60, 25 + (idx * SPACE_FOR_BUTTON))
					_tmpObj.Hide()
				except:
					import exception; exception.Abort("__CreateSaveAccountBoard SAB SAVE")
				### SAB ACCESS
				try:
					## default init
					_tmpName = btnNameAccess % (idx)
					SetObject(_tmpName, ui.Button())
					_tmpObj = GetObject(_tmpName)
					_tmpObj.SetParent(self.saveAccountBoard)
					## custom data
					_tmpBtnPath = "d:/ymir work/ui/public/xlarge_button_%02d.sub" # xsmall small middle large xlarge big
					_tmpObj.SetUpVisual(_tmpBtnPath % (btnImage["default"]))
					_tmpObj.SetOverVisual(_tmpBtnPath % (btnImage["over"]))
					_tmpObj.SetDownVisual(_tmpBtnPath % (btnImage["down"]))
					_tmpObj.SetText(uiScriptLocale.SAVE_ACCOUNT_CONNECT.format(idx+1))
					_tmpObj.SAFE_SetEvent(self.SAB_Click_Access, idx)
					## default data
					_tmpObj.SetPosition(35, 25 + (idx * SPACE_FOR_BUTTON))
					_tmpObj.Show()
				except:
					import exception; exception.Abort("__CreateSaveAccountBoard SAB ACCESS")
				### SAB REMOVE
				try:
					## default init
					_tmpName = btnNameRemove % (idx)
					SetObject(_tmpName, ui.Button())
					_tmpObj = GetObject(_tmpName)
					_tmpObj.SetParent(self.saveAccountBoard)
					## custom data
					_tmpBtnPath = "d:/ymir work/ui/public/middle_button_%02d.sub" # xsmall small middle large xlarge big
					_tmpObj.SetUpVisual(_tmpBtnPath % (btnImage["default"]))
					_tmpObj.SetOverVisual(_tmpBtnPath % (btnImage["over"]))
					_tmpObj.SetDownVisual(_tmpBtnPath % (btnImage["down"]))
					_tmpObj.SetText(uiScriptLocale.SAVE_ACCOUNT_REMOVE)
					_tmpObj.SAFE_SetEvent(self.SAB_Click_Remove, idx)
					## default data
					_tmpObj.SetPosition(35 + 190, 25 + (idx * SPACE_FOR_BUTTON))
					_tmpObj.Show()
				except:
					import exception; exception.Abort("__CreateSaveAccountBoard SAB REMOVE")
			self.SAB_BtnRearrange()

	def __LoadScript(self, fileName):
		import dbg
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, fileName)
		except:
			import exception
			exception.Abort("LoginWindow.__LoadScript.LoadObject")
		try:
			GetObject=self.GetChild
			self.serverBoard			= GetObject("ServerBoard")
			self.serverList				= GetObject("ServerList")
			self.channelList			= GetObject("ChannelList")
			self.serverSelectButton		= GetObject("ServerSelectButton")
			self.serverExitButton		= GetObject("ServerExitButton")
			self.connectBoard			= GetObject("ConnectBoard")
			self.loginBoard				= GetObject("LoginBoard")
			self.idEditLine				= GetObject("ID_EditLine")
			self.pwdEditLine			= GetObject("Password_EditLine")
			self.serverInfo				= GetObject("ConnectName")
			self.selectConnectButton	= GetObject("SelectConnectButton")
			self.loginButton			= GetObject("LoginButton")
			self.loginExitButton		= GetObject("LoginExitButton")

			if constInfo.ENABLE_SAVE_ACCOUNT:
				self.__CreateSaveAccountBoard()

			self.virtualKeyboard		= self.GetChild2("VirtualKeyboard")
			
			if app.__BL_MULTI_LANGUAGE_PREMIUM__:
				self.__BuildLanguageDropdown()
			if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
				panel_width1 = 160
				screen_width1 = wndMgr.GetScreenWidth()
				self.anon_mode_board = ui.ThinBoard()
				self.anon_mode_board.SetParent(self)
				self.anon_mode_board.SetSize(160, 35) 
				# self.anon_mode_board.SetPosition(0, 20 + self.language_board.GetHeight()) # sol koseye
				self.anon_mode_board.SetPosition((screen_width1 - panel_width1) / 2, 10)
				self.anon_mode_board.Show()

				self.anon_mode_text = ui.TextLine()
				self.anon_mode_text.SetParent(self.anon_mode_board)
				if localeInfo.IsARABIC():
					self.anon_mode_text.SetPosition(123, 7)
				else:
					self.anon_mode_text.SetPosition(15, 10)
				self.anon_mode_text.SetFontName(localeInfo.UI_DEF_FONT_LARGE)
				self.anon_mode_text.SetText(uiScriptLocale.LANGUAGE_ANONYMOUS_MODE)
				self.anon_mode_text.Show()

				self.anon_mode_checkbox_bg = ui.ImageBox()
				self.anon_mode_checkbox_bg.SetParent(self.anon_mode_board)
				if localeInfo.IsARABIC():
					self.anon_mode_checkbox_bg.SetPosition(15, 9)
				else:
					self.anon_mode_checkbox_bg.SetPosition(123, 9)
				self.anon_mode_checkbox_bg.LoadImage("d:/ymir work/ui/public/popup_notice_checkbox_bg.sub")
				self.anon_mode_checkbox_bg.SetEvent(ui.__mem_func__(self.__EventAnonymous), "mouse_click", "")
				self.anon_mode_checkbox_bg.Show()

				self.anon_mode_checkbox = ui.ImageBox()
				self.anon_mode_checkbox.SetParent(self.anon_mode_checkbox_bg)
				self.anon_mode_checkbox.AddFlag("not_pick")
				self.anon_mode_checkbox.SetPosition(0, 0)
				self.anon_mode_checkbox.LoadImage("d:/ymir work/ui/public/popup_notice_checkbox.sub")
				
				self.RefreshAnonymousMode()

			if self.virtualKeyboard:
				self.VIRTUAL_KEY_ALPHABET_UPPERS = Suffle(localeInfo.VIRTUAL_KEY_ALPHABET_UPPERS)
				self.VIRTUAL_KEY_ALPHABET_LOWERS = "".join([localeInfo.VIRTUAL_KEY_ALPHABET_LOWERS[localeInfo.VIRTUAL_KEY_ALPHABET_UPPERS.index(e)] for e in self.VIRTUAL_KEY_ALPHABET_UPPERS])
				if localeInfo.IsBRAZIL():
					self.VIRTUAL_KEY_SYMBOLS_BR = Suffle(localeInfo.VIRTUAL_KEY_SYMBOLS_BR)
				else:
					self.VIRTUAL_KEY_SYMBOLS = Suffle(localeInfo.VIRTUAL_KEY_SYMBOLS)
				self.VIRTUAL_KEY_NUMBERS = Suffle(localeInfo.VIRTUAL_KEY_NUMBERS)
				self.__VirtualKeyboard_SetAlphabetMode()

				self.GetChild("key_space").SetEvent(lambda : self.__VirtualKeyboard_PressKey(' '))
				self.GetChild("key_backspace").SetEvent(lambda : self.__VirtualKeyboard_PressBackspace())
				self.GetChild("key_enter").SetEvent(lambda : self.__VirtualKeyboard_PressReturn())
				self.GetChild("key_shift").SetToggleDownEvent(lambda : self.__VirtualKeyboard_SetUpperMode())
				self.GetChild("key_shift").SetToggleUpEvent(lambda : self.__VirtualKeyboard_SetLowerMode())
				self.GetChild("key_at").SetToggleDownEvent(lambda : self.__VirtualKeyboard_SetSymbolMode())
				self.GetChild("key_at").SetToggleUpEvent(lambda : self.__VirtualKeyboard_SetAlphabetMode())

		except:
			import exception
			exception.Abort("LoginWindow.__LoadScript.BindObject")

		if self.IS_TEST:
			self.selectConnectButton.Hide()
		else:
			self.selectConnectButton.SetEvent(ui.__mem_func__(self.__OnClickSelectConnectButton))

		self.serverBoard.OnKeyUp = ui.__mem_func__(self.__ServerBoard_OnKeyUp)
		self.xServerBoard, self.yServerBoard = self.serverBoard.GetLocalPosition()

		self.serverSelectButton.SetEvent(ui.__mem_func__(self.__OnClickSelectServerButton))
		self.serverExitButton.SetEvent(ui.__mem_func__(self.__OnClickExitButton))

		self.loginButton.SetEvent(ui.__mem_func__(self.__OnClickLoginButton))
		self.loginExitButton.SetEvent(ui.__mem_func__(self.__OnClickExitButton))

		self.serverList.SetEvent(ui.__mem_func__(self.__OnSelectServer))

		self.idEditLine.SetReturnEvent(ui.__mem_func__(self.pwdEditLine.SetFocus))
		self.idEditLine.SetTabEvent(ui.__mem_func__(self.pwdEditLine.SetFocus))

		self.pwdEditLine.SetReturnEvent(ui.__mem_func__(self.__OnClickLoginButton))
		self.pwdEditLine.SetTabEvent(ui.__mem_func__(self.idEditLine.SetFocus))

		if IsFullBackImage():
			self.GetChild("bg1").Show()
			self.GetChild("bg2").Hide()
		self.__BuildLoginFooterButtons()
		return 1

	def __OnClickLoginFooterLink(self, url):
		if not url:
			return
		try:
			import os
			os.startfile(url)
		except:
			import dbg
			dbg.TraceError("LoginWindow.__OnClickLoginFooterLink failed: %s" % (url,))

	def __BuildLoginFooterButtons(self):
		self.login_footer_buttons = []

		btn_path = "d:/ymir work/ui/public/large_button_%02d.sub"
		screen_h = wndMgr.GetScreenHeight()
		cursor_y = screen_h - LOGIN_FOOTER_MARGIN_BOTTOM

		# Links (edit URLs here): opened with os.startfile on Windows
		link_specs = (
			("https://discord.gg/ayazmt2", getattr(localeInfo, "LOGIN_BTN_DISCORD", "Discord")),
			("https://ayazmt2.com", getattr(localeInfo, "LOGIN_BTN_WEBSITE", "Website")),
			("https://ayazmt2.com", getattr(localeInfo, "LOGIN_BTN_PATCH_NOTES", "Patch notes")),
		)

		for url, label in link_specs:
			btn = ui.Button()
			btn.SetParent(self)
			btn.SetUpVisual(btn_path % 1)
			btn.SetOverVisual(btn_path % 2)
			btn.SetDownVisual(btn_path % 3)
			btn_h = btn.GetHeight()
			cursor_y -= btn_h
			btn.SetPosition(LOGIN_FOOTER_MARGIN_X, cursor_y)
			btn.SetText(label)
			url = url.strip()
			if url:
				btn.SetEvent(ui.__mem_func__(self.__OnClickLoginFooterLink), url)
			btn.Show()
			self.login_footer_buttons.append(btn)
			cursor_y -= LOGIN_FOOTER_BTN_GAP

	def __VirtualKeyboard_SetKeys(self, keyCodes):
		uiDefFontBackup = localeInfo.UI_DEF_FONT
		localeInfo.UI_DEF_FONT = localeInfo.UI_DEF_FONT_LARGE

		keyIndex = 1
		for keyCode in keyCodes:
			key = self.GetChild2("key_%d" % keyIndex)
			if key:
				key.SetEvent(lambda x=keyCode: self.__VirtualKeyboard_PressKey(x))
				key.SetText(keyCode)
				key.ButtonText.SetFontColor(0, 0, 0)
				keyIndex += 1

		for keyIndex in xrange(keyIndex, VIRTUAL_KEYBOARD_NUM_KEYS+1):
			key = self.GetChild2("key_%d" % keyIndex)
			if key:
				key.SetEvent(lambda x=' ': self.__VirtualKeyboard_PressKey(x))
				key.SetText(' ')

		localeInfo.UI_DEF_FONT = uiDefFontBackup

	def __VirtualKeyboard_PressKey(self, code):
		ime.PasteString(code)

		#if self.virtualKeyboardMode == "ALPHABET" and self.virtualKeyboardIsUpper:
		#	self.__VirtualKeyboard_SetLowerMode()

	def __VirtualKeyboard_PressBackspace(self):
		ime.PasteBackspace()

	def __VirtualKeyboard_PressReturn(self):
		ime.PasteReturn()

	def __VirtualKeyboard_SetUpperMode(self):
		self.virtualKeyboardIsUpper = True

		if self.virtualKeyboardMode == "ALPHABET":
			self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_ALPHABET_UPPERS)
		elif self.virtualKeyboardMode == "NUMBER":
			if localeInfo.IsBRAZIL():
				self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_SYMBOLS_BR)
			else:
				self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_SYMBOLS)
		else:
			self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_NUMBERS)

	def __VirtualKeyboard_SetLowerMode(self):
		self.virtualKeyboardIsUpper = False

		if self.virtualKeyboardMode == "ALPHABET":
			self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_ALPHABET_LOWERS)
		elif self.virtualKeyboardMode == "NUMBER":
			self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_NUMBERS)
		else:
			if localeInfo.IsBRAZIL():
				self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_SYMBOLS_BR)
			else:
				self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_SYMBOLS)

	def __VirtualKeyboard_SetAlphabetMode(self):
		self.virtualKeyboardIsUpper = False
		self.virtualKeyboardMode = "ALPHABET"
		self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_ALPHABET_LOWERS)

	def __VirtualKeyboard_SetNumberMode(self):
		self.virtualKeyboardIsUpper = False
		self.virtualKeyboardMode = "NUMBER"
		self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_NUMBERS)

	def __VirtualKeyboard_SetSymbolMode(self):
		self.virtualKeyboardIsUpper = False
		self.virtualKeyboardMode = "SYMBOL"
		if localeInfo.IsBRAZIL():
			self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_SYMBOLS_BR)
		else:
			self.__VirtualKeyboard_SetKeys(self.VIRTUAL_KEY_SYMBOLS)

	def Connect(self, id, pwd):

		if constInfo.SEQUENCE_PACKET_ENABLE:
			net.SetPacketSequenceMode()

		if IsLoginDelay():
			loginDelay = GetLoginDelay()
			self.connectingDialog = ConnectingDialog()
			self.connectingDialog.Open(loginDelay)
			self.connectingDialog.SAFE_SetTimeOverEvent(self.OnEndCountDown)
			self.connectingDialog.SAFE_SetExitEvent(self.OnPressExitKey)
			self.isNowCountDown = True

		else:
			self.stream.popupWindow.Close()
			self.stream.popupWindow.Open(localeInfo.LOGIN_CONNETING, self.SetPasswordEditLineFocus, localeInfo.UI_CANCEL)

		self.stream.SetLoginInfo(id, pwd)
		self.stream.Connect()

	def __OnClickExitButton(self):
		self.stream.SetPhaseWindow(0)

	if app.__BL_MULTI_LANGUAGE_ULTIMATE__:	
		def __EventAnonymous(self, event_type, arg):
			if "mouse_click" == event_type :
				systemSetting.SetAnonymousCountryMode(not systemSetting.GetAnonymousCountryMode())
				self.RefreshAnonymousMode()
		
		def RefreshAnonymousMode(self):
			if systemSetting.GetAnonymousCountryMode():
				self.anon_mode_checkbox.Show()
			else:
				self.anon_mode_checkbox.Hide()

	if app.__BL_MULTI_LANGUAGE_PREMIUM__:
		def __OnClickLanguageDropdownHeader(self):
			self.__ToggleLangList()

		def __ToggleLangList(self):
			if not self.language_list:
				return
			self.lang_drop_list_open = not self.lang_drop_list_open
			if self.lang_drop_list_open:
				self.__LayoutLangListBoard()
				if self.lang_list_board:
					self.lang_list_board.Show()
					self.lang_list_board.SetTop()
			elif self.lang_list_board:
				self.lang_list_board.Hide()

		def __CloseLangList(self):
			self.lang_drop_list_open = False
			if self.lang_list_board:
				self.lang_list_board.Hide()

		def __GetCurrentLanguageRowIndex(self):
			cur_locale = app.GetLocaleName()
			for idx, lang_entry in enumerate(self.language_list):
				if lang_entry["locale"] == cur_locale:
					return idx
			return 0

		def __ApplyLanguageHeader(self):
			if not self.language_list:
				return
			if self.lang_header_flag:
				active = self.language_list[self.__GetCurrentLanguageRowIndex()]
				# img_path = "d:/ymir work/ui/intro/login/server_flag_{}.sub".format(active["locale"])
				img_path = "d:/ymir work/flags/server_flag_{}.png".format(active["locale"])
				try:
					self.lang_header_flag.LoadImage(img_path)
				except:
					import dbg
					dbg.TraceError("LoginWindow: missing lang flag {}".format(active["locale"]))
			if self.lang_header_name_text:
				active = self.language_list[self.__GetCurrentLanguageRowIndex()]
				self.lang_header_name_text.SetText(active["name"])

		def __LayoutLangListBoard(self):
			if not self.lang_list_board or not self.language_list:
				return
			row_count = len(self.language_list)
			body_h = (
				row_count * LANG_DROPDOWN_ROW_BTN_H
				+ max(0, row_count - 1) * LANG_DROPDOWN_ROW_GAP
			)
			list_panel_height = LANG_DROPDOWN_LIST_PAD * 2 + body_h
			self.lang_list_board.SetSize(self.lang_panel_w, list_panel_height)
			screen_x, screen_y = self.language_board.GetGlobalPosition()
			self.lang_list_board.SetPosition(screen_x, screen_y + self.language_board.GetHeight())

		def __OnLanguageRowButton(self, row_index):
			self.__CloseLangList()
			self.__ClickLanguage(row_index)

		def __BuildLanguageDropdown(self):
			self.lang_row_entries = []
			self.lang_drop_list_open = False

			panel_width = 260
			screen_width = wndMgr.GetScreenWidth()
			content_margin = 12
			top_pad = 6
			title_band = 20
			header_y = top_pad + title_band + 2

			self.language_board = ui.ThinBoard()
			self.language_board.SetParent(self)
			self.language_board.SetPosition((screen_width - panel_width) / 2, 50)

			self.lang_panel_w = panel_width
			self.lang_row_inner_w = panel_width - content_margin * 2

			self.lang_title_text = ui.TextLine()
			self.lang_title_text.SetParent(self.language_board)
			self.lang_title_text.SetPosition(content_margin, top_pad + 2)
			self.lang_title_text.SetHorizontalAlignLeft()
			self.lang_title_text.SetFontName(localeInfo.UI_DEF_FONT_LARGE)
			self.lang_title_text.SetPackedFontColor(0xffffffff)
			try:
				self.lang_title_text.SetText(localeInfo.LOGIN_LANGUAGE_SELECT_TITLE)
			except:
				self.lang_title_text.SetText("Language selection")
			self.lang_title_text.Show()

			self.lang_header_btn = ui.Button()
			self.lang_header_btn.SetParent(self.language_board)
			self.lang_header_btn.SetUpVisual("d:/ymir work/ui/public/xlarge_button_01.sub")
			self.lang_header_btn.SetOverVisual("d:/ymir work/ui/public/xlarge_button_02.sub")
			self.lang_header_btn.SetDownVisual("d:/ymir work/ui/public/xlarge_button_03.sub")
			header_btn_height = self.lang_header_btn.GetHeight()
			self.lang_header_btn.SetPosition(content_margin, header_y)
			self.lang_header_btn.SetSize(self.lang_row_inner_w, header_btn_height)
			self.lang_header_btn.SetEvent(ui.__mem_func__(self.__OnClickLanguageDropdownHeader))
			self.lang_header_btn.Show()

			self.lang_header_flag = ui.ImageBox()
			self.lang_header_flag.SetParent(self.language_board)
			self.lang_header_flag.AddFlag("not_pick")
			self.lang_header_flag.SetPosition(content_margin + 10, header_y + 4)
			self.lang_header_flag.Show()

			self.lang_header_arrow = ui.ImageBox()
			self.lang_header_arrow.SetParent(self.language_board)
			self.lang_header_arrow.AddFlag("not_pick")
			self.lang_header_arrow.LoadImage("d:/ymir work/ui/chat/chattingoption_dropdown_arrow_01.sub")
			arr_w = self.lang_header_arrow.GetWidth()
			arr_h = self.lang_header_arrow.GetHeight()
			self.lang_header_arrow.SetPosition(
				content_margin + self.lang_row_inner_w - arr_w - 6,
				header_y + (header_btn_height - arr_h) / 2
			)
			self.lang_header_arrow.Show()

			self.lang_header_name_text = ui.TextLine()
			self.lang_header_name_text.SetParent(self.language_board)
			self.lang_header_name_text.AddFlag("not_pick")
			self.lang_header_name_text.SetPosition(content_margin + 44, header_y + 5)
			self.lang_header_name_text.SetHorizontalAlignLeft()
			self.lang_header_name_text.SetFontName(localeInfo.UI_DEF_FONT_LARGE)
			self.lang_header_name_text.SetPackedFontColor(0xffffffff)
			self.lang_header_name_text.Show()

			board_height = header_y + header_btn_height + top_pad + 6
			self.language_board.SetSize(panel_width, board_height)
			self.language_board.Show()

			self.lang_list_board = ui.ThinBoard("TOP_MOST")
			self.lang_list_board.SetParent(self)
			self.lang_list_board.Hide()

			row_inner = self.lang_row_inner_w - LANG_DROPDOWN_LIST_PAD * 2
			row_step = LANG_DROPDOWN_ROW_BTN_H + LANG_DROPDOWN_ROW_GAP

			for row_index, lang_entry in enumerate(self.language_list):
				row_top = LANG_DROPDOWN_LIST_PAD + row_index * row_step
				row_btn = ui.Button()
				row_btn.SetParent(self.lang_list_board)
				row_btn.SetPosition(LANG_DROPDOWN_LIST_PAD, row_top)
				row_btn.SetUpVisual("d:/ymir work/ui/public/xlarge_button_01.sub")
				row_btn.SetOverVisual("d:/ymir work/ui/public/xlarge_button_02.sub")
				row_btn.SetDownVisual("d:/ymir work/ui/public/xlarge_button_03.sub")
				row_btn.SetSize(row_inner, LANG_DROPDOWN_ROW_BTN_H)
				row_btn.SetEvent(ui.__mem_func__(self.__OnLanguageRowButton), row_index)
				row_btn.Show()

				row_flag = ui.ImageBox()
				row_flag.SetParent(self.lang_list_board)
				row_flag.AddFlag("not_pick")
				try:
					row_flag.LoadImage(
						# "d:/ymir work/ui/intro/login/server_flag_{}.sub".format(lang_entry["locale"])
						"d:/ymir work/flags/server_flag_{}.png".format(lang_entry["locale"])
					)
				except:
					pass
				row_flag.SetPosition(LANG_DROPDOWN_LIST_PAD + 6, row_top + 6)
				row_flag.Show()

				row_label = ui.TextLine()
				row_label.SetParent(self.lang_list_board)
				row_label.AddFlag("not_pick")
				row_label.SetPosition(LANG_DROPDOWN_LIST_PAD + 38, row_top + 5)
				row_label.SetHorizontalAlignLeft()
				row_label.SetFontName(localeInfo.UI_DEF_FONT)
				row_label.SetPackedFontColor(0xffffffff)
				row_label.SetText(lang_entry["name"])
				row_label.Show()

				self.lang_row_entries.append({"btn": row_btn, "flag": row_flag, "text": row_label})

			self.__ApplyLanguageHeader()

		def __LoadLocaleListFile(self):
			try:
				with open("locale_list.txt", "rt") as file:
					lines = file.readlines()
			except:
				import dbg
				dbg.LogBox("__LoadLocaleListFile error locale_list.txt")
				app.Abort()
			
			lineIndex = 1
			for line in lines:
				try:
					tokens = line[:-1].split(" ")
					if len(tokens) == 3:
						name = tokens[0]
						code_page = tokens[1]
						locale = tokens[2]
						
						if locale in uiScriptLocale.LOCALE_NAME_DICT:
							name = uiScriptLocale.LOCALE_NAME_DICT[locale]
						
						self.language_list.append({"name" : name, "code_page" : code_page, "locale" : locale})
					else:
						raise RuntimeError, "Unknown TokenSize"

					lineIndex += 1
				except:
					import dbg
					dbg.LogBox("%s: line(%d): %s" % ("locale_list.txt", lineIndex, line), "Error")
					raise
		
		def __SaveLoca(self, code_page, locale):
			try:
				with open("loca.cfg", "wt") as file:
					file.write("{} {}".format(code_page, locale))
			except:
				import dbg
				dbg.LogBox("__SaveLoca error")
				app.Abort()
		
		def __ClickLanguage(self, index):
			if index >= len(self.language_list):
				return

			self.__CloseLangList()

			lang = self.language_list[index]
			self.__SaveLoca(lang["code_page"], lang["locale"])
			app.SetReloadLocale(lang["locale"] != app.GetLocaleName())
			self.__ApplyLanguageHeader()

			if not self.language_popup:
				self.language_popup = uiCommon.PopupDialog()
			self.language_popup.SetText(uiScriptLocale.LANGUAGE_WILL_CHANGE)
			self.language_popup.Open()

	def __SetServerInfo(self, name):
		net.SetServerInfo(name.strip())
		self.serverInfo.SetText(name)

	def __LoadLoginInfo(self, loginInfoFileName):
		def getValue(element, name, default):
			if [] != element.getElementsByTagName(name):
				return element.getElementsByTagName(name).item(0).firstChild.nodeValue
			else:
				return default

		self.id = None
		self.pwd = None
		self.loginnedServer = None
		self.loginnedChannel = None
		app.loggined = False

		self.loginInfo = True

		from xml.dom.minidom import parse
		try:
			f = old_open(loginInfoFileName, "r")
			dom = parse(f)
		except:
			return
		serverLst = dom.getElementsByTagName("server")
		if [] != dom.getElementsByTagName("logininfo"):
			logininfo = dom.getElementsByTagName("logininfo")[0]
		else:
			return

		try:
			server_name = logininfo.getAttribute("name")
			channel_idx = int(logininfo.getAttribute("channel_idx"))
		except:
			return

		try:
			matched = False

			for k, v in serverInfo.REGION_DICT[0].iteritems():
				if v["name"] == server_name:
					account_addr = serverInfo.REGION_AUTH_SERVER_DICT[0][k]["ip"]
					account_port = serverInfo.REGION_AUTH_SERVER_DICT[0][k]["port"]

					channel_info = v["channel"][channel_idx]
					channel_name = channel_info["name"]
					addr = channel_info["ip"]
					port = channel_info["tcp_port"]

					net.SetMarkServer(addr, port)
					self.stream.SetConnectInfo(addr, port, account_addr, account_port)

					matched = True
					break

			if False == matched:
				return
		except:
			return

		self.__SetServerInfo("%s, %s " % (server_name, channel_name))
		id = getValue(logininfo, "id", "")
		pwd = getValue(logininfo, "pwd", "")
		self.idEditLine.SetText(id)
		self.pwdEditLine.SetText(pwd)
		slot = getValue(logininfo, "slot", "0")
		locale = getValue(logininfo, "locale", "")
		locale_dir = getValue(logininfo, "locale_dir", "")
		is_auto_login = int(getValue(logininfo, "auto_login", "0"))

		self.stream.SetCharacterSlot(int(slot))
		self.stream.isAutoLogin=is_auto_login
		self.stream.isAutoSelect=is_auto_login

		if locale and locale_dir:
			app.ForceSetLocale(locale, locale_dir)

		if 0 != is_auto_login:
			self.Connect(id, pwd)

		return


	def PopupDisplayMessage(self, msg):
		self.stream.popupWindow.Close()
		if app.__BL_MULTI_LANGUAGE__:
			self.stream.popupWindow.Open(msg, 0, localeInfo.UI_CANCEL)
		else:
			self.stream.popupWindow.Open(msg)

	def PopupNotifyMessage(self, msg, func=0):
		if not func:
			func=self.EmptyFunc

		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)

	def __OnCloseInputDialog(self):
		if self.inputDialog:
			self.inputDialog.Close()
		self.inputDialog = None
		return True

	def OnPressExitKey(self):
		self.stream.popupWindow.Close()
		self.stream.SetPhaseWindow(0)
		return True

	def OnExit(self):
		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(localeInfo.LOGIN_FAILURE_WRONG_MATRIX_CARD_NUMBER_TRIPLE, app.Exit, localeInfo.UI_OK)

	def OnUpdate(self):
		ServerStateChecker.Update()
		if ENABLE_MAP_INTERACTIVE_LOGIN:
			app.UpdateGame()

	def EmptyFunc(self):
		pass

	#####################################################################################

	def __ServerBoard_OnKeyUp(self, key):
		if self.serverBoard.IsShow():
			if app.DIK_RETURN==key:
				self.__OnClickSelectServerButton()
		return True

	def __GetRegionID(self):
		return 0

	def __GetServerID(self):
		return self.serverList.GetSelectedItem()

	def __GetChannelID(self):
		return self.channelList.GetSelectedItem()

	# SEVER_LIST_BUG_FIX
	def __ServerIDToServerIndex(self, regionID, targetServerID):
		try:
			regionDict = serverInfo.REGION_DICT[regionID]
		except KeyError:
			return -1

		retServerIndex = 0
		for eachServerID, regionDataDict in regionDict.items():
			if eachServerID == targetServerID:
				return retServerIndex

			retServerIndex += 1

		return -1

	def __ChannelIDToChannelIndex(self, channelID):
		return channelID - 1
	# END_OF_SEVER_LIST_BUG_FIX

	def __OpenServerBoard(self):

		loadRegionID, loadServerID, loadChannelID = self.__LoadChannelInfo()

		serverIndex = self.__ServerIDToServerIndex(loadRegionID, loadServerID)
		channelIndex = self.__ChannelIDToChannelIndex(loadChannelID)

		self.serverList.SelectItem(serverIndex)

		if constInfo.ENABLE_RANDOM_CHANNEL_SEL:
			self.channelList.SelectItem(app.GetRandom(0, self.channelList.GetItemCount()))
		else:
			if channelIndex >= 0:
				self.channelList.SelectItem(channelIndex)

		self.serverBoard.SetPosition(self.xServerBoard, self.yServerBoard)
		self.serverBoard.Show()
		self.connectBoard.Hide()
		self.loginBoard.Hide()
		if constInfo.ENABLE_SAVE_ACCOUNT:
			self.saveAccountBoard.Hide()

		self.KillInputFocus() #@fixme019

		if self.virtualKeyboard:
			self.virtualKeyboard.Hide()

		if app.loggined and not SKIP_LOGIN_PHASE_SUPPORT_CHANNEL:
			self.serverList.SelectItem(self.loginnedServer-1)
			self.channelList.SelectItem(self.loginnedChannel-1)
			self.__OnClickSelectServerButton()

	def KillInputFocus(self): #@fixme019
		if self.idEditLine and self.idEditLine.IsFocus():
			self.idEditLine.KillFocus()
		if self.pwdEditLine and self.pwdEditLine.IsFocus():
			self.pwdEditLine.KillFocus()

	def __OpenLoginBoard(self):

		self.serverExitButton.SetEvent(ui.__mem_func__(self.__OnClickExitServerButton))
		self.serverExitButton.SetText(localeInfo.UI_CLOSE)

		self.serverBoard.SetPosition(self.xServerBoard, wndMgr.GetScreenHeight())
		self.serverBoard.Hide()

		if self.virtualKeyboard:
			self.virtualKeyboard.Show()

		if app.loggined:
			self.Connect(self.id, self.pwd)
			self.connectBoard.Hide()
			self.loginBoard.Hide()
			if constInfo.ENABLE_SAVE_ACCOUNT:
				self.saveAccountBoard.Hide()
		elif not self.stream.isAutoLogin:
			self.connectBoard.Show()
			self.loginBoard.Show()
			if constInfo.ENABLE_SAVE_ACCOUNT:
				self.saveAccountBoard.Show()

		## if users have the login infomation, then don't initialize.2005.9 haho
		if self.idEditLine == None:
			self.idEditLine.SetText("")
		if self.pwdEditLine == None:
			self.pwdEditLine.SetText("")

		self.idEditLine.SetFocus()

		global SKIP_LOGIN_PHASE
		if SKIP_LOGIN_PHASE:
			if not self.loginInfo:
				self.connectBoard.Hide()

	def __OnSelectRegionGroup(self):
		self.__RefreshServerList()

	def __OnSelectSettlementArea(self):
		# SEVER_LIST_BUG_FIX
		regionID = self.__GetRegionID()
		serverID = self.serverListOnRegionBoard.GetSelectedItem()

		serverIndex = self.__ServerIDToServerIndex(regionID, serverID)
		self.serverList.SelectItem(serverIndex)
		# END_OF_SEVER_LIST_BUG_FIX

		self.__OnSelectServer()

	def __RefreshServerList(self):
		regionID = self.__GetRegionID()

		if not serverInfo.REGION_DICT.has_key(regionID):
			return

		self.serverList.ClearItem()

		regionDict = serverInfo.REGION_DICT[regionID]

		# SEVER_LIST_BUG_FIX
		visible_index = 1
		for id, regionDataDict in regionDict.items():
			name = regionDataDict.get("name", "noname")
			try:
				server_id = serverInfo.SERVER_ID_DICT[id]
			except:
				server_id = visible_index

			self.serverList.InsertItem(id, "  %02d. %s" % (int(server_id), name))

			visible_index += 1

		# END_OF_SEVER_LIST_BUG_FIX

	def __OnSelectServer(self):
		self.__OnCloseInputDialog()
		self.__RequestServerStateList()
		self.__RefreshServerStateList()

	def __RequestServerStateList(self):
		regionID = self.__GetRegionID()
		serverID = self.__GetServerID()

		try:
			channelDict = serverInfo.REGION_DICT[regionID][serverID]["channel"]
		except:
			print(" __RequestServerStateList - serverInfo.REGION_DICT(%d, %d)" % (regionID, serverID))
			return

		ServerStateChecker.Initialize()
		for id, channelDataDict in channelDict.items():
			key=channelDataDict["key"]
			ip=channelDataDict["ip"]
			tcp_port=channelDataDict["tcp_port"]
			ServerStateChecker.AddChannel(key, ip, tcp_port)

		ServerStateChecker.Request()

	def __RefreshServerStateList(self):

		regionID = self.__GetRegionID()
		serverID = self.__GetServerID()
		bakChannelID = self.channelList.GetSelectedItem()

		self.channelList.ClearItem()

		try:
			channelDict = serverInfo.REGION_DICT[regionID][serverID]["channel"]
		except:
			print(" __RequestServerStateList - serverInfo.REGION_DICT(%d, %d)" % (regionID, serverID))
			return

		for channelID, channelDataDict in channelDict.items():
			channelName = channelDataDict["name"]
			channelState = channelDataDict["state"]
			self.channelList.InsertItem(channelID, " %s %s" % (channelName, channelState))

		self.channelList.SelectItem(bakChannelID-1)

	def __GetChannelName(self, regionID, selServerID, selChannelID):
		try:
			return serverInfo.REGION_DICT[regionID][selServerID]["channel"][selChannelID]["name"]
		except KeyError:
			if 9==selChannelID:
				return localeInfo.CHANNEL_PVP
			else:
				return localeInfo.CHANNEL_NORMAL % (selChannelID)

	def NotifyChannelState(self, addrKey, state):
		try:
			stateName=serverInfo.STATE_DICT[state]
		except:
			stateName=serverInfo.STATE_NONE

		regionID=int(addrKey/1000)
		serverID=int(addrKey/10) % 100
		channelID=addrKey%10

		try:
			serverInfo.REGION_DICT[regionID][serverID]["channel"][channelID]["state"] = stateName
			self.__RefreshServerStateList()

		except:
			import exception
			exception.Abort(localeInfo.CHANNEL_NOT_FIND_INFO)

	def __OnClickExitServerButton(self):
		print("exit server")
		self.__OpenLoginBoard()

		if IsFullBackImage():
			self.GetChild("bg1").Hide()
			self.GetChild("bg2").Show()


	def __OnClickSelectRegionButton(self):
		regionID = self.__GetRegionID()
		serverID = self.__GetServerID()

		if (not serverInfo.REGION_DICT.has_key(regionID)):
			self.PopupNotifyMessage(localeInfo.CHANNEL_SELECT_REGION)
			return

		if (not serverInfo.REGION_DICT[regionID].has_key(serverID)):
			self.PopupNotifyMessage(localeInfo.CHANNEL_SELECT_SERVER)
			return

		self.__SaveChannelInfo()

		self.serverExitButton.SetEvent(ui.__mem_func__(self.__OnClickExitServerButton))
		self.serverExitButton.SetText(localeInfo.UI_CLOSE)

		self.__RefreshServerList()
		self.__OpenServerBoard()

	def __OnClickSelectServerButton(self):
		if IsFullBackImage():
			self.GetChild("bg1").Hide()
			self.GetChild("bg2").Show()

		regionID = self.__GetRegionID()
		serverID = self.__GetServerID()
		channelID = self.__GetChannelID()

		if (not serverInfo.REGION_DICT.has_key(regionID)):
			self.PopupNotifyMessage(localeInfo.CHANNEL_SELECT_REGION)
			return

		if (not serverInfo.REGION_DICT[regionID].has_key(serverID)):
			self.PopupNotifyMessage(localeInfo.CHANNEL_SELECT_SERVER)
			return

		try:
			channelDict = serverInfo.REGION_DICT[regionID][serverID]["channel"]
		except KeyError:
			return

		try:
			state = channelDict[channelID]["state"]
		except KeyError:
			self.PopupNotifyMessage(localeInfo.CHANNEL_SELECT_CHANNEL)
			return

		if state == serverInfo.STATE_DICT[3]:
			self.PopupNotifyMessage(localeInfo.CHANNEL_NOTIFY_FULL)
			return

		self.__SaveChannelInfo()

		try:
			serverName = serverInfo.REGION_DICT[regionID][serverID]["name"]
			channelName = serverInfo.REGION_DICT[regionID][serverID]["channel"][channelID]["name"]
			addrKey = serverInfo.REGION_DICT[regionID][serverID]["channel"][channelID]["key"]

		except:
			print(" ERROR __OnClickSelectServerButton(%d, %d, %d)" % (regionID, serverID, channelID))
			serverName = localeInfo.CHANNEL_EMPTY_SERVER
			channelName = localeInfo.CHANNEL_NORMAL % channelID

		self.__SetServerInfo("%s, %s " % (serverName, channelName))

		try:
			ip = serverInfo.REGION_DICT[regionID][serverID]["channel"][channelID]["ip"]
			tcp_port = serverInfo.REGION_DICT[regionID][serverID]["channel"][channelID]["tcp_port"]
		except:
			import exception
			exception.Abort("LoginWindow.__OnClickSelectServerButton")

		try:
			account_ip = serverInfo.REGION_AUTH_SERVER_DICT[regionID][serverID]["ip"]
			account_port = serverInfo.REGION_AUTH_SERVER_DICT[regionID][serverID]["port"]
		except:
			account_ip = 0
			account_port = 0

		try:
			markKey = regionID*1000 + serverID*10
			markAddrValue=serverInfo.MARKADDR_DICT[markKey]
			net.SetMarkServer(markAddrValue["ip"], markAddrValue["tcp_port"])
			app.SetGuildMarkPath(markAddrValue["mark"])
			# GUILD_SYMBOL
			app.SetGuildSymbolPath(markAddrValue["symbol_path"])
			# END_OF_GUILD_SYMBOL

		except:
			import exception
			exception.Abort("LoginWindow.__OnClickSelectServerButton")


		self.stream.SetConnectInfo(ip, tcp_port, account_ip, account_port)
		self.__OpenLoginBoard()


	def __OnClickSelectConnectButton(self):
		if IsFullBackImage():
			self.GetChild("bg1").Show()
			self.GetChild("bg2").Hide()
		self.__RefreshServerList()
		self.__OpenServerBoard()

	def __OnClickLoginButton(self):
		id = self.idEditLine.GetText()
		pwd = self.pwdEditLine.GetText()

		if len(id)==0:
			self.PopupNotifyMessage(localeInfo.LOGIN_INPUT_ID, self.SetIDEditLineFocus)
			return

		if len(pwd)==0:
			self.PopupNotifyMessage(localeInfo.LOGIN_INPUT_PASSWORD, self.SetPasswordEditLineFocus)
			return

		self.Connect(id, pwd)

	def OnKeyDown(self, key):
		if constInfo.ENABLE_SAVE_ACCOUNT:
			for idx in xrange(constInfo.SAB.slotCount):
				if app.DIK_F1+idx == key and self.SAB_GetAccountData(idx):
					self.SAB_Click_Access(idx)
		return True
