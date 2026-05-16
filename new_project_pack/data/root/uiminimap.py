import os
import sys
import ui
import uiScriptLocale
import wndMgr
import player
import miniMap
import localeInfo
import net
import app
import colorInfo
import constInfo
import background
import chr
from constInfo import TextColor

ATLAS_ZOOM_BTN_ROOT = "d:/ymir work/ui/minimap/"
ATLAS_ZOOM_BTN_Y = 10
ATLAS_RESIZE_GRIP_IMAGE = "d:/ymir work/flags/im.png"

class MapTextToolTip(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)

		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetHorizontalAlignCenter()
		textLine.SetOutline()
		textLine.SetHorizontalAlignRight()
		textLine.Show()
		self.textLine = textLine

	def __del__(self):
		ui.Window.__del__(self)

	def SetText(self, text):
		self.textLine.SetText(text)

	def SetTooltipPosition(self, PosX, PosY):
		if localeInfo.IsARABIC():
			w, h = self.textLine.GetTextSize()
			self.textLine.SetPosition(PosX - w - 5, PosY)
		else:
			self.textLine.SetPosition(PosX - 5, PosY)

	def SetTextColor(self, TextColor):
		self.textLine.SetPackedFontColor(TextColor)

	def GetTextSize(self):
		return self.textLine.GetTextSize()

ATLAS_BOARD_EXTRA_W = 15
ATLAS_BOARD_EXTRA_H = 38
ATLAS_RESIZE_GRIP_MARGIN = 6
ATLAS_RESIZE_GRIP_FALLBACK_W = 24
ATLAS_RESIZE_GRIP_FALLBACK_H = 24
ATLAS_ZOOM_STATE_FILE = "atlas_zoom.cfg"
ATLAS_ZOOM_CFG_THROTTLE_MS = 400
_cachedAtlasZoom = None

def _AtlasZoomCfgPaths():
	seen = set()
	out = []
	try:
		if getattr(sys, "frozen", False):
			root = os.path.dirname(sys.executable)
		else:
			argv0 = sys.argv[0]
			if argv0:
				root = os.path.dirname(os.path.abspath(argv0))
			else:
				root = ""
			if not root or root in (".", os.path.curdir):
				root = os.getcwd()
		p1 = os.path.join(os.path.normpath(root), ATLAS_ZOOM_STATE_FILE)
	except Exception:
		p1 = ATLAS_ZOOM_STATE_FILE
	for p in (p1, os.path.join(os.getcwd(), ATLAS_ZOOM_STATE_FILE), ATLAS_ZOOM_STATE_FILE):
		if not p:
			continue
		try:
			np = os.path.normpath(p)
		except Exception:
			np = p
		if np in seen:
			continue
		seen.add(np)
		out.append(np)
	return out

def _AtlasZoomCfgWritePath():
	paths = _AtlasZoomCfgPaths()
	return paths[0] if paths else ATLAS_ZOOM_STATE_FILE

def _RememberAtlasZoom(z):
	global _cachedAtlasZoom
	zc = _ClampEngineAtlasZoom(z)
	if zc is not None:
		_cachedAtlasZoom = zc

def _ReadSavedAtlasZoom():
	global _cachedAtlasZoom
	for path in _AtlasZoomCfgPaths():
		try:
			if not os.path.isfile(path):
				continue
			f = open(path, "r")
			try:
				for line in f:
					line = line.strip()
					if not line or line.startswith("#"):
						continue
					if line.startswith("ATLAS_ZOOM="):
						z = float(line.split("=", 1)[1].strip())
						_cachedAtlasZoom = _ClampEngineAtlasZoom(z)
						return _cachedAtlasZoom
			finally:
				f.close()
		except:
			pass
	return None

def _WriteSavedAtlasZoom(zoom):
	path = _AtlasZoomCfgWritePath()
	try:
		f = open(path, "w")
		try:
			f.write("ATLAS_ZOOM=%.6f\n" % zoom)
		finally:
			f.close()
		return True
	except:
		return False

def _ClampEngineAtlasZoom(z):
	try:
		zf = float(z)
	except:
		return None
	if zf < 1.0:
		return 1.0
	if zf > 3.0:
		return 3.0
	return zf

def _PickZoomForPersist(engineZoom):
	ez = _ClampEngineAtlasZoom(engineZoom) if engineZoom is not None else None
	cz = _cachedAtlasZoom
	if ez is None:
		return cz
	if cz is None:
		return ez
	# LoadAtlas() in the client resets engine zoom to 1.0; do not persist that over cache.
	if ez <= 1.001 and cz > 1.001:
		return cz
	return ez

class AtlasResizeGrip(ui.DragButton):
	def __init__(self):
		ui.DragButton.__init__(self)

	def __del__(self):
		ui.DragButton.__del__(self)

	def OnMouseOverIn(self):
		app.SetCursor(app.HVSIZE)

	def OnMouseOverOut(self):
		app.SetCursor(app.NORMAL)

class AtlasWindow(ui.ScriptWindow):

	class AtlasRenderer(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.AddFlag("not_pick")

		def OnUpdate(self):
			miniMap.UpdateAtlas()

		def OnRender(self):
			(x, y) = self.GetGlobalPosition()
			fx = float(x)
			fy = float(y)
			miniMap.RenderAtlas(fx, fy)

		def HideAtlas(self):
			miniMap.HideAtlas()

		def ShowAtlas(self):
			miniMap.ShowAtlas()

	def __init__(self):
		self.tooltipInfo = MapTextToolTip()
		self.tooltipInfo.Hide()
		self.infoGuildMark = ui.MarkBox()
		self.infoGuildMark.Hide()
		self.AtlasMainWindow = None
		self.mapName = ""
		self.board = 0
		self.atlasZoomInBtn = None
		self.atlasZoomOutBtn = None
		self.tooltipAtlasZoomIn = None
		self.tooltipAtlasZoomOut = None
		self._atlasZoomRepeatLastMs = 0
		self._atlasZoomCfgLastWriteMs = 0
		self._atlasZoomUserDirty = False

		ui.ScriptWindow.__init__(self)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def SetMapName(self, mapName):
		if 949==app.GetDefaultCodePage():
			try:
				self.board.SetTitleName(localeInfo.MINIMAP_ZONE_NAME_DICT[mapName])
			except:
				pass
		self.__ApplySavedAtlasZoomFromFile()
		if miniMap.IsAtlas():
			self.__ApplyAtlasLayoutFromEngine()

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/AtlasWindow.py")
		except:
			import exception
			exception.Abort("AtlasWindow.LoadWindow.LoadScript")

		try:
			self.board = self.GetChild("board")

		except:
			import exception
			exception.Abort("AtlasWindow.LoadWindow.BindObject")

		self.AtlasMainWindow = self.AtlasRenderer()
		self.board.SetCloseEvent(self.Hide)
		self.AtlasMainWindow.SetParent(self.board)
		self.AtlasMainWindow.SetPosition(7, 30)
		self.tooltipInfo.SetParent(self.board)
		self.infoGuildMark.SetParent(self.board)
		self.__CreateAtlasZoomControls()
		self.SetPosition(wndMgr.GetScreenWidth() - 136 - 256 - 10, 0)
		if app.ENABLE_MINIMAP_TELEPORT_CLICK:
			self.board.SetMouseLeftButtonUpEvent(ui.__mem_func__(self.OnMouseLeftButtonUpEvent))
		self.Hide()

		miniMap.RegisterAtlasWindow(self)
		self.__ApplySavedAtlasZoomFromFile()

	def __ApplySavedAtlasZoomFromFile(self):
		z = _cachedAtlasZoom
		if z is None:
			z = _ReadSavedAtlasZoom()
		if z is None:
			return
		zc = _ClampEngineAtlasZoom(z)
		if zc is None:
			return
		_RememberAtlasZoom(zc)
		if not miniMap.IsAtlas():
			return
		try:
			miniMap.SetAtlasZoom(zc)
		except:
			pass

	def __MarkAtlasZoomUserChanged(self):
		self._atlasZoomUserDirty = True
		if miniMap.IsAtlas():
			try:
				_RememberAtlasZoom(miniMap.GetAtlasZoom())
			except:
				pass

	def PersistAtlasZoom(self):
		self.__PersistAtlasZoomToFile(1)

	def __PersistAtlasZoomToFile(self, forceWrite):
		dirty = bool(getattr(self, "_atlasZoomUserDirty", False))
		if not forceWrite and not dirty:
			return

		ez = None
		if miniMap.IsAtlas():
			try:
				ez = miniMap.GetAtlasZoom()
			except:
				pass
		zc = _PickZoomForPersist(ez)
		if zc is None:
			return
		if not forceWrite:
			t = app.GetTime()
			lastWrite = getattr(self, "_atlasZoomCfgLastWriteMs", 0) or 0
			if t - lastWrite < ATLAS_ZOOM_CFG_THROTTLE_MS:
				return
		if _WriteSavedAtlasZoom(zc):
			_RememberAtlasZoom(zc)
			if getattr(self, "_atlasZoomCfgLastWriteMs", None) is not None:
				self._atlasZoomCfgLastWriteMs = app.GetTime()
			if forceWrite and getattr(self, "_atlasZoomUserDirty", None) is not None:
				self._atlasZoomUserDirty = False

	def __DestroyAtlasZoomControls(self):
		for w in (self.atlasZoomInBtn, self.atlasZoomOutBtn, self.atlasResizeGrip):
			if w:
				try:
					w.Hide()
					w.Destroy()
				except:
					pass
		self.atlasZoomInBtn = None
		self.atlasZoomOutBtn = None
		self.atlasResizeGrip = None
		for tip in (self.tooltipAtlasZoomIn, self.tooltipAtlasZoomOut):
			if tip:
				try:
					tip.Hide()
					tip.Destroy()
				except:
					pass
		self.tooltipAtlasZoomIn = None
		self.tooltipAtlasZoomOut = None

	def __CreateAtlasZoomControls(self):
		inBtn = ui.Button()
		inBtn.SetParent(self.board)
		inBtn.SetUpVisual(ATLAS_ZOOM_BTN_ROOT + "minimap_scaleup_default.sub")
		inBtn.SetOverVisual(ATLAS_ZOOM_BTN_ROOT + "minimap_scaleup_over.sub")
		inBtn.SetDownVisual(ATLAS_ZOOM_BTN_ROOT + "minimap_scaleup_down.sub")
		inBtn.SetEvent(ui.__mem_func__(self.__AtlasZoomInClick))
		inBtn.SetPosition(180, ATLAS_ZOOM_BTN_Y)
		inBtn.Show()
		self.atlasZoomInBtn = inBtn

		outBtn = ui.Button()
		outBtn.SetParent(self.board)
		outBtn.SetUpVisual(ATLAS_ZOOM_BTN_ROOT + "minimap_scaledown_default.sub")
		outBtn.SetOverVisual(ATLAS_ZOOM_BTN_ROOT + "minimap_scaledown_over.sub")
		outBtn.SetDownVisual(ATLAS_ZOOM_BTN_ROOT + "minimap_scaledown_down.sub")
		outBtn.SetEvent(ui.__mem_func__(self.__AtlasZoomOutClick))
		outBtn.SetPosition(158, ATLAS_ZOOM_BTN_Y)
		outBtn.Show()
		self.atlasZoomOutBtn = outBtn

		self.tooltipAtlasZoomIn = MapTextToolTip()
		self.tooltipAtlasZoomIn.SetText(localeInfo.MINIMAP_INC_SCALE)
		self.tooltipAtlasZoomIn.SetParent(self)
		self.tooltipAtlasZoomIn.Hide()

		self.tooltipAtlasZoomOut = MapTextToolTip()
		self.tooltipAtlasZoomOut.SetText(localeInfo.MINIMAP_DEC_SCALE)
		self.tooltipAtlasZoomOut.SetParent(self)
		self.tooltipAtlasZoomOut.Hide()

		grip = AtlasResizeGrip()
		grip.SetParent(self.board)
		grip.SetUpVisual(ATLAS_RESIZE_GRIP_IMAGE)
		grip.SetOverVisual(ATLAS_RESIZE_GRIP_IMAGE)
		grip.SetDownVisual(ATLAS_RESIZE_GRIP_IMAGE)
		gw = grip.GetWidth()
		gh = grip.GetHeight()
		if gw <= 0 or gh <= 0:
			grip.SetSize(ATLAS_RESIZE_GRIP_FALLBACK_W, ATLAS_RESIZE_GRIP_FALLBACK_H)
		grip.SetMoveEvent(ui.__mem_func__(self.__AtlasOnResizeGrip))
		grip.Show()
		self.atlasResizeGrip = grip

	def __ApplyAtlasLayoutFromEngine(self):
		if not self.board:
			return
		(bGet, iSizeX, iSizeY) = miniMap.GetAtlasSize()
		if not bGet:
			return
		self.SetSize(iSizeX + ATLAS_BOARD_EXTRA_W, iSizeY + ATLAS_BOARD_EXTRA_H)
		if localeInfo.IsARABIC():
			self.board.SetPosition(iSizeX + ATLAS_BOARD_EXTRA_W, 0)
		self.board.SetSize(iSizeX + ATLAS_BOARD_EXTRA_W, iSizeY + ATLAS_BOARD_EXTRA_H)
		if self.atlasZoomInBtn and self.atlasZoomOutBtn:
			bw = iSizeX + ATLAS_BOARD_EXTRA_W
			self.atlasZoomInBtn.SetPosition(bw - 46, ATLAS_ZOOM_BTN_Y)
			self.atlasZoomOutBtn.SetPosition(bw - 68, ATLAS_ZOOM_BTN_Y)
		self.__AtlasPositionResizeGrip()

	def __AtlasZoomInClick(self):
		try:
			miniMap.SetAtlasZoom(miniMap.GetAtlasZoom() * 1.12)
		except:
			return
		self._atlasZoomRepeatLastMs = app.GetTime()
		self.__ApplyAtlasLayoutFromEngine()
		self.__MarkAtlasZoomUserChanged()
		self.__PersistAtlasZoomToFile(1)

	def __AtlasZoomOutClick(self):
		try:
			miniMap.SetAtlasZoom(miniMap.GetAtlasZoom() / 1.12)
		except:
			return
		self._atlasZoomRepeatLastMs = app.GetTime()
		self.__ApplyAtlasLayoutFromEngine()
		self.__MarkAtlasZoomUserChanged()
		self.__PersistAtlasZoomToFile(1)

	def __AtlasZoomRepeat(self, direction):
		try:
			t = app.GetTime()
			if t - self._atlasZoomRepeatLastMs < 55:
				return
			self._atlasZoomRepeatLastMs = t
			z = miniMap.GetAtlasZoom()
			if direction > 0:
				miniMap.SetAtlasZoom(z * 1.04)
			else:
				miniMap.SetAtlasZoom(z / 1.04)
			self.__ApplyAtlasLayoutFromEngine()
			self.__MarkAtlasZoomUserChanged()
			self.__PersistAtlasZoomToFile(0)
		except:
			pass

	def __AtlasPositionResizeGrip(self):
		if not self.board or not self.atlasResizeGrip:
			return
		bw = self.board.GetWidth()
		bh = self.board.GetHeight()
		gw = self.atlasResizeGrip.GetWidth()
		gh = self.atlasResizeGrip.GetHeight()
		self.atlasResizeGrip.SetPosition(
			bw - gw - ATLAS_RESIZE_GRIP_MARGIN,
			bh - gh - ATLAS_RESIZE_GRIP_MARGIN)
		self.__AtlasUpdateResizeGripMovementBounds()

	def __AtlasComputeResizeLimits(self):
		if not miniMap.IsAtlas():
			return None
		(bGet, iSizeX, iSizeY) = miniMap.GetAtlasSize()
		if not bGet:
			return None
		try:
			zx, zy = miniMap.GetAtlasZoomXY()
		except:
			return None
		if zx <= 0.0001 or zy <= 0.0001:
			return None
		fTexW = float(iSizeX) / zx
		fTexH = float(iSizeY) / zy
		minBw = int(fTexW + ATLAS_BOARD_EXTRA_W)
		minBh = int(fTexH + ATLAS_BOARD_EXTRA_H)
		maxBw = int(fTexW * 3.0 + ATLAS_BOARD_EXTRA_W)
		maxBh = int(fTexH * 3.0 + ATLAS_BOARD_EXTRA_H)
		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		wx, wy = self.GetGlobalPosition()
		maxBw = max(minBw, min(maxBw, sw - wx - 4))
		maxBh = max(minBh, min(maxBh, sh - wy - 4))
		return (fTexW, fTexH, minBw, minBh, maxBw, maxBh)

	def __AtlasUpdateResizeGripMovementBounds(self):
		if not self.board or not self.atlasResizeGrip:
			return
		lims = self.__AtlasComputeResizeLimits()
		if not lims:
			return
		(_fTexW, _fTexH, minBw, minBh, maxBw, maxBh) = lims
		gw = self.atlasResizeGrip.GetWidth()
		gh = self.atlasResizeGrip.GetHeight()
		m = ATLAS_RESIZE_GRIP_MARGIN
		minGx = minBw - gw - m
		minGy = minBh - gh - m
		maxGx = maxBw - gw - m
		maxGy = maxBh - gh - m
		if minGx > maxGx:
			minGx, maxGx = maxGx, minGx
		if minGy > maxGy:
			minGy, maxGy = maxGy, minGy
		if minGx < 0:
			minGx = 0
		if minGy < 0:
			minGy = 0
		rw = max(1, maxGx - minGx + 1)
		rh = max(1, maxGy - minGy + 1)
		self.atlasResizeGrip.SetRestrictMovementArea(minGx, minGy, rw, rh)

	def __AtlasOnResizeGrip(self):
		if not self.board or not self.atlasResizeGrip:
			return
		grip = self.atlasResizeGrip
		grip.TurnOffCallBack()
		try:
			self.__AtlasOnResizeGripImpl()
		finally:
			grip.TurnOnCallBack()

	def __AtlasOnResizeGripImpl(self):
		if not self.board or not self.atlasResizeGrip:
			return
		lims = self.__AtlasComputeResizeLimits()
		if not lims:
			return
		fTexW, fTexH, minBw, minBh, maxBw, maxBh = lims

		gx, gy = self.atlasResizeGrip.GetLocalPosition()
		gw = self.atlasResizeGrip.GetWidth()
		gh = self.atlasResizeGrip.GetHeight()
		bw = gx + gw
		bh = gy + gh

		bw = max(minBw, min(bw, maxBw))
		bh = max(minBh, min(bh, maxBh))

		cw = float(bw - ATLAS_BOARD_EXTRA_W)
		ch = float(bh - ATLAS_BOARD_EXTRA_H)
		if cw <= 0.0 or ch <= 0.0:
			return
		zw = cw / fTexW
		zh = ch / fTexH
		z = min(zw, zh)
		if z < 1.0:
			z = 1.0
		elif z > 3.0:
			z = 3.0
		try:
			miniMap.SetAtlasZoom(z)
		except:
			return
		self.__ApplyAtlasLayoutFromEngine()
		self.__MarkAtlasZoomUserChanged()
		self.__PersistAtlasZoomToFile(0)

	if app.ENABLE_MINIMAP_TELEPORT_CLICK:
		def OnMouseLeftButtonUpEvent(self):
			(mouseX, mouseY) = wndMgr.GetMousePosition()
			(bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID) = miniMap.GetAtlasInfo(mouseX, mouseY)
			if chr.IsGameMaster(player.GetMainCharacterIndex()):
				net.SendChatPacket("/goto {} {}".format(iPosX, iPosY))

	@ui.WindowDestroy
	def Destroy(self):
		self.__PersistAtlasZoomToFile(1)
		miniMap.UnregisterAtlasWindow()
		self.__DestroyAtlasZoomControls()
		self.ClearDictionary()
		self.AtlasMainWindow = None
		self.tooltipAtlasClose = 0
		self.tooltipInfo = None
		self.infoGuildMark = None
		self.board = None

	def OnUpdate(self):
		if self.AtlasMainWindow and self.AtlasMainWindow.IsShow():
			if self.atlasZoomInBtn and self.atlasZoomInBtn.IsDown():
				self.__AtlasZoomRepeat(1)
			elif self.atlasZoomOutBtn and self.atlasZoomOutBtn.IsDown():
				self.__AtlasZoomRepeat(-1)

		if self.atlasZoomInBtn and self.tooltipAtlasZoomIn:
			if self.atlasZoomInBtn.IsIn():
				(bx, by) = self.atlasZoomInBtn.GetGlobalPosition()
				self.tooltipAtlasZoomIn.SetTooltipPosition(bx, by)
				self.tooltipAtlasZoomIn.Show()
			else:
				self.tooltipAtlasZoomIn.Hide()
		if self.atlasZoomOutBtn and self.tooltipAtlasZoomOut:
			if self.atlasZoomOutBtn.IsIn():
				(bx, by) = self.atlasZoomOutBtn.GetGlobalPosition()
				self.tooltipAtlasZoomOut.SetTooltipPosition(bx, by)
				self.tooltipAtlasZoomOut.Show()
			else:
				self.tooltipAtlasZoomOut.Hide()

		if not self.tooltipInfo:
			return

		if not self.infoGuildMark:
			return

		self.infoGuildMark.Hide()
		self.tooltipInfo.Hide()

		if False == self.board.IsIn():
			return

		(mouseX, mouseY) = wndMgr.GetMousePosition()
		(bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID) = miniMap.GetAtlasInfo(mouseX, mouseY)

		if False == bFind:
			return

		if "empty_guild_area" == sName:
			sName = localeInfo.GUILD_EMPTY_AREA

		if localeInfo.IsARABIC() and sName[-1].isalnum():
			self.tooltipInfo.SetText("(%s)%d, %d" % (sName, iPosX, iPosY))
		else:
			self.tooltipInfo.SetText("%s(%d, %d)" % (sName, iPosX, iPosY))

		(x, y) = self.GetGlobalPosition()
		self.tooltipInfo.SetTooltipPosition(mouseX - x, mouseY - y)
		self.tooltipInfo.SetTextColor(dwTextColor)
		self.tooltipInfo.Show()
		self.tooltipInfo.SetTop()

		if 0 != dwGuildID:
			textWidth, textHeight = self.tooltipInfo.GetTextSize()
			self.infoGuildMark.SetIndex(dwGuildID)
			self.infoGuildMark.SetPosition(mouseX - x - textWidth - 18 - 5, mouseY - y)
			self.infoGuildMark.Show()

	def Hide(self):
		if self.AtlasMainWindow:
			self.AtlasMainWindow.HideAtlas()
			self.AtlasMainWindow.Hide()
		ui.ScriptWindow.Hide(self)

	def Show(self):
		if self.AtlasMainWindow:
			(bGet, iSizeX, iSizeY) = miniMap.GetAtlasSize()
			if bGet:
				self.__ApplySavedAtlasZoomFromFile()
				self.__ApplyAtlasLayoutFromEngine()
				self.AtlasMainWindow.ShowAtlas()
				self.AtlasMainWindow.Show()
		ui.ScriptWindow.Show(self)

	def SetCenterPositionAdjust(self, x, y):
		self.SetPosition((wndMgr.GetScreenWidth() - self.GetWidth()) / 2 + x, (wndMgr.GetScreenHeight() - self.GetHeight()) / 2 + y)

	def OnPressEscapeKey(self):
		self.Hide()
		return True

def __RegisterMiniMapColor(type, rgb):
	miniMap.RegisterColor(type, rgb[0], rgb[1], rgb[2])

class MiniMap(ui.ScriptWindow):

	CANNOT_SEE_INFO_MAP_DICT = {
		"metin2_map_monkeydungeon" : False,
		"metin2_map_monkeydungeon_02" : False,
		"metin2_map_monkeydungeon_03" : False,
		"metin2_map_devilsCatacomb" : False,
	}

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__Initialize()

		miniMap.Create()
		miniMap.SetScale(2.0)

		self.AtlasWindow = AtlasWindow()
		self.AtlasWindow.LoadWindow()
		_ReadSavedAtlasZoom()
		self.AtlasWindow.Hide()

		self.tooltipMiniMapOpen = MapTextToolTip()
		self.tooltipMiniMapOpen.SetText(localeInfo.MINIMAP)
		self.tooltipMiniMapOpen.Show()
		self.tooltipMiniMapClose = MapTextToolTip()
		self.tooltipMiniMapClose.SetText(localeInfo.UI_CLOSE)
		self.tooltipMiniMapClose.Show()
		self.tooltipScaleUp = MapTextToolTip()
		self.tooltipScaleUp.SetText(localeInfo.MINIMAP_INC_SCALE)
		self.tooltipScaleUp.Show()
		self.tooltipScaleDown = MapTextToolTip()
		self.tooltipScaleDown.SetText(localeInfo.MINIMAP_DEC_SCALE)
		self.tooltipScaleDown.Show()
		self.tooltipAtlasOpen = MapTextToolTip()
		self.tooltipAtlasOpen.SetText(localeInfo.MINIMAP_SHOW_AREAMAP)
		self.tooltipAtlasOpen.Show()
		self.tooltipInfo = MapTextToolTip()
		self.tooltipInfo.Show()

		if miniMap.IsAtlas():
			self.tooltipAtlasOpen.SetText(localeInfo.MINIMAP_SHOW_AREAMAP)
		else:
			self.tooltipAtlasOpen.SetText(localeInfo.MINIMAP_CAN_NOT_SHOW_AREAMAP)

		self.tooltipInfo = MapTextToolTip()
		self.tooltipInfo.Show()

		self.mapName = ""

		self.isLoaded = 0
		self.canSeeInfo = True

		# AUTOBAN
		self.imprisonmentDuration = 0
		self.imprisonmentEndTime = 0
		self.imprisonmentEndTimeText = ""
		# END_OF_AUTOBAN

	def __del__(self):
		miniMap.Destroy()
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.positionInfo = 0
		self.observerCount = 0

		self.OpenWindow = 0
		self.CloseWindow = 0
		self.ScaleUpButton = 0
		self.ScaleDownButton = 0
		self.MiniMapHideButton = 0
		self.MiniMapShowButton = 0
		self.AtlasShowButton = 0

		self.tooltipMiniMapOpen = 0
		self.tooltipMiniMapClose = 0
		self.tooltipScaleUp = 0
		self.tooltipScaleDown = 0
		self.tooltipAtlasOpen = 0
		self.tooltipInfo = None
		self.serverInfo = None

	def SetMapName(self, mapName):
		self.mapName=mapName
		self.AtlasWindow.SetMapName(mapName)

		if self.CANNOT_SEE_INFO_MAP_DICT.has_key(mapName):
			self.canSeeInfo = False
			self.HideMiniMap()
			self.tooltipMiniMapOpen.SetText(localeInfo.MINIMAP_CANNOT_SEE)
		else:
			self.canSeeInfo = True
			self.ShowMiniMap()
			self.tooltipMiniMapOpen.SetText(localeInfo.MINIMAP)

	# AUTOBAN
	def SetImprisonmentDuration(self, duration):
		self.imprisonmentDuration = duration
		self.imprisonmentEndTime = app.GetGlobalTimeStamp() + duration

		self.__UpdateImprisonmentDurationText()

	def __UpdateImprisonmentDurationText(self):
		restTime = max(self.imprisonmentEndTime - app.GetGlobalTimeStamp(), 0)

		imprisonmentEndTimeText = localeInfo.SecondToDHM(restTime)
		if imprisonmentEndTimeText != self.imprisonmentEndTimeText:
			self.imprisonmentEndTimeText = imprisonmentEndTimeText
			self.serverInfo.SetText("%s: %s" % (uiScriptLocale.AUTOBAN_QUIZ_REST_TIME, self.imprisonmentEndTimeText))
	# END_OF_AUTOBAN

	def Show(self):
		self.__LoadWindow()

		ui.ScriptWindow.Show(self)

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			if localeInfo.IsARABIC():
				pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "Minimap.py")
			else:
				pyScrLoader.LoadScriptFile(self, "UIScript/MiniMap.py")
		except:
			import exception
			exception.Abort("MiniMap.LoadWindow.LoadScript")

		try:
			self.OpenWindow = self.GetChild("OpenWindow")
			self.MiniMapWindow = self.GetChild("MiniMapWindow")
			self.ScaleUpButton = self.GetChild("ScaleUpButton")
			self.ScaleDownButton = self.GetChild("ScaleDownButton")
			self.MiniMapHideButton = self.GetChild("MiniMapHideButton")
			self.AtlasShowButton = self.GetChild("AtlasShowButton")
			self.CloseWindow = self.GetChild("CloseWindow")
			self.MiniMapShowButton = self.GetChild("MiniMapShowButton")
			self.positionInfo = self.GetChild("PositionInfo")
			self.observerCount = self.GetChild("ObserverCount")
			self.serverInfo = self.GetChild("ServerInfo")
		except:
			import exception
			exception.Abort("MiniMap.LoadWindow.Bind")

		if constInfo.MINIMAP_POSITIONINFO_ENABLE==0:
			self.positionInfo.Hide()

		self.serverInfo.SetText(net.GetServerInfo())
		self.ScaleUpButton.SetEvent(ui.__mem_func__(self.ScaleUp))
		self.ScaleDownButton.SetEvent(ui.__mem_func__(self.ScaleDown))
		self.MiniMapHideButton.SetEvent(ui.__mem_func__(self.HideMiniMap))
		self.MiniMapShowButton.SetEvent(ui.__mem_func__(self.ShowMiniMap))

		if miniMap.IsAtlas():
			self.AtlasShowButton.SetEvent(ui.__mem_func__(self.ToggleAtlasWindow)) # @fixme014 ShowAtlas

		self.RefreshTooltipPosition()

		self.ShowMiniMap()

	def RefreshTooltipPosition(self):
		if self.MiniMapShowButton and self.tooltipMiniMapOpen:
			(ButtonPosX, ButtonPosY) = self.MiniMapShowButton.GetGlobalPosition()
			self.tooltipMiniMapOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if self.MiniMapHideButton and self.tooltipMiniMapClose:
			(ButtonPosX, ButtonPosY) = self.MiniMapHideButton.GetGlobalPosition()
			self.tooltipMiniMapClose.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if self.ScaleUpButton and self.tooltipScaleUp:
			(ButtonPosX, ButtonPosY) = self.ScaleUpButton.GetGlobalPosition()
			self.tooltipScaleUp.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if self.ScaleDownButton and self.tooltipScaleDown:
			(ButtonPosX, ButtonPosY) = self.ScaleDownButton.GetGlobalPosition()
			self.tooltipScaleDown.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if self.AtlasShowButton and self.tooltipAtlasOpen:
			(ButtonPosX, ButtonPosY) = self.AtlasShowButton.GetGlobalPosition()
			self.tooltipAtlasOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

	@ui.WindowDestroy
	def Destroy(self):
		self.PersistAtlasZoom()
		self.HideMiniMap()
		if self.AtlasWindow:
			self.AtlasWindow.Destroy()
			self.AtlasWindow = None

		self.ClearDictionary()

		self.__Initialize()

	def UpdateCurrentChannel(self, channelID):
		(serverName, channelName) = net.GetServerInfo().split(",")
		channelName = TextColor("CH-{}".format(channelID), "FFffFF")
		net.SetServerInfo("{}, {}".format(serverName, channelName))
		if self.serverInfo:
			self.serverInfo.SetText(net.GetServerInfo())

	def UpdateObserverCount(self, observerCount):
		if observerCount>0:
			self.observerCount.Show()
		elif observerCount<=0:
			self.observerCount.Hide()

		self.observerCount.SetText(localeInfo.MINIMAP_OBSERVER_COUNT % observerCount)

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		miniMap.Update(x, y)

		if localeInfo.IsARABIC():
			self.positionInfo.SetText("%.0f, %.0f" % (x/100, y/100))
		else:
			self.positionInfo.SetText("(%.0f, %.0f)" % (x/100, y/100))

		if self.tooltipInfo:
			if True == self.MiniMapWindow.IsIn():
				(mouseX, mouseY) = wndMgr.GetMousePosition()
				(bFind, sName, iPosX, iPosY, dwTextColor) = miniMap.GetInfo(mouseX, mouseY)
				if bFind == 0:
					self.tooltipInfo.Hide()
				elif not self.canSeeInfo:
					self.tooltipInfo.SetText("%s(%s)" % (sName, localeInfo.UI_POS_UNKNOWN))
					self.tooltipInfo.SetTooltipPosition(mouseX - 5, mouseY)
					self.tooltipInfo.SetTextColor(dwTextColor)
					self.tooltipInfo.Show()
				else:
					if localeInfo.IsARABIC() and sName[-1].isalnum():
						self.tooltipInfo.SetText("(%s)%d, %d" % (sName, iPosX, iPosY))
					else:
						self.tooltipInfo.SetText("%s(%d, %d)" % (sName, iPosX, iPosY))
					self.tooltipInfo.SetTooltipPosition(mouseX - 5, mouseY)
					self.tooltipInfo.SetTextColor(dwTextColor)
					self.tooltipInfo.Show()
			else:
				self.tooltipInfo.Hide()

			# AUTOBAN
			if self.imprisonmentDuration:
				self.__UpdateImprisonmentDurationText()
			# END_OF_AUTOBAN

		if True == self.MiniMapShowButton.IsIn():
			self.tooltipMiniMapOpen.Show()
		else:
			self.tooltipMiniMapOpen.Hide()

		if True == self.MiniMapHideButton.IsIn():
			self.tooltipMiniMapClose.Show()
		else:
			self.tooltipMiniMapClose.Hide()

		if True == self.ScaleUpButton.IsIn():
			self.tooltipScaleUp.Show()
		else:
			self.tooltipScaleUp.Hide()

		if True == self.ScaleDownButton.IsIn():
			self.tooltipScaleDown.Show()
		else:
			self.tooltipScaleDown.Hide()

		if True == self.AtlasShowButton.IsIn():
			self.tooltipAtlasOpen.Show()
		else:
			self.tooltipAtlasOpen.Hide()

	def OnRender(self):
		(x, y) = self.GetGlobalPosition()
		fx = float(x)
		fy = float(y)
		miniMap.Render(fx + 4.0, fy + 5.0)

	def Close(self):
		self.HideMiniMap()

	def HideMiniMap(self):
		miniMap.Hide()
		if self.OpenWindow:
			self.OpenWindow.Hide()
		if localeInfo.IsARABIC():
			self.SetPosition(wndMgr.GetScreenWidth() - 36, 0)
			self.RefreshTooltipPosition()

		if self.CloseWindow:
			self.CloseWindow.Show()

	def ShowMiniMap(self):
		if not self.canSeeInfo:
			return
		self.CloseWindow.Hide()
		if localeInfo.IsARABIC():
			self.SetPosition(wndMgr.GetScreenWidth() - 136, 0)
			self.RefreshTooltipPosition()
		miniMap.Show()
		self.OpenWindow.Show()

	def isShowMiniMap(self):
		return miniMap.isShow()

	def ScaleUp(self):
		miniMap.ScaleUp()

	def ScaleDown(self):
		miniMap.ScaleDown()

	def ShowAtlas(self):
		if not miniMap.IsAtlas():
			return
		if not self.AtlasWindow.IsShow():
			self.AtlasWindow.Show()

	def ToggleAtlasWindow(self):
		if not miniMap.IsAtlas():
			return
		if self.AtlasWindow.IsShow():
			self.AtlasWindow.Hide()
		else:
			self.AtlasWindow.Show()

	def PersistAtlasZoom(self):
		if self.AtlasWindow:
			self.AtlasWindow.PersistAtlasZoom()
