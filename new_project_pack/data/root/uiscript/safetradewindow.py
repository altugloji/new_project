window = {
	"name" : "SafeTradeWindow",

	"x" : 100,
	"y" : 20,

	"style" : ("movable", "float",),

	"width" : 218,
	"height" : 213,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",

			"x" : 0,
			"y" : 0,

			"width" : 218,
			"height" : 213,

			"children" :
			(
				## Title
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"width" : 203,
					"color" : "yellow",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":101, "y":3, "text":"", "text_horizontal_align":"center" },
					),
				},

				## Buttons
				{
					"name" : "LockButton",
					"type" : "button",
					"x" : 18, "y" : 180,
					"text" : "",
					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name" : "ConfirmButton",
					"type" : "button",
					"x" : 18, "y" : 180,
					"text" : "",
					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name" : "ClaimButton",
					"type" : "button",
					"x" : 18, "y" : 180,
					"text" : "",
					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name" : "CloseButton",
					"type" : "button",
					"x" : 111, "y" : 180,
					"text" : "",
					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
			),
		},
	),
}
