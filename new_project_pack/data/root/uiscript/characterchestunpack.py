import uiScriptLocale

WINDOW_WIDTH = 300
WINDOW_HEIGHT = 180

window = {
	"name" : "CharacterChestUnpackDialog",
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
					"name" : "name_text",
					"type" : "text",
					"x" : 15,
					"y" : 45,
					"text" : "",
				},
				{
					"name" : "question_text",
					"type" : "text",
					"x" : 15,
					"y" : 70,
					"text" : "",
				},
				{
					"name" : "accept_button",
					"type" : "button",
					"x" : 50,
					"y" : 130,
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
					"x" : 160,
					"y" : 130,
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
