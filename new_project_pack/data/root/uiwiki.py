# author: dracaryS
# v3.2 Update Multifunctional Wiki

# static imports
import ui, localeInfo, constInfo, WikiUI, os

# dynamics imports
import grp, app, wiki, renderTarget, item, nonplayer, skill, player, chat, dbg, net, wndMgr, sys

# if false will be textline!
USE_ITEM_COUNT_NUMBER_LINE = False

# if this true item refine showing start index in +0 than +9 will be next item if have!
SHOW_NEXT_ITEM_REFINE = False

SHOW_ITEM_LOWER_TO_BIG = True
# category load speed
AUTOLOAD_SPEED = 0.010
AUTOLOAD_MONSTER_SPEED = 0.020

IMG_DIR = "d:/ymir work/ui/game/wiki/"

PUBLIC_BTN = "d:/ymir work/ui/public/middle_button_%02d.sub"

# Wiki ekipman: +0..+9 ve satir icindeki +N / yang / ikonlar icin yatay sutun adimi (px)
WIKI_REFINE_COL_STEP = 52
# Gosterilen sutunlar en fazla +0 .. +9 (10 sutun); +10 ve uzeri listelenmez
WIKI_REFINE_MAX_PLUS = 9
WIKI_REFINE_MAX_COLS = WIKI_REFINE_MAX_PLUS + 1
WIKI_CATEGORY_HEADER_COLOR = 0xFFFFC700

def _WikiParseSelectArg(arg):
	if hasattr(WikiUI, "ParseCategorySelectArg"):
		ret = WikiUI.ParseCategorySelectArg(arg)
		if len(ret) >= 4:
			return ret
		return (ret[0], ret[1], ret[2], 0)
	parts = arg.split("#")
	categoryType = parts[0].lower() if not localeInfo.IsARABIC() else parts[0]
	itemType = int(parts[1]) if len(parts) > 1 else 0
	weaponSubType = -1
	weaponFilter = 0
	if categoryType == "equipment" and len(parts) > 2:
		try:
			weaponSubType = int(parts[2])
			weaponFilter = 1
		except:
			weaponSubType = -1
			weaponFilter = 0
	return (categoryType, itemType, weaponSubType, weaponFilter)

def _WikiBuildWeaponMatchList(weaponSubType):
	# Wiki C++: weapons per job (m_vecWeapon[0..3]), each job sorted by level in C++.
	# Merge all jobs for this subtype, then sort globally by required level (not job order).
	matchList = []
	subtypeHits = {}
	totalScanned = 0
	seenVnums = {}
	for charIdx in xrange(4):
		total = wiki.GetCategorySize(charIdx, 0)
		totalScanned += total
		for i in xrange(total):
			vnum = wiki.GetCategoryData(charIdx, 0, i)
			if not vnum:
				continue
			item.SelectItem(vnum)
			if item.GetItemType() != item.ITEM_TYPE_WEAPON:
				continue
			st = item.GetItemSubType()
			subtypeHits[st] = subtypeHits.get(st, 0) + 1
			if st != weaponSubType:
				continue
			if seenVnums.has_key(vnum):
				continue
			seenVnums[vnum] = 1
			lvl = WikiGetItemRequiredLevel(vnum)
			matchList.append((charIdx, i, lvl, vnum))
	# Low level first (wiki list: small to big)
	matchList.sort(key=lambda e: (e[2], e[3]), reverse=False)
	flat = [(e[0], e[1]) for e in matchList]
	return (flat, subtypeHits, totalScanned)

def _WikiIterCategoryLeaves():
	if hasattr(WikiUI, "IterCategoryLeafEntries"):
		for label, selectArg in WikiUI.IterCategoryLeafEntries():
			yield (label, selectArg)
		return
	cdict = WikiUI.GetCategoryDict()
	for mainKey in sorted(cdict.keys()):
		data = cdict[mainKey]
		ctype = data["type"] if data.has_key("type") else "article"
		items = data["items"] if data.has_key("items") else {}
		for sk in sorted(items.keys()):
			entry = items[sk]
			if hasattr(WikiUI, "GetCategoryItemLabel"):
				label = WikiUI.GetCategoryItemLabel(entry)
				arg = WikiUI.GetCategoryItemSelectArg(data, sk, entry)
			else:
				label = entry
				arg = "%s#%d" % (ctype, sk)
			yield (label, arg)

# Isim / seviye / +N baslik bandi (zebra govdesinden ayri)
WIKI_EQUIP_HEADER_BG = 0xff352d26
# Refine alanini tumuyle kaydir (sag / yukari = +X, -Y)
WIKI_REFINE_GRID_SHIFT_X = 16
WIKI_REFINE_GRID_SHIFT_Y = -14
# Refine satirlarinda malzeme slot ikonlari (Y asagi = arti)
WIKI_REFINE_MATERIAL_SLOT_SHIFT_Y = 3
# Ana esya ikonu tum refine satirlarinda (px)
WIKI_EQUIP_ICON_SHIFT_X = 10
# Tek malzeme satirli refine satirinda ana ikon (px yukari = negatif)
WIKI_EQUIP_ICON_1ROW_SHIFT_Y = -30
# Sonuc listesi / ekipman satiri ic genislik: sagdan daraltma (px)
WIKI_RESULT_LIST_RIGHT_SHRINK = 10
WIKI_REFINE_GRID_LEFT = 10 + 130 + WIKI_REFINE_GRID_SHIFT_X

# Programatik wiki gorunumu (wiki/slot TGA yerine)
WIKI_SLOT_PLATE = "d:/ymir work/ui/public/Slot_Base.sub"
WIKI_REFINE_YANG_ICON = "d:/ymir work/ui/game/windows/money_icon.sub"
# Yang ikonu X: ana ikon sol-ustune gore; Y: +0 sutun yang metni (WikiRefineColumnPriceY)
WIKI_EQUIP_ITEM_YANG_ICON_OFFSET_X = 87
# Y yedek / ince ayar (+/- px), gorunur sutun yoksa iy ile kullanilir
WIKI_EQUIP_ITEM_YANG_ICON_OFFSET_Y = 31
WIKI_ROW_ZEBRA_A = 0xff1a1816
WIKI_ROW_ZEBRA_B = 0xff262220
WIKI_ROW_BORDER = 0xFF4a3a2e
# Refine sutun ayirici (dikey, tam yukseklik)
WIKI_REFINE_LINE_V = 0xFF454545
# Refine satiri: sadece esya adi ve malzeme adet yazilari (+N basliklari beyaz)
WIKI_REFINE_ITEM_TEXT_COLOR = 0xFFF2E7C1
WIKI_PANEL_NEUTRAL = 0xff1e1a18
# Modern wiki: sol kategori paneli (zebra + basliklar)
WIKI_MODERN_CAT_X = 14
WIKI_MODERN_CAT_Y = 46
WIKI_MODERN_CAT_W = 128
# Modern wiki: arama satiri sol X (kategori panelinin saginda)
WIKI_SEARCH_ROW_SLOT_X = WIKI_MODERN_CAT_X + WIKI_MODERN_CAT_W + 10
# Mod butonlari (sandik/refine/item) wiki penceresinin sag disinda
WIKI_MODE_BTN_W = 92
WIKI_MODE_BTN_H = 21
WIKI_MODE_BTN_OUTSIDE_GAP = 10
WIKI_MODE_BTN_STACK_GAP = 6
# Sandik onizleme: slot boyutu / aralik; sutun X icin dinamik, satir Y sabit
WIKI_CHEST_PREVIEW_SLOT_SIZE = 32
WIKI_CHEST_PREVIEW_SLOT_GAP = 2
WIKI_CHEST_PREVIEW_GRID_ROWS = 14
WIKI_MOB_DROP_GRID_COLS = 15
WIKI_MOB_DROP_GRID_ROWS = 4
WIKI_MOB_DROP_GRID_SHIFT_X = -20
WIKI_ITEM_PREVIEW_LINE = 16
# 1 = syserr'e [WIKI_DROP] loglari; 0 = kapali
WIKI_DEBUG_MOB_DROP = 0
# 1 = syserr'e [WIKI_CAT] silah alt tipi / kategori yukleme loglari
WIKI_DEBUG_CATEGORY = 1
# 1 = syserr'e [WIKI_VIEW] mod gecisi / sonuc listesi temizleme loglari
WIKI_DEBUG_VIEW_MODE = 1
# 1 = syserr'e [WIKI_LAYOUT] satir yuksekligi / grid yerlesim / liste sirasi loglari
WIKI_DEBUG_LAYOUT = 1
# Metin/mob wiki satiri: sol onizleme + govde arka plan Y (WikiMobDropPanelRowHeight ile uyumlu)
WIKI_MOB_DROP_PANEL_PREVIEW_H = 163


def WikiDebugCategory(msg):
	if not WIKI_DEBUG_CATEGORY:
		return
	try:
		dbg.TraceError("[WIKI_CAT] %s" % msg)
	except:
		pass

def WikiDebugMobDrop(msg):
	if not WIKI_DEBUG_MOB_DROP:
		return
	try:
		dbg.TraceError("[WIKI_DROP] %s" % msg)
	except:
		pass

def WikiDebugViewMode(msg):
	if not WIKI_DEBUG_VIEW_MODE:
		return
	try:
		dbg.TraceError("[WIKI_VIEW] %s" % msg)
	except:
		pass


def WikiDebugLayout(msg):
	if not WIKI_DEBUG_LAYOUT:
		return
	try:
		dbg.TraceError("[WIKI_LAYOUT] %s" % msg)
	except:
		pass


def WikiShowGridItemTooltip(vnum):
	try:
		iface = constInfo.GetInterfaceInstance()
		if not iface or not iface.tooltipItem:
			return
		tip = iface.tooltipItem
		tip.ClearToolTip()
		if hasattr(tip, "SetItemToolTipWiki"):
			tip.SetItemToolTipWiki(int(vnum))
		else:
			tip.SetItemToolTip(int(vnum))
			tip.ShowToolTip()
	except:
		pass


def WikiHideGridItemTooltip():
	try:
		iface = constInfo.GetInterfaceInstance()
		if iface and iface.tooltipItem:
			iface.tooltipItem.ClearToolTip()
			iface.tooltipItem.HideToolTip()
	except:
		pass


def _WikiClipText(s, maxLen):
	if s is None:
		return ""
	s = str(s)
	if len(s) <= maxLen:
		return s
	m = max(0, maxLen - 3)
	return s[:m] + "..."


def WikiDropRowMatchItem(display_vnum, drop_vnum, is_refine_item):
	if not is_refine_item:
		return int(drop_vnum) == int(display_vnum)
	try:
		rm = wiki.GetRefineMaxLevel(int(drop_vnum))
		dv = int(display_vnum)
		drop = int(drop_vnum)
		return dv >= drop and dv <= drop + rm
	except:
		return int(drop_vnum) == int(display_vnum)


def WikiMobDropCountForItem(mob_vnum, display_vnum, is_refine_item):
	try:
		nz = wiki.GetMobInfoSize(mob_vnum)
	except:
		return 1
	for j in xrange(nz):
		try:
			(v, cnt) = wiki.GetMobInfoData(mob_vnum, j)
		except:
			continue
		if WikiDropRowMatchItem(display_vnum, v, is_refine_item):
			return int(cnt) if cnt else 1
	return 1


def WikiChestDropCountForItem(chest_vnum, display_vnum, is_refine_item):
	try:
		nz = wiki.GetSpecialInfoSize(chest_vnum)
	except:
		return 1
	for j in xrange(nz):
		try:
			(v, cnt) = wiki.GetSpecialInfoData(chest_vnum, j)
		except:
			continue
		if WikiDropRowMatchItem(display_vnum, v, is_refine_item):
			return int(cnt) if cnt else 1
	return 1


def WikiFormatItemPreviewLocation(mob_index):
	try:
		nm = WikiUI.GetOriginMapName(mob_index)
	except:
		nm = ""
	if isinstance(nm, list):
		if not nm:
			return "-"
		if len(nm) == 1:
			return _WikiClipText(nm[0], 44)
		return _WikiClipText(nm[0] + " (+%d)" % (len(nm) - 1), 44)
	if nm:
		return _WikiClipText(nm, 44)
	return "-"


def WikiGetResultListInnerWidth():
	try:
		par = constInfo.GetWikiInterface()
		if par:
			return max(420, par.children["resultpageListbox"].GetWidth() - 8)
	except:
		pass
	return 540


def WikiGetResultListInnerHeight():
	try:
		par = constInfo.GetWikiInterface()
		if par:
			return max(220, par.children["resultpageListbox"].GetHeight())
	except:
		pass
	return 400


def WikiMobDropPanelRowHeight():
	slot = WIKI_CHEST_PREVIEW_SLOT_SIZE
	gap = WIKI_CHEST_PREVIEW_SLOT_GAP
	gh = WIKI_MOB_DROP_GRID_ROWS * slot + (WIKI_MOB_DROP_GRID_ROWS - 1) * gap
	headerH = 34
	bodyTop = headerH + 8
	return bodyTop + max(WIKI_MOB_DROP_PANEL_PREVIEW_H, gh) + 8


def WikiGetItemRequiredLevel(vnum):
	try:
		item.SelectItem(int(vnum))
		for i in xrange(item.LIMIT_MAX_NUM):
			(limitType, limitValue) = item.GetLimit(i)
			if item.LIMIT_LEVEL == limitType:
				return int(limitValue) if limitValue else 0
	except:
		pass
	return 0


def WikiGetMonsterLevel(vnum):
	try:
		lv = nonplayer.GetMonsterLevel(int(vnum))
		return int(lv) if lv else 0
	except:
		pass
	return 0


def WikiCollectSortedDrops(ownerVnum, fromMobTable):
	entries = []
	try:
		sizeFn = wiki.GetMobInfoSize if fromMobTable else wiki.GetSpecialInfoSize
		dataFn = wiki.GetMobInfoData if fromMobTable else wiki.GetSpecialInfoData
		n = sizeFn(ownerVnum)
	except:
		n = 0
	for j in xrange(n):
		try:
			(vnum, count) = dataFn(ownerVnum, j)
		except:
			continue
		if not vnum:
			continue
		entries.append((WikiGetItemRequiredLevel(vnum), int(vnum), int(count) if count else 1))
	entries.sort(key=lambda e: (e[0], e[1]))
	return entries


def WikiMobHasDrops(mob_vnum):
	# wiki m_vecMobDrop: gercek dusen item yoksa listeleme
	if not mob_vnum:
		return False
	try:
		return len(WikiCollectSortedDrops(int(mob_vnum), True)) > 0
	except:
		return False


def WikiEquipHasRefineData(itemVnum):
	# refine tablosu ve en az bir malzeme slotu dolu degilse listeleme
	if not itemVnum:
		return False
	try:
		itemVnum = int(itemVnum)
		refineLevel = int(wiki.GetRefineMaxLevel(itemVnum))
	except:
		return False
	baseVnum = itemVnum - refineLevel
	foundStep = False
	foundMaterial = False
	for j in xrange(refineLevel + 1):
		try:
			if item.SelectItemWiki(baseVnum + j) != 1:
				continue
			argv = wiki.GetRefineItems(item.GetRefineSet())
			if not argv or argv == 0:
				continue
			foundStep = True
			for k in xrange(5):
				try:
					mv = int(argv[1 + k * 2])
				except:
					mv = 0
				if mv:
					foundMaterial = True
					break
			if foundMaterial:
				break
		except:
			continue
	return foundStep and foundMaterial


def WikiRefineRdKey(colIndex):
	if SHOW_NEXT_ITEM_REFINE or colIndex == 0:
		return colIndex
	return colIndex - 1


def WikiRefineColumnHasContent(rd):
	if not rd:
		return False
	if rd.has_key("item"):
		for v in rd["item"]:
			try:
				if int(v) > 0:
					return True
			except:
				pass
	try:
		if rd.has_key("cost") and int(rd["cost"]) > 0:
			return True
	except:
		pass
	try:
		if rd.has_key("prob") and int(rd["prob"]) > 0:
			return True
	except:
		pass
	return False


def WikiRefineMaterialRowsForStep(refineData, globalMax):
	if globalMax <= 0:
		globalMax = 1
	used = 0
	if refineData and refineData.has_key("item"):
		items = refineData["item"]
		for i in xrange(min(len(items), globalMax)):
			try:
				if int(items[i]) > 0:
					used = i + 1
			except:
				pass
	return max(used, 1)


def WikiRefineMaterialRowsForColumn(colIndex, refineData, globalMax):
	# +0 sutununda malzeme gosterilmez; ayni rdKey +1'de kalmasin diye slot cizme
	if not SHOW_NEXT_ITEM_REFINE and colIndex == 0:
		return 0
	return WikiRefineMaterialRowsForStep(refineData, globalMax)


def WikiRefineVisibleColumnCount(refineItems, refineLevel):
	cap = min(refineLevel + 1, WIKI_REFINE_MAX_COLS)
	while cap > 1:
		rdKey = WikiRefineRdKey(cap - 1)
		rd = refineItems[rdKey] if refineItems.has_key(rdKey) else {}
		if WikiRefineColumnHasContent(rd):
			break
		cap -= 1
	return cap


def WikiEquipMaxMaterialRows(refineItems, refineLevel, globalMax):
	cap = WikiRefineVisibleColumnCount(refineItems, refineLevel)
	best = 1
	for i in xrange(cap):
		rdKey = WikiRefineRdKey(i)
		rd = refineItems[rdKey] if refineItems.has_key(rdKey) else {}
		n = WikiRefineMaterialRowsForColumn(i, rd, globalMax)
		if n > best:
			best = n
	return best


def WikiGridTryPlaceRowMajor(layout, cols, rows, cursor, iw, ih):
	maxSlots = cols * rows
	while cursor < maxSlots:
		row = cursor // cols
		col = cursor % cols
		if col + iw > cols:
			cursor = (row + 1) * cols
			continue
		pos = cursor
		if layout.put(pos, iw, ih):
			return (pos, row * cols + col + iw)
		cursor += 1
	return (-1, cursor)


def WikiGridFillDropSlots(grid, gridVnums, cols, rows, entries):
	layout = WikiUI.Grid(cols, rows)
	maxSlots = cols * rows
	cursor = 0
	for (_lvl, iv, cnt) in entries:
		try:
			item.SelectItem(iv)
			(iw, ih) = item.GetItemSize()
		except:
			continue
		if iw <= 0 or ih <= 0:
			continue
		(pos, cursor) = WikiGridTryPlaceRowMajor(layout, cols, rows, cursor, iw, ih)
		if pos < 0:
			WikiDebugLayout("grid FULL vnum=%s size=%dx%d cols=%d rows=%d" % (iv, iw, ih, cols, rows))
			break
		grid.SetItemSlot(pos, iv, cnt if cnt > 1 else 0)
		row = pos // cols
		col = pos % cols
		WikiDebugLayout("grid place vnum=%s pos=%d r=%d c=%d size=%dx%d" % (iv, pos, row, col, iw, ih))
		for dy in xrange(ih):
			for dx in xrange(iw):
				idx = (row + dy) * cols + (col + dx)
				if 0 <= idx < maxSlots:
					gridVnums[idx] = iv


def WikiDropGridRowsNeeded(cols, entries):
	slotRows = WIKI_CHEST_PREVIEW_GRID_ROWS
	while slotRows < 80:
		layout = WikiUI.Grid(cols, slotRows)
		cursor = 0
		fits = True
		for (_lvl, vnum, _cnt) in entries:
			try:
				item.SelectItem(vnum)
				(iw, ih) = item.GetItemSize()
			except:
				iw, ih = 1, 1
			if iw <= 0:
				iw = 1
			if ih <= 0:
				ih = 1
			(_pos, cursor) = WikiGridTryPlaceRowMajor(layout, cols, slotRows, cursor, iw, ih)
			if _pos < 0:
				fits = False
				break
		if fits:
			return slotRows
		slotRows += 2
	return slotRows


def WikiEquipListInnerSize(refineCount):
	try:
		par = constInfo.GetWikiInterface()
		pw = 411
		if par and getattr(par, "_wikiModernLayout", 0):
			pw = max(440, par.GetWidth() - 150)
			pw = max(pw, WIKI_REFINE_MAX_COLS * WIKI_REFINE_COL_STEP)
			pw = max(WIKI_REFINE_MAX_COLS * WIKI_REFINE_COL_STEP, pw - WIKI_RESULT_LIST_RIGHT_SHRINK)
	except:
		pw = 411
	rc = refineCount if refineCount < 6 else 5
	rs = 32 + 5 + 8
	lastRowBottom = 22 + 5 + WIKI_REFINE_MATERIAL_SLOT_SHIFT_Y + (rc - 1) * rs + 32
	priceY = lastRowBottom + 8
	ih = max(priceY + 34, 72)
	return pw, ih


