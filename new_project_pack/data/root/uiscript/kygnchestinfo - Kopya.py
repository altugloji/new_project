
FULL_WIDTH = 342 + 10 + 10
FULL_HEIGHT = 303

TOP_BOARD_HEIGHT = 293

window = {
	"name" : "PiyasaNPC",
	"style" : ("movable", "float",),

	"x" : SCREEN_WIDTH / 2 - (FULL_WIDTH/2),
	"y" : SCREEN_HEIGHT / 2 - (FULL_HEIGHT/2),

	"width" : FULL_WIDTH,
	"height" : FULL_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : FULL_WIDTH,
			"height" : TOP_BOARD_HEIGHT,

			"children" :
			(
				{
					"name" : "board_Days",
					"type" : "board",
					"style" : ("attach",),

					"x" : 10,
					"y" : 16,

					"width" : 342,
					"height" : 267,

					"children" :
					(
						{
							"name" : "itemTC", "type" : "thinboard_circle", "x" : 7, "y" : 14, "width" : 162, "height" : 20,
							"children" :
							(
								{ "name" : "locationText", "type" : "text", "x" : 0, "y" : 0, "text": "Sayfa", "all_align":"center" },
							),
						},
						{
							"name" : "itemTC", "type" : "thinboard_circle", "x" : 7, "y" : 14 + 20 + 2, "width" : 162, "height" : 20,
							"children" :
							(
								{
									"name" : "PrevButton",
									"type" : "button",
									"x" : -20,
									"y" : 1,
									"vertical_align" : "center",
									"horizontal_align" : "center",
									"default_image" : "d:/ymir work/ui/target_info/prev_btn_01.tga",
									"over_image" : "d:/ymir work/ui/target_info/prev_btn_02.tga",
									"down_image" : "d:/ymir work/ui/target_info/prev_btn_01.tga",
								},

								{
									"name" : "CurrentPage",
									"type" : "text",
									
									"x" : 0,
									"y" : 0,

									"vertical_align" : "center",
									"horizontal_align" : "center",

									"text_vertical_align" : "center",
									"text_horizontal_align" : "center",

									"text" : "1",
								},

								{
									"name" : "NextButton",
									"type" : "button",
									"x" : 18,
									"y" : 1,
									"vertical_align" : "center",
									"horizontal_align" : "center",
									"default_image" : "d:/ymir work/ui/target_info/next_btn_01.tga",
									"over_image" : "d:/ymir work/ui/target_info/next_btn_02.tga",
									"down_image" : "d:/ymir work/ui/target_info/next_btn_01.tga",
								},
							),
						},
						{
							"name" : "itemTC", "type" : "thinboard_circle", "x" : 7 + 162 + 3, "y" : 14, "width" : 162, "height" : 40 + 2,
							"children" :
							(
								{
									"name" : "chestSlot",
									"type" : "grid_table",
									"x" : 65,
									"y" : 5,
									"start_index" : 0,
									"x_count" : 1,
									"y_count" : 1,
									"x_step" : 32,
									"y_step" : 32,
									"image" : "d:/ymir work/ui/public/Slot_Base.sub"
								},
							),
						},
						{
							"name" : "itemTC", "type" : "thinboard_circle", "x" : 7, "y" : 58, "width" : 326, "height" : 200,
							"children" :
							(
								{
									"name" : "ItemSlot",
									"type" : "grid_table",
									"x" : 3,
									"y" : 4,
									"start_index" : 0,
									"x_count" : 10,
									"y_count" : 6,
									"x_step" : 32,
									"y_step" : 32,
									"image" : "d:/ymir work/ui/public/Slot_Base.sub"
								},
							),
						},
					),
				},

				## Title
				{
					"name" : "titleBar",
					"type" : "titlebar",
					"style" : ("attach",),

					"x" : 5,
					"y" : 6,

					"width" : FULL_WIDTH-12,
					"color" : "gray",

					"children" :
					(
						{ "name":"titlename", "type":"text", "x":0, "y":3, 
						"text" : "Metin35 - Sandýk Aynasý", 
						"horizontal_align":"center", "text_horizontal_align":"center" },
					),
				},
			),
		},
	),
}

