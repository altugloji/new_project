import localeInfo

IMG_DIR = "d:/ymir work/ui/game/exchange_log/"

WINDOW_SIZE = [653, 428]

window = {
	"name" : "ExchangeLogWindow",
	# "style" : ("movable", "float","animate",),
	"style" : ("movable", "float",),
	"x" : 0, "y" : 0,
	"width" : WINDOW_SIZE[0], "height" : WINDOW_SIZE[1],
	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"x" : 0,"y" : 0,"title": localeInfo.EXCHANGELOG_TITLE+"(Null)",
			"width" : WINDOW_SIZE[0],"height" : WINDOW_SIZE[1],
			"children":
			(
				{
					"name" : "bg",
					"type" : "image",
					"x" : 8,"y" : 30,
					"image": IMG_DIR + "bg.tga",
					"children":
					(
						# Titles
						{"name" : "ownername_title","type" : "text","text_horizontal_align" : "left" ,"x" : 43,"y" : 8,"text": localeInfo.EXCHANGELOG_OWNERNAME,},
						{"name" : "targetname_title","type" : "text","text_horizontal_align" : "left" ,"x" : 151,"y" : 8,"text": localeInfo.EXCHANGELOG_TARGETNAME,},
						{"name" : "goldtraded_title","type" : "text","text_horizontal_align" : "left" ,"x" : 255,"y" : 8,"text": localeInfo.EXCHANGELOG_GOLDTRADED,},
						{"name" : "date_title","type" : "text","text_horizontal_align" : "left" ,"x" : 362,"y" : 8,"text": localeInfo.EXCHANGELOG_DATE,},
						{"name" : "ip_title","type" : "text","text_horizontal_align" : "left" ,"x" : 456,"y" : 8,"text": localeInfo.EXCHANGELOG_IP,},
						{"name" : "content_title","type" : "text","text_horizontal_align" : "left" ,"x" : 545,"y" : 8,"text": localeInfo.EXCHANGELOG_CONTENT,},

						# Page Buttons
						{"name" : "first_prev_button","type" : "button","x" : 71,"y" : 368,"default_image" : IMG_DIR + "first_page_0.tga","over_image" : IMG_DIR + "first_page_0.tga","down_image" : IMG_DIR + "first_page_1.tga",},
						{"name" : "last_next_button","type" : "button","x" : 267,"y" : 368,"default_image" : IMG_DIR + "last_page_0.tga","over_image" : IMG_DIR + "last_page_0.tga","down_image" : IMG_DIR + "last_page_1.tga",},
						{"name" : "prev_button","type" : "button","x" : 87,"y" : 368,"default_image" : IMG_DIR + "back_page_0.tga","over_image" : IMG_DIR + "back_page_0.tga","down_image" : IMG_DIR + "back_page_1.tga",},
						{"name" : "next_button","type" : "button","x" : 250,"y" : 368,"default_image" : IMG_DIR + "next_page_0.tga","over_image" : IMG_DIR + "next_page_0.tga","down_image" : IMG_DIR + "next_page_1.tga",},
						
						# Page Index Buttons
						{"name" : "page_0","type" : "button","x" : 104 + (0 * 29),"y" : 360,"text": "1","default_image" : IMG_DIR + "page_box.tga","over_image" : IMG_DIR + "page_box.tga","down_image" : IMG_DIR + "page_box.tga",},
						{"name" : "page_1","type" : "button","x" : 104 + (1 * 29),"y" : 360,"text": "2","default_image" : IMG_DIR + "page_box.tga","over_image" : IMG_DIR + "page_box.tga","down_image" : IMG_DIR + "page_box.tga",},
						{"name" : "page_2","type" : "button","x" : 104 + (2 * 29),"y" : 360,"text": "3","default_image" : IMG_DIR + "page_box.tga","over_image" : IMG_DIR + "page_box.tga","down_image" : IMG_DIR + "page_box.tga",},
						{"name" : "page_3","type" : "button","x" : 104 + (3 * 29),"y" : 360,"text": "4","default_image" : IMG_DIR + "page_box.tga","over_image" : IMG_DIR + "page_box.tga","down_image" : IMG_DIR + "page_box.tga",},
						{"name" : "page_4","type" : "button","x" : 104 + (4 * 29),"y" : 360,"text": "5","default_image" : IMG_DIR + "page_box.tga","over_image" : IMG_DIR + "page_box.tga","down_image" : IMG_DIR + "page_box.tga",},

						#Delete Buttons
						# {"name" : "delete_selected","type" : "button","x" : 356, "y" : 360,"text": localeInfo.EXCHANGELOG_DELETESELECTED,"default_image" : IMG_DIR + "button_0.tga","over_image" : IMG_DIR + "button_1.tga","down_image" : IMG_DIR + "button_2.tga",},
						# {"name" : "delete_all","type" : "button","x" : 492, "y" : 360,"text": localeInfo.EXCHANGELOG_DELETEALL,"default_image" : IMG_DIR + "button_0.tga","over_image" : IMG_DIR + "button_1.tga","down_image" : IMG_DIR + "button_2.tga",},

						{"name" : "listbox","type" : "listbox_new","x" : 2, "y" : 36, "width" : 628,"height" : 313,},

					),
				},
			),
		},
	),
}