def WikiRefinePriceRowCount(materialRowCount, alignMaterialRows):
	priceRows = alignMaterialRows if alignMaterialRows > 0 else materialRowCount
	if priceRows <= 0:
		priceRows = 1
	return priceRows


def WikiRefineColumnPriceY(materialRowCount, alignMaterialRows):
	rs = 32 + 5 + 8
	slotYBase = 22 + 5 + WIKI_REFINE_MATERIAL_SLOT_SHIFT_Y
	rc = materialRowCount if materialRowCount > 0 else 0
	priceRows = WikiRefinePriceRowCount(rc, alignMaterialRows)
	lastRowBottom = slotYBase + (priceRows - 1) * rs + 32
	return lastRowBottom + 8


def WikiRefineColumnHeight(refine, itemVnum, materialRowCount, refineData, alignMaterialRows=0):
	priceY = WikiRefineColumnPriceY(materialRowCount, alignMaterialRows)
	return max(priceY + 34, 72)


def WikiApplySolidBg(target, width, height, color):
	target.SetSize(width, height)
	b = ui.Bar()
	b.SetParent(target)
	b.SetPosition(0, 0)
	b.SetSize(width, height)
	b.SetColor(color)
	b.AddFlag("not_pick")
	b.Show()
	target._children["wikiSolidBg"] = b
	ln = ui.Line()
	ln.SetParent(target)
	ln.SetPosition(0, max(0, height - 1))
	ln.SetSize(width, 0)
	ln.SetColor(WIKI_ROW_BORDER)
	ln.AddFlag("not_pick")
	ln.Show()
	target._children["wikiSolidBgLine"] = ln


