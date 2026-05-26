import dbg
import player
import item
import net
import snd
import ui
import uiToolTip
import localeInfo
import constInfo

class EfsunChangeDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.scrollItemPos = 0
		self.targetItemPos = 0
		self.scrollVnum = 0
		self.itemToolTip = None
		self.scrollCountText = None
		self.__LoadScript()

	def __LoadScript(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/efsunchangedialog.py")
		except:
			import exception
			exception.Abort("EfsunChangeDialog.__LoadScript.LoadObject")

		try:
			self.board = self.GetChild("Board")
			self.titleBar = self.GetChild("TitleBar")
			self.scrollCountText = self.GetChild("ScrollCountText")
			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.OnChange))
			self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Close))
		except:
			import exception
			exception.Abort("EfsunChangeDialog.__LoadScript.BindObject")

		itemToolTip = uiToolTip.ItemToolTip()
		itemToolTip.SetParent(self.board)
		itemToolTip.SetPosition(25, 35)
		itemToolTip.SetFollow(False)
		itemToolTip.Show()
		self.itemToolTip = itemToolTip

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	@ui.WindowDestroy
	def Destroy(self):
		if self.itemToolTip:
			self.itemToolTip.Hide()
			self.itemToolTip = None
		self.ClearDictionary()
		self.board = None
		self.titleBar = None
		self.scrollCountText = None

	def Open(self, scrollItemPos, targetItemPos):
		self.scrollItemPos = scrollItemPos
		self.targetItemPos = targetItemPos
		self.scrollVnum = player.GetItemIndex(scrollItemPos)

		if not self.RefreshDisplay():
			return

		self.SetCenterPosition()
		self.SetTop()
		self.Show()

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def RefreshDisplay(self):
		itemIndex = player.GetItemIndex(self.targetItemPos)
		scrollIndex = player.GetItemIndex(self.scrollItemPos)

		if itemIndex == 0 or scrollIndex == 0:
			self.Close()
			return False

		hasAttr = False
		for i in xrange(player.ATTRIBUTE_SLOT_MAX_NUM):
			if player.GetItemAttribute(self.targetItemPos, i)[0] != 0:
				hasAttr = True
				break
		if not hasAttr:
			self.Close()
			return False

		self.itemToolTip.ClearToolTip()
		item.SelectItem(itemIndex)
		self.itemToolTip.AppendTextLine(
			"Vnum: %d  Type: %d  SubType: %d" % (itemIndex, item.GetItemType(), item.GetItemSubType()),
			0xFFFFFFFF)
		self.itemToolTip.AppendSpace(5)
		self.itemToolTip.SetInventoryItem(self.targetItemPos)

		self.__RefreshScrollCountText()

		self.UpdateDialog()
		return True

	def __RefreshScrollCountText(self):
		if not self.scrollCountText:
			return

		scrollVnum = self.scrollVnum
		if scrollVnum == 0:
			scrollVnum = player.GetItemIndex(self.scrollItemPos)

		if scrollVnum == 0:
			self.scrollCountText.SetText("")
			return

		self.scrollVnum = scrollVnum
		scrollCount = player.GetItemCountByVnum(scrollVnum)
		if scrollCount <= 0:
			self.Close()
			return
		self.scrollCountText.SetText("Envanterindeki Efsun Nesnesi: %d" % scrollCount)

	def UpdateDialog(self):
		if not self.itemToolTip:
			return

		toolTipWidth = self.itemToolTip.GetWidth()
		toolTipHeight = self.itemToolTip.GetHeight()

		newWidth = max(280, toolTipWidth + 40)
		newHeight = max(220, toolTipHeight + 115)

		self.board.SetSize(newWidth, newHeight)
		self.titleBar.SetWidth(newWidth - 15)
		self.SetSize(newWidth, newHeight)

		(x, y) = self.GetLocalPosition()
		self.SetPosition(x, y)

	def OnChange(self):
		if player.GetItemIndex(self.scrollItemPos) == 0 or player.GetItemIndex(self.targetItemPos) == 0:
			self.Close()
			return

		net.SendItemUseToItemPacket(self.scrollItemPos, self.targetItemPos)
		snd.PlaySound("sound/ui/make_soket.wav")
		self.SetTop()

	def Close(self):
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True
