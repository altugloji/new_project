import uiScriptLocale

# --- Cube UI ayar rehberi (boyut / konum) ---
# Scrollbar (kayd?rma):
#   A?a??da "contentScrollbar" s?zl???: "x" = sa?dan i?eri ofset (horizontal_align "right" iken),
#   Daha sa?a (d?? kenara): x k???lt; daha sola (i?eri): x b?y?t.
#   "y" = dikey konum (RECIPE_LIST_TOP_Y ile ayn? hizada), "size" = scrollbar piksel y?ksekli?i.
#   Liste alan?n?n y?ksekli?i: RECIPE_LIST_HEIGHT (sat?r y?ksekli?i * sat?r say?s?).
#
# Ye?il se?im bar? (Highlight):
#   _recipe_row() i?indeki "%sHighlight" bar: "x","y" = sat?r penceresine g?re (y i?in RECIPE_ROW_BG_BAR_Y),
#   "width" = RECIPE_ROW_W - HIGHLIGHT_BAR_SHRINK, "height" = RECIPE_ROW_BG_BAR_H,
#   "color" = 0xAARRGGBB (ye?il ton).
#   Sadece geni?li?i k?saltmak i?in: HIGHLIGHT_BAR_SHRINK sabitini de?i?tir.
#
# Sat?r zebra arka plan? (RowStripe):
#   Her sat?rda Highlight'tan ?nce tam geni?likte "%sRowStripe" bar; y / height = RECIPE_ROW_BG_BAR_Y / RECIPE_ROW_BG_BAR_H.
#   Renkler s?rayla ROW_STRIPE_HEX_A (#181717) ve ROW_STRIPE_HEX_B (#0f0f0e); tek/?ift sat?rda alternatif.
#   ?izim s?ras?: ?nce RowStripe (arkada), sonra Highlight, sonra slotlar ? se?ili de?ilken Highlight gizli (uicuberenewal).
#
# Yang (GoldCircle) ve ?ans (LuckCircle) kutular?:
#   Geni?lik/y?kseklik: ECON_COL_W, ECON_STRIP_H (her iki ?erit ayn? y?kseklik).
#   Sat?rdaki yatay konum: ECON_COL_X (rehber: RECIPE_ROW_W - s?tun - bo?luk; gerekirse form?l? de?i?tir).
#   Sat?rdaki dikey ba?lang??: ECON_STRIP_ROW_Y (GoldCircle "y"); ?ans: ECON_STRIP_ROW_Y + ECON_STRIP_H + 4.
#   ??erideki yang ikonu: "%sGoldIcon" x, y, x_scale, y_scale.
#   Yaz?lar: "%sGoldText" ve "%sPercentText" x, y, hizalama.
# ---

ICON_SLOT_FILE = "d:/ymir work/ui/public/Slot_Base.sub"
# ?retilecek sonu? item slotu (sadece recipeRowNResult)
CUBE_RESULT_SLOT_FILE = "d:/ymir work/ui/game/cube/gold_slot.png"
MONEY_ICON = "d:/ymir work/ui/game/windows/money_icon.sub"
SMALL_BTN = "d:/ymir work/ui/public/small_button_0%d.sub"

# Slot art ~32px; step must be >= 32.
MAT_STEP_X = 32
MAT_STEP_Y = 32
ROW_HEIGHT = 78
VISIBLE_RECIPE_COUNT = 6
RECIPE_LIST_HEIGHT = ROW_HEIGHT * VISIBLE_RECIPE_COUNT

# Scrollbar ta?mas?n? azaltmak i?in tahta biraz geni? (+5 px sol geni?leme)
BOARD_W = 445
TITLE_BOTTOM_Y = 38
RECIPE_LIST_TOP_Y = TITLE_BOTTOM_Y

# Se?ili sat?r ye?il bar?: geni?lik = RECIPE_ROW_W - bu de?er (k???lt ? ye?il bar geni?ler)
HIGHLIGHT_BAR_SHRINK = 19
# Zebra + ye?il barlar?n sat?r i?inde ?stten ofseti (px a?a??); y?kseklik sat?ra s??s?n diye k?salt?l?r
RECIPE_ROW_BG_BAR_Y = 2
RECIPE_ROW_BG_BAR_H = ROW_HEIGHT - RECIPE_ROW_BG_BAR_Y

