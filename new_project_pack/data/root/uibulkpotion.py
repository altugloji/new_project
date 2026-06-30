import os
import sys

import ui
import player
import mouseModule
import net
import app
import item
import chat
import uiScriptLocale
import localeInfo
import constInfo

BULK_POTION_SLOT_COUNT = 24
BULK_POTION_STATE_FILE = "bulk_potion_panel.cfg"
BULK_POTION_INVENTORY_OFFSET_X = 50
BULK_POTION_INVENTORY_OFFSET_Y = 60

def _CfgPaths():
	seen = set()
	out = []
	try:
		if getattr(sys, "frozen", False):
			root = os.path.dirname(sys.executable)
		else:
			argv0 = sys.argv[0]
			if argv0:
				root = os.path.dirname(os.path.abspath(argv0))
			else:
				root = ""
			if not root or root in (".", os.path.curdir):
				root = os.getcwd()
		p1 = os.path.join(os.path.normpath(root), BULK_POTION_STATE_FILE)
	except Exception:
		p1 = BULK_POTION_STATE_FILE
	for p in (p1, os.path.join(os.getcwd(), BULK_POTION_STATE_FILE), BULK_POTION_STATE_FILE):
		if not p:
			continue
		try:
			np = os.path.normpath(p)
		except Exception:
			np = p
		if np in seen:
			continue
		seen.add(np)
		out.append(np)
	return out

class BulkPotionWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.tooltipItem = None
		self.adwVnum = [0] * BULK_POTION_SLOT_COUNT
		self.isPanelLoaded = False		# YENI: panel bu oturumda cfg'den okundu mu / duzenlendi mi (bos-uzerine-yazma korumasi)
		self.__LoadWindow()
		self.LoadPanel()				# YENI: insa aninda kayitli durumu yukle; panel hic acilmasa bile asla "sahte bos" kalmaz

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/bulkpotionwindow.py")
		except:
			import exception
			exception.Abort("BulkPotionWindow.__LoadWindow")

		try:
			self.board = self.GetChild("Board")
			self.itemSlot = self.GetChild("ItemSlot")
			self.btnUse = self.GetChild("UseButton")
			self.btnClear = self.GetChild("ClearButton")
		except:
			import exception
			exception.Abort("BulkPotionWindow.BindObject")

		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.btnUse.SetEvent(ui.__mem_func__(self.OnUse))
		self.btnClear.SetEvent(ui.__mem_func__(self.OnClear))

		self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.OnSelectEmptySlot))
		self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.OnSelectItemSlot))
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OnOverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OnOverOutItem))

	def Initialize(self):
		self.tooltipItem = None
		self.adwVnum = [0] * BULK_POTION_SLOT_COUNT

	@ui.WindowDestroy
	def Destroy(self):
		self.SavePanel()
		self.Initialize()
		self.ClearDictionary()

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def __AlignNearInventory(self, wndInventory):
		if not wndInventory:
			self.SetCenterPosition()
			return

		(ix, iy) = wndInventory.GetGlobalPosition()
		ih = wndInventory.GetHeight()
		pw = self.GetWidth()
		ph = self.GetHeight()
		x = ix - BULK_POTION_INVENTORY_OFFSET_X - pw
		y = iy + (ih - ph) / 2 + BULK_POTION_INVENTORY_OFFSET_Y
		self.SetPosition(int(x), int(y))

	def Open(self, wndInventory=None):
		self.LoadPanel()
		self.__AlignNearInventory(wndInventory)
		self.Refresh()
		self.Show()
		self.SetTop()

	def Close(self):
		self.SavePanel()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnClear(self):
		self.adwVnum = [0] * BULK_POTION_SLOT_COUNT
		self.isPanelLoaded = True		# YENI: kullanici bilincli temizledi -> bu durum kaydedilmeli
		self.Refresh()

	def OnUse(self):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS():
			return

		hasAny = False
		for vnum in self.adwVnum:
			if vnum:
				hasAny = True
				break

		if not hasAny:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.BULK_POTION_EMPTY_PANEL)
			return

		net.SendBulkPotionUsePacket(self.adwVnum)

	def __CountVnumInInventory(self, vnum):
		total = 0
		size = player.INVENTORY_PAGE_SIZE * player.INVENTORY_PAGE_COUNT
		for i in xrange(size):
			if player.GetItemIndex(i) == vnum:
				total += player.GetItemCount(i)
		return total

	def Refresh(self):
		for i in xrange(BULK_POTION_SLOT_COUNT):
			vnum = self.adwVnum[i]
			if not vnum:
				self.itemSlot.ClearSlot(i)
				continue

			count = self.__CountVnumInInventory(vnum)
			if count <= 1:
				count = 0
			self.itemSlot.SetItemSlot(i, vnum, count)
		self.itemSlot.RefreshSlot()

	def OnSelectEmptySlot(self, slotIndex):
		if slotIndex < 0 or slotIndex >= BULK_POTION_SLOT_COUNT:
			return

		if not mouseModule.mouseController.isAttached():
			return

		attachedSlotType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()

		if player.SLOT_TYPE_INVENTORY != attachedSlotType:
			return

		itemVnum = player.GetItemIndex(attachedSlotPos)
		if not itemVnum:
			return

		if not constInfo.IS_BULK_POTION_ALLOWED(itemVnum):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.BULK_POTION_NOT_ALLOWED)
			return

		if itemVnum in self.adwVnum:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.BULK_POTION_ALREADY_REGISTERED)
			return

		self.adwVnum[slotIndex] = itemVnum
		self.isPanelLoaded = True		# YENI: kullanici slot atadi -> kaydedilebilir
		self.Refresh()

	def OnSelectItemSlot(self, slotIndex):
		if slotIndex < 0 or slotIndex >= BULK_POTION_SLOT_COUNT:
			return

		if mouseModule.mouseController.isAttached():
			self.OnSelectEmptySlot(slotIndex)
			return

		self.adwVnum[slotIndex] = 0
		self.isPanelLoaded = True		# YENI: kullanici slotu bilincli bosalttı -> kaydedilmeli
		self.Refresh()

	def OnOverInItem(self, slotIndex):
		if not self.tooltipItem:
			return
		if slotIndex < 0 or slotIndex >= BULK_POTION_SLOT_COUNT:
			return
		vnum = self.adwVnum[slotIndex]
		if not vnum:
			return
		self.tooltipItem.SetItemToolTip(vnum)

	def OnOverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def LoadPanel(self):
		paths = _CfgPaths()
		for path in paths:
			if not os.path.exists(path):
				continue
			try:
				lines = open(path, "r").readlines()
			except Exception:
				continue
			self.adwVnum = [0] * BULK_POTION_SLOT_COUNT
			for line in lines:
				line = line.strip()
				if not line or line.startswith("#"):
					continue
				parts = line.split("=", 1)
				if len(parts) != 2:
					continue
				try:
					idx = int(parts[0])
					vnum = int(parts[1])
				except ValueError:
					continue
				if idx < 0 or idx >= BULK_POTION_SLOT_COUNT:
					continue
				if constInfo.IS_BULK_POTION_ALLOWED(vnum):
					self.adwVnum[idx] = vnum
			self.isPanelLoaded = True		# YENI: cfg basariyla okundu -> kayitli durum gecerli, artik kaydedilebilir
			return

	def SavePanel(self):
		# YENI: panel bu oturumda hic yuklenmedi/duzenlenmedi -> kayitli cfg'yi BOS ile EZME.
		# (Asil "gir-cik iksir kaybi" bug fix: pencere her giriste sifir adwVnum ile olusup
		#  hicbir sey acilmadan cikista SavePanel cagriliyor ve dosyayi siliyordu.)
		if not getattr(self, "isPanelLoaded", False):
			return

		paths = _CfgPaths()
		path = paths[0] if paths else BULK_POTION_STATE_FILE

		# Tum cikti tek seferde hazirlanir (satir-satir yazimda yarim-yazim riskini azaltir)
		data = ""
		for i in xrange(BULK_POTION_SLOT_COUNT):
			if self.adwVnum[i]:
				data += "%d=%d\n" % (i, self.adwVnum[i])

		# YENI: once .tmp'e yaz, sonra yerine koy -> relog/Destroy crash penceresinde
		# mevcut cfg yarim/bos kalmaz (eski dosyaya hic dokunulmadan once tam veri yazilir).
		tmp = path + ".tmp"
		try:
			f = open(tmp, "w")
			try:
				f.write(data)
			finally:
				f.close()
		except Exception:
			return

		try:
			os.rename(tmp, path)
		except OSError:
			# Windows: hedef dosya zaten varsa rename hata verir -> eskiyi sil, tekrar dene
			try:
				os.remove(path)
			except OSError:
				pass
			try:
				os.rename(tmp, path)
			except OSError:
				try:
					os.remove(tmp)
				except OSError:
					pass
