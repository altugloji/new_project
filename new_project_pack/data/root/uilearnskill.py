import ui, dbg, constInfo, player, app, net, event, chat

class SkillBoard(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.Initialize()
		#self.BuildWindow()

	def __del__(self):
		ui.Window.__del__(self)

	def Initialize(self):
		self.Board = None
		self.Islem = None
		self.a = None
		self.x = None
		self.b = None
		self.f = None
		self.k = None

	@ui.WindowDestroy
	def Destroy(self):
		constInfo.skillBoard = 0
		self.Initialize()

	def BuildWindow(self,Job):
		self.Board = ui.Board()
		self.Board.SetSize(290, 140)
		self.Board.SetCenterPosition()
		self.Board.AddFlag('movable')
		self.Board.AddFlag('float')
		self.OpenWindow()
		self.Islem = Wrapper()
		constInfo.skillBoard = 1
		# beceriArrayName = ["Unknown", "Unknown"]
		# dJob = int(Job)
		# if dJob == 0: beceriArrayName = ["Body Warrior","Mental Warrior"]
		# if dJob == 1: beceriArrayName = ["Blade-Fight","Archery"]
		# if dJob == 2: beceriArrayName = ["Weaponary","Black Magic"]
		# if dJob == 3: beceriArrayName = ["Dragon Force","Healing Force"]
		# if dJob == 4: beceriArrayName = ["Instinct","Unknown"]

		# self.a=self.Islem.TextLine(self.Board,"You can select your skill group from here.",92, 25)
		# self.x=self.Islem.TextLine(self.Board,"(This notification appears every time you level up.)",65, 40)
		# self.b = self.Islem.Button(self.Board, beceriArrayName[0], '' ,20, 65, self.BeceriAl_1, 'd:/ymir work/ui/feed_button/feed_button_default.sub', 'd:/ymir work/ui/feed_button/feed_button_over.sub', 'd:/ymir work/ui/feed_button/feed_button_down.sub')
		# self.f = self.Islem.Button(self.Board, beceriArrayName[1], '', 150, 65, self.BeceriAl_2, 'd:/ymir work/ui/feed_button/feed_button_default.sub', 'd:/ymir work/ui/feed_button/feed_button_over.sub', 'd:/ymir work/ui/feed_button/feed_button_down.sub')
		# self.k = self.Islem.Button(self.Board, 'Later', '', 85, 100, self.IslemYapma, 'd:/ymir work/ui/feed_button/feed_button_default.sub', 'd:/ymir work/ui/feed_button/feed_button_over.sub', 'd:/ymir work/ui/feed_button/feed_button_down.sub')

		beceriArrayName = ["Bilinmiyor", "Bilinmiyor"]
		dJob = int(Job)
		if dJob == 0: beceriArrayName = ["Bedensel","Zihinsel"]
		if dJob == 1: beceriArrayName = ["Yakin Dovus","Uzak Dovus"]
		if dJob == 2: beceriArrayName = ["Buyulu Silah","Kara Buyu"]
		if dJob == 3: beceriArrayName = ["Ejderha Gucu","Iyilestirme"]

		self.a=self.Islem.TextLine(self.Board,"Becerini buradan secebilirsin.",92, 25)
		self.x=self.Islem.TextLine(self.Board,"(Bu bildiri her seviye atlayisinda cikar.)",65, 40)
		self.b = self.Islem.Button(self.Board, beceriArrayName[0], '' ,20, 65, self.BeceriAl_1, 'd:/ymir work/ui/pet/feed_button/feed_button_default.sub', 'd:/ymir work/ui/pet/feed_button/feed_button_over.sub', 'd:/ymir work/ui/pet/feed_button/feed_button_down.sub')
		self.f = self.Islem.Button(self.Board, beceriArrayName[1], '', 150, 65, self.BeceriAl_2, 'd:/ymir work/ui/pet/feed_button/feed_button_default.sub', 'd:/ymir work/ui/pet/feed_button/feed_button_over.sub', 'd:/ymir work/ui/pet/feed_button/feed_button_down.sub')
		self.k = self.Islem.Button(self.Board, 'Daha Sonra', '', 85, 100, self.IslemYapma, 'd:/ymir work/ui/pet/feed_button/feed_button_default.sub', 'd:/ymir work/ui/pet/feed_button/feed_button_over.sub', 'd:/ymir work/ui/pet/feed_button/feed_button_down.sub')


	def BeceriAl_1(self):
		net.SendChatPacket("/skill_select 1")
		self.Close()
	def BeceriAl_2(self):
		net.SendChatPacket("/skill_select 2")
		self.Close()
	def IslemYapma(self):
		self.Close()
	def OpenWindow(self):
		if self.Board and not self.Board.IsShow():
			self.Board.Show()
	def Close(self):
		constInfo.skillBoard=0
		if self.Board:
			self.Board.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True

class Wrapper:
	def Button(self, parent, buttonName, tooltipText, x, y, func, UpVisual, OverVisual, DownVisual):
		button = ui.Button()
		if parent != None: button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetUpVisual(UpVisual)
		button.SetOverVisual(OverVisual)
		button.SetDownVisual(DownVisual)
		button.SetText(buttonName)
		button.SetToolTipText(tooltipText)
		button.Show()
		button.SAFE_SetEvent(func)
		return button

	def ToggleButton(self, parent, buttonName, tooltipText, x, y, funcUp, funcDown, UpVisual, OverVisual, DownVisual):
		button = ui.ToggleButton()
		if parent != None: button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetUpVisual(UpVisual)
		button.SetOverVisual(OverVisual)
		button.SetDownVisual(DownVisual)
		button.SetText(buttonName)
		button.SetToolTipText(tooltipText)
		button.Show()
		button.SetToggleUpEvent(funcUp)
		button.SetToggleDownEvent(funcDown)
		return button

	def EditLine(self, parent, editlineText, x, y, width, heigh, max):
		SlotBar = ui.SlotBar()
		if parent != None: SlotBar.SetParent(parent)
		SlotBar.SetSize(width, heigh)
		SlotBar.SetPosition(x, y)
		SlotBar.Show()
		Value = ui.EditLine()
		Value.SetParent(SlotBar)
		Value.SetSize(width, heigh)
		Value.SetPosition(1, 1)
		Value.SetMax(max)
		Value.SetLimitWidth(width)
		Value.SetMultiLine()
		Value.SetText(editlineText)
		Value.Show()
		return SlotBar, Value

	def TextLine(self, parent, text, x, y):
		tmpText = ui.TextLine()

		if parent:
			tmpText.SetParent(parent)

		tmpText.SetPosition(x, y)
		tmpText.SetText(text)

		tmpText.Show()
		return tmpText

	def RGB(self, r, g, b):
		return (r*255, g*255, b*255)

	def SliderBar(self, parent, sliderPos, func, x, y):
		Slider = ui.SliderBar()
		if parent != None:Slider.SetParent(parent)
		Slider.SetPosition(x, y)
		Slider.SetSliderPos(sliderPos / 100)
		Slider.Show()
		Slider.SetEvent(func)
		return Slider

	def ExpandedImage(self, parent, x, y, img):
		image = ui.ExpandedImageBox()
		if parent != None:image.SetParent(parent)
		image.SetPosition(x, y)
		image.LoadImage(img)
		image.Show()
		return image

	def ComboBox(self, parent, text, x, y, width):
		combo = ui.ComboBox()
		if parent != None:combo.SetParent(parent)
		combo.SetPosition(x, y)
		combo.SetSize(width, 15)
		combo.SetCurrentItem(text)
		combo.Show()
		return combo

	def ThinBoard(self, parent, moveable, x, y, width, heigh, center):
		thin = ui.ThinBoard()
		if parent != None:
			thin.SetParent(parent)
		if moveable == TRUE:
			thin.AddFlag('movable')
			thin.AddFlag('float')
		thin.SetSize(width, heigh)
		thin.SetPosition(x, y)
		if center == TRUE:
			thin.SetCenterPosition()
		thin.Show()
		return thin

	def Gauge(self, parent, width, color, x, y):
		gauge = ui.Gauge()
		if parent != None:
			gauge.SetParent(parent)
		gauge.SetPosition(x, y)
		gauge.MakeGauge(width, color)
		gauge.Show()
		return gauge

	def ListBoxEx(self, parent, x, y, width, heigh):
		bar = ui.Bar()
		if parent != None:
			bar.SetParent(parent)
		bar.SetPosition(x, y)
		bar.SetSize(width, heigh)
		bar.SetColor(0x77000000)
		bar.Show()
		ListBox=ui.ListBoxEx()
		ListBox.SetParent(bar)
		ListBox.SetPosition(0, 0)
		ListBox.SetSize(width, heigh)
		ListBox.Show()
		scroll = ui.ScrollBar()
		scroll.SetParent(ListBox)
		scroll.SetPosition(width-15, 0)
		scroll.SetScrollBarSize(heigh)
		scroll.Show()
		ListBox.SetScrollBar(scroll)
		return bar, ListBox

