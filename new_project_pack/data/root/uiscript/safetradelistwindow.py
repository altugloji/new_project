window = {
	"name" : "SafeTradeListWindow",

	"x" : 100,
	"y" : 20,

	"style" : ("movable", "float",),

	"width" : 260,
	"height" : 320,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",

			"x" : 0,
			"y" : 0,

			"width" : 260,
			"height" : 320,

			"children" :
			(
				## Title
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 8,
					"y" : 7,

					"width" : 245,
					"color" : "yellow",

					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":122, "y":3, "text":"", "text_horizontal_align":"center" },
					),
				},

				## View / Claim button
				{
					"name" : "ViewButton",
					"type" : "button",
					"x" : 0, "y" : 285,
					"horizontal_align" : "center",
					"text" : "",
					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},
			),
		},
	),
}