# Liste sat?r? zebra zemini (0xAARRGGBB)
ROW_STRIPE_HEX_A = 0xFF181717  # #181717
ROW_STRIPE_HEX_B = 0xFF0F0F0E  # #0f0f0e

SEARCH_BG_X = 14
SEARCH_BAR_Y = RECIPE_LIST_TOP_Y + RECIPE_LIST_HEIGHT + 8

SEARCH_BAR_W = 420
SEARCH_BAR_H = 25
# Alt b?l?m: miktar (+/-), geli?tirme slotu ve butonlar i?in tahta y?ksekli?i
CRAFT_ROW_Y = SEARCH_BAR_Y + SEARCH_BAR_H + 6

# YENI: Beceri kitabi grid alani (cube uretiminde kullanilacak kitaplar buraya secilir)
# 13 sutun x 2 satir = 26 slot. Slot sayisi degisecekse SKILL_GRID_COLS/ROWS guncelle ve
# uicuberenewal.py icindeki CUBE_SKILL_GRID_MAX (= COLS*ROWS) ile ayni olacak sekilde tut.
SKILL_GRID_COLS = 13
SKILL_GRID_ROWS = 2
SKILL_GRID_X = 15
SKILL_LABEL_Y = CRAFT_ROW_Y + 45
SKILL_GRID_Y = SKILL_LABEL_Y + 18
SKILL_GRID_W = SKILL_GRID_COLS * MAT_STEP_X
SKILL_GRID_H = SKILL_GRID_ROWS * MAT_STEP_Y

# Pencere VARSAYILAN (orijinal/kucuk) yukseklik: 20001 DISINDAKI NPC'lerde bu kullanilir.
# Sadece 20001'de python (uicuberenewal.SetSkillGridEnable) pencereyi BOARD_H_BIG'e buyutur.
BOARD_H_SMALL = 633
BOARD_H_BIG = SKILL_GRID_Y + SKILL_GRID_H + 50
BOARD_H = BOARD_H_SMALL
PATTERN_PATH = "d:/ymir work/ui/pattern/"
# base_pattern (lootingsystem.py ile ayni 9-parca border_A); board zeminin uzerinde, icerik altinda
BASE_PATTERN_X = 5
BASE_PATTERN_Y = TITLE_BOTTOM_Y - 10
BASE_PATTERN_BOTTOM_MARGIN = 42
PATTERN_WINDOW_WIDTH = BOARD_W - (BASE_PATTERN_X * 2)
PATTERN_WINDOW_HEIGHT = BOARD_H - BASE_PATTERN_Y - BASE_PATTERN_BOTTOM_MARGIN
PATTERN_X_COUNT = (PATTERN_WINDOW_WIDTH - 32) / 16
PATTERN_Y_COUNT = (PATTERN_WINDOW_HEIGHT - 32) / 16
ECON_STRIP_H = 20
RECIPE_ROW_W = BOARD_W - 24
# Yang/?ans kutular?: yatay ECON_COL_X, geni?lik ECON_COL_W, ?erit y?ksekli?i ECON_STRIP_H
ECON_COL_W = 82
ECON_COL_X = RECIPE_ROW_W - ECON_COL_W - 4 - 19
# Yang + ?ans ?eritlerinin sat?r i?inde ?stten konumu (_recipe_row i?inde GoldCircle/LuckCircle "y")
ECON_STRIP_ROW_Y = 20


