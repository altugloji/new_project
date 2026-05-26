import uiScriptLocale

BOARD_WIDTH = 280
BOARD_HEIGHT = 360

window = {
	"name" : "EfsunChangeDialog",
	"style" : ("movable", "float",),

	"x" : 0,
	"y" : 0,

	"width" : BOARD_WIDTH,
	"height" : BOARD_HEIGHT,

	"children" :
	(
		{
			"name" : "Board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : BOARD_WIDTH,
			"height" : BOARD_HEIGHT,

			"children" :
			(
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 8,

					"width" : BOARD_WIDTH - 15,

					"children" :
					(
						{
							"name" : "TitleName",
							"type" : "text",
							"text" : "Efsun Degistir",
							"horizontal_align" : "center",
							"text_horizontal_align" : "center",
							"x" : 0,
							"y" : 3,
						},
					),
				},
				{
					"name" : "ScrollCountText",
					"type" : "text",

					"x" : 0,
					"y" : 65,

					"text" : "Envanterindeki Efsun Nesnesi: 0",
					"horizontal_align" : "center",
					"vertical_align" : "bottom",
					"text_horizontal_align" : "center",
					# "color" : 0xFFf863ff,
				},
				{
					"name" : "AcceptButton",
					"type" : "button",

					"x" : -55,
					"y" : 35,

					"text" : "Degistir",
					"horizontal_align" : "center",
					"vertical_align" : "bottom",

					"default_image" : "d:/ymir work/ui/public/Middle_Button_01.sub",
					"over_image" : "d:/ymir work/ui/public/Middle_Button_02.sub",
					"down_image" : "d:/ymir work/ui/public/Middle_Button_03.sub",
				},
				{
					"name" : "CancelButton",
					"type" : "button",

					"x" : 55,
					"y" : 35,

					"text" : "Kapat",
					"horizontal_align" : "center",
					"vertical_align" : "bottom",

					"default_image" : "d:/ymir work/ui/public/Middle_Button_01.sub",
					"over_image" : "d:/ymir work/ui/public/Middle_Button_02.sub",
					"down_image" : "d:/ymir work/ui/public/Middle_Button_03.sub",
				},
			),
		},
	),
}
