import ui
import app
import item
import localeInfo
import uiToolTip
import player
import grp
import cube_renewal
import mouseModule
import constInfo
import chat
import snd
import net
import chr

COLOR_MATERIAL_ENOUGH = grp.GenerateColor(0.5411, 0.7254, 0.5568, 1.0)
COLOR_MATERIAL_SHORT = grp.GenerateColor(0.9, 0.4745, 0.4627, 1.0)

# Grid script: 7x2 = 14 material slots (fixed layout). Packet may send up to 10 pairs.
MATERIAL_GRID_SLOTS = 14
MAX_PACKET_MATERIALS = 10

# YENI: toplu uretim KAPALI (server ENABLE_CUBE_RENEWAL_DISABLE_BULK ile senkron olmali).
# 1 iken miktar alani duzenlenemez ve make paketi daima tek parti (count=1) gonderir.
CUBE_DISABLE_BULK_PRODUCTION = 1

# YENI: cube grid'ine secilebilecek azami Beceri Kitabi sayisi.
# uiscript SKILL_GRID_COLS*SKILL_GRID_ROWS ve server CUBE_SKILL_GRID_MAX ile AYNI olmali.
CUBE_SKILL_GRID_MAX = 26

# YENI: pencere 20001'de buyur. Eklenen yukseklik = uiscript (BOARD_H_BIG - BOARD_H_SMALL).
# Bu deger uiscript ile SENKRON olmali (grid 3px asagi alindiktan sonra 89 px).
CUBE_SKILL_SECTION_H = 89
# Alt butonlarin tahta altindan ofseti (uiscript: "y" = BOARD_H - 35)
CUBE_SKILL_BTN_BOTTOM_MARGIN = 35

# YENI: GetWidth/GetHeight nadiren 0 donerse (layout henuz oturmamis) kullanilacak yedek olculer.
# 0-boyut pencere gorunmez kalir ama input'u yutar (client donmasi) -> uiscript ile AYNI yedege dus.
# cuberenewalwindow.py icindeki BOARD_W / BOARD_H_SMALL ile senkron tutulmali.
CUBE_BOARD_W_FALLBACK = 445
CUBE_BOARD_H_SMALL_FALLBACK = 633

# YENI: OnUpdate'teki PASIF tam-repaint kac karede bir calissin. Her kare _PaintVisibleRows
# (6 satir x malzeme = kare basina yuzlerce GetDates/tuple) zayif PC'de hafif donma yapiyordu.
# Secim/scroll/arama/miktar olaylari Refresh()'i zaten ANINDA cagirir; bu sadece envanter
# kaymasini (malzeme adedi/tint) yansitmak icin -> saniyede ~10 kez yeter.
CUBE_UPDATE_PAINT_EVERY = 6


# YENI: parse edilmis tarif info dict'i, index bazinda cache. cube_renewal.GetDates her cagrida
# C++'ta 26-elemanli tuple kurup donduruyordu; _PaintVisibleRows bunu kare basina yuzlerce kez
# cagiriyordu (hafif donma). Tarif verisi acik pencere boyunca SABIT oldugu icin guvenle cache'lenir;
# yeni liste (BINARY_CUBE_RENEWAL_LOADING) ve pencere kapanisinda (_ClearCubeDatesCache) bosaltilir.
_CUBE_DATES_CACHE = {}


def _ClearCubeDatesCache():
	_CUBE_DATES_CACHE.clear()


def _BuildCubeInfo(index):
	raw = cube_renewal.GetDates(index)
	if raw is None:
		raw = ()
	n = len(raw)
	info = {
		"vnum_reward" : 0,
		"count_reward" : 0,
		"item_reward_stackable" : 0,
		"gold" : 0,
		"percent" : 0,
		"category" : "",
	}
	for mi in xrange(1, MAX_PACKET_MATERIALS + 1):
		info["vnum_material_%d" % mi] = 0
		info["count_material_%d" % mi] = 0
	# Tuple layout: (vnum_reward, count_reward, stackable, vnum_m1, cnt_m1, ... , gold, percent, category)
	if n >= 9:
		info["gold"] = raw[-3]
		info["percent"] = raw[-2]
		info["category"] = raw[-1]
		info["vnum_reward"] = raw[0]
		info["count_reward"] = raw[1]
		info["item_reward_stackable"] = raw[2]
		mid = raw[3:-3]
		pair_count = len(mid) // 2
		if pair_count > MAX_PACKET_MATERIALS:
			pair_count = MAX_PACKET_MATERIALS
		for mi in xrange(1, pair_count + 1):
			base = (mi - 1) * 2
			info["vnum_material_%d" % mi] = mid[base]
			info["count_material_%d" % mi] = mid[base + 1]
	return info


def FReturnInfo(func, index):
	info = _CUBE_DATES_CACHE.get(index)
	if info is None:
		info = _BuildCubeInfo(index)
		_CUBE_DATES_CACHE[index] = info
	return info[func]


