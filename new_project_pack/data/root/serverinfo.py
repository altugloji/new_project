import app
import localeInfo
from constInfo import TextColor
app.ServerName = None

# Auth dagitimi: client her acilista authlist'ten rastgele bir port secer.
# NOT: eski time-based RNG (int(time*1e6) % len) ms cozunurlukte HEP index 0 veriyordu
# (1000'in katlari 4'e tam bolunur), yani herkes 30001'e baglaniyordu. Binary RNG
# app.GetRandom kullaniyoruz: stdlib gerektirmez ve her client'ta gercekten farkli.
def get_item_from_list(_list):
	return _list[app.GetRandom(0, len(_list) - 1)]

SRV1 = {
	"name": "AyazMt2",
	"host":"45.131.198.34",
	"srv1-auth1":30001,
	"srv1-auth2":30003,
	"srv1-auth3":30005,
	"srv1-auth4":30007,
	"srv1-auth5":30009,
	"srv1-auth6":30011,
	"srv1-auth7":30013,
	"srv1-auth8":30015,
	"ch1":30017,
	"ch2":30025,
	"ch3":30033,
	"ch4":30041,
	"ch5":30049,
	"ch6":30057,
	"ch7":30065,
	"ch8":30073,
	"ch9":30081,
	"ch10":30089,
	"ch11":30097,
	"ch12":30105,

	"authlist": [ 30001,30003,30005,30007,30009,30011,30013,30015, ],
}

# ---- AUTH FAILOVER (otomatik auth gecisi) -------------------------------------
# Oturum acarken secili auth basarisiz olur (TCP reddi/timeout) veya YAVAS kalirsa
# (bagli ama el sikismasi gelmiyor), client otomatik olarak authlist'teki diger auth
# portlarina sirayla gecer. Tum auth'lar tukenince normal hata mesaji gosterilir.
# Sadece client-side calisir; sunucu degisikligi gerektirmez (her auth core bagimsiz).
ENABLE_AUTH_FAILOVER = True
# Bagli ama auth/oyun el sikismasi bu kadar saniyede gelmezse auth "yavas" sayilir ve
# bir sonraki auth'a gecilir. Bu sure TUM auth bacagini kapsar; auth basarili olduktan
# SONRA oyun-kanali asamasinda watchdog zaten devre disi (net.IsConnect/app.loggined
# guard'i, bkz. intrologin.__OnAuthSlowTimeout). Yine de auth handshake + ~3sn oyun
# baglanti penceresini RAHAT asmasi icin C++ connect timeout'undan (~3sn) belirgin buyuk
# olmali. Acilis (5000+) gibi cok yogun anlarda yanlis gecis gorurseniz yukseltin.
AUTH_FAILOVER_SLOW_TIMEOUT = 20.0
# 0 = tum auth'lari sirayla dene. >0 ise en fazla bu kadar auth denenir.
AUTH_FAILOVER_MAX_TRIES = 0
# True iken failover akisinin her adimi syserr.txt'e "[AUTH-FAILOVER]" ile yazilir.
# Test/teshis icindir; canliya cikarken False yapin.
AUTH_FAILOVER_DEBUG = True

def GetAuthFailoverList(regionID, serverID):
	# (ip, port) cifti listesi -> failover icin SIRALI auth aday listesi dondurur.
	# Yuk dagilimi icin rastgele bir auth'tan baslar, sonra digerlerini doner.
	ports = list(SRV1.get("authlist", []))
	# ip: once secili sunucu; cozulemezse (or. auto-login'de server listesi henuz
	# secili degil) SRV1 host'a geri dus -> auto-login de failover korumasi alir.
	# NOT: Bugun tek sunucu (SRV1) var; coklu sunucuda burada region/server -> SRV
	# eslemesi yapilmali (yoksa baska sunucunun ip'sine SRV1 portlari eslenir).
	try:
		ip = REGION_AUTH_SERVER_DICT[regionID][serverID]["ip"]
	except Exception:
		ip = SRV1.get("host")
	if not ip:
		return []
	if not ports:
		try:
			return [(ip, REGION_AUTH_SERVER_DICT[regionID][serverID]["port"])]
		except Exception:
			return []
	start = app.GetRandom(0, len(ports) - 1)
	ordered = ports[start:] + ports[:start]
	return [(ip, p) for p in ordered]

