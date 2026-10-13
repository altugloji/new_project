# Orb Rush Etkinligi (Kure Avi / orb event) - kisiye ozel kure alani + siralama penceresi (server ENABLE_ORB_EVENT)
# Server her saat basi 5 dk boyunca oyuncunun etrafina KISIYE OZEL kureler dogurur
# (mavi = +2 puan, beyaz = -1 puan ceza); client kureleri dunya efekti olarak cizer, toplama
# server tarafinda olur. Pencere uibossrank/uiffaboard kalibiyla DINAMIK kurulur
# (uiscript yok): widget'lar BIR KEZ yaratilir, guncellemede sadece SetText yapilir.
# Server komutlari (CHAT_TYPE_COMMAND; game.py serverCommandList):
#   orb_start <eid> <kalanSn>                 tur basladi / tur icinde hazir olundu
#   orb_put <slot>,<gx>,<gy>,<tip>;...        kure(ler) dogdu (tip 1 beyaz, 2 mavi); ayni slot = degistir
#   orb_take <slot> <kazanc> <toplam> <nx> <ny> <ntip>   kure toplandi; ntip != 0 ise ayni slota yenisi
#   orb_clear                                 tum kureleri sil (pano kalir)
#   orb_top <kalanSn>#<sira>|<isim>|<puan>;.. ilk 10 (sayaci da yeniden esler)
#   orb_me <sira> <puan> <katilimci>          kendi siran (0 = ilk 100 disi -> "100+")
#   orb_end <eid>                             tur bitti: kureler silinir, pano 60 sn son durumu gosterir
#   orb_result <sira> <adet>                  odul hediye kutusuna gitti
# Eski server bu komutlari gondermez; pencere kendini gostermez (skew-safe).
# Koordinat: server GLOBAL cm yollar; background.GlobalPositionToLocalPosition ile
# yerel (lx, ly) alinir, z = background.GetHeight(lx, ly) + 120. Harita henuz
# yuklenmemisse GetHeight 0 doner: 250 ms'de bir, en fazla 4 deneme (~1 sn) beklenir;
# orb_* komutlari hep oyun fazinda geldiginden bu yalniz emniyet kemeri, duz/sifir
# yukseklikli arazide (GetHeight gercekten 0) kure 1 sn icinde yine cizilir.
# Efekt binding'i (effect.CreateWorld/DeleteEffect) eski binary'de yoksa alan
# sessizce kapali kalir, pano yine calisir (hasattr kapisi).
# AE (Arapca) kurali (uibossrank dersi): CP_ARABIC'te ALIGN_LEFT metni ankrajdan
# SOLA uzatir; ALIGN_RIGHT kaydirmaz = LTR sol-hizali karsiligi. Bu yuzden AE'de
# tum TextLine'lara SetHorizontalAlignRight verilir ve sag sutun da sol ankrajdan
# baslar; metin bicimlerinde ( ) [ ] < > yoktur.
# NOT: wndMgr python referansi tutmaz - her widget self uzerinde saklanmali.
# NOT: OnPressEscapeKey BILEREK yok (uiffaboard dersi): pano pasif HUD'dir.
import ui
import app
import wndMgr
import localeInfo
import effect
import background
import snd
import dbg
import _weakref

ORB_BLUE_PATH = "d:/ymir work/effect/etc/orb_event/orb_blue.mse"		# tip 2 (2 puan)
ORB_WHITE_PATH = "d:/ymir work/effect/etc/orb_event/orb_white.mse"	# tip 1 (-1 puan, ceza)
ORB_GOLD_PATH = "d:/ymir work/effect/etc/orb_event/orb_gold.mse"		# tip 3 (10 puan, 3 sn omurlu, %10 sans)
GOLD_SOUND = "sound/ui/money.wav"	# sari kure toplama sesi
ORB_HEIGHT_OFFSET = 120.0		# zeminden yukseklik (cm)
HEIGHT_RETRY_INTERVAL = 0.25	# GetHeight 0 donerse yeniden deneme araligi (sn)
HEIGHT_RETRY_MAX = 4			# en fazla deneme (~1 sn), sonra z = 0 + offset ile yine de cizilir (sifir yukseklikli arazi)
PICK_SOUND = "sound/ui/pick.wav"
PENALTY_SOUND = "sound/ui/drop.wav"	# beyaz kure (eksi puan) sesi

