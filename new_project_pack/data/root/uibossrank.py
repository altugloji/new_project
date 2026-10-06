# Boss Hasar Siralamasi penceresi (server ENABLE_BOSS_DAMAGE_RANKING)
# GORUNUM: Eski_A uibossranking.py kalibi (kullanici istegi 2026-09-10):
#   satir = irk ikonu (d:/ymir work/boss_ranking/N.tga) + bayrak renginde
#   "Nick [Lv.75]" + 117px kirmizi gauge + "%xx.x"; sol-alt varsayilan konum.
# ANCAK Eski_A'nin buglari TASINMADI: widget'lar BIR KEZ kurulur (her pakette
# yikip-yeniden-yaratma sizintisi yok), SetPackedFontColor yerine SetFontColor
# (packed renk C binding'i py2'de PyLong TypeError verir - ui conventions GOTCHA),
# polymorph ikonu server tarafinda cozuldu.
# Server komutlari (CHAT_TYPE_COMMAND):
#   boss_rank <vnum>,<vid>#<sira>|<isim>|<hasar>|<yuzde>|<irk>|<imp>|<seviye>;...#<benSira>|<benHasar>|<benYuzde>
#   boss_rank_end <vid>   -> boss oldu, pencereyi aninda kapat
# Eski alan sayisi toleransi: len>=4 satir kabul edilir (irk/imp/seviye yoksa sade).
# Coklu boss: pencere ilk gelen VID'e kilitlenir; yayin bayatlarsa digerine gecer.
# Eski server komut gondermez = pencere hic acilmaz; eski root komutu yok sayar.
# AE (Arapca) duzeltmesi (2026-09-10, F7 pazar arama dersiyle ayni GENEL KURAL):
#   GrpTextInstance CP_ARABIC'te ALIGN_LEFT metni ankrajdan SOLA uzatir (619-631);
#   ALIGN_RIGHT ise kaydirmaz = LTR sol-hizali davranisin karsiligi. Bu yuzden
#   AE'de tum TextLine'lara SetHorizontalAlignRight verilir (ayni x, ayni kutu).
#   Ayrica RTL cizici ()[] sembollerini aynalayip bas/sona tasidigindan AE
#   metin bicimleri ayracsiz kurulur ("Nick Lv.75", parantezsiz Sen satiri).
# NOT: wndMgr python referansi tutmaz - her widget self uzerinde saklanmali.
import ui
import app
import wndMgr
import localeInfo

BOARD_WIDTH = 400	# Eski_A 325 idi; hasar sutunu icin genisletildi (kullanici istegi)
ROW_COUNT = 10	# server BOSS_RANKING_TOP_COUNT ile ayni (isimler wire'da 11 karaktere kesilir)
Y_START = 15
Y_PASS = 20
ICON_X = 5
ICON_PATH = "d:/ymir work/boss_ranking/%d.tga"	# 0..8 (Eski_A varliklari, root pack'e eklendi)
NAME_X = 26
DMG_X = 170
GAUGE_X = 245
GAUGE_WIDTH = 100
PCT_X = 350
MYLINE_PAD = 4
BOTTOM_PAD = 20
STALE_HIDE_SECONDS = 8.0	# bu kadar sure boss_rank gelmezse gizle (olum/despawn/uzaklasma)

# bayrak renkleri (Eski_A packed degerlerin float karsiligi: ffe34b4b/fffaf884/ff84a3fa)
EMPIRE_COLORS = {
	1 : (0.890, 0.294, 0.294),	# kirmizi (Shinsoo)
	2 : (0.980, 0.973, 0.518),	# sari (Chunjo)
	3 : (0.518, 0.639, 0.980),	# mavi (Jinno)
}
DEFAULT_ROW_COLOR = (0.9, 0.9, 0.9)


