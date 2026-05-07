#### @martysama0134 start scripts ####
from platform import system as p_system
v_system = p_system()

from subprocess import check_output as sp_co, call as sp_call, CalledProcessError as sp_CalledProcessError
def fShell(szCmd, bRet=False):
	try:
		if bRet:
			return sp_co(szCmd, shell=True)[:-1]	# remove final \n
		else:
			return sp_call(szCmd, shell=True)
	except sp_CalledProcessError:
		return -1

DISABLE_TEST_MODE_IN_CH1 = False

if v_system=="FreeBSD":
	v_adminPageLocalIP=fShell("ifconfig em0 | grep -Eo 'inet ([0-9]{1,3}\.){3}([0-9]{1,3})' | awk '{print $2}'", True).decode()
elif v_system=="Linux":
	v_adminPageLocalIP=fShell("ifconfig eth0 | grep -Eo 'inet addr:([0-9]{1,3}\.){3}([0-9]{1,3})' | awk -F':' '{print $2}'", True).decode()
elif v_system=="Windows":
	v_adminPageLocalIP="127.0.0.1"

v_adminPagePassword='58948HG83H4G8H84G'				#adminpage_password
v_serverHostname='127.0.0.1'						#host for sql connections
v_serverUserPass='mt2 mt2'							#user&pwd for sql connections
v_serverData=f"{v_serverHostname} {v_serverUserPass}"	#host, user and pwd for db sql connections

# v_bindHostname='10.0.2.15'
# v_proxyHostname='127.0.0.1'
v_dbHostname='127.0.0.1'#default hostname for db
v_dbPort=30000		#default port for db (the others will be automatically calculated)
v_mysqlport=3306	#default mysql port (3306 or 0)
v_logFolder='logs'		#name of the all_log path
v_chanFolder='chan/'		#name of the channel path
v_chanPath='../'		#workaround that should be equivalent to $v_charS paths per ../

#############################
## to specify custom ports:
# 1) be sure the key matches "{ServerName}-{FolderName}-{ProcessName}"
# 2) and check if they are still commented
# 3) if you're under NAT, be sure to portforward the new ports
M2PORTS = {
	# "srv1-db":(15000), #db port
	# "srv1-auth1":(11000,12000), #port,p2p_port
	# "srv1-auth2":(11001,12001), #port,p2p_port
	# "srv1-ch1-core1":(13101,14101),
	# "srv1-ch1-core2":(13102,14102),
	# "srv1-ch1-core3":(13103,14103),
	# "srv1-ch1-core4":(13104,14104),
	# "srv1-ch2-core1":(13201,14201),
	# "srv1-ch2-core2":(13202,14202),
	# "srv1-ch2-core3":(13203,14203),
	# "srv1-ch2-core4":(13204,14204),
	# "srv1-ch3-core1":(13301,14301),
	# "srv1-ch3-core2":(13302,14302),
	# "srv1-ch3-core3":(13303,14303),
	# "srv1-ch3-core4":(13304,14304),
	# "srv1-ch4-core1":(13401,14401),
	# "srv1-ch4-core2":(13402,14402),
	# "srv1-ch4-core3":(13403,14403),
	# "srv1-ch4-core4":(13404,14404),
	# "srv1-ch99-core99":(13099,14099),
}

M2SD = {
	"account":		"account",
	"common":		"common",
	"hotbackup":	"hotbackup",
	"log":			"log",
	"player":		"player",
}

class M2TYPE:
	SERVER, DB, AUTH, CHANFOLDER, CHANNEL, CORE = range(6)
	NOCHAN = 0

class PORT:
	RANDOMI = v_dbPort	# a random port will start from such value
	PORT, P2P_PORT, DB_PORT, BIND_PORT = range(4)
	lPORT = ("PORT", "P2P_PORT", "DB_PORT", "BIND_PORT")

