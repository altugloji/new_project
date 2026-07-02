import dbg
import ui
import snd
import systemSetting
import net
import chat
import app
import localeInfo
import constInfo
import chrmgr
import player
import background
if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
	import uiScriptLocale

blockMode = 0

class OptionDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		print(" -------------------------------------- DELETE SYSTEM OPTION DIALOG")

	def __Initialize(self):
		self.tilingMode = 0
		self.titleBar = 0
		self.ctrlMusicVolume = 0
		self.ctrlSoundVolume = 0
		self.tilingApplyButton = 0
		self.cameraModeButtonList = []
		self.fogModeButtonList = []
		if app.__BL_FOG_FIX__:
			self.fogButtonList = []
		self.tilingModeButtonList = []
		self.ctrlShadowQuality = 0
		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.anonymous_button = None
		if app.ENABLE_NIGHT_MODE_OPTION:
			self.ctrlNightMode = 0
		if app.ENABLE_FOV_OPTION:
			self.ctrlFOV = 0

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()

		self.__Initialize()
		print(" -------------------------------------- DESTROY SYSTEM OPTION DIALOG")

	def __Load_LoadScript(self, fileName):
		try:
			pyScriptLoader = ui.PythonScriptLoader()
			pyScriptLoader.LoadScriptFile(self, fileName)
		except:
			import exception
			exception.Abort("System.OptionDialog.__Load_LoadScript")

	def __Load_BindObject(self):
		try:
			GetObject = self.GetChild
			self.titleBar = GetObject("titlebar")
			self.ctrlMusicVolume = GetObject("music_volume_controller")
			self.ctrlSoundVolume = GetObject("sound_volume_controller")
			self.cameraModeButtonList.append(GetObject("camera_short"))
			self.cameraModeButtonList.append(GetObject("camera_long"))
			if app.__BL_FOG_FIX__:
				self.fogButtonList.append(GetObject("fog_off"))
				self.fogButtonList.append(GetObject("fog_on"))
			else:
				self.fogModeButtonList.append(GetObject("fog_level0"))
				self.fogModeButtonList.append(GetObject("fog_level1"))
				self.fogModeButtonList.append(GetObject("fog_level2"))
			self.tilingModeButtonList.append(GetObject("tiling_cpu"))
			self.tilingModeButtonList.append(GetObject("tiling_gpu"))
			self.tilingApplyButton=GetObject("tiling_apply")
			if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
				self.anonymous_button = GetObject("anonymous_button")
			if app.ENABLE_NIGHT_MODE_OPTION:
				self.ctrlNightMode = GetObject("night_mode_controller")
			if app.ENABLE_FOV_OPTION:
				self.ctrlFOV = GetObject("fov_bar")
			#self.ctrlShadowQuality = GetObject("shadow_bar")
		except:
			import exception
			exception.Abort("OptionDialog.__Load_BindObject")

	def __Load(self):
		self.__Load_LoadScript("uiscript/systemoptiondialog.py")
		self.__Load_BindObject()

		self.SetCenterPosition()

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

		self.ctrlMusicVolume.SetSliderPos(float(systemSetting.GetMusicVolume()))
		self.ctrlMusicVolume.SetEvent(ui.__mem_func__(self.OnChangeMusicVolume))

		self.ctrlSoundVolume.SetSliderPos(float(systemSetting.GetSoundVolume()) / 5.0)
		self.ctrlSoundVolume.SetEvent(ui.__mem_func__(self.OnChangeSoundVolume))

		if app.ENABLE_NIGHT_MODE_OPTION:
			self.ctrlNightMode.SetSliderPos(float(systemSetting.GetNightModeVolume()))
			self.ctrlNightMode.SetEvent(ui.__mem_func__(self.OnChangeNightMode))
			constInfo.APPLY_NIGHT_MODE()

		if app.ENABLE_FOV_OPTION:
			self.ctrlFOV.SetSliderPos((float(systemSetting.GetFOVLevel()) - 30.0) / 30.0)
			self.ctrlFOV.SetEvent(ui.__mem_func__(self.OnChangeFOV))

