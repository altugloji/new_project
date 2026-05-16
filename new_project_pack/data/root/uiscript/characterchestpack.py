import uiScriptLocale

WINDOW_WIDTH = 280
WINDOW_HEIGHT = 300

window = {
	"name" : "CharacterChestPackDialog",
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
					"name" : "desc",
					"type" : "text",
					"x" : 15,
					"y" : 35,
					"text" : "",
				},
				{
					"name" : "list_slot",
					"type" : "thinboard_circle",
					"x" : 15,
					"y" : 55,
					"width" : 248,
					"height" : 140,
				},
				{
					"name" : "password_label",
					"type" : "text",
					"x" : 15,
					"y" : 205,
					"text" : "Karakter silme sifresi",
				},
				{
					"name" : "password_slot",
					"type" : "slotbar",
					"x" : 15,
					"y" : 225,
					"width" : 248,
					"height" : 18,
				},
				{
					"name" : "accept_button",
					"type" : "button",
					"x" : 40,
					"y" : 260,
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
					"x" : 150,
					"y" : 260,
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
