
GRID_COLUMNS = 5
GRID_ROWS = 8

FULL_WIDTH = 12 + GRID_COLUMNS * 32 + 12
TITLE_CONTENT_TOP = 36
GRID_HEIGHT = GRID_ROWS * 32

PAGE_BAR_Y = TITLE_CONTENT_TOP + GRID_HEIGHT + 8
HORIZONTAL_BAR_Y = PAGE_BAR_Y + 28
FOOTER_Y = HORIZONTAL_BAR_Y + 21

CHEST_BOARD_HEIGHT = FOOTER_Y + 42 + 10

window = {
	"name" : "KygnChestInfoWindow",
	"style" : ("movable", "float",),
	"x" : 420,
	"y" : 167,
	"width" : 184,
	"height" : 433,
	"children" : (
		{
			"name" : "ChestBoard",
			"type" : "board_with_titlebar",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : 190,
			"height" : 323,
			"title" : "",
			"children" : (
				{
					"name" : "ItemSlot",
					"type" : "grid_table",
					"x" : 15,
					"y" : 36,
					"start_index" : 0,
					"x_count" : 5,
					"y_count" : 8,
					"x_step" : 32,
					"y_step" : 32,
					"image" : "d:/ymir work/ui/public/slot_base.sub",
				},
				{
					"name" : "PrevButton",
					"type" : "button",
					"x" : 49,
					"y" : 297,
					"default_image" : "d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub",
					"over_image" : "d:/ymir work/ui/public/public_intro_btn/prev_btn_02.sub",
					"down_image" : "d:/ymir work/ui/public/public_intro_btn/prev_btn_01.sub",
				},
				{
					"name" : "CurrentPage",
					"type" : "text",
					"x" : -3,
					"y" : 297,
					"width" : 32,
					"height" : 20,
					"text" : "1",
					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
				},
				{
					"name" : "NextButton",
					"type" : "button",
					"x" : 70,
					"y" : 297,
					"horizontal_align" : "right",
					"default_image" : "d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub",
					"over_image" : "d:/ymir work/ui/public/public_intro_btn/next_btn_02.sub",
					"down_image" : "d:/ymir work/ui/public/public_intro_btn/next_btn_01.sub",
				},
			),
		},
	),
}
