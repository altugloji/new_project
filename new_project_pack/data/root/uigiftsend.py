# Hediye Gonderme Sistemi - istemci penceresi (ENABLE_GIFT_SEND_SYSTEM).
# Oyuncudan oyuncuya kozmetik hediye gonderimi. Aliciya item verilmez; hediyenin
# EP fiyati kadar deger alicinin "hediye puani" olarak birikir.
#
# NOT: Mevcut item-mall "GiftDialog" (uigift.py) sisteminden TAMAMEN ayridir.
# Cakismasin diye ayri isimler kullanilir: GiftSendDialog, /gift_send*, GIFT_SEND_*.
import ui
import net
import app
import chat
import snd
import dbg
import localeInfo

GIFT_MAX_COUNT = 99

# --- Hediye kart yerlesimi ---
# Kartlar item ikonu DEGIL, senin kendi gorsellerin: d:/ymir work/gift_character/<N>.png
# gift_item.icon_image kolonu = gorsel numarasi (1..14). Kart boyutuna gore adimlari ayarla.
GIFT_CARD_COL = 5						# sutun sayisi
GIFT_CARD_ROW = 3						# satir sayisi
GIFT_CARD_MAX = GIFT_CARD_COL * GIFT_CARD_ROW	# 15 kart, sayfalama YOK
# Kart gorselleri 113x153 (orijinaller 1048x1501 -> DX9 doku limiti asiyordu, bos geliyordu).
# Kart boyutunu degistirirsen bu adimlari da guncelle.
GIFT_CARD_START_X = 30					# ilk kartin sol-ust x'i (board'a gore, gift_slot_base icinde)
GIFT_CARD_START_Y = 105					# ilk kartin sol-ust y'si
GIFT_CARD_STEP_X = 119					# yatay adim = kart genisligi(113) + bosluk(6)
GIFT_CARD_STEP_Y = 161					# dikey adim = kart yuksekligi(153) + bosluk(8)
GIFT_CARD_IMAGE = "d:/ymir work/gift_character/%d.png"	# %d = gift_item.icon_image

# --- flag bitleri (server ile ayni) ---
GIFT_FLAG_PACKAGE = 1
GIFT_FLAG_ANONYMOUS = 2

# --- gonderim sonuc kodlari (server EGiftSendResult) ---
GIFT_SEND_OK = 0
GIFT_SEND_NOT_ENOUGH_EP = 1
GIFT_SEND_TARGET_NOT_FOUND = 2
GIFT_SEND_SELF = 3
GIFT_SEND_COOLDOWN = 4
GIFT_SEND_INVALID_GIFT = 5
GIFT_SEND_INVALID_COUNT = 6
GIFT_SEND_BLOCKED = 7
GIFT_SEND_DB_ERROR = 8

# --- isim dogrulama sonuc kodlari (server EGiftFindResult) ---
GIFT_FIND_NOT_FOUND = 0
GIFT_FIND_OK = 1
GIFT_FIND_SELF = 2