BOARD_WIDTH = 250			# baslik "Orb Rush Etkinligi" + sayac ayni satirda
ROW_COUNT = 10					# server ORB_EVENT_TOP_COUNT ile ayni
ROW_HEIGHT = 16
TITLE_Y = 8
ROWS_Y = 26
NAME_X = 12
RIGHT_X = BOARD_WIDTH - 12		# LTR: sag sutun ankraji (ALIGN_RIGHT = sag kenar)
RIGHT_X_AE = 196				# AE: sag sutun sol ankrajdan baslar (dosya basi nota bak)
TIME_X_AE = 160					# AE: sayac "Kalan 09:32" ~70 px, 176'dan saga akinca 230'u tasar; baslik x=12 ~60 px'te biter
ME_Y = ROWS_Y + ROW_COUNT * ROW_HEIGHT + 4
PART_Y = ME_Y + 16
BOARD_HEIGHT = ME_Y + 20		# katilimci satiri kaldirildi (v3), pano kendi satirinda biter
DEFAULT_X = 10					# sol kenar
DEFAULT_MIN_Y = 60				# buff ikonlari (uiaffectshower 10,10 + 25px satirlar) altina
TOP_STALE_SECONDS = 20.0		# tur aktifken bu kadar sure orb_top gelmezse gizle (yayin kesildi)
END_SHOW_SECONDS = 60.0			# orb_end sonrasi son durum bu kadar kalir
RESULT_SHOW_SECONDS = 15.0		# orb_result pano acikken geldiyse en az bu kadar daha gorunur

RANK_COLORS = {
	0 : (1.0, 0.85, 0.2),	# altin
	1 : (0.8, 0.8, 0.85),	# gumus
	2 : (0.8, 0.55, 0.3),	# bronz
}
DEFAULT_ROW_COLOR = (0.9, 0.9, 0.9)

# Oyuncunun tasidigi pencere konumu; warp'ta interface yeniden kurulsa da korunur
_BOARD_POS = None
# Yuklenemeyen efekt yollari (.mse pakette yoksa): CEffectManager::RegisterEffect her
# cagrida LoadScript'i yeniden dener + TraceError yazar (EffectManager.cpp:136-141);
# yol bazinda BIR kez vazgecilir ve tek satir log dusulur, slot bazinda spam olmaz
_FAILED_PATHS = {}


class _OrbTicker(ui.Window):
	# Gorunmez 0x0 pencere: wndMgr OnUpdate'i yalniz GORUNEN pencerelere cagirir
	# (PythonWindow.cpp CWindow::Update IsShow kapisi). Pano gizliyken de bekleyen
	# kurelerin yukseklik denemesi surmeli diye alan kendi tetikleyicisini tasir;
	# yalniz bekleyen kure varken gosterilir.

	def __init__(self, field):
		ui.Window.__init__(self)
		# zayif referans: ui.Window __del__'li oldugundan py2 GC alan<->tetikleyici
		# dongusunu toplayamaz; proxy ile dongu kurulmaz
		self.__field = _weakref.proxy(field)
		self.SetSize(0, 0)
		self.SetPosition(0, 0)
		try:
			self.AddFlag("not_pick")
		except RuntimeError:
			pass

	def __del__(self):
		ui.Window.__del__(self)

	def OnUpdate(self):
		try:
			self.__field.Update()
		except ReferenceError:
			self.Hide()