def _recipe_row(prefix, y):
	row_index = int(prefix[-1]) - 1
	stripe_color = ROW_STRIPE_HEX_A if row_index % 2 == 0 else ROW_STRIPE_HEX_B
	return {
			"name" : "%sBoard" % prefix,
			"type" : "window",
			"x" : 0,
			"y" : y,
			"width" : RECIPE_ROW_W,
			"height" : ROW_HEIGHT,
			"children" :
			(
				{
					"name" : "%sRowStripe" % prefix,
					"type" : "bar",
					"x" : 0,
					"y" : RECIPE_ROW_BG_BAR_Y,
					"width" : RECIPE_ROW_W,
					"height" : RECIPE_ROW_BG_BAR_H,
					"color" : stripe_color,
				},
				{
					"name" : "%sHighlight" % prefix,
					"type" : "bar",
					"x" : 0,
					"y" : RECIPE_ROW_BG_BAR_Y,
					"width" : RECIPE_ROW_W - HIGHLIGHT_BAR_SHRINK,
					"height" : RECIPE_ROW_BG_BAR_H,
					"color" : 0x7700DDAA,
				},
				{
					"name" : "%sResult" % prefix,
					"type" : "grid_table",
					"x" : 6,
					"y" : 14,
					"start_index" : 0,
					"x_count" : 1,
					"y_count" : 1,
					"x_step" : MAT_STEP_X,
					"y_step" : MAT_STEP_Y,
					"image" : CUBE_RESULT_SLOT_FILE,
				},
				{
					"name" : "%sArrow" % prefix,
					"type" : "text",
					"x" : 52,
					"y" : 28,
					"text" : "<",
				},
				{
					"name" : "%sMaterials" % prefix,
					"type" : "grid_table",
					"x" : 68,
					"y" : 10,
					"start_index" : 0,
					"x_count" : 7,
					"y_count" : 2,
					"x_step" : MAT_STEP_X,
					"y_step" : MAT_STEP_Y,
					"image" : ICON_SLOT_FILE,
				},
				{
					"name" : "%sGoldCircle" % prefix,
					"type" : "thinboard_circle",
					"style" : ("attach",),
					"x" : ECON_COL_X,
					"y" : ECON_STRIP_ROW_Y,
					"width" : ECON_COL_W,
					"height" : ECON_STRIP_H,
					"children" :
					(
						{
							"name" : "%sGoldIcon" % prefix,
							"type" : "expanded_image",
							"x" : 6,
							"y" : 7,
							"x_scale" : 0.4,
							"y_scale" : 0.4,
							"image" : MONEY_ICON,
						},
						{
							"name" : "%sGoldText" % prefix,
							"type" : "text",
							"x" : 6,
							"y" : 4,
							"horizontal_align" : "right",
							"text_horizontal_align" : "right",
							"text" : "0",
						},
					),
				},
				{
					"name" : "%sLuckCircle" % prefix,
					"type" : "thinboard_circle",
					"style" : ("attach",),
					"x" : ECON_COL_X,
					"y" : ECON_STRIP_ROW_Y + ECON_STRIP_H + 4,
					"width" : ECON_COL_W,
					"height" : ECON_STRIP_H,
					"children" :
					(
						{
							"name" : "%sPercentText" % prefix,
							"type" : "text",
							"x" : 6,
							"y" : 4,
							"horizontal_align" : "right",
							"text_horizontal_align" : "right",
							"text" : "100%",
						},
					),
				},
			),
	}

