import uiScriptLocale
import item
import app

COSTUME_START_INDEX = item.COSTUME_SLOT_START

if app.ENABLE_WEAPON_COSTUME_SYSTEM:
	window = {
		"name" : "CostumeWindow",

		"x" : SCREEN_WIDTH - 175 - 140,
		"y" : SCREEN_HEIGHT - 37 - 565,

		"style" : ("movable", "float",),

		"width" : 140,
		"height" : (180 + 90),

		"children" :
		(
			{
				"name" : "board",
				"type" : "board",
				"style" : ("attach",),

				"x" : 0,
				"y" : 0,

				"width" : 140,
				"height" : (180 + 90),

				"children" :
				(
					## Title
					{
						"name" : "TitleBar",
						"type" : "titlebar",
						"style" : ("attach",),

						"x" : 6,
						"y" : 6,

						"width" : 130,
						"color" : "yellow",

						"children" :
						(
							{ "name":"TitleName", "type":"text", "x":60, "y":3, "text":uiScriptLocale.COSTUME_WINDOW_TITLE, "text_horizontal_align":"center" },
						),
					},

					## Equipment Slot
					{
						"name" : "Costume_Base",
						"type" : "image",

						"x" : 13,
						"y" : 38,

						"image" : uiScriptLocale.LOCALE_UISCRIPT_PATH + "costume/new_costume_bg.jpg",

						"children" :
						(

							{
								"name" : "CostumeSlot",
								"type" : "slot",

								"x" : 3,
								"y" : 3,

								"width" : 127,
								"height" : 175+30,

								"slot" : (
											{"index":COSTUME_START_INDEX+0, "x":37, "y":51, "width":32, "height":64},	#zırh
											{"index":COSTUME_START_INDEX+1, "x":37, "y":14, "width":32, "height":32},	#kask
											{"index":COSTUME_START_INDEX+2, "x":37, "y":126, "width":32, "height":32},	#binek
											{"index":180+25, "x":37, "y":126+37, "width":32, "height":32},
																						# {"index":COSTUME_START_INDEX+3, "x":37, "y":126, "width":32, "height":32},
											# {"index":item.COSTUME_SLOT_WEAPON, "x":13, "y":13, "width":32, "height":96}, #silah
										),
							},
						),
					},
				),
			},
		),
	}