class OrbField(object):
	# slot -> dunya efekti; server slot numarasiyla konusur (0..24)

	def __init__(self):
		self.__enabled = hasattr(effect, "CreateWorld") and hasattr(effect, "DeleteEffect")
		self.__effects = {}		# slot -> efekt id (>= 0)
		self.__types = {}		# slot -> kure tipi (1 beyaz, 2 mavi, 3 sari); ses secimi icin
		self.__pending = {}		# slot -> [gx, gy, tip, sonrakiDeneme, denemeSayisi]
		self.__ticker = None
		if self.__enabled:
			self.__ticker = _OrbTicker(self)

	def Destroy(self):
		self.Clear()
		if self.__ticker:
			self.__ticker.Hide()
			self.__ticker = None

	def IsEnabled(self):
		return self.__enabled

	def GetCount(self):
		return len(self.__effects)

	def __TypeOf(self, slot):
		# slotta duran kurenin tipi (efekt olusmus ya da yukseklik bekliyor), yoksa 0
		ent = self.__pending.get(slot)
		if ent:
			return ent[2]
		return self.__types.get(slot, 0)

	def __Path(self, otype):
		if otype == 3:
			return ORB_GOLD_PATH
		if otype == 2:
			return ORB_BLUE_PATH
		return ORB_WHITE_PATH

	def __DeleteEffect(self, slot):
		eid = self.__effects.pop(slot, None)
		if eid is not None and eid >= 0:
			try:
				effect.DeleteEffect(eid)
			except Exception:
				pass

	def __ShowTicker(self):
		if self.__ticker and not self.__ticker.IsShow():
			self.__ticker.Show()

	def __HideTicker(self):
		if self.__ticker and self.__ticker.IsShow():
			self.__ticker.Hide()

	def __TryCreate(self, slot, ent, now):
		# 1 = slot bitti (yaratildi ya da vazgecildi), 0 = yeniden dene
		path = self.__Path(ent[2])
		if path in _FAILED_PATHS:
			return 1
		try:
			lx, ly = background.GlobalPositionToLocalPosition(int(ent[0]), int(ent[1]))
			h = background.GetHeight(float(lx), float(ly))
		except Exception:
			return 1
		if h == 0.0 and ent[4] < HEIGHT_RETRY_MAX:
			# harita/zemin henuz yuklenmedi: biraz sonra tekrar
			ent[4] += 1
			ent[3] = now + HEIGHT_RETRY_INTERVAL
			return 0
		try:
			idx = effect.CreateWorld(path, float(lx), float(ly), float(h) + ORB_HEIGHT_OFFSET)
		except Exception:
			idx = -1
		if idx is None or idx < 0:
			# efekt dosyasi pakette yok vb.: yol bir kez loglanir, bir daha hic denenmez
			_FAILED_PATHS[path] = 1
			dbg.TraceError("OrbField: efekt yuklenemedi %s" % path)
			return 1
		self.__effects[slot] = idx
		return 1

	def Put(self, slot, gx, gy, otype):
		if not self.__enabled:
			return
		# ayni slot yeniden = degistir (once eskisi silinir)
		self.__DeleteEffect(slot)
		self.__pending.pop(slot, None)
		if otype != 1 and otype != 2 and otype != 3:
			return
		now = app.GetTime()
		self.__types[slot] = otype
		ent = [gx, gy, otype, now, 0]
		if not self.__TryCreate(slot, ent, now):
			self.__pending[slot] = ent
			self.__ShowTicker()

	def PutPayload(self, payload):
		# "<slot>,<gx>,<gy>,<tip>;<slot>,<gx>,<gy>,<tip>;..." (en fazla 12 girdi)
		for token in str(payload).split(";"):
			cols = token.split(",")
			if len(cols) < 4:
				continue
			try:
				slot = int(cols[0])
				gx = int(cols[1])
				gy = int(cols[2])
				otype = int(cols[3])
			except ValueError:
				continue
			self.Put(slot, gx, gy, otype)

	def Take(self, slot):
		self.__DeleteEffect(slot)
		self.__pending.pop(slot, None)
		self.__types.pop(slot, None)
		if not self.__pending:
			self.__HideTicker()

	def Collect(self, slot, nx, ny, ntype, gain=1):
		# orb_take: slot silinir, ses calar (eksi puanda ceza, sari kurede ozel ses), ntip != 0 ise ayni slota yenisi konur
		takenType = self.__TypeOf(slot)
		self.Take(slot)
		try:
			if takenType == 3:
				snd.PlaySound(GOLD_SOUND)
			elif gain < 0:
				snd.PlaySound(PENALTY_SOUND)
			else:
				snd.PlaySound(PICK_SOUND)
		except Exception:
			pass
		if ntype:
			self.Put(slot, nx, ny, ntype)

	def Clear(self):
		# warp'ta motor efektleri zaten siler ama select fazina donuste silmez;
		# bayat id'de DeleteEffect zararsizdir (EffectManager map'te bulamayinca doner)
		for slot in self.__effects.keys():
			self.__DeleteEffect(slot)
		self.__effects = {}
		self.__pending = {}
		self.__types = {}
		self.__HideTicker()

	def Update(self):
		# tetikleyici pencereden kare basina; bekleyen yoksa tetikleyici kapanir
		if not self.__pending:
			self.__HideTicker()
			return
		now = app.GetTime()
		for slot in self.__pending.keys():
			ent = self.__pending[slot]
			if now < ent[3]:
				continue
			if self.__TryCreate(slot, ent, now):
				del self.__pending[slot]
		if not self.__pending:
			self.__HideTicker()


