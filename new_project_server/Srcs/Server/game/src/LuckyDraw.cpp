#include "stdafx.h"

#ifdef ENABLE_LUCKY_DRAW

#include "constants.h"
#include "config.h"
#include "packet.h"
#include "desc.h"
#include "desc_manager.h"
#include "buffer_manager.h"
#include "questmanager.h"
#include "char.h"
#include "char_manager.h"
#include "LuckyDraw.h"
#include "utils.h"
#include "db.h"
#include "cmd.h"
#include <algorithm>
#include "item_manager.h"
#include "item.h"
#include "p2p.h"

void LD_BroadcastNotice(const char* format, ...)
{
	if (!format) { return; }

	char textBuf[CHAT_MAX_LEN + 1];
	va_list args;

	va_start(args, format);
	vsnprintf(textBuf, sizeof(textBuf), format, args);
	va_end(args);

	BroadcastNotice(textBuf);
}

// Bu core'daki TUM online oyunculara client komutu gonder
// (minimap gostergesi gibi durum sinyalleri icin; game.py serverCommandList isler)
void LD_BroadcastCommand(const char* c_pszCmd)
{
	if (!c_pszCmd) { return; }

	const DESC_MANAGER::DESC_SET & c_set_desc = DESC_MANAGER::instance().GetClientSet();
	for (DESC_MANAGER::DESC_SET::const_iterator it = c_set_desc.begin(); it != c_set_desc.end(); ++it)
	{
		LPDESC d = *it;
		if (d && d->GetCharacter())
			d->GetCharacter()->ChatPacket(CHAT_TYPE_COMMAND, "%s", c_pszCmd);
	}
}

EVENTINFO(ld_event_info) {
	uint16_t updateDelay;
	uint32_t elapsedTimeSec;
	uint32_t maxTimeSec;
	ld_event_info() :updateDelay(0), elapsedTimeSec(0), maxTimeSec(0) {}
};
EVENTFUNC(ld_event_timer) {
	ld_event_info* info = dynamic_cast<ld_event_info*>(event->info);
	if (info == NULL) { return 0; }
	info->elapsedTimeSec += info->updateDelay;
	if (info->elapsedTimeSec >= info->maxTimeSec) {
		// 0 dondugumuzde event serbest birakilir; sinifta sarkan pointer kalmasin
		CLuckyDraw::Instance().ClearUpdateTimer();
		CLuckyDraw::Instance().EndLuckyDraw(true);
		return 0;
	}
	return PASSES_PER_SEC(info->updateDelay);
}