class EncyclopediaofGame(ui.ThinBoard):
	# MANUEL layout: asagidaki "MANUEL:" yorumlari pencere/kombo/arama/sonuc listesi
	# ve EquipmentItem sutun hizalarini elle oynatmak icin isaretlendi.
	def __del__(self):
		ui.ThinBoard.__del__(self)

	def Destroy(self):
		self.__WikiDestroyRefineHeaders()
		self.__WikiDestroyModeButtons()
		if getattr(self, "children", None):
			if self.children.has_key("wikiCategoryCombo") and self.children["wikiCategoryCombo"]:
				try:
					self.children["wikiCategoryCombo"].Destroy()
				except:
					pass
				try:
					del self.children["wikiCategoryCombo"]
				except:
					pass
			for k in ("wikiTitleBg", "wikiTitleLine", "wikiTitleText", "wikiCloseBtn", "wikiBodyBg"):
				if self.children.has_key(k) and self.children[k]:
					try:
						self.children[k].Hide()
					except:
						pass
					try:
						del self.children[k]
					except:
						pass

		if self.children.has_key("listBoxCube"):
			self.children["listBoxCube"].ClearItem()
			self.children["listBoxCube"]=None
			del self.children["listBoxCube"]

		if self.children.has_key("resultpageListbox"):
			lb = self.children["resultpageListbox"]
			sb = getattr(lb, "scrollBar", None)
			if sb:
				try:
					sb.Hide()
					sb.Destroy()
				except:
					pass
				try:
					lb.scrollBar = None
				except:
					pass
			lb.RemoveAllItems()
			self.children["resultpageListbox"] = None
			del self.children["resultpageListbox"]

		self.selectArg=""
		self.currentCharacterIdx=-1
		self.AIAppendAlgoritm = None

		if len(self.children) != 0:
			ui.ThinBoard.Destroy(self)

		self.children = {}

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.SetWindowName("EncyclopediaofGame")
		self.AddFlag("movable")
		self.AddFlag("float")
		self.children = {}

		self.Destroy()

		# Default variable
		self.children["characterIndex"]=0
		self._wikiRefineHeaderTls = []
		self._wikiModernLayout = 1
		self._wikiComboArgs = []
		self._wikiEquipMatchList = []
		self._wikiItemViewMode = "refine"
		self._wikiModeBtnLastPos = None
		self.Initialize()

	def Initialize(self):
		sw = wndMgr.GetScreenWidth()
		sh = wndMgr.GetScreenHeight()
		winW = min(980, max(760, sw - 40)) - 275 + 180  # MANUEL: wiki pencere genisligi (+180)
		winH = min(720, max(520, sh - 40)) - 70  # MANUEL: wiki pencere yuksekligi (ustten kisaltma miktar)
		winW = max(480, winW)  # MANUEL: wiki minimum genislik
		winH = max(380, winH)  # MANUEL: wiki minimum yukseklik
		self.SetSize(winW, winH)  # MANUEL: wiki ana pencere boyutu (Initialize)
		self.__WikiBuildChrome()
		self.SetCenterPosition()

		self.LoadSearchInfos()
		self.LoadCategoryInfos()
		self.LoadResultPage()
		self.__ApplyWikiModernLayout()
		self.__WikiResizeChrome()
		self.__WikiSyncResultScrollBarPos()

	def __WikiBuildChrome(self):
		inset = 10  # MANUEL: chrome kenar boslugu (title/body ic ice)
		titleY = 8  # MANUEL: ust bar Y
		topBarH = 30  # MANUEL: ust bar yuksekligi
		w = max(100, self.GetWidth())
		h = max(80, self.GetHeight())

		titleBg = ui.Bar()
		titleBg.SetParent(self)
		titleBg.AddFlag("not_pick")
		titleBg.SetPosition(inset, titleY)  # MANUEL: baslik zemin konumu
		titleBg.SetSize(w - inset * 2, topBarH)  # MANUEL: baslik zemin boyutu
		titleBg.SetColor(0xff2d2018)
		titleBg.Show()
		self.children["wikiTitleBg"] = titleBg

		titleLine = ui.Line()
		titleLine.SetParent(self)
		titleLine.AddFlag("not_pick")
		titleLine.SetColor(0xFF6a4030)
		titleLine.SetPosition(inset, titleY + topBarH)  # MANUEL: baslik alt cizgi konumu
		titleLine.SetSize(w - inset * 2, 0)  # MANUEL: baslik alt cizgi genisligi
		titleLine.Show()
		self.children["wikiTitleLine"] = titleLine

		tl = ui.TextLine()
		tl.SetParent(self)
		tl.SetPosition(w / 2, titleY + 7)  # MANUEL: wiki baslik metni konumu (ortalanmis X + Y offset)
		tl.SetHorizontalAlignCenter()
		tl.SetFontName(localeInfo.UI_DEF_FONT)
		tl.SetPackedFontColor(0xFFFFE8C8)
		try:
			tl.SetText(getattr(localeInfo, "WIKI_DROP_VIEW_TITLE", localeInfo.WIKI_TITLE))
		except:
			tl.SetText(localeInfo.WIKI_TITLE)
		tl.Show()
		self.children["wikiTitleText"] = tl

		cb = ui.Button()
		cb.SetParent(self)
		cb.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		cb.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		cb.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		cb.SetPosition(w - inset - 24, titleY + 5)  # MANUEL: kapat butonu konumu
		cb.SetToolTipText(localeInfo.UI_CLOSE)
		cb.SetEvent(ui.__mem_func__(self.Close))
		cb.Show()
		self.children["wikiCloseBtn"] = cb

		bodyTop = titleY + topBarH + 5  # MANUEL: govde alani ust Y (baslik alt bosluk)
		body = ui.Bar()
		body.SetParent(self)
		body.AddFlag("not_pick")
		body.SetColor(0xff151210)
		body.SetPosition(inset, bodyTop)  # MANUEL: govde zemin konumu
		body.SetSize(w - inset * 2, max(40, h - bodyTop - inset))  # MANUEL: govde zemin boyutu (min yukseklik 40)
		body.Show()
		self.children["wikiBodyBg"] = body

	def __WikiResizeChrome(self):
		if not getattr(self, "children", None):
			return
		inset = 10  # MANUEL: chrome kenar boslugu (Resize ile ayni olmali)
		titleY = 8  # MANUEL: ust bar Y
		topBarH = 30  # MANUEL: ust bar yuksekligi
		w = max(100, self.GetWidth())
		h = max(80, self.GetHeight())
		bodyTop = titleY + topBarH + 5  # MANUEL: govde alani ust Y
		try:
			if self.children.has_key("wikiTitleBg") and self.children["wikiTitleBg"]:
				self.children["wikiTitleBg"].SetPosition(inset, titleY)  # MANUEL: baslik zemin konumu
				self.children["wikiTitleBg"].SetSize(w - inset * 2, topBarH)  # MANUEL: baslik zemin boyutu
			if self.children.has_key("wikiTitleLine") and self.children["wikiTitleLine"]:
				self.children["wikiTitleLine"].SetPosition(inset, titleY + topBarH)  # MANUEL: baslik alt cizgi
				self.children["wikiTitleLine"].SetSize(w - inset * 2, 0)
			if self.children.has_key("wikiTitleText") and self.children["wikiTitleText"]:
				self.children["wikiTitleText"].SetPosition(w / 2, titleY + 7)  # MANUEL: baslik metni
			if self.children.has_key("wikiCloseBtn") and self.children["wikiCloseBtn"]:
				self.children["wikiCloseBtn"].SetPosition(w - inset - 24, titleY + 5)  # MANUEL: kapat
			if self.children.has_key("wikiBodyBg") and self.children["wikiBodyBg"]:
				self.children["wikiBodyBg"].SetPosition(inset, bodyTop)  # MANUEL: govde zemin konumu
				self.children["wikiBodyBg"].SetSize(w - inset * 2, max(40, h - bodyTop - inset))  # MANUEL: govde boyutu
		except:
			pass
		try:
			self.__WikiLayoutCategoryPanel()
			self.__WikiLayoutSearchRow()
			self.__WikiLayoutChestPreviewButton()
			self.__WikiRaiseToolbarZOrder()
		except:
			pass

	def SetSize(self, width, height):
		ui.ThinBoard.SetSize(self, width, height)
		if getattr(self, "children", None) and self.children.has_key("wikiBodyBg") and self.children["wikiBodyBg"]:
			self.__WikiResizeChrome()
		self.__WikiSyncResultScrollBarPos()

	def __WikiSyncResultScrollBarPos(self):
		# Sonuc scrollbar listbox cocugu degil self uzerinde; Z-order ile satirlardan ustte kalir
		if not getattr(self, "children", None) or not self.children.has_key("resultpageListbox"):
			return
		lb = self.children["resultpageListbox"]
		sb = getattr(lb, "scrollBar", None)
		if not sb:
			return
		try:
			(lx, ly) = lb.GetLocalPosition()
			sb.SetPosition(lx + lb.GetWidth() - 9, ly + 1)
			sb.SetSize(8, lb.GetHeight())
			try:
				sb.SetTop()
			except:
				pass
		except:
			pass

	def LoadResultPage(self):
		resultpageListbox = WikiUI.ListBoxSpecial()
		resultpageListbox.SetParent(self)
		self.children["resultpageListbox"] = resultpageListbox

		resultpageListboxScrollbar = WikiUI.ScrollBarSpecial()
		resultpageListboxScrollbar.SetParent(self)
		resultpageListbox.SetScrollBar(resultpageListboxScrollbar)

		resultpagebtn = ui.ExpandedImageBox()
		resultpagebtn.SetParent(self)
		resultpagebtn.SetPosition(14, 90)  # MANUEL: rehber/ozel sonuc gorseli tiklanabilir alan konumu
		resultpagebtn.SetSize(1, 1)  # MANUEL: gorunmez hitbox boyutu
		resultpagebtn.Hide()
		resultpagebtn.SetEvent(ui.__mem_func__(self.LoadGuidePage), "mouse_click")
		self.children["resultpagebtn"] = resultpagebtn

	def __WikiDestroyRefineHeaders(self):
		for o in getattr(self, "_wikiRefineHeaderTls", []):
			if o:
				try:
					o.Hide()
				except:
					pass
		self._wikiRefineHeaderTls = []

	def __WikiRefineHeaderTip(self, idx):
		try:
			iface = constInfo.GetInterfaceInstance()
			if iface and iface.tooltipItem:
				iface.tooltipItem.ClearToolTip()
				tip = getattr(localeInfo, "WIKI_REFINE_HEADER_TIP", "+%d") % idx
				iface.tooltipItem.AppendTextLine(tip)
				iface.tooltipItem.ShowToolTip()
		except:
			pass

	def __WikiRefineHeaderTipOut(self):
		try:
			iface = constInfo.GetInterfaceInstance()
			if iface and iface.tooltipItem:
				iface.tooltipItem.HideToolTip()
		except:
			pass

	def __WikiBuildRefineHeaders(self, baseX, baseY):
		self.__WikiDestroyRefineHeaders()
		self._wikiRefineHeaderTls = []
		COL_STEP = getattr(self, "_wikiColStep", WIKI_REFINE_COL_STEP)
		for i in xrange(WIKI_REFINE_MAX_COLS):
			t = ui.TextLine()
			t.SetParent(self)
			t.SetPosition(baseX + i * COL_STEP + COL_STEP / 2, baseY)  # MANUEL: sutun merkezi (WIKI_REFINE_COL_STEP ile hizada)
			t.SetHorizontalAlignCenter()
			t.SetVerticalAlignCenter()
			t.SetText("+%d" % i)
			t.SetPackedFontColor(0xFFFFFFFF)
			t.SetFontName(localeInfo.UI_DEF_FONT)
			t.Show()
			try:
				t.SetShowToolTipEvent(ui.__mem_func__(self.__WikiRefineHeaderTip), i)
				t.SetHideToolTipEvent(ui.__mem_func__(self.__WikiRefineHeaderTipOut))
			except:
				pass
			self._wikiRefineHeaderTls.append(t)

	def __WikiGetCategoryPanelRight(self):
		if getattr(self, "_wikiModernLayout", 0):
			return WIKI_MODERN_CAT_X + WIKI_MODERN_CAT_W + 8
		return 13

	def __WikiGetResultListLeft(self):
		if getattr(self, "_wikiModernLayout", 0) and getattr(self, "_wikiItemViewMode", "refine") in ("chest", "itempreview"):
			return 14
		return self.__WikiGetCategoryPanelRight()

	def __WikiSyncCategoryPanelVisibility(self):
		if not getattr(self, "_wikiModernLayout", 0):
			return
		hide = getattr(self, "_wikiItemViewMode", "refine") in ("chest", "itempreview")
		for k in ("listBoxCube",):
			if not self.children.has_key(k) or not self.children[k]:
				continue
			if hide:
				self.children[k].Hide()
			else:
				self.children[k].Show()
		if not hide:
			self.__WikiLayoutCategoryPanel()

	def __WikiLayoutCategoryPanel(self):
		if not getattr(self, "_wikiModernLayout", 0):
			return
		if getattr(self, "_wikiItemViewMode", "refine") in ("chest", "itempreview"):
			return
		if not self.children.has_key("listBoxCube"):
			return
		catH = max(220, self.GetHeight() - WIKI_MODERN_CAT_Y - 14)
		lb = self.children["listBoxCube"]
		lb.Show()
		lb.SetPosition(WIKI_MODERN_CAT_X, WIKI_MODERN_CAT_Y)
		lb.SetSize(WIKI_MODERN_CAT_W, catH)
		if hasattr(lb, "SetItemWidth"):
			lb.SetItemWidth(WIKI_MODERN_CAT_W - 4)
		try:
			lb.SetTop()
		except:
			pass

	def __WikiSyncCategoryListFromArg(self, arg):
		lb = self.children.get("listBoxCube")
		if not lb:
			return
		for categoryBtn in lb.itemList:
			for childItem in categoryBtn.itemList:
				if getattr(childItem, "_wikiSelectArg", None) == arg:
					lb.selectedItem = childItem
					if not categoryBtn.IsExpanded():
						categoryBtn.Expand()
					lb.RefreshList()
					return

	def __WikiSyncComboFromArg(self, arg):
		self.__WikiSyncCategoryListFromArg(arg)
		if not getattr(self, "children", None) or not self.children.has_key("wikiCategoryCombo"):
			return
		if not getattr(self, "_wikiComboArgs", None):
			return
		try:
			if arg in self._wikiComboArgs:
				i = self._wikiComboArgs.index(arg)
				self.children["wikiCategoryCombo"].SelectItem(i)
		except:
			pass

	def __OnWikiCategoryCombo(self, index):
		if index < 0 or index >= len(getattr(self, "_wikiComboArgs", [])):
			return
		arg = self._wikiComboArgs[index]
		if arg.startswith("wiki_char#"):
			try:
				ci = int(arg.split("#")[1])
			except:
				return
			if ci < 0 or ci > 3:
				return
			self.children["characterIndex"] = ci
			sel = getattr(self, "selectArg", "")
			if sel:
				parts = sel.split("#")
				if len(parts) > 0 and parts[0].lower() == "equipment":
					self.__SelectType(sel, True, False)
			return
		self.__SelectType(arg, False, True)

	def __WikiLayoutSearchRow(self):
		W = self.GetWidth()
		if not self.children.has_key("searchSlot"):
			return
		toolbarY = 46  # MANUEL: arama satiri Y (combo ile hizada)
		slot = self.children["searchSlot"]
		modeStr = getattr(self, "_wikiItemViewMode", "refine")
		wideToolbar = modeStr in ("chest", "itempreview")
		if getattr(self, "_wikiModernLayout", 0):
			if wideToolbar:
				sx = 14
				ew = max(140, W - sx - 24)
			else:
				sx = WIKI_SEARCH_ROW_SLOT_X
				ew = max(140, W - sx - 24 - 36)
		else:
			sx = WIKI_SEARCH_ROW_SLOT_X
			ew = max(140, W - sx - 24 - 36)
		slot.SetPosition(sx, toolbarY)  # MANUEL: arama kutusu sol X
		try:
			slot.SetSize(ew + 44, 34)  # MANUEL: arama slot penceresi boyutu
		except:
			pass
		# uiscript "editline" ile ayni: EditLine zemini; ic satir daha kucuk ki dis cerceve gorunsun
		bgW = max(80, ew + 42)
		bgH = 30
		innerW = max(50, ew - 26)
		innerH = 24
		if self.children.has_key("searchFieldBgEdit") and self.children["searchFieldBgEdit"]:
			bg = self.children["searchFieldBgEdit"]
			bg.SetPosition(1, 2)
			bg.SetSize(bgW, bgH)
			try:
				bg.UpdateRect()
			except:
				pass
		if self.children.has_key("mobFieldBgEdit") and self.children["mobFieldBgEdit"]:
			mbg = self.children["mobFieldBgEdit"]
			mbg.SetPosition(1, 2)
			mbg.SetSize(bgW, bgH)
			try:
				mbg.UpdateRect()
			except:
				pass
		se = self.children["searchItemName"]
		se.SetSize(innerW, innerH)  # MANUEL: item adi EditLine (zemin icine oturtulmus)
		se.SetPosition(5, 6)  # MANUEL: zemin cercevesi icinde offset
		if self.children.has_key("searchClearBtn"):
			self.children["searchClearBtn"].SetPosition(ew - 20, 5)  # MANUEL: item arama temizle (X)
		if self.children.has_key("mobSlot") and self.children["mobSlot"]:
			self.children["mobSlot"].SetPosition(sx, toolbarY)  # MANUEL: mob arama kutusu (item ile ayni X)
			try:
				self.children["mobSlot"].SetSize(ew + 44, 34)
			except:
				pass
			sm = self.children["searchMobName"]
			sm.SetSize(innerW, innerH)
			sm.SetPosition(5, 6)
			if self.children.has_key("searchClearBtnMob"):
				self.children["searchClearBtnMob"].SetPosition(ew - 20, 5)

	def __WikiRaiseToolbarZOrder(self):
		# Sonuc listesi ve govde ustunde kalsin: kombo + arama cubugu
		if not getattr(self, "_wikiModernLayout", 0):
			return
		try:
			for k in ("searchSlot", "mobSlot", "listBoxCube", "wikiChestPreviewBtn", "wikiRefineViewBtn", "wikiItemPreviewBtn"):
				if self.children.has_key(k) and self.children[k]:
					self.children[k].SetTop()
		except:
			pass

	def __WikiSetModernSearchMode(self, argList):
		if not getattr(self, "_wikiModernLayout", 0):
			return
		if not self.children.has_key("searchSlot") or not self.children.has_key("mobSlot"):
			return
		categoryType = ""
		if len(argList) > 0:
			categoryType = argList[0].lower() if not localeInfo.IsARABIC() else argList[0]
		useMob = categoryType in ("monster", "bosses", "metinstone")
		if useMob:
			self.children["searchSlot"].Hide()
			self.children["mobSlot"].Show()
		else:
			self.children["mobSlot"].Hide()
			self.children["searchSlot"].Show()
		for bk in ("wikiChestPreviewBtn", "wikiRefineViewBtn", "wikiItemPreviewBtn"):
			if not self.children.has_key(bk):
				continue
			if useMob:
				self.children[bk].Hide()
			else:
				self.children[bk].Show()
		if self.children.has_key("wikiChestPreviewBtn"):
			self.__WikiLayoutChestPreviewButton()
		self.__WikiSyncCategoryPanelVisibility()
		self.__WikiLayoutSearchRow()
		self.__WikiRaiseToolbarZOrder()

	def __ApplyWikiModernLayout(self):
		for key in ("categoryText", "historyBack", "historyNext"):
			if self.children.has_key(key):
				self.children[key].Hide()
		if self.children.has_key("wikiCategoryCombo"):
			self.children["wikiCategoryCombo"].Hide()
		self._wikiComboArgs = []
		self.__WikiLayoutCategoryPanel()

		try:
			chestLbl = getattr(localeInfo, "WIKI_CHEST_PREVIEW_BTN", "Sandik")
		except:
			chestLbl = "Sandik"
		try:
			refineLbl = getattr(localeInfo, "WIKI_REFINE_VIEW_BTN", "Refine")
		except:
			refineLbl = "Refine"
		try:
			itemLbl = getattr(localeInfo, "WIKI_ITEM_PREVIEW_BTN", "Item")
		except:
			itemLbl = "Item"

		self.children["wikiChestPreviewBtn"] = self.__WikiCreateModeButton(
			chestLbl, self.__WikiOpenChestPreview)
		self.children["wikiRefineViewBtn"] = self.__WikiCreateModeButton(
			refineLbl, self.__WikiSetRefineItemView)
		self.children["wikiItemPreviewBtn"] = self.__WikiCreateModeButton(
			itemLbl, self.__WikiOpenItemPreview)

		self.__WikiLayoutSearchRow()
		self.__WikiLayoutChestPreviewButton()
		self.__WikiRaiseToolbarZOrder()

		if self.children.has_key("resultpagebtn"):
			self.children["resultpagebtn"].Hide()

	def LoadGuidePage(self, emptyArg = ""):
		firstArg = "equipment#0#0"
		for _label, selectArg in _WikiIterCategoryLeaves():
			firstArg = selectArg
			break
		self.__SelectType(firstArg, False, False)

	def LoadBlock(self):
		pass

	def LoadSearchInfos(self):
		self.children["selectedMob"] = 0
		self.children["selectedItem"] = 0
		self._wikiLiveSearchItemVnum = None
		self._wikiLiveSearchMobVnum = None

		searchSlot = ui.Window()
		searchSlot.SetParent(self)
		self.children["searchSlot"] = searchSlot

		searchFieldBgEdit = ui.EditLine()
		searchFieldBgEdit.SetParent(searchSlot)
		searchFieldBgEdit.SetPosition(1, 2)
		searchFieldBgEdit.SetSize(160, 30)
		searchFieldBgEdit.AddFlag("not_pick")
		searchFieldBgEdit.SetMax(1)
		searchFieldBgEdit.SetText("")
		searchFieldBgEdit.SetOutline()
		searchFieldBgEdit.Show()
		self.children["searchFieldBgEdit"] = searchFieldBgEdit

		searchItemName = WikiUI.CreateWindow(ui.EditLine(), searchSlot, (2, 5), "", "", (120, 26))  # MANUEL: item adi EditLine (pos + boyut)
		try:
			searchItemName.SetInfoMessage(getattr(localeInfo, "WIKI_ITEM_NAME_PLACEHOLDER", localeInfo.WIKI_ITEM_NAME))
		except:
			searchItemName.SetInfoMessage(localeInfo.WIKI_ITEM_NAME)
		searchItemName.SetMax(30)
		searchItemName.isNeedEmpty = True
		searchItemName.OnPressEscapeKey = ui.__mem_func__(self.Close)
		searchItemName.SetOutline()
		searchItemName.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateItem)
		searchItemName.SetReturnEvent(ui.__mem_func__(self.__WikiSearchItemReturn))
		self.children["searchItemName"] = searchItemName

		searchClearBtn = WikiUI.CreateWindow(ui.Button(), searchSlot, (100, 5))  # MANUEL: item arama temizle (X)
		searchClearBtn.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		searchClearBtn.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		searchClearBtn.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		searchClearBtn.SAFE_SetEvent(self.ClearEditlineItem)
		searchClearBtn.Hide()
		self.children["searchClearBtn"] = searchClearBtn

		mobSlot = ui.Window()
		mobSlot.SetParent(self)
		self.children["mobSlot"] = mobSlot

		mobFieldBgEdit = ui.EditLine()
		mobFieldBgEdit.SetParent(mobSlot)
		mobFieldBgEdit.SetPosition(1, 2)
		mobFieldBgEdit.SetSize(160, 30)
		mobFieldBgEdit.AddFlag("not_pick")
		mobFieldBgEdit.SetMax(1)
		mobFieldBgEdit.SetText("")
		mobFieldBgEdit.SetOutline()
		mobFieldBgEdit.Show()
		self.children["mobFieldBgEdit"] = mobFieldBgEdit

		searchMobName = WikiUI.CreateWindow(ui.EditLine(), mobSlot, (2, 5), "", "", (120, 26))  # MANUEL: mob adi EditLine
		searchMobName.SetInfoMessage(localeInfo.WIKI_MOB_NAME)
		searchMobName.isNeedEmpty = True
		searchMobName.SetMax(30)
		searchMobName.SetOutline()
		searchMobName.OnPressEscapeKey = ui.__mem_func__(self.Close)
		searchMobName.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdateMob)
		searchMobName.SetReturnEvent(ui.__mem_func__(self.__WikiSearchMobReturn))
		self.children["searchMobName"] = searchMobName

		searchClearBtnMob = WikiUI.CreateWindow(ui.Button(), mobSlot, (100, 5))  # MANUEL: mob arama temizle (X)
		searchClearBtnMob.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		searchClearBtnMob.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		searchClearBtnMob.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		searchClearBtnMob.SAFE_SetEvent(self.ClearEditlineMob)
		searchClearBtnMob.Hide()
		self.children["searchClearBtnMob"] = searchClearBtnMob

		searchSlot.Show()
		mobSlot.Hide()
	
	def LoadCategoryInfos(self):
		self.children["categoryText"] = WikiUI.CreateWindow(ui.TextLine(), self, (13, 89), localeInfo.WIKI_CATEGORY)  # MANUEL: sol kategori baslik (gizli modda)

		listBoxCube = WikiUI.CreateWindow(WikiUI.CategoryList(), self, (13, 105), "", "", (109, 335))  # MANUEL: sol kategori liste konum + boyut
		self.children["listBoxCube"] = listBoxCube

		self.children["historySearch"] = []
		self.children["currentIndex"] = 0

		historyBack = WikiUI.CreateWindow(ui.Button(), self, (13,105+345))  # MANUEL: gecmis geri butonu konumu
		historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
		historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_normal.tga")
		historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_normal.tga")
		historyBack.SAFE_SetEvent(self.ClickBackHistory)
		self.children["historyBack"] = historyBack

		historyNext = WikiUI.CreateWindow(ui.Button(), self, (13+historyBack.GetWidth()+2,105+345))  # MANUEL: gecmis ileri (geri butonuna gore +2)
		historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		historyNext.SAFE_SetEvent(self.ClickNextHistory)
		self.children["historyNext"] = historyNext

		categoryDict = WikiUI.GetCategoryDict()
		listBoxCubeItems = []
		for key, data in categoryDict.iteritems():
			newDict = {}
			try:
				headerItem = WikiUI.CreateCategoryItem(
					data["name"] if data.has_key("name") else "Noname",
					None,
					0,
					WIKI_CATEGORY_HEADER_COLOR,
					True,
				)
			except TypeError:
				headerItem = WikiUI.CreateCategoryItem(
					data["name"] if data.has_key("name") else "Noname",
					None,
				)
				try:
					headerItem.children["textLine"].SetPackedFontColor(WIKI_CATEGORY_HEADER_COLOR)
				except:
					pass
				headerItem.headerOnly = True
				headerItem.OnMouseLeftButtonDown = lambda: None
				try:
					headerItem.AddFlag("not_pick")
				except:
					pass
			if not headerItem.IsExpanded():
				headerItem.Expand()
			newDict["item"] = headerItem
			newDict["children"] = []
			itemDict = data["items"] if data.has_key("items") else {}
			for categoryIdx, categoryEntry in itemDict.iteritems():
				subDict = {}
				if hasattr(WikiUI, "GetCategoryItemSelectArg"):
					selectArg = WikiUI.GetCategoryItemSelectArg(data, categoryIdx, categoryEntry)
					subLabel = WikiUI.GetCategoryItemLabel(categoryEntry)
				else:
					subLabel = categoryEntry
					selectArg = "%s#%d" % (
						data["type"] if data.has_key("type") else "article",
						categoryIdx,
					)
				subItem = WikiUI.CreateCategorySubItem(
					subLabel,
					lambda arg=selectArg: self.__SelectType(arg),
				)
				try:
					subItem.children["textLine"].SetPackedFontColor(0xFFFFFFFF)
				except:
					pass
				subItem._wikiSelectArg = selectArg
				subDict["item"] = subItem
				newDict["children"].append(subDict)
			listBoxCubeItems.append(newDict)
		listBoxCube = self.children["listBoxCube"]
		listBoxCube.AppendItemList(listBoxCubeItems)
		if hasattr(listBoxCube, "ExpandAllCategories"):
			listBoxCube.ExpandAllCategories()

	def SetHistoryButtons(self):
		historyBack = self.children["historyBack"]
		historyNext = self.children["historyNext"]

		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]

		if len(historySearch) == 0:
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			return

		if currentIndex > 0:
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_hover.tga")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_down.tga")
		else:
			historyBack.SetUpVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetOverVisual(IMG_DIR+"btn_arrow_left_normal.tga")
			historyBack.SetDownVisual(IMG_DIR+"btn_arrow_left_normal.tga")

		if currentIndex+1 >= len(historySearch):
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_normal.tga")
		else:
			historyNext.SetUpVisual(IMG_DIR+"btn_arrow_right_normal.tga")
			historyNext.SetOverVisual(IMG_DIR+"btn_arrow_right_hover.tga")
			historyNext.SetDownVisual(IMG_DIR+"btn_arrow_right_down.tga")

	def RunHistoryArgument(self, argument):
		if argument.find("NEW") != -1:
			argumentList = argument.split("#")
			self.ShowItemInfo(int(argumentList[1]), int(argumentList[2]), False)
		else:
			self.__SelectType(argument, False, False)

	def ClickBackHistory(self):
		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]
		if currentIndex-1 < 0:
			return
		currentIndex-=1
		self.children["currentIndex"]=currentIndex
		self.RunHistoryArgument(historySearch[currentIndex])
		self.SetHistoryButtons()

	def ClickNextHistory(self):
		currentIndex = self.children["currentIndex"]
		historySearch = self.children["historySearch"]
		if currentIndex+1 >= len(historySearch):
			return
		currentIndex+=1
		self.children["currentIndex"]=currentIndex
		self.RunHistoryArgument(historySearch[currentIndex])
		self.SetHistoryButtons()

	def get_length(self, x):
		return len(x[0])

	def UpdateItemsList(self):
		input_text_real = self.children["searchItemName"].GetText()
		input_len = len(input_text_real)
		if input_len == 0:
			self.ClearEditlineItem()
			return False
		if localeInfo.IsARABIC():
			input_text = input_text_real
		else:
			input_text = input_text_real.lower()
		self.children["searchClearBtn"].Show()
		items_list = item.GetItemsByName(str(input_text))
		itemList = []
		namesList = []
		chestOnly = getattr(self, "_wikiItemViewMode", "refine") == "chest"
		for i, itemVnum in enumerate(items_list, start=1):
			(realVnum, isRefineItem) = WikiUI.getRealVnum(itemVnum)
			if isRefineItem:
				realVnum += wiki.GetRefineMaxLevel(realVnum)
				if itemVnum != realVnum:
					continue
				if getattr(self, "_wikiItemViewMode", "refine") == "refine" and not WikiEquipHasRefineData(realVnum):
					continue
			item.SelectItem(itemVnum)
			if chestOnly and item.GetItemType() != item.ITEM_TYPE_GIFTBOX:
				continue
			itemName = item.GetItemName() if localeInfo.IsARABIC() else item.GetItemName().lower()
			if itemName.find("+") != -1:
				itemName = itemName[:itemName.find("+")]
			tempName = list(itemName)
			for i in xrange(input_len):
				tempName[i]=list(input_text_real)[i]
			itemName = ""
			for x in xrange(len(tempName)):
				itemName+=tempName[x]
			if itemName in namesList:
				continue
			namesList.append(itemName)
			itemList.append([itemName, realVnum])
		if len(itemList) > 0:
			if len(itemList) > 1:
				itemList = sorted(itemList, key=self.get_length, reverse=False)
			self.children["selectedItem"] = itemList[0][1]
		else:
			self.children["selectedItem"] = 0
		self.children["searchItemName"].SetInfoMessage("")
		return True

	def __OnValueUpdateItem(self):
		ui.EditLine.OnIMEUpdate(self.children["searchItemName"])
		mode = getattr(self, "_wikiItemViewMode", "refine")
		if not self.UpdateItemsList():
			self.ClearEditlineItem()
			return
		if self.children["selectedItem"] != 0:
			v = self.children["selectedItem"]
			if v != getattr(self, "_wikiLiveSearchItemVnum", None):
				self._wikiLiveSearchItemVnum = v
				WikiDebugViewMode(
					"OnValueUpdateItem StartSearchItem v=%s mode=%s list=%s"
					% (v, mode, self.__WikiDbgListItems())
				)
				self.StartSearchItem(False)

	def __WikiSearchItemReturn(self):
		self.StartSearchItem(True)

	def ClearEditlineItem(self):
		self.children["selectedItem"]=0
		self._wikiLiveSearchItemVnum = None
		self.children["searchItemName"].SetText("")
		try:
			self.children["searchItemName"].SetInfoMessage(getattr(localeInfo, "WIKI_ITEM_NAME_PLACEHOLDER", localeInfo.WIKI_ITEM_NAME))
		except:
			self.children["searchItemName"].SetInfoMessage(localeInfo.WIKI_ITEM_NAME)
		self.children["searchClearBtn"].Hide()

	def StartSearchItem(self, addToHistory=True):
		if self.children["selectedItem"] != 0:
			self.ShowItemInfo(self.children["selectedItem"], 0, addToHistory)

	def UpdateMobsList(self):
		input_text_real = self.children["searchMobName"].GetText()
		input_len = len(input_text_real)
		if input_len == 0:
			self.ClearEditlineMob()
			return False
		input_text = input_text_real if localeInfo.IsARABIC() else input_text_real.lower()
		self.children["searchClearBtnMob"].Show()
		mobs_list = nonplayer.GetMobsByName(str(input_text))
		mobList = []
		namesList = []
		for i, mobVnum in enumerate(mobs_list, start=1):
			if not WikiMobHasDrops(mobVnum):
				continue
			if localeInfo.IsARABIC():
				mob_name = nonplayer.GetMonsterName(mobVnum)
			else:
				mob_name = nonplayer.GetMonsterName(mobVnum).lower()
			tempName = list(mob_name)
			for i in xrange(input_len):
				tempName[i]=list(input_text_real)[i]
			mob_name = ""
			for x in xrange(len(tempName)):
				mob_name+=tempName[x]
			if mob_name in namesList:
				continue
			namesList.append(mob_name)
			mobList.append([mob_name, mobVnum])
		if len(mobList) > 0:
			if len(mobList) > 1:
				mobList = sorted(mobList, key=self.get_length,reverse=False)
			self.children["selectedMob"] = mobList[0][1]
		else:
			self.children["selectedMob"] = 0
		self.children["searchMobName"].SetInfoMessage("")
		return True

	def __OnValueUpdateMob(self):
		ui.EditLine.OnIMEUpdate(self.children["searchMobName"])
		if not self.UpdateMobsList():
			self.ClearEditlineMob()
			return
		if self.children["selectedMob"] != 0:
			v = self.children["selectedMob"]
			if v != getattr(self, "_wikiLiveSearchMobVnum", None):
				self._wikiLiveSearchMobVnum = v
				self.StartSearchMob(False)

	def __WikiSearchMobReturn(self):
		self.StartSearchMob(True)

	def ClearEditlineMob(self):
		self.children["selectedMob"]=0
		self._wikiLiveSearchMobVnum = None
		self.children["searchMobName"].SetText("")
		self.children["searchMobName"].SetInfoMessage(localeInfo.WIKI_MOB_NAME)
		self.children["searchClearBtnMob"].Hide()

	def StartSearchMob(self, addToHistory=True):
		if self.children["selectedMob"] != 0:
			self.ShowItemInfo(self.children["selectedMob"], 1, addToHistory)

	def LoadData(self, arg):
		self.__SelectType(arg)

	def SetCharacterImagesStatus(self, showStatus):
		pass

	def ClearResultListbox(self, argList, isSingleItem = False):
		self.AIAppendAlgoritm = None
		self.__WikiDestroyRefineHeaders()

		resultpageListbox = self.children["resultpageListbox"]
		resultpageListbox.RemoveAllItems()
		resultpageListbox.Render(0)
		resultpageListbox.Show()

		if len(argList) == 0:
			return

		imageFile = WikiUI.GetResultPageImage(argList)
		isArt = WikiUI.IsArticleCategory(argList)
		isEquipmentPage = True if WikiUI.IsCategory(argList[0], "equipment") and isSingleItem == False else False
		m = getattr(self, "_wikiModernLayout", 0)

		if m:
			if isArt:
				if imageFile:
					self.children["resultpagebtn"].LoadImage(imageFile)
					self.children["resultpagebtn"].Show()
			else:
				if self.children.has_key("resultpagebtn"):
					self.children["resultpagebtn"].Hide()
		else:
			if imageFile:
				self.children["resultpagebtn"].LoadImage(imageFile)
				self.children["resultpagebtn"].Show()

		self.SetCharacterImagesStatus(isEquipmentPage)

		if m:
			listLeft = self.__WikiGetResultListLeft()
			rw = max(320, self.GetWidth() - listLeft - 16 - WIKI_RESULT_LIST_RIGHT_SHRINK)
			ly = 88 if isEquipmentPage else 90  # MANUEL: sonuc listesi ust Y (+N sadece satir icinde step_refine)
			rh = max(200, self.GetHeight() - ly - 16)  # MANUEL: sonuc listesi yuksekligi (alt pay 16)
			resultpageListbox.SetPosition(listLeft, ly)  # MANUEL: sonuc listesi (kategori panelinin saginda)
			resultpageListbox.SetSize(rw, rh)
			if isEquipmentPage and not isSingleItem:
				self._wikiColStep = WIKI_REFINE_COL_STEP  # MANUEL: sutun adimi (Listbox / RefineItem ile)
		else:
			resultpageListbox.SetPosition(152, 162 if isEquipmentPage else 105)  # MANUEL: klasik layout sonuc listesi konumu
			resultpageListbox.SetSize(555, 297 if isEquipmentPage else 375 if isArt else 360)  # MANUEL: klasik layout liste boyutu

		resultpageListboxScrollbar = self.children["resultpageListbox"].scrollBar
		if resultpageListboxScrollbar:
			self.__WikiSyncResultScrollBarPos()
			resultpageListboxScrollbar.Show()  # RemoveAllItems sonrasi tekrar gorunur olsun
			try:
				resultpageListboxScrollbar.SetTop()
			except:
				pass

	def __SelectType(self, arg, isCharacterBtn = False, isHistory = True):
		#try:
		#if not isCharacterBtn and self.selectArg == arg:
		#	return
		self.selectArg = arg
		self.currentCharacterIdx = self.children["characterIndex"]
		self._wikiItemViewMode = "refine"

		if isHistory:
			self.children["historySearch"].append(arg)
			self.children["currentIndex"] = len(self.children["historySearch"])-1
			self.SetHistoryButtons()
		
		argList = arg.split("#")
		self.__WikiSetModernSearchMode(argList)
		self.ClearResultListbox(argList)
		
		if WikiUI.IsArticleCategory(argList):
			resultpageListbox = self.children["resultpageListbox"]
			event_item = ArticleGUI(argList[1]+"#"+argList[2] if len(argList) == 3 else int(argList[1]))
			resultpageListbox.AppendItem(event_item)
			event_item.LoadItemInfos()
			if resultpageListbox.scrollBar:
				resultpageListbox.scrollBar.Hide()
		
		else:
			AIAppendAlgoritm = WikiUI.AutoLoad()
			(categoryType, itemType, weaponSubType, weaponFilter) = _WikiParseSelectArg(arg)
			loadSpeed = AUTOLOAD_SPEED
			maxSize = -1
			self._wikiEquipMatchList = []
		
			if categoryType == "equipment":
				charIdx = self.children["characterIndex"]
				AIAppendAlgoritm.SetFlag("characterIndex", charIdx)
				AIAppendAlgoritm.SetFlag("weaponSubType", weaponSubType)
				AIAppendAlgoritm.SetFlag("weaponFilter", weaponFilter)
				if weaponFilter and itemType == 0:
					matchList, subtypeHits, total = _WikiBuildWeaponMatchList(weaponSubType)
					self._wikiEquipMatchList = matchList
					maxSize = len(matchList)
					WikiDebugCategory(
						"select=%s uiChar=%d sub=%d scanned=%d match=%d dist=%s"
						% (arg, charIdx, weaponSubType, total, len(matchList), str(subtypeHits))
					)
					AIAppendAlgoritm.SetFlag("weaponMatchMode", 1)
				else:
					maxSize = wiki.GetCategorySize(charIdx, itemType)
					AIAppendAlgoritm.SetFlag("weaponMatchMode", 0)
			else:
				_methodFunc = {
					"costume": wiki.GetCostumeSize,
					"chests": wiki.GetChestSize,
					"bosses": wiki.GetBossSize,
					"monster": wiki.GetMonsterSize,
					"metinstone": wiki.GetStoneSize,
				}
				maxSize = _methodFunc[categoryType](itemType)
				if categoryType == "monster":
					loadSpeed = AUTOLOAD_MONSTER_SPEED
		
			if maxSize <= 0:
				return
		
			AIAppendAlgoritm.SetFlag("maxSize", maxSize-1)
			AIAppendAlgoritm.SetFlag("loadTime", loadSpeed)
			AIAppendAlgoritm.SetFlag("loadType",argList[0])
			AIAppendAlgoritm.SetFlag("itemType",itemType)
			self.AIAppendAlgoritm = AIAppendAlgoritm
		self.__WikiSyncComboFromArg(self.selectArg)
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in select type func ai method.")

	def GetHyperlinkData(self):
		hyperlink = ""
		historyLen = len(self.children["historySearch"])
		if historyLen:
			currendCommand = self.children["historySearch"][ historyLen - 1]
			hyperlink = "|cffffc700|Hwiki:"+currendCommand+"|h[Wiki-{}: {}]|h|r"
			currendCommandList = currendCommand.split("#")
			if currendCommand.find("NEW") != -1:
				selectedVnum = int(currendCommandList[1])
				argumentIndex = int(currendCommandList[2])
				if argumentIndex == 0:
					import item
					item.SelectItem(selectedVnum)
					hyperlink = hyperlink.format("Item", item.GetItemName())
				elif argumentIndex == 1:
					hyperlink = hyperlink.format("Monster", nonplayer.GetMonsterName(selectedVnum))
			else:
				if hasattr(WikiUI, "FindCategoryBySelectArg"):
					groupName, leafName = WikiUI.FindCategoryBySelectArg(currendCommand)
					if groupName and leafName:
						hyperlink = hyperlink.format(groupName, leafName)
				else:
					for key, data in WikiUI.GetCategoryDict().iteritems():
						if data["type"] == currendCommandList[0]:
							if data["items"].has_key(int(currendCommandList[1])):
								hyperlink = hyperlink.format(
									data["name"],
									data["items"][int(currendCommandList[1])],
								)
								break
			return hyperlink

	def ShowItemInfo(self, selectedVnum, argumentIndex, isHistory = True):
		if self.children.has_key("listBoxCube") and self.children["listBoxCube"]:
			self.children["listBoxCube"].Reset()
		#try:
		if isHistory:
			self.children["historySearch"].append("NEW#{}#{}".format(selectedVnum, argumentIndex))
			self.children["currentIndex"] = len(self.children["historySearch"])-1
			self.SetHistoryButtons()

		resultpageListbox = self.children["resultpageListbox"]

		if argumentIndex == 0:
			self.ClearResultListbox("equipment#0".split("#"), True)
			mode = getattr(self, "_wikiItemViewMode", "refine")
			WikiDebugViewMode(
				"ShowItemInfo v=%s mode=%s arg=%s list_cleared"
				% (selectedVnum, mode, argumentIndex)
			)
			if mode == "chest":
				innerW = self.__WikiGetResultListInnerWidth()
				if not selectedVnum:
					resultpageListbox.AppendItem(WikiInPanelChestDropView(0, innerW, True))
				else:
					(sv, isRefineItem) = WikiUI.getRealVnum(selectedVnum)
					if isRefineItem:
						sv += wiki.GetRefineMaxLevel(sv)
					resultpageListbox.AppendItem(WikiInPanelChestDropView(sv, innerW, True))
				resultpageListbox.CalculateScroll()
				resultpageListbox.Render(0)
				try:
					self.__WikiSyncCategoryPanelVisibility()
					self.__WikiLayoutSearchRow()
					self.__WikiLayoutChestPreviewButton()
					self.__WikiRaiseToolbarZOrder()
				except:
					pass
				WikiDebugViewMode("ShowItemInfo -> WikiInPanelChestDropView list=%s" % self.__WikiDbgListItems())
				return

			if mode == "itempreview":
				innerW = self.__WikiGetResultListInnerWidth()
				if not selectedVnum:
					resultpageListbox.AppendItem(WikiInPanelItemDropView(0, 0, False, innerW, True))
				else:
					(baseV, isRef) = WikiUI.getRealVnum(selectedVnum)
					dispV = baseV
					if isRef:
						dispV = baseV + wiki.GetRefineMaxLevel(baseV)
					resultpageListbox.AppendItem(WikiInPanelItemDropView(dispV, baseV, isRef, innerW, True))
				resultpageListbox.CalculateScroll()
				resultpageListbox.Render(0)
				try:
					self.__WikiSyncCategoryPanelVisibility()
					self.__WikiLayoutSearchRow()
					self.__WikiLayoutChestPreviewButton()
					self.__WikiRaiseToolbarZOrder()
				except:
					pass
				return

			(selectedVnum, isRefineItem) = WikiUI.getRealVnum(selectedVnum)
			if isRefineItem:
				selectedVnum += wiki.GetRefineMaxLevel(selectedVnum)# add max refine on itemvnum. example: 10 + 9
				if WikiEquipHasRefineData(selectedVnum):
					resultpageListbox.AppendItem(EquipmentItem(99, selectedVnum, True))

			item.SelectItem(selectedVnum)
			if item.GetItemType() == item.ITEM_TYPE_GIFTBOX:
				innerW = self.__WikiGetResultListInnerWidth()
				try:
					innerH = max(220, resultpageListbox.GetHeight())
				except:
					innerH = 400
				resultpageListbox.AppendItem(WikiMobDropPanel(selectedVnum, innerW, innerH, False, True))
				resultpageListbox.AppendItem(MonsterStatics(selectedVnum, 3, True))
			else:
				resultpageListbox.AppendItem(MonsterItemSpecial(selectedVnum, 1, True))
			resultpageListbox.CalculateScroll()
			resultpageListbox.Render(0)

		elif argumentIndex == 1:
			WikiDebugMobDrop("ShowItemInfo argIdx=1 mob=%s -> WikiMobDropPanel" % selectedVnum)
			self.ClearResultListbox("monster#0".split("#"), True)
			innerW = self.__WikiGetResultListInnerWidth()
			try:
				innerH = max(220, resultpageListbox.GetHeight())
			except:
				innerH = 400
			resultpageListbox.AppendItem(WikiMobDropPanel(selectedVnum, innerW, innerH, True, True))
			resultpageListbox.AppendItem(MonsterStatics(selectedVnum, 0, True))
			resultpageListbox.CalculateScroll()
			resultpageListbox.Render(0)

		elif argumentIndex == 3:
			self.__SelectType(selectedVnum)
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in show item info.")

	def OnUpdate(self):
		self.__WikiSyncModeButtonFollow()
		self.CheckLoadProcess()

	def CheckLoadProcess(self):
		#try:
		__ai = self.AIAppendAlgoritm
		if __ai != None:
			if __ai.GetFlag("nexTime") > app.GetTime():
				return
			__ai.SetFlag("nexTime", app.GetTime()+__ai.GetFlag("loadTime"))
			(loadType, listIndex) = (__ai.GetFlag("loadType"), __ai.GetFlag("maxSize"))
			if WikiUI.IsCategory(loadType, "equipment"):
				if listIndex < 0:
					self.AIAppendAlgoritm = None
					self.__WikiFinalizeResultList(loadType)
					return
				charIdx = __ai.GetFlag("characterIndex")
				itemType = __ai.GetFlag("itemType")
				if __ai.GetFlag("weaponMatchMode"):
					matchList = getattr(self, "_wikiEquipMatchList", [])
					if listIndex >= len(matchList):
						self.__WikiAutoloadStepBack(__ai, listIndex, loadType)
						return
					entry = matchList[listIndex]
					if type(entry) == type(()):
						(realCharIdx, realIndex) = entry
					else:
						realCharIdx, realIndex = charIdx, entry
					itemVnum = wiki.GetCategoryData(realCharIdx, itemType, realIndex)
				else:
					itemVnum = wiki.GetCategoryData(charIdx, itemType, listIndex)
				sortIndex = WikiGetItemRequiredLevel(itemVnum)
				if not itemVnum:
					WikiDebugLayout("skip equip wikiIdx=%s (vnum=0)" % listIndex)
					self.__WikiAutoloadStepBack(__ai, listIndex, loadType)
					return
				if not WikiEquipHasRefineData(itemVnum):
					WikiDebugLayout("skip equip wikiIdx=%s vnum=%s (no refine mats)" % (listIndex, itemVnum))
					self.__WikiAutoloadStepBack(__ai, listIndex, loadType)
					return
				lb = self.children["resultpageListbox"]
				displayIdx = len(lb.itemList)
				equipItemPointer = EquipmentItem(displayIdx, itemVnum, True)
				equipItemPointer.sortIndex = sortIndex
				lb.AppendItem(equipItemPointer, False)
				self.__WikiPlaceListItemAtBottom(equipItemPointer)
				WikiDebugLayout(
					"append equip wikiIdx=%s disp=%s sort=%s vnum=%s y=%s h=%s"
					% (listIndex, displayIdx, sortIndex, itemVnum, equipItemPointer.exPos[1], equipItemPointer.GetHeight())
				)
			elif WikiUI.IsCategory(loadType, "costume"):
				createNewWindow = True
				ListBoxItems = self.children["resultpageListbox"].itemList
				if len(ListBoxItems) > 0:
					lastItem = ListBoxItems[len(ListBoxItems)-1]
					if lastItem.CanAddNewItem():
						lastItem.LoadItemInfos(wiki.GetCostumeData(__ai.GetFlag("itemType"), listIndex))
						createNewWindow = False
				if createNewWindow:
					lb = self.children["resultpageListbox"]
					displayIdx = len(lb.itemList)
					equipItemPointer = SpecialClass(displayIdx, 0)
					equipItemPointer.LoadItemInfos(wiki.GetCostumeData(__ai.GetFlag("itemType"), listIndex))
					equipItemPointer.sortIndex = listIndex
					lb.AppendItem(equipItemPointer, False)
					self.__WikiPlaceListItemAtBottom(equipItemPointer)
			elif WikiUI.IsCategory(loadType, "chests"):
				(itemVnum, bossVnum) = wiki.GetChestData(__ai.GetFlag("itemType"), listIndex)
				if itemVnum == 0:
					return
				lb = self.children["resultpageListbox"]
				displayIdx = len(lb.itemList)
				equipItemPointer = ListBoxItemSpecial(displayIdx, itemVnum, bossVnum, 0, True)
				equipItemPointer.sortIndex = listIndex
				lb.AppendItem(equipItemPointer, False)
				self.__WikiPlaceListItemAtBottom(equipItemPointer)
			elif WikiUI.IsCategory(loadType, "monster") or WikiUI.IsCategory(loadType, "bosses") or WikiUI.IsCategory(loadType, "metinstone"):
				if listIndex < 0:
					self.AIAppendAlgoritm = None
					self.__WikiFinalizeResultList(loadType)
					return
				if WikiUI.IsCategory(loadType, "monster"):
					mobVnum = wiki.GetMonsterData(__ai.GetFlag("itemType"), listIndex)
				elif WikiUI.IsCategory(loadType, "bosses"):
					mobVnum = wiki.GetBossData(__ai.GetFlag("itemType"), listIndex)
				else:
					mobVnum = wiki.GetStoneData(__ai.GetFlag("itemType"), listIndex)
				if mobVnum == 0:
					self.__WikiAutoloadStepBack(__ai, listIndex, loadType)
					return
				if not WikiMobHasDrops(mobVnum):
					WikiDebugLayout("skip mob wikiIdx=%s vnum=%s (no drops)" % (listIndex, mobVnum))
					self.__WikiAutoloadStepBack(__ai, listIndex, loadType)
					return
				lb = self.children["resultpageListbox"]
				innerW = max(320, lb.GetWidth() - 8)
				rowH = WikiMobDropPanelRowHeight()
				equipItemPointer = WikiMobDropPanel(mobVnum, innerW, rowH, True, True)
				equipItemPointer.sortIndex = WikiGetMonsterLevel(mobVnum)
				lb.AppendItem(equipItemPointer, False)
				self.__WikiPlaceListItemAtBottom(equipItemPointer)
			self.__WikiAutoloadStepBack(__ai, listIndex, loadType)
		#except:
		#	dbg.TraceError("Wiki-Debug: Something is wrong in check load process")

	def get_key(self, data):
		return data.sortIndex

	def __WikiAutoloadStepBack(self, __ai, listIndex, loadType):
		nextIdx = listIndex - 1
		__ai.SetFlag("maxSize", nextIdx)
		if nextIdx < 0:
			self.AIAppendAlgoritm = None
			self.__WikiFinalizeResultList(loadType)

	def __WikiPlaceListItemAtBottom(self, listItem):
		lb = self.children["resultpageListbox"]
		_y = 0
		for child in lb.itemList:
			if child is listItem:
				continue
			h = child.exPos[1] + child.GetHeight()
			if h > _y:
				_y = h
		listItem.SetPosition(0, _y, True)

	def __WikiDbgListLayout(self):
		try:
			lb = self.children["resultpageListbox"]
			parts = []
			for i, it in enumerate(lb.itemList):
				tn = type(it).__name__
				si = getattr(it, "sortIndex", "?")
				ex = it.exPos
				h = it.GetHeight()
				vn = "?"
				try:
					if it._children.has_key("itemVnum"):
						vn = it._children["itemVnum"]
					elif getattr(it, "_ownerVnum", 0):
						vn = it._ownerVnum
					elif getattr(it, "_chestVnum", 0):
						vn = it._chestVnum
				except:
					pass
				parts.append("%d:%s v=%s sort=%s y=%s h=%s" % (i, tn, vn, si, ex[1], h))
			return "%d rows | %s" % (len(parts), " ; ".join(parts) if parts else "-")
		except:
			return "?"

	def __WikiFinalizeResultList(self, loadType):
		lb = self.children["resultpageListbox"]
		WikiDebugLayout("finalize BEFORE loadType=%s %s" % (loadType, self.__WikiDbgListLayout()))
		self.SetPositionToSort(lb, loadType)
		lb.CalculateScroll()
		lb.Render(0)
		WikiDebugLayout(
			"finalize AFTER scrollLen=%s listH=%s %s"
			% (getattr(lb, "scrollLen", "?"), lb.GetHeight(), self.__WikiDbgListLayout())
		)

	def SetPositionToSort(self, listBox, loadType):
		(itemList, _y) = (listBox.itemList, 0)
		if WikiUI.IsCategory(loadType, "costume"):
			reverseMethod = True
		elif WikiUI.IsCategory(loadType, "equipment"):
			reverseMethod = False  # sortIndex = level: low to high
		elif WikiUI.IsCategory(loadType, "monster") or WikiUI.IsCategory(loadType, "bosses") or WikiUI.IsCategory(loadType, "metinstone"):
			reverseMethod = False  # sortIndex = mob level: low to high
		else:
			reverseMethod = SHOW_ITEM_LOWER_TO_BIG
		if len(itemList) > 1:
			itemList = sorted(itemList, key=self.get_key,reverse=reverseMethod)
			listBox.itemList = itemList
		for child in itemList:
			ch = child.GetHeight()
			if ch <= 0:
				WikiDebugLayout("WARN zero height %s sort=%s" % (type(child).__name__, getattr(child, "sortIndex", "?")))
			child.SetPosition(0, _y, True)
			_y += ch

	def SetWindowStatus(self, bShowStatus):
		if self.children.has_key("resultpageListbox"):
			resultpageListbox = self.children["resultpageListbox"].itemList
			for child in resultpageListbox:
				renderIndex = child._children["renderIndex"] if child._children.has_key("renderIndex") else -1
				if renderIndex != -1:
					renderTarget.SetVisibility(renderIndex, bShowStatus)

		__ai = self.AIAppendAlgoritm
		if __ai != None:
			__ai.SetFlag("nexTime",app.GetTime()+(0.15 if bShowStatus else 999999))

	def Open(self):
		self._wikiItemViewMode = "refine"
		self._wikiModeBtnLastPos = None
		self.SetWindowStatus(True)
		self.Show()
		self.SetTop()
		try:
			self.__WikiLayoutSearchRow()
			self.__WikiSetModeButtonsVisible(True)
			self.__WikiLayoutChestPreviewButton()
			self.__WikiRaiseToolbarZOrder()
		except:
			pass

	def Close(self):
		self.SetWindowStatus(False)
		self.__WikiSetModeButtonsVisible(False)
		self.Hide()

	def __WikiResolveChestVnumForPreview(self):
		v = self.children.get("selectedItem", 0)
		if v:
			return v
		try:
			self.UpdateItemsList()
		except:
			pass
		return self.children.get("selectedItem", 0)

	def __WikiGetResultListInnerWidth(self):
		try:
			return max(320, self.children["resultpageListbox"].GetWidth() - 8)
		except:
			return 540

	def __WikiDbgListItems(self):
		try:
			lb = self.children["resultpageListbox"]
			names = []
			for it in lb.itemList:
				names.append(type(it).__name__)
			return "%d:[%s]" % (len(names), ",".join(names) if names else "-")
		except:
			return "?"

	def __WikiHasInPanelPreviewRows(self):
		try:
			for it in self.children["resultpageListbox"].itemList:
				cname = type(it).__name__
				if cname in ("WikiInPanelChestDropView", "WikiInPanelItemDropView"):
					return True
		except:
			pass
		return False

	def __WikiPurgeInPanelPreview(self, tag=""):
		if not self.__WikiHasInPanelPreviewRows():
			WikiDebugViewMode("purge(%s) skip (no preview rows) list=%s" % (tag, self.__WikiDbgListItems()))
			return False
		WikiDebugViewMode("purge(%s) BEFORE list=%s" % (tag, self.__WikiDbgListItems()))
		if self.children.has_key("listBoxCube") and self.children["listBoxCube"]:
			try:
				self.children["listBoxCube"].Reset()
			except:
				pass
		self.ClearResultListbox("equipment#0".split("#"), True)
		try:
			lb = self.children["resultpageListbox"]
			lb.CalculateScroll()
			lb.Render(0)
		except:
			pass
		WikiDebugViewMode("purge(%s) AFTER list=%s" % (tag, self.__WikiDbgListItems()))
		return True

	def __WikiSwitchItemViewMode(self, newMode, force=False):
		oldMode = getattr(self, "_wikiItemViewMode", "refine")
		hasPreview = self.__WikiHasInPanelPreviewRows()
		if (not force) and oldMode == newMode and not hasPreview:
			WikiDebugViewMode("switch skip same mode=%s list=%s" % (oldMode, self.__WikiDbgListItems()))
			return oldMode
		WikiDebugViewMode(
			"switch %s -> %s force=%s previewRows=%s list_before=%s"
			% (oldMode, newMode, force, hasPreview, self.__WikiDbgListItems())
		)
		self._wikiItemViewMode = newMode
		self._wikiLiveSearchItemVnum = None
		if force or oldMode != newMode or hasPreview:
			if oldMode in ("chest", "itempreview") or newMode in ("chest", "itempreview") or hasPreview:
				self.__WikiPurgeInPanelPreview("switch")
		try:
			self.__WikiSyncCategoryPanelVisibility()
			self.__WikiLayoutSearchRow()
			self.__WikiLayoutChestPreviewButton()
			self.__WikiRaiseToolbarZOrder()
		except:
			pass
		WikiDebugViewMode("switch done mode=%s list=%s" % (self._wikiItemViewMode, self.__WikiDbgListItems()))
		return oldMode

	def __WikiShowItemPreviewPageOnly(self, selectedVnum):
		self.ClearResultListbox("equipment#0".split("#"), True)
		lb = self.children["resultpageListbox"]
		innerW = self.__WikiGetResultListInnerWidth()
		if not selectedVnum:
			lb.AppendItem(WikiInPanelItemDropView(0, 0, False, innerW, True))
		else:
			(baseV, isRef) = WikiUI.getRealVnum(selectedVnum)
			dispV = baseV + wiki.GetRefineMaxLevel(baseV) if isRef else baseV
			lb.AppendItem(WikiInPanelItemDropView(dispV, baseV, isRef, innerW, True))
		lb.CalculateScroll()
		lb.Render(0)
		try:
			self.__WikiLayoutSearchRow()
			self.__WikiLayoutChestPreviewButton()
			self.__WikiRaiseToolbarZOrder()
		except:
			pass

	def __WikiOpenItemPreview(self):
		self.__WikiSwitchItemViewMode("itempreview")
		v = self.__WikiResolveChestVnumForPreview()
		if not v:
			try:
				chat.AppendChat(
					chat.CHAT_TYPE_INFO,
					getattr(localeInfo, "WIKI_ITEM_PREVIEW_NO_SELECT", getattr(localeInfo, "WIKI_CHEST_PREVIEW_NO_SELECT", "")),
				)
			except:
				pass
			self.__WikiShowItemPreviewPageOnly(0)
			return
		self.ShowItemInfo(v, 0, False)

	def __WikiShowChestDropPageOnly(self, chestVnum):
		self.__WikiSwitchItemViewMode("chest")
		self.ClearResultListbox("equipment#0".split("#"), True)
		lb = self.children["resultpageListbox"]
		lb.AppendItem(WikiInPanelChestDropView(int(chestVnum) if chestVnum else 0, self.__WikiGetResultListInnerWidth(), True))
		lb.CalculateScroll()
		lb.Render(0)
		try:
			self.__WikiSyncCategoryPanelVisibility()
			self.__WikiLayoutSearchRow()
			self.__WikiLayoutChestPreviewButton()
			self.__WikiRaiseToolbarZOrder()
		except:
			pass

	def __WikiOpenChestPreview(self):
		self.__WikiSwitchItemViewMode("chest")
		v = self.__WikiResolveChestVnumForPreview()
		if not v:
			try:
				chat.AppendChat(
					chat.CHAT_TYPE_INFO,
					getattr(localeInfo, "WIKI_CHEST_PREVIEW_NO_SELECT", "Wiki aramasinda once bir esya secin."),
				)
			except:
				pass
			self.__WikiShowChestDropPageOnly(0)
			return
		self.ShowItemInfo(v, 0, False)

	def __WikiSetRefineItemView(self):
		oldMode = getattr(self, "_wikiItemViewMode", "refine")
		leftPreview = oldMode in ("chest", "itempreview")
		WikiDebugViewMode(
			"SetRefine enter old=%s leftPreview=%s sel=%s list=%s"
			% (oldMode, leftPreview, self.children.get("selectedItem", 0), self.__WikiDbgListItems())
		)
		if leftPreview:
			self.children["selectedItem"] = 0
			self._wikiLiveSearchItemVnum = None
		self.__WikiSwitchItemViewMode("refine", force=(leftPreview or self.__WikiHasInPanelPreviewRows()))
		v = self.children.get("selectedItem", 0)
		if leftPreview or not v:
			firstArg = "equipment#0"
			args = getattr(self, "_wikiComboArgs", None)
			if args:
				for a in args:
					if not a.startswith("wiki_char#"):
						firstArg = a
						break
			try:
				self.__SelectType(firstArg, False, False)
			except:
				self.ClearResultListbox("equipment#0".split("#"), True)
				self.children["resultpageListbox"].CalculateScroll()
				self.children["resultpageListbox"].Render(0)
		else:
			self.ShowItemInfo(v, 0, False)
		WikiDebugViewMode("SetRefine done mode=%s sel=%s list=%s" % (
			getattr(self, "_wikiItemViewMode", "?"),
			self.children.get("selectedItem", 0),
			self.__WikiDbgListItems(),
		))
		try:
			self.__WikiSyncCategoryPanelVisibility()
			self.__WikiLayoutSearchRow()
			self.__WikiLayoutChestPreviewButton()
			self.__WikiRaiseToolbarZOrder()
		except:
			pass

	def __WikiGetModeBtnParent(self):
		try:
			game = constInfo.GetGameInstance()
			if game:
				return game
		except:
			pass
		return self

	def __WikiDestroyModeButtons(self):
		if not getattr(self, "children", None):
			return
		for k in ("wikiChestPreviewBtn", "wikiRefineViewBtn", "wikiItemPreviewBtn"):
			if not self.children.has_key(k):
				continue
			btn = self.children[k]
			if btn:
				try:
					btn.Hide()
					btn.Destroy()
				except:
					pass
			try:
				del self.children[k]
			except:
				pass

	def __WikiSetModeButtonsVisible(self, show):
		if not getattr(self, "children", None):
			return
		for k in ("wikiChestPreviewBtn", "wikiRefineViewBtn", "wikiItemPreviewBtn"):
			if not self.children.has_key(k) or not self.children[k]:
				continue
			btn = self.children[k]
			if show:
				btn.Show()
				try:
					btn.SetTop()
				except:
					pass
			else:
				btn.Hide()

	def __WikiSyncModeButtonFollow(self):
		if not getattr(self, "_wikiModernLayout", 0):
			return
		if not self.IsShow():
			return
		try:
			pos = self.GetGlobalPosition()
		except:
			return
		if pos == getattr(self, "_wikiModeBtnLastPos", None):
			return
		self._wikiModeBtnLastPos = pos
		self.__WikiLayoutChestPreviewButton()

	def __WikiCenterModeButtonText(self, btn):
		if not btn or not getattr(btn, "ButtonText", None):
			return
		try:
			bw = btn.GetWidth()
			bh = btn.GetHeight()
		except:
			bw, bh = WIKI_MODE_BTN_W, WIKI_MODE_BTN_H
		btn.ButtonText.SetPosition(bw / 2, bh / 2)
		btn.ButtonText.SetHorizontalAlignCenter()
		btn.ButtonText.SetVerticalAlignCenter()

	def __WikiCreateModeButton(self, label, event):
		b = ui.Button()
		b.SetParent(self.__WikiGetModeBtnParent())
		b.AddFlag("float")
		b.SetUpVisual(PUBLIC_BTN % 1)
		b.SetOverVisual(PUBLIC_BTN % 2)
		b.SetDownVisual(PUBLIC_BTN % 3)
		try:
			b.SetSize(WIKI_MODE_BTN_W, WIKI_MODE_BTN_H)
		except:
			pass
		b.SetText(label)
		self.__WikiCenterModeButtonText(b)
		b.SAFE_SetEvent(event)
		b.Show()
		return b

	def __WikiLayoutChestPreviewButton(self):
		if not getattr(self, "_wikiModernLayout", 0):
			return
		if not self.children.has_key("wikiChestPreviewBtn"):
			return
		if not self.IsShow():
			return
		btns = []
		for k in ("wikiChestPreviewBtn", "wikiRefineViewBtn", "wikiItemPreviewBtn"):
			if self.children.has_key(k) and self.children[k]:
				btns.append(self.children[k])
		if not btns:
			return
		try:
			gx, gy = self.GetGlobalPosition()
		except:
			gx, gy = self.GetLocalPosition()
		bh = WIKI_MODE_BTN_H
		gap = WIKI_MODE_BTN_STACK_GAP
		totalH = len(btns) * bh + (len(btns) - 1) * gap
		try:
			winH = self.GetHeight()
		except:
			winH = 520
		y0 = gy + max(40, (winH - totalH) / 2)
		x = gx + self.GetWidth() + WIKI_MODE_BTN_OUTSIDE_GAP
		y = y0
		for b in btns:
			b.SetPosition(x, y)
			self.__WikiCenterModeButtonText(b)
			try:
				bh = b.GetHeight()
			except:
				bh = WIKI_MODE_BTN_H
			try:
				b.SetTop()
			except:
				pass
			y += bh + gap

	def OnPressExitKey(self):
		self.Close()
		return TRUE
	def OnPressEscapeKey(self):
		self.Close()
		return TRUE

