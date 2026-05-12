import localeInfo

IMG_DIR = "d:/ymir work/ui/gemshop/"

WINDOW_X = 171
WINDOW_Y = 250

window = {
	"name" : "GemShopWindows",
	"x" : 0,
	"y" : 0,
	"style" : ("movable", "float"),
	"width" : WINDOW_X,
	"height" : WINDOW_Y,
	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" :WINDOW_X,
			"height" : WINDOW_Y,
			"title" : localeInfo.GEMSHOP_TITLE2,
			"children" :
			(
				{
					"name" : "bg_slots",
					"type" : "image",
					"style" : ("not_pick",),
					"x" : 16,
					"y" : 33,
					"image" : IMG_DIR+"gemshop_backimg.sub",
				},
				{
					"name": "time_gaya",
					"type": "text",
					"style" : ("not_pick",),
					"x" : 14+100,
					"y" : 32+5,
					"text": "0s",
				},

				{
					"name" : "back_btn",
					"type" : "button",
					"x" : 14+35,
					"y" : 39,
					"default_image" : IMG_DIR+"back_page_0.tga",
					"over_image" : IMG_DIR+"back_page_0.tga",
					"down_image" : IMG_DIR+"back_page_1.tga",
				},

				{
					"name" : "page_slot",
					"type" : "image",
					"style" : ("not_pick",),
					"x" : 14+45,
					"y" : 37,
					"image" : IMG_DIR+"page_box.tga",
					"children":(
						{
							"name": "page_text",
							"type": "text",
							"style" : ("not_pick",),
							"x" : -8,
							"y" : 0,
							"text": "0/0",
							"horizontal_align":"center",
						},
					),
				},

				{
					"name" : "next_btn",
					"type" : "button",
					"x" : 14+80,
					"y" : 39,
					"default_image" : IMG_DIR+"next_page_0.tga",
					"over_image" : IMG_DIR+"next_page_0.tga",
					"down_image" : IMG_DIR+"next_page_1.tga",
				},

				{
					"name" : "refresh_button",
					"type" : "button",

					"x" : 14,
					"y" : 32,

					"default_image" : IMG_DIR+"gemshop_refreshbutton_down.sub",
					"over_image" : IMG_DIR+"gemshop_refreshbutton_over.sub",
					"down_image" : IMG_DIR+"gemshop_refreshbutton_up.sub",
				},
			),
		},
	),
}