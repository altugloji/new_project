# GM Balik Bilgisi penceresi (server: ENABLE_GM_FISH_INFO, /fish_info <isim>)
# Veri akisi: uitarget.py FISH_INFO butonu -> /fish_info -> server chat-command satirlari
# (fish_info_begin / fish_info / fish_info_end) -> game.py handler'lari -> bu modul.
# Sayfalama tamamen client tarafindadir: 10 sayfa x 50 kayit = son 500 kayit.
# NOT: dosya ASCII kalmali; metinler duz ASCII Turkce yazilir (kullanici tercihi:
# cp1254 \x escape KULLANMA, "Basarili" gibi aksansiz yaz).

import ui

ROWS_PER_COL = 25
COL_COUNT = 2
ROWS_PER_PAGE = ROWS_PER_COL * COL_COUNT	# 50
MAX_PAGE = 10								# 10 x 50 = son 500 kayit

STATE_SUCCESS_TEXT = "Basarili"
STATE_FAIL_TEXT = "Basarisiz"
COLOR_SUCCESS = (0.3, 1.0, 0.3)
COLOR_FAIL = (1.0, 0.35, 0.35)
COLOR_HEADER = (1.0, 0.85, 0.3)
COLOR_EMPTY = (0.7, 0.7, 0.7)

# Bot suphesi araligi: take_time_ms bu araliktaysa "bot benzeri" sayilir
# (botlar sabit ~3sn'de yakalar; insan tepkisi genis dagilir).
# Ihtimal = araliktaki kayit / toplam kayit (son 500 uzerinden).
BOT_MS_MIN = 2920
BOT_MS_MAX = 3160
COLOR_BOT_HIGH = (1.0, 0.3, 0.3)	# >= %70
COLOR_BOT_MID = (1.0, 0.8, 0.2)		# %40-69
COLOR_BOT_LOW = (0.4, 1.0, 0.4)		# < %40