class WikiInPanelItemDropView(WikiUI.DefaultWikiImage):
	def __init__(self, displayVnum, apiBaseVnum, isRefineItem, panelWidth, directlyLoad=False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._displayVnum = int(displayVnum) if displayVnum else 0
		self._apiBaseVnum = int(apiBaseVnum) if apiBaseVnum else 0
		self._isRefineItem = bool(isRefineItem)
		self._panelWidth = max(280, int(panelWidth))
		self._previewWidgets = []
		if directlyLoad:
			self.LoadItemInfos()

	def Destroy(self):
		for w in list(getattr(self, "_previewWidgets", [])):
			try:
				w.Hide()
				w.Destroy()
			except:
				pass
		self._previewWidgets = []
		for k in ("wikiSolidBg", "wikiSolidBgLine"):
			if self._children.has_key(k) and self._children[k]:
				try:
					self._children[k].Hide()
					self._children[k].Destroy()
				except:
					pass
				try:
					del self._children[k]
				except:
					pass
		WikiUI.DefaultWikiImage.Destroy(self)

	def _tl(self, x, y, txt, color=0xFFE8E8E8):
		t = ui.TextLine()
		t.SetParent(self)
		t.SetPosition(int(x), int(y))
		try:
			t.SetFontName(localeInfo.UI_DEF_FONT)
		except:
			pass
		t.SetPackedFontColor(color)
		t.SetText(_WikiClipText(txt, 120))
		t.Show()
		self._previewWidgets.append(t)

	def LoadItemInfos(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True
		pw = self._panelWidth
		LN = WIKI_ITEM_PREVIEW_LINE
		x0, x1, x2, x3 = 8, int(pw * 0.36), int(pw * 0.50), int(pw * 0.58)
		if not self._displayVnum:
			WikiApplySolidBg(self, pw, 80, WIKI_PANEL_NEUTRAL)
			self._tl(8, 8, getattr(localeInfo, "WIKI_ITEM_PREVIEW_NO_SELECT", "Select an item from wiki search."), 0xFFFFAA88)
			self.Show()
			return
		try:
			mobList = wiki.GetItemDropFromMonster(self._apiBaseVnum, self._isRefineItem)
		except:
			mobList = []
		try:
			chestList = wiki.GetItemDropFromChest(self._apiBaseVnum, self._isRefineItem)
		except:
			chestList = []
		try:
			specialData = WikiUI.GetSpecialDropWays(self._apiBaseVnum, self._isRefineItem)
		except:
			specialData = []
		try:
			item.SelectItem(self._displayVnum)
			itemTitle = item.GetItemName()
		except:
			itemTitle = "?"
		badge = str(len(mobList) + len(chestList) + len(specialData))
		yTop = 8 + LN + 6 + LN + 4
		h = yTop
		hasAny = bool(mobList or chestList or specialData)
		if mobList:
			h += LN + 2 + len(mobList) * LN + 6
		if chestList:
			h += LN + 2 + len(chestList) * LN + 6
		if specialData:
			h += LN + 2 + len(specialData) * LN
		if not hasAny:
			h += LN + 4
		h += 20
		WikiApplySolidBg(self, pw, h, WIKI_PANEL_NEUTRAL)
		y = 8
		self._tl(x0, y, itemTitle, 0xFFFFE8B8)
		self._tl(max(x3, pw - 80), y, badge, 0xFFD0D0D0)
		y += LN + 6
		self._tl(x0, y, getattr(localeInfo, "WIKI_ITEM_PREVIEW_COL_NAME", "Name"), 0xFFAAAACC)
		self._tl(x1, y, getattr(localeInfo, "WIKI_ITEM_PREVIEW_COL_LEVEL", "Lv"), 0xFFAAAACC)
		self._tl(x2, y, getattr(localeInfo, "WIKI_ITEM_PREVIEW_COL_COUNT", "Cnt"), 0xFFAAAACC)
		self._tl(x3, y, getattr(localeInfo, "WIKI_ITEM_PREVIEW_COL_LOC", "Location"), 0xFFAAAACC)
		y += LN + 4
		if mobList:
			sect = getattr(localeInfo, "WIKI_ITEM_PREVIEW_SECTION_MOB", "Mobs / Metins / Bosses") + " - %d" % len(mobList)
			self._tl(x0, y, sect, 0xFF66AAFF)
			y += LN + 2
			for mobVnum in mobList:
				try:
					nm = nonplayer.GetMonsterName(mobVnum)
					lv = nonplayer.GetMonsterLevel(mobVnum)
					lvStr = str(lv) if lv > 0 else "-"
					cnt = WikiMobDropCountForItem(mobVnum, self._displayVnum, self._isRefineItem)
					loc = WikiFormatItemPreviewLocation(mobVnum)
				except:
					nm, lvStr, cnt, loc = ("?", "-", "1", "-")
				self._tl(x0, y, nm, 0xFFEEEEEE)
				self._tl(x1, y, lvStr, 0xFFEEEEEE)
				self._tl(x2, y, str(cnt), 0xFFEEEEEE)
				self._tl(x3, y, loc, 0xFFEEEEEE)
				y += LN
			y += 6
		if chestList:
			sect = getattr(localeInfo, "WIKI_ITEM_PREVIEW_SECTION_CHEST", "Chests") + " - %d" % len(chestList)
			self._tl(x0, y, sect, 0xFF66AAFF)
			y += LN + 2
			for cv in chestList:
				try:
					item.SelectItem(cv)
					cn = item.GetItemName()
					cnt = WikiChestDropCountForItem(cv, self._displayVnum, self._isRefineItem)
				except:
					cn, cnt = ("?", "1")
				self._tl(x0, y, cn, 0xFFEEEEEE)
				self._tl(x1, y, "-", 0xFFEEEEEE)
				self._tl(x2, y, str(cnt), 0xFFEEEEEE)
				self._tl(x3, y, "-", 0xFFEEEEEE)
				y += LN
			y += 6
		if specialData:
			sect = getattr(localeInfo, "WIKI_ITEM_PREVIEW_SECTION_OTHER", "Other") + " - %d" % len(specialData)
			self._tl(x0, y, sect, 0xFF66AAFF)
			y += LN + 2
			for sw in specialData:
				self._tl(x0, y, sw, 0xFFEEEEEE)
				self._tl(x1, y, "-", 0xFFEEEEEE)
				self._tl(x2, y, "1", 0xFFEEEEEE)
				self._tl(x3, y, "-", 0xFFEEEEEE)
				y += LN
		if not hasAny:
			self._tl(x0, y, getattr(localeInfo, "WIKI_ITEM_PREVIEW_EMPTY", "No drop sources in wiki data."), 0xFF888888)
		self.Show()

class WikiMobDropPanel(WikiUI.DefaultWikiImage):
	MOB_PREVIEW_W = 187
	MOB_PREVIEW_H = WIKI_MOB_DROP_PANEL_PREVIEW_H

	def __init__(self, ownerVnum, panelWidth, panelHeight, fromMobTable, directlyLoad=False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._ownerVnum = int(ownerVnum) if ownerVnum else 0
		self._fromMobTable = bool(fromMobTable)
		self._panelW = max(320, int(panelWidth))
		self._panelH = max(180, int(panelHeight))
		self.grid = None
		self._gridVnums = None
		if directlyLoad:
			self.LoadItemInfos()

	def GetWidth(self):
		return self._panelW

	def GetHeight(self):
		return self._panelH

	def Destroy(self):
		if self._children.has_key("renderIndex"):
			try:
				renderTarget.SetVisibility(self._children["renderIndex"], False)
				renderTarget.ResetModel(self._children["renderIndex"])
			except:
				pass
		if getattr(self, "grid", None):
			try:
				self.grid.Hide()
				self.grid.Destroy()
			except:
				pass
		self.grid = None
		self._gridVnums = None
		for k in ("wikiSolidBg", "wikiSolidBgLine", "rowZebraBg", "rowBottomLine"):
			if self._children.has_key(k) and self._children[k]:
				try:
					self._children[k].Hide()
					self._children[k].Destroy()
				except:
					pass
				try:
					del self._children[k]
				except:
					pass
		WikiUI.DefaultWikiImage.Destroy(self)

	def __OnSelectDropGridSlot(self, slotIndex):
		try:
			if self._gridVnums is None:
				return
			if slotIndex < 0 or slotIndex >= len(self._gridVnums):
				return
			vn = self._gridVnums[slotIndex]
			if vn:
				self.OnClickItem("mouse_click", 0, vn)
		except:
			pass

	def __OverInDropGridItem(self, slotIndex):
		try:
			if self._gridVnums is None:
				return
			if slotIndex < 0 or slotIndex >= len(self._gridVnums):
				return
			vn = self._gridVnums[slotIndex]
			if vn:
				WikiShowGridItemTooltip(vn)
		except:
			pass

	def __OverOutDropGridItem(self):
		WikiHideGridItemTooltip()

	def LoadItemInfos(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True
		ownerVnum = self._ownerVnum
		fromMob = self._fromMobTable
		WikiDebugMobDrop("WikiMobDropPanel.LoadItemInfos START owner=%s fromMob=%s pw=%s ph=%s" % (
			ownerVnum, fromMob, self._panelW, self._panelH))
		try:
			pw = self._panelW
			totalH = self._panelH
			slot = WIKI_CHEST_PREVIEW_SLOT_SIZE
			gap = WIKI_CHEST_PREVIEW_SLOT_GAP
			cols = WIKI_MOB_DROP_GRID_COLS
			entries = WikiCollectSortedDrops(ownerVnum, fromMob)
			rows = WIKI_MOB_DROP_GRID_ROWS
			gw = cols * slot + (cols - 1) * gap
			gh = rows * slot + (rows - 1) * gap
			leftX = 8
			previewX = leftX
			gridLeft = previewX + self.MOB_PREVIEW_W + 12 + WIKI_MOB_DROP_GRID_SHIFT_X
			pw = max(pw, gridLeft + gw + 12)
			self._panelW = pw
			headerH = 34
			bodyTop = headerH + 8
			contentMinH = bodyTop + max(self.MOB_PREVIEW_H, gh) + 8
			totalH = max(totalH, contentMinH)
			ui.Window.SetSize(self, pw, totalH)
			self._panelH = totalH

			rowBg = ui.Bar()
			rowBg.SetParent(self)
			rowBg.SetPosition(0, 0)
			rowBg.SetSize(pw, totalH)
			rowBg.SetColor(WIKI_ROW_ZEBRA_A)
			rowBg.AddFlag("not_pick")
			rowBg.Show()
			self._children["rowZebraBg"] = rowBg
			rowLn = ui.Bar()
			rowLn.SetParent(self)
			rowLn.SetPosition(0, totalH - 1)
			rowLn.SetSize(pw, 1)
			rowLn.SetColor(WIKI_ROW_BORDER)
			rowLn.AddFlag("not_pick")
			rowLn.Show()
			self._children["rowBottomLine"] = rowLn

			hdrBg = ui.Bar()
			hdrBg.SetParent(self)
			hdrBg.SetPosition(0, 0)
			hdrBg.SetSize(pw, headerH)
			hdrBg.SetColor(WIKI_EQUIP_HEADER_BG)
			hdrBg.AddFlag("not_pick")
			hdrBg.Show()
			self._children["dropHeaderBg"] = hdrBg

			if fromMob:
				titleTxt = localeInfo.WIKI_DROPLIST_INFO % nonplayer.GetMonsterName(ownerVnum)
				try:
					lv = nonplayer.GetMonsterLevel(ownerVnum)
					if lv > 0:
						titleTxt += "  |  Lv.%d" % lv
				except:
					pass
			else:
				item.SelectItem(ownerVnum)
				titleTxt = localeInfo.WIKI_CONTENT_INFO % item.GetItemName()

			self._children["dropTitle"] = WikiUI.CreateWindow(ui.TextLine(), self, (10, 10), titleTxt)
			try:
				self._children["dropTitle"].SetPackedFontColor(0xFFFFE8B8)
			except:
				pass

			if fromMob:
				renderIndex = renderTarget.GetFreeIndex(1000, 1000000)
				self._children["renderIndex"] = renderIndex
				renterTarget = WikiUI.CreateWindow(WikiUI.RenderTargetNew(), self, (previewX, bodyTop), "", "", (self.MOB_PREVIEW_W, self.MOB_PREVIEW_H))
				renterTarget.SetRenderTarget(renderIndex)
				renderTarget.SetRotation(renderIndex, False)
				self._children["renterTarget"] = renterTarget
				renderTarget.SelectModel(renderIndex, ownerVnum)
				renderTarget.SetVisibility(renderIndex, True)
			else:
				item.SelectItem(ownerVnum)
				ix = previewX + (self.MOB_PREVIEW_W - slot) / 2
				iy = bodyTop + (self.MOB_PREVIEW_H - slot) / 2
				slotBg = ui.ExpandedImageBox()
				slotBg.SetParent(self)
				slotBg.SetPosition(ix, iy)
				slotBg.LoadImage(WIKI_SLOT_PLATE)
				slotBg.SetSize(slot, slot)
				slotBg.AddFlag("not_pick")
				slotBg.Show()
				self._children["ownerSlotBg"] = slotBg
				itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (ix, iy), item.GetIconImageFileName())
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, ownerVnum)
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0, ownerVnum)
				self._children["itemIcon"] = itemIcon

			gridY = bodyTop + max(0, (max(self.MOB_PREVIEW_H, gh) - gh) / 2)
			maxSlots = cols * rows
			self._gridVnums = [0] * maxSlots
			self.grid = ui.GridSlotWindow()
			self.grid.SetParent(self)
			self.grid.SetPosition(gridLeft, gridY)
			self.grid.ArrangeSlot(0, cols, rows, slot, slot, gap, gap)
			self.grid.SetSlotBaseImage(WIKI_SLOT_PLATE, 1.0, 1.0, 1.0, 1.0)
			self.grid.SetOverInItemEvent(ui.__mem_func__(self.__OverInDropGridItem))
			self.grid.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutDropGridItem))
			self.grid.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSelectDropGridSlot))
			self.grid.Show()
			self._children["dropGrid"] = self.grid

			WikiGridFillDropSlots(self.grid, self._gridVnums, cols, rows, entries)

			WikiDebugMobDrop("WikiMobDropPanel.LoadItemInfos OK drops=%d pw=%s ph=%s" % (len(entries), pw, totalH))
			self.Show()
		except:
			try:
				dbg.TraceError("[WIKI_DROP] WikiMobDropPanel.LoadItemInfos EXC: %s" % sys.exc_info()[1])
			except:
				pass