class OrbBoard(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__eid = 0
		self.__active = 0
		self.__endTime = 0.0
		self.__lastTopTime = 0.0
		self.__hideAt = 0.0
		self.__shownRemain = -1
		self.__myRank = 0
		self.__myScore = 0
		self.__meKnown = 0		# ilk orb_me geldi mi (sira ancak o zaman bilinir)
		self.__minScore = 0		# odul esigi (orb_start ile gelir)
		self.__tookAny = 0		# bu turda en az bir kure toplandi mi (negatif puanda da 'henuz toplamadin' yazilmasin)
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
		self.titleLine = None
		self.timeLine = None
		self.myLine = None
		self.partLine = None

	def __MakeText(self, x, y, r, g, b, rightColumn=0):
		text = ui.TextLine()
		text.SetParent(self.board)
		if localeInfo.IsARABIC():
			# AE: ALIGN_RIGHT = ankrajdan saga akis; sag sutun da sol ankrajdan baslar
			if rightColumn:
				x = RIGHT_X_AE
			text.SetHorizontalAlignRight()
		elif rightColumn:
			text.SetHorizontalAlignRight()
		text.SetPosition(x, y)
		text.SetFontColor(r, g, b)
		text.SetText("")
		text.Show()
		self.__widgets.append(text)
		return text

	def __BuildWindow(self):
		self.SetSize(BOARD_WIDTH, BOARD_HEIGHT)

		# tasima bayraklari DIS pencerede (uiffaboard dersi); board "attach" ile
		# tiklamalari dis pencerenin tasimasina baglar
		self.AddFlag("movable")
		self.AddFlag("float")

		self.board = ui.ThinBoard()
		self.board.SetParent(self)
		self.board.SetSize(BOARD_WIDTH, BOARD_HEIGHT)
		self.board.AddFlag("attach")
		self.board.Show()

		self.titleLine = self.__MakeText(NAME_X, TITLE_Y, 1.0, 0.85, 0.2)
		self.titleLine.SetText("Orb Rush Etkinligi")
		self.timeLine = self.__MakeText(RIGHT_X, TITLE_Y, 1.0, 0.85, 0.1, 1)
		if localeInfo.IsARABIC():
			# sayac puan sutunundan uzun: 176'dan saga akinca ThinBoard'u tasar, ayri ankraj
			self.timeLine.SetPosition(TIME_X_AE, TITLE_Y)

		for i in xrange(ROW_COUNT):
			y = ROWS_Y + i * ROW_HEIGHT
			color = RANK_COLORS.get(i, DEFAULT_ROW_COLOR)
			nameText = self.__MakeText(NAME_X, y, color[0], color[1], color[2])
			scoreText = self.__MakeText(RIGHT_X, y, color[0], color[1], color[2], 1)
			self.__rows.append({"name" : nameText, "score" : scoreText})

		self.myLine = self.__MakeText(NAME_X, ME_Y, 0.3, 1.0, 0.3)

	def __ClearRows(self):
		for row in self.__rows:
			row["name"].SetText("")
			row["score"].SetText("")

	def __RefreshMyLine(self):
		if not self.__tookAny and self.__myScore == 0 and self.__myRank <= 0:	# negatif puan = zaten toplamis (relog)
			self.myLine.SetText("Henuz kure toplamadin")
			return
		if self.__myScore <= 0:
			# beyaz kureler eksi puan verir: toplam 0 veya negatifse siralamaya girmez
			self.myLine.SetText("Siralama disi - Puan %d" % self.__myScore)
			return
		# odul esiginin altindaysa hatirlatma (ayracsiz: AE uyumu)
		hint = ""
		if self.__minScore > 0 and self.__myScore < self.__minScore:
			hint = " - Odul icin %d" % self.__minScore
		if not self.__meKnown:
			# ilk orb_me (3 sn'lik snapshot) gelmeden sira bilinmez; "100+" yazilmaz
			self.myLine.SetText("Puan %d%s" % (self.__myScore, hint))
			return
		if self.__myRank > 0:
			rankText = "%d" % self.__myRank
		else:
			rankText = "100+"
		self.myLine.SetText("Siran %s - Puan %d%s" % (rankText, self.__myScore, hint))

	def __UpdateCountdown(self, now):
		remain = int(self.__endTime - now + 0.999)
		if remain < 0:
			remain = 0
		if remain != self.__shownRemain:
			self.__shownRemain = remain
			self.timeLine.SetText("Kalan %02d:%02d" % (remain / 60, remain % 60))

	def __DefaultPos(self):
		# gorev mektubu sutunu (interfacemodule.__ArrangeQuestButton) y = 170*H/600'den
		# asagi dizilir, hediye kutusu ikonu sol-altta, buff ikonlari sol-ustte:
		# pano mektuplarin USTUNE, buff ikonlarinin altina gelecek sekilde yerlesir
		screenHeight = wndMgr.GetScreenHeight()
		questY = 170 * screenHeight / 600
		y = questY - BOARD_HEIGHT - 4
		if y < DEFAULT_MIN_Y:
			y = DEFAULT_MIN_Y
		return (DEFAULT_X, y)

	def __PosOnScreen(self, pos):
		try:
			x = int(pos[0])
			y = int(pos[1])
		except (TypeError, ValueError, IndexError):
			return 0
		if x < 0 or y < 0:
			return 0
		if x + BOARD_WIDTH > wndMgr.GetScreenWidth() or y + BOARD_HEIGHT > wndMgr.GetScreenHeight():
			return 0
		return 1

	def Open(self):
		# oyuncunun tasidigi konum modul duzeyinde saklanir (warp'ta pencere yeniden
		# kurulur); yoksa ya da ekran disinda kaldiysa varsayilan
		pos = _BOARD_POS
		if pos is None or not self.__PosOnScreen(pos):
			pos = self.__DefaultPos()
		self.SetPosition(pos[0], pos[1])
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()

	def OnMoveWindow(self, x, y):
		# wndMgr movable surukleme sonrasi cagirir (PythonWindowManager OnMoveWindow)
		global _BOARD_POS
		_BOARD_POS = (x, y)

	def OnRoundStart(self, eid, remain, minscore=0):
		now = app.GetTime()
		self.__eid = eid
		self.__active = 1
		self.__minScore = minscore		# odul icin gereken en az puan (server orb_start 3. alani; 0 = esik yok)
		self.__endTime = now + remain
		self.__lastTopTime = now
		self.__hideAt = 0.0
		self.__shownRemain = -1
		self.__myRank = 0
		self.__myScore = 0
		self.__meKnown = 0
		self.__tookAny = 0
		self.__ClearRows()
		self.__RefreshMyLine()
		self.__UpdateCountdown(now)
		self.Open()

	def SetTopPayload(self, payload):
		# "<kalanSn>#<sira>|<isim>|<puan>;..." (en fazla 10 girdi, isim <= 16 karakter)
		try:
			parts = str(payload).split("#")
			remain = int(parts[0])
			rowsPart = parts[1] if len(parts) > 1 else ""
		except (ValueError, IndexError):
			return

		now = app.GetTime()
		self.__lastTopTime = now
		if self.__active:
			# sayaci server ile yeniden esle
			self.__endTime = now + remain
			self.__shownRemain = -1

		rows = []
		if rowsPart:
			for token in rowsPart.split(";"):
				cols = token.split("|")
				if len(cols) >= 3:
					rows.append(cols)

		for i in xrange(ROW_COUNT):
			row = self.__rows[i]
			if i < len(rows):
				cols = rows[i]
				row["name"].SetText("%s. %s" % (cols[0], cols[1]))
				row["score"].SetText(cols[2])
			else:
				row["name"].SetText("")
				row["score"].SetText("")

		if self.__active and not self.IsShow():
			# bayat-gizleme sonrasi yayin geri geldi: tekrar goster
			self.__UpdateCountdown(now)
			self.Open()

	def SetMe(self, rank, score, participants):
		self.__myRank = rank
		self.__myScore = score
		self.__meKnown = 1
		self.__RefreshMyLine()
		# katilimci sayisi gosterilmiyor (kullanici istegi); server alani yine gelir, yok sayilir

	def OnTake(self, gain, total):
		# kendi puanin aninda guncellenir; sira bir sonraki orb_me ile gelir
		self.__tookAny = 1
		self.__myScore = total
		self.__RefreshMyLine()

	def OnRoundEnd(self, eid):
		if not self.__active and not self.IsShow():
			return
		self.__active = 0
		self.__shownRemain = -1
		self.timeLine.SetText("Bitti")
		if self.IsShow():
			self.__hideAt = app.GetTime() + END_SHOW_SECONDS

	def OnResult(self, rank, count):
		# odul hediye kutusuna gitti (server ayrica CHAT_TYPE_INFO yazar); pano gizliyse
		# yeniden acilmaz, acik ise bir sure daha kalir
		self.myLine.SetText("Odul: %d. sira - %d adet hediye kutunda" % (rank, count))
		if self.IsShow():
			now = app.GetTime()
			if self.__hideAt < now + RESULT_SHOW_SECONDS:
				self.__hideAt = now + RESULT_SHOW_SECONDS

	def OnUpdate(self):
		if not self.IsShow():
			return
		now = app.GetTime()
		if self.__active:
			self.__UpdateCountdown(now)
			if self.__lastTopTime and now - self.__lastTopTime > TOP_STALE_SECONDS:
				# yayin kesildi (DC / kanal gecisi / orb_end gelmedi): gizle; orb_top
				# geri gelirse SetTopPayload yeniden acar
				self.Hide()
			return
		if self.__hideAt and now >= self.__hideAt:
			self.__hideAt = 0.0
			self.Hide()

	# NOT: OnPressEscapeKey BILEREK yok (uiffaboard dersi): ESC oyunda surekli
	# kullanilir; pano pasif HUD'dir, tur bitince/yayin kesilince kendini gizler.
