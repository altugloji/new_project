import ui
import app
import net
import item
import chat
import wndMgr
import constInfo
import localeInfo
import exception

# Metinlerin birincil kaynagi locale/tr/locale_game.txt LUCKYDRAW_* anahtarlaridir.
# Anahtar eksik/bos ya da %s yer tutuculari bozuksa asagidaki ASCII yedekler devreye
# girer: pencere calismaya devam eder, crash olmaz (locale repack yine de yapilmali).
_DEFAULTS = {
	"LUCKYDRAW_TITLE"			: "Sansli Cekilis",
	"LUCKYDRAW_TIME"			: "Kalan Sure: %02d:%02d:%02d",
	"LUCKYDRAW_CLOSED"			: "Etkinlik su an kapali.",
	"LUCKYDRAW_REQ_TITLE"		: "Katilim icin gerekenler:",
	"LUCKYDRAW_YANG_NEEDED"		: "Gereken Yang:",
	"LUCKYDRAW_PRIZES"			: "Oduller",
	"LUCKYDRAW_WINNER_LABEL"	: "%d. Kazanan",
	"LUCKYDRAW_WINNER_TICKETS"	: "%s (%s Katilim)",
	"LUCKYDRAW_JOINERS_TITLE"	: "Katilimcilar %s / %s",
	"LUCKYDRAW_TICKETS"			: "Biletlerin: %s / %s",
	"LUCKYDRAW_BTN_BUY"			: "Bilet Al",
	"LUCKYDRAW_BTN_REWARD"		: "Odul Al",
	"LUCKYDRAW_BTN_REFRESH"		: "Yenile",
	"LUCKYDRAW_BOTTOM_NOTE"		: "Etkinlik bitiminde cekilis yapilacak ve kazananlar ilan edilecektir.",
	"LUCKYDRAW_JOINER_TICKETS"	: "%s bilet",
	"LUCKYDRAW_JOIN_SENT"		: "Katilim istegi gonderildi. Guncel durumu Yenile ile gorebilirsiniz.",
	"LUCKYDRAW_REWARD_SENT"		: "Odul talebi gonderildi.",
}

def _L(key):
	value = getattr(localeInfo, key, None)
	if not value:
		return _DEFAULTS[key]
	return value

def _F(key, args):
	# locale degeri format bozuksa (orn. TAB/%s kaybi) ASCII yedekle formatla
	try:
		return _L(key) % args
	except (TypeError, ValueError):
		return _DEFAULTS[key] % args

LD_MAX_WINNERS = 5
LD_MAX_REWARDS = 5
LD_MAX_REQ_ITEMS = 5
LD_MAX_JOINER_LIST = 20

# Bilet Al butonu gorseli (etkinlik aciksa gorunur; dosya yoksa standart butona duser)
TICKET_BUY_IMAGE_PATH = "d:/ymir work/ui/ticket_buy.png"

# --- Giris tanitim gorseli (promo) ---
# Kullanicinin koyacagi gorsel: 350x214 PNG
# (png uzantisi ScriptLib/Resource.cpp'de kayitli, D3DX ile cozulur)
# Kaynak dosya: pack/yw_etc/ymir work/ui/luckydraw_promo.png
PROMO_IMAGE_PATH = "d:/ymir work/ui/luckydraw_promo.png"
PROMO_WIDTH = 350
PROMO_HEIGHT = 214

# Modul bayragi: client PROCESS'i basina 1 kez gosterim. Kanal/karakter degisiminde
# modul yeniden yuklenmedigi icin bayrak korunur; oyun tamamen kapatilip acilinca sifirlanir.
PROMO_SHOWN = 0

def WasPromoShown():
	return PROMO_SHOWN

def MarkPromoShown():
	global PROMO_SHOWN
	PROMO_SHOWN = 1

# --- Minimap gostergesi ---
# Etkinlik AKTIFKEN minimap'in solunda gorunen tiklanabilir ikon.
# Kaynak dosya: pack/yw_etc/ymir work/ui/lucky.png (dogal boyutunda cizilir)
INDICATOR_IMAGE_PATH = "d:/ymir work/ui/lucky.png"
MINIMAP_WIDTH = 136		# uiminimap.py: SetPosition(GetScreenWidth() - 136, 0)
INDICATOR_MARGIN = 5
INDICATOR_OFFSET_X = 10	# minimap'ten ekstra sola kaydirma
INDICATOR_OFFSET_Y = 10	# ekstra asagi kaydirma