class WikiInPanelChestDropView(WikiUI.DefaultWikiImage):
	def __init__(self, chestVnum, panelWidth, directlyLoad=False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._chestVnum = int(chestVnum) if chestVnum else 0
		self._panelWidth = max(320, int(panelWidth))
		self.grid = None
		self.iconSlot = None
		self.nameField = None
		self.countField = None
		self._gridVnums = None
		self._chestGridCols = 1
		self._chestGridRows = 1
		if directlyLoad:
			self.LoadItemInfos()

	def Destroy(self):
		try:
			if getattr(self, "grid", None):
				self.grid.Hide()
				self.grid.Destroy()
		except:
			pass
		self.grid = None
		for nm in ("iconSlot", "nameField", "countField"):
			o = getattr(self, nm, None)
			if o:
				try:
					o.Hide()
					o.Destroy()
				except:
					pass
				setattr(self, nm, None)
		self._gridVnums = None
		for k in ("wikiSolidBg", "wikiSolidBgLine"):
			if self._children.has_key(k) and self._children[k]:
				try:
					self._children[k].Hide()
					self._children[k].Destroy()
				except:
					pass
				try:
					del self._children[k]
				except:
					pass
		WikiUI.DefaultWikiImage.Destroy(self)

	def LoadItemInfos(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True
		slot = WIKI_CHEST_PREVIEW_SLOT_SIZE
		gap = WIKI_CHEST_PREVIEW_SLOT_GAP
		availW = max(slot, self._panelWidth - 16)
		step = slot + gap
		cols = max(1, (availW + gap) // step) if step > 0 else 1
		rows = WIKI_CHEST_PREVIEW_GRID_ROWS

		self._chestGridCols = cols
		self._chestGridRows = rows

		gw = cols * slot + (cols - 1) * gap
		gh = rows * slot + (rows - 1) * gap
		rowTop = 8
		rowH = 36
		gridY = rowTop + rowH + 6
		totalH = gridY + gh + 12
		pw = max(self._panelWidth, gw + 16)
		self._panelWidth = pw
		WikiApplySolidBg(self, pw, totalH, WIKI_PANEL_NEUTRAL)

		self.iconSlot = ui.GridSlotWindow()
		self.iconSlot.SetParent(self)
		self.iconSlot.SetPosition(8, rowTop)
		self.iconSlot.ArrangeSlot(0, 1, 1, slot, slot, 0, 0)
		self.iconSlot.SetSlotBaseImage(WIKI_SLOT_PLATE, 1.0, 1.0, 1.0, 1.0)
		self.iconSlot.Show()

		nameW = max(120, pw - 8 - slot - 8 - 60 - 8)
		self.nameField = ui.EditLine()
		self.nameField.SetParent(self)
		self.nameField.SetPosition(8 + slot + 8, rowTop + 6)
		self.nameField.SetSize(nameW, 22)
		self.nameField.AddFlag("not_pick")
		self.nameField.SetMax(64)
		self.nameField.SetOutline()
		self.nameField.Show()

		self.countField = ui.EditLine()
		self.countField.SetParent(self)
		self.countField.SetPosition(pw - 8 - 60, rowTop + 6)
		self.countField.SetSize(56, 22)
		self.countField.AddFlag("not_pick")
		self.countField.SetMax(12)
		self.countField.SetOutline()
		self.countField.Show()

		self.grid = ui.GridSlotWindow()
		self.grid.SetParent(self)
		self.grid.SetPosition(max(4, (pw - gw) / 2), gridY)
		self.grid.ArrangeSlot(0, cols, rows, slot, slot, gap, gap)
		self.grid.SetSlotBaseImage(WIKI_SLOT_PLATE, 1.0, 1.0, 1.0, 1.0)
		self.grid.SetOverInItemEvent(ui.__mem_func__(self.__OverInGridItem))
		self.grid.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutGridItem))
		self.grid.Show()

		self.__ApplyChestData()
		self.Show()

	def __ApplyChestData(self):
		cv = self._chestVnum
		cols = getattr(self, "_chestGridCols", 1)
		rows = getattr(self, "_chestGridRows", 1)
		maxSlots = cols * rows
		self._gridVnums = [0] * maxSlots
		for i in xrange(maxSlots):
			self.grid.ClearSlot(i)
		if not cv:
			self.iconSlot.ClearSlot(0)
			try:
				self.nameField.SetText(getattr(localeInfo, "WIKI_CHEST_PREVIEW_NO_SELECT", ""))
			except:
				self.nameField.SetText("")
			self.countField.SetText("0")
			return
		try:
			item.SelectItem(cv)
			self.iconSlot.ClearSlot(0)
			self.iconSlot.SetItemSlot(0, cv, 0)
			self.nameField.SetText(item.GetItemName())
		except:
			self.iconSlot.ClearSlot(0)
			self.nameField.SetText("")
		n = 0
		try:
			n = wiki.GetSpecialInfoSize(cv)
		except:
			n = 0
		self.countField.SetText(str(n))
		chestEntries = []
		for i in xrange(n):
			try:
				(iv, cnt) = wiki.GetSpecialInfoData(cv, i)
			except:
				iv, cnt = 0, 0
			if iv:
				chestEntries.append((0, iv, cnt))
		WikiGridFillDropSlots(self.grid, self._gridVnums, cols, rows, chestEntries)

	def __OverInGridItem(self, slotIndex):
		try:
			if self._gridVnums is None:
				return
			if slotIndex < 0 or slotIndex >= len(self._gridVnums):
				return
			vn = self._gridVnums[slotIndex]
			if vn:
				WikiShowGridItemTooltip(vn)
		except:
			pass

	def __OverOutGridItem(self):
		WikiHideGridItemTooltip()

class EquipmentItem(WikiUI.DefaultWikiImage):
	# MANUEL: asagidaki RefineItem / LoadItemInfos "MANUEL:" ile esya satiri ve +N sutunlari

	class RefineItem(WikiUI.DefaultWikiWindow):
		def LoadData(self, refine, itemVnum, materialRowCount, refineData, rowPixelHeight=0, alignMaterialRows=0):
			colW = self.GetWidth() if self.GetWidth() > 8 else WIKI_REFINE_COL_STEP
			ix0 = max(0, (colW - 32) / 2)  # MANUEL: 32px ikonu sutun icinde yatay ortala
			rowStep = 32 + 5 + 8  # MANUEL: malzeme satirlari dikey aralik
			slotYBase = 22 + 5 + WIKI_REFINE_MATERIAL_SLOT_SHIFT_Y
			rc = materialRowCount if materialRowCount > 0 else 0
			priceRows = WikiRefinePriceRowCount(rc, alignMaterialRows)
			priceY = WikiRefineColumnPriceY(materialRowCount, alignMaterialRows)
			colH = max(priceY + 34, 72)
			tipH = rowPixelHeight if rowPixelHeight > colH else colH
			tooltipImage = WikiUI.CreateWindow(ui.ImageBox(), self, (0, 0), "", "", (colW, tipH))  # MANUEL: sutun tooltip hit (satir yuksekligi ile)
			tooltipImage.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, (itemVnum-wiki.GetRefineMaxLevel(itemVnum))+refine)
			tooltipImage.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			self._children["tooltipImage"] = tooltipImage

			if refine == 0:
				vl = ui.Bar()
				vl.SetParent(self)
				vl.SetPosition(0, 0)
				vl.SetSize(1, tipH)
				vl.SetColor(WIKI_REFINE_LINE_V)
				vl.AddFlag("not_pick")
				vl.Show()
				self._children["refineColLineL"] = vl
			vr = ui.Bar()
			vr.SetParent(self)
			vr.SetPosition(colW - 1, 0)
			vr.SetSize(1, tipH)
			vr.SetColor(WIKI_REFINE_LINE_V)
			vr.AddFlag("not_pick")
			vr.Show()
			self._children["refineColLineR"] = vr

			self._children["step_refine"] = WikiUI.CreateWindow(ui.TextLine(), self, (colW / 2, 4), "+{}".format(refine), "horizontal:center")  # MANUEL: +N sutun ortasi (WIKI_REFINE_COL_STEP)
			self._children["step_refine"].AddFlag("not_pick")
			try:
				self._children["step_refine"].SetPackedFontColor(0xFFFFFFFF)
			except:
				pass

			costStr = "-"
			if refineData and refineData.has_key("cost"):
				c = refineData["cost"]
				if c:
					costStr = localeInfo.MoneyFormat(c).replace(".000","k")
			self._children["step_price"] = WikiUI.CreateWindow(ui.TextLine(), self, (colW / 2, priceY), costStr, "horizontal:center")  # MANUEL: yang fiyat satiri
			try:
				self._children["step_price"].SetPackedFontColor(0xFFFFD700)
			except:
				pass

			probStr = "-"
			if refineData and refineData.has_key("prob") and refineData["prob"]:
				try:
					probStr = str(int(refineData["prob"]))
				except:
					probStr = str(refineData["prob"])
			if probStr != "-":
				probStr = str(probStr).strip().rstrip("%") + "%"
			self._children["step_prob"] = WikiUI.CreateWindow(ui.TextLine(), self, (colW / 2, priceY + 16), probStr, "horizontal:center")  # MANUEL: basari sansi (priceY + 16)
			try:
				self._children["step_prob"].SetPackedFontColor(0xFF66CCFF)
			except:
				pass

			slotDrawCount = WikiRefinePriceRowCount(rc, alignMaterialRows)
			for i in xrange(slotDrawCount):
				materialItem = 0
				if refineData and refineData.has_key("item") and i < len(refineData["item"]):
					try:
						materialItem = int(refineData["item"][i])
					except:
						materialItem = 0
				needInsertIcon = materialItem != 0
				if needInsertIcon and SHOW_NEXT_ITEM_REFINE == False and refine == 0:
					needInsertIcon = False
				iy = slotYBase + i * rowStep
				slotBg = ui.ExpandedImageBox()
				slotBg.SetParent(self)
				slotBg.SetPosition(ix0, iy)
				slotBg.LoadImage(WIKI_SLOT_PLATE)
				slotBg.SetSize(32, 32)
				slotBg.AddFlag("not_pick")
				slotBg.Show()
				self._children["refineSlotBg{}".format(i)] = slotBg
				if needInsertIcon:
					item.SelectItem(materialItem)
					refineItemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (ix0, iy), item.GetIconImageFileName())  # MANUEL: malzeme ikonu (sutun ortali)
					refineItemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, materialItem)
					refineItemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
					refineItemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0, materialItem)
					self._children["refineItemIcon{}".format(i)] = refineItemIcon
					materialItemCount = refineData["count"][i] if refineData and refineData.has_key("count") else 0
					if materialItemCount > 0:
						cntLine = WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), self, (ix0 + 20, iy + (32 if USE_ITEM_COUNT_NUMBER_LINE else 20)), str(materialItemCount))  # MANUEL: adet (ikon alti)
						self._children["refineItemCount{}".format(i)] = cntLine
						try:
							cntLine.SetPackedFontColor(WIKI_REFINE_ITEM_TEXT_COLOR)
						except:
							pass

			try:
				h = self.GetHeight()
				if h > 0:
					if self._children.has_key("refineColLineL"):
						self._children["refineColLineL"].SetSize(1, h)
					if self._children.has_key("refineColLineR"):
						self._children["refineColLineR"].SetSize(1, h)
			except:
				pass

	def __init__(self, listIndex, itemVnum, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["itemVnum"] = itemVnum
		self._children["refineItems"] = {}
		self._children["refineCount"] = 2
		self._children["refineLevel"] = wiki.GetRefineMaxLevel(itemVnum)

		for j in xrange(self._children["refineLevel"]+1):
			if item.SelectItemWiki((itemVnum-self._children["refineLevel"])+j) == 1:
				argv = wiki.GetRefineItems(item.GetRefineSet())
				if argv != 0:
					self.InsertRefine(j, *argv)

		refineItems = self._children["refineItems"]
		refineLevel = self._children["refineLevel"]
		refineCount = self._children["refineCount"]
		matRows = WikiEquipMaxMaterialRows(refineItems, refineLevel, refineCount)
		iw, ih = WikiEquipListInnerSize(matRows)
		listX = 130 + WIKI_REFINE_GRID_SHIFT_X
		listY = 20 + WIKI_REFINE_GRID_SHIFT_Y
		rowW = listX + iw + 20
		rowH = ih + listY + 14
		self.SetSize(rowW, rowH)

		li = self._children["listIndex"]
		zcol = WIKI_ROW_ZEBRA_A if (li % 2) == 0 else WIKI_ROW_ZEBRA_B
		rowBg = ui.Bar()
		rowBg.SetParent(self)
		rowBg.SetPosition(0, 0)
		rowBg.SetSize(self.GetWidth(), self.GetHeight())
		rowBg.SetColor(zcol)
		rowBg.AddFlag("not_pick")
		rowBg.Show()
		self._children["rowZebraBg"] = rowBg
		rowLn = ui.Bar()
		rowLn.SetParent(self)
		rowLn.SetPosition(0, self.GetHeight() - 1)
		rowLn.SetSize(self.GetWidth(), 1)
		rowLn.SetColor(WIKI_ROW_BORDER)
		rowLn.AddFlag("not_pick")
		rowLn.Show()
		self._children["rowBottomLine"] = rowLn

		listYHdr = 20 + WIKI_REFINE_GRID_SHIFT_Y
		headerH = listYHdr + 26
		hdrBg = ui.Bar()
		hdrBg.SetParent(self)
		hdrBg.SetPosition(0, 0)
		hdrBg.SetSize(self.GetWidth(), headerH)
		hdrBg.SetColor(WIKI_EQUIP_HEADER_BG)
		hdrBg.AddFlag("not_pick")
		hdrBg.Show()
		self._children["equipHeaderBg"] = hdrBg

		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True
			(itemVnum, refineLevel, refineCount, listIndex, refineItems) = (self._children["itemVnum"], self._children["refineLevel"], self._children["refineCount"], self._children["listIndex"], self._children["refineItems"])
			item.SelectItemWiki(itemVnum)
			itemName = item.GetItemName()
			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (5, 5), itemName[:itemName.find("+")] if itemName.find("+") != -1 else itemName)  # MANUEL: esya adi
			try:
				self._children["itemName"].SetPackedFontColor(WIKI_REFINE_ITEM_TEXT_COLOR)
			except:
				pass

			matRowsGlobal = WikiEquipMaxMaterialRows(refineItems, refineLevel, refineCount)
			itemLevelCoordinates = [ [0,0],[0,0],[10,55],[10,70],[10,80],[10,115]]  # MANUEL: ana ikon konumu (refineCount index)
			ix = itemLevelCoordinates[refineCount][0] + 20 + WIKI_EQUIP_ICON_SHIFT_X
			iy = itemLevelCoordinates[refineCount][1] + 20
			if matRowsGlobal <= 1:
				iy += WIKI_EQUIP_ICON_1ROW_SHIFT_Y
			itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (ix, iy), item.GetIconImageFileName() if item.GetIconImageFileName().find("gr2") == -1 else "icon/item/27995.tga")
			if listIndex == 99:
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, itemVnum-refineLevel)
			else:
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, itemVnum)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			self._children["itemIcon"] = itemIcon

			rd0 = refineItems[0] if refineItems.has_key(0) else {}
			matRows0 = WikiRefineMaterialRowsForColumn(0, rd0, refineCount)
			listYGrid = 20 + WIKI_REFINE_GRID_SHIFT_Y
			displayColsYang = WikiRefineVisibleColumnCount(refineItems, refineLevel)
			if displayColsYang > 0:
				yangIconY = listYGrid + WikiRefineColumnPriceY(matRows0, matRowsGlobal)
			else:
				yangIconY = iy + WIKI_EQUIP_ITEM_YANG_ICON_OFFSET_Y

			itemYangIcon = ui.ImageBox()
			itemYangIcon.SetParent(self)
			itemYangIcon.LoadImage(WIKI_REFINE_YANG_ICON)
			itemYangIcon.AddFlag("not_pick")
			itemYangIcon.SetPosition(ix + WIKI_EQUIP_ITEM_YANG_ICON_OFFSET_X, yangIconY)
			itemYangIcon.Show()
			self._children["itemYangIcon"] = itemYangIcon

			iw, _ih = WikiEquipListInnerSize(matRowsGlobal)
			par = constInfo.GetWikiInterface()
			colStep = WIKI_REFINE_COL_STEP  # MANUEL: sutun adimi
			try:
				if par and getattr(par, "_wikiModernLayout", 0) and getattr(par, "_wikiColStep", 0):
					colStep = par._wikiColStep
			except:
				colStep = WIKI_REFINE_COL_STEP  # MANUEL: sutun adimi fallback

			displayCols = WikiRefineVisibleColumnCount(refineItems, refineLevel)
			maxH = 72
			for i in xrange(displayCols):
				rdKey = WikiRefineRdKey(i)
				rd = refineItems[rdKey] if refineItems.has_key(rdKey) else {}
				matRows = WikiRefineMaterialRowsForColumn(i, rd, refineCount)
				h = WikiRefineColumnHeight(i, itemVnum, matRows, rd, matRowsGlobal)
				if h > maxH:
					maxH = h

			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxEx(True), self, (130 + WIKI_REFINE_GRID_SHIFT_X, 20 + WIKI_REFINE_GRID_SHIFT_Y), "", "", (iw, maxH))  # MANUEL: refine sutunlari listesi konum + boyut
			Listbox.SetItemStep(colStep)
			Listbox.SetItemSize(colStep, maxH)
			Listbox.SetViewItemCount(displayCols)

			for i in xrange(displayCols):
				refine_data = self.RefineItem()
				Listbox.AppendItem(refine_data)
				rdKey = WikiRefineRdKey(i)
				rd = refineItems[rdKey] if refineItems.has_key(rdKey) else {}
				matRows = WikiRefineMaterialRowsForColumn(i, rd, refineCount)
				refine_data.LoadData(i, itemVnum, matRows, rd, maxH, matRowsGlobal)

			Listbox.SetBasePos(0)
			Listbox.Show()
			self._children["Listbox"] = Listbox

			listX = 130 + WIKI_REFINE_GRID_SHIFT_X
			listY = 20 + WIKI_REFINE_GRID_SHIFT_Y
			rowW = listX + iw + 20
			rowH = maxH + listY + 14
			self.SetSize(rowW, rowH)
			if self._children.has_key("rowZebraBg"):
				self._children["rowZebraBg"].SetSize(self.GetWidth(), self.GetHeight())
			if self._children.has_key("rowBottomLine"):
				self._children["rowBottomLine"].SetPosition(0, self.GetHeight() - 1)

			WikiDebugLayout(
				"equip row vnum=%s cols=%d matGlobal=%d refineCount=%d maxH=%d row=%dx%d init=%dx%d"
				% (itemVnum, displayCols, matRowsGlobal, refineCount, maxH, rowW, rowH, self.GetWidth(), self.GetHeight())
			)
			for i in xrange(displayCols):
				rdKey = WikiRefineRdKey(i)
				rd = refineItems[rdKey] if refineItems.has_key(rdKey) else {}
				mr = WikiRefineMaterialRowsForColumn(i, rd, refineCount)
				WikiDebugLayout("  col +%d rdKey=%s matRows=%d hasContent=%s" % (i, rdKey, mr, WikiRefineColumnHasContent(rd)))

			self.Show()

	def OnClickItem(self, arg, itemVnum = 0):
		self.OverOutItem()
		parent = constInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(itemVnum+wiki.GetRefineMaxLevel(itemVnum) if itemVnum != 0 else self._children["itemVnum"], 0)

	def InsertRefine(self, refineIndex, *refineData):
		refineMaterialCount = 5
		(refineItems, refineCount) = (self._children["refineItems"], self._children["refineCount"])
		refineItems[refineIndex] = {
			#"id" : int(refineData[0]), # unused
			"item" : [int(refineData[1+(j * 2)]) for j in xrange(refineMaterialCount)],
			"count" : [int(refineData[2+(j * 2)]) for j in xrange(refineMaterialCount)],
			"cost" : int(refineData[(refineMaterialCount * 2) + 1]),
			"prob" : int(refineData[(refineMaterialCount * 2) + 2]),
			#"refine_count" : int(refineData[(refineMaterialCount * 2) + 3]), #unused
		}
		if int(refineData[(refineMaterialCount * 2) + 3]) > refineCount:
			refineCount = int(refineData[(refineMaterialCount * 2) + 3])
		(self._children["refineItems"], self._children["refineCount"]) = (refineItems, refineCount)

