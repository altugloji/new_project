window = {
	"name" : "LuckyDrawWindow",

	"x" : 60,
	"y" : 40,

	"style" : ("movable", "float",),

	"width" : 680,
	"height" : 520,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),

			"x" : 0,
			"y" : 0,

			"width" : 680,
			"height" : 520,

			"title" : "",

			"children" :
			(
				## --- Katilim gereksinimleri paneli (sol ust) ---
				{
					"name" : "ReqBoard",
					"type" : "thinboard",
					"style" : ("not_pick",),

					"x" : 12,
					"y" : 36,

					"width" : 222,
					"height" : 122,

					"children" :
					(
						{ "name" : "ReqTitle", "type" : "text", "x" : 12, "y" : 6, "text" : "",
						  "fontname" : "Arial:16", "style" : ("not_pick",) },

						{ "name" : "YangIcon", "type" : "image", "x" : 16, "y" : 84,
						  "image" : "d:/ymir work/ui/game/windows/money_icon.sub", "style" : ("not_pick",) },
						{ "name" : "YangLabel", "type" : "text", "x" : 38, "y" : 82, "text" : "",
						  "r" : 0.95, "g" : 0.85, "b" : 0.55, "style" : ("not_pick",) },
						{ "name" : "YangValue", "type" : "text", "x" : 126, "y" : 82, "text" : "", "style" : ("not_pick",) },

					),
				},

				## --- Bilet Al blogu (ayri panel): ustte sure, ortada ticket_buy, altta biletlerin ---
				{
					"name" : "BuyBoard",
					"type" : "thinboard",
					"style" : ("not_pick",),

					"x" : 240,
					"y" : 36,

					"width" : 172,
					"height" : 122,

					"children" :
					(
						{ "name" : "TimeText", "type" : "text", "x" : 24, "y" : 6, "text" : "",
						  "fontname" : "Arial:16", "r" : 1.0, "g" : 0.90, "b" : 0.55, "style" : ("not_pick",) },
						{ "name" : "TicketText", "type" : "text", "x" : 14, "y" : 96, "text" : "", "style" : ("not_pick",) },
					),
				},
				{
					"name" : "ReqSlots",
					"type" : "grid_table",

					"x" : 28,
					"y" : 66,

					"start_index" : 0,
					"x_count" : 5,
					"y_count" : 1,
					"x_step" : 33,
					"y_step" : 33,

					"image" : "d:/ymir work/ui/public/slot_base.sub",
				},

				{
					"name" : "RewardButton",
					"type" : "button",

					"x" : 254,
					"y" : 72,

					"text" : "",

					"default_image" : "d:/ymir work/ui/public/large_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/large_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/large_button_03.sub",
				},

				## --- Oduller paneli (sol alt): 5 kazanan satiri, zebra desen ---
				{
					"name" : "PrizeBoard",
					"type" : "thinboard",
					"style" : ("not_pick",),

					"x" : 12,
					"y" : 166,

					"width" : 400,
					"height" : 324,

					"children" :
					(
						{ "name" : "PrizeTitle", "type" : "text", "x" : 200, "y" : 6, "text" : "",
						  "fontname" : "Arial:16", "r" : 1.0, "g" : 0.83, "b" : 0.35,
						  "text_horizontal_align" : "center", "style" : ("not_pick",) },

						## zebra bantlari (metinlerden ONCE: altta kalirlar)
						{ "name" : "ZebraBar0", "type" : "bar", "x" : 8, "y" : 30,  "width" : 384, "height" : 56, "color" : 0x28000000, "style" : ("not_pick",) },
						{ "name" : "ZebraBar1", "type" : "bar", "x" : 8, "y" : 88,  "width" : 384, "height" : 56, "color" : 0x14FFFFFF, "style" : ("not_pick",) },
						{ "name" : "ZebraBar2", "type" : "bar", "x" : 8, "y" : 146, "width" : 384, "height" : 56, "color" : 0x28000000, "style" : ("not_pick",) },
						{ "name" : "ZebraBar3", "type" : "bar", "x" : 8, "y" : 204, "width" : 384, "height" : 56, "color" : 0x14FFFFFF, "style" : ("not_pick",) },
						{ "name" : "ZebraBar4", "type" : "bar", "x" : 8, "y" : 262, "width" : 384, "height" : 56, "color" : 0x28000000, "style" : ("not_pick",) },

						## sira etiketleri: 1 altin, 2 gumus, 3 bronz, 4-5 notr
						{ "name" : "WinnerLabel0", "type" : "text", "x" : 16, "y" : 34,  "text" : "",
						  "r" : 1.00, "g" : 0.84, "b" : 0.20, "style" : ("not_pick",) },
						{ "name" : "WinnerName0",  "type" : "text", "x" : 16, "y" : 56,  "text" : "", "style" : ("not_pick",) },

						{ "name" : "WinnerLabel1", "type" : "text", "x" : 16, "y" : 92,  "text" : "",
						  "r" : 0.83, "g" : 0.83, "b" : 0.88, "style" : ("not_pick",) },
						{ "name" : "WinnerName1",  "type" : "text", "x" : 16, "y" : 114, "text" : "", "style" : ("not_pick",) },

						{ "name" : "WinnerLabel2", "type" : "text", "x" : 16, "y" : 150, "text" : "",
						  "r" : 0.85, "g" : 0.55, "b" : 0.30, "style" : ("not_pick",) },
						{ "name" : "WinnerName2",  "type" : "text", "x" : 16, "y" : 172, "text" : "", "style" : ("not_pick",) },

						{ "name" : "WinnerLabel3", "type" : "text", "x" : 16, "y" : 208, "text" : "",
						  "r" : 0.60, "g" : 0.66, "b" : 0.76, "style" : ("not_pick",) },
						{ "name" : "WinnerName3",  "type" : "text", "x" : 16, "y" : 230, "text" : "", "style" : ("not_pick",) },

						{ "name" : "WinnerLabel4", "type" : "text", "x" : 16, "y" : 266, "text" : "",
						  "r" : 0.60, "g" : 0.66, "b" : 0.76, "style" : ("not_pick",) },
						{ "name" : "WinnerName4",  "type" : "text", "x" : 16, "y" : 288, "text" : "", "style" : ("not_pick",) },
					),
				},
				{
					"name" : "RewardSlots",
					"type" : "grid_table",

					"x" : 182,
					"y" : 200,

					"start_index" : 0,
					"x_count" : 5,
					"y_count" : 5,
					"x_step" : 33,
					"y_step" : 58,

					"image" : "d:/ymir work/ui/public/slot_base.sub",
				},

				## --- Katilimcilar paneli (sag kolon, tam boy) ---
				{
					"name" : "JoinerBoard",
					"type" : "thinboard",
					"style" : ("not_pick",),

					"x" : 420,
					"y" : 36,

					"width" : 248,
					"height" : 454,

					"children" :
					(
						{ "name" : "JoinerTitle", "type" : "text", "x" : 12, "y" : 8, "text" : "", "style" : ("not_pick",) },

						{ "name" : "JoinerName0", "type" : "text", "x" : 12, "y" : 32, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName1", "type" : "text", "x" : 12, "y" : 53, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName2", "type" : "text", "x" : 12, "y" : 74, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName3", "type" : "text", "x" : 12, "y" : 95, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName4", "type" : "text", "x" : 12, "y" : 116, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName5", "type" : "text", "x" : 12, "y" : 137, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName6", "type" : "text", "x" : 12, "y" : 158, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName7", "type" : "text", "x" : 12, "y" : 179, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName8", "type" : "text", "x" : 12, "y" : 200, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName9", "type" : "text", "x" : 12, "y" : 221, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName10", "type" : "text", "x" : 12, "y" : 242, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName11", "type" : "text", "x" : 12, "y" : 263, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName12", "type" : "text", "x" : 12, "y" : 284, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName13", "type" : "text", "x" : 12, "y" : 305, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName14", "type" : "text", "x" : 12, "y" : 326, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName15", "type" : "text", "x" : 12, "y" : 347, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName16", "type" : "text", "x" : 12, "y" : 368, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName17", "type" : "text", "x" : 12, "y" : 389, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName18", "type" : "text", "x" : 12, "y" : 410, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerName19", "type" : "text", "x" : 12, "y" : 431, "text" : "", "style" : ("not_pick",) },

						{ "name" : "JoinerCount0", "type" : "text", "x" : 168, "y" : 32, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount1", "type" : "text", "x" : 168, "y" : 53, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount2", "type" : "text", "x" : 168, "y" : 74, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount3", "type" : "text", "x" : 168, "y" : 95, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount4", "type" : "text", "x" : 168, "y" : 116, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount5", "type" : "text", "x" : 168, "y" : 137, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount6", "type" : "text", "x" : 168, "y" : 158, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount7", "type" : "text", "x" : 168, "y" : 179, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount8", "type" : "text", "x" : 168, "y" : 200, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount9", "type" : "text", "x" : 168, "y" : 221, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount10", "type" : "text", "x" : 168, "y" : 242, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount11", "type" : "text", "x" : 168, "y" : 263, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount12", "type" : "text", "x" : 168, "y" : 284, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount13", "type" : "text", "x" : 168, "y" : 305, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount14", "type" : "text", "x" : 168, "y" : 326, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount15", "type" : "text", "x" : 168, "y" : 347, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount16", "type" : "text", "x" : 168, "y" : 368, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount17", "type" : "text", "x" : 168, "y" : 389, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount18", "type" : "text", "x" : 168, "y" : 410, "text" : "", "style" : ("not_pick",) },
						{ "name" : "JoinerCount19", "type" : "text", "x" : 168, "y" : 431, "text" : "", "style" : ("not_pick",) },
					),
				},
				{
					"name" : "RefreshButton",
					"type" : "button",

					"x" : 594,
					"y" : 40,

					"text" : "",

					"default_image" : "d:/ymir work/ui/public/middle_button_01.sub",
					"over_image" : "d:/ymir work/ui/public/middle_button_02.sub",
					"down_image" : "d:/ymir work/ui/public/middle_button_03.sub",
				},

				## --- Alt bilgi satiri ---
				{ "name" : "BottomNote", "type" : "text", "x" : 340, "y" : 496, "text" : "", "text_horizontal_align" : "center", "style" : ("not_pick",) },
			),
		},
	),
}
