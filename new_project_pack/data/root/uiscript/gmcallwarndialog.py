import uiScriptLocale

ROOT_PUBLIC = "d:/ymir work/ui/public/"

window = {
	"name" : "GmCallWarnDialog",
	"style" : ("movable", "float",),

	"x" : (SCREEN_WIDTH - 500) / 2,
	"y" : (SCREEN_HEIGHT - 135) / 2,

	"width" : 500,
	"height" : 135,

	"children" :
	(
		{
			"name" : "board",
			"type" : "thinboard",

			"x" : 0,
			"y" : 0,

			"width" : 500,
			"height" : 135,

			"children" :
			(
				{
					"name" : "title",
					"type" : "text",

					"x" : 0,
					"y" : 10,

					"text" : uiScriptLocale.MESSAGE,

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "center",
				},
				{
					"name" : "body_line_1",
					"type" : "text",

					"x" : 0,
					"y" : 20,

					"text" : "",

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "top",
				},
				{
					"name" : "body_line_2",
					"type" : "text",

					"x" : 0,
					"y" : 32,

					"text" : "",

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "top",
				},
				{
					"name" : "body_line_3",
					"type" : "text",

					"x" : 0,
					"y" : 44,

					"text" : "",

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "top",
				},
				{
					"name" : "body_line_4",
					"type" : "text",

					"x" : 0,
					"y" : 56+15,

					"text" : "",

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "top",
				},
				{
					"name" : "body_line_5",
					"type" : "text",

					"x" : 0,
					"y" : 68+15,

					"text" : "",

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "top",
				},
				{
					"name" : "body_line_6",
					"type" : "text",

					"x" : 0,
					"y" : 80+15,

					"text" : "",

					"horizontal_align" : "center",
					"text_horizontal_align" : "center",
					"text_vertical_align" : "top",
				},
				{
					"name" : "accept",
					"type" : "button",

					"x" : -40,
					"y" : 100,

					"width" : 61,
					"height" : 21,

					"horizontal_align" : "center",
					"text" : uiScriptLocale.YES,

					"default_image" : ROOT_PUBLIC + "middle_button_01.sub",
					"over_image" : ROOT_PUBLIC + "middle_button_02.sub",
					"down_image" : ROOT_PUBLIC + "middle_button_03.sub",
				},
				{
					"name" : "cancel",
					"type" : "button",

					"x" : 40,
					"y" : 100,

					"width" : 61,
					"height" : 21,

					"horizontal_align" : "center",
					"text" : uiScriptLocale.NO,

					"default_image" : ROOT_PUBLIC + "middle_button_01.sub",
					"over_image" : ROOT_PUBLIC + "middle_button_02.sub",
					"down_image" : ROOT_PUBLIC + "middle_button_03.sub",
				},
			),
		},
	),
}