M2CONFIG = {
	"db": {
		"general": (
			('SQL_ACCOUNT = "{} {} {} {}"', (v_serverHostname, M2SD["account"], v_serverUserPass, v_mysqlport)),
			('SQL_COMMON = "{} {} {} {}"', (v_serverHostname, M2SD["common"], v_serverUserPass, v_mysqlport)),
			('SQL_PLAYER = "{} {} {} {}"', (v_serverHostname, M2SD["player"], v_serverUserPass, v_mysqlport)),
			('SQL_HOTBACKUP = "{} {} {} {}"', (v_serverHostname, M2SD["hotbackup"], v_serverUserPass, v_mysqlport)),
			('SQL_LOG = "{} {} {} {}"', (v_serverHostname, M2SD["log"], v_serverUserPass, v_mysqlport)),
			#
			('TABLE_POSTFIX = "{}"', ""),
			#
			# ("BIND_PORT = {}", v_dbPort),
			# ("DB_SLEEP_MSEC = 10", ()),
			("CLIENT_HEART_FPS = {}", 25),
			# ("HASH_PLAYER_LIFE_SEC = {}", 600),
			("PLAYER_ID_START = {}", 100),
			("PLAYER_DELETE_LEVEL_LIMIT = {}", 70),
			("PLAYER_DELETE_LEVEL_LIMIT_LOWER = {}", 15),
			("ITEM_ID_RANGE = {} {} ", (100000000, 200000000)),
			# ("BACKUP_LIMIT_SEC = {}", 3600),
			("DISABLE_HOTBACKUP = {:d}", True),
			("LOCALE = {}", "latin1"),
		),
		"extra": (
			("PROTO_FROM_DB = {:d}", False),
			("MIRROR2DB = {:d}", False),
		)
	},
	"core": {
		M2TYPE.AUTH: (
			("AUTH_SERVER: {}", "master"),
			("PLAYER_SQL: {} {} {}", (v_serverData, M2SD["account"], v_mysqlport)),
		),
		M2TYPE.CORE: (
			("PLAYER_SQL: {} {} {}", (v_serverData, M2SD["player"], v_mysqlport)),
		),
		"general": (
			# ("TABLE_POSTFIX: {}", ""),
			# ("ITEM_ID_RANGE: {} {}", (5000001, 10000000)),
			("VIEW_RANGE: {}", 10000),
			("PASSES_PER_SEC: {}", 25),
			("SAVE_EVENT_SECOND_CYCLE: {}", 180),
			("PING_EVENT_SECOND_CYCLE: {}", 180),
			#
			# ("BIND_IP: {}", v_bindHostname),#VPS NAT
			# ("PROXY_IP: {}", v_proxyHostname),#VPS NAT
			("DB_ADDR: {}", v_dbHostname),
			("COMMON_SQL: {} {} {}", (v_serverData, M2SD["common"], v_mysqlport)),
			("LOG_SQL: {} {} {}", (v_serverData, M2SD["log"], v_mysqlport)),
			("TEST_SERVER: {:d}", True),#TEST ONLY
			# ("PK_SERVER: {:d}", True),
			("ADMINPAGE_IP1: {}", v_adminPageLocalIP),
			("ADMINPAGE_PASSWORD: {}", v_adminPagePassword),
			("MAX_LEVEL: {}", 99),
		),
		"extra": (
			# ("CHECK_VERSION_SERVER: {:d}", True),
			# ("CHECK_VERSION_VALUE: {}", 1215955205),
			("CHANGE_ATTR_TIME_LIMIT: {:d}", False),
			("EMOTION_MASK_REQUIRE: {:d}", False),
			("PRISM_ITEM_REQUIRE: {:d}", False),
			("SHOP_PRICE_3X_TAX: {:d}", False),
			("GLOBAL_SHOUT: {:d}", True),
			("ITEM_COUNT_LIMIT: {}", 250),
			("STATUS_POINT_GET_LEVEL_LIMIT: {}", 99),
			("STATUS_POINT_SET_MAX_VALUE: {}", 90),
			("SHOUT_LIMIT_LEVEL: {}", 15),
			("DB_LOG_LEVEL: {}", 1),
			("EMPIRE_LANGUAGE_CHECK: {:d}", False),
			# ("ITEM_DESTROY_TIME_AUTOGIVE: {}", 30),
			# ("ITEM_DESTROY_TIME_DROPITEM: {}", 30),
			# ("ITEM_DESTROY_TIME_DROPGOLD: {}", 30),
		),
	},
}

COMMONCHAN=(
	{
		"name": "core1",
		"type": M2TYPE.CORE,
		"config": M2CONFIG["core"],
		"maps": "1 21 41 3 23 43 4 24 44 5 25 45 108 109 112 301 302 303 304",
	},
	{
		"name": "core2",
		"type": M2TYPE.CORE,
		"config": M2CONFIG["core"],
		"maps": "61 62 63 64 65 66 67 68 69 70 71 72 73 104 193 206 208 207 216 217 351",
	},
)

CHAN99=(
	{
		"name": "core99",
		"type": M2TYPE.CORE,
		"config": M2CONFIG["core"],
		"maps": "81 103 105 110 111 113 114 118 119 120 121 122 123 124 125 126 127 128 181 182 183 200",
	},
)

M2S=(
	{
		"name": "srv1",
		"type": M2TYPE.SERVER,
		"isextra": True,
		"sub": (
			{
				"name": "db",
				"type": M2TYPE.DB,
				"config": M2CONFIG["db"],
			},
			{
				"name": "auth1",
				"type": M2TYPE.AUTH,
				"config": M2CONFIG["core"],
			},
			# {
			# 	"name": "auth2",
			# 	"type": M2TYPE.AUTH,
			# 	"config": M2CONFIG["core"],
			# },
			{
				"name": "chan",
				"type": M2TYPE.CHANFOLDER,
				"sub": (
					{
						"name": "ch1",
						"type": M2TYPE.CHANNEL,
						"chan": 1,
						"sub": COMMONCHAN,
					},
					# {
						# "name": "ch2",
						# "type": M2TYPE.CHANNEL,
						# "chan": 2,
						# "sub": COMMONCHAN,
					# },
					# {
					# 	"name": "ch3",
					# 	"type": M2TYPE.CHANNEL,
					# 	"chan": 3,
					# 	"sub": COMMONCHAN,
					# },
					# {
					# 	"name": "ch4",
					# 	"type": M2TYPE.CHANNEL,
					# 	"chan": 4,
					# 	"sub": COMMONCHAN,
					# },
					{
						"name": "ch99",
						"type": M2TYPE.CHANNEL,
						"chan": 99,
						"sub": CHAN99,
					},
				)
			}
		)
	},
)

