import uiScriptLocale

window = {
	"name" : "SafeTradeConfirmDialog",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH/2 - 180,
	"y" : SCREEN_HEIGHT/2 - 70,

	"width" : 360,
	"height" : 140,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",

			"x" : 0,
			"y" : 0,

			"width" : 360,
			"height" : 140,

			"children" :
			(
				{ "name":"line1", "type":"text", "x":0, "y":24, "text":"", "horizontal_align":"center", "text_horizontal_align":"center" },
				{ "name":"line2", "type":"text", "x":0, "y":44, "text":"", "horizontal_align":"center", "text_horizontal_align":"center" },
				{ "name":"line3", "type":"text", "x":0, "y":74, "text":"", "horizontal_align":"center", "text_horizontal_align":"center" },

				{
					"name" : "accept",
					"type" : "button",
					"x" : -45, "y" : 102,
					"width" : 61, "height" : 21,
					"horizontal_align" : "center",
					"text" : uiScriptLocale.YES,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
				{
					"name" : "cancel",
					"type" : "button",
					"x" : 45, "y" : 102,
					"width" : 61, "height" : 21,
					"horizontal_align" : "center",
					"text" : uiScriptLocale.NO,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
			),
		},
	),
}