def _base_pattern():
	return {
		"name" : "base_pattern",
		"type" : "window",
		"style" : ("attach", "ltr",),
		"x" : BASE_PATTERN_X,
		"y" : BASE_PATTERN_Y,
		"width" : PATTERN_WINDOW_WIDTH,
		"height" : PATTERN_WINDOW_HEIGHT,
		"children" :
		(
			{
				"name" : "pattern_left_top_img",
				"type" : "image",
				"style" : ("ltr",),
				"x" : 0,
				"y" : 0,
				"image" : PATTERN_PATH + "border_A_left_top.tga",
			},
			{
				"name" : "pattern_right_top_img",
				"type" : "image",
				"style" : ("ltr",),
				"x" : PATTERN_WINDOW_WIDTH - 16,
				"y" : 0,
				"image" : PATTERN_PATH + "border_A_right_top.tga",
			},
			{
				"name" : "pattern_left_bottom_img",
				"type" : "image",
				"style" : ("ltr",),
				"x" : 0,
				"y" : PATTERN_WINDOW_HEIGHT - 16,
				"image" : PATTERN_PATH + "border_A_left_bottom.tga",
			},
			{
				"name" : "pattern_right_bottom_img",
				"type" : "image",
				"style" : ("ltr",),
				"x" : PATTERN_WINDOW_WIDTH - 16,
				"y" : PATTERN_WINDOW_HEIGHT - 16,
				"image" : PATTERN_PATH + "border_A_right_bottom.tga",
			},
			{
				"name" : "pattern_top_cetner_img",
				"type" : "expanded_image",
				"style" : ("ltr",),
				"x" : 16,
				"y" : 0,
				"image" : PATTERN_PATH + "border_A_top.tga",
				"rect" : (0.0, 0.0, PATTERN_X_COUNT, 0),
			},
			{
				"name" : "pattern_left_center_img",
				"type" : "expanded_image",
				"style" : ("ltr",),
				"x" : 0,
				"y" : 16,
				"image" : PATTERN_PATH + "border_A_left.tga",
				"rect" : (0.0, 0.0, 0, PATTERN_Y_COUNT),
			},
			{
				"name" : "pattern_right_center_img",
				"type" : "expanded_image",
				"style" : ("ltr",),
				"x" : PATTERN_WINDOW_WIDTH - 16,
				"y" : 16,
				"image" : PATTERN_PATH + "border_A_right.tga",
				"rect" : (0.0, 0.0, 0, PATTERN_Y_COUNT),
			},
			{
				"name" : "pattern_bottom_center_img",
				"type" : "expanded_image",
				"style" : ("ltr",),
				"x" : 16,
				"y" : PATTERN_WINDOW_HEIGHT - 16,
				"image" : PATTERN_PATH + "border_A_bottom.tga",
				"rect" : (0.0, 0.0, PATTERN_X_COUNT, 0),
			},
			{
				"name" : "pattern_center_img",
				"type" : "expanded_image",
				"style" : ("ltr",),
				"x" : 16,
				"y" : 16,
				"image" : PATTERN_PATH + "border_A_center.tga",
				"rect" : (0.0, 0.0, PATTERN_X_COUNT, PATTERN_Y_COUNT),
			},
		),
	}