class LuckyDrawPromoWindow(ui.ScriptWindow):
	"""Giriste gosterilen tiklanabilir tanitim gorseli; tiklayinca cekilis penceresi acilir."""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__Build()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.promoImage = None
		self.closeButton = None
		self.clickEvent = None
		self.imageLoaded = False

	def __Build(self):
		self.SetSize(PROMO_WIDTH, PROMO_HEIGHT)
		self.AddFlag("float")

		image = ui.ExpandedImageBox()
		image.SetParent(self)
		image.SetPosition(0, 0)
		try:
			image.LoadImage(PROMO_IMAGE_PATH)
			self.imageLoaded = True
		except:
			# gorsel pakette yoksa promo sessizce gosterilmez (crash yok)
			self.imageLoaded = False
		if self.imageLoaded:
			# gorsel hangi boyutta olursa olsun 250x150'ye olcekle
			imgW = image.GetWidth()
			imgH = image.GetHeight()
			if imgW > 0 and imgH > 0 and (imgW != PROMO_WIDTH or imgH != PROMO_HEIGHT):
				image.SetScale(PROMO_WIDTH / float(imgW), PROMO_HEIGHT / float(imgH))
		image.AddFlag("not_pick")	# tiklama bu pencereye dussun
		image.Show()
		self.promoImage = image

		closeBtn = ui.Button()
		closeBtn.SetParent(self)
		closeBtn.SetPosition(PROMO_WIDTH - 18, 3)
		closeBtn.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		closeBtn.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		closeBtn.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		closeBtn.SAFE_SetEvent(self.Close)
		closeBtn.Show()
		self.closeButton = closeBtn

		self.Hide()

	def IsImageLoaded(self):
		return self.imageLoaded

	def SetClickEvent(self, event):
		# interfacemodule ui.__mem_func__ ile sarilmis olarak gonderir
		self.clickEvent = event

	def OnMouseLeftButtonDown(self):
		if self.clickEvent:
			self.clickEvent()
		return True

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	@ui.WindowDestroy
	def Destroy(self):
		if self.closeButton:
			self.closeButton.SetEvent(0)
		self.clickEvent = None
		self.__Initialize()


class LuckyDrawMinimapIcon(ui.ScriptWindow):
	"""Etkinlik aktifken minimap'in solunda duran ikon; tiklayinca cekilis penceresi acilir."""

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__Build()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.iconImage = None
		self.clickEvent = None
		self.imageLoaded = False

	def __Build(self):
		self.AddFlag("float")

		image = ui.ExpandedImageBox()
		image.SetParent(self)
		image.SetPosition(0, 0)
		try:
			image.LoadImage(INDICATOR_IMAGE_PATH)
			self.imageLoaded = True
		except:
			# gorsel pakette yoksa gosterge sessizce gosterilmez (crash yok)
			self.imageLoaded = False

		if self.imageLoaded:
			imgW = image.GetWidth()
			imgH = image.GetHeight()
			if imgW > 0 and imgH > 0:
				self.SetSize(imgW, imgH)

		image.AddFlag("not_pick")	# tiklama bu pencereye dussun
		image.Show()
		self.iconImage = image

		self.Hide()

	def SetClickEvent(self, event):
		# interfacemodule ui.__mem_func__ ile sarilmis olarak gonderir
		self.clickEvent = event

	def OnMouseLeftButtonDown(self):
		if self.clickEvent:
			self.clickEvent()
		return True

	def Open(self):
		if not self.imageLoaded:
			return
		# minimap'in hemen solu (minimap sag-ust kosede 136px genisliginde)
		x = wndMgr.GetScreenWidth() - MINIMAP_WIDTH - self.GetWidth() - INDICATOR_MARGIN - INDICATOR_OFFSET_X
		self.SetPosition(x, INDICATOR_MARGIN + INDICATOR_OFFSET_Y)
		self.SetTop()
		self.Show()

	def Close(self):
		self.Hide()

	@ui.WindowDestroy
	def Destroy(self):
		self.clickEvent = None
		self.__Initialize()