class BossRankBoard(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__lastRecvTime = 0.0
		self.__userClosed = 0
		self.__defaultPosSet = 0	# konum yalniz ILK acilista atanir; oyuncunun tasidigi yer korunur
		self.__bossVid = 0
		self.__lastVisible = -1
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

	def __MakeRowText(self, x, y):
		# AE: CP_ARABIC'te ALIGN_RIGHT = ankrajdan saga akis (dosya basi nota bak)
		text = ui.TextLine()
		text.SetParent(self.board)
		text.SetPosition(x, y)
		if localeInfo.IsARABIC():
			text.SetHorizontalAlignRight()
		text.SetFontColor(DEFAULT_ROW_COLOR[0], DEFAULT_ROW_COLOR[1], DEFAULT_ROW_COLOR[2])
		text.SetText("")
		text.Hide()
		self.__widgets.append(text)
		return text

	def __BuildWindow(self):
		# tasima bayraklari DIS pencerede olmali (uiffaboard dersi); board "attach" ile
		# tiklamalari dis pencerenin tasimasina baglar
		self.AddFlag("movable")
		self.AddFlag("float")

		self.board = ui.ThinBoard()
		self.board.SetParent(self)
		self.board.AddFlag("attach")
		self.board.Show()

		for i in xrange(ROW_COUNT):
			y = Y_START + i * Y_PASS

			icon = ui.ImageBox()
			icon.SetParent(self.board)
			icon.SetPosition(ICON_X, y - 6)
			icon.AddFlag("attach")
			icon.Hide()
			self.__widgets.append(icon)

			nameText = self.__MakeRowText(NAME_X, y - 4)
			dmgText = self.__MakeRowText(DMG_X, y - 4)

			gauge = ui.Gauge()
			gauge.SetParent(self.board)
			gauge.MakeGauge(GAUGE_WIDTH, "red")
			gauge.SetPosition(GAUGE_X, y)
			gauge.SetPercentage(0, 100)
			try:
				gauge.AddFlag("attach")
			except RuntimeError:
				pass
			gauge.Hide()
			self.__widgets.append(gauge)

			pctText = self.__MakeRowText(PCT_X, y - 4)

			self.__rows.append({"icon" : icon, "name" : nameText, "dmg" : dmgText, "gauge" : gauge, "pct" : pctText, "race" : -1})

		# alt: kendi satirin (ham hasar burada gosterilir; satirlar Eski_A gibi sade)
		myLine = ui.TextLine()
		myLine.SetParent(self.board)
		myLine.SetPosition(NAME_X, Y_START)	# gercek konumu __Relayout ayarlar
		if localeInfo.IsARABIC():
			myLine.SetHorizontalAlignRight()
		myLine.SetFontColor(0.3, 1.0, 0.3)
		myLine.SetText("")
		myLine.Show()
		self.myLine = myLine

		self.__Relayout(ROW_COUNT)

	def __Relayout(self, visibleCount):
		# gorunen satir sayisina gore pencere/board boyu + kendi-satiri konumu
		if visibleCount == self.__lastVisible:
			return
		self.__lastVisible = visibleCount
		myY = Y_START + visibleCount * Y_PASS + MYLINE_PAD
		height = myY + BOTTOM_PAD
		self.SetSize(BOARD_WIDTH, height)
		self.board.SetSize(BOARD_WIDTH, height)
		self.myLine.SetPosition(NAME_X, myY)

	def __SetRowIcon(self, row, race):
		# irk degismediyse yeniden yukleme yok (payload 3 sn'de bir gelir)
		if race == row["race"]:
			if race >= 0:
				row["icon"].Show()
			return
		row["race"] = race
		icon = row["icon"]
		if race < 0:
			icon.Hide()
			return
		try:
			icon.LoadImage(ICON_PATH % race)
			icon.Show()
		except Exception:
			# gorsel pakette yoksa ikonsuz devam
			row["race"] = -1
			icon.Hide()

	def __FormatDamage(self, s):
		try:
			return localeInfo.NumberToString(long(s))
		except (ValueError, AttributeError):
			return s

	def __SwitchBoss(self, vid):
		self.__bossVid = vid
		self.__userClosed = 0	# yeni boss oturumu: elle kapatma sifirlanir

	def SetRankPayload(self, payload):
		try:
			parts = str(payload).split("#")
			headCols = parts[0].split(",")
			vid = int(headCols[1])
			rowsPart = parts[1] if len(parts) > 1 else ""
			mePart = parts[2] if len(parts) > 2 else ""
		except (ValueError, IndexError):
			return

		now = app.GetTime()

		if self.__bossVid and vid != self.__bossVid:
			# mevcut boss'un yayini taze ise baska boss'un yayinini yok say
			if self.__lastRecvTime and now - self.__lastRecvTime <= STALE_HIDE_SECONDS:
				return
			self.__SwitchBoss(vid)
		elif not self.__bossVid:
			self.__SwitchBoss(vid)

		self.__lastRecvTime = now

		rows = []
		if rowsPart:
			for token in rowsPart.split(";"):
				cols = token.split("|")
				if len(cols) >= 4:
					rows.append(cols)

		visible = 0
		for i in xrange(ROW_COUNT):
			row = self.__rows[i]
			if i < len(rows):
				cols = rows[i]
				visible += 1

				# yeni alanlar (irk/imp/seviye) satir sonunda; eski server toleransi
				race = -1
				empire = 0
				level = 0
				if len(cols) >= 7:
					try:
						race = int(cols[4])
						empire = int(cols[5])
						level = int(cols[6])
					except ValueError:
						race = -1

				if level > 0:
					# AE: koseli ayraclar RTL cizicide aynalanip yer degistirir - ayracsiz bicim
					if localeInfo.IsARABIC():
						row["name"].SetText("%s Lv.%d" % (cols[1], level))
					else:
						row["name"].SetText("%s [Lv.%d]" % (cols[1], level))
				else:
					row["name"].SetText(cols[1])
				color = EMPIRE_COLORS.get(empire, DEFAULT_ROW_COLOR)
				row["name"].SetFontColor(color[0], color[1], color[2])
				row["name"].Show()

				row["dmg"].SetText(self.__FormatDamage(cols[2]))
				row["dmg"].Show()

				try:
					row["gauge"].SetPercentage(float(cols[3]), 100)
				except ValueError:
					row["gauge"].SetPercentage(0, 100)
				row["gauge"].Show()

				row["pct"].SetText("%%%s" % cols[3])
				row["pct"].Show()

				self.__SetRowIcon(row, race)
			else:
				row["name"].Hide()
				row["dmg"].Hide()
				row["gauge"].Hide()
				row["pct"].Hide()
				row["icon"].Hide()

		if visible > 0:
			self.__Relayout(visible)

		meCols = mePart.split("|")
		if len(meCols) >= 3 and meCols[0] != "0":
			# AE: parantezler RTL cizicide aynalanip basa tasinir - parantezsiz bicim
			if localeInfo.IsARABIC():
				self.myLine.SetText("Sen: %s. sira - %s - %%%s" % (meCols[0], self.__FormatDamage(meCols[1]), meCols[2]))
			else:
				self.myLine.SetText("Sen: %s. sira - %s (%%%s)" % (meCols[0], self.__FormatDamage(meCols[1]), meCols[2]))
		else:
			self.myLine.SetText("Sen: henuz hasar yok")

		if not self.IsShow() and not self.__userClosed:
			self.Open()

	def OnBossEnd(self, vidStr):
		try:
			vid = int(vidStr)
		except (ValueError, TypeError):
			return
		# baska (taze) boss'un penceresi acikken yanlis kapatma olmasin
		if self.__bossVid and vid != self.__bossVid:
			return
		self.__bossVid = 0
		self.__lastRecvTime = 0.0
		self.__userClosed = 0
		self.Hide()

	def Open(self):
		# varsayilan konum: sol alt (Eski_A kalibi); yalniz ilk acilista atanir,
		# sonraki acilislarda oyuncunun tasidigi konum korunur (oturum boyunca)
		if not self.__defaultPosSet:
			self.__defaultPosSet = 1
			height = Y_START + ROW_COUNT * Y_PASS + MYLINE_PAD + BOTTOM_PAD
			self.SetPosition(5, wndMgr.GetScreenHeight() - (height + 120))
		self.SetTop()
		self.Show()

	def Close(self):
		self.__userClosed = 1
		self.Hide()

	def OnUpdate(self):
		# yayin kesildiyse (boss oldu/despawn/uzaklasildi) kendini gizle
		if self.IsShow() and self.__lastRecvTime and app.GetTime() - self.__lastRecvTime > STALE_HIDE_SECONDS:
			self.Hide()
			self.__bossVid = 0

	def OnPressEscapeKey(self):
		self.Close()
		return 1