class FishInfoWindow(ui.BoardWithTitleBar):

	BOARD_WIDTH = 660
	BOARD_HEIGHT = 480
	ROW_START_Y = 76
	ROW_STEP_Y = 14
	COL_X = (22, 340)

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)

		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.BOARD_WIDTH, self.BOARD_HEIGHT)
		self.SetTitleName("Balik Bilgisi")
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()

		self.playerName = ""
		self.rows = []
		self.curPage = 0
		self.loading = False

		headerLine = ui.TextLine()
		headerLine.SetParent(self)
		headerLine.SetPosition(0, 38)
		headerLine.SetWindowHorizontalAlignCenter()
		headerLine.SetHorizontalAlignCenter()
		headerLine.SetFontColor(*COLOR_HEADER)
		headerLine.SetText("")
		headerLine.Show()
		self.headerLine = headerLine

		botLine = ui.TextLine()
		botLine.SetParent(self)
		botLine.SetPosition(0, 56)
		botLine.SetWindowHorizontalAlignCenter()
		botLine.SetHorizontalAlignCenter()
		botLine.SetText("")
		botLine.Show()
		self.botLine = botLine

		self.rowLines = []
		for i in xrange(ROWS_PER_PAGE):
			col = i / ROWS_PER_COL
			rowIdx = i % ROWS_PER_COL
			line = ui.TextLine()
			line.SetParent(self)
			line.SetPosition(self.COL_X[col], self.ROW_START_Y + rowIdx * self.ROW_STEP_Y)
			line.SetText("")
			line.Hide()
			self.rowLines.append(line)

		prevButton = ui.Button()
		prevButton.SetParent(self)
		prevButton.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
		prevButton.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
		prevButton.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")
		prevButton.SetText("<")
		prevButton.SetPosition(self.BOARD_WIDTH / 2 - 125, self.BOARD_HEIGHT - 42)
		prevButton.SetEvent(ui.__mem_func__(self.OnPrevPage))
		prevButton.Show()
		self.prevButton = prevButton

		nextButton = ui.Button()
		nextButton.SetParent(self)
		nextButton.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
		nextButton.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
		nextButton.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")
		nextButton.SetText(">")
		nextButton.SetPosition(self.BOARD_WIDTH / 2 + 60, self.BOARD_HEIGHT - 42)
		nextButton.SetEvent(ui.__mem_func__(self.OnNextPage))
		nextButton.Show()
		self.nextButton = nextButton

		pageLine = ui.TextLine()
		pageLine.SetParent(self)
		pageLine.SetPosition(0, self.BOARD_HEIGHT - 38)
		pageLine.SetWindowHorizontalAlignCenter()
		pageLine.SetHorizontalAlignCenter()
		pageLine.SetText("")
		pageLine.Show()
		self.pageLine = pageLine

		self.Hide()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def Destroy(self):
		self.headerLine = None
		self.botLine = None
		self.rowLines = []
		self.prevButton = None
		self.nextButton = None
		self.pageLine = None

	# ---- disaridan cagrilan akis ----

	def Open(self, name):
		self.playerName = str(name)
		self.rows = []
		self.curPage = 0
		self.loading = True
		self.headerLine.SetText("%s - Yukleniyor..." % self.playerName)
		self.botLine.SetText("")
		self.__RefreshPage()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def BeginData(self, name, total):
		self.playerName = str(name)
		self.rows = []
		self.curPage = 0
		self.loading = True

	def AppendRows(self, token):
		# token: "tarih|durum|ms;tarih|durum|ms;..." (bosluksuz)
		for rawRow in str(token).split(";"):
			parts = rawRow.split("|")
			if len(parts) >= 3:
				self.rows.append(parts)

	def EndData(self):
		self.loading = False
		self.headerLine.SetText("%s - Toplam %d kayit (son 500)" % (self.playerName, len(self.rows)))
		self.__RefreshBotChance()
		self.curPage = 0
		self.__RefreshPage()
		self.SetTop()
		self.Show()

	def __RefreshBotChance(self):
		total = len(self.rows)
		if total == 0:
			self.botLine.SetText("")
			return

		botCount = 0
		for parts in self.rows:
			try:
				ms = int(parts[2])
			except ValueError:
				continue
			if BOT_MS_MIN <= ms and ms <= BOT_MS_MAX:
				botCount += 1

		pct = 100 * botCount / total

		if pct >= 70:
			self.botLine.SetFontColor(*COLOR_BOT_HIGH)
		elif pct >= 40:
			self.botLine.SetFontColor(*COLOR_BOT_MID)
		else:
			self.botLine.SetFontColor(*COLOR_BOT_LOW)

		self.botLine.SetText("Bot ihtimali: %%%d (%d-%dms araliginda %d/%d kayit)" % (pct, BOT_MS_MIN, BOT_MS_MAX, botCount, total))

	# ---- sayfalama ----

	def __PageCount(self):
		pageCount = (len(self.rows) + ROWS_PER_PAGE - 1) / ROWS_PER_PAGE
		if pageCount < 1:
			pageCount = 1
		if pageCount > MAX_PAGE:
			pageCount = MAX_PAGE
		return pageCount

	def OnPrevPage(self):
		if self.curPage > 0:
			self.curPage -= 1
			self.__RefreshPage()

	def OnNextPage(self):
		if self.curPage < self.__PageCount() - 1:
			self.curPage += 1
			self.__RefreshPage()

	def __RefreshPage(self):
		start = self.curPage * ROWS_PER_PAGE

		for i in xrange(ROWS_PER_PAGE):
			line = self.rowLines[i]
			idx = start + i

			if idx >= len(self.rows):
				line.SetText("")
				line.Hide()
				continue

			(dateStr, stateStr, msStr) = self.rows[idx][0], self.rows[idx][1], self.rows[idx][2]

			try:
				secText = "%.1f sn" % (int(msStr) / 1000.0)
			except ValueError:
				secText = "-"

			if stateStr == "SUCCESS":
				stateText = STATE_SUCCESS_TEXT
				line.SetFontColor(*COLOR_SUCCESS)
			elif stateStr == "FAIL":
				stateText = STATE_FAIL_TEXT
				line.SetFontColor(*COLOR_FAIL)
			else:
				stateText = stateStr
				line.SetFontColor(0.9, 0.9, 0.9)

			line.SetText("%s   %s   %s" % (dateStr.replace("_", " "), stateText, secText))
			line.Show()

		if len(self.rows) == 0 and not self.loading:
			emptyLine = self.rowLines[0]
			emptyLine.SetFontColor(*COLOR_EMPTY)
			emptyLine.SetText("Kayit bulunamadi.")
			emptyLine.Show()

		self.pageLine.SetText("Sayfa %d/%d" % (self.curPage + 1, self.__PageCount()))

	# ---- pencere ----

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True


# ---- modul seviyesi tekil pencere ----

_window = None


def _GetWindow():
	global _window
	if not _window:
		_window = FishInfoWindow()
	return _window


def Open(name):
	_GetWindow().Open(name)


def BeginData(name, total):
	_GetWindow().BeginData(name, total)


def AppendData(token):
	_GetWindow().AppendRows(token)


def EndData():
	_GetWindow().EndData()
