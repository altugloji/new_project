import uiScriptLocale

# Hediye Siralamasi penceresi (400x480). Klasik Player Rank gorunumu.
# Sekmeler, sutun basliklari, satirlar ve "kendi siram" satiri root/uigiftrank.py
# icinde KODLA olusturulur (koyu bar + cerceve + metin); bu iskelet sadece
# board + liste zeminini tasir (yukleniyor metni z-order icin kodda EN SON olusturulur).

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 480

window = {
	"name" : "GiftRankDialog",
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
			"title" : "Hediye Siralamasi",

			"children" :
			(
				## liste zemini (satirlar ve tum metinler bunun ustune kodla cizilir;
				## yukleniyor metni z-order icin kodda EN SON olusturulur)
				{
					"name" : "list_bg",
					"type" : "thinboard",
					"x" : 10,
					"y" : 90,
					"width" : 380,
					"height" : 312,
				},
			),
		},
	),
}