class CubeRenewalWindows(ui.ScriptWindow):
	VISIBLE_ROWS = 6

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		cube_renewal.SetCubeRenewalHandler(self)

		self.selectedRecipeGlobalIndex = -1
		self.firstSlotIndex = 0
		self.matchingIndices = []
		self._lastSearchText = None

		self.count_item_reward = 0
		self.vnum_item_improve = 79605
		self.max_count_item_improve = 40
		self.slot_item_improve = -1
		self.interface = 0

		self.toolTip = uiToolTip.ItemToolTip()

		self.titleBar = None
		self.btnAccept = None
		self.btnCancel = None
		self.contentScrollbar = None
		self.searchEdit = None
		self.searchClearButton = None
		self.searchPlaceholder = None
		self.recipeRowBoards = []
		self.recipeResultSlots = []
		self.recipeMaterialSlots = []
		self.recipeGoldTexts = []
		self.recipePercentTexts = []
		self.recipeRowHighlights = []

		self.result_qty = None
		self.qty_sub_button = None
		self.qty_add_button = None
		self.imporve_slot = None
		self.slot_improve = None

		# YENI: beceri kitabi secim grid'i
		self.skill_grid = None
		self.skill_grid_label = None
		self.skill_grid_bg = None
		self.skillSlotList = []
		self.skillGridEnabled = 0  # sadece CUBE_SKILL_GRID_NPC'de server 1 yapar

		# YENI: OnUpdate pasif-repaint throttle sayaci (her kare degil)
		self._updateTick = 0

		# YENI: pencere yeniden boyutlandirma baseline'lari (yuklemede okunur)
		self.board = None
		self._cubeBoardW = 0
		self._cubeBoardHSmall = 0
		self._cubeBoardHBig = 0
		self._acceptBtnX = 0
		self._cancelBtnX = 0

		self.LoadWindow()

	def __del__(self):
		cube_renewal.SetCubeRenewalHandler(None)
		ui.ScriptWindow.__del__(self)

	def _LogCubeErr(self, where):
		# YENI: yutulan Python exception'larini syserr.txt'e yaz (nadir "acilmiyor/donuyor" teshisi icin)
		try:
			import dbg, traceback
			dbg.TraceError("[CUBE_RENEWAL] %s\n%s" % (where, traceback.format_exc()))
		except:
			pass

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/cuberenewalwindow.py")
		except:
			import exception
			exception.Abort("CubeRenewalWindows.LoadWindow.LoadObject")

		try:
			GetObject = self.GetChild
			self.board = GetObject("board")
			self.titleBar = GetObject("TitleBar")
			self.btnAccept = GetObject("AcceptButton")
			self.btnCancel = GetObject("CancelButton")
			self.contentScrollbar = GetObject("contentScrollbar")
			self.searchEdit = GetObject("searchEdit")
			self.searchClearButton = GetObject("searchClearButton")
			_ed = self.ElementDictionary
			self.searchPlaceholder = _ed.get("searchPlaceholder")

			self.recipeRowBoards = []
			self.recipeResultSlots = []
			self.recipeMaterialSlots = []
			self.recipeGoldTexts = []
			self.recipePercentTexts = []
			self.recipeRowHighlights = []

			for i in xrange(self.VISIBLE_ROWS):
				p = "recipeRow%d" % (i + 1)
				self.recipeRowBoards.append(GetObject("%sBoard" % p))
				self.recipeResultSlots.append(GetObject("%sResult" % p))
				self.recipeMaterialSlots.append(GetObject("%sMaterials" % p))
				self.recipeGoldTexts.append(GetObject("%sGoldText" % p))
				self.recipePercentTexts.append(GetObject("%sPercentText" % p))
				self.recipeRowHighlights.append(GetObject("%sHighlight" % p))

			for vis in xrange(self.VISIBLE_ROWS):
				rs = self.recipeResultSlots[vis]
				ms = self.recipeMaterialSlots[vis]
				rs.SetOverInItemEvent(lambda slot, v=vis: self.__OverInCubeResultSlot(0, v))
				rs.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutMaterialSlot))
				rs.SetSelectEmptySlotEvent(lambda slot, v=vis: self.__OnRecipeResultSlotClick(v, slot))
				rs.SetSelectItemSlotEvent(lambda slot, v=vis: self.__OnRecipeResultSlotClick(v, slot))
				ms.SetOverInItemEvent(lambda slot, v=vis: self.__OverInMaterialSlotGrid(v, slot))
				ms.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutMaterialSlot))
				ms.SetSelectEmptySlotEvent(lambda slot, v=vis: self.__OnRecipeMaterialSlotClick(v, slot))
				ms.SetSelectItemSlotEvent(lambda slot, v=vis: self.__OnRecipeMaterialSlotClick(v, slot))

			def _RowPickDown(row):
				def OnMouseLeftButtonDown():
					self.__OnRecipeRowSelect(row)
					return True
				return OnMouseLeftButtonDown

			for vis in xrange(self.VISIBLE_ROWS):
				rowDown = _RowPickDown(vis)
				self.recipeRowBoards[vis].OnMouseLeftButtonDown = rowDown
				for suffix in ("GoldCircle", "LuckCircle", "Arrow", "GoldIcon", "GoldText", "PercentText"):
					try:
						GetObject("recipeRow%d%s" % (vis + 1, suffix)).OnMouseLeftButtonDown = rowDown
					except:
						pass

			self.result_qty = GetObject("result_qty")
			self.qty_sub_button = GetObject("qty_sub_button")
			self.qty_add_button = GetObject("qty_add_button")
			self.imporve_slot = GetObject("imporve_slot")
			self.skill_grid = GetObject("skill_grid")
			self.skill_grid_label = self.ElementDictionary.get("skill_grid_label")
			self.skill_grid_bg = self.ElementDictionary.get("skill_grid_bg")

		except:
			import exception
			exception.Abort("CubeRenewalWindows.LoadWindow.LoadElements")

		self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
		self.btnCancel.SetEvent(self.Close)
		self.btnAccept.SetEvent(self.AceptCube)

		self.contentScrollbar.SetScrollEvent(ui.__mem_func__(self.OnScrollResultList))
		self.contentScrollbar.SetScrollStep(0.9)

		self.result_qty.SetReturnEvent(self.AceptInputItem)
		self.result_qty.CanEdit(False)
		self.qty_sub_button.SetEvent(self.QtySubButton)
		self.qty_add_button.SetEvent(self.QtyAddButton)

		self.searchClearButton.SetEvent(ui.__mem_func__(self.__OnSearchClear))
		if self.searchEdit:
			self.searchEdit.SetReturnEvent(ui.__mem_func__(self.__OnSearchReturn))
			self.searchEdit.SetText("")

		for hl in self.recipeRowHighlights:
			hl.Hide()

		self.slot_improve = ui.SlotWindow()
		self.slot_improve.SetParent(self.imporve_slot)
		self.slot_improve.SetSize(32, 32)
		self.slot_improve.SetPosition(6, 5)
		self.slot_improve.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnSelectEmptySlot))
		self.slot_improve.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSelectItemSlot))
		self.slot_improve.AppendSlot(0, 0, 0, 32, 32)
		self.slot_improve.Show()

		# YENI: beceri kitabi grid eventleri (grid_table zaten slotlari olusturur)
		if self.skill_grid:
			self.skill_grid.SetSelectEmptySlotEvent(ui.__mem_func__(self.__OnSkillSlotEmpty))
			self.skill_grid.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSkillSlotItem))
			self.skill_grid.SetOverInItemEvent(ui.__mem_func__(self.__OverInSkillSlot))
			self.skill_grid.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutSkillSlot))

		# YENI: pencere boyut baseline'lari (kucuk/orijinal olculer) yuklemeden sonra okunur.
		# GetWidth/GetHeight nadiren 0 donebilir; 0 ise uiscript yedegine dus, yoksa _ApplyWindowSize
		# SetSize(0,..) cagirip gorunmez-ama-input-yutan (donuk) pencere yaratir.
		self._cubeBoardW = self.GetWidth()
		self._cubeBoardHSmall = self.GetHeight()
		if self._cubeBoardW <= 0:
			self._cubeBoardW = CUBE_BOARD_W_FALLBACK
		if self._cubeBoardHSmall <= 0:
			self._cubeBoardHSmall = CUBE_BOARD_H_SMALL_FALLBACK
		self._cubeBoardHBig = self._cubeBoardHSmall + CUBE_SKILL_SECTION_H
		try:
			(self._acceptBtnX, _ay) = self.btnAccept.GetLocalPosition()
			(self._cancelBtnX, _cy) = self.btnCancel.GetLocalPosition()
		except:
			self._acceptBtnX = 353
			self._cancelBtnX = 273

		# YENI: grid varsayilan gizli + pencere kucuk (sadece 20001'de server acar)
		self.SetSkillGridEnable(0)

		self.Refresh()

	def OnMouseWheel(self, delta):
		if not self.contentScrollbar or not self.contentScrollbar.IsShow():
			return False
		if max(0, len(self.matchingIndices) - self.VISIBLE_ROWS) <= 0:
			return False
		sb = self.contentScrollbar
		wheel = getattr(sb, "OnMouseWheel", None)
		if wheel:
			return wheel(delta)
		step = sb.GetScrollStep() / 4
		if delta > 0:
			sb.SetPos(sb.GetPos() - step)
		else:
			sb.SetPos(sb.GetPos() + step)
		return True

	def _RecipeCount(self):
		return cube_renewal.CountDates()

	def _RecipeIndexForVisibleRow(self, visibleRow):
		pos = self.firstSlotIndex + visibleRow
		if pos < 0 or pos >= len(self.matchingIndices):
			return -1
		return self.matchingIndices[pos]

	def _RefreshMatchingIndices(self):
		prevSel = self.selectedRecipeGlobalIndex
		kw = ""
		if self.searchEdit:
			try:
				kw = self.searchEdit.GetText().strip().lower()
			except:
				kw = ""

		n = self._RecipeCount()
		if not kw:
			self.matchingIndices = range(n)
		else:
			self.matchingIndices = []
			for i in xrange(n):
				vnum = FReturnInfo("vnum_reward", i)
				if vnum == 0:
					continue
				# YENI: client item_proto'sunda olmayan vnum SelectItem/GetItemName'de patlayabilir;
				# tek bozuk tarif tum aramayi (ve render'i) kesmesin.
				try:
					item.SelectItem(vnum)
					name = item.GetItemName().lower()
				except:
					name = ""
				if kw in name:
					self.matchingIndices.append(i)

		maxStart = max(0, len(self.matchingIndices) - self.VISIBLE_ROWS)
		if self.firstSlotIndex > maxStart:
			self.firstSlotIndex = maxStart

		if 0 == len(self.matchingIndices):
			self.selectedRecipeGlobalIndex = -1
		elif self.selectedRecipeGlobalIndex not in self.matchingIndices:
			self.selectedRecipeGlobalIndex = self.matchingIndices[0]

		# Sunucu Cube_Make: count_item == 0 ise sessizce cikiyor. Otomatik secilen tarif icin miktar 0 kalmasin.
		if self.selectedRecipeGlobalIndex >= 0:
			cr = FReturnInfo("count_reward", self.selectedRecipeGlobalIndex)
			if cr <= 0:
				cr = 1
			if self.selectedRecipeGlobalIndex != prevSel or self.count_item_reward < cr:
				self.count_item_reward = cr
				if self.result_qty:
					self.result_qty.SetText("%d" % self.count_item_reward)

	def _SyncContentScrollbarPos(self):
		if not self.contentScrollbar:
			return
		scmax = max(0, len(self.matchingIndices) - self.VISIBLE_ROWS)
		if scmax > 0:
			self.contentScrollbar.SetPos(float(self.firstSlotIndex) / float(scmax))
		else:
			self.contentScrollbar.SetPos(0)

	def OnScrollResultList(self):
		scrollLineCount = max(0, len(self.matchingIndices) - self.VISIBLE_ROWS)
		if scrollLineCount <= 0:
			startIndex = 0
		else:
			startIndex = min(scrollLineCount, int(round(self.contentScrollbar.GetPos() * scrollLineCount)))

		if startIndex != self.firstSlotIndex:
			self.firstSlotIndex = startIndex
			self.Refresh()

	def __OnSearchClear(self):
		if self.searchEdit:
			self.searchEdit.SetText("")
		self._lastSearchText = ""
		self.firstSlotIndex = 0
		self.contentScrollbar.SetPos(0)
		self.Refresh()

	def __OnSearchReturn(self):
		if self.searchEdit:
			try:
				self._lastSearchText = self.searchEdit.GetText()
			except:
				self._lastSearchText = ""
		self.firstSlotIndex = 0
		self.contentScrollbar.SetPos(0)
		self.Refresh()

	def __OverOutMaterialSlot(self):
		self.toolTip.Hide()

	def __OverInMaterialSlotGrid(self, visibleRow, slotPos):
		if slotPos < 0 or slotPos >= MATERIAL_GRID_SLOTS:
			self.__OverOutMaterialSlot()
			return
		self.__OverInMaterialSlot(0, visibleRow, slotPos)

	def __OnRecipeMaterialSlotClick(self, visibleRow, slotPos):
		if slotPos < 0 or slotPos >= MATERIAL_GRID_SLOTS:
			return
		recipeIndex = self._RecipeIndexForVisibleRow(visibleRow)
		if recipeIndex < 0:
			return
		matIdx = slotPos + 1
		if matIdx > MAX_PACKET_MATERIALS:
			self.__OnRecipeRowSelect(visibleRow)
			return
		if chr.IsGameMaster(player.GetMainCharacterIndex()):
			mv = FReturnInfo("vnum_material_%d" % matIdx, recipeIndex)
			if mv:
				net.SendChatPacket("/i %d 100" % mv)
				try:
					snd.PlaySound("sound/ui/pick.wav")
				except:
					pass
				return
		self.__OnRecipeRowSelect(visibleRow)

	def __OnRecipeResultSlotClick(self, visibleRow, slotIdx):
		self.__OnRecipeRowSelect(visibleRow)

	def __OnRecipeRowSelect(self, visibleRow):
		idx = self._RecipeIndexForVisibleRow(visibleRow)
		if idx < 0:
			return
		self.selectedRecipeGlobalIndex = idx
		self.count_item_reward = FReturnInfo("count_reward", idx)
		self.result_qty.KillFocus()
		if CUBE_DISABLE_BULK_PRODUCTION:
			self.result_qty.CanEdit(False)
		else:
			self.result_qty.CanEdit(FReturnInfo("item_reward_stackable", idx))
		self.result_qty.SetText("%s" % self.count_item_reward)
		self.result_qty.Show()
		self.Refresh()

	# YENI: henuz uretilmemis item onizlemesi icin socket doldur; sureli item'lerde
	# tooltip sureyi socket(0)'dan okur, hepsi 0 gecilince sure hic gorunmuyordu.
	# Degerler server item_manager.cpp CreateItem ile AYNI (REAL_TIME: now+deger,
	# 0 ise 7 gun; TIMER_BASED_ON_WEAR: deger, 0 ise 10 saat). START_FIRST_USE'a
	# dokunma: tooltip socket(0)==0 iken sureyi zaten proto'dan hesapliyor.
	def __BuildPreviewMetinSlot(self, vnum):
		metinSlot = []
		for i in xrange(player.METIN_SOCKET_MAX_NUM):
			metinSlot.append(0)

		try:
			item.SelectItem(vnum)
			for i in xrange(item.LIMIT_MAX_NUM):
				(limitType, limitValue) = item.GetLimit(i)
				if item.LIMIT_REAL_TIME == limitType:
					if limitValue == 0:
						limitValue = 60 * 60 * 24 * 7
					metinSlot[0] = app.GetGlobalTimeStamp() + limitValue
					break
				elif item.LIMIT_TIMER_BASED_ON_WEAR == limitType:
					if limitValue == 0:
						limitValue = 60 * 60 * 10
					metinSlot[0] = limitValue
					break
		except:
			pass

		return metinSlot

	def __OverInCubeResultSlot(self, trash, visibleRow):
		self.toolTip.ClearToolTip()

		recipeIndex = self._RecipeIndexForVisibleRow(visibleRow)
		if recipeIndex < 0:
			return

		vnum = FReturnInfo("vnum_reward", recipeIndex)
		if vnum == 0:
			return

		self.toolTip.AddItemData(vnum, self.__BuildPreviewMetinSlot(vnum))

	def __OverInMaterialSlot(self, trash, visibleRow, col):
		self.toolTip.ClearToolTip()

		recipeIndex = self._RecipeIndexForVisibleRow(visibleRow)
		if recipeIndex < 0:
			return

		matIdx = col + 1
		if matIdx > MAX_PACKET_MATERIALS:
			return
		vnum = FReturnInfo("vnum_material_%d" % matIdx, recipeIndex)
		if vnum == 0:
			return

		self.toolTip.AddItemData(vnum, self.__BuildPreviewMetinSlot(vnum))

		cnt = self._MaterialNeedCount(recipeIndex, matIdx)
		have = player.GetItemCountByVnum(vnum)
		if have >= cnt:
			self.toolTip.AppendTextLine(
				getattr(localeInfo, "CUBE_RENEWAL_MATERIAL_COUNT", "%d / %d") % (have, cnt),
				COLOR_MATERIAL_ENOUGH).SetFeather()
		else:
			self.toolTip.AppendTextLine(
				getattr(localeInfo, "CUBE_RENEWAL_MATERIAL_COUNT", "%d / %d") % (have, cnt),
				COLOR_MATERIAL_SHORT).SetFeather()

		self.toolTip.Show()

	def _MaterialNeedCount(self, recipeIndex, matIdx):
		base = FReturnInfo("count_material_%d" % matIdx, recipeIndex)
		if recipeIndex != self.selectedRecipeGlobalIndex:
			return base
		cr = max(1, FReturnInfo("count_reward", recipeIndex))
		count = max(1, self.count_item_reward / cr)
		return base * count

	def _TintMaterialSlot(self, matSlot, col, recipeIndex, applyShortageTint):
		matIdx = col + 1
		if matIdx > MAX_PACKET_MATERIALS:
			matSlot.DeactivateSlot(col)
			return
		vnum = FReturnInfo("vnum_material_%d" % matIdx, recipeIndex)
		if vnum == 0:
			matSlot.DeactivateSlot(col)
			return
		if not applyShortageTint:
			matSlot.DeactivateSlot(col)
			return
		need = self._MaterialNeedCount(recipeIndex, matIdx)
		if player.GetItemCountByVnum(vnum) >= need:
			matSlot.DeactivateSlot(col)
		else:
			matSlot.ActivateSlot(col, 220.0 / 255.0, 52.0 / 255.0, 52.0 / 255.0, 0.62)

	def _EffectivePercent(self, recipeIndex):
		base = FReturnInfo("percent", recipeIndex)
		if recipeIndex != self.selectedRecipeGlobalIndex:
			return base
		add = self.GetPorcentNew()
		if add == 0:
			return base
		return min(100, base + add)

	def GetPorcentNew(self):
		index_improve = self.slot_item_improve
		if index_improve != -1:
			itemVNum = player.GetItemIndex(index_improve)
			itemCount = player.GetItemCount(index_improve)
			if itemVNum == self.vnum_item_improve and itemCount <= self.max_count_item_improve:
				return itemCount
		return 0

	def _RowGoldDisplay(self, recipeIndex):
		base = FReturnInfo("gold", recipeIndex)
		if recipeIndex != self.selectedRecipeGlobalIndex:
			return base
		cr = max(1, FReturnInfo("count_reward", recipeIndex))
		count = max(1, self.count_item_reward / cr)
		return base * count

	def _PaintVisibleRows(self):
		# YENI: bir satirin bozuk verisi (eksik vnum / bozuk gold) tum paint'i kesip
		# pencereyi gorunmez+donuk birakmasin; her satir kendi try/except'inde.
		for vis in xrange(self.VISIBLE_ROWS):
			try:
				self._PaintVisibleRow(vis)
			except:
				self._LogCubeErr("_PaintVisibleRow[%d]" % vis)

	def _PaintVisibleRow(self, vis):
		board = self.recipeRowBoards[vis]
		highlight = self.recipeRowHighlights[vis]
		resultSlot = self.recipeResultSlots[vis]
		matSlot = self.recipeMaterialSlots[vis]
		goldText = self.recipeGoldTexts[vis]
		pctText = self.recipePercentTexts[vis]

		idxInList = self.firstSlotIndex + vis
		if idxInList >= len(self.matchingIndices):
			board.Hide()
			highlight.Hide()
			resultSlot.ClearSlot(0)
			for clearIdx in xrange(matSlot.GetSlotCount()):
				matSlot.DeactivateSlot(clearIdx)
				matSlot.ClearSlot(clearIdx)
			return

		board.Show()
		recipeIdx = self.matchingIndices[idxInList]

		if recipeIdx == self.selectedRecipeGlobalIndex:
			highlight.Show()
		else:
			highlight.Hide()

		vReward = FReturnInfo("vnum_reward", recipeIdx)
		cReward = FReturnInfo("count_reward", recipeIdx)
		if vReward != 0:
			if recipeIdx == self.selectedRecipeGlobalIndex:
				resultSlot.SetItemSlot(0, vReward, self.count_item_reward)
			else:
				resultSlot.SetItemSlot(0, vReward, cReward)
		else:
			resultSlot.ClearSlot(0)

		goldText.SetText(localeInfo.NumberToString(self._RowGoldDisplay(recipeIdx)))
		pctText.SetText("%d%%" % self._EffectivePercent(recipeIdx))

		maxCol = min(MATERIAL_GRID_SLOTS, matSlot.GetSlotCount())
		for col in xrange(maxCol):
			matIdx = col + 1
			if matIdx > MAX_PACKET_MATERIALS:
				matSlot.DeactivateSlot(col)
				matSlot.ClearSlot(col)
				continue
			mvnum = FReturnInfo("vnum_material_%d" % matIdx, recipeIdx)
			mcount = FReturnInfo("count_material_%d" % matIdx, recipeIdx)
			if mvnum != 0:
				if recipeIdx == self.selectedRecipeGlobalIndex:
					cr = max(1, FReturnInfo("count_reward", recipeIdx))
					mult = max(1, self.count_item_reward / cr)
					matSlot.SetItemSlot(col, mvnum, mcount * mult)
				else:
					matSlot.SetItemSlot(col, mvnum, mcount)
				self._TintMaterialSlot(matSlot, col, recipeIdx, recipeIdx == self.selectedRecipeGlobalIndex)
			else:
				matSlot.DeactivateSlot(col)
				matSlot.ClearSlot(col)

		for k in xrange(maxCol, matSlot.GetSlotCount()):
			matSlot.DeactivateSlot(k)
			matSlot.ClearSlot(k)

		matSlot.RefreshSlot()

	def _SyncScrollbarToList(self):
		mi = len(self.matchingIndices)
		if mi <= self.VISIBLE_ROWS:
			self.contentScrollbar.SetMiddleBarSize(1.0)
		else:
			self.contentScrollbar.SetMiddleBarSize(float(self.VISIBLE_ROWS) / float(mi))
		self._SyncContentScrollbarPos()

	def Refresh(self):
		# YENI: tek bir bozuk tarif/veri pencereyi cizemez (gorunmez+donuk) hale getirmesin.
		try:
			self._RefreshMatchingIndices()
			self._PaintVisibleRows()
			self._SyncScrollbarToList()
		except:
			self._LogCubeErr("Refresh")

	def _UpdateConstInfoCubeCount(self):
		if self.selectedRecipeGlobalIndex < 0:
			constInfo.cube_count_items = {}
			return
		constInfo.cube_count_items = {}
		for i in xrange(1, MAX_PACKET_MATERIALS + 1):
			constInfo.cube_count_items[i - 1] = FReturnInfo("vnum_material_%d" % i, self.selectedRecipeGlobalIndex)

	def BINARY_CUBE_RENEWAL_LOADING(self):
		# YENI: yeni tarif listesi geldi -> eski parse cache'ini bosalt (farkli NPC = farkli veri)
		_ClearCubeDatesCache()
		self.selectedRecipeGlobalIndex = -1
		self.firstSlotIndex = 0
		self.count_item_reward = 0
		self.slot_item_improve = -1
		# YENI: pencere acilista grid gizli baslar; server (Cube_open) 20001 ise cube_skill_grid 1 ile acar
		self.SetSkillGridEnable(0)
		if self.searchEdit:
			self.searchEdit.SetText("")
		self._lastSearchText = ""
		self.contentScrollbar.SetPos(0)
		constInfo.CUBE_RENEWAL_IS_OPENED = 1
		self.Refresh()
		if self.result_qty:
			if self.selectedRecipeGlobalIndex >= 0:
				self.result_qty.Show()
			else:
				self.result_qty.Hide()

	def BINARY_CUBE_RENEWAL_UPDATE(self):
		self.Refresh()

	def __OnSelectEmptySlot(self, selectedSlotPos):
		if self.selectedRecipeGlobalIndex < 0:
			return
		if self._EffectivePercent(self.selectedRecipeGlobalIndex) >= 100:
			return
		if not mouseModule.mouseController.isAttached():
			return
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		itemVNum = player.GetItemIndex(attachedSlotPos)
		itemCount = player.GetItemCount(attachedSlotPos)
		if itemVNum == self.vnum_item_improve and itemCount <= self.max_count_item_improve:
			self.slot_improve.SetItemSlot(selectedSlotPos, itemVNum, itemCount)
			self.slot_item_improve = attachedSlotPos

	def __OnSelectItemSlot(self, selectedSlotPos):
		if self.selectedRecipeGlobalIndex < 0:
			return
		if self._EffectivePercent(self.selectedRecipeGlobalIndex) >= 100:
			return
		if mouseModule.mouseController.isAttached():
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			mouseModule.mouseController.DeattachObject()
			itemVNum = player.GetItemIndex(attachedSlotPos)
			itemCount = player.GetItemCount(attachedSlotPos)
			if itemVNum == self.vnum_item_improve and itemCount <= self.max_count_item_improve:
				self.slot_improve.SetItemSlot(selectedSlotPos, itemVNum, itemCount)
				self.slot_item_improve = attachedSlotPos
		else:
			self.slot_improve.SetItemSlot(0, 0, 0)
			self.slot_item_improve = -1

	# --- YENI: Beceri Kitabi secim grid'i ---
	def _IsSkillBookSlot(self, invSlot):
		vnum = player.GetItemIndex(invSlot)
		if vnum == 0:
			return False
		# YENI: bozuk/eksik proto SelectItem'da patlamasin (OnUpdate'te her kare cagriliyor)
		try:
			item.SelectItem(vnum)
			return item.GetItemType() == item.ITEM_TYPE_SKILLBOOK
		except:
			return False

	def _ApplyWindowSize(self, big):
		# 20001'de buyuk, diger NPC'lerde orijinal/kucuk pencere boyutu.
		# Hem yukseklik HEM genislik gecerli olmali; aksi halde SetSize(0,..) gorunmez+donuk pencere yapar.
		if not self._cubeBoardHSmall or not self._cubeBoardW:
			return
		h = self._cubeBoardHBig if big else self._cubeBoardHSmall
		self.SetSize(self._cubeBoardW, h)
		if self.board:
			self.board.SetSize(self._cubeBoardW, h)  # Board.SetSize 9-parca zemini yeniden stretch eder
		btnY = h - CUBE_SKILL_BTN_BOTTOM_MARGIN
		if self.btnAccept:
			self.btnAccept.SetPosition(self._acceptBtnX, btnY)
		if self.btnCancel:
			self.btnCancel.SetPosition(self._cancelBtnX, btnY)

	def SetSkillGridEnable(self, enable):
		# Server (Cube_open) sadece CUBE_SKILL_GRID_NPC icin enable=1 gonderir.
		self.skillGridEnabled = 1 if enable else 0
		self._ApplyWindowSize(self.skillGridEnabled)
		widgets = (self.skill_grid, self.skill_grid_label, self.skill_grid_bg)
		if self.skillGridEnabled:
			for w in widgets:
				if w:
					w.Show()
		else:
			self._ClearSkillGrid()
			for w in widgets:
				if w:
					w.Hide()

	def __TryAttachSkillBook(self):
		if not self.skillGridEnabled:
			return
		if not mouseModule.mouseController.isAttached():
			return
		attachedType = mouseModule.mouseController.GetAttachedType()
		attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
		attachedInvenType = player.SlotTypeToInvenType(attachedType)
		mouseModule.mouseController.DeattachObject()
		# sadece ana envanterden surukleme kabul (dragon soul / diger pencereler haric)
		if attachedType != player.SLOT_TYPE_INVENTORY or attachedInvenType != player.INVENTORY:
			return
		if not self._IsSkillBookSlot(attachedSlotPos):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Bu alana sadece Beceri Kitabi koyabilirsin.")
			return
		if attachedSlotPos in self.skillSlotList:
			return
		if len(self.skillSlotList) >= CUBE_SKILL_GRID_MAX:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Beceri Kitabi slotlari dolu.")
			return
		self.skillSlotList.append(attachedSlotPos)
		self._RefreshSkillGrid()

	def __OnSkillSlotEmpty(self, gridPos):
		self.__TryAttachSkillBook()

	def __OnSkillSlotItem(self, gridPos):
		# elde item varsa yeni kitap eklemeyi dene; yoksa bu slottaki kitabi gridden geri al
		if mouseModule.mouseController.isAttached():
			self.__TryAttachSkillBook()
			return
		if 0 <= gridPos < len(self.skillSlotList):
			del self.skillSlotList[gridPos]
			self._RefreshSkillGrid()

	def _RefreshSkillGrid(self):
		if not self.skill_grid or not self.skillGridEnabled:
			return
		# Bayat slotlari ele: tasinmis / satilmis / silinmis / artik beceri kitabi olmayan
		valid = []
		for invSlot in self.skillSlotList:
			if self._IsSkillBookSlot(invSlot) and player.GetItemCount(invSlot) > 0:
				valid.append(invSlot)
		self.skillSlotList = valid
		slotCount = self.skill_grid.GetSlotCount()
		for i in xrange(slotCount):
			if i < len(self.skillSlotList):
				s = self.skillSlotList[i]
				self.skill_grid.SetItemSlot(i, player.GetItemIndex(s), player.GetItemCount(s))
			else:
				self.skill_grid.SetItemSlot(i, 0, 0)
		self.skill_grid.RefreshSlot()

	def _ClearSkillGrid(self):
		self.skillSlotList = []
		if self.skill_grid:
			for i in xrange(self.skill_grid.GetSlotCount()):
				self.skill_grid.SetItemSlot(i, 0, 0)
			self.skill_grid.RefreshSlot()

	def __OverInSkillSlot(self, gridPos):
		if gridPos < 0 or gridPos >= len(self.skillSlotList):
			return
		invSlot = self.skillSlotList[gridPos]
		if player.GetItemIndex(invSlot) == 0:
			return
		self.toolTip.SetInventoryItem(invSlot)

	def __OverOutSkillSlot(self):
		self.toolTip.Hide()

	def _SafeIntQty(self, text, defaultVal):
		try:
			v = int(str(text).strip())
		except (ValueError, TypeError):
			return defaultVal
		return v

	def _NormalizeResultQtyFromUI(self):
		"""Read result_qty edit, clamp, snap to recipe batch; update count_item_reward."""
		if self.selectedRecipeGlobalIndex < 0:
			return
		if not self.result_qty:
			return
		sel = self.selectedRecipeGlobalIndex
		minReward = FReturnInfo("count_reward", sel)
		if minReward <= 0:
			minReward = 1
		if CUBE_DISABLE_BULK_PRODUCTION:
			# Toplu uretim kapali: miktar daima tek partinin odul adedi.
			self.count_item_reward = minReward
			self.result_qty.SetText("%d" % minReward)
			return
		result_total = self._SafeIntQty(self.result_qty.GetText(), minReward)
		if result_total < 0:
			result_total = minReward
		if result_total < minReward:
			result_total = minReward
		elif result_total > 64000:
			result_total = 64000
		else:
			total = FReturnInfo("count_reward", sel)
			if total > 0:
				rem = result_total % total
				if rem != 0:
					result_total = result_total - rem
					if result_total < minReward:
						result_total = minReward

		self.count_item_reward = result_total
		self.result_qty.SetText("%d" % result_total)

	def AceptInputItem(self):
		if self.selectedRecipeGlobalIndex < 0:
			return
		self.result_qty.KillFocus()
		self._NormalizeResultQtyFromUI()
		self.Refresh()

	def _NotifyCubeFail(self, msg):
		chat.AppendChat(chat.CHAT_TYPE_INFO, msg)
		snd.PlaySound("sound/ui/loginfail.wav")

	def _TotalGoldCost(self, recipeIdx, batches):
		g = FReturnInfo("gold", recipeIdx)
		try:
			g = long(g)
		except (ValueError, TypeError):
			g = 0
		try:
			b = long(batches)
		except (ValueError, TypeError):
			b = 0
		if g <= 0 or b <= 0:
			return 0
		return g * b

	def AceptCube(self):
		self.CheckInputFocus()
		sel = self.selectedRecipeGlobalIndex
		if sel < 0:
			self._NotifyCubeFail(
				getattr(localeInfo, "CUBE_SELECT_ITEM_FIRST", getattr(localeInfo, "CUBE_PLEASE_SELECT", "Once uretmek istediginiz tarifi secin."))
			)
			return
		# Miktar alanindaki deger commit edilmeden Accept edilirse count_item_reward eski kalmasin.
		self._NormalizeResultQtyFromUI()
		if self.result_qty:
			self.result_qty.KillFocus()
		cr = max(1, FReturnInfo("count_reward", sel))
		if self.count_item_reward < cr:
			self.count_item_reward = cr
			if self.result_qty:
				self.result_qty.SetText("%d" % self.count_item_reward)
		count = self.count_item_reward / cr
		if CUBE_DISABLE_BULK_PRODUCTION:
			count = 1
		if count <= 0:
			self._NotifyCubeFail(
				getattr(localeInfo, "CUBE_NOT_ENOUGH_MATERIAL", "Uretim miktari gecersiz; miktar alanini kontrol edin.")
			)
			return
		for mi in xrange(1, MAX_PACKET_MATERIALS + 1):
			v = FReturnInfo("vnum_material_%d" % mi, sel)
			if v == 0:
				continue
			need = self._MaterialNeedCount(sel, mi)
			if player.GetItemCountByVnum(v) < need:
				self._NotifyCubeFail(
					getattr(localeInfo, "CUBE_NOT_ENOUGH_MATERIAL", "Yeterli malzemen yok.")
				)
				return
		needGold = self._TotalGoldCost(sel, count)
		if needGold > 0:
			getElk = getattr(player, "GetElk", None)
			if not getElk:
				getElk = getattr(player, "GetMoney", None)
			if getElk and getElk() < needGold:
				self._NotifyCubeFail(
					getattr(localeInfo, "CUBE_NOT_ENOUGH_YANG", getattr(localeInfo, "NOT_ENOUGH_MONEY", "Yeterli yang yok."))
				)
				return
		index_improve = self.slot_item_improve
		# YENI: secili Beceri Kitabi slotlarini make paketinden HEMEN once gonder (sadece grid aciksa).
		# Ayni TCP akisi -> server bu komutu (interpret_command) make'ten once isler.
		if self.skillGridEnabled:
			self._RefreshSkillGrid()
			net.SendChatPacket("/cube_skill_slots " + " ".join([str(s) for s in self.skillSlotList]))
		cube_renewal.CubeRenewalMakeItem(sel, count, index_improve)
		try:
			snd.PlaySound("sound/ui/make_soket.wav")
		except:
			pass

	def QtyAddButton(self):
		if CUBE_DISABLE_BULK_PRODUCTION:
			return
		if self.selectedRecipeGlobalIndex < 0:
			return
		if not FReturnInfo("item_reward_stackable", self.selectedRecipeGlobalIndex):
			return
		sel = self.selectedRecipeGlobalIndex
		cr = FReturnInfo("count_reward", sel)
		if cr <= 0:
			cr = 1
		batches = self._MaxCraftFromInventory(sel)
		if batches <= 0:
			self.result_qty.SetText("%d" % cr)
		else:
			cap = min(64000, cr * batches)
			self.result_qty.SetText("%d" % cap)
		self.AceptInputItem()

	def _MaxCraftFromInventory(self, recipeIdx):
		counts = []
		total_mats = 0
		for i in xrange(1, MAX_PACKET_MATERIALS + 1):
			v = FReturnInfo("vnum_material_%d" % i, recipeIdx)
			c = FReturnInfo("count_material_%d" % i, recipeIdx)
			if v == 0:
				continue
			if c <= 0:
				continue
			total_mats += 1
			adet = player.GetItemCountByVnum(v)
			if adet >= c:
				counts.append(adet / c)
		if total_mats == 0:
			return 1
		if len(counts) < total_mats:
			return 0
		return min(counts)

	def QtySubButton(self):
		if CUBE_DISABLE_BULK_PRODUCTION:
			return
		if self.selectedRecipeGlobalIndex < 0:
			return
		if not FReturnInfo("item_reward_stackable", self.selectedRecipeGlobalIndex):
			return
		sel = self.selectedRecipeGlobalIndex
		self.result_qty.SetText("%d" % FReturnInfo("count_reward", sel))
		self.AceptInputItem()

	def CheckInputFocus(self):
		if self.selectedRecipeGlobalIndex < 0:
			return
		if self.result_qty and self.result_qty.IsFocus():
			self.result_qty.KillFocus()
			self._NormalizeResultQtyFromUI()

	def BindInterfaceClass(self, interface):
		self.interface = interface

	def OnUpdate(self):
		# YENI: OnUpdate her karede calisir; burada yutulmamis bir exception pencereyi
		# "acik ama cizilmeyen + input-yutan" (donuk) durumda birakir. Tum govdeyi koru + logla.
		try:
			self._OnUpdateBody()
		except:
			self._LogCubeErr("OnUpdate")

	def _OnUpdateBody(self):
		# YENI: agir per-frame isler (grid senkronu + tam repaint) her kare degil, throttle'li calisir.
		self._updateTick += 1
		doHeavy = (self._updateTick >= CUBE_UPDATE_PAINT_EVERY)
		if doHeavy:
			self._updateTick = 0

		# item tasinir/satilir/silinir/count degisirse grid otomatik guncellenir (throttle'li)
		if doHeavy:
			self._RefreshSkillGrid()

		if self.IsShow() and self.searchEdit:
			try:
				t = self.searchEdit.GetText()
			except:
				t = ""
			if t != self._lastSearchText:
				self._lastSearchText = t
				self.firstSlotIndex = 0
				self.contentScrollbar.SetPos(0)
				self.Refresh()

			if self.searchPlaceholder:
				try:
					if self.searchEdit.IsFocus():
						self.searchPlaceholder.Hide()
					elif len(t.strip()) == 0:
						self.searchPlaceholder.Show()
					else:
						self.searchPlaceholder.Hide()
				except:
					pass

		if self.selectedRecipeGlobalIndex >= 0 and doHeavy:
			self._UpdateConstInfoCubeCount()
			self._PaintVisibleRows()

		index_improve = self.slot_item_improve
		if index_improve != -1:
			itemVNum = player.GetItemIndex(index_improve)
			itemCount = player.GetItemCount(index_improve)
			if itemVNum == self.vnum_item_improve and itemCount <= self.max_count_item_improve:
				self.slot_improve.SetItemSlot(0, itemVNum, itemCount)
			else:
				self.slot_improve.SetItemSlot(0, 0, 0)
				self.slot_item_improve = -1
		else:
			self.slot_improve.SetItemSlot(0, 0, 0)

		if self.selectedRecipeGlobalIndex >= 0:
			if FReturnInfo("percent", self.selectedRecipeGlobalIndex) >= 100 and self.slot_item_improve != -1:
				self.slot_improve.SetItemSlot(0, 0, 0)
				self.slot_item_improve = -1

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Close(self):
		# YENI: ESC her zaman pencereden cikarabilmeli; ara adim hata verse bile odak birak + Hide GARANTI.
		try:
			cube_renewal.CubeRenewalClose()
			self.slot_item_improve = -1
			if self.slot_improve:
				self.slot_improve.SetItemSlot(0, 0, 0)
			# YENI: pencere kapaninca secili beceri kitabi slotlari temizlensin
			self._ClearSkillGrid()
			self.selectedRecipeGlobalIndex = -1
			constInfo.cube_count_items = {}
			constInfo.CUBE_RENEWAL_IS_OPENED = 0
			_ClearCubeDatesCache()  # YENI: kapaninca parse cache'ini birak (bellek + sonraki acilis taze)
			self.toolTip.Hide()
		except:
			self._LogCubeErr("Close")
		# Edit satirlarinin klavye kilidini (ime capture) birak ki kapaninca input geri gelsin.
		try:
			if self.result_qty:
				self.result_qty.KillFocus()
			if self.searchEdit:
				self.searchEdit.KillFocus()
		except:
			pass
		self.Hide()
