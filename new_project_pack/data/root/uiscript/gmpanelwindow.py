import uiScriptLocale

MARGIN_X = 10
CONTENT_W = 488
WINDOW_WIDTH = CONTENT_W + (MARGIN_X * 2)

SEARCH_Y = 33
SEARCH_H = 18
COUNT_Y = SEARCH_Y + SEARCH_H + 10
COUNT_H = 17
LIST_Y = COUNT_Y + COUNT_H + 4

VIEW_COUNT = 20
ROW_H = 22
HEADER_H = 20
LISTBOX_H = VIEW_COUNT * ROW_H
LIST_H = (HEADER_H + 2) + LISTBOX_H + 6
WINDOW_HEIGHT = LIST_Y + LIST_H + 10

window = {
	"name" : "GmPlayerPanelWindow",
	"style" : ("movable", "float",),
	"x" : 0,
	"y" : 0,
	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,
	"children" :
	(
		{
			"name" : "Board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,
			"title" : "GM Oyuncu Paneli",
			"children" :
			(
				{
					"name" : "SearchLabel",
					"type" : "text",
					"x" : MARGIN_X,
					"y" : 36,
					"text" : "Ara:",
					"outline" : 1,
				},
				{
					"name" : "SearchSlot",
					"type" : "slotbar",
					"x" : MARGIN_X,
					"y" : SEARCH_Y,
					"width" : CONTENT_W,
					"height" : SEARCH_H,
				},
				{
					"name" : "CountSlot",
					"type" : "horizontalbar",
					"x" : MARGIN_X,
					"y" : COUNT_Y,
					"width" : CONTENT_W,
					"children" :
					(
						{
							"name" : "CountText",
							"type" : "text",
							"x" : 0,
							"y" : 0,
							"text" : "",
						},
					),
				},
			),
		},
	),
}
