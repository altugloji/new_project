#include "stdafx.h"

#ifdef ENABLE_IP_BAN

#include "db.h"
#include "ban_ip.h"

// player.ban_ip tablosunda c_pszIP var mi? Her cagrida DB'ye dogrudan sorar (cache yok).
// c_pszIP, inet_ntoa ciktisidir (kanonik noktali-ondalik, tirnak icermez); yine de guvenlik
// icin EscapeString'den gecirilir. Tablo yok / DB hatasi -> false (fail-open: kimse yanlislikla
// engellenmez).
bool IsIPBanned(const char * c_pszIP)
{
	if (!c_pszIP || !*c_pszIP)
		return false;

	char szIP[32];
	DBManager::instance().EscapeString(szIP, sizeof(szIP), c_pszIP, strlen(c_pszIP));

	char szQuery[128];
	snprintf(szQuery, sizeof(szQuery), "SELECT 1 FROM player.ban_ip WHERE ip = '%s' LIMIT 1", szIP);

	auto pMsg(DBManager::instance().DirectQuery("%s", szQuery));

	if (!pMsg->Get() || pMsg->uiSQLErrno != 0)
		return false;

	return pMsg->Get()->uiNumRows > 0;
}

#endif // ENABLE_IP_BAN
