import localeInfo

IMG_DIR = "d:/ymir work/ui/game/exchange_log/"

window = {
	"name" : "ExchangeLogWindow",
	"style" : (),
	"x" : 0, "y" : 0,
	"width" : 614, "height" : 35,
	"children" :
	(
		{
			"name" : "board",
			"type" : "expanded_image",
			"x" : 0,"y" : 0,
			"image" : IMG_DIR+"log_bar.tga",
			"children":
			(
				{"name" : "select_btn","type" : "expanded_image","x":0,"y":0,},

				{"name" : "owner","type" : "text","fontname": "Tahoma:11","text_horizontal_align" : "center" ,"x" : 75,"y" : 10,},
				{"name" : "target","type" : "text","fontname": "Tahoma:11","text_horizontal_align" : "center" ,"x" : 180,"y" : 10,},
				{"name" : "gold","type" : "text","fontname": "Tahoma:11","text_horizontal_align" : "left" ,"x" : 274,"y" : 10,},
				{"name" : "date","type" : "text","fontname": "Tahoma:11","text_horizontal_align" : "center" ,"x" : 370,"y" : 10,},
				{"name" : "ip","type" : "text","fontname": "Tahoma:11","text_horizontal_align" : "center" ,"x" : 460,"y" : 10,},

				{"name" : "content","type" : "button","x" : 520,"y" : 8,"default_image" : IMG_DIR + "view_0.tga","over_image" : IMG_DIR + "view_1.tga","down_image" : IMG_DIR + "view_2.tga",},

			),
		},
	),
}