class LuckyDrawWindow(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		# widget referanslari
		self.board = None
		self.tooltipItem = None
		self.reqTitle = None
		self.yangLabel = None
		self.yangValue = None
		self.reqSlots = None
		self.timeText = None
		self.ticketText = None
		self.joinButton = None
		self.rewardButton = None
		self.refreshButton = None
		self.prizeTitle = None
		self.winnerLabels = []
		self.winnerNameTexts = []
		self.rewardSlots = None
		self.joinerTitle = None
		self.joinerNameTexts = []
		self.joinerCountTexts = []
		self.bottomNote = None

		# paket verisi
		self.isActive = False
		self.endTimeStamp = 0.0
		self.lastShownSecond = -1
		self.joinCount = 0
		self.maxJoinCount = 0
		self.myJoinCount = 0
		self.maxTicketCount = 0
		self.neededYang = 0
		self.requirements = [(0, 0)] * LD_MAX_REQ_ITEMS
		self.winnerNames = [""] * LD_MAX_WINNERS
		self.winnerTickets = [0] * LD_MAX_WINNERS
		self.rewards = [[] for _i in xrange(LD_MAX_WINNERS)]
		self.joiners = [("", 0)] * LD_MAX_JOINER_LIST

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/luckydrawwindow.py")
		except:
			exception.Abort("LuckyDrawWindow.__LoadWindow.LoadScriptFile")
			return

		try:
			self.board = self.GetChild("board")
			self.reqTitle = self.GetChild("ReqTitle")
			self.yangLabel = self.GetChild("YangLabel")
			self.yangValue = self.GetChild("YangValue")
			self.reqSlots = self.GetChild("ReqSlots")
			self.timeText = self.GetChild("TimeText")
			self.ticketText = self.GetChild("TicketText")
			self.rewardButton = self.GetChild("RewardButton")
			self.refreshButton = self.GetChild("RefreshButton")
			self.prizeTitle = self.GetChild("PrizeTitle")
			self.winnerLabels = [self.GetChild("WinnerLabel%d" % i) for i in xrange(LD_MAX_WINNERS)]
			self.winnerNameTexts = [self.GetChild("WinnerName%d" % i) for i in xrange(LD_MAX_WINNERS)]
			self.rewardSlots = self.GetChild("RewardSlots")
			self.joinerTitle = self.GetChild("JoinerTitle")
			self.joinerNameTexts = [self.GetChild("JoinerName%d" % i) for i in xrange(LD_MAX_JOINER_LIST)]
			self.joinerCountTexts = [self.GetChild("JoinerCount%d" % i) for i in xrange(LD_MAX_JOINER_LIST)]
			self.bottomNote = self.GetChild("BottomNote")
		except:
			exception.Abort("LuckyDrawWindow.__LoadWindow.BindObject")
			return

		self.board.SetTitleName(_L("LUCKYDRAW_TITLE"))
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))

		self.reqTitle.SetText(_L("LUCKYDRAW_REQ_TITLE"))
		self.yangLabel.SetText(_L("LUCKYDRAW_YANG_NEEDED"))
		self.prizeTitle.SetText(_L("LUCKYDRAW_PRIZES"))
		self.bottomNote.SetText(_L("LUCKYDRAW_BOTTOM_NOTE"))

		self.rewardButton.SetText(_L("LUCKYDRAW_BTN_REWARD"))
		self.refreshButton.SetText(_L("LUCKYDRAW_BTN_REFRESH"))

		self.rewardButton.SAFE_SetEvent(self.OnReward)
		self.refreshButton.SAFE_SetEvent(self.OnRefresh)

		# Bilet Al = ticket_buy.png butonu, ayri "BuyBoard" panelinde
		# (ustunde kalan sure, 10px altinda buton, butonun 10px altinda biletlerin;
		# gorsel yoksa standart butona duser, boylece islev her durumda calisir)
		joinBtn = ui.Button()
		joinBtn.SetParent(self.GetChild("BuyBoard"))
		try:
			joinBtn.SetUpVisual(TICKET_BUY_IMAGE_PATH)
			joinBtn.SetOverVisual(TICKET_BUY_IMAGE_PATH)
			joinBtn.SetDownVisual(TICKET_BUY_IMAGE_PATH)
		except:
			joinBtn.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
			joinBtn.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
			joinBtn.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
			joinBtn.SetText(_L("LUCKYDRAW_BTN_BUY"))
		joinBtn.SetPosition(24, 36)
		joinBtn.SAFE_SetEvent(self.OnJoin)
		joinBtn.Hide()	# gorunurluk RefreshUI'da etkinlik durumuna gore
		self.joinButton = joinBtn

		# Biletlerin yazisi butonun HEMEN 10px altina (buton yuksekligi gorsele bagli)
		btnH = joinBtn.GetHeight()
		if btnH <= 0:
			btnH = 26
		self.ticketText.SetPosition(29, 36 + btnH + 10)

		self.reqSlots.SetOverInItemEvent(ui.__mem_func__(self.OnOverInReqSlot))
		self.reqSlots.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))
		self.rewardSlots.SetOverInItemEvent(ui.__mem_func__(self.OnOverInRewardSlot))
		self.rewardSlots.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))

		for i in xrange(LD_MAX_WINNERS):
			self.winnerLabels[i].SetText(_F("LUCKYDRAW_WINNER_LABEL", (i + 1)))

		self.Hide()

	def SetItemToolTip(self, tooltip):
		self.tooltipItem = tooltip

	# ---- binary -> game.py -> interface -> buraya gelen veri ----

	def ClearCachedData(self):
		self.isActive = False
		self.endTimeStamp = 0.0
		self.lastShownSecond = -1
		self.joinCount = 0
		self.maxJoinCount = 0
		self.myJoinCount = 0
		self.maxTicketCount = 0
		self.neededYang = 0
		self.requirements = [(0, 0)] * LD_MAX_REQ_ITEMS
		self.winnerNames = [""] * LD_MAX_WINNERS
		self.winnerTickets = [0] * LD_MAX_WINNERS
		self.rewards = [[] for _i in xrange(LD_MAX_WINNERS)]
		self.joiners = [("", 0)] * LD_MAX_JOINER_LIST

	def SetLuckyDrawInfo(self, endTime, joinCount, maxJoinCount, myJoinCount, maxTicketCount, neededYang):
		self.joinCount = joinCount
		self.maxJoinCount = maxJoinCount
		self.myJoinCount = myJoinCount
		self.maxTicketCount = maxTicketCount
		self.neededYang = neededYang
		if endTime > 0:
			self.isActive = True
			self.endTimeStamp = app.GetTime() + endTime
		else:
			self.isActive = False
			self.endTimeStamp = 0.0
		self.lastShownSecond = -1

	def SetRequirement(self, reqIndex, itemVnum, itemCount):
		if reqIndex < 0 or reqIndex >= LD_MAX_REQ_ITEMS:
			return
		self.requirements[reqIndex] = (itemVnum, itemCount)

	def SetWinnerName(self, winnerIndex, name, ticketCount=0):
		if winnerIndex < 0 or winnerIndex >= LD_MAX_WINNERS:
			return
		self.winnerNames[winnerIndex] = name
		self.winnerTickets[winnerIndex] = ticketCount

	def SetRewards(self, winnerIndex, rewardVnum):
		if winnerIndex < 0 or winnerIndex >= LD_MAX_WINNERS:
			return
		if not rewardVnum:
			return
		if len(self.rewards[winnerIndex]) >= LD_MAX_REWARDS:
			return
		self.rewards[winnerIndex].append(rewardVnum)

	def SetJoiner(self, joinerIndex, name, ticketCount):
		if joinerIndex < 0 or joinerIndex >= LD_MAX_JOINER_LIST:
			return
		self.joiners[joinerIndex] = (name, ticketCount)

	def RefreshUI(self):
		# ust panel: sure + bilet + bedel
		self.__RefreshTimeText()
		self.ticketText.SetText(_F("LUCKYDRAW_TICKETS", (str(self.myJoinCount), str(self.maxTicketCount))))
		self.__RefreshButtons()

		# gereksinim slotlari
		for i in xrange(LD_MAX_REQ_ITEMS):
			(vnum, count) = self.requirements[i]
			self.reqSlots.ClearSlot(i)
			if vnum and count:
				self.reqSlots.SetItemSlot(i, vnum, count)
		if self.neededYang:
			self.yangValue.SetText(constInfo.intWithCommas(self.neededYang))
		else:
			self.yangValue.SetText("-")

		# kazananlar + odul slotlari
		for w in xrange(LD_MAX_WINNERS):
			name = self.winnerNames[w]
			if name:
				if self.winnerTickets[w] > 0:
					self.winnerNameTexts[w].SetText(_F("LUCKYDRAW_WINNER_TICKETS", (name, str(self.winnerTickets[w]))))
				else:
					self.winnerNameTexts[w].SetText(name)
			else:
				self.winnerNameTexts[w].SetText("-")

			for k in xrange(LD_MAX_REWARDS):
				slotIdx = w * LD_MAX_REWARDS + k
				self.rewardSlots.ClearSlot(slotIdx)
				if k < len(self.rewards[w]):
					self.rewardSlots.SetItemSlot(slotIdx, self.rewards[w][k], 1)

		# katilimcilar
		self.joinerTitle.SetText(_F("LUCKYDRAW_JOINERS_TITLE", (str(self.joinCount), str(self.maxJoinCount))))
		for j in xrange(LD_MAX_JOINER_LIST):
			(name, count) = self.joiners[j]
			if name:
				self.joinerNameTexts[j].SetText(name)
				self.joinerCountTexts[j].SetText(_F("LUCKYDRAW_JOINER_TICKETS", (str(count),)))
			else:
				self.joinerNameTexts[j].SetText("")
				self.joinerCountTexts[j].SetText("")

		self.Open()

	# ---- tooltip ----

	def OnOverInReqSlot(self, slotIndex):
		if not self.tooltipItem:
			return
		if slotIndex < 0 or slotIndex >= LD_MAX_REQ_ITEMS:
			return
		vnum = self.requirements[slotIndex][0]
		if vnum:
			self.tooltipItem.SetItemToolTip(vnum)

	def OnOverInRewardSlot(self, slotIndex):
		if not self.tooltipItem:
			return
		w = slotIndex // LD_MAX_REWARDS
		k = slotIndex % LD_MAX_REWARDS
		if w < 0 or w >= LD_MAX_WINNERS:
			return
		if k < len(self.rewards[w]):
			self.tooltipItem.SetItemToolTip(self.rewards[w][k])

	def OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	# ---- yardimcilar ----

	def __RefreshButtons(self):
		# etkinlik ACIKKEN Bilet Al (ticket_buy) gorunur; KAPALIYKEN yerinde Odul Al durur
		if self.isActive:
			if self.joinButton:
				self.joinButton.Show()
			if self.rewardButton:
				self.rewardButton.Hide()
		else:
			if self.joinButton:
				self.joinButton.Hide()
			if self.rewardButton:
				self.rewardButton.Show()

	def __RefreshTimeText(self):
		if not self.isActive:
			self.timeText.SetText(_L("LUCKYDRAW_CLOSED"))
			return
		remaining = int(self.endTimeStamp - app.GetTime())
		if remaining < 0:
			remaining = 0
		self.lastShownSecond = remaining
		self.timeText.SetText(_F("LUCKYDRAW_TIME", (remaining // 3600, (remaining % 3600) // 60, remaining % 60)))

	# ---- buton olaylari ----

	def OnJoin(self):
		net.SendChatPacket("/lucky_draw 2")
		chat.AppendChat(chat.CHAT_TYPE_INFO, _L("LUCKYDRAW_JOIN_SENT"))

	def OnReward(self):
		net.SendChatPacket("/lucky_draw 3")
		chat.AppendChat(chat.CHAT_TYPE_INFO, _L("LUCKYDRAW_REWARD_SENT"))

	def OnRefresh(self):
		net.SendChatPacket("/lucky_draw 1")

	# ---- yasam dongusu ----

	def Open(self):
		if not self.IsShow():
			self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		# yalnizca geri sayim; saniye degismedikce dokunma
		if not self.isActive:
			return
		if not self.timeText:
			return
		remaining = int(self.endTimeStamp - app.GetTime())
		if remaining < 0:
			remaining = 0
		if remaining == self.lastShownSecond:
			return
		self.lastShownSecond = remaining
		self.timeText.SetText(_F("LUCKYDRAW_TIME", (remaining // 3600, (remaining % 3600) // 60, remaining % 60)))
		if remaining == 0:
			self.isActive = False
			self.timeText.SetText(_L("LUCKYDRAW_CLOSED"))
			self.__RefreshButtons()

	@ui.WindowDestroy
	def Destroy(self):
		if self.joinButton:
			self.joinButton.SetEvent(0)
		if self.rewardButton:
			self.rewardButton.SetEvent(0)
		if self.refreshButton:
			self.refreshButton.SetEvent(0)
		self.ClearDictionary()
		self.__Initialize()