elif app.ENABLE_MOUNT_COSTUME_SYSTEM:
	if app.ENABLE_ACCE_COSTUME_SYSTEM:
	    window = {
		    "name" : "CostumeWindow",

		    "x" : SCREEN_WIDTH - 175 - 140,
		    "y" : SCREEN_HEIGHT - 37 - 565,

		    "style" : ("movable", "float",),

		    "width" : 140,
		    "height" : (180 + 47),

		    "children" :
		    (
			    {
				    "name" : "board",
				    "type" : "board",
				    "style" : ("attach",),

				    "x" : 0,
				    "y" : 0,

				    "width" : 140,
				    "height" : (180 + 47),

				    "children" :
				    (
					    ## Title
					    {
						    "name" : "TitleBar",
						    "type" : "titlebar",
						    "style" : ("attach",),

						    "x" : 6,
						    "y" : 6,

						    "width" : 130,
						    "color" : "yellow",

						    "children" :
						    (
							    { "name":"TitleName", "type":"text", "x":60, "y":3, "text":uiScriptLocale.COSTUME_WINDOW_TITLE, "text_horizontal_align":"center" },
						    ),
					    },

					    ## Equipment Slot
					    {
						    "name" : "Costume_Base",
						    "type" : "image",

						    "x" : 13,
						    "y" : 38,

						    "image" : uiScriptLocale.LOCALE_UISCRIPT_PATH + "costume/new_costume_bg.jpg",

						    "children" :
						    (

							    {
								    "name" : "CostumeSlot",
								    "type" : "slot",

								    "x" : 3,
								    "y" : 3,

								    "width" : 127,
								    "height" : 145,

								    "slot" : (
											    {"index":COSTUME_START_INDEX+0, "x":62, "y":45, "width":32, "height":64},
											    {"index":COSTUME_START_INDEX+1, "x":62, "y": 9, "width":32, "height":32},
											    {"index":COSTUME_START_INDEX+2, "x":13, "y":126, "width":32, "height":32},
											    {"index":COSTUME_START_INDEX+3, "x":62, "y":126, "width":32, "height":32},
											    {"index":180+25, "x":13, "y":9, "width":32, "height":32},	#eldiven
											    										    ),
							    },
						    ),
					    },

				    ),
			    },
		    ),
	    }
	else:
	    window = {
		    "name" : "CostumeWindow",

		    "x" : SCREEN_WIDTH - 175 - 140,
		    "y" : SCREEN_HEIGHT - 37 - 565,

		    "style" : ("movable", "float",),

		    "width" : 140,
		    "height" : (180 + 47),

		    "children" :
		    (
			    {
				    "name" : "board",
				    "type" : "board",
				    "style" : ("attach",),

				    "x" : 0,
				    "y" : 0,

				    "width" : 140,
				    "height" : (180 + 47),

				    "children" :
				    (
					    ## Title
					    {
						    "name" : "TitleBar",
						    "type" : "titlebar",
						    "style" : ("attach",),

						    "x" : 6,
						    "y" : 6,

						    "width" : 130,
						    "color" : "yellow",

						    "children" :
						    (
							    { "name":"TitleName", "type":"text", "x":60, "y":3, "text":uiScriptLocale.COSTUME_WINDOW_TITLE, "text_horizontal_align":"center" },
						    ),
					    },

					    ## Equipment Slot
					    {
						    "name" : "Costume_Base",
						    "type" : "image",

						    "x" : 13,
						    "y" : 38,

						    "image" : uiScriptLocale.LOCALE_UISCRIPT_PATH + "costume/new_costume_bg.jpg",

						    "children" :
						    (

							    {
								    "name" : "CostumeSlot",
								    "type" : "slot",

								    "x" : 3,
								    "y" : 3,

								    "width" : 127,
								    "height" : 145,

								    "slot" : (
											    {"index":COSTUME_START_INDEX+0, "x":62, "y":45, "width":32, "height":64},
											    {"index":COSTUME_START_INDEX+1, "x":62, "y": 9, "width":32, "height":32},
											    {"index":COSTUME_START_INDEX+2, "x":13, "y":125, "width":32, "height":32},
											    {"index":180+25, "x":13, "y":9, "width":32, "height":32},	#eldiven
											    										    ),
							    },
						    ),
					    },

				    ),
			    },
		    ),
	    }
else:
	window = {
		"name" : "CostumeWindow",

		"x" : SCREEN_WIDTH - 175 - 140,
		"y" : SCREEN_HEIGHT - 37 - 565,

		"style" : ("movable", "float",),

		"width" : 140,
		"height" : 180,

		"children" :
		(
			{
				"name" : "board",
				"type" : "board",
				"style" : ("attach",),

				"x" : 0,
				"y" : 0,

				"width" : 140,
				"height" : 180,

				"children" :
				(
					## Title
					{
						"name" : "TitleBar",
						"type" : "titlebar",
						"style" : ("attach",),

						"x" : 6,
						"y" : 6,

						"width" : 130,
						"color" : "yellow",

						"children" :
						(
							{ "name":"TitleName", "type":"text", "x":60, "y":3, "text":uiScriptLocale.COSTUME_WINDOW_TITLE, "text_horizontal_align":"center" },
						),
					},

					## Equipment Slot
					{
						"name" : "Costume_Base",
						"type" : "image",

						"x" : 13,
						"y" : 38,

						"image" : uiScriptLocale.LOCALE_UISCRIPT_PATH + "costume/costume_bg.jpg",

						"children" :
						(

							{
								"name" : "CostumeSlot",
								"type" : "slot",

								"x" : 3,
								"y" : 3,

								"width" : 127,
								"height" : 145,

								"slot" : (
											{"index":COSTUME_START_INDEX+0, "x":61, "y":45, "width":32, "height":64},
											{"index":COSTUME_START_INDEX+1, "x":61, "y": 8, "width":32, "height":32},
											{"index":COSTUME_START_INDEX+2, "x":5, "y":145, "width":32, "height":32},
											{"index":180+25, "x":5, "y":8, "width":32, "height":32},	#eldiven
																					),
							},
						),
					},

				),
			},
		),
	}
