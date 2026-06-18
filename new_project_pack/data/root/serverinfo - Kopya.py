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
	"host":"185.128.115.194",
	"srv1-auth1":30001,
	"srv1-auth2":30003,
	"srv1-auth3":30005,
	"srv1-auth4":30007,
	"ch1":30009,
	"ch2":30017,
	"ch3":30025,
	"ch4":30033,
	"ch5":30041,
	"ch6":30049,

	"authlist": [ 30001,30003,30005,30007, ],
}

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
