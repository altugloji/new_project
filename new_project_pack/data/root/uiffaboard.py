# Kaos Savasi (FFA) - skor penceresi + ekran ortasi sayac (server ENABLE_FFA_EVENT)
# Gorsel stil: Eski_A uiigriswarranking deseni (ThinBoard + satir basina ThinBoardCircle
# kutulari + irk ikonlari, yesil basliklar) - ANCAK widget'lar BIR KEZ kurulur,
# guncellemede sadece SetText/LoadImage yapilir (Eski_A her seferinde yeniden yaratip
# sizdiriyordu). Kalan sure pencerede DEGIL ekran ortasinda gosterilir (kullanici istegi).
# Server komutlari (CHAT_TYPE_COMMAND):
#   ffa_rank <kalanSn>#<sira>|<isim>|<kill>|<olum>|<irk>;...#<benSira>|<benKill>|<benOlum>
#   ffa_warmup <saniye>   -> ekran ortasi geri sayim ("Savasin baslamasina N saniye kaldi!")
#   ffa_start             -> 3 sn kirmizi "SAVAS BASLADI!", sonra bitis sayacina gecer
# Eski server bu komutlari gondermez; pencereler kendini gostermez (skew-safe).
# NOT: wndMgr python referansi tutmaz - her widget self uzerinde saklanmali.
import ui
import app
import wndMgr

BOARD_WIDTH = 244
ROW_COUNT = 10
ROW_HEIGHT = 22
ICON_X = 8
ICON_SIZE = 20
ICON_PATH = "d:/ymir work/pvp_war/race_%d.png"	# race_0..race_7 (97x100 png, 20x20 olceklenir)
NAME_X = 32
NAME_WIDTH = 146
SCORE_X = 184
SCORE_WIDTH = 46
HEADER_Y = 10
ROWS_Y = 30
STALE_HIDE_SECONDS = 12.0	# bu kadar sure ffa_rank gelmezse pencere gizlenir (haritadan cikis)
WARMUP_STALE_SECONDS = 6.0	# isinma sayaci tazelenmezse gizle (server 2 sn'de bir yollar)
FIGHT_TEXT_SECONDS = 3.0

RANK_COLORS = {
	0 : (1.0, 0.85, 0.2),	# altin
	1 : (0.8, 0.8, 0.85),	# gumus
	2 : (0.8, 0.55, 0.3),	# bronz
}
DEFAULT_ROW_COLOR = (0.9, 0.9, 0.9)

# FFACenterTimer modlari
TIMER_NONE = 0
TIMER_WARMUP = 1
TIMER_FIGHT_FLASH = 2
TIMER_WAR = 3


class FFABoardWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__lastRecvTime = 0.0
		self.__userClosed = 0
		self.__rows = []
		self.__widgets = []
		self.__BuildWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.__rows = []
		self.__widgets = []
		self.board = None
		self.myLine = None

	def __MakeCenteredText(self, parent, r, g, b):
		text = ui.TextLine()
		text.SetParent(parent)
		text.SetPosition(0, -1)
		text.SetWindowHorizontalAlignCenter()
		text.SetWindowVerticalAlignCenter()
		text.SetHorizontalAlignCenter()
		text.SetVerticalAlignCenter()
		text.SetFontColor(r, g, b)
		text.SetText("")
		text.Show()
		self.__widgets.append(text)
		return text

	def __MakeCircleBox(self, x, y, width):
		box = ui.ThinBoardCircle()
		box.AddFlag("attach")
		box.SetParent(self.board)
		box.SetSize(width, 20)
		box.SetPosition(x, y)
		box.Show()
		self.__widgets.append(box)
		return box

	def __SetRowIcon(self, row, race):
		# irk degismediyse yeniden yukleme yok (her 3 sn'de bir payload gelir)
		if race == row["race"]:
			return
		row["race"] = race
		icon = row["icon"]
		if race < 0:
			icon.Hide()
			return
		try:
			icon.LoadImage(ICON_PATH % race)
			w = icon.GetWidth()
			h = icon.GetHeight()
			if w > 0 and h > 0:
				icon.SetScale(float(ICON_SIZE) / w, float(ICON_SIZE) / h)
			icon.Show()
		except Exception:
			# gorsel pakette yoksa (orn. lycan irki icin race_8) ikonsuz devam
			icon.Hide()

	def __BuildWindow(self):
		height = ROWS_Y + ROW_COUNT * ROW_HEIGHT + 26
		self.SetSize(BOARD_WIDTH, height)

		self.board = ui.ThinBoard()
		self.board.SetParent(self)
		self.board.SetSize(BOARD_WIDTH, height)
		self.board.AddFlag("movable")
		self.board.AddFlag("float")
		self.board.Show()

		# basliklar (yesil, gorseldeki gibi; baslik satiri yok - kullanici istegi)
		nameHead = ui.TextLine()
		nameHead.SetParent(self.board)
		nameHead.SetPosition(NAME_X + NAME_WIDTH / 2, HEADER_Y)
		nameHead.SetHorizontalAlignCenter()
		nameHead.SetFontColor(0.0, 1.0, 0.0)
		nameHead.SetText("Oyuncu Adi")
		nameHead.Show()
		self.__widgets.append(nameHead)

		scoreHead = ui.TextLine()
		scoreHead.SetParent(self.board)
		scoreHead.SetPosition(SCORE_X + SCORE_WIDTH / 2, HEADER_Y)
		scoreHead.SetHorizontalAlignCenter()
		scoreHead.SetFontColor(0.0, 1.0, 0.0)
		scoreHead.SetText("Skor")
		scoreHead.Show()
		self.__widgets.append(scoreHead)

		# satirlar: irk ikonu + isim kutusu "Isim (olum)" + skor kutusu (kill)
		for i in xrange(ROW_COUNT):
			y = ROWS_Y + i * ROW_HEIGHT
			color = RANK_COLORS.get(i, DEFAULT_ROW_COLOR)

			# karakter irk ikonu (gorseldeki lonca amblemi konumu)
			icon = ui.ExpandedImageBox()
			icon.SetParent(self.board)
			icon.SetPosition(ICON_X, y)
			icon.Hide()
			self.__widgets.append(icon)

			nameBox = self.__MakeCircleBox(NAME_X, y, NAME_WIDTH)
			nameText = self.__MakeCenteredText(nameBox, color[0], color[1], color[2])
			nameText.SetText("---")

			scoreBox = self.__MakeCircleBox(SCORE_X, y, SCORE_WIDTH)
			scoreText = self.__MakeCenteredText(scoreBox, color[0], color[1], color[2])
			scoreText.SetText("-")

			self.__rows.append({"name" : nameText, "score" : scoreText, "icon" : icon, "race" : -1})

		# alt: kendi satirin
		myLine = ui.TextLine()
		myLine.SetParent(self.board)
		myLine.SetPosition(BOARD_WIDTH / 2, ROWS_Y + ROW_COUNT * ROW_HEIGHT + 6)
		myLine.SetHorizontalAlignCenter()
		myLine.SetFontColor(0.3, 1.0, 0.3)
		myLine.SetText("")
		myLine.Show()
		self.myLine = myLine

	def SetRankPayload(self, payload):
		now = app.GetTime()
		# 15+ sn sessizlik = yeni etkinlik girisi sayilir; elle kapatma sifirlanir
		if self.__userClosed and self.__lastRecvTime and now - self.__lastRecvTime > 15.0:
			self.__userClosed = 0
		self.__lastRecvTime = now

		try:
			parts = str(payload).split("#")
			rowsPart = parts[1] if len(parts) > 1 else ""
			mePart = parts[2] if len(parts) > 2 else ""
		except (ValueError, IndexError):
			return

		rows = []
		if rowsPart:
			for token in rowsPart.split(";"):
				cols = token.split("|")
				if len(cols) >= 4:
					rows.append(cols)

		for i in xrange(ROW_COUNT):
			row = self.__rows[i]
			if i < len(rows):
				cols = rows[i]
				row["name"].SetText("%s (%s)" % (cols[1], cols[3]))
				row["score"].SetText(cols[2])
				race = -1
				if len(cols) >= 5:
					try:
						race = int(cols[4])
					except ValueError:
						race = -1
				self.__SetRowIcon(row, race)
			else:
				row["name"].SetText("---")
				row["score"].SetText("-")
				self.__SetRowIcon(row, -1)

		meCols = mePart.split("|")
		if len(meCols) >= 3 and meCols[0] != "0":
			self.myLine.SetText("Sen: %s. sira - %s kill / %s olum" % (meCols[0], meCols[1], meCols[2]))
		else:
			self.myLine.SetText("Sen: henuz kill yok")

		if not self.IsShow() and not self.__userClosed:
			self.Open()

	def Open(self):
		self.SetPosition(wndMgr.GetScreenWidth() - BOARD_WIDTH - 10, 250)
		self.SetTop()
		self.Show()

	def Close(self):
		self.__userClosed = 1
		self.Hide()

	def OnUpdate(self):
		# server yayin kesildiyse (haritadan cikis / etkinlik bitti) kendini gizle
		if self.IsShow() and self.__lastRecvTime and app.GetTime() - self.__lastRecvTime > STALE_HIDE_SECONDS:
			self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return 1


