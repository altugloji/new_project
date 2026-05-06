import localeInfo

IMG_DIR = "d:/ymir work/ui/game/exchange_log/"

exchange_grid_size = [4, 3]
bgWidth = ((exchange_grid_size[0] * 32) * 2) + (10 + 16)
bgHeight = 7+(exchange_grid_size[1]*32)+44

windowWidth = 10+bgWidth
windowHeight = 31+bgHeight

window = {
	"name" : "ExchangeLogWindow",
	# "style" : ("animate","float"),
	"style" : ("float",),
	"x" : 0, "y" : 0,
	"width" : windowWidth, "height" : windowHeight,
	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"x" : 0,"y" : 0,
			"width" : windowWidth,"height" : windowHeight,
			"title":localeInfo.EXCHANGELOG_FAKETITLE,
			"children":
			(
				{
					"name" : "bg",
					"type" : "expanded_image",
					"x" : 5,"y" : 26,
					"image":IMG_DIR+"exchange_bg.tga",
					"x_scale": bgWidth * (1.0/636.0), "y_scale": bgHeight * (1.0/324.0),
					"children":
					(
						{
							"name" : "owner_slot",
							"type" : "grid_table",
							"start_index" : 0,
							"x" : 5,
							"y" : 7,
							"x_count" : exchange_grid_size[0],"y_count" : exchange_grid_size[1],
							"x_step" : 32,"y_step" : 32,
							"x_blank" : 0,"y_blank" : 0,
							"image" : "d:/ymir work/ui/public/slot_base.sub",
							"children":
							(
								{
									"name" : "owner_gold_slot",
									"type" : "image",
									"x": (exchange_grid_size[0] * 32) - 127,
									"y": (exchange_grid_size[1] * 32) + 11,
									"image":IMG_DIR+"gold_slot.tga",
									"children":
									(
										{
											"name" : "owner_gold",
											"type" : "text",
											"x": 120,
											"y": 3,
											"fontname": "Tahoma:11",
											"text_horizontal_align" : "right",
											"text":"0",
										},
									),
								},
							),
						},

						{"name" : "direction","type" : "image","x":5 + (exchange_grid_size[0]*32) + 2,"y": 7 + ((exchange_grid_size[1]*32)/2) - 5, "image":IMG_DIR+"center_direction.tga",},
						{"name" : "loadingText","type" : "text","x":bgWidth/2,"y": bgHeight/2, "text":localeInfo.EXCHANGELOG_LOADING,},
						{
							"name" : "target_slot",
							"type" : "grid_table",
							"start_index" : 0,
							"x" : 5 + (exchange_grid_size[0]*32) + 16,
							"y" : 7,
							"x_count" : exchange_grid_size[0],"y_count" : exchange_grid_size[1],
							"x_step" : 32,"y_step" : 32,
							"x_blank" : 0,"y_blank" : 0,
							"image" : "d:/ymir work/ui/public/slot_base.sub",
							"children":
							(
								{
									"name" : "target_gold_slot",
									"type" : "image",
									"x": (exchange_grid_size[0] * 32) - 127,
									"y": (exchange_grid_size[1] * 32) + 11,
									"image":IMG_DIR+"gold_slot.tga",
									"children":
									(
										{
											"name" : "target_gold",
											"type" : "text",
											"x": 120,
											"y": 3,
											"fontname": "Tahoma:11",
											"text_horizontal_align" : "right",
											"text":"0",
										},
									),
								},
							),
						},

					),
				},
			),
		},
	),
}
