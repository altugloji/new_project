import uiScriptLocale

ROOT_PATH = "d:/ymir work/ui/public/"
QUEST_CHECK_PATH = "d:/ymir work/ui/game/quest/"

WINDOW_WIDTH = 220
WINDOW_HEIGHT = 285

window = {
	"name" : "ReportWindow",
	"style" : ("movable", "float",),
	"x" : SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,
	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,
	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"x" : 0,
			"y" : 0,
			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,
			"title" : uiScriptLocale.USER_REPORT_SYSTEM_UI_WINDOW_NAME,
			"children" :
			(
				{"name" : "target_label", "type" : "text", "x" : 0, "y" : 36, "text" : uiScriptLocale.USER_REPORT_SYSTEM_UI_TARGET_CHECK, "horizontal_align" : "center", "text_horizontal_align" : "center"},
				{"name" : "name_slot" , "type" : "text", "x" : 0, "y" : 57, "text" : "", "horizontal_align" : "center", "text_horizontal_align" : "center"},
				{"name" : "reason_label", "type" : "text", "x" : 0, "y" : 88, "text" : uiScriptLocale.USER_REPORT_SYSTEM_UI_SELECT_REASON, "horizontal_align" : "center", "text_horizontal_align" : "center"},
				{
					"name" : "button_yang_sell",
					"type" : "toggle_button",
					"x" : 20,
					"y" : 104+7,
					"default_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"over_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"down_image" : QUEST_CHECK_PATH + "quest_checked.tga",
				},
				{"name" : "reason_yang_sell_text", "type" : "text", "x" : 44, "y" : 104+6, "text" : ""},
				{
					"name" : "button_farm_bot",
					"type" : "toggle_button",
					"x" : 20,
					"y" : 129+7,
					"default_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"over_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"down_image" : QUEST_CHECK_PATH + "quest_checked.tga",
				},
				{"name" : "reason_farm_text", "type" : "text", "x" : 44, "y" : 129+6, "text" : ""},
				{
					"name" : "button_fish_bot",
					"type" : "toggle_button",
					"x" : 20,
					"y" : 154+7,
					"default_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"over_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"down_image" : QUEST_CHECK_PATH + "quest_checked.tga",
				},
				{"name" : "reason_fish_text", "type" : "text", "x" : 44, "y" : 154+6, "text" : ""},
				{
					"name" : "button_reklam",
					"type" : "toggle_button",
					"x" : 20,
					"y" : 179+7,
					"default_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"over_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"down_image" : QUEST_CHECK_PATH + "quest_checked.tga",
				},
				{"name" : "reason_reklam_text", "type" : "text", "x" : 44, "y" : 179+6, "text" : ""},
				{
					"name" : "button_diger",
					"type" : "toggle_button",
					"x" : 20,
					"y" : 204+7,
					"default_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"over_image" : QUEST_CHECK_PATH + "quest_checkbox.tga",
					"down_image" : QUEST_CHECK_PATH + "quest_checked.tga",
				},
				{"name" : "reason_diger_text", "type" : "text", "x" : 44, "y" : 204+6, "text" : ""},
				{
					"name" : "send_button",
					"type" : "button",
					"x" : 20,
					"y" : 249,
					"text" : uiScriptLocale.USER_REPORT_SYSTEM_UI_SEND_BUTTON,
					"default_image" : ROOT_PATH + "middle_button_01.sub",
					"over_image" : ROOT_PATH + "middle_button_02.sub",
					"down_image" : ROOT_PATH + "middle_button_03.sub",
					"disable_image" : ROOT_PATH + "middle_button_01.sub",
				},
				{
					"name" : "close_button",
					"type" : "button",
					"x" : 115,
					"y" : 249,
					"text" : uiScriptLocale.USER_REPORT_SYSTEM_UI_CLOSE_BUTTON,
					"default_image" : ROOT_PATH + "middle_button_01.sub",
					"over_image" : ROOT_PATH + "middle_button_02.sub",
					"down_image" : ROOT_PATH + "middle_button_03.sub",
					"disable_image" : ROOT_PATH + "middle_button_01.sub",
				},
			),
		},
	),
}