import uiScriptLocale

window = {
	"name" : "BulkPotionWindow",
	"x" : 0,
	"y" : 0,
	"style" : ("movable", "float",),
	"width" : 215,
	"height" : 210,
	"children" :
	(
		{
			"name" : "Board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : 215,
			"height" : 210,
			"title" : uiScriptLocale.BULK_POTION_TITLE,
			"children" :
			(
				{
					"name" : "ItemSlot",
					"type" : "grid_table",
					"x" : 12,
					"y" : 34,
					"start_index" : 0,
					"x_count" : 6,
					"y_count" : 4,
					"x_step" : 32,
					"y_step" : 32,
					"image" : "d:/ymir work/ui/public/Slot_Base.sub",
				},
				{
					"name" : "UseButton",
					"type" : "button",
					"x" : 28,
					"y" : 175,
					"width" : 61,
					"height" : 21,
					"text" : uiScriptLocale.BULK_POTION_USE,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
				{
					"name" : "ClearButton",
					"type" : "button",
					"x" : 118,
					"y" : 175,
					"width" : 61,
					"height" : 21,
					"text" : uiScriptLocale.BULK_POTION_CLEAR,
					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},
			),
		},
	),
}