class MonsterItemSpecial(WikiUI.DefaultWikiImage):
	MOB_PREVIEW_W = 187
	MOB_PREVIEW_H = WIKI_MOB_DROP_PANEL_PREVIEW_H

	def Destroy(self):
		if self._children.has_key("renderIndex"):
			try:
				renderTarget.SetVisibility(self._children["renderIndex"], False)
				renderTarget.ResetModel(self._children["renderIndex"])
			except:
				pass
		if getattr(self, "grid", None):
			try:
				self.grid.Hide()
				self.grid.Destroy()
			except:
				pass
		self.grid = None
		self._gridVnums = None
		for k in ("wikiSolidBg", "wikiSolidBgLine", "rowZebraBg", "rowBottomLine"):
			if self._children.has_key(k) and self._children[k]:
				try:
					self._children[k].Hide()
					self._children[k].Destroy()
				except:
					pass
				try:
					del self._children[k]
				except:
					pass
		WikiUI.DefaultWikiImage.Destroy(self)

	def __init__(self, selectedVnum, isType, directlyLoad=False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["selectedVnum"] = selectedVnum
		self._children["isType"] = isType
		self.grid = None
		self._gridVnums = None
		if directlyLoad:
			self.LoadItemInfos()

	def __OnSelectDropGridSlot(self, slotIndex):
		try:
			if self._gridVnums is None:
				return
			if slotIndex < 0 or slotIndex >= len(self._gridVnums):
				return
			vn = self._gridVnums[slotIndex]
			if vn:
				self.OnClickItem("mouse_click", 0, vn)
		except:
			pass

	def __OverInDropGridItem(self, slotIndex):
		try:
			if self._gridVnums is None:
				return
			if slotIndex < 0 or slotIndex >= len(self._gridVnums):
				return
			vn = self._gridVnums[slotIndex]
			if vn:
				WikiShowGridItemTooltip(vn)
		except:
			pass

	def __OverOutDropGridItem(self):
		WikiHideGridItemTooltip()

	def __BuildDropGridPage(self, selectedVnum, isType):
		fromMob = (isType == 0)
		pw = WikiGetResultListInnerWidth()
		totalH = WikiGetResultListInnerHeight()
		slot = WIKI_CHEST_PREVIEW_SLOT_SIZE
		gap = WIKI_CHEST_PREVIEW_SLOT_GAP
		cols = WIKI_MOB_DROP_GRID_COLS
		entries = WikiCollectSortedDrops(selectedVnum, fromMob)
		rows = WIKI_MOB_DROP_GRID_ROWS
		gw = cols * slot + (cols - 1) * gap
		gh = rows * slot + (rows - 1) * gap
		leftX = 8
		previewX = leftX
		gridLeft = previewX + self.MOB_PREVIEW_W + 12 + WIKI_MOB_DROP_GRID_SHIFT_X
		pw = max(pw, gridLeft + gw + 12)
		headerH = 34
		bodyTop = headerH + 8
		contentMinH = bodyTop + max(self.MOB_PREVIEW_H, gh) + 8
		totalH = max(totalH, contentMinH)
		self.SetSize(pw, totalH)

		rowBg = ui.Bar()
		rowBg.SetParent(self)
		rowBg.SetPosition(0, 0)
		rowBg.SetSize(pw, totalH)
		rowBg.SetColor(WIKI_ROW_ZEBRA_A)
		rowBg.AddFlag("not_pick")
		rowBg.Show()
		self._children["rowZebraBg"] = rowBg
		rowLn = ui.Bar()
		rowLn.SetParent(self)
		rowLn.SetPosition(0, totalH - 1)
		rowLn.SetSize(pw, 1)
		rowLn.SetColor(WIKI_ROW_BORDER)
		rowLn.AddFlag("not_pick")
		rowLn.Show()
		self._children["rowBottomLine"] = rowLn

		hdrBg = ui.Bar()
		hdrBg.SetParent(self)
		hdrBg.SetPosition(0, 0)
		hdrBg.SetSize(pw, headerH)
		hdrBg.SetColor(WIKI_EQUIP_HEADER_BG)
		hdrBg.AddFlag("not_pick")
		hdrBg.Show()
		self._children["dropHeaderBg"] = hdrBg

		if isType == 0:
			titleTxt = localeInfo.WIKI_DROPLIST_INFO % nonplayer.GetMonsterName(selectedVnum)
			try:
				lv = nonplayer.GetMonsterLevel(selectedVnum)
				if lv > 0:
					titleTxt += "  |  Lv.%d" % lv
			except:
				pass
		else:
			item.SelectItem(selectedVnum)
			titleTxt = localeInfo.WIKI_CONTENT_INFO % item.GetItemName()

		self._children["dropTitle"] = WikiUI.CreateWindow(ui.TextLine(), self, (10, 10), titleTxt)
		try:
			self._children["dropTitle"].SetPackedFontColor(0xFFFFE8B8)
		except:
			pass

		if isType == 0:
			renderIndex = renderTarget.GetFreeIndex(1000, 1000000)
			self._children["renderIndex"] = renderIndex
			renterTarget = WikiUI.CreateWindow(WikiUI.RenderTargetNew(), self, (previewX, bodyTop), "", "", (self.MOB_PREVIEW_W, self.MOB_PREVIEW_H))
			renterTarget.SetRenderTarget(renderIndex)
			renderTarget.SetRotation(renderIndex, False)
			self._children["renterTarget"] = renterTarget
			renderTarget.SelectModel(renderIndex, selectedVnum)
			renderTarget.SetVisibility(renderIndex, True)
		else:
			item.SelectItem(selectedVnum)
			slot = WIKI_CHEST_PREVIEW_SLOT_SIZE
			ix = previewX + (self.MOB_PREVIEW_W - slot) / 2
			iy = bodyTop + (self.MOB_PREVIEW_H - slot) / 2
			slotBg = ui.ExpandedImageBox()
			slotBg.SetParent(self)
			slotBg.SetPosition(ix, iy)
			slotBg.LoadImage(WIKI_SLOT_PLATE)
			slotBg.SetSize(slot, slot)
			slotBg.AddFlag("not_pick")
			slotBg.Show()
			self._children["ownerSlotBg"] = slotBg
			itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (ix, iy), item.GetIconImageFileName())
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, selectedVnum)
			itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
			itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0, selectedVnum)
			self._children["itemIcon"] = itemIcon

		maxSlots = cols * rows
		self._gridVnums = [0] * maxSlots
		self.grid = ui.GridSlotWindow()
		self.grid.SetParent(self)
		self.grid.SetPosition(gridLeft, bodyTop)
		self.grid.ArrangeSlot(0, cols, rows, slot, slot, gap, gap)
		self.grid.SetSlotBaseImage(WIKI_SLOT_PLATE, 1.0, 1.0, 1.0, 1.0)
		for i in xrange(maxSlots):
			try:
				self.grid.ClearSlot(i)
			except:
				pass
		self.grid.SetOverInItemEvent(ui.__mem_func__(self.__OverInDropGridItem))
		self.grid.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutDropGridItem))
		self.grid.SetSelectItemSlotEvent(ui.__mem_func__(self.__OnSelectDropGridSlot))
		self.grid.Show()
		self._children["dropGrid"] = self.grid

		WikiGridFillDropSlots(self.grid, self._gridVnums, cols, rows, entries)

	def LoadItemInfos(self):
		if self.IsLoaded:
			return
		self.IsLoaded = True

		(isType, selectedVnum) = (self._children["isType"], self._children["selectedVnum"])

		if isType == 0 or isType == 3:
			self.__BuildDropGridPage(selectedVnum, isType)
			self.Show()
			return

		renderIndex = renderTarget.GetFreeIndex(1000, 1000000)
		self._children["renderIndex"] = renderIndex
		pw = WikiGetResultListInnerWidth()
		innerH = WikiGetResultListInnerHeight()
		listY = 25
		bottomPad = 10
		# Fill wiki result row height; old fixed 200 clipped Sandiklar/Canavarlar list.
		panelH = max(innerH, 1 + self.MOB_PREVIEW_H + bottomPad)
		listH = max(120, panelH - listY - bottomPad)
		WikiApplySolidBg(self, pw, panelH, WIKI_PANEL_NEUTRAL)
		self.SetSize(pw, panelH)

		item.SelectItem(selectedVnum)

		renterTarget = None
		if WikiUI.IsCanModelPreview(selectedVnum):
			renterTarget = WikiUI.CreateWindow(WikiUI.RenderTargetNew(), self, (1, 1), "", "", (self.MOB_PREVIEW_W, self.MOB_PREVIEW_H))
			renterTarget.SetRenderTarget(renderIndex)
			renderTarget.SetRotation(renderIndex, False)
			self._children["renterTarget"] = renterTarget
			WikiUI.SetItemToModelPreview(renderIndex, selectedVnum)

		if renterTarget:
			iconX = renterTarget.GetWidth() - 33 - 3
			iconY = 3
		else:
			iconX, iconY = 70, 45
		itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (iconX, iconY), item.GetIconImageFileName())
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, selectedVnum)
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
		self._children["itemIcon"] = itemIcon

		self._children["avaible"] = WikiUI.CreateWindow(ui.TextLine(), self, (350, 6), localeInfo.WIKI_AVAIBLE_AT)

		Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (190, listY), "", "", (350, listH))
		self._children["Listbox"] = Listbox

		WikiUI.PrintDrop(selectedVnum, self, Listbox)

		if Listbox.isNeedScrollBar():
			scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), Listbox, (Listbox.GetWidth()-10, 0), "", "", (8, max(40, listH - 1)))
			Listbox.SetScrollBar(scrollBar)

		if len(Listbox.itemList) > 0:
			Listbox.SetBasePos(0, False)
		self.Show()

class MonsterStatics(WikiUI.DefaultWikiImage):
	def __init__(self, mobVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["mobVnum"] = mobVnum
		self._children["isType"] = isType
		WikiApplySolidBg(self, 540, 240, WIKI_PANEL_NEUTRAL)
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True
			ListBox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (0, 0), "", "", (self.GetWidth(), self.GetHeight()-3))
			self._children["ListBox"] = ListBox
			(mobVnum, isType) = (self._children["mobVnum"], self._children["isType"])
			if isType == 3:
				WikiUI.PrintDrop(mobVnum, self, ListBox)
			elif isType == 0:
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3, True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_LEVEL_MOB_TEXT%nonplayer.GetMonsterLevel(mobVnum)))
				RACE_FLAG_TO_NAME = {
					1 << 0  : localeInfo.TARGET_INFO_RACE_ANIMAL,
					1 << 1 	: localeInfo.TARGET_INFO_RACE_UNDEAD,
					1 << 2  : localeInfo.TARGET_INFO_RACE_DEVIL,
					1 << 3  : localeInfo.TARGET_INFO_RACE_HUMAN,
					1 << 4  : localeInfo.TARGET_INFO_RACE_ORC,
					1 << 5  : localeInfo.TARGET_INFO_RACE_MILGYO,
				}
				SUB_RACE_FLAG_TO_NAME = {
					1 << 11 : localeInfo.TARGET_INFO_RACE_ELEC,
					1 << 12 : localeInfo.TARGET_INFO_RACE_FIRE,
					1 << 13 : localeInfo.TARGET_INFO_RACE_ICE,
					1 << 14 : localeInfo.TARGET_INFO_RACE_WIND,
					1 << 15 : localeInfo.TARGET_INFO_RACE_EARTH,
					1 << 16 : localeInfo.TARGET_INFO_RACE_DARK,
					1 << 17 : localeInfo.TARGET_INFO_RACE_ZODIAC,
				}
				(mainrace, subrace, dwRaceFlag) = ("", "", nonplayer.GetMonsterRaceFlag(mobVnum))

				for i in xrange(18):
					curFlag = 1 << i
					if WikiUI.IS_SET(dwRaceFlag, curFlag):
						if RACE_FLAG_TO_NAME.has_key(curFlag):
							mainrace += RACE_FLAG_TO_NAME[curFlag] + ", "
						elif SUB_RACE_FLAG_TO_NAME.has_key(curFlag):
							subrace += SUB_RACE_FLAG_TO_NAME[curFlag] + ", "

				if nonplayer.IsMonsterStone(mobVnum):
					mainrace += localeInfo.TARGET_INFO_RACE_METIN + ", "

				mainrace = localeInfo.TARGET_INFO_NO_RACE if mainrace == "" else mainrace[:-2]
				subrace = localeInfo.TARGET_INFO_NO_RACE if subrace == "" else subrace[:-2]

				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*1), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_TYPE%(mainrace, subrace)))

				(mindmg, maxdmg) = nonplayer.GetMonsterDamage(mobVnum)
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*2), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_DMG%(mindmg,maxdmg,nonplayer.GetMonsterMaxHP(mobVnum))))

				(minyang, maxyang) = nonplayer.GetMonsterPrice(mobVnum)
				exp = nonplayer.GetMonsterExp(mobVnum)
				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*3), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_YNG%(minyang, maxyang, exp)))

				ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (5, 3*(7*4), True), "|Eemoji/e_wiki|e "+localeInfo.WIKI_STATICS_INFO_DEFENSES))
				resists = {
					nonplayer.MOB_RESIST_SWORD : localeInfo.TARGET_INFO_RESIST_SWORD,
					nonplayer.MOB_RESIST_TWOHAND : localeInfo.TARGET_INFO_RESIST_TWOHAND,
					nonplayer.MOB_RESIST_DAGGER : localeInfo.TARGET_INFO_RESIST_DAGGER,
					nonplayer.MOB_RESIST_BELL : localeInfo.TARGET_INFO_RESIST_BELL,
					nonplayer.MOB_RESIST_FAN : localeInfo.TARGET_INFO_RESIST_FAN,
					nonplayer.MOB_RESIST_BOW : localeInfo.TARGET_INFO_RESIST_BOW,
					nonplayer.MOB_RESIST_MAGIC : localeInfo.TARGET_INFO_RESIST_MAGIC,
				}
				c = 0
				for resist, label in resists.items():
					ListBox.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListBox, (20, 3*(7*(5+c)), True), label % nonplayer.GetMonsterResist(mobVnum, resist)))
					c+=1
			if ListBox.isNeedScrollBar():
				ListBox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), ListBox, (ListBox.GetWidth()-10, 0, True), "", "", (8, ListBox.GetHeight()+5)))
			ListBox.Show()
			self._children["ListBox"] = ListBox
			self.Show()

