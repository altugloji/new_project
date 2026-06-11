import ui
import localeInfo
import player
import eventManager
import colorInfo

EVENT_OPEN_ATTRIBUTE_LIST = "EVENT_OPEN_ATTRIBUTE_LIST" # | args: None


def _pts(*names):
	# Resolve point names to their numeric ids, skipping any that this client
	# build does not provide (so the window never fails on a missing POINT_*).
	result = []
	for name in names:
		value = getattr(player, name, None)
		if value is not None:
			result.append(value)
	return result


CATEGORY_SORT_ORDER = [
	"DEFENSIVE_PLAYER",
	"OFFENSIVE",
	"OFFENSIVE_MONSTER",
	"OFFENSIVE_PLAYER",
	"DEFENSIVE",
	"OTHER",
]

ATTRIBUTE_LIST = {
	"DEFENSIVE_PLAYER": {
		"locale": localeInfo.ATTRIBUTE_LIST_DEFENSIVE_PLAYER,
		"attr_list": _pts(
			"POINT_ATTBONUS_HUMAN",
			# "POINT_RESIST_HUMAN",
			# "POINT_RESIST_WARRIOR",
			# "POINT_RESIST_ASSASSIN",
			# "POINT_RESIST_SURA",
			# "POINT_RESIST_SHAMAN",
			"POINT_RESIST_SWORD",
			"POINT_RESIST_TWOHAND",
			"POINT_RESIST_DAGGER",
			"POINT_RESIST_BELL",
			"POINT_RESIST_FAN",
			"POINT_RESIST_BOW",
			"POINT_RESIST_MAGIC",
		),
	},

	"OFFENSIVE": {
		"locale": localeInfo.ATTRIBUTE_LIST_OFFENSIVE,
		"attr_list": _pts(
			"POINT_CRITICAL_PCT",
			"POINT_PENETRATE_PCT",
			"POINT_POISON_PCT",
			"POINT_STUN_PCT",
			"POINT_SLOW_PCT",
			"POINT_SKILL_DAMAGE_BONUS",
			"POINT_NORMAL_HIT_DAMAGE_BONUS",
			"POINT_REFLECT_MELEE",
			"POINT_REFLECT_ARROW",
		),
	},

	"OFFENSIVE_MONSTER": {
		"locale": localeInfo.ATTRIBUTE_LIST_OFFENSIVE_MONSTER,
		"attr_list": _pts(
			"POINT_ATTBONUS_ANIMAL",
			"POINT_ATTBONUS_ORC",
			"POINT_ATTBONUS_MILGYO",
			"POINT_ATTBONUS_UNDEAD",
			"POINT_ATTBONUS_DEVIL",
			"POINT_ATTBONUS_STONE",
			"POINT_ATTBONUS_BOSS",
			"POINT_ATTBONUS_CZ",
			"POINT_ENCHANT_DARK",
			"POINT_RESIST_FIRE",
			"POINT_RESIST_WIND",
			"POINT_RESIST_ELEC",
		),
	},

	"OFFENSIVE_PLAYER": {
		"locale": localeInfo.ATTRIBUTE_LIST_OFFENSIVE_PLAYER,
		"attr_list": _pts(
			"POINT_ATTBONUS_WARRIOR",
			"POINT_ATTBONUS_ASSASSIN",
			"POINT_ATTBONUS_SURA",
			"POINT_ATTBONUS_SHAMAN",
		),
	},

	"DEFENSIVE": {
		"locale": localeInfo.ATTRIBUTE_LIST_DEFENSIVE,
		"attr_list": _pts(
			# "POINT_SKILL_DEFEND_BONUS",
			# "POINT_NORMAL_HIT_DEFEND_BONUS",
			# "POINT_RESIST_CRITICAL",
			# "POINT_RESIST_PENETRATE",
			"POINT_BLOCK",
			"POINT_DODGE",
			"POINT_POISON_REDUCE",
		),
	},

	"OTHER": {
		"locale": localeInfo.ATTRIBUTE_LIST_OTHER,
		"attr_list": _pts(
			"POINT_STEAL_HP",
			"POINT_STEAL_SP",
			"POINT_MANA_BURN_PCT",
			"POINT_HP_REGEN",
			"POINT_SP_REGEN",
			"POINT_ST_REGEN",
			"POINT_SKILL_DURATION",
		),
	},
}

def GetAttributeName(attr_index, value):
	return localeInfo.GetApplyString(attr_index, value)

