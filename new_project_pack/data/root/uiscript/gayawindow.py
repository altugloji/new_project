import uiScriptLocale

GRID_COLS = 20
GRID_ROWS = 4
SLOT_SIZE = 32
SLOT_GAP = 1
GRID_WIDTH = GRID_COLS * SLOT_SIZE + (GRID_COLS - 1) * SLOT_GAP
GRID_HEIGHT = GRID_ROWS * SLOT_SIZE + (GRID_ROWS - 1) * SLOT_GAP

WINDOW_WIDTH = GRID_WIDTH + 32
WINDOW_HEIGHT = 280

SLOT_LIST = tuple(
	{
		"index": i,
		"x": (i % GRID_COLS) * (SLOT_SIZE + SLOT_GAP),
		"y": (i / GRID_COLS) * (SLOT_SIZE + SLOT_GAP),
		"width": SLOT_SIZE,
		"height": SLOT_SIZE,
	}
	for i in xrange(GRID_COLS * GRID_ROWS)
)

window = {
	"name" : "GayaWindow",
	"x" : 0,
	"y" : 0,
	"style" : ("movable", "float",),
	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,
	"children" :
	(
		{
			"name" : "board",
			"type" : "board",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,
			"children" :
			(
				{
					"name" : "TitleBar",
					"type" : "titlebar",
					"style" : ("attach",),
					"x" : 8,
					"y" : 7,
					"width" : WINDOW_WIDTH - 15,
					"color" : "yellow",
					"children" :
					(
						{ "name":"TitleName", "type":"text", "x":(WINDOW_WIDTH / 2) - 8, "y":3, "text":"Gem Puanlari", "text_horizontal_align":"center" },
					),
				},
				{
					"name" : "DescText",
					"type" : "text",
					"x" : 16,
					"y" : 34,
					"text" : "Gem Puanina cevrilecek esyalar",
				},
				{
					"name":"GayaPoints",
					"type":"text",
					"x":16,
					"y":52,
					"text":"Gaya: 0",
				},
				{
					"name" : "GayaItemSlot",
					"type" : "slot",
					"x" : 16,
					"y" : 70,
					"width" : GRID_WIDTH,
					"height" : GRID_HEIGHT,
					"image" : "d:/ymir work/ui/public/slot_base.sub",
					"slot" : SLOT_LIST,
				},
				{
					"name":"MinusButton",
					"type":"button",
					"x":16,
					"y":225,
					"default_image" : "d:/ymir work/ui/public/small_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/small_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/small_button_03.sub",
					"text":"-",
				},
				{
					"name":"QuantityText",
					"type":"text",
					"x":71,
					"y":231,
					"text":"1",
					"text_horizontal_align":"center",
				},
				{
					"name":"PlusButton",
					"type":"button",
					"x":104,
					"y":225,
					"default_image" : "d:/ymir work/ui/public/small_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/small_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/small_button_03.sub",
					"text":"+",
				},
				{
					"name":"ConvertButton",
					"type":"button",
					"x":WINDOW_WIDTH - 174,
					"y":225,
					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
					"text":"Secileni Cevir x1",
				},
			),
		},
	),
}