class ListBoxItemSpecial(WikiUI.DefaultWikiImage):

	def __init__(self, listIndex, itemVnum, mobVnum, isType, directlyLoad = False):
		WikiUI.DefaultWikiImage.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["isType"] = isType
		self._children["itemVnum"] = itemVnum
		self._children["mobVnum"] = mobVnum
		li = listIndex
		zc = WIKI_ROW_ZEBRA_A if (li % 2) == 0 else WIKI_ROW_ZEBRA_B
		WikiApplySolidBg(self, 540, 94, zc)
		if directlyLoad:
			self.LoadItemInfos()

	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded=True

			(listIndex, isType, itemVnum, mobVnum) = (self._children["listIndex"], self._children["isType"], self._children["itemVnum"], self._children["mobVnum"])

			name = nonplayer.GetMonsterName(mobVnum if isType == 0 else itemVnum)

			if isType == 0:
				item.SelectItem(itemVnum)

			setItemName = localeInfo.WIKI_CONTENT_INFO%item.GetItemName()
			if isType != 0:
				setItemName = localeInfo.WIKI_DROPLIST_INFO%name
				setItemName += " - Level {}".format(nonplayer.GetMonsterLevel(itemVnum))
				if WikiUI.IsGameMaster():
					setItemName += " - Mob Vnum {}".format(itemVnum)

			self._children["itemName"] = WikiUI.CreateWindow(ui.TextLine(), self, (230, 5), setItemName, "horizontal:center")
			self._children["origin"] = WikiUI.CreateWindow(ui.TextLine(), self, (480, 5), localeInfo.WIKI_ORIGIN)

			needOriginListBox = True if not (isType == 0 and mobVnum != 0) and isinstance(WikiUI.GetOriginMapName(itemVnum), list) and len(WikiUI.GetOriginMapName(itemVnum)) > 4 else False 

			needAppendNames = []
			if needOriginListBox:
				nameList = WikiUI.GetOriginMapName(itemVnum)
				for originName in nameList:
					needAppendNames.append(originName)
			else:
				if isType == 0 and mobVnum != 0:
					needAppendNames.append(name[:12] + "..." if len(name) > 15 else name)
				else:
					name = WikiUI.GetOriginMapName(itemVnum)
					if isinstance(name, list):
						for originName in name:
							needAppendNames.append(originName)
					else:
						needAppendNames.append(name if name != "" else "-")

			if len(needAppendNames):
				ListboxOrigin = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (450, 25), "", "", (90, 66))
				for originName in needAppendNames:
					textPtr = WikiUI.CreateWindow(ui.TextLine(), ListboxOrigin, (0, 0), originName[:12] + "..." if len(originName) > 15 else originName, "", (-1, -1), "Tahoma:11")
					if len(needAppendNames) <= 4:
						textPtr.SetPosition(45 - (textPtr.GetTextSize()[0]/2), [25, 15, 10, 5][len(needAppendNames)-1] + ( needAppendNames.index(originName) * 13))
					else:
						textPtr.SetPosition(5, needAppendNames.index(originName) * 16, True)
					ListboxOrigin.AppendItem(textPtr)
				if ListboxOrigin.isNeedScrollBar():
					ListboxOrigin.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (450+83, 22), "", "", (8, ListboxOrigin.GetHeight())))
				self._children["ListboxOrigin"] = ListboxOrigin

			#if needOriginListBox:
			#	yPos = 0
			#	ListboxOrigin = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (450, 25), "", "", (90, 66))
			#	nameList = WikiUI.GetOriginMapName(itemVnum)
			#	for originName in nameList:
			#		ListboxOrigin.AppendItem(WikiUI.CreateWindow(ui.TextLine(), ListboxOrigin, (5, yPos, True), originName[:12] + "..." if len(originName) > 15 else originName, "horizontal:left", (-1, -1), "Tahoma:11"))
			#		yPos+=13
			#	if ListboxOrigin.isNeedScrollBar():
			#		ListboxOrigin.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (450+83, 22), "", "", (8, ListboxOrigin.GetHeight())))
			#	self._children["ListboxOrigin"] = ListboxOrigin
			#else:
			#
			#	bossVnum = WikiUI.CreateWindow(WikiUI.MultiTextLine(), self, (450, 23), "", "", (90, 66))
			#	bossVnum.SetTextRange(13)
			#	bossVnum.SetTextType("all_align#1")
			#	if isType == 0 and mobVnum != 0:
			#		bossVnum.SetText(name[:12] + "..." if len(name) > 15 else name)
			#	else:
			#		name = WikiUI.GetOriginMapName(itemVnum)
			#		if isinstance(name, list):
			#			newText = ""
			#			for tr in name:
			#				newText+=tr+"#"
			#			bossVnum.SetText(newText if newText != "" else "-")
			#			bossVnum.SetPosition(450, 22-(len(name)*4))
			#		else:
			#			bossVnum.SetText(name if name != "" else "-")
			#	self._children["bossVnum"] = bossVnum

			if isType == 0:
				itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), self, (10, 25), item.GetIconImageFileName())
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem,itemVnum)
				itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
				itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
				self._children["itemIcon"] = itemIcon

			else:
				renterTarget = WikiUI.CreateWindow(ui.RenderTarget(), self, (1, 1), "", "", (47,87))
				renterTarget.SetRenderTarget(20+listIndex)
				renterTarget.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 1, itemVnum)
				self._children["renterTarget"] = renterTarget

				renderTarget.SelectModel(20+listIndex, itemVnum)
				renderTarget.SetVisibility(20+listIndex, True)
				self._children["renderIndex"] = 20+listIndex
			whileSize = wiki.GetSpecialInfoSize(itemVnum) if isType == 0 else wiki.GetMobInfoSize(itemVnum)

			if whileSize != 0:
				Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (48, 22), "", "", (403, 65))
				fromMob = (isType != 0)
				ownerKey = itemVnum
				entries = WikiCollectSortedDrops(ownerKey, fromMob)
				gridCalculate = WikiUI.Grid(width=12, height=50)

				for (_lvl, vnum, count) in entries:
					item.SelectItem(vnum)
					(width, height) = item.GetItemSize()
					if width == 0 or height == 0:
						continue
					pos = gridCalculate.find_blank(width, height)
					if pos < 0:
						continue
					gridCalculate.put(pos, width, height)
					(x, y) = WikiUI.calculatePos(pos, 11)

					slotBg = ui.ExpandedImageBox()
					slotBg.SetParent(Listbox)
					for dy in xrange(height):
						for dx in xrange(width):
							sx = x + dx * 32
							sy = y + dy * 32
							if dx == 0 and dy == 0:
								slotBg.SetPosition(sx, sy, True)
								slotBg.LoadImage(WIKI_SLOT_PLATE)
								slotBg.SetSize(32, 32)
								slotBg.AddFlag("not_pick")
								slotBg.Show()
								Listbox.AppendItem(slotBg)
							else:
								extraBg = ui.ExpandedImageBox()
								extraBg.SetParent(Listbox)
								extraBg.SetPosition(sx, sy, True)
								extraBg.LoadImage(WIKI_SLOT_PLATE)
								extraBg.SetSize(32, 32)
								extraBg.AddFlag("not_pick")
								extraBg.Show()
								Listbox.AppendItem(extraBg)

					item_new = WikiUI.CreateWindow(ui.ExpandedImageBox(), Listbox, (x, y, True), item.GetIconImageFileName())
					item_new.SAFE_SetStringEvent("MOUSE_OVER_IN", self.OverInItem, vnum)
					item_new.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.OverOutItem)
					if isType != 0:
						item_new.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 1, itemVnum)
					else:
						item_new.SetEvent(ui.__mem_func__(self.OnClickItem), "mouse_click", 0, vnum)
					Listbox.AppendItem(item_new)

					if count > 1:
						Listbox.AppendItem(WikiUI.CreateWindow(ui.NumberLine() if USE_ITEM_COUNT_NUMBER_LINE else ui.TextLine(), Listbox, (x+15, y+item_new.GetHeight()-10, True) if USE_ITEM_COUNT_NUMBER_LINE else (x+item_new.GetWidth()-5, y+item_new.GetHeight()-10, True), str(count)))
				if Listbox.isNeedScrollBar():
					Listbox.SetScrollBar(WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (443, 23), "", "", (8, 63)))
				self._children["Listbox"] = Listbox
			self.Show()

class ArticleGUI(WikiUI.DefaultWikiWindow):
	def __init__(self, index):
		WikiUI.DefaultWikiWindow.__init__(self)
		if isinstance(index, str):
			if index.find("#") != -1:
				indexList = index.split("#")
				if len(indexList) == 2:
					self._children["index"] = int(indexList[0])
					self._children["scrollPos"] = float(indexList[1])
		else:
			self._children["index"] = index
			self._children["scrollPos"] =  0.0
		mainParent = constInfo.GetWikiInterface()
		if mainParent != None:
			self.SetSize(mainParent.children["resultpageListbox"].GetWidth(),mainParent.children["resultpageListbox"].GetHeight())
	def LoadItemInfos(self):
		if self.IsLoaded == False:
			self.IsLoaded = True
			Listbox = WikiUI.CreateWindow(WikiUI.ListBoxGrid(), self, (0,0), "", "", (self.GetWidth()-15, self.GetHeight()-15))
			self.ReadArticle(Listbox, self._children["index"])
			self.CheckScrollBarNeed(Listbox)
			self._children["Listbox"] = Listbox
			self.Show()
	def ParseToken(self, data):
		data = data.replace(chr(10), "").replace(chr(13), "")
		if not (len(data) and data[0] == "["):
			return (False, {}, data)
		fnd = data.find("]")
		if fnd <= 0:
			return (False, {}, data)
		content = data[1:fnd]
		data = data[fnd+1:]
		content = content.split(";")
		container = {}
		for i in content:
			i = i.strip()
			splt = i.split("=")
			if len(splt) == 1:
				container[splt[0].lower().strip()] = True
			else:
				#container[splt[0].lower().strip()] = splt[1].lower().strip()
				container[splt[0].lower().strip()] = splt[1].lower().strip() if splt[0].lower() != "linktext" else splt[1]
		return (True, container, data)
	def GetColorFromString(self, strCol):
		retData = []
		dNum = 4
		hCol = long(strCol, 16)
		if hCol <= 0xFFFFFF:
			retData.append(1.0)
			dNum = 3
		for i in xrange(dNum):
			retData.append(float((hCol >> (8 * i)) & 0xFF) / 255.0)
		retData.reverse()
		return retData
	def DirectionEvent(self, emptyArg, type, index, pos):
		parent = constInfo.GetWikiInterface()
		if parent != None:
			if "item" == type:
				parent.ShowItemInfo(int(index), 0)
			elif "mob" == type:
				parent.ShowItemInfo(int(index), 1)
			elif "article" == type:
				parent.ShowItemInfo("System#"+str(index)+"#"+str(pos),3)
			elif "article" == type:
				parent.ShowItemInfo("System#"+str(index)+"#"+str(pos),3)
			elif "warp" == type:
				net.SendChatPacket("/wiki_server warp {} {}".format(index, pos))
				mainParent = constInfo.GetWikiInterface()
				if mainParent:
					mainParent.Close()
			elif "website" == type:
				os.system("start \"\" {}".format(index))

	def ReadArticle(self, Listbox, index):
		fileName = WikiUI.GetArticleFileName(index)
		if fileName == "":
			return
		try:
			lines = open(fileName, "r").readlines()
		except:
			pass
		_y = 15
		for i in lines:
			(ret, tokenMap, i) = self.ParseToken(i)
			if ret:
				if tokenMap.has_key("banner_img"):
					mainParent = constInfo.GetWikiInterface()
					if mainParent != None:
						resultpagebtn = mainParent.children["resultpagebtn"]
						resultpagebtn.LoadImage(tokenMap["banner_img"])
						resultpagebtn.Show()
						tokenMap.pop("banner_img")

				if tokenMap.has_key("img"):
					cimg = ui.ExpandedImageBox()
					cimg.SetParent(Listbox)
					cimg.AddFlag("attach")
					cimg.AddFlag("not_pick")
					cimg.LoadImage(tokenMap["img"])
					cimg.Show()
					tokenMap.pop("img")
					x = 0
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					y = 0
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("center_align"):
						cimg.SetPosition(Listbox.GetWidth() / 2 - cimg.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						cimg.SetPosition(Listbox.GetWidth() - cimg.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						cimg.SetPosition(x, y, True)
					Listbox.AppendItem(cimg)

				if tokenMap.has_key("item"):
					itemVnum = int(tokenMap["item"])
					tokenMap.pop("item")

					metinSlot = [0 for j in xrange(player.METIN_SOCKET_MAX_NUM)]
					attrSlot = [[0,0] for j in xrange(player.ATTRIBUTE_SLOT_MAX_NUM)]

					if tokenMap.has_key("socket"):
						metinSlotData = tokenMap["socket"].split("#")  if tokenMap["socket"].find("#") else tokenMap["socket"]
						tokenMap.pop("socket")
						for metin in metinSlotData:
							metinSplit = metin.split(":")
							if len(metinSplit) != 2:
								continue
							metinSlot[int(metinSplit[0])] = int(metinSplit[1])

					if tokenMap.has_key("attr"):
						attrSlotData = tokenMap["attr"].split("#") if tokenMap["attr"].find("#") else tokenMap["attr"]
						tokenMap.pop("attr")

						for attr in attrSlotData:
							attrSplit = attr.split(":")
							if len(attrSplit) != 2:
								continue
							attrDataSplit = attrSplit[1].split("?")
							if len(attrDataSplit) != 2:
								continue
							attrSlot[int(attrSplit[0])] = [int(attrDataSplit[0]), int(attrDataSplit[1])]

					for k in xrange(player.ATTRIBUTE_SLOT_MAX_NUM):
						attrSlot[k] = tuple(attrSlot[k])

					item.SelectItem(itemVnum)
					cimg = ui.ExpandedImageBox()
					cimg.SetParent(Listbox)
					if item.GetIconImageFileName().find("gr2") == -1:
						cimg.LoadImage(item.GetIconImageFileName())
					else:
						cimg.LoadImage("icon/item/27995.tga")
					cimg.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItem, itemVnum, metinSlot, attrSlot)
					cimg.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
					cimg.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click",0,itemVnum)
					cimg.Show()
					x = 0
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					y = 0
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("center_align"):
						cimg.SetPosition(Listbox.GetWidth() / 2 - cimg.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						cimg.SetPosition(Listbox.GetWidth() - cimg.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						cimg.SetPosition(x, y, True)

					Listbox.AppendItem(cimg)

				if tokenMap.has_key("link"):
					link = tokenMap["link"].split("#")
					tokenMap.pop("link")
					if len(link) != 3:
						continue

					if tokenMap.has_key("text"):
						#linkText = WikiUI.GetArgToString(tokenMap["text"])
						linkText =tokenMap["text"]
						tokenMap.pop("text")
					else:
						linkText = ""

					tmp = WikiUI.TextlineLink()
					tmp.SetParent(Listbox)
					if tokenMap.has_key("font_size"):
						splt = localeInfo.UI_DEF_FONT.split(":")
						tmp.SetFontName(splt[0]+":"+tokenMap["font_size"])
						tokenMap.pop("font_size")
					else:
						tmp.SetFontName(localeInfo.UI_DEF_FONT)

					linkText = linkText.replace("*", "|Eemoji/e_wiki|e")

					#tmp.SetText(WikiUI.GetArgToString(linkText), 1.2)
					tmp.SetText(linkText, 1.2)
					tmp.Show()
					if tokenMap.has_key("color"):
						fontColor = self.GetColorFromString(tokenMap["color"])
						tmp.SetColor(grp.GenerateColor(fontColor[0], fontColor[1], fontColor[2], fontColor[3]), fontColor[0], fontColor[1], fontColor[2])
						tokenMap.pop("color")
					tmp.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.DirectionEvent), "", link[0], link[1],link[2])
					tmp.linkIcon.SetMouseLeftButtonDownEvent(ui.__mem_func__(self.DirectionEvent),"", link[0], link[1], link[2])
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")						
					if tokenMap.has_key("center_align"):
						tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

				if tokenMap.has_key("rendertarget"):
					mobVnum = int(tokenMap["rendertarget"])
					tokenMap.pop("rendertarget")

					(width, height) = (47, 87)

					if tokenMap.has_key("width"):
						width = int(tokenMap["width"])
						tokenMap.pop("width")

					if tokenMap.has_key("height"):
						height = int(tokenMap["height"])
						tokenMap.pop("height")

					targetIndex = renderTarget.GetFreeIndex(1000, 1000000)
					tmp = WikiUI.RenderTargetNew()
					tmp.SetParent(Listbox)
					tmp.SetSize(width, height)
					tmp.SetRenderTarget(targetIndex)
					renderTarget.SetRotation(targetIndex, False)
					tmp.SetEvent(ui.__mem_func__(self.DirectionEvent),"mouse_click", "mob", mobVnum, 0)
					tmp.Show()
					
					
					if tokenMap.has_key("movable"):
						if int(tokenMap["movable"]):
							tmp.AddFlag("movable")
						tokenMap.pop("movable")

					renderTarget.SelectModel(targetIndex, mobVnum)
					renderTarget.SetVisibility(targetIndex, True)
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")						
					if tokenMap.has_key("center_align"):
						tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)
				
				if tokenMap.has_key("button"):
					button = tokenMap["button"].split("#")
					tokenMap.pop("button")
					if len(button) != 3:
						continue

					tmp = ui.Button()
					tmp.SetParent(Listbox)
					tmp.SetUpVisual(button[0])
					tmp.SetOverVisual(button[1])
					tmp.SetDownVisual(button[2])
					tmp.Show()
					if tokenMap.has_key("linkindex"):
						try:
							linkindex = tokenMap["linkindex"].split("#")
							if len(linkindex) == 3:
								tmp.SAFE_SetEvent(self.DirectionEvent, "", linkindex[0], linkindex[1], linkindex[2])
						except:
							pass
						tokenMap.pop("linkindex")
					if tokenMap.has_key("text"):
						tmp.SetText(tokenMap["text"])
						tokenMap.pop("text")
					if tokenMap.has_key("y"):
						y = int(tokenMap["y"])
						tokenMap.pop("y")
					if tokenMap.has_key("x"):
						x = int(tokenMap["x"])
						tokenMap.pop("x")
					if tokenMap.has_key("center_align"):
						tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, y, True)
						tokenMap.pop("center_align")
					elif tokenMap.has_key("right_align"):
						tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), y, True)
						tokenMap.pop("right_align")
					else:
						tmp.SetPosition(x, y, True)
					Listbox.AppendItem(tmp)

			if ret and not len(i):
				continue

			i = i.replace("*", "|Eemoji/e_wiki|e")
			tmp = ui.TextLine()
			tmp.SetParent(Listbox)
			if tokenMap.has_key("font_size"):
				splt = localeInfo.UI_DEF_FONT.split(":")
				tmp.SetFontName(splt[0]+":"+tokenMap["font_size"])
				tokenMap.pop("font_size")
			else:
				tmp.SetFontName(localeInfo.UI_DEF_FONT)
			tmp.SetText(WikiUI.GetArgToString(i))
			tmp.Show()
			tmp.SetSize(*tmp.GetTextSize())

			if tokenMap.has_key("color"):
				fontColor = self.GetColorFromString(tokenMap["color"])
				tmp.SetPackedFontColor(grp.GenerateColor(fontColor[0], fontColor[1], fontColor[2], fontColor[3]))
				tokenMap.pop("color")

			tmp.SetPosition(5, _y, True)
			_y+=tmp.GetHeight()

			if tokenMap.has_key("center_align"):
				tmp.SetPosition(Listbox.GetWidth() / 2 - tmp.GetWidth() / 2, tmp.GetLocalPosition()[1], True)
				tokenMap.pop("center_align")
			elif tokenMap.has_key("right_align"):
				tmp.SetPosition(Listbox.GetWidth() - tmp.GetWidth(), tmp.GetLocalPosition()[1], True)
				tokenMap.pop("right_align")
			elif tokenMap.has_key("x_padding"):
				tmp.SetPosition(int(tokenMap["x_padding"]), tmp.GetLocalPosition()[1], True)
				tokenMap.pop("x_padding")
			tmp.Show()
			Listbox.AppendItem(tmp)

	def CheckScrollBarNeed(self, Listbox):
		if Listbox.isNeedScrollBar():
			scrollBar = WikiUI.CreateWindow(WikiUI.ScrollBarSpecial(), self, (self.GetWidth()-8, 2), "", "", (8, self.GetHeight() - 15))
			scrollBar.SetPos(self._children["scrollPos"])
			Listbox.SetScrollBar(scrollBar)
			Listbox.OnScroll()

class SpecialClass(WikiUI.DefaultWikiWindow):
	def __init__(self, listIndex, isMonster):
		WikiUI.DefaultWikiWindow.__init__(self)
		self._children["listIndex"] = listIndex
		self._children["vnumList"] = []
		self._children["renderIndex"] = -1
		self.SetSize(540, 147)  # MANUEL: SpecialClass (kostum grid) pencere boyutu
	
	def CanAddNewItem(self):
		return len(self._children["vnumList"]) < 4

	def LoadItemInfos(self, data = -1):
		if data == -1:
			return
		xPos = len(self._children["vnumList"]) * (127+9)  # MANUEL: kostum hucresi yatay aralik (127 genislik + 9 bosluk)

		idx = len(self._children["vnumList"])
		zc = WIKI_ROW_ZEBRA_A if (idx % 2) == 0 else WIKI_ROW_ZEBRA_B
		bg = ui.Bar()
		bg.SetParent(self)
		bg.SetPosition(xPos, 0)
		bg.SetSize(127, 127)
		bg.SetColor(zc)
		bg.AddFlag("not_pick")
		bg.Show()
		self._children["bg{}".format(data)] = bg

		item.SelectItem(data)
		itemIcon = WikiUI.CreateWindow(ui.ExpandedImageBox(), bg, (-1, -1), item.GetIconImageFileName())
		itemIcon.SetPosition((bg.GetWidth()/2)-(itemIcon.GetWidth()/2), ((bg.GetHeight()-20)/2)-(itemIcon.GetHeight()/2))  # MANUEL: ikon hucere icinde ortala (-20 alt bosluk metin icin)
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInItemSpecial, data)
		itemIcon.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutItem)
		itemIcon.SetEvent(ui.__mem_func__(self.OnClickItem),"mouse_click", 0, data)
		self._children["itemIcon{}".format(data)] = itemIcon
		self._children["itemName{}".format(data)] = WikiUI.CreateWindow(ui.TextLine(), self, (len(self._children["vnumList"]) * (127+9)+(bg.GetWidth()/2), bg.GetHeight()-18), item.GetItemName(), "horizontal:center")
		self._children["vnumList"].append(data)
		self.Show()

	def OverOutItem(self):
		renderIndex = self._children["renderIndex"]
		if renderIndex != -1:
			renderTarget.SetVisibility(renderIndex, False)
			renderTarget.ResetModel(renderIndex)
		WikiUI.DefaultWikiWindow.OverOutItem(self)

	def OverInItemSpecial(self, itemVnum):
		interface = constInfo.GetInterfaceInstance()
		if interface:
			tooltipItem = interface.tooltipItem
			if tooltipItem:
				tooltipItem.ClearToolTip()

				renderIndex = renderTarget.GetFreeIndex(1000, 1000000)
				self._children["renderIndex"] = renderIndex

				tooltipItem.toolTipWidth -= 35

				renterTarget = WikiUI.CreateWindow(ui.RenderTarget(), tooltipItem, (10, 5), "", "", (tooltipItem.toolTipWidth-20, 150))
				renterTarget.SetRenderTarget(renderIndex)
				tooltipItem.childrenList.append(renterTarget)

				tooltipItem.toolTipHeight += 150
				tooltipItem.ResizeToolTip()
				tooltipItem.SetItemToolTipWiki(itemVnum)
				WikiUI.SetItemToModelPreview(renderIndex, itemVnum)

# Forks that still do "import uiWiki" get this module (class EncyclopediaofGame lives here).
import sys as __wiki_sys_alias_mod
if __name__ and __wiki_sys_alias_mod.modules.get(__name__) is not None:
	__wiki_sys_alias_mod.modules["uiWiki"] = __wiki_sys_alias_mod.modules[__name__]