class FFAWarmupCounter(ui.ScriptWindow):
	# Ekran ortasi sayac; uc gorev:
	# 1) isinma: "Savasin baslamasina N saniye kaldi!" (ffa_warmup ile senkron)
	# 2) baslama: 3 sn kirmizi "SAVAS BASLADI!" (ffa_start)
	# 3) savas: "Savasin bitmesine kalan sure: mm:ss" (ffa_rank'in kalanSn alanindan)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__mode = TIMER_NONE
		self.__warmupEndTime = 0.0
		self.__warEndTime = 0.0
		self.__warRecvTime = 0.0
		self.__warmupRecvTime = 0.0
		self.__fightTextUntil = 0.0
		self.__BuildWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.textLine = None

	def __BuildWindow(self):
		self.SetSize(460, 30)
		try:
			self.AddFlag("not_pick")
		except RuntimeError:
			pass

		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetPosition(230, 8)
		try:
			textLine.SetHorizontalAlignCenter()
		except AttributeError:
			pass
		try:
			textLine.SetFontName("Arial:16")
		except AttributeError:
			pass
		try:
			textLine.SetOutline()
		except AttributeError:
			pass
		textLine.SetFontColor(1.0, 0.85, 0.1)
		textLine.SetText("")
		textLine.Show()
		self.textLine = textLine

	def __ShowCentered(self):
		self.SetPosition((wndMgr.GetScreenWidth() - 460) / 2, 130)
		self.SetTop()
		self.Show()

	def StartCountdown(self, seconds):
		# isinma sayaci (ffa_warmup) - savas sayacindan oncelikli
		try:
			seconds = int(seconds)
		except ValueError:
			return
		now = app.GetTime()
		self.__mode = TIMER_WARMUP
		self.__warmupEndTime = now + seconds
		self.__warmupRecvTime = now
		self.__fightTextUntil = 0.0
		self.__ShowCentered()

	def FightStart(self):
		now = app.GetTime()
		self.__mode = TIMER_FIGHT_FLASH
		self.__fightTextUntil = now + FIGHT_TEXT_SECONDS
		self.textLine.SetFontColor(1.0, 0.2, 0.2)
		self.textLine.SetText("SAVAS BASLADI! Herkes dusman!")
		self.__ShowCentered()

	def SetWarRemainPayload(self, payload):
		# ffa_rank payload'inin ilk alani = savasin bitmesine kalan saniye
		try:
			remain = int(str(payload).split("#")[0])
		except (ValueError, IndexError):
			return
		now = app.GetTime()
		self.__warEndTime = now + remain
		self.__warRecvTime = now
		# isinma/baslama gosterimi surerken savas sayacina GECME; onlar bitince gecilir
		if self.__mode in (TIMER_NONE, TIMER_WAR) and remain > 0:
			if self.__mode != TIMER_WAR:
				self.__mode = TIMER_WAR
				self.__ShowCentered()

	def __SwitchToWarOrHide(self):
		now = app.GetTime()
		if self.__warEndTime > now and self.__warRecvTime and now - self.__warRecvTime <= STALE_HIDE_SECONDS:
			self.__mode = TIMER_WAR
			self.__ShowCentered()
		else:
			self.__mode = TIMER_NONE
			self.Hide()

	def OnUpdate(self):
		if not self.IsShow():
			return

		now = app.GetTime()

		if self.__mode == TIMER_FIGHT_FLASH:
			if now >= self.__fightTextUntil:
				self.__SwitchToWarOrHide()
			return

		if self.__mode == TIMER_WARMUP:
			# server 2 sn'de bir tazeler; tazelenmiyorsa haritadan cikilmis demektir
			if self.__warmupRecvTime and now - self.__warmupRecvTime > WARMUP_STALE_SECONDS:
				self.__mode = TIMER_NONE
				self.Hide()
				return
			remain = int(self.__warmupEndTime - now + 0.999)
			if remain > 0:
				self.textLine.SetFontColor(1.0, 0.85, 0.1)
				self.textLine.SetText("Savasin baslamasina %d saniye kaldi!" % remain)
			else:
				# dogal sifir: "BASLADI" mesajini server ffa_start ile gonderir
				self.__SwitchToWarOrHide()
			return

		if self.__mode == TIMER_WAR:
			# yayin kesildiyse (haritadan cikis / etkinlik bitti) gizle
			if self.__warRecvTime and now - self.__warRecvTime > STALE_HIDE_SECONDS:
				self.__mode = TIMER_NONE
				self.Hide()
				return
			remain = int(self.__warEndTime - now + 0.999)
			if remain > 0:
				self.textLine.SetFontColor(1.0, 0.85, 0.1)
				self.textLine.SetText("Savasin bitmesine kalan sure: %d:%02d" % (remain / 60, remain % 60))
			else:
				self.__mode = TIMER_NONE
				self.Hide()
			return

		# TIMER_NONE ama gorunur kalmis: temizle
		self.Hide()