# Tum metinler burada. Once localeInfo.GIFT_SEND_<KEY> denenir (ceviri override),
# yoksa buradaki varsayilan (ASCII-Turkce) kullanilir. Boylece locale dosyasi
# duzenlemeden calisir, istenirse locale'e tasinabilir.
_DEFAULT = {
	"TITLE"				: "Hediye Gonder",
	"PLAYER_NAME"		: "Oyuncu Adi",
	"NAME_PLACEHOLDER"	: "Oyuncu adini giriniz.",
	"FIND"				: "Bul",
	"HELP"				: "?",
	"CURRENT_EP"		: "Mevcut EP: %s",
	"GIFTS"				: "Hediyeler",
	"SELECTED"			: "Secili Hediye",
	"COUNT"				: "Adet",
	"PRICE"				: "Ucret",
	"UNIT_PRICE"		: "%s EP",
	"MESSAGE_TITLE"		: "Hediye Mesaji",
	"MESSAGE_OPTIONAL"	: "(Istege bagli)",
	"MESSAGE_PLACEHOLDER": "Mesajini yaz...",
	"PACKAGE"			: "Hediye Paketi",
	"ANONYMOUS"			: "Anonim Gonder",
	"TOTAL"				: "Toplam Ucret",
	"SEND"				: "Gonder",
	"CANCEL"			: "Iptal",
	"RANK"				: "Siralama",
	"MY_POINT"			: "Hediye Puani: %s",
	"CONFIRM"			: "%s oyuncusuna '%s' hediyesini %s EP karsiliginda gondermek istiyor musun?",
	"NEED_NAME"			: "Once oyuncu adi gir.",
	"NEED_GIFT"			: "Once bir hediye sec.",
	"NEED_EP"			: "Yeterli EP'n yok.",
	"HELP_TEXT"			: "Bir oyuncuya kozmetik hediye gonder. Hediyenin EP degeri kadar 'hediye puani' aliciya eklenir; esya verilmez.",
	# gonderim sonuc mesajlari
	"RES_OK"			: "Hediye gonderildi!",
	"RES_NOT_ENOUGH_EP"	: "Yeterli EP'n yok.",
	"RES_NOT_FOUND"		: "Oyuncu bulunamadi.",
	"RES_SELF"			: "Kendine veya kendi hesabina hediye gonderemezsin.",
	"RES_COOLDOWN"		: "Cok hizli gonderiyorsun, biraz bekle.",
	"RES_INVALID_GIFT"	: "Gecersiz hediye.",
	"RES_INVALID_COUNT"	: "Gecersiz adet.",
	"RES_BLOCKED"		: "Su an hediye gonderemezsin (ticaret/pazar/olu).",
	"RES_DB"			: "Islem basarisiz, tekrar dene.",
	# isim dogrulama mesajlari
	"FIND_OK"			: "Oyuncu bulundu: %s",
	"FIND_NOT_FOUND"	: "Oyuncu bulunamadi.",
	"FIND_SELF"			: "Kendine hediye gonderemezsin.",
	# bildirim mesajlari
	"NOTIFY_RECV"		: "%s sana '%s' gonderdi! (+%s Puan)",
	"NOTIFY_ANON"		: "Gizli bir hayran sana '%s' gonderdi! (+%s Puan)",
	"NOTIFY_MSG"		: "Mesaj: %s",
}


def GL(key):
	# localeInfo.GIFT_SEND_<key> varsa onu, yoksa varsayilani dondur.
	try:
		val = getattr(localeInfo, "GIFT_SEND_" + key)
		if val and val != ("GIFT_SEND_" + key):
			return val
	except:
		pass
	return _DEFAULT.get(key, key)


def FormatEP(n):
	# Noktali binlik ayrac: 1000 -> "1.000"
	try:
		n = int(n)
	except:
		n = 0
	neg = n < 0
	s = str(abs(n))
	out = ""
	while len(s) > 3:
		out = "." + s[-3:] + out
		s = s[:-3]
	out = s + out
	if neg:
		out = "-" + out
	return out