#		self.ctrlShadowQuality.SetSliderPos(float(systemSetting.GetShadowLevel()) / 5.0)
#		self.ctrlShadowQuality.SetEvent(ui.__mem_func__(self.OnChangeShadowQuality))

		self.cameraModeButtonList[0].SAFE_SetEvent(self.__OnClickCameraModeShortButton)
		self.cameraModeButtonList[1].SAFE_SetEvent(self.__OnClickCameraModeLongButton)

		if app.__BL_FOG_FIX__:
			self.fogButtonList[0].SAFE_SetEvent(self.__OnClickFogModeOffButton)
			self.fogButtonList[1].SAFE_SetEvent(self.__OnClickFogModeOnButton)
		else:
			self.fogModeButtonList[0].SAFE_SetEvent(self.__OnClickFogModeLevel0Button)
			self.fogModeButtonList[1].SAFE_SetEvent(self.__OnClickFogModeLevel1Button)
			self.fogModeButtonList[2].SAFE_SetEvent(self.__OnClickFogModeLevel2Button)

		self.tilingModeButtonList[0].SAFE_SetEvent(self.__OnClickTilingModeCPUButton)
		self.tilingModeButtonList[1].SAFE_SetEvent(self.__OnClickTilingModeGPUButton)

		self.tilingApplyButton.SAFE_SetEvent(self.__OnClickTilingApplyButton)

		self.__SetCurTilingMode()

		if app.__BL_FOG_FIX__:
			self.__ClickRadioButton(self.fogButtonList, background.GetFogMode())
		else:
			self.__ClickRadioButton(self.fogModeButtonList, constInfo.GET_FOG_LEVEL_INDEX())
		self.__ClickRadioButton(self.cameraModeButtonList, constInfo.GET_CAMERA_MAX_DISTANCE_INDEX())

		if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
			self.anonymous_button.SetEvent( ui.__mem_func__(self.__OnClickAnonymousButton) )
			self.RefreshLanguageSettings()

	def __OnClickTilingModeCPUButton(self):
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_CPU_TILING_1)
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_CPU_TILING_2)
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_CPU_TILING_3)
		self.__SetTilingMode(0)

	def __OnClickTilingModeGPUButton(self):
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_GPU_TILING_1)
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_GPU_TILING_2)
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_GPU_TILING_3)
		self.__SetTilingMode(1)

	def __OnClickTilingApplyButton(self):
		self.__NotifyChatLine(localeInfo.SYSTEM_OPTION_TILING_EXIT)
		if 0==self.tilingMode:
			background.EnableSoftwareTiling(1)
		else:
			background.EnableSoftwareTiling(0)

		net.ExitGame()

	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			selButton=buttonList[buttonIndex]
		except IndexError:
			return

		for eachButton in buttonList:
			eachButton.SetUp()

		selButton.Down()


	def __SetTilingMode(self, index):
		self.__ClickRadioButton(self.tilingModeButtonList, index)
		self.tilingMode=index

	def __SetCameraMode(self, index):
		constInfo.SET_CAMERA_MAX_DISTANCE_INDEX(index)
		self.__ClickRadioButton(self.cameraModeButtonList, index)

	def __SetFogLevel(self, index):
		constInfo.SET_FOG_LEVEL_INDEX(index)
		self.__ClickRadioButton(self.fogModeButtonList, index)

	def __OnClickCameraModeShortButton(self):
		self.__SetCameraMode(0)

	def __OnClickCameraModeLongButton(self):
		self.__SetCameraMode(1)

	def __OnClickFogModeLevel0Button(self):
		self.__SetFogLevel(0)

	def __OnClickFogModeLevel1Button(self):
		self.__SetFogLevel(1)

	def __OnClickFogModeLevel2Button(self):
		self.__SetFogLevel(2)

	if app.__BL_FOG_FIX__:
		def __OnClickFogModeOnButton(self):
			background.SetFogMode(True)
			self.__ClickRadioButton(self.fogButtonList, 1)

		def __OnClickFogModeOffButton(self):
			background.SetFogMode(False)
			self.__ClickRadioButton(self.fogButtonList, 0)

	def OnChangeMusicVolume(self):
		pos = self.ctrlMusicVolume.GetSliderPos()
		snd.SetMusicVolume(pos * net.GetFieldMusicVolume())
		systemSetting.SetMusicVolume(pos)

	def OnChangeSoundVolume(self):
		pos = self.ctrlSoundVolume.GetSliderPos()
		snd.SetSoundVolumef(pos)
		systemSetting.SetSoundVolumef(pos)

	if app.ENABLE_NIGHT_MODE_OPTION:
		def OnChangeNightMode(self):
			pos = self.ctrlNightMode.GetSliderPos()
			systemSetting.SetNightModeVolume(pos)
			constInfo.APPLY_NIGHT_MODE(pos)

	if app.ENABLE_FOV_OPTION:
		def OnChangeFOV(self):
			pos = self.ctrlFOV.GetSliderPos()
			systemSetting.SetFOVLevel(30.0 + pos * 30.0)

	def OnChangeShadowQuality(self):
		pos = self.ctrlShadowQuality.GetSliderPos()
		systemSetting.SetShadowLevel(int(pos / 0.2))

	def OnCloseInputDialog(self):
		self.inputDialog.Close()
		self.inputDialog = None
		return True

	def OnCloseQuestionDialog(self):
		self.questionDialog.Close()
		self.questionDialog = None
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.__SetCurTilingMode()
		self.Hide()

	def __SetCurTilingMode(self):
		if background.IsSoftwareTiling():
			self.__SetTilingMode(0)
		else:
			self.__SetTilingMode(1)

	def __NotifyChatLine(self, text):
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	if app.__BL_MULTI_LANGUAGE_ULTIMATE__:
		def __OnClickAnonymousButton(self):
			net.SendChatPacket("/language_anonymous")

		def LanguageChangeAnonymous(self):
			systemSetting.SetAnonymousCountryMode(not systemSetting.GetAnonymousCountryMode())
			self.RefreshLanguageSettings()

		def RefreshLanguageSettings(self):
			if systemSetting.GetAnonymousCountryMode():
				self.anonymous_button.SetText(uiScriptLocale.LANGUAGE_SETTINGS_ANON_OFF)
			else:
				self.anonymous_button.SetText(uiScriptLocale.LANGUAGE_SETTINGS_ANON_ON)