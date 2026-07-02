import ui
import app
import net

TEXT_DOGRULAYIN = "Bot kontrol dogrulanamadi"
TEXT_DOGRULAYIN_2 = "Asagidaki dogru kodu secin:"

class BotControlBoard(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.butonList=[]
		self.snSayac=0
		self.kalanSureSayac=0
		self.kalanSure=0
	def __del__(self):
		ui.Window.__del__(self)
		self.butonList=[]
		self.snSayac=0
		self.kalanSureSayac=0
		self.kalanSure=0
	def Destroy(self):
		self.ClearDictionary()
		self.butonList=[]
		self.snSayac=0
		self.kalanSureSayac=0
		self.kalanSure=0
	def ShowBotControl(self,gelenKod=0,kalanSure=0):
		ui.ScriptWindow.Show(self)
		self.Board = ui.Board()
		self.Board.SetSize(185, 250)
		self.Board.SetCenterPosition()
		self.Board.AddFlag('float')
		self.OpenWindow()
		dogruKod=app.GetRandom(0,3)
		self.kalanSureSayac=kalanSure

		for i in xrange(4):
			ekleKod = app.GetRandom(100000,999999)
			if i == dogruKod: ekleKod=gelenKod
			dogrulaBtn = ui.Button()
			dogrulaBtn.SetParent(self.Board)
			dogrulaBtn.SetUpVisual("d:/ymir work/ui/pet/feed_button/feed_button_default.sub")
			dogrulaBtn.SetOverVisual("d:/ymir work/ui/pet/feed_button/feed_button_over.sub")
			dogrulaBtn.SetDownVisual("d:/ymir work/ui/pet/feed_button/feed_button_down.sub")
			dogrulaBtn.SetText(str(ekleKod))
			dogrulaBtn.SetPosition(30, 90+(i*30))
			dogrulaBtn.SetEvent(ui.__mem_func__(self.KodYolla), ekleKod)
			dogrulaBtn.Show()
			dogrulaBtn.SetTop()
			self.butonList.append(dogrulaBtn)

		self.ustBilgi = ui.TextLine()
		self.ustBilgi.SetParent(self.Board)
		self.ustBilgi.SetFeather()
		self.ustBilgi.SetOutline()
		self.ustBilgi.SetPosition(16, 20)
		self.ustBilgi.SetText(TEXT_DOGRULAYIN)
		self.ustBilgi.Show()

		self.ustBilgi_2 = ui.TextLine()
		self.ustBilgi_2.SetParent(self.Board)
		self.ustBilgi_2.SetFeather()
		self.ustBilgi_2.SetOutline()
		self.ustBilgi_2.SetPosition(26, 40)
		self.ustBilgi_2.SetText(TEXT_DOGRULAYIN_2)
		self.ustBilgi_2.Show()

		self.dogruKod = ui.TextLine()
		self.dogruKod.SetFontName("Arial:17")
		self.dogruKod.SetParent(self.Board)
		self.dogruKod.SetFeather()
		self.dogruKod.SetOutline()
		self.dogruKod.SetPosition(70,60)
		self.dogruKod.SetText("|cff40d74e|H|h"+str(gelenKod)+"|r")
		self.dogruKod.Show()

		self.kalanSure = ui.TextLine()
		self.kalanSure.SetFontName("Arial:17")
		self.kalanSure.SetParent(self.Board)
		self.kalanSure.SetFeather()
		self.kalanSure.SetOutline()
		self.kalanSure.SetPosition(78,215)
		self.kalanSure.SetText("|cfff1ea35|H|h"+str(kalanSure)+"sn|r")
		self.kalanSure.Show()

	def SureGuncelle(self,kSure):
		self.kalanSure.SetText("|cfff1ea35|H|h"+str(kSure)+"sn|r")
	def KodYolla(self,gelenKod):
		net.SendBotControlPacket(str(gelenKod))
		self.Close()
	def OnUpdate(self):
		if int(self.snSayac) <= int(app.GetTime()):
			self.snSayac=int(app.GetTime())+1
			self.kalanSureSayac-=1
			self.SureGuncelle(self.kalanSureSayac)
		if self.kalanSureSayac <= 0: app.Exit()
	def OpenWindow(self):
		if self.Board.IsShow(): pass
		else: self.Board.Show()
	def Close(self):
		self.Board.Hide()
		self.Hide()
		ui.ScriptWindow.Hide(self)