CustIpfwList="""#!/bin/sh
IPF="ipfw -q add"
ipfw -q -f flush

#loopback
$IPF 10 allow all from any to any via lo0
$IPF 20 deny all from any to 127.0.0.0/8
$IPF 30 deny all from 127.0.0.0/8 to any
$IPF 40 deny tcp from any to any frag

# stateful
$IPF 50 check-state
$IPF 60 allow tcp from any to any established
$IPF 70 allow all from any to any out keep-state
$IPF 80 allow icmp from any to any

# open port ftp (20, 21), ssh (22), mail (25)
# http (80), https (443), dns (53), mysql (3306)
default_udp_allowed_ports='53'
default_tcp_allowed_ports='22 53 3306'
default_tcp_blocked_ports=''

# here auth PORTs for "NORM"/"..." thing
metin2_udp_allowed_ports='{udp_allowed_ports}'
# here PORTs
metin2_tcp_allowed_ports='{tcp_allowed_ports}'
# here DB_PORTs and P2P_PORTs
metin2_tcp_blocked_ports='{tcp_blocked_ports}'

# merge lists
udp_allowed_ports="$default_udp_allowed_ports $metin2_udp_allowed_ports"
tcp_allowed_ports="$default_tcp_allowed_ports $metin2_tcp_allowed_ports"
tcp_blocked_ports="$default_tcp_blocked_ports $metin2_tcp_blocked_ports"

# white ip list
white_sites=''

# block tcp/udp ports
for val in $tcp_blocked_ports; do
	$IPF 2220 allow all from 127.0.0.0/8 to any $val
	for whitez in $white_sites; do
		$IPF 2210 allow tcp from $whitez to any $val in
		$IPF 2210 allow tcp from 127.0.0.0/8 to $whitez $val out
	done
	$IPF 2230 deny all from any to me $val
done
# unblock tcp ports
for val in $tcp_allowed_ports; do
	$IPF 2200 allow tcp from any to any $val in limit src-addr 20
	$IPF 2210 allow tcp from any to any $val out
done
# unblock udp ports
for val in $udp_allowed_ports; do
	$IPF 2200 allow udp from any to any $val in limit src-addr 20
	$IPF 2210 allow udp from any to any $val out
done
"""

CustServerInfo="""
import app
import localeInfo
from constInfo import TextColor
app.ServerName = None

ENABLE_RANDOM_AUTH_NO_LIB = True
if ENABLE_RANDOM_AUTH_NO_LIB:
	from time import time as time_time
	def get_random_number(upper_limit):
		_timestamp = time_time()
		_timestamp = int(_timestamp*1000000)
		return _timestamp % upper_limit

	def get_item_from_list(_list):
		choice = get_random_number(len(_list))
		assert choice < len(_list), "Index should be less than length of list"
		return _list[choice]
else:
	from random import choice as random_choice
	def get_item_from_list(_list):
		return random_choice(_list)

SRV1 = {{
	"name":TextColor("ServerName", "ffd500"), #GOLD
	"host":"{hostname}",
{portlist}
	"authlist": [ {authlist} ],
}}

STATE_NONE = TextColor(localeInfo.CHANNEL_STATUS_OFFLINE, "FF0000") #RED

STATE_DICT = {{
	0: TextColor(localeInfo.CHANNEL_STATUS_OFFLINE, "FF0000"), #RED
	1: TextColor(localeInfo.CHANNEL_STATUS_RECOMMENDED, "00ff00"), #GREEN
	2: TextColor(localeInfo.CHANNEL_STATUS_BUSY, "ffff00"), #YELLOW
	3: TextColor(localeInfo.CHANNEL_STATUS_FULL, "ff8a08") #ORANGE
}}

SERVER1_CHANNEL_DICT = {{
{channel_dict}
}}

REGION_NAME_DICT = {{
	0: SRV1["name"],
}}

REGION_AUTH_SERVER_DICT = {{
	0: {{
{auth_dict}
	}}
}}

REGION_DICT = {{
	0: {{
		1: {{"name": SRV1["name"], "channel": SERVER1_CHANNEL_DICT,}},
	}},
}}

MARKADDR_DICT = {{
	10: {{"ip": SRV1["host"], "tcp_port": SRV1["ch1"], "mark": "10.tga", "symbol_path": "10",}},
}}

TESTADDR = {{"ip": SRV1["host"], "tcp_port": SRV1["ch1"], "udp_port": SRV1["ch1"],}}
"""
