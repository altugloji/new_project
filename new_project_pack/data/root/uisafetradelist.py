import ui
import net
import chat
import localeInfo
import exception

try:
	import safetrade
except ImportError:
	safetrade = None


class SafeTradeListWindow(ui.ScriptWindow):
	def __init__(self, parentInterface):
		ui.ScriptWindow.__init__(self)
		self.parentInterface = parentInterface
		self.outgoing = 0
		self.selectedTradeID = 0
		self.ownerDict = {}
		self.listBox = None
		self.viewButton = None
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/safetradelistwindow.py")
		except:
			exception.Abort("SafeTradeListWindow.__LoadWindow.LoadScriptFile")
			return

		try:
			self.GetChild("TitleName").SetText(localeInfo.SAFETRADE_LIST_TITLE)
			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.OnClose))
			self.viewButton = self.GetChild("ViewButton")
			self.viewButton.SetText(localeInfo.SAFETRADE_VIEW)
			self.viewButton.SetEvent(ui.__mem_func__(self.OnViewSelected))
		except:
			exception.Abort("SafeTradeListWindow.__LoadWindow.GetChild")
			return

		self.listBox = ui.ListBox()
		self.listBox.SetParent(self)
		self.listBox.SetPosition(20, 40)
		self.listBox.SetSize(220, 235)
		self.listBox.SetTextCenterAlign(False)
		self.listBox.SetEvent(ui.__mem_func__(self.OnSelectTrade))
		self.listBox.Show()

		self.Hide()

	@ui.WindowDestroy
	def Destroy(self):
		self.listBox = None
		self.viewButton = None
		self.parentInterface = None

	def Open(self, outgoing):
		self.outgoing = outgoing
		self.selectedTradeID = 0
		if not safetrade or not self.listBox:
			return
		count = safetrade.GetListCount()
		if count == 0:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SAFETRADE_EMPTY_LIST)
			self.Hide()
			return

		self.listBox.ClearItem()
		self.ownerDict = {}
		for i in xrange(count):
			tid = safetrade.GetListTradeID(i)
			sender = safetrade.GetListSenderName(i)
			n = safetrade.GetListItemCount(i)
			self.ownerDict[tid] = safetrade.GetListIsOwner(i)
			if self.outgoing:
				label = localeInfo.SAFETRADE_OUTGOING_FMT % (sender, n)
			else:
				label = localeInfo.SAFETRADE_INCOMING_FMT % (sender, n)
			self.listBox.InsertItem(tid, label)

		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	# ListBox seciminde (tiklayinca) cagrilir: (key=tradeID, text)
	def OnSelectTrade(self, tradeID, text):
		self.selectedTradeID = tradeID

	def OnViewSelected(self):
		tradeID = self.selectedTradeID
		if not tradeID:
			tradeID = self.listBox.GetSelectedItem()
		if not tradeID:
			return
		net.SendSafeTradeViewPacket(tradeID)
		if not self.parentInterface:
			return
		if self.outgoing:
			if self.ownerDict.get(tradeID, 0):
				# A (baslatan): Son Onay penceresi
				self.parentInterface.OpenSafeTradeConfirmWindow(tradeID)
			else:
				# B (alici): salt onizleme (Son Onay yok)
				self.parentInterface.OpenSafeTradePreviewWindow(tradeID)
		else:
			# B: gelen trade -> Itemleri Al penceresi
			self.parentInterface.OpenSafeTradeClaimWindow(tradeID)

	def OnClose(self):
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		self.OnClose()
		return True