class AttributeListWindow(ui.ScriptWindow):
	class AttrItem(ui.TextValueBar):
		def __init__(self, attr_index, is_perc_val):
			self.attr_index = attr_index
			self.is_perc_val = is_perc_val
			ui.TextValueBar.__init__(self, self.GetAttrName(), self.GetValueText(0), 318, 20)
			self.Show()

		def __del__(self):
			ui.TextValueBar.__del__(self)

		def GetAttrName(self):
			temp_name = GetAttributeName(self.attr_index, 999)
			temp_name = temp_name.replace("999", "")
			temp_name = temp_name.replace("+", "")
			temp_name = temp_name.replace("-", "")
			temp_name = temp_name.replace(":", "")

			if self.attr_index not in (player.POINT_STEAL_HP, player.POINT_STEAL_SP):
				temp_name = temp_name.replace("% ", "")
				temp_name = temp_name.replace(" %", "")
			return temp_name

		def GetValueText(self, attr_value):
			if self.is_perc_val:
				return "%d%%" % attr_value
			else:
				return "%d" % attr_value

		def SetValue(self, value):
			self.SetValueLabel(self.GetValueText(value))

			color = colorInfo.DISABLED_FONT_COLOR
			if value > 0:
				color = colorInfo.POSITIVE_COLOR
			elif value < 0:
				color = colorInfo.NEGATIVE_COLOR

			self.title.SetPackedFontColor(color)
			self.value.SetPackedFontColor(color)

		def RefreshStatus(self):
			val = player.GetStatus(self.attr_index)
			self.SetValue(val)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.LoadDialog()

		eventManager.EventManager().add_observer(EVENT_OPEN_ATTRIBUTE_LIST, self.Open)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.categoryList = []
		self.attrItemList = []

	@ui.WindowDestroy
	def Destroy(self):
		self.ClearDictionary()
		self.__Initialize()

	def LoadDialog(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/attributelistwindow.py")

			self.board = self.GetChild("Board")
			self.content = self.GetChild("ContentWindow")
			self.mask = self.GetChild("ContentMask")
			self.titleBar = self.GetChild("TitleBar")
			self.scrollBar = self.GetChild("ScrollBar")

			self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))

			self.scrollBar.SetScrollContent(self.mask, self.content)
			self.scrollBar.SAFE_SetOnWheelEvent(self.content)

			for category in CATEGORY_SORT_ORDER:
				data = ATTRIBUTE_LIST[category]
				if not data["attr_list"]:
					continue
				self.__AddCategory(data["locale"])
				for attr_index in data["attr_list"]:
					self.__AddAttr(attr_index)

		except:
			import exception
			exception.Abort("AttributeListWindow.LoadDialog.BindObject")

	def __AddCategory(self, category_name):
		category = ui.HorizontalBarTitle(318, category_name)
		category.SetParent(self.content)
		category.SetPosition(8, 0)
		category.title.SetWindowHorizontalAlignCenter()
		category.title.SetHorizontalAlignCenter()
		category.title.SetPosition(0, 0)
		category.Show()
		self.__AddContentItem(category)
		self.categoryList.append(category)
		return category

	def __AddAttr(self, attr_index):
		is_perc_value = GetAttributeName(attr_index, 1).find('%')
		attrItem = self.AttrItem(attr_index, is_perc_value)
		attrItem.SetParent(self.content)
		attrItem.SetPosition(8, 0)
		attrItem.SetBarBackground(len(self.attrItemList) % 2 == 0)
		self.__AddContentItem(attrItem)
		self.attrItemList.append(attrItem)
		return attrItem

	def __AddContentItem(self, item):
		x, y = item.GetLocalPosition()
		item.SetPosition(x, self.content.GetHeight())
		self.content.SetSize(self.content.GetWidth(), self.content.GetHeight() + item.GetHeight())
		item.SetClippingMaskWindow(self.mask)
		self.scrollBar.ResizeScrollBar()

	def RefreshStatus(self): # binary call
		for i in self.attrItemList:
			i.RefreshStatus()

	def OnMouseWheel(self, delta):
		scrollBar = getattr(self, "scrollBar", None)
		if scrollBar and scrollBar.IsShow():
			wheel = getattr(scrollBar, "OnMouseWheel", None)
			if wheel:
				return wheel(delta)
		return False

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Close(self):
		self.Hide()

	def Open(self):
		if self.IsShow():
			self.Close()
		else:
			self.Show()
			self.SetTop()