class GiftSendDialog(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.isLoaded = False
		# widget refleri
		self.board = None
		self.nameEdit = None
		self.nameHint = None
		self.findButton = None
		self.helpButton = None
		self.epText = None
		self.giftCards = []
		self.selectFrame = None
		self.cardPos = {}
		self.previewImage = None
		self.giftNameText = None
		self.countValue = None
		self.countUpButton = None
		self.countDownButton = None
		self.priceText = None
		self.descText = None
		self.messageEdit = None
		self.messageHint = None
		self.packageButton = None
		self.anonButton = None
		self.totalText = None
		self.sendButton = None
		self.cancelButton = None
		self.rankButton = None
		self.rankOpenEvent = None
		self.questionDialog = None
		# veri
		self.giftList = []			# [{index, icon, price, page, slot, name, desc}, ...]
		self.slotToGift = {}		# kart slotu -> gift
		self.selectedGift = None
		self.count = 1
		self.ep = 0
		self.myPoint = 0
		self.packageFlag = False
		self.anonFlag = False

	@ui.WindowDestroy
	def Destroy(self):
		if self.questionDialog:
			self.questionDialog.Close()
		self.questionDialog = None
		self.__Initialize()
		self.ClearDictionary()

	def __LoadWindow(self):
		if self.isLoaded:
			return
		self.isLoaded = True

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/giftsenddialogwindow.py")
		except:
			dbg.TraceError("GiftSendDialog.LoadScript failed")
			self.isLoaded = False
			return

		GetObject = self.GetChild
		try:
			self.board = GetObject("board")
			self.nameHint = GetObject("name_hint")
			self.findButton = GetObject("find_button")
			self.helpButton = GetObject("help_button")
			self.epText = GetObject("ep_text")
			self.previewImage = GetObject("preview_image")
			self.giftNameText = GetObject("gift_name_text")
			self.countValue = GetObject("count_value")
			self.countUpButton = GetObject("count_up_button")
			self.countDownButton = GetObject("count_down_button")
			self.priceText = GetObject("price_text")
			self.descText = GetObject("desc_text")
			self.messageHint = GetObject("message_hint")
			self.packageButton = GetObject("package_check_button")
			self.anonButton = GetObject("anon_check_button")
			self.totalText = GetObject("total_text")
			self.sendButton = GetObject("send_button")
			self.cancelButton = GetObject("cancel_button")
			self.rankButton = GetObject("rank_button")
			nameSlot = GetObject("player_name_slot")
			messageSlot = GetObject("message_slot")
		except:
			dbg.TraceError("GiftSendDialog.BindObject failed")
			self.isLoaded = False
			return

		# statik etiketleri koddan ayarla (locale override + fallback)
		self.board.SetTitleName(GL("TITLE"))
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		GetObject("player_name_label").SetText(GL("PLAYER_NAME"))
		self.findButton.SetText(GL("FIND"))
		GetObject("gift_panel_title").SetText(GL("GIFTS"))
		GetObject("selected_title").SetText(GL("SELECTED"))
		GetObject("count_label").SetText(GL("COUNT"))
		GetObject("price_label").SetText(GL("PRICE"))
		GetObject("message_title").SetText(GL("MESSAGE_TITLE"))
		GetObject("message_optional").SetText(GL("MESSAGE_OPTIONAL"))
		GetObject("package_check_label").SetText(GL("PACKAGE"))
		GetObject("anon_check_label").SetText(GL("ANONYMOUS"))
		GetObject("total_label").SetText(GL("TOTAL"))
		self.sendButton.SetText(GL("SEND"))
		self.cancelButton.SetText(GL("CANCEL"))
		self.rankButton.SetText(GL("RANK"))
		self.nameHint.SetText(GL("NAME_PLACEHOLDER"))
		self.messageHint.SetText(GL("MESSAGE_PLACEHOLDER"))

		# oyuncu adi EditLine (tek satir)
		self.nameEdit = ui.EditLine()
		self.nameEdit.SetParent(nameSlot)
		self.nameEdit.SetPosition(5, 3)
		self.nameEdit.SetSize(205, 14)
		self.nameEdit.SetMax(24)
		self.nameEdit.SetReturnEvent(ui.__mem_func__(self.OnClickFind))
		self.nameEdit.Show()

		# mesaj EditLine (cok satir, max 120)
		self.messageEdit = ui.EditLine()
		self.messageEdit.SetParent(messageSlot)
		self.messageEdit.SetPosition(6, 5)
		self.messageEdit.SetSize(395, 85)
		self.messageEdit.SetMax(120)
		self.messageEdit.SetMultiLine()
		self.messageEdit.Show()

		# hediye kartlari: her kart = tiklanabilir kendi gorselin (gift_character/N.png)
		self.giftCards = []
		for i in xrange(GIFT_CARD_MAX):
			card = ui.Button()
			card.SetParent(self.board)
			card.SetEvent(ui.__mem_func__(self.OnSelectGiftCard), i)
			card.Hide()
			self.giftCards.append(card)

		# secili kart icin altin cerceve (kartlarin ustunde cizilir)
		self.selectFrame = ui.Box()
		self.selectFrame.SetParent(self.board)
		self.selectFrame.SetColor(0xFFFFD700)		# altin (ARGB)
		self.selectFrame.Hide()

		# buton olaylari
		self.findButton.SetEvent(ui.__mem_func__(self.OnClickFind))
		self.helpButton.SetEvent(ui.__mem_func__(self.OnClickHelp))
		self.countUpButton.SetEvent(ui.__mem_func__(self.OnCountUp))
		self.countDownButton.SetEvent(ui.__mem_func__(self.OnCountDown))
		self.packageButton.SetEvent(ui.__mem_func__(self.OnTogglePackage))
		self.anonButton.SetEvent(ui.__mem_func__(self.OnToggleAnon))
		self.sendButton.SetEvent(ui.__mem_func__(self.OnClickSend))
		self.cancelButton.SetEvent(ui.__mem_func__(self.Close))
		self.rankButton.SetEvent(ui.__mem_func__(self.OnClickRank))

		self.__RefreshSelectedPanel()
		self.__RefreshTotal()

	def SetRankOpenEvent(self, event):
		# interfacemodule tarafindan baglanir (siralama penceresini acar)
		self.rankOpenEvent = event

	def OnClickRank(self):
		if self.rankOpenEvent:
			self.rankOpenEvent()

	# ------------------------------------------------------------------
	# Ac / Kapat
	# ------------------------------------------------------------------
	def Open(self, targetName=""):
		self.__LoadWindow()
		if not self.isLoaded:
			return

		self.count = 1
		self.packageFlag = False
		self.anonFlag = False
		self.__RefreshCheckVisual()
		if self.nameEdit:
			self.nameEdit.SetText(targetName or "")
		if self.messageEdit:
			self.messageEdit.SetText("")
		self.__SetCount(1)

		# sunucudan katalog + EP + puani iste
		if app.ENABLE_GIFT_SEND_SYSTEM:
			net.SendGiftListPacket()

		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		if self.nameEdit:
			self.nameEdit.KillFocus()
		if self.messageEdit:
			self.messageEdit.KillFocus()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnUpdate(self):
		# placeholder (hint) gorunurlugu + EP tazeligi
		if self.nameHint and self.nameEdit:
			if self.nameEdit.GetText():
				self.nameHint.Hide()
			else:
				self.nameHint.Show()
		if self.messageHint and self.messageEdit:
			if self.messageEdit.GetText():
				self.messageHint.Hide()
			else:
				self.messageHint.Show()

	# ------------------------------------------------------------------
	# Katalog / sayfalama
	# ------------------------------------------------------------------
	def SetGiftList(self, giftList):
		# giftList: [(index, icon, price, page, slot, name, desc), ...]
		self.giftList = []
		for entry in giftList:
			try:
				self.giftList.append({
					"index": int(entry[0]),
					"icon" : int(entry[1]),
					"price": int(entry[2]),
					"page" : int(entry[3]),
					"slot" : int(entry[4]),
					"name" : entry[5],
					"desc" : entry[6],
				})
			except Exception, e:
				dbg.TraceError("GiftSendDialog.SetGiftList entry error: %s" % e)

		total = len(self.giftList)
		if total > GIFT_CARD_MAX:
			dbg.TraceError("GiftSendDialog: %d hediye var ama panel %d kart gosterir, fazlasi gizli" % (total, GIFT_CARD_MAX))
		self.selectedGift = None
		self.__RefreshCards()
		self.__RefreshSelectedPanel()
		self.__RefreshTotal()

	def __RefreshCards(self):
		if not self.giftCards:
			return
		self.slotToGift = {}
		self.cardPos = {}
		for local in xrange(GIFT_CARD_MAX):
			card = self.giftCards[local]
			gi = local
			if gi < len(self.giftList):
				gift = self.giftList[gi]
				self.slotToGift[local] = gift
				path = GIFT_CARD_IMAGE % gift["icon"]
				card.SetUpVisual(path)
				card.SetOverVisual(path)
				card.SetDownVisual(path)
				col = local % GIFT_CARD_COL
				row = local // GIFT_CARD_COL
				x = GIFT_CARD_START_X + col * GIFT_CARD_STEP_X
				y = GIFT_CARD_START_Y + row * GIFT_CARD_STEP_Y
				card.SetPosition(x, y)
				self.cardPos[local] = (x, y)
				card.Show()
			else:
				card.Hide()

		self.__RefreshSelectionOverlay()

	def __RefreshSelectionOverlay(self):
		if not self.selectFrame:
			return
		self.selectFrame.Hide()
		if not self.selectedGift:
			return
		for local, gift in self.slotToGift.items():
			if gift["index"] == self.selectedGift["index"]:
				card = self.giftCards[local]
				x, y = self.cardPos.get(local, (0, 0))
				w = card.GetWidth()
				h = card.GetHeight()
				if w <= 0:
					w = GIFT_CARD_STEP_X - 4
				if h <= 0:
					h = GIFT_CARD_STEP_Y - 4
				self.selectFrame.SetPosition(x - 2, y - 2)
				self.selectFrame.SetSize(w + 4, h + 4)
				self.selectFrame.Show()
				break

	# ------------------------------------------------------------------
	# Secim
	# ------------------------------------------------------------------
	def OnSelectGiftCard(self, local):
		gift = self.slotToGift.get(local)
		if not gift:
			return
		self.selectedGift = gift
		self.count = 1
		self.__SetCount(1)
		self.__RefreshSelectionOverlay()
		self.__RefreshSelectedPanel()
		self.__RefreshTotal()
		snd.PlaySound("sound/ui/click.wav")

	def __RefreshSelectedPanel(self):
		gift = self.selectedGift
		if not gift:
			if self.giftNameText: self.giftNameText.SetText("")
			if self.descText: self.descText.SetText("")
			if self.priceText: self.priceText.SetText("")
			if self.previewImage:
				self.previewImage.Hide()
			return

		if self.giftNameText:
			self.giftNameText.SetText(gift["name"])
		if self.descText:
			self.descText.SetText(gift["desc"])
		if self.previewImage:
			# onizleme = secili hediyenin buyuk kart gorseli
			try:
				self.previewImage.LoadImage(GIFT_CARD_IMAGE % gift["icon"])
				self.previewImage.Show()
			except:
				self.previewImage.Hide()
		self.__RefreshPrice()

	def __RefreshPrice(self):
		if not self.priceText:
			return
		if self.selectedGift:
			unit = self.selectedGift["price"]
			self.priceText.SetText(GL("UNIT_PRICE") % FormatEP(unit * self.count))
		else:
			self.priceText.SetText("")

	# ------------------------------------------------------------------
	# Adet
	# ------------------------------------------------------------------
	def __SetCount(self, value):
		if value < 1:
			value = 1
		if value > GIFT_MAX_COUNT:
			value = GIFT_MAX_COUNT
		self.count = value
		if self.countValue:
			self.countValue.SetText(str(self.count))
		self.__RefreshPrice()
		self.__RefreshTotal()

	def OnCountUp(self):
		self.__SetCount(self.count + 1)

	def OnCountDown(self):
		self.__SetCount(self.count - 1)

	def __RefreshTotal(self):
		if not self.totalText:
			return
		if self.selectedGift:
			total = self.selectedGift["price"] * self.count
			self.totalText.SetText(GL("UNIT_PRICE") % FormatEP(total))
		else:
			self.totalText.SetText(GL("UNIT_PRICE") % "0")

	# ------------------------------------------------------------------
	# Checkbox'lar
	# ------------------------------------------------------------------
	def OnTogglePackage(self):
		self.packageFlag = not self.packageFlag
		self.__RefreshCheckVisual()

	def OnToggleAnon(self):
		self.anonFlag = not self.anonFlag
		self.__RefreshCheckVisual()

	def __RefreshCheckVisual(self):
		if self.packageButton:
			img = "d:/ymir work/ui/game/refine/checked.tga" if self.packageFlag else "d:/ymir work/ui/game/refine/checkbox.tga"
			self.packageButton.SetUpVisual(img)
			self.packageButton.SetOverVisual(img)
		if self.anonButton:
			img = "d:/ymir work/ui/game/refine/checked.tga" if self.anonFlag else "d:/ymir work/ui/game/refine/checkbox.tga"
			self.anonButton.SetUpVisual(img)
			self.anonButton.SetOverVisual(img)

	# ------------------------------------------------------------------
	# EP / puan gosterimi (sunucudan)
	# ------------------------------------------------------------------
	def SetEP(self, ep):
		self.ep = int(ep)
		if self.epText:
			self.epText.SetText(GL("CURRENT_EP") % FormatEP(self.ep))

	def SetGiftPoint(self, point):
		self.myPoint = int(point)
		# istenirse baslikta/panelde gosterilebilir; simdilik sadece saklanir.

	# ------------------------------------------------------------------
	# Bul
	# ------------------------------------------------------------------
	def __GetName(self):
		if not self.nameEdit:
			return ""
		return self.nameEdit.GetText().strip()

	def OnClickFind(self):
		name = self.__GetName()
		if not name:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("NEED_NAME"))
			return
		if app.ENABLE_GIFT_SEND_SYSTEM:
			net.SendGiftFindPacket(name)

	def OnFindResult(self, result, name):
		if result == GIFT_FIND_OK:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("FIND_OK") % name)
		elif result == GIFT_FIND_SELF:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("FIND_SELF"))
		else:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("FIND_NOT_FOUND"))

	# ------------------------------------------------------------------
	# Gonder
	# ------------------------------------------------------------------
	def OnClickSend(self):
		name = self.__GetName()
		if not name:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("NEED_NAME"))
			return
		if not self.selectedGift:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("NEED_GIFT"))
			return

		total = self.selectedGift["price"] * self.count
		if total > self.ep:
			chat.AppendChat(chat.CHAT_TYPE_INFO, GL("NEED_EP"))
			return

		import uiCommon
		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(GL("CONFIRM") % (name, self.selectedGift["name"], FormatEP(total)))
		self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.__OnConfirmSend))
		self.questionDialog.SetCancelEvent(ui.__mem_func__(self.__OnCancelSend))
		self.questionDialog.Open()

	def __OnCancelSend(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		return True

	def __OnConfirmSend(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None

		if not self.selectedGift:
			return True

		name = self.__GetName()
		if not name:
			return True

		flags = 0
		if self.packageFlag:
			flags |= GIFT_FLAG_PACKAGE
		if self.anonFlag:
			flags |= GIFT_FLAG_ANONYMOUS

		message = ""
		if self.messageEdit:
			message = self.messageEdit.GetText()

		if app.ENABLE_GIFT_SEND_SYSTEM:
			net.SendGiftSendPacket(name, self.selectedGift["index"], self.count, flags, message)
		return True

	def OnSendResult(self, result, newEP, giftIndex, count):
		# guncel EP'yi tazele
		self.SetEP(newEP if result == GIFT_SEND_OK else self.ep)

		msgMap = {
			GIFT_SEND_OK			: "RES_OK",
			GIFT_SEND_NOT_ENOUGH_EP	: "RES_NOT_ENOUGH_EP",
			GIFT_SEND_TARGET_NOT_FOUND: "RES_NOT_FOUND",
			GIFT_SEND_SELF			: "RES_SELF",
			GIFT_SEND_COOLDOWN		: "RES_COOLDOWN",
			GIFT_SEND_INVALID_GIFT	: "RES_INVALID_GIFT",
			GIFT_SEND_INVALID_COUNT	: "RES_INVALID_COUNT",
			GIFT_SEND_BLOCKED		: "RES_BLOCKED",
			GIFT_SEND_DB_ERROR		: "RES_DB",
		}
		key = msgMap.get(result, "RES_DB")
		chat.AppendChat(chat.CHAT_TYPE_INFO, GL(key))

		if result == GIFT_SEND_OK:
			snd.PlaySound("sound/ui/money.wav")
			if self.messageEdit:
				self.messageEdit.SetText("")

	# ------------------------------------------------------------------
	# Yardim
	# ------------------------------------------------------------------
	def OnClickHelp(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, GL("HELP_TEXT"))
