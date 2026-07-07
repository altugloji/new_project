import uiScriptLocale

# Hediye Gonder penceresi (1100x650). Metnin tamami root/uigiftsend.py icinde
# SetText ile atanir (locale override + fallback), boylece bu iskelet metin-bagimsizdir.
# Sol panel: 5x3 = 15 kart (113x153 png), sayfalama YOK.

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 650

window = {
	"name" : "GiftSendDialog",
	"style" : ("movable", "float",),
	"x" : SCREEN_WIDTH / 2 - WINDOW_WIDTH / 2,
	"y" : SCREEN_HEIGHT / 2 - WINDOW_HEIGHT / 2,
	"width" : WINDOW_WIDTH,
	"height" : WINDOW_HEIGHT,

	"children" :
	(
		{
			"name" : "board",
			"type" : "board_with_titlebar",
			"style" : ("attach",),
			"x" : 0,
			"y" : 0,
			"width" : WINDOW_WIDTH,
			"height" : WINDOW_HEIGHT,
			"title" : "Hediye Gonder",

			"children" :
			(
				## ---- Ust kisim: oyuncu adi + Bul + EP + yardim ----
				{ "name":"player_name_label", "type":"text", "x":20, "y":40, "text":"" },
				{
					"name":"player_name_slot", "type":"thinboard",
					"x":110, "y":36, "width":215, "height":20,
					"children":
					(
						{ "name":"name_hint", "type":"text", "x":5, "y":3, "text":"", "r":0.53, "g":0.53, "b":0.53 },
					),
				},
				{
					"name":"find_button", "type":"button",
					"x":335, "y":35, "width":61, "height":21, "text":"",
					"default_image":"d:/ymir work/ui/public/middle_button_01.sub",
					"over_image":"d:/ymir work/ui/public/middle_button_02.sub",
					"down_image":"d:/ymir work/ui/public/middle_button_03.sub",
				},
				{ "name":"ep_text", "type":"text", "x":650, "y":40, "text":"" },
				{
					"name":"rank_button", "type":"button",
					"x":985, "y":35, "width":61, "height":21, "text":"",
					"default_image":"d:/ymir work/ui/public/middle_button_01.sub",
					"over_image":"d:/ymir work/ui/public/middle_button_02.sub",
					"down_image":"d:/ymir work/ui/public/middle_button_03.sub",
				},
				{
					"name":"help_button", "type":"button",
					"x":1055, "y":35, "width":20, "height":20, "text":"?",
					"default_image":"d:/ymir work/ui/public/small_button_01.sub",
					"over_image":"d:/ymir work/ui/public/small_button_02.sub",
					"down_image":"d:/ymir work/ui/public/small_button_03.sub",
				},

				## ---- Sol panel: Hediyeler (5x3 kart, sayfalama yok) ----
				{
					"name":"gift_panel", "type":"thinboard",
					"x":15, "y":70, "width":620, "height":525,
					"children":
					(
						{ "name":"gift_panel_title", "type":"text", "x":15, "y":10, "text":"" },
						{
							"name":"gift_slot_base", "type":"thinboard",
							"x":12, "y":32, "width":596, "height":481,
						},
					),
				},

				## ---- Sag ust panel: Secili Hediye ----
				{
					"name":"selected_panel", "type":"thinboard",
					"x":645, "y":70, "width":435, "height":250,
					"children":
					(
						{ "name":"selected_title", "type":"text", "x":15, "y":10, "text":"" },
						{
							"name":"preview_slot", "type":"thinboard",
							"x":15, "y":35, "width":121, "height":161,
						},
						{ "name":"preview_image", "type":"image", "x":19, "y":39, "image":"d:/ymir work/ui/public/slot_base.sub" },
						{ "name":"gift_name_text", "type":"text", "x":150, "y":40, "text":"", "fontsize":"LARGE" },

						{ "name":"count_label", "type":"text", "x":150, "y":80, "text":"" },
						{
							"name":"count_down_button", "type":"button",
							"x":215, "y":76, "width":20, "height":20, "text":"-",
							"default_image":"d:/ymir work/ui/public/small_button_01.sub",
							"over_image":"d:/ymir work/ui/public/small_button_02.sub",
							"down_image":"d:/ymir work/ui/public/small_button_03.sub",
						},
						{
							"name":"count_slot", "type":"thinboard",
							"x":238, "y":75, "width":44, "height":22,
							"children":
							(
								{ "name":"count_value", "type":"text", "x":22, "y":4, "text":"1", "text_horizontal_align":"center" },
							),
						},
						{
							"name":"count_up_button", "type":"button",
							"x":285, "y":76, "width":20, "height":20, "text":"+",
							"default_image":"d:/ymir work/ui/public/small_button_01.sub",
							"over_image":"d:/ymir work/ui/public/small_button_02.sub",
							"down_image":"d:/ymir work/ui/public/small_button_03.sub",
						},

						{ "name":"price_label", "type":"text", "x":150, "y":115, "text":"" },
						{ "name":"price_text", "type":"text", "x":215, "y":115, "text":"" },

						{ "name":"desc_text", "type":"text", "x":150, "y":150, "text":"" },
					),
				},

				## ---- Sag orta panel: Hediye Mesaji ----
				{
					"name":"message_panel", "type":"thinboard",
					"x":645, "y":330, "width":435, "height":140,
					"children":
					(
						{ "name":"message_title", "type":"text", "x":15, "y":10, "text":"" },
						{ "name":"message_optional", "type":"text", "x":110, "y":10, "text":"" },
						{
							"name":"message_slot", "type":"thinboard",
							"x":15, "y":32, "width":405, "height":95,
							"children":
							(
								{ "name":"message_hint", "type":"text", "x":6, "y":5, "text":"", "r":0.53, "g":0.53, "b":0.53 },
							),
						},
					),
				},

				## ---- Checkbox'lar ----
				{
					"name":"package_check_button", "type":"button",
					"x":650, "y":485, "width":16, "height":16, "text":"",
					"default_image":"d:/ymir work/ui/game/refine/checkbox.tga",
					"over_image":"d:/ymir work/ui/game/refine/checkbox.tga",
					"down_image":"d:/ymir work/ui/game/refine/checked.tga",
				},
				{ "name":"package_check_label", "type":"text", "x":673, "y":487, "text":"" },
				{
					"name":"anon_check_button", "type":"button",
					"x":835, "y":485, "width":16, "height":16, "text":"",
					"default_image":"d:/ymir work/ui/game/refine/checkbox.tga",
					"over_image":"d:/ymir work/ui/game/refine/checkbox.tga",
					"down_image":"d:/ymir work/ui/game/refine/checked.tga",
				},
				{ "name":"anon_check_label", "type":"text", "x":858, "y":487, "text":"" },

				## ---- Alt kisim: Toplam Ucret + Gonder/Iptal ----
				{ "name":"total_label", "type":"text", "x":30, "y":608, "text":"" },
				{ "name":"total_text", "type":"text", "x":150, "y":608, "text":"", "fontsize":"LARGE" },
				{
					"name":"send_button", "type":"button",
					"x":890, "y":600, "width":90, "height":26, "text":"",
					"default_image":"d:/ymir work/ui/public/large_button_01.sub",
					"over_image":"d:/ymir work/ui/public/large_button_02.sub",
					"down_image":"d:/ymir work/ui/public/large_button_03.sub",
				},
				{
					"name":"cancel_button", "type":"button",
					"x":985, "y":600, "width":90, "height":26, "text":"",
					"default_image":"d:/ymir work/ui/public/large_button_01.sub",
					"over_image":"d:/ymir work/ui/public/large_button_02.sub",
					"down_image":"d:/ymir work/ui/public/large_button_03.sub",
				},
			),
		},
	),
}
