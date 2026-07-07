# Hediye Siralamasi penceresi (ENABLE_GIFT_SEND_SYSTEM).
# Klasik Player Rank gorunumu: koyu satir kutulari, sutun basliklari,
# 2 sekme (Gonderen/Alan), altta ayrik "kendi siram" satiri.
# Satirlar/sekmeler kodla kurulur; iskelet uiscript/giftrankwindow.py.
import ui
import net
import app
import player
import dbg
import localeInfo
import uigiftsend

# board tipleri (server GIFT_RANK_BOARD_* ile ayni)
BOARD_SENDER = 0
BOARD_RECEIVER = 1

RANK_ROW_COUNT = 10

# --- yerlesim (board koordinatlari) ---
TAB_Y = 38
TAB_H = 26
TAB1_X = 15
TAB2_X = 205
TAB_W = 180

HEADER_Y = 72
ROW_X = 16
ROW_W = 352
ROW_H = 27
ROW_START_Y = 96
ROW_STEP_Y = 30

COL_RANK_X = 36			# ortalanmis anchor
COL_NAME_X = 60
COL_POINT_X = 358		# saga hizali anchor

MY_LINE_Y = 408
MY_ROW_Y = 414

SCROLL_X = 372
SCROLL_Y = 94
SCROLL_H = 304

# --- renkler ---
ROW_BG = 0x82000000
ROW_BORDER = 0xFF3C3C3C
TAB_ACTIVE_BG = 0x8C32280A
TAB_ACTIVE_BORDER = 0xFFFFD700
MY_ROW_BG = 0x821E1400
MY_ROW_BORDER = 0xFFAA8C3C

_DEFAULT = {
	"TITLE"			: "Hediye Siralamasi",
	"TAB_SENDER"	: "En Cok Hediye Gonderen",
	"TAB_RECEIVER"	: "En Cok Hediye Alan",
	"COL_RANK"		: "#",
	"COL_NAME"		: "Isim",
	"COL_POINT"		: "Puan",
	"MY_RANK"		: "Kendi Siram",
	"LOADING"		: "Yukleniyor...",
	"NO_RANK"		: "-",
}


def GL(key):
	# localeInfo.GIFT_RANK_<key> varsa onu, yoksa varsayilani dondur.
	try:
		val = getattr(localeInfo, "GIFT_RANK_" + key)
		if val and val != ("GIFT_RANK_" + key):
			return val
	except:
		pass
	return _DEFAULT.get(key, key)


class GiftRankDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.isLoaded = False
		self.board = None
		self.loadingText = None
		self.scrollBar = []
		self.tabs = []			# [{bar, box, text, button}, ...] 0=gonderen 1=alan
		self.headerTexts = []
		self.headerLine = None
		self.rows = []			# [{bar, box, rank, name, point}, ...]
		self.myLine = None
		self.myRow = None		# {bar, box, label, rank, name, point}
		self.boardType = BOARD_SENDER
		self.isLoading = False

	@ui.WindowDestroy
	def Destroy(self):
		self.__Initialize()
		self.ClearDictionary()

	# ------------------------------------------------------------------
	# Kurulum
	# ------------------------------------------------------------------
	def __MakeText(self, x, y, text="", r=0.8549, g=0.8549, b=0.8549):
		t = ui.TextLine()
		t.SetParent(self.board)
		t.SetPosition(x, y)
		t.SetText(text)
		t.SetFontColor(r, g, b)
		t.SetOutline()
		t.Show()
		return t

	def __MakeRowBox(self, x, y, w, h, fillColor, borderColor):
		bar = ui.Bar()
		bar.SetParent(self.board)
		bar.SetPosition(x, y)
		bar.SetSize(w, h)
		bar.SetColor(fillColor)
		bar.Show()

		box = ui.Box()
		box.SetParent(self.board)
		box.SetPosition(x, y)
		box.SetSize(w, h)
		box.SetColor(borderColor)
		box.Show()
		return bar, box

	def __LoadWindow(self):
		if self.isLoaded:
			return
		self.isLoaded = True

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/giftrankwindow.py")
		except:
			dbg.TraceError("GiftRankDialog.LoadScript failed")
			self.isLoaded = False
			return

		try:
			self.board = self.GetChild("board")
		except:
			dbg.TraceError("GiftRankDialog.BindObject failed")
			self.isLoaded = False
			return

		self.board.SetTitleName(GL("TITLE"))
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))

		# --- sekmeler (koyu bar + cerceve + metin + gorselsiz tiklama butonu) ---
		self.tabs = []
		tabDefs = (
			(TAB1_X, GL("TAB_SENDER"), self.__OnTabSender),
			(TAB2_X, GL("TAB_RECEIVER"), self.__OnTabReceiver),
		)
		for x, label, event in tabDefs:
			bar, box = self.__MakeRowBox(x, TAB_Y, TAB_W, TAB_H, ROW_BG, ROW_BORDER)
			text = self.__MakeText(x + TAB_W // 2, TAB_Y + 7, label)
			text.SetHorizontalAlignCenter()
			btn = ui.Button()
			btn.SetParent(self.board)
			btn.SetPosition(x, TAB_Y)
			btn.SetSize(TAB_W, TAB_H)		# gorselsiz buton: rect tabanli tiklama (engine dogrulandi)
			btn.SetEvent(ui.__mem_func__(event))
			btn.Show()
			self.tabs.append({"bar": bar, "box": box, "text": text, "button": btn})

		# --- sutun basliklari ---
		self.headerTexts = []
		h1 = self.__MakeText(COL_RANK_X, HEADER_Y, GL("COL_RANK"), 1.0, 0.84, 0.0)
		h1.SetHorizontalAlignCenter()
		h2 = self.__MakeText(COL_NAME_X, HEADER_Y, GL("COL_NAME"), 1.0, 0.84, 0.0)
		h3 = self.__MakeText(COL_POINT_X, HEADER_Y, GL("COL_POINT"), 1.0, 0.84, 0.0)
		h3.SetHorizontalAlignRight()
		self.headerTexts = [h1, h2, h3]

		hline = ui.Bar()
		hline.SetParent(self.board)
		hline.SetPosition(12, HEADER_Y + 16)
		hline.SetSize(376, 1)
		hline.SetColor(ROW_BORDER)
		hline.Show()
		self.headerLine = hline

		# --- 10 satir ---
		self.rows = []
		for i in xrange(RANK_ROW_COUNT):
			y = ROW_START_Y + i * ROW_STEP_Y
			bar, box = self.__MakeRowBox(ROW_X, y, ROW_W, ROW_H, ROW_BG, ROW_BORDER)
			ty = y + 7
			rank = self.__MakeText(COL_RANK_X, ty, "")
			rank.SetHorizontalAlignCenter()
			name = self.__MakeText(COL_NAME_X, ty, "")
			point = self.__MakeText(COL_POINT_X, ty, "")
			point.SetHorizontalAlignRight()
			self.rows.append({"bar": bar, "box": box, "rank": rank, "name": name, "point": point})

		# --- dekoratif scrollbar GORUNUMU (liste 10 sabit satir; kaydirma yok) ---
		# Gercek ScrollBar widget'i etkilesimli kalip hicbir seyi kaydirmayacagi
		# icin "bozuk" gorunurdu; statik, tiklanamaz ImageBox'larla ayni gorunum verilir.
		self.scrollBar = []
		imgUp = ui.ImageBox()
		imgUp.SetParent(self.board)
		imgUp.AddFlag("not_pick")
		imgUp.LoadImage("d:/ymir work/ui/public/scrollbar_small_thin_up_button_01.sub")
		imgUp.SetPosition(SCROLL_X, SCROLL_Y)
		imgUp.Show()
		self.scrollBar.append(imgUp)

		imgDown = ui.ImageBox()
		imgDown.SetParent(self.board)
		imgDown.AddFlag("not_pick")
		imgDown.LoadImage("d:/ymir work/ui/public/scrollbar_small_thin_down_button_01.sub")
		imgDown.SetPosition(SCROLL_X, SCROLL_Y + SCROLL_H - imgDown.GetHeight())
		imgDown.Show()
		self.scrollBar.append(imgDown)

		imgThumb = ui.ImageBox()
		imgThumb.SetParent(self.board)
		imgThumb.AddFlag("not_pick")
		imgThumb.LoadImage("d:/ymir work/ui/public/scrollbar_small_thin_middle_button_01.sub")
		imgThumb.SetPosition(SCROLL_X, SCROLL_Y + imgUp.GetHeight() + 2)
		imgThumb.Show()
		self.scrollBar.append(imgThumb)

		# --- kendi siram (ayirici cizgi + tek satir) ---
		mline = ui.Bar()
		mline.SetParent(self.board)
		mline.SetPosition(12, MY_LINE_Y)
		mline.SetSize(376, 1)
		mline.SetColor(MY_ROW_BORDER)
		mline.Show()
		self.myLine = mline

		bar, box = self.__MakeRowBox(ROW_X, MY_ROW_Y, ROW_W, ROW_H, MY_ROW_BG, MY_ROW_BORDER)
		ty = MY_ROW_Y + 7
		rank = self.__MakeText(COL_RANK_X, ty, GL("NO_RANK"), 0.9, 0.78, 0.35)
		rank.SetHorizontalAlignCenter()
		name = self.__MakeText(COL_NAME_X, ty, "", 0.9, 0.78, 0.35)
		point = self.__MakeText(COL_POINT_X, ty, "", 0.9, 0.78, 0.35)
		point.SetHorizontalAlignRight()
		self.myRow = {"bar": bar, "box": box, "rank": rank, "name": name, "point": point}

		# yukleniyor metni EN SON olusturulur ki satir barlarinin USTUNDE cizilsin
		self.loadingText = self.__MakeText(200, 230, GL("LOADING"), 1.0, 0.84, 0.0)
		self.loadingText.SetHorizontalAlignCenter()
		self.loadingText.Hide()

		self.__RefreshTabVisual()

	# ------------------------------------------------------------------
	# Ac / Kapat
	# ------------------------------------------------------------------
	def Open(self):
		self.__LoadWindow()
		if not self.isLoaded:
			return
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.__RequestBoard(self.boardType)

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	# ------------------------------------------------------------------
	# Sekmeler
	# ------------------------------------------------------------------
	def __OnTabSender(self):
		self.__SelectBoard(BOARD_SENDER)

	def __OnTabReceiver(self):
		self.__SelectBoard(BOARD_RECEIVER)

	def __SelectBoard(self, boardType):
		if boardType == self.boardType:
			return		# ayni sekme; tekrar isteme
		self.boardType = boardType
		self.__RefreshTabVisual()
		self.__RequestBoard(boardType)

	def __RefreshTabVisual(self):
		for i, tab in enumerate(self.tabs):
			if i == self.boardType:
				tab["bar"].SetColor(TAB_ACTIVE_BG)
				tab["box"].SetColor(TAB_ACTIVE_BORDER)
				tab["text"].SetFontColor(1.0, 0.84, 0.0)
			else:
				tab["bar"].SetColor(ROW_BG)
				tab["box"].SetColor(ROW_BORDER)
				tab["text"].SetFontColor(0.71, 0.71, 0.71)

	# ------------------------------------------------------------------
	# Veri
	# ------------------------------------------------------------------
	def __RequestBoard(self, boardType):
		self.__SetLoading(True)
		if app.ENABLE_GIFT_SEND_SYSTEM:
			net.SendGiftRankPacket(boardType)

	def __SetLoading(self, flag):
		self.isLoading = flag
		if not self.isLoaded:
			return
		if flag:
			self.loadingText.Show()
			for row in self.rows:
				row["rank"].SetText("")
				row["name"].SetText("")
				row["point"].SetText("")
			if self.myRow:
				self.myRow["rank"].SetText(GL("NO_RANK"))
				self.myRow["name"].SetText(player.GetName())
				self.myRow["point"].SetText("")
		else:
			self.loadingText.Hide()

	def SetRankData(self, boardType, entries, myRank, myPoint):
		if not self.isLoaded:
			return
		# server yankisi hangi sekmeyse onu goster (gec gelen cevapla senkron kal)
		if boardType != self.boardType:
			self.boardType = boardType
			self.__RefreshTabVisual()

		self.__SetLoading(False)

		for i in xrange(RANK_ROW_COUNT):
			row = self.rows[i]
			if i < len(entries):
				try:
					name = entries[i][0]
					point = int(entries[i][1])
				except Exception, e:
					dbg.TraceError("GiftRankDialog.SetRankData entry %d error: %s" % (i, e))
					continue
				row["rank"].SetText(str(i + 1))
				# ilk 3 sira altin renkli
				if i < 3:
					row["rank"].SetFontColor(1.0, 0.84, 0.0)
				else:
					row["rank"].SetFontColor(0.8549, 0.8549, 0.8549)
				row["name"].SetText(name)
				row["point"].SetText(uigiftsend.FormatEP(point))
			else:
				row["rank"].SetText("")
				row["name"].SetText("")
				row["point"].SetText("")

		if self.myRow:
			myRank = int(myRank)
			myPoint = int(myPoint)
			self.myRow["rank"].SetText(str(myRank) if myRank > 0 else GL("NO_RANK"))
			self.myRow["name"].SetText(player.GetName())
			self.myRow["point"].SetText(uigiftsend.FormatEP(myPoint) if myPoint > 0 else GL("NO_RANK"))
