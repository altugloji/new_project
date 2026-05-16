
#import Legal Bilisim ?nternet Hizmetleri

import uiScriptLocale
import localeInfo

LOCALE_PATH = "d:/ymir work/ui/privatesearch/"
ITEM_SHOP_FONT = getattr(localeInfo, "UI_BOLD_FONT_LARGE", localeInfo.UI_DEF_FONT_LARGE)
NESNE_ITEMS_BG_PATH = "d:/ymir work/flags/nesne_bg.png"
NESNE_ITEMS_BG_NATURAL_W = 573
NESNE_ITEMS_BG_NATURAL_H = 110
ITEM_ROW_GAP = 10
ITEM_LIST_TOP_PAD = 10
ITEM_SHOP_VISIBLE_ITEM_ROWS = 5
ITEM_SHOP_SCROLLBAR_TRACK_W = 8
ITEM_SHOP_SCROLLBAR_GAP = 4
SECOND_BOARD_SIDE_PAD = 8
POS_START_Y = 65
# Five item rows (110px) + four 10px gaps + top pad + bottom margin inside board_second; -25 shortens window from bottom
BOARD_HEIGHT = POS_START_Y + ITEM_LIST_TOP_PAD + (ITEM_SHOP_VISIBLE_ITEM_ROWS * NESNE_ITEMS_BG_NATURAL_H) + ((ITEM_SHOP_VISIBLE_ITEM_ROWS - 1) * ITEM_ROW_GAP) + 35 + 10 - 25
#------------------------------------------------------------------
BOARD_WIDTH = 735
SEARCH_AREA_X_SHIFT = 50
FIRST_BOARD_START_X = 2
FIRST_BOARD_START_Y = 25
# Hesabi Doldur: absolute on main board (was board_first 10+8, 65+6) +320 right, -36 up
COIN_BUY_BTN_X = 338
COIN_BUY_BTN_Y = 35
FIRST_BOARD_WIDTH = 176
FIRST_BOARD_HEIGHT = (BOARD_HEIGHT - FIRST_BOARD_START_Y - 10)

#------------------------------------------------------------------
SECOND_BOARD_START_X = (FIRST_BOARD_START_X + FIRST_BOARD_WIDTH)
SECOND_BOARD_START_Y = POS_START_Y
SECOND_BOARD_WIDTH = SECOND_BOARD_SIDE_PAD + NESNE_ITEMS_BG_NATURAL_W + ITEM_SHOP_SCROLLBAR_GAP + ITEM_SHOP_SCROLLBAR_TRACK_W + SECOND_BOARD_SIDE_PAD
SECOND_BOARD_HEIGHT = (BOARD_HEIGHT - SECOND_BOARD_START_Y - 10)
#------------------------------------------------------------------
ITEM_BOARD_START_X = 10
ITEM_BOARD_START_Y = 10
ITEM_BOARD_WIDTH = 160
ITEM_BOARD_HEIGHT = 130