window = {
	"name" : "CubeWindow",

	"x" : SCREEN_WIDTH - BOARD_W - 40,
	# Konumu BUYUK boyuta gore ayarla ki 20001'de pencere asagi buyuyunce ekran disina tasmasin.
	"y" : SCREEN_HEIGHT - BOARD_H_BIG - 40,

	"style" : ("movable", "float",),

	"width" : BOARD_W,
	"height" : BOARD_H,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : BOARD_W,
			"height" : BOARD_H,

			"children" :
			(
				_base_pattern(),
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),
					"x" : 6,
					"y" : 6,
					"width" : BOARD_W - 12,
					"color" : "yellow",
					"children" :
					(
						{
							"name" : "TitleName",
							"type" : "text",
							"x" : (BOARD_W - 12) / 2,
							"y" : 3,
							"text" : uiScriptLocale.CUBE_TITLE,
							"text_horizontal_align" : "center",
						},
					),
				},

				{
					"name" : "recipeListArea",
					"type" : "window",
					"x" : 10,
					"y" : RECIPE_LIST_TOP_Y,
					"width" : RECIPE_ROW_W,
					"height" : RECIPE_LIST_HEIGHT,
					"children" :
					(
						_recipe_row("recipeRow1", 0),
						_recipe_row("recipeRow2", ROW_HEIGHT),
						_recipe_row("recipeRow3", ROW_HEIGHT * 2),
						_recipe_row("recipeRow4", ROW_HEIGHT * 3),
						_recipe_row("recipeRow5", ROW_HEIGHT * 4),
						_recipe_row("recipeRow6", ROW_HEIGHT * 5),
					),
				},

				{
					# Scrollbar: x,y,size ? y ve size listeyi sat?rla hizalar
					"name" : "contentScrollbar",
					"type" : "scrollbar",
					"x" : 27,
					"y" : RECIPE_LIST_TOP_Y,
					"size" : RECIPE_LIST_HEIGHT,
					"horizontal_align" : "right",
				},

				{
					"name" : "searchBackground",
					"type" : "thinboard_circle",
					"style" : ("attach",),
					"x" : SEARCH_BG_X,
					"y" : SEARCH_BAR_Y,
					"width" : SEARCH_BAR_W,
					"height" : SEARCH_BAR_H,
				},
				{
					"name" : "searchPlaceholder",
					"type" : "text",
					"x" : SEARCH_BG_X + 10,
					"y" : SEARCH_BAR_Y + 5,
					"text" : "Ara...",
					"r" : 0.55,
					"g" : 0.55,
					"b" : 0.55,
				},
				{
					"name" : "searchEdit",
					"type" : "editline",
					"x" : SEARCH_BG_X + 10,
					"y" : SEARCH_BAR_Y + 5,
					"width" : SEARCH_BAR_W - 62,
					"height" : 16,
					"input_limit" : 32,
				},
				{
					"name" : "searchClearButton",
					"type" : "button",
					"x" : SEARCH_BG_X + SEARCH_BAR_W - 50,
					"y" : SEARCH_BAR_Y + 3,
					"default_image" : SMALL_BTN % 1,
					"over_image" : SMALL_BTN % 2,
					"down_image" : SMALL_BTN % 3,
					"text" : "X",
				},

				{
					"name" : "imporve_slot",
					"type" : "thinboard_circle",
					"style" : ("attach",),
					"x" : 60,
					"y" : CRAFT_ROW_Y + 12,
					"width" : 50,
					"height" : 20,
				},

				# YENI: Beceri kitabi secim grid'i (etiket + zemin + slotlar)
				{
					"name" : "skill_grid_label",
					"type" : "text",
					"x" : SKILL_GRID_X + 2,
					"y" : SKILL_LABEL_Y,
					"text" : "Skill Books",
				},
				{
					"name" : "skill_grid_bg",
					"type" : "thinboard_circle",
					"style" : ("attach",),
					"x" : SKILL_GRID_X - 3,
					"y" : SKILL_GRID_Y - 6,
					"width" : SKILL_GRID_W + 6,
					"height" : SKILL_GRID_H + 12,
				},
				{
					"name" : "skill_grid",
					"type" : "grid_table",
					"x" : SKILL_GRID_X,
					"y" : SKILL_GRID_Y,
					"start_index" : 0,
					"x_count" : SKILL_GRID_COLS,
					"y_count" : SKILL_GRID_ROWS,
					"x_step" : MAT_STEP_X,
					"y_step" : MAT_STEP_Y,
					"image" : ICON_SLOT_FILE,
				},
				{
					"name" : "qty_sub_button",
					"type" : "button",
					"x" : 15,
					"y" : CRAFT_ROW_Y + 12,
					"default_image" : SMALL_BTN % 1,
					"over_image" : SMALL_BTN % 2,
					"down_image" : SMALL_BTN % 3,
					"text" : "-",
				},
				{
					"name" : "result_qty",
					"type" : "editline",
					"x" : 80,
					"y" : CRAFT_ROW_Y + 14,
					"width" : 50,
					"height" : 20,
					"input_limit" : 3,
				},
				{
					"name" : "qty_add_button",
					"type" : "button",
					"x" : 115,
					"y" : CRAFT_ROW_Y + 12,
					"default_image" : SMALL_BTN % 1,
					"over_image" : SMALL_BTN % 2,
					"down_image" : SMALL_BTN % 3,
					"text" : "+",
				},

				{
					"name" : "AcceptButton",
					"type" : "button",
					"x" : 353,
					"y" : BOARD_H - 35,
					"text" : uiScriptLocale.OK,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
				{
					"name" : "CancelButton",
					"type" : "button",
					"x" : 273,
					"y" : BOARD_H - 35,
					"text" : uiScriptLocale.CANCEL,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
			),
		},
	),
}
