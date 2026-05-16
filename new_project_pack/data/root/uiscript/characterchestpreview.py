import uiScriptLocale

CHAR_PANEL_X = 12
CHAR_PANEL_Y = 36
INV_PANEL_X = 277
INV_PANEL_Y = 36

WINDOW_WIDTH = 469
WINDOW_HEIGHT = 640

window = {
	"name" : "CharacterChestPreviewDialog",
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
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,
			"title" : "Karakter Sandigi",
			"children" :
			(
				{
					"name" : "accept_button",
					"type" : "button",
					"x" : 80,
					"y" : 601,
					"width" : 61,
					"height" : 21,
					"text" : uiScriptLocale.OK,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
				{
					"name" : "cancel_button",
					"type" : "button",
					"x" : 156,
					"y" : 601,
					"width" : 61,
					"height" : 21,
					"text" : uiScriptLocale.CANCEL,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
			),
		},
	),
}