window = {
	"name" : "ItemShopWindow",

	"x" : 0,
	"y" : 0,

	"style" : ("movable", "float",),

	"width" : BOARD_WIDTH+100,
	"height" : BOARD_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : BOARD_WIDTH+65,
			"height" : BOARD_HEIGHT,

			"children" :
			(
				# {
					# "name" : "bg",
					# "type" : "image",
					# "x" : 0,"y": 22,
					# "horizontal_align" : "center",
					# "image" : "d:/ymir work/salihq.png",

				# },

				## Title
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 6,
					"y" : 6,

					"width" : BOARD_WIDTH+53,
					"color" : "yellow",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":BOARD_WIDTH/2, "y":3, "text": "Nesne Market", "text_horizontal_align":"center" },
					),
				},
				
				{
					"name":"coins_icon",
					"type":"image",
					"x" : 18,
					"y" : POS_START_Y - 25,
					"image":"d:/ymir work/ui/itemshop/ep.png",
				},
				{
					"name" : "Coins_Slot",
					"type" : "slotbar",
					"x" : 44,
					"y" : POS_START_Y - 27,
					"width" : 82,
					"height" : 22,
					"children" :
					(
						{
							"name" : "dragon_coin_text",
							"type" : "text",
							"x" : 0,
							"y" : 0,
							"all_align" : "center",
							"text" : "0 EP",
							"outline" : 1,
						},
					),
				},
				{
					"name" : "search_slotbar", "type" : "slotbar",
					"x" : BOARD_WIDTH - 230 + SEARCH_AREA_X_SHIFT,
					"y" : POS_START_Y - 30,
					"width" : 160, "height" : 24,
					"children" : (
						{
							"name" : "search_editline", "type" : "editline",
							"x" : 3, "y" : 4, "width" : 150, "height" : 24,
							"input_limit" : 24, "fontname" : ITEM_SHOP_FONT,
						},
					),
				},
				{
					"name" : "search_button", "type" : "button",
					"x" : BOARD_WIDTH - 60 + SEARCH_AREA_X_SHIFT,
					"y" : POS_START_Y - 30,
					"default_image" : "d:/ymir work/ui/itemshop/search_button_default.sub",
					"over_image" 	: "d:/ymir work/ui/itemshop/search_button_over.sub",
					"down_image" 	: "d:/ymir work/ui/itemshop/search_button_down.sub",
				},
				{
					"name" : "coin_buy_button", "type" : "button",
					"x" : COIN_BUY_BTN_X,
					"y" : COIN_BUY_BTN_Y,
					"text" : "|cffFEE3AEEP SATIN AL",
					"default_image" : "d:/ymir work/nesne_market/ep_al.png",
					"over_image" 	: "d:/ymir work/nesne_market/ep_al.png",
					"down_image" 	: "d:/ymir work/nesne_market/ep_al.png",
				},

				{
					"name" : "board_first",
					"type" : "window",
					"style" : ("attach",),

					"x" : FIRST_BOARD_START_X,
					"y" : FIRST_BOARD_START_Y,

					"width" : FIRST_BOARD_WIDTH,
					"height" : FIRST_BOARD_HEIGHT,
					
					"children" : 
					(
						{
							"name" : "ScrollBar",
							"type" : "image",
							"x" : 25,
							"y" : 40,
							"size" : FIRST_BOARD_HEIGHT - 52,
							"horizontal_align" : "right",
						},
					),
				},

				{
					"name" : "board_second",
					"type" : "window",
					"style" : ("attach",),

					"x" : SECOND_BOARD_START_X,
					"y" : SECOND_BOARD_START_Y,

					"width" : SECOND_BOARD_WIDTH,
					"height" : SECOND_BOARD_HEIGHT,

					"children"  :
					(
						{
							"name" : "itemBoard_01",
							"type" : "window",
							"style" : ("attach",),
							"x" : SECOND_BOARD_SIDE_PAD,
							"y" : ITEM_LIST_TOP_PAD,
							"width" : NESNE_ITEMS_BG_NATURAL_W,
							"height" : NESNE_ITEMS_BG_NATURAL_H,
							"children" :
							(
								{
									"name" : "item_row_bg_01",
									"type" : "image",
									"x" : 0,
									"y" : 0,
									"image" : NESNE_ITEMS_BG_PATH,
								},
								{
									"name" : "itemSlot_01", "type" : "grid_table", "x" : 37, "y" : 38, "start_index" : 1,
									"x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32, "x_blank" : 2, "y_blank" : 2,
								},
								{
									"name" : "itemQtyBg_01", "type" : "slotbar",
									"x" : 337, "y" : 78, "width" : 82, "height" : 22,
									"children" : (),
								},
								{
									"name" : "itemName_01", "type" : "text",
									"x" : 166, "y" : 20,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemOldPrice_01", "type" : "text",
									"x" : 347, "y" : 80,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemPreviewButton_01", "type" : "button",
									"x" : 118, "y" : 39,
									"horizontal_align" : "right",
									"tooltip_text" : "|cff00ccffOn Izleme",
									"default_image" : "d:/ymir work/ui/itemshop/preview_button_01.tga",
									"over_image" : "d:/ymir work/ui/itemshop/preview_button_02.tga",
									"down_image" : "d:/ymir work/ui/itemshop/preview_button_03.tga",
								},
								{
									"name" : "itemBuyButton_01", "type" : "button",
									"x" : 103, "y" : 78,
									"horizontal_align" : "right",
									"text" : "", "tooltip_text" : "|cff00ccffSatin al",
									"default_image" : "d:/ymir work/ui/public/Large_Button_01.sub",
									"over_image" : "d:/ymir work/ui/public/Large_Button_02.sub",
									"down_image" : "d:/ymir work/ui/public/Large_Button_03.sub",
								},
							),
						},


						{
							"name" : "itemBoard_02",
							"type" : "window",
							"style" : ("attach",),
							"x" : SECOND_BOARD_SIDE_PAD,
							"y" : ITEM_LIST_TOP_PAD + 1 * (NESNE_ITEMS_BG_NATURAL_H + ITEM_ROW_GAP),
							"width" : NESNE_ITEMS_BG_NATURAL_W,
							"height" : NESNE_ITEMS_BG_NATURAL_H,
							"children" :
							(
								{
									"name" : "item_row_bg_02",
									"type" : "image",
									"x" : 0,
									"y" : 0,
									"image" : NESNE_ITEMS_BG_PATH,
								},
								{
									"name" : "itemSlot_02", "type" : "grid_table", "x" : 37, "y" : 38, "start_index" : 2,
									"x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32, "x_blank" : 2, "y_blank" : 2,
								},
								{
									"name" : "itemQtyBg_02", "type" : "slotbar",
									"x" : 337, "y" : 78, "width" : 82, "height" : 22,
									"children" : (),
								},
								{
									"name" : "itemName_02", "type" : "text",
									"x" : 166, "y" : 20,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemOldPrice_02", "type" : "text",
									"x" : 347, "y" : 80,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemPreviewButton_02", "type" : "button",
									"x" : 118, "y" : 39,
									"horizontal_align" : "right",
									"tooltip_text" : "|cff00ccffOn Izleme",
									"default_image" : "d:/ymir work/ui/itemshop/preview_button_01.tga",
									"over_image" : "d:/ymir work/ui/itemshop/preview_button_02.tga",
									"down_image" : "d:/ymir work/ui/itemshop/preview_button_03.tga",
								},
								{
									"name" : "itemBuyButton_02", "type" : "button",
									"x" : 103, "y" : 78,
									"horizontal_align" : "right",
									"text" : "", "tooltip_text" : "|cff00ccffSatin al",
									"default_image" : "d:/ymir work/ui/public/Large_Button_01.sub",
									"over_image" : "d:/ymir work/ui/public/Large_Button_02.sub",
									"down_image" : "d:/ymir work/ui/public/Large_Button_03.sub",
								},
							),
						},


						{
							"name" : "itemBoard_03",
							"type" : "window",
							"style" : ("attach",),
							"x" : SECOND_BOARD_SIDE_PAD,
							"y" : ITEM_LIST_TOP_PAD + 2 * (NESNE_ITEMS_BG_NATURAL_H + ITEM_ROW_GAP),
							"width" : NESNE_ITEMS_BG_NATURAL_W,
							"height" : NESNE_ITEMS_BG_NATURAL_H,
							"children" :
							(
								{
									"name" : "item_row_bg_03",
									"type" : "image",
									"x" : 0,
									"y" : 0,
									"image" : NESNE_ITEMS_BG_PATH,
								},
								{
									"name" : "itemSlot_03", "type" : "grid_table", "x" : 37, "y" : 38, "start_index" : 3,
									"x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32, "x_blank" : 2, "y_blank" : 2,
								},
								{
									"name" : "itemQtyBg_03", "type" : "slotbar",
									"x" : 337, "y" : 78, "width" : 82, "height" : 22,
									"children" : (),
								},
								{
									"name" : "itemName_03", "type" : "text",
									"x" : 166, "y" : 20,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemOldPrice_03", "type" : "text",
									"x" : 347, "y" : 80,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemPreviewButton_03", "type" : "button",
									"x" : 118, "y" : 39,
									"horizontal_align" : "right",
									"tooltip_text" : "|cff00ccffOn Izleme",
									"default_image" : "d:/ymir work/ui/itemshop/preview_button_01.tga",
									"over_image" : "d:/ymir work/ui/itemshop/preview_button_02.tga",
									"down_image" : "d:/ymir work/ui/itemshop/preview_button_03.tga",
								},
								{
									"name" : "itemBuyButton_03", "type" : "button",
									"x" : 103, "y" : 78,
									"horizontal_align" : "right",
									"text" : "", "tooltip_text" : "|cff00ccffSatin al",
									"default_image" : "d:/ymir work/ui/public/Large_Button_01.sub",
									"over_image" : "d:/ymir work/ui/public/Large_Button_02.sub",
									"down_image" : "d:/ymir work/ui/public/Large_Button_03.sub",
								},
							),
						},


						{
							"name" : "itemBoard_04",
							"type" : "window",
							"style" : ("attach",),
							"x" : SECOND_BOARD_SIDE_PAD,
							"y" : ITEM_LIST_TOP_PAD + 3 * (NESNE_ITEMS_BG_NATURAL_H + ITEM_ROW_GAP),
							"width" : NESNE_ITEMS_BG_NATURAL_W,
							"height" : NESNE_ITEMS_BG_NATURAL_H,
							"children" :
							(
								{
									"name" : "item_row_bg_04",
									"type" : "image",
									"x" : 0,
									"y" : 0,
									"image" : NESNE_ITEMS_BG_PATH,
								},
								{
									"name" : "itemSlot_04", "type" : "grid_table", "x" : 37, "y" : 38, "start_index" : 4,
									"x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32, "x_blank" : 2, "y_blank" : 2,
								},
								{
									"name" : "itemQtyBg_04", "type" : "slotbar",
									"x" : 337, "y" : 78, "width" : 82, "height" : 22,
									"children" : (),
								},
								{
									"name" : "itemName_04", "type" : "text",
									"x" : 166, "y" : 20,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemOldPrice_04", "type" : "text",
									"x" : 347, "y" : 80,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemPreviewButton_04", "type" : "button",
									"x" : 118, "y" : 39,
									"horizontal_align" : "right",
									"tooltip_text" : "|cff00ccffOn Izleme",
									"default_image" : "d:/ymir work/ui/itemshop/preview_button_01.tga",
									"over_image" : "d:/ymir work/ui/itemshop/preview_button_02.tga",
									"down_image" : "d:/ymir work/ui/itemshop/preview_button_03.tga",
								},
								{
									"name" : "itemBuyButton_04", "type" : "button",
									"x" : 103, "y" : 78,
									"horizontal_align" : "right",
									"text" : "", "tooltip_text" : "|cff00ccffSatin al",
									"default_image" : "d:/ymir work/ui/public/Large_Button_01.sub",
									"over_image" : "d:/ymir work/ui/public/Large_Button_02.sub",
									"down_image" : "d:/ymir work/ui/public/Large_Button_03.sub",
								},
							),
						},


						{
							"name" : "itemBoard_05",
							"type" : "window",
							"style" : ("attach",),
							"x" : SECOND_BOARD_SIDE_PAD,
							"y" : ITEM_LIST_TOP_PAD + 4 * (NESNE_ITEMS_BG_NATURAL_H + ITEM_ROW_GAP),
							"width" : NESNE_ITEMS_BG_NATURAL_W,
							"height" : NESNE_ITEMS_BG_NATURAL_H,
							"children" :
							(
								{
									"name" : "item_row_bg_05",
									"type" : "image",
									"x" : 0,
									"y" : 0,
									"image" : NESNE_ITEMS_BG_PATH,
								},
								{
									"name" : "itemSlot_05", "type" : "grid_table", "x" : 37, "y" : 38, "start_index" : 5,
									"x_count" : 1, "y_count" : 1, "x_step" : 32, "y_step" : 32, "x_blank" : 2, "y_blank" : 2,
								},
								{
									"name" : "itemQtyBg_05", "type" : "slotbar",
									"x" : 337, "y" : 78, "width" : 82, "height" : 22,
									"children" : (),
								},
								{
									"name" : "itemName_05", "type" : "text",
									"x" : 166, "y" : 20,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemOldPrice_05", "type" : "text",
									"x" : 347, "y" : 80,
									"fontname" : ITEM_SHOP_FONT, "text" : "", "outline" : 1,
								},
								{
									"name" : "itemPreviewButton_05", "type" : "button",
									"x" : 118, "y" : 39,
									"horizontal_align" : "right",
									"tooltip_text" : "|cff00ccffOn Izleme",
									"default_image" : "d:/ymir work/ui/itemshop/preview_button_01.tga",
									"over_image" : "d:/ymir work/ui/itemshop/preview_button_02.tga",
									"down_image" : "d:/ymir work/ui/itemshop/preview_button_03.tga",
								},
								{
									"name" : "itemBuyButton_05", "type" : "button",
									"x" : 103, "y" : 78,
									"horizontal_align" : "right",
									"text" : "", "tooltip_text" : "|cff00ccffSatin al",
									"default_image" : "d:/ymir work/ui/public/Large_Button_01.sub",
									"over_image" : "d:/ymir work/ui/public/Large_Button_02.sub",
									"down_image" : "d:/ymir work/ui/public/Large_Button_03.sub",
								},
							),
						},


					),
				},
			),
		},
	),
}
