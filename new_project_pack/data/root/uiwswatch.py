# WS 1v1 Turnuva - seyirci kamera paneli (ENABLE_WS_TOURNAMENT)
# RUMELI2 fikri: paketsiz, tamamen client-side kamera. Duello haritasinda (112)
# TAB ile acilir (interfacemodule.ToggleTabPanel). Ring koordinatlari
# settings.lua arena.add_map degerlerinin orta noktalaridir (server cm birimi).
# Oyuncu Izle: Eski_A watch-camera portu; kamera secilen oyuncuyu her kare izler
# (app.SetWatchCamera + chrmgr.GetPlayerListInUnsafe).
import ui
import app
import chrmgr
import player

# (x, y) server-cm: ring baslangic noktalarinin ortasi
RING_POINTS = (
	(854900.0, 10100.0),	# Ring 1: (8534,101)-(8564,101)
	(859900.0, 10100.0),	# Ring 2: (8584,101)-(8614,101)
	(854900.0, 15500.0),	# Ring 3: (8534,155)-(8564,155)
	(859900.0, 15500.0),	# Ring 4: (8584,155)-(8614,155)
)

CAMERA_ZOOM = 3000.0
CAMERA_PITCH = 35.0
CAMERA_ROTATION = 0.0

# Oyuncu takibi: daha yakin kamera
FOLLOW_ZOOM = 1800
FOLLOW_PITCH = 30
FOLLOW_ROTATION = 0

# WATCH modunda hedef kaybolursa kameranin dusecegi merkez (harita ortasi)
FALLBACK_X = 857400
FALLBACK_Y = 12800

MAX_PLAYER_BUTTONS = 8

BASE_HEIGHT = 196


class WSWatchBoard(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__cameraActive = 0
		# wndMgr python referansi tutmaz: referanssiz widget GC ile aninda yok olur
		self.__widgets = []
		self.__playerWidgets = []
		self.__BuildWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.__ResetCamera()
		self.ClearDictionary()
		self.__widgets = []
		self.__playerWidgets = []
		self.board = None

	def __MakeSmallButton(self, x, y, text, event, widgetList=None):
		btn = ui.Button()
		btn.SetParent(self.board)
		btn.SetPosition(x, y)
		btn.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
		btn.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
		btn.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
		btn.SetText(text)
		btn.SetEvent(event)
		btn.Show()
		if widgetList is None:
			widgetList = self.__widgets
		widgetList.append(btn)
		return btn

	def __BuildWindow(self):
		self.SetSize(190, BASE_HEIGHT)

		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetSize(190, BASE_HEIGHT)
		self.board.SetTitleName("WS Seyirci")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.AddFlag("movable")
		self.board.AddFlag("float")
		self.board.Show()

		hint = ui.TextLine()
		hint.SetParent(self.board)
		hint.SetPosition(15, 32)
		hint.SetText("TAB ile ac/kapat")
		hint.SetFontColor(0.6, 0.6, 0.6)
		hint.Show()
		self.hintLine = hint

		self.__MakeSmallButton(15, 52, "Ring 1", lambda: self.__WatchRing(0))
		self.__MakeSmallButton(100, 52, "Ring 2", lambda: self.__WatchRing(1))
		self.__MakeSmallButton(15, 80, "Ring 3", lambda: self.__WatchRing(2))
		self.__MakeSmallButton(100, 80, "Ring 4", lambda: self.__WatchRing(3))
		self.__MakeSmallButton(15, 108, "Kendine Don", ui.__mem_func__(self.__OnResetCamera))

		playerTitle = ui.TextLine()
		playerTitle.SetParent(self.board)
		playerTitle.SetPosition(15, 140)
		playerTitle.SetText("Oyuncular:")
		playerTitle.Show()
		self.playerTitle = playerTitle

		self.__MakeSmallButton(100, 136, "Yenile", ui.__mem_func__(self.__RefreshPlayers))

		emptyLine = ui.TextLine()
		emptyLine.SetParent(self.board)
		emptyLine.SetPosition(15, 162)
		emptyLine.SetText("Izlenecek oyuncu yok")
		emptyLine.SetFontColor(0.6, 0.6, 0.6)
		emptyLine.Hide()
		self.emptyLine = emptyLine

	def __WatchRing(self, ringIndex):
		if ringIndex < 0 or ringIndex >= len(RING_POINTS):
			return
		(x, y) = RING_POINTS[ringIndex]
		try:
			app.WSTWatchCamera(x, y, CAMERA_ZOOM, CAMERA_PITCH, CAMERA_ROTATION)
			self.__cameraActive = 1
		except AttributeError:
			pass

	def __WatchPlayer(self, vid):
		try:
			(px, py, pz) = player.GetMainCharacterPosition()
		except Exception:
			pz = 0.0
		# SetWatchCamera ham koordinat ister: y client eksenine gore negatif
		try:
			app.SetWatchCamera(int(FALLBACK_X), int(-FALLBACK_Y), int(pz),
				int(FOLLOW_ZOOM), int(FOLLOW_ROTATION), int(FOLLOW_PITCH), int(vid))
			self.__cameraActive = 1
		except AttributeError:
			pass

	def __RefreshPlayers(self):
		for wdg in self.__playerWidgets:
			wdg.Hide()
		self.__playerWidgets = []

		try:
			playerList = chrmgr.GetPlayerListInUnsafe()
		except (AttributeError, RuntimeError):
			playerList = []

		if not playerList:
			self.emptyLine.Show()
			self.__ResizeBoard(0)
			return

		self.emptyLine.Hide()
		playerList = playerList[:MAX_PLAYER_BUTTONS]
		row = 0
		for i in xrange(len(playerList)):
			(name, vid) = playerList[i]
			x = 15 + (i % 2) * 85
			y = 162 + (i / 2) * 26
			self.__MakeSmallButton(x, y, name, self.__MakeWatchEvent(vid), self.__playerWidgets)
			row = (i / 2) + 1
		self.__ResizeBoard(row)

	def __MakeWatchEvent(self, vid):
		return lambda: self.__WatchPlayer(vid)

	def __ResizeBoard(self, playerRows):
		if playerRows > 0:
			height = 162 + playerRows * 26 + 16
		else:
			height = BASE_HEIGHT
		self.SetSize(190, height)
		self.board.SetSize(190, height)

	def __OnResetCamera(self):
		self.__ResetCamera()

	def __ResetCamera(self):
		if self.__cameraActive:
			self.__cameraActive = 0
			try:
				app.SetDefaultCamera()
			except AttributeError:
				pass

	def Open(self):
		self.SetPosition(20, 120)
		self.SetTop()
		self.__RefreshPlayers()
		self.Show()

	def Close(self):
		self.__ResetCamera()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return 1
