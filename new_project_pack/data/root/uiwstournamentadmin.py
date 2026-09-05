# WS 1v1 Turnuva - GM yonetim paneli (ENABLE_WS_TOURNAMENT)
# Form degerleri /ws_admin komutlarina cevrilir; yetki kontrolu SERVER'da
# (cmd tablosu GM_HIGH_WIZARD) - buradaki IsGameMaster sadece kozmetik kapidir.
import ui
import net
import chr
import player

STATE_NAMES = { 0 : "Turnuva yok", 1 : "KAYIT DONEMI", 2 : "DEVAM EDIYOR" }


class WSAdminWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		# wndMgr python referansi tutmaz: referanssiz widget GC ile aninda yok olur
		self.__widgets = []
		self.__BuildWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.__widgets = []
		self.__editSlots = []
		self.board = None

	def __MakeText(self, x, y, text = "", r = 0.85, g = 0.85, b = 0.85):
		line = ui.TextLine()
		line.SetParent(self.board)
		line.SetPosition(x, y)
		line.SetText(text)
		line.SetFontColor(r, g, b)
		line.Show()
		self.__widgets.append(line)
		return line

	def __MakeSmallButton(self, x, y, text, event):
		btn = ui.Button()
		btn.SetParent(self.board)
		btn.SetPosition(x, y)
		btn.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
		btn.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
		btn.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
		btn.SetText(text)
		btn.SetEvent(event)
		btn.Show()
		self.__widgets.append(btn)
		return btn

	def __MakeEdit(self, x, y, width, defaultText, maxLen = 12):
		slot = ui.SlotBar()
		slot.SetParent(self.board)
		slot.SetSize(width, 18)
		slot.SetPosition(x, y)
		slot.Show()

		edit = ui.EditLine()
		edit.SetParent(slot)
		edit.SetSize(width - 6, 16)
		edit.SetPosition(4, 2)
		edit.SetMax(maxLen)
		edit.SetText(defaultText)
		edit.Show()

		self.__editSlots.append(slot)
		return edit

	def __BuildWindow(self):
		self.SetSize(400, 360)
		self.__editSlots = []

		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetSize(400, 360)
		self.board.SetTitleName("WS Turnuvasi - GM Paneli")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.AddFlag("movable")
		self.board.AddFlag("float")
		self.board.Show()

		self.stateLine = self.__MakeText(15, 34, "Durum bilgisi icin turnuva penceresini yenileyin.", 1.0, 0.9, 0.4)

		self.__MakeText(15, 60, "Ucret (yang):")
		self.feeEdit = self.__MakeEdit(120, 58, 110, "100000000")
		self.__MakeText(240, 60, "Kayit (dk):")
		self.regEdit = self.__MakeEdit(320, 58, 50, "5", 3)

		self.__MakeText(15, 86, "Set:")
		self.setEdit = self.__MakeEdit(120, 84, 50, "3", 2)
		self.__MakeText(240, 86, "Mac (dk):")
		self.minuteEdit = self.__MakeEdit(320, 84, 50, "5", 3)

		self.__MakeText(15, 112, "Seviye min/max:")
		self.minLvEdit = self.__MakeEdit(120, 110, 50, "1", 3)
		self.maxLvEdit = self.__MakeEdit(180, 110, 50, "120", 3)
		self.__MakeText(240, 112, "Sinif (0-4):")
		self.jobEdit = self.__MakeEdit(320, 110, 50, "0", 1)

		self.__MakeText(15, 138, "Sinif: 0=Hepsi 1=Savasci 2=Ninja 3=Sura 4=Saman", 0.6, 0.6, 0.6)

		self.__MakeSmallButton(15, 162, "Turnuva Kur", ui.__mem_func__(self.__OnCreate))
		self.__MakeSmallButton(115, 162, "Baslat", ui.__mem_func__(self.__OnStart))
		self.__MakeSmallButton(215, 162, "Iptal Et", ui.__mem_func__(self.__OnCancel))
		self.__MakeSmallButton(315, 162, "Durum", ui.__mem_func__(self.__OnStatus))

		self.__MakeText(15, 196, "Diskalifiye (oyuncu adi):")
		self.dqEdit = self.__MakeEdit(170, 194, 130, "", 24)
		self.__MakeSmallButton(315, 194, "DQ", ui.__mem_func__(self.__OnDQ))

		self.__MakeText(15, 228, "Event flag'lar: ws_disabled ws_rake_pct ws_prize1_pct", 0.6, 0.6, 0.6)
		self.__MakeText(15, 244, "ws_prize2_pct ws_min_players ws_max_players", 0.6, 0.6, 0.6)
		self.__MakeText(15, 260, "ws_summon_seconds ws_allow_same_ip (/e ile ayarla)", 0.6, 0.6, 0.6)
		self.__MakeText(15, 290, "Not: Islem sonuclari sohbet/duyuru olarak gelir.", 0.6, 0.6, 0.6)
		self.__MakeText(15, 306, "Detayli durum icin CH99 uzerinde /ws_admin durum.", 0.6, 0.6, 0.6)

	# ------------------------------------------------------------------ actions
	def __GetNumber(self, edit, default):
		try:
			return int(edit.GetText())
		except ValueError:
			return default

	def __OnCreate(self):
		fee = self.__GetNumber(self.feeEdit, -1)
		if fee < 0:
			self.stateLine.SetText("Ucret gecersiz!")
			return

		cmd = "/ws_admin kur %d %d %d %d %d %d %d" % (
			fee,
			self.__GetNumber(self.setEdit, 3),
			self.__GetNumber(self.minuteEdit, 5),
			self.__GetNumber(self.minLvEdit, 1),
			self.__GetNumber(self.maxLvEdit, 120),
			self.__GetNumber(self.jobEdit, 0),
			self.__GetNumber(self.regEdit, 5))
		net.SendChatPacket(cmd)

	def __OnStart(self):
		net.SendChatPacket("/ws_admin baslat")

	def __OnCancel(self):
		net.SendChatPacket("/ws_admin iptal")

	def __OnStatus(self):
		net.SendChatPacket("/ws_admin durum")

	def __OnDQ(self):
		name = self.dqEdit.GetText().strip()
		if not name:
			self.stateLine.SetText("DQ icin oyuncu adi gir!")
			return
		net.SendChatPacket("/ws_admin dq " + name)
		self.dqEdit.SetText("")

	# ------------------------------------------------------------------ data
	def SetData(self, entryList, matchList, state, round, minLv, maxLv, jobFilter, setCount, matchMin, myStatus, secondsLeft, fee, pool):
		aliveCount = 0
		for entry in entryList:
			if entry[3]:
				aliveCount += 1
		self.stateLine.SetText("Durum: %s | Tur: %d | Kayit: %d | Hayatta: %d | Havuz: %s" % (
			STATE_NAMES.get(state, "?"), round, len(entryList), aliveCount, str(pool)))

	# ------------------------------------------------------------------ open/close
	def Open(self):
		if not chr.IsGameMaster(player.GetMainCharacterIndex()):
			return
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		try:
			net.SendWSTournamentRequestPacket()
		except AttributeError:
			pass

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return 1
