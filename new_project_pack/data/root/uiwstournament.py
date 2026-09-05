# WS 1v1 Turnuva - oyuncu penceresi (ENABLE_WS_TOURNAMENT)
# Veri: GC 247 (net.SendWSTournamentRequestPacket -> game.py WST_SetData -> interface -> SetData)
# Aksiyonlar chat komutlariyla gider (/ws kayit vb.) - yetki her zaman server'da.
import ui
import net
import app

STATE_NAMES = { 0 : "Turnuva yok", 1 : "KAYITLAR ACIK", 2 : "TURNUVA DEVAM EDIYOR" }
MY_STATUS_NAMES = { 0 : "Kayitli degilsin", 1 : "KAYITLISIN", 2 : "Elendin", 3 : "AKTIF MACIN VAR!" }
JOB_NAMES = ("Savasci", "Ninja", "Sura", "Saman")
LIST_PAGE_SIZE = 14
REFRESH_SECONDS = 5.0


def JobFilterName(jobFilter):
	if jobFilter <= 0 or jobFilter > 4:
		return "Hepsi"
	return JOB_NAMES[jobFilter - 1]


def MatchLineText(matchInfo):
	(nameA, nameB, round, state, result) = matchInfo
	if state == 3:
		if result == 1:
			durum = nameA + " kazandi"
		elif result == 2:
			durum = nameB + " kazandi"
		elif result == 3:
			durum = "cift eleme"
		else:
			durum = "bitti"
	elif state == 2:
		durum = "OYNANIYOR"
	elif state == 1:
		durum = "cagrildi"
	else:
		durum = "bekliyor"
	return "T%d: %s vs %s  [%s]" % (round, nameA, nameB, durum)


class WSTournamentWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__entryList = []
		self.__matchList = []
		self.__entryPage = 0
		self.__matchPage = 0
		self.__nextRefreshTime = 0.0
		# wndMgr python referansi tutmaz: referanssiz widget GC ile aninda yok olur
		self.__widgets = []
		self.__BuildWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()
		self.__widgets = []
		self.board = None

	def __MakeText(self, x, y, text = "", r = 0.85, g = 0.85, b = 0.85):
		line = ui.TextLine()
		line.SetParent(self.board)
		line.SetPosition(x, y)
		line.SetText(text)
		line.SetFontColor(r, g, b)
		line.Show()
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

	def __BuildWindow(self):
		self.SetSize(470, 470)

		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetSize(470, 470)
		self.board.SetTitleName("WS Turnuvasi")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.AddFlag("movable")
		self.board.AddFlag("float")
		self.board.Show()

		self.stateLine = self.__MakeText(15, 34, "Turnuva bilgisi bekleniyor...", 1.0, 0.9, 0.4)
		self.feeLine = self.__MakeText(15, 52, "")
		self.ruleLine = self.__MakeText(15, 68, "")
		self.timeLine = self.__MakeText(15, 84, "")
		self.myLine = self.__MakeText(15, 100, "", 0.6, 1.0, 0.6)

		self.__MakeSmallButton(15, 122, "Kayit Ol", ui.__mem_func__(self.__OnRegister))
		self.__MakeSmallButton(85, 122, "Iptal", ui.__mem_func__(self.__OnUnregister))
		self.__MakeSmallButton(155, 122, "Izle", ui.__mem_func__(self.__OnWatch))
		self.__MakeSmallButton(225, 122, "Yenile", ui.__mem_func__(self.__OnRefresh))

		self.entryHeader = self.__MakeText(15, 150, "Katilimcilar (0)", 1.0, 1.0, 1.0)
		self.__MakeSmallButton(155, 147, "<", ui.__mem_func__(self.__EntryPrevPage))
		self.__MakeSmallButton(195, 147, ">", ui.__mem_func__(self.__EntryNextPage))

		self.matchHeader = self.__MakeText(245, 150, "Maclar (0)", 1.0, 1.0, 1.0)
		self.__MakeSmallButton(385, 147, "<", ui.__mem_func__(self.__MatchPrevPage))
		self.__MakeSmallButton(425, 147, ">", ui.__mem_func__(self.__MatchNextPage))

		self.entryLines = []
		self.matchLines = []
		for i in xrange(LIST_PAGE_SIZE):
			self.entryLines.append(self.__MakeText(15, 172 + i * 19, ""))
			self.matchLines.append(self.__MakeText(245, 172 + i * 19, ""))

	# ------------------------------------------------------------------ actions
	def __OnRegister(self):
		net.SendChatPacket("/ws kayit")
		self.__nextRefreshTime = app.GetTime() + 1.0

	def __OnUnregister(self):
		net.SendChatPacket("/ws iptal")
		self.__nextRefreshTime = app.GetTime() + 1.0

	def __OnWatch(self):
		net.SendChatPacket("/ws izle")

	def __OnRefresh(self):
		self.__Request()

	def __EntryPrevPage(self):
		if self.__entryPage > 0:
			self.__entryPage -= 1
			self.__RefreshLists()

	def __EntryNextPage(self):
		if (self.__entryPage + 1) * LIST_PAGE_SIZE < len(self.__entryList):
			self.__entryPage += 1
			self.__RefreshLists()

	def __MatchPrevPage(self):
		if self.__matchPage > 0:
			self.__matchPage -= 1
			self.__RefreshLists()

	def __MatchNextPage(self):
		if (self.__matchPage + 1) * LIST_PAGE_SIZE < len(self.__matchList):
			self.__matchPage += 1
			self.__RefreshLists()

	def __Request(self):
		try:
			net.SendWSTournamentRequestPacket()
		except AttributeError:
			pass
		self.__nextRefreshTime = app.GetTime() + REFRESH_SECONDS

	# ------------------------------------------------------------------ data
	def SetData(self, entryList, matchList, state, round, minLv, maxLv, jobFilter, setCount, matchMin, myStatus, secondsLeft, fee, pool):
		self.__entryList = entryList
		self.__matchList = matchList

		self.stateLine.SetText("Durum: %s   (Tur %d)" % (STATE_NAMES.get(state, "?"), round))
		self.feeLine.SetText("Ucret: %s yang   |   Odul havuzu: %s yang" % (str(fee), str(pool)))
		self.ruleLine.SetText("Seviye: %d-%d   Sinif: %s   Set: %d   Mac: %d dk" % (minLv, maxLv, JobFilterName(jobFilter), setCount, matchMin))

		if state == 1 and secondsLeft > 0:
			self.timeLine.SetText("Kayit icin kalan sure: %d dk %d sn" % (secondsLeft / 60, secondsLeft % 60))
		else:
			self.timeLine.SetText("")

		self.myLine.SetText(MY_STATUS_NAMES.get(myStatus, ""))

		self.__entryPage = 0
		self.__matchPage = 0
		self.__RefreshLists()

	def __RefreshLists(self):
		aliveCount = 0
		for entry in self.__entryList:
			if entry[3]:
				aliveCount += 1

		self.entryHeader.SetText("Katilimcilar (%d/%d)" % (aliveCount, len(self.__entryList)))
		self.matchHeader.SetText("Maclar (%d)" % len(self.__matchList))

		start = self.__entryPage * LIST_PAGE_SIZE
		for i in xrange(LIST_PAGE_SIZE):
			if start + i < len(self.__entryList):
				(name, level, job, alive) = self.__entryList[start + i]
				jobName = JOB_NAMES[job] if job < 4 else "?"
				if alive:
					self.entryLines[i].SetText("%s  Lv%d %s" % (name, level, jobName))
					self.entryLines[i].SetFontColor(0.85, 0.85, 0.85)
				else:
					self.entryLines[i].SetText("%s  Lv%d %s [ELENDI]" % (name, level, jobName))
					self.entryLines[i].SetFontColor(0.55, 0.35, 0.35)
			else:
				self.entryLines[i].SetText("")

		start = self.__matchPage * LIST_PAGE_SIZE
		for i in xrange(LIST_PAGE_SIZE):
			if start + i < len(self.__matchList):
				self.matchLines[i].SetText(MatchLineText(self.__matchList[start + i]))
				if self.__matchList[start + i][3] == 2:
					self.matchLines[i].SetFontColor(0.5, 1.0, 0.5)
				else:
					self.matchLines[i].SetFontColor(0.85, 0.85, 0.85)
			else:
				self.matchLines[i].SetText("")

	# ------------------------------------------------------------------ open/close
	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.__Request()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return 1

	def OnUpdate(self):
		if not self.IsShow():
			return
		if app.GetTime() >= self.__nextRefreshTime:
			self.__Request()