CLuckyDraw::CLuckyDraw()
{
	updateTimer = NULL;
	lastFetchTime = 0;
	m_luckyDrawInf = {};
	m_winnerInfo = {};
	m_joinerList = {};
	m_bIsMainHandler = false;
	m_bIsActivated = false;
}
void CLuckyDraw::Destroy()
{
	lastFetchTime = 0;
	m_luckyDrawInf = {};
	m_joinerList = {};
	m_bIsMainHandler = false;
	m_bIsActivated = false;
	if (updateTimer) { event_cancel(&updateTimer); }
}
void CLuckyDraw::Initialize() {
	lastFetchTime = 0;
	m_luckyDrawInf = {};
	m_winnerInfo = {};
	m_joinerList = {};
	m_bIsMainHandler = false;
	m_bIsActivated = false;
	if (updateTimer) { event_cancel(&updateTimer); }

	RequestLuckyDraw();
	RequestLuckyDrawJoiners();
	RequestWinnerInfo();
}
void CLuckyDraw::EndLuckyDraw(bool determineWinners)
{
	// manage-2 ile erken bitiste kurulu timer iptal edilmezse sure dolunca ikinci cekilis yapar (dupe yolu);
	// timer'dan gelen cagrida ld_event_timer ClearUpdateTimer() yaptigi icin burasi NULL gorur, guvenli
	if (updateTimer) { event_cancel(&updateTimer); }

	std::unique_ptr<SQLMsg> pMsg_Start(DBManager::Instance().DirectQuery("UPDATE player.luckydraw_config SET is_activated = 0;"));
	RequestLuckyDraw();

	if (determineWinners) {
		// v2: once TUM siralar kosulsuz temizlenir (0 katilimcili bitiste onceki
		// etkinligin kazananlari gorunmeye/claim edilmeye devam etmesin), sonra
		// bulunan kadar kazanan yazilir (v1 hepsi-yoksa-hicbiri idi)
		for (uint8_t w = 0; w < LD_MAX_WINNERS; ++w) {
			std::unique_ptr<SQLMsg> pMsg_Clear(DBManager::Instance().DirectQuery(
				"UPDATE player.luckydraw_winners SET winner_pid = 0, winner_name = '', is_taken = 0 WHERE winner_place = %u;", (uint32_t)(w + 1)));
		}

		// eski (v1) winners tablosunda 5 satir olmayabilir: cekilisi satir sayisina klample
		uint8_t drawLimit = 0;
		{
			std::unique_ptr<SQLMsg> pMsg_Rows(DBManager::Instance().DirectQuery("SELECT COUNT(*) FROM player.luckydraw_winners;"));
			if (pMsg_Rows->Get()->uiNumRows != 0) {
				MYSQL_ROW mRowC = mysql_fetch_row(pMsg_Rows->Get()->pSQLResult);
				uint32_t rowCount = 0;
				str_to_number(rowCount, mRowC[0]);
				drawLimit = (rowCount < LD_MAX_WINNERS) ? (uint8_t)rowCount : (uint8_t)LD_MAX_WINNERS;
			}
			if (drawLimit < LD_MAX_WINNERS)
				sys_err("LuckyDraw: luckydraw_winners %u satir (beklenen %d) - sql/luckydraw_v2_upgrade.sql uygulanmali", (unsigned)drawLimit, LD_MAX_WINNERS);
		}

		uint32_t winnerPID[LD_MAX_WINNERS] = {};
		char winnerName[LD_MAX_WINNERS][CHARACTER_NAME_MAX_LEN + 1] = {};
		uint8_t foundCount = 0;

		char szExclude[256] = { 0 };
		for (uint8_t w = 0; w < drawLimit; ++w) {
			// NOT IN (0...): PID 0 olamaz, bos-liste sozdizimi sorununu onler
			std::unique_ptr<SQLMsg> pMsgW(DBManager::Instance().DirectQuery(
				"SELECT player_id, player_name FROM player.luckydraw_joiners WHERE player_id NOT IN (0%s) ORDER BY RAND() LIMIT 1;", szExclude));
			if (pMsgW->Get()->uiNumRows == 0)
				break;
			MYSQL_ROW mRowW = mysql_fetch_row(pMsgW->Get()->pSQLResult);
			str_to_number(winnerPID[w], mRowW[0]);
			snprintf(winnerName[w], sizeof(winnerName[w]), "%s", mRowW[1]);

			size_t exLen = strlen(szExclude);
			snprintf(szExclude + exLen, sizeof(szExclude) - exLen, ",%u", winnerPID[w]);
			foundCount++;
		}

		if (foundCount > 0) {
			char szNotice[CHAT_MAX_LEN + 1];
			int noticeLen = snprintf(szNotice, sizeof(szNotice), "<LuckyDraw> Etkinlik sona erdi. Kazananlar:");
			for (uint8_t w = 0; w < foundCount; ++w) {
				// is_taken = 0: yeni etkinligin kazananlari odulunu alabilsin
				std::unique_ptr<SQLMsg> pMsg_Winner(DBManager::Instance().DirectQuery(
					"UPDATE player.luckydraw_winners SET winner_pid = %u, winner_name = '%s', is_taken = 0 WHERE winner_place = %u;",
					winnerPID[w], winnerName[w], (uint32_t)(w + 1)));
				if (noticeLen > 0 && noticeLen < (int)sizeof(szNotice))
					noticeLen += snprintf(szNotice + noticeLen, sizeof(szNotice) - noticeLen, " %u. %s", (uint32_t)(w + 1), winnerName[w]);
			}
			LD_BroadcastNotice("%s tebrikler.", szNotice);
		}

		RequestWinnerInfo();
		// kosulsuz duyuru: bitis hangi core'dan tetiklenirse tetiklensin digerleri senkron kalsin
		// (P2P isleyicisi EndLuckyDraw cagirmaz -> yanki dongusu olusamaz)
		SendP2PPacket(5);
	}
	else {
		SendP2PPacket(3);
	}
}
void CLuckyDraw::RequestLuckyDraw(bool bStart)
{
	if (bStart)
		std::unique_ptr<SQLMsg> pMsg_Start(DBManager::Instance().DirectQuery("UPDATE player.luckydraw_config SET is_activated = 1;"));

	bool bWasActivated = m_bIsActivated;

	std::unique_ptr<SQLMsg> pMsg(DBManager::Instance().DirectQuery("SELECT * FROM player.luckydraw_config;"));
	if (pMsg->Get()->uiNumRows == 0) { return; }
	MYSQL_ROW mRow = mysql_fetch_row(pMsg->Get()->pSQLResult);
	str_to_number(m_luckyDrawInf.maxJoinCount, mRow[1]);
	str_to_number(m_luckyDrawInf.maxTicketCount, mRow[2]);
	str_to_number(m_luckyDrawInf.neededItemVnum[0], mRow[3]);
	str_to_number(m_luckyDrawInf.neededItemCount[0], mRow[4]);
	str_to_number(m_luckyDrawInf.neededYang, mRow[5]);

	uint8_t isActivated = 0;
	str_to_number(isActivated, mRow[6]);
	m_bIsActivated = (isActivated == 1);

	// v2: ek katilim itemleri kolon [7..14]; eski semada yoksa sifir kalir (upgrade SQL gerekir)
	for (uint8_t r = 1; r < LD_MAX_REQ_ITEMS; ++r) {
		m_luckyDrawInf.neededItemVnum[r] = 0;
		m_luckyDrawInf.neededItemCount[r] = 0;
	}
	unsigned int numFields = mysql_num_fields(pMsg->Get()->pSQLResult);
	if (numFields >= 7 + (LD_MAX_REQ_ITEMS - 1) * 2) {
		for (uint8_t r = 1; r < LD_MAX_REQ_ITEMS; ++r) {
			str_to_number(m_luckyDrawInf.neededItemVnum[r], mRow[7 + (r - 1) * 2]);
			str_to_number(m_luckyDrawInf.neededItemCount[r], mRow[8 + (r - 1) * 2]);
		}
	}
	else {
		sys_err("LuckyDraw: luckydraw_config eski semada (%u kolon) - sql/luckydraw_v2_upgrade.sql uygulanmali", numFields);
	}

	lastFetchTime = get_global_time();

	// etkinlik kapandiysa bu core'da kurulu timer varsa sondur
	// (baska core'dan gelen bitis duyurusu -arg 3/5- buradan gecer; cifte cekilisi engeller)
	if (!m_bIsActivated && updateTimer) { event_cancel(&updateTimer); }

	// durum degistiyse bu core'daki online oyunculara minimap gostergesi sinyali gonder
	// (tum start/end yollari -yerel komut, timer, P2P arg 1/3/5- buradan gecer)
	if (bWasActivated != m_bIsActivated)
		LD_BroadcastCommand(m_bIsActivated ? "lucky_draw_state 1" : "lucky_draw_state 0");
}
void CLuckyDraw::RequestLuckyDrawJoiners(bool bBroadcast)
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::Instance().DirectQuery("SELECT COUNT(*) as count FROM player.luckydraw_joiners;"));
	if (pMsg->Get()->uiNumRows == 0) { return; }

	MYSQL_ROW mRow = mysql_fetch_row(pMsg->Get()->pSQLResult);
	str_to_number(m_luckyDrawInf.joinCount, mRow[0]);

	// pencere icin en cok bileti olan katilimcilar (v2)
	m_joinerList = {};
	std::unique_ptr<SQLMsg> pMsgList(DBManager::Instance().DirectQuery(
		"SELECT player_name, COUNT(*) AS c FROM player.luckydraw_joiners GROUP BY player_id, player_name ORDER BY c DESC, player_name ASC LIMIT %d;", LD_MAX_JOINER_LIST));
	if (pMsgList->Get()->uiNumRows != 0) {
		uint8_t iOrder = 0;
		while (iOrder < LD_MAX_JOINER_LIST && NULL != (mRow = mysql_fetch_row(pMsgList->Get()->pSQLResult))) {
			snprintf(m_joinerList.szName[iOrder], sizeof(m_joinerList.szName[iOrder]), "%s", mRow[0]);
			str_to_number(m_joinerList.ticketCount[iOrder], mRow[1]);
			iOrder++;
		}
	}

	// bBroadcast: yalnizca YEREL bir degisiklikten sonra (join / GM yenileme) diger
	// core'lara duyur; P2P arg 2 isleyicisi false ile cagirir -> yayin firtinasi olmaz
	if (bBroadcast)
		SendP2PPacket(2);
}
void CLuckyDraw::RequestWinnerInfo()
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::Instance().DirectQuery("SELECT * FROM player.luckydraw_winners ORDER BY winner_place ASC LIMIT %d;", LD_MAX_WINNERS));
	if (pMsg->Get()->uiNumRows == 0) { return; }

	MYSQL_ROW mRow;
	uint8_t iOrder = 0;
	while (NULL != (mRow = mysql_fetch_row(pMsg->Get()->pSQLResult))) {
		if (iOrder >= LD_MAX_WINNERS)
			break;
		BYTE cur = 0;
		str_to_number(m_winnerInfo.iPlace[iOrder], mRow[cur++]);
		str_to_number(m_winnerInfo.playerID[iOrder], mRow[cur++]);
		snprintf(m_winnerInfo.szName[iOrder], sizeof(m_winnerInfo.szName[iOrder]), "%s", mRow[cur++]);
		str_to_number(m_winnerInfo.iReward1[iOrder], mRow[cur++]);
		str_to_number(m_winnerInfo.iReward2[iOrder], mRow[cur++]);
		str_to_number(m_winnerInfo.iReward3[iOrder], mRow[cur++]);
		str_to_number(m_winnerInfo.iReward4[iOrder], mRow[cur++]);
		str_to_number(m_winnerInfo.iReward5[iOrder], mRow[cur++]);

		// kazananin bilet sayisi: joiners bir sonraki baslatmaya kadar durur,
		// bu yuzden son cekilisin kazananlari icin sayim her zaman dogrudur
		m_winnerInfo.ticketCount[iOrder] = m_winnerInfo.playerID[iOrder] ? GetJoinCountByPID(m_winnerInfo.playerID[iOrder]) : 0;

		iOrder++;
	}
}
void CLuckyDraw::ClientPacket(LPCHARACTER ch)
{
	if (!ch) { return; }
	if (!ch->GetDesc()) { return; }

	// bilgi-istegi bekleme suresi kullanici istegiyle kaldirildi (2026-07-20);
	// taban koruma ENABLE_ANTI_CMD_FLOOD'da (500ms'de 5 komut siniri)

	TPacketGCLuckyDrawInfo p = {};

	p.bHeader = HEADER_GC_LUCKYDRAW_INFO;
	p.myJoinCount = GetJoinCountByPID(ch->GetPlayerID());
	p.joinCount = m_luckyDrawInf.joinCount;
	p.maxJoinCount = m_luckyDrawInf.maxJoinCount;
	p.maxTicketCount = m_luckyDrawInf.maxTicketCount;
	p.neededYang = m_luckyDrawInf.neededYang;

	for (uint8_t r = 0; r < LD_MAX_REQ_ITEMS; r++) {
		p.neededItemVnum[r] = m_luckyDrawInf.neededItemVnum[r];
		p.neededItemCount[r] = m_luckyDrawInf.neededItemCount[r];
	}

	p.endTime = m_bIsActivated ? (int32_t)(m_luckyDrawInf.endTime - get_global_time()) : 0;
	if (p.endTime < 0)
		p.endTime = 0;

	for (uint8_t i = 0; i < LD_MAX_WINNERS; i++) {
		snprintf(p.winnerNames[i], sizeof(p.winnerNames[i]), "%s", m_winnerInfo.szName[i]);
		p.winnerTickets[i] = m_winnerInfo.ticketCount[i];
		p.iReward1[i] = m_winnerInfo.iReward1[i];
		p.iReward2[i] = m_winnerInfo.iReward2[i];
		p.iReward3[i] = m_winnerInfo.iReward3[i];
		p.iReward4[i] = m_winnerInfo.iReward4[i];
		p.iReward5[i] = m_winnerInfo.iReward5[i];
	}

	for (uint8_t j = 0; j < LD_MAX_JOINER_LIST; j++) {
		snprintf(p.joinerNames[j], sizeof(p.joinerNames[j]), "%s", m_joinerList.szName[j]);
		p.joinerTickets[j] = m_joinerList.ticketCount[j];
	}

	ch->GetDesc()->Packet(&p, sizeof(TPacketGCLuckyDrawInfo));
}
void CLuckyDraw::SendP2PPacket(DWORD arg1, DWORD arg2, DWORD arg3)
{
	TPacketGGLuckyDraw p2pPacket = {};
	p2pPacket.bHeader = HEADER_GG_LUCKY_DRAW;
	p2pPacket.bArg = arg1;
	if (arg2)
		p2pPacket.bArg_2 = arg2;
	if (arg3)
		p2pPacket.bArg_3 = arg3;

	P2P_MANAGER::instance().Send(&p2pPacket, sizeof(TPacketGGLuckyDraw));
}
void CLuckyDraw::StartLuckyDraw(DWORD maxTime, bool fromP2P)
{
	std::unique_ptr<SQLMsg> pMsg_Start(DBManager::Instance().DirectQuery("DELETE FROM player.luckydraw_joiners;"));

	// yeni cekilis: onceki etkinligin kazanan verisi temizlenir (odul kolonlari korunur);
	// her core'da calisir, idempotent (joiners DELETE ile ayni desen)
	for (uint8_t w = 0; w < LD_MAX_WINNERS; ++w) {
		std::unique_ptr<SQLMsg> pMsg_Clear(DBManager::Instance().DirectQuery(
			"UPDATE player.luckydraw_winners SET winner_pid = 0, winner_name = '', is_taken = 0 WHERE winner_place = %u;", (uint32_t)(w + 1)));
	}

	RequestLuckyDraw(true);
	if (!IsLuckyDrawActivated())
		return;

	RequestLuckyDrawJoiners();
	RequestWinnerInfo();

	m_luckyDrawInf.endTime = get_global_time() + maxTime;

	// capraz-core cifte baslatma korumasi: onceki etkinlikten kalan timer hangi
	// dalda olursak olalim iptal edilir; P2P ile baslatilan core ana isleyici degildir
	if (updateTimer) { event_cancel(&updateTimer); }

	if (!fromP2P) {
		m_bIsMainHandler = true;

		ld_event_info* info;
		info = AllocEventInfo<ld_event_info>();
		info->updateDelay = LD_TIMER_TICK_DELAY;
		info->maxTimeSec = maxTime;
		info->elapsedTimeSec = 0;	// orijinalde tick-onyuklemesi etkinligi 1 sn erken bitiriyordu
		updateTimer = event_create(ld_event_timer, info, PASSES_PER_SEC(info->updateDelay));

		SendP2PPacket(1, maxTime);

		int iHour = maxTime / 3600;
		int iMin = (maxTime % 3600) / 60;

		LD_BroadcastNotice("<LuckyDraw> Etkinlik %d saat %d dakika sure ile basladi.", iHour, iMin);
	}
	else {
		// baska core baslatti: bu core artik ana isleyici degil
		m_bIsMainHandler = false;
	}
}
uint32_t CLuckyDraw::GetJoinCountByPID(DWORD playerID)
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::Instance().DirectQuery("SELECT COUNT(*) as count FROM player.luckydraw_joiners WHERE player_id = %u;", playerID));
	if (pMsg->Get()->uiNumRows == 0) { return 0; }

	uint32_t rtVal = 0;
	MYSQL_ROW mRow = mysql_fetch_row(pMsg->Get()->pSQLResult);
	str_to_number(rtVal, mRow[0]);
	return rtVal;
}
bool CLuckyDraw::IsLuckyDrawActivated()
{
	return m_bIsActivated;
}
bool CLuckyDraw::JoinLuckyDraw(LPCHARACTER pCh)
{
	if (!pCh || !pCh->GetDesc())
		return false;
	if (!m_bIsActivated)
		return false;

	if (!pCh->CanWarp()) {
		pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Once butun pencereleri kapatin ve lutfen biraz bekleyin.");
		return false;
	}

	// katilim bekleme suresi kullanici istegiyle kaldirildi (2026-07-20);
	// taban koruma ENABLE_ANTI_CMD_FLOOD'da (500ms'de 5 komut siniri)

	if (GetJoinCountByPID(pCh->GetPlayerID()) >= m_luckyDrawInf.maxTicketCount) {
		pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Maksimum katilim hakkina ulastiniz.");
		return false;
	}

	// coklu core: global sayaci DB'den canli oku; baska core'daki katilimlar yerel onbellekte gorunmez
	RequestLuckyDrawJoiners();
	if (m_luckyDrawInf.joinCount >= m_luckyDrawInf.maxJoinCount) {
		pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Sistem maksimum katilim kapasitesini doldurdu.");
		return false;
	}

	bool removeGold = false;

	// v2: tum item sartlarini ONCE kontrol et (ayni vnum birden fazla slottaysa toplamini tek seferde iste)
	for (uint8_t r = 0; r < LD_MAX_REQ_ITEMS; ++r) {
		uint32_t vnum = m_luckyDrawInf.neededItemVnum[r];
		uint32_t cnt = m_luckyDrawInf.neededItemCount[r];
		if (!vnum || !cnt)
			continue;

		bool seenBefore = false;
		for (uint8_t s = 0; s < r; ++s) {
			if (m_luckyDrawInf.neededItemVnum[s] == vnum && m_luckyDrawInf.neededItemCount[s]) { seenBefore = true; break; }
		}
		if (seenBefore)
			continue;

		uint32_t totalNeeded = cnt;
		for (uint8_t s = r + 1; s < LD_MAX_REQ_ITEMS; ++s) {
			if (m_luckyDrawInf.neededItemVnum[s] == vnum)
				totalNeeded += m_luckyDrawInf.neededItemCount[s];
		}

		if (pCh->CountSpecifyItem(vnum) < (int)totalNeeded) {
			pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Gerekli esyaya sahip degilsiniz.");
			return false;
		}
	}
	if (m_luckyDrawInf.neededYang) {
		if ((uint64_t)pCh->GetGold() < m_luckyDrawInf.neededYang) {
			pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Yeterli yanga sahip degilsiniz.");
			return false;
		}
		removeGold = true;
	}

	std::unique_ptr<SQLMsg> sqlQuery(DBManager::instance().DirectQuery("INSERT INTO player.luckydraw_joiners (account_id, player_id, player_name, join_time) VALUES(%u, %u, '%s', NOW());",
		pCh->GetDesc()->GetAccountTable().id, pCh->GetPlayerID(), pCh->GetName()));
	if (sqlQuery->Get()->uiInsertID != 0) {
		for (uint8_t r = 0; r < LD_MAX_REQ_ITEMS; ++r) {
			if (m_luckyDrawInf.neededItemVnum[r] && m_luckyDrawInf.neededItemCount[r])
				pCh->RemoveSpecifyItem(m_luckyDrawInf.neededItemVnum[r], m_luckyDrawInf.neededItemCount[r]);
		}
		if (removeGold)
			// katilim kontrolu gold >= neededYang sartini gecti; gold INT oldugu icin neededYang burada INT_MAX'i asamaz
			pCh->PointChange(POINT_GOLD, -static_cast<int>(m_luckyDrawInf.neededYang));

		pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Katilim basarili.");
		RequestLuckyDrawJoiners(true);	// yerel katilim: diger core'larin listesi de guncellensin

		return true;
	}

	return false;
}
bool CLuckyDraw::RequestReward(LPCHARACTER pCh)
{
	if (!pCh || !pCh->GetDesc())
		return false;

	if (!pCh->CanRequestLDReward()) {
		pCh->ChatPacket(CHAT_TYPE_INFO, "Lutfen biraz bekleyin.");
		return false;
	}

	pCh->SetLastLuckyDrawRequestRewardTime();

	std::unique_ptr<SQLMsg> pMsg(DBManager::Instance().DirectQuery("SELECT winner_pid, is_taken, reward1_vnum, reward2_vnum, reward3_vnum, reward4_vnum, reward5_vnum FROM player.luckydraw_winners WHERE winner_pid = %u;", pCh->GetPlayerID()));
	if (pMsg->Get()->uiNumRows == 0) { return false; }

	DWORD chPID = 0, isTaken = 0;
	DWORD rewardItems[LD_MAX_REWARDS];

	MYSQL_ROW mRow = mysql_fetch_row(pMsg->Get()->pSQLResult);
	str_to_number(chPID, mRow[0]);
	str_to_number(isTaken, mRow[1]);
	for (uint8_t w = 0; w < LD_MAX_REWARDS; w++) {
		str_to_number(rewardItems[w], mRow[2 + w]);
	}

	if (chPID) {
		if (isTaken == 1) {
			pCh->ChatPacket(CHAT_TYPE_INFO, "<LuckyDraw> Odulu zaten aldiniz.");
		}
		else {
			std::unique_ptr<SQLMsg> pMsg_Start(DBManager::Instance().DirectQuery("UPDATE player.luckydraw_winners SET is_taken = 1 WHERE winner_pid = %u;", chPID));
			for (uint8_t i = 0; i < LD_MAX_REWARDS; i++) {
				if (rewardItems[i]) {
					pCh->AutoGiveItem(rewardItems[i]);
				}
			}

			return true;
		}
	}

	return false;
}

#endif // ENABLE_LUCKY_DRAW