STATE_NONE = localeInfo.CHANNEL_STATUS_OFFLINE

STATE_DICT = {
	0: localeInfo.CHANNEL_STATUS_OFFLINE,
	1: localeInfo.CHANNEL_STATUS_RECOMMENDED,
	2: localeInfo.CHANNEL_STATUS_BUSY,
	3: localeInfo.CHANNEL_STATUS_FULL,
}

SERVER1_CHANNEL_DICT = {
	0: {"key":10, "name": "CH-1", "ip":SRV1["host"], "tcp_port":SRV1["ch1"], "udp_port":SRV1["ch1"], "state":STATE_NONE,},
	1: {"key":11, "name": "CH-2", "ip":SRV1["host"], "tcp_port":SRV1["ch2"], "udp_port":SRV1["ch2"], "state":STATE_NONE,},
	2: {"key":12, "name": "CH-3", "ip":SRV1["host"], "tcp_port":SRV1["ch3"], "udp_port":SRV1["ch3"], "state":STATE_NONE,},
	3: {"key":13, "name": "CH-4", "ip":SRV1["host"], "tcp_port":SRV1["ch4"], "udp_port":SRV1["ch4"], "state":STATE_NONE,},
	4: {"key":14, "name": "CH-5", "ip":SRV1["host"], "tcp_port":SRV1["ch5"], "udp_port":SRV1["ch5"], "state":STATE_NONE,},
	5: {"key":15, "name": "CH-6", "ip":SRV1["host"], "tcp_port":SRV1["ch6"], "udp_port":SRV1["ch6"], "state":STATE_NONE,},
	6: {"key":16, "name": "CH-7", "ip":SRV1["host"], "tcp_port":SRV1["ch7"], "udp_port":SRV1["ch7"], "state":STATE_NONE,},
	7: {"key":17, "name": "CH-8", "ip":SRV1["host"], "tcp_port":SRV1["ch8"], "udp_port":SRV1["ch8"], "state":STATE_NONE,},
	8: {"key":18, "name": "CH-9", "ip":SRV1["host"], "tcp_port":SRV1["ch9"], "udp_port":SRV1["ch9"], "state":STATE_NONE,},
	9: {"key":19, "name": "CH-10", "ip":SRV1["host"], "tcp_port":SRV1["ch10"], "udp_port":SRV1["ch10"], "state":STATE_NONE,},
	10: {"key":20, "name": "CH-11", "ip":SRV1["host"], "tcp_port":SRV1["ch11"], "udp_port":SRV1["ch11"], "state":STATE_NONE,},
	11: {"key":21, "name": "CH-12", "ip":SRV1["host"], "tcp_port":SRV1["ch12"], "udp_port":SRV1["ch12"], "state":STATE_NONE,},
}

REGION_NAME_DICT = {
	0: SRV1["name"],
}

REGION_AUTH_SERVER_DICT = {
	0: {
		1: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		2: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		3: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		4: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		5: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		6: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		7: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		8: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		9: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		10: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		11: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
		12: {"ip": SRV1["host"], "port": get_item_from_list(SRV1["authlist"]),},
	}
}

REGION_DICT = {
	0: {
		1: {"name": SRV1["name"], "channel": SERVER1_CHANNEL_DICT,},
	},
}

MARKADDR_DICT = {
	10: {"ip": SRV1["host"], "tcp_port": SRV1["ch1"], "mark": "10.tga", "symbol_path": "10",},
}

TESTADDR = {"ip": SRV1["host"], "tcp_port": SRV1["ch1"], "udp_port": SRV1["ch1"],}
