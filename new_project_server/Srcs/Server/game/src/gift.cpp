// gift.cpp - Hediye Gonderme Sistemi (ENABLE_GIFT_SEND_SYSTEM)
#include "stdafx.h"

#ifdef ENABLE_GIFT_SEND_SYSTEM

#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "desc_manager.h"
#include "db.h"
#include "log.h"
#include "p2p.h"
#include "packet.h"
#include "gift.h"

// ---------------------------------------------------------------------
// Yardimcilar
// ---------------------------------------------------------------------

// SQL string escape: tek tirnak ve ters bolu kacisi + kontrol karakteri temizligi.
// Kullanici mesaji DirectQuery'ye HER ZAMAN bu fonksiyondan gecirilerek yazilir.
static std::string EscapeSQL(const char* c_szSrc)
{
	std::string out;
	if (!c_szSrc)
		return out;

	for (const char* p = c_szSrc; *p; ++p)
	{
		const unsigned char c = (unsigned char)*p;
		if (c < 0x20)			// kontrol karakterlerini at (newline/format vb.)
			continue;
		if (c == '\'' || c == '\\')
			out.push_back('\\');
		out.push_back((char)c);
	}
	return out;
}

// Client'tan gelen mesaji goruntulenmek uzere temizler (kontrol karakterlerini
// bosluga cevirir, null-terminasyonu ve uzunlugu garanti eder).
static void SanitizeMessage(const char* c_szSrc, char* szDst, size_t dstSize)
{
	if (!szDst || dstSize == 0)
		return;

	size_t j = 0;
	if (c_szSrc)
	{
		for (const char* p = c_szSrc; *p && j < dstSize - 1; ++p)
		{
			const unsigned char c = (unsigned char)*p;
			szDst[j++] = (c < 0x20) ? ' ' : (char)c;
		}
	}
	szDst[j] = '\0';
}

// ---------------------------------------------------------------------
// CGiftManager
// ---------------------------------------------------------------------

#define GIFT_RANK_CACHE_SEC		30		// ilk-10 listesi cache suresi (sn)

CGiftManager::CGiftManager()
	: m_bLoaded(false)
{
	m_aiRankCacheTime[0] = 0;
	m_aiRankCacheTime[1] = 0;
}

CGiftManager::~CGiftManager()
{
}

bool CGiftManager::LoadGiftItems()
{
	m_vecGifts.clear();

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"SELECT id, icon_image, price_ep, page, slot_index, locale_name, locale_desc "
		"FROM player.gift_item WHERE enabled = 1 ORDER BY page, slot_index"));

	m_bLoaded = true;	// bir daha lazy-load denemesin (bos tablo da gecerli sonuctur)

	if (!pMsg || !pMsg->Get() || pMsg->Get()->uiNumRows == 0)
	{
		sys_log(0, "GIFT: hediye tanimi yok (player.gift_item bos veya erisilemedi)");
		return false;
	}

	MYSQL_ROW row;
	while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
	{
		if (m_vecGifts.size() >= GIFT_LIST_MAX)
		{
			sys_err("GIFT: %d ustunde hediye tanimi var, fazlasi listelenmiyor (GIFT_LIST_MAX)", GIFT_LIST_MAX);
			break;
		}

		TGiftItemDef def;
		DWORD dwTmp = 0;
		str_to_number(dwTmp, row[0]); def.dwId = dwTmp;
		dwTmp = 0; str_to_number(dwTmp, row[1]); def.dwIconVnum = dwTmp;
		dwTmp = 0; str_to_number(dwTmp, row[2]); def.dwPriceEP = dwTmp;
		int iTmp = 0; str_to_number(iTmp, row[3]); def.bPage = (BYTE)iTmp;
		iTmp = 0; str_to_number(iTmp, row[4]); def.bSlot = (BYTE)iTmp;
		def.stName = row[5] ? row[5] : "";
		def.stDesc = row[6] ? row[6] : "";

		m_vecGifts.push_back(def);
	}

	sys_log(0, "GIFT: %zu hediye tanimi yuklendi", m_vecGifts.size());
	return true;
}

void CGiftManager::Reload()
{
	m_bLoaded = false;
	LoadGiftItems();
}

const TGiftItemDef* CGiftManager::FindGift(DWORD dwId) const
{
	for (const auto& g : m_vecGifts)
		if (g.dwId == dwId)
			return &g;
	return nullptr;
}

void CGiftManager::SendGiftList(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
		return;

	if (!m_bLoaded)
		LoadGiftItems();

	TPacketGCGiftList gc;
	memset(&gc, 0, sizeof(gc));
	gc.bHeader = HEADER_GC_GIFT_LIST;

	BYTE bCount = 0;
	for (const auto& g : m_vecGifts)
	{
		if (bCount >= GIFT_LIST_MAX)
			break;

		TGiftItemEntry& e = gc.entries[bCount];
		e.wIndex = (WORD)g.dwId;
		e.dwIconVnum = g.dwIconVnum;
		e.dwPriceEP = g.dwPriceEP;
		e.bPage = g.bPage;
		e.bSlot = g.bSlot;
		strlcpy(e.szName, g.stName.c_str(), sizeof(e.szName));
		strlcpy(e.szDesc, g.stDesc.c_str(), sizeof(e.szDesc));
		++bCount;
	}

	gc.bCount = bCount;
	gc.wSize = (WORD)(offsetof(TPacketGCGiftList, entries) + bCount * sizeof(TGiftItemEntry));
	ch->GetDesc()->Packet(&gc, gc.wSize);

	// katalogla birlikte guncel EP + oyuncunun kendi hediye puanini da yolla
	SendEP(ch);
	SendGiftPoint(ch);
}

void CGiftManager::SendEP(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
		return;

	DWORD dwEP = 0;
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"SELECT cash FROM account.account WHERE id = %u", ch->GetDesc()->GetAccountTable().id));
	if (pMsg && pMsg->Get() && pMsg->Get()->uiNumRows > 0)
	{
		MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
		if (row && row[0])
			str_to_number(dwEP, row[0]);
	}

	TPacketGCGiftEP p;
	p.bHeader = HEADER_GC_GIFT_EP;
	p.dwEP = dwEP;
	ch->GetDesc()->Packet(&p, sizeof(p));
}

void CGiftManager::SendGiftPoint(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
		return;

	TPacketGCGiftPoint p;
	p.bHeader = HEADER_GC_GIFT_POINT;
	p.dwPoint = ch->GetGiftPoint();
	ch->GetDesc()->Packet(&p, sizeof(p));
}

bool CGiftManager::GetTargetByName(const char* c_szName, DWORD& r_dwPID, DWORD& r_dwAID) const
{
	r_dwPID = 0;
	r_dwAID = 0;

	if (!c_szName || !*c_szName)
		return false;

	// offline-guvenli isim -> pid/account_id cozumu (get_table_postfix ile shard-uyumlu)
	char szEscName[CHARACTER_NAME_MAX_LEN * 2 + 1];
	DBManager::instance().EscapeString(szEscName, sizeof(szEscName), c_szName, strlen(c_szName));

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"SELECT id, account_id FROM player%s WHERE name = '%s'", get_table_postfix(), szEscName));

	if (!pMsg || !pMsg->Get() || pMsg->Get()->uiNumRows == 0)
		return false;

	MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
	if (!row || !row[0] || !row[1])
		return false;

	str_to_number(r_dwPID, row[0]);
	str_to_number(r_dwAID, row[1]);
	return (r_dwPID != 0);
}

void CGiftManager::FindTarget(LPCHARACTER ch, const char* c_szName)
{
	if (!ch || !ch->GetDesc())
		return;

	TPacketGCGiftFindResult p;
	p.bHeader = HEADER_GC_GIFT_FIND_RESULT;
	p.bResult = GIFT_FIND_NOT_FOUND;
	memset(p.szName, 0, sizeof(p.szName));
	if (c_szName)
		strlcpy(p.szName, c_szName, sizeof(p.szName));

	DWORD dwPID = 0, dwAID = 0;
	if (GetTargetByName(c_szName, dwPID, dwAID))
	{
		const DWORD dwSenderAID = ch->GetDesc()->GetAccountTable().id;
		if (dwPID == ch->GetPlayerID() || dwAID == dwSenderAID)
			p.bResult = GIFT_FIND_SELF;
		else
			p.bResult = GIFT_FIND_OK;
	}

	ch->GetDesc()->Packet(&p, sizeof(p));
}

bool CGiftManager::IsBlocked(LPCHARACTER ch) const
{
	if (!ch)
		return true;
	if (ch->IsDead())
		return true;
	if (ch->GetExchange())			// ticaret aciksa engelle
		return true;
	if (ch->GetMyShop())			// pazar aciksa engelle
		return true;
	if (ch->IsOpenSafebox())		// depo aciksa engelle
		return true;
	return false;
}

bool CGiftManager::DeductEP(DWORD dwAccountID, DWORD dwTotal, DWORD& r_dwNewEP) const
{
	r_dwNewEP = 0;

	// ATOMIK dusme: kosul cash >= dwTotal. Etkilenen satir 0 ise yetersiz bakiye.
	// Boylece iki es-zamanli gonderim ayni bakiyeyi iki kez harcayamaz.
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"UPDATE account.account SET cash = cash - %u WHERE id = %u AND cash >= %u",
		dwTotal, dwAccountID, dwTotal));

	if (!pMsg || !pMsg->Get() || pMsg->Get()->uiAffectedRows == 0)
		return false;

	// yeni bakiyeyi oku
	std::unique_ptr<SQLMsg> pMsg2(DBManager::instance().DirectQuery(
		"SELECT cash FROM account.account WHERE id = %u", dwAccountID));
	if (pMsg2 && pMsg2->Get() && pMsg2->Get()->uiNumRows > 0)
	{
		MYSQL_ROW row = mysql_fetch_row(pMsg2->Get()->pSQLResult);
		if (row && row[0])
			str_to_number(r_dwNewEP, row[0]);
	}
	return true;
}

bool CGiftManager::AddGiftPoint(DWORD dwTargetPID, DWORD dwPoint) const
{
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"INSERT INTO player.gift_point (pid, total_point, last_update) VALUES (%u, %u, NOW()) "
		"ON DUPLICATE KEY UPDATE total_point = total_point + %u, last_update = NOW()",
		dwTargetPID, dwPoint, dwPoint));

	return (pMsg && pMsg->Get() && pMsg->Get()->uiAffectedRows > 0);
}

void CGiftManager::AddGiftSentPoint(DWORD dwSenderPID, DWORD dwPoint) const
{
	// Siralama istatistigi (best-effort): basarisiz olursa gonderim iptal EDILMEZ.
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"INSERT INTO player.gift_sent_point (pid, total_point, last_update) VALUES (%u, %u, NOW()) "
		"ON DUPLICATE KEY UPDATE total_point = total_point + %u, last_update = NOW()",
		dwSenderPID, dwPoint, dwPoint));

	if (!pMsg || !pMsg->Get() || pMsg->Get()->uiAffectedRows == 0)
		sys_err("GIFT: gift_sent_point guncellenemedi pid %u puan %u (tablo eksik olabilir, gift_rank_system.sql calistirildi mi?)", dwSenderPID, dwPoint);
}

void CGiftManager::DeliverNotify(LPCHARACTER ch, const char* c_szSenderName, const char* c_szGiftName,
	const char* c_szMessage, bool bAnonymous, DWORD dwPoint, DWORD dwTotalPoint) const
{
	if (!ch || !ch->GetDesc())
		return;

	TPacketGCGiftNotify p;
	memset(&p, 0, sizeof(p));
	p.bHeader = HEADER_GC_GIFT_NOTIFY;
	p.bAnonymous = bAnonymous ? 1 : 0;
	p.dwPoint = dwPoint;
	p.dwTotalPoint = dwTotalPoint;
	// anonim gonderimde gonderen adi client tarafinda "Gizli bir hayran..." olur;
	// yine de sunucu ismi sizdirmamak icin bos gonderir.
	if (!bAnonymous && c_szSenderName)
		strlcpy(p.szSenderName, c_szSenderName, sizeof(p.szSenderName));
	if (c_szGiftName)
		strlcpy(p.szGiftName, c_szGiftName, sizeof(p.szGiftName));
	if (c_szMessage)
		strlcpy(p.szMessage, c_szMessage, sizeof(p.szMessage));

	ch->GetDesc()->Packet(&p, sizeof(p));
}

void CGiftManager::SendGift(LPCHARACTER ch, const char* c_szName, WORD wGiftIndex, BYTE bCount, BYTE bFlags, const char* c_szMessage)
{
	if (!ch || !ch->GetDesc())
		return;

	auto fnResult = [&](BYTE bResult, DWORD dwNewEP)
	{
		TPacketGCGiftSendResult r;
		r.bHeader = HEADER_GC_GIFT_SEND_RESULT;
		r.bResult = bResult;
		r.dwNewEP = dwNewEP;
		r.wGiftIndex = wGiftIndex;
		r.bCount = bCount;
		ch->GetDesc()->Packet(&r, sizeof(r));
	};

	// 1) engel kontrolu (ticaret/pazar/depo/olu)
	if (IsBlocked(ch))
	{
		fnResult(GIFT_SEND_BLOCKED, 0);
		return;
	}

	// 2) flood/cooldown (pulse tabanli)
	if (ch->GetGiftSendTime() != 0 &&
		(thecore_pulse() - ch->GetGiftSendTime()) < PASSES_PER_SEC(GIFT_SEND_COOLTIME_SEC))
	{
		fnResult(GIFT_SEND_COOLDOWN, 0);
		return;
	}

	// 3) hediye gecerli mi
	if (!m_bLoaded)
		LoadGiftItems();
	const TGiftItemDef* pGift = FindGift(wGiftIndex);
	if (!pGift)
	{
		fnResult(GIFT_SEND_INVALID_GIFT, 0);
		return;
	}

	// 4) adet sunucu tarafinda tekrar dogrulanir
	if (bCount < 1 || bCount > GIFT_SEND_MAX_COUNT)
	{
		fnResult(GIFT_SEND_INVALID_COUNT, 0);
		return;
	}

	// 5) toplam ucret (64-bit ile hesapla, DWORD tasmasini engelle)
	const unsigned long long ullTotal = (unsigned long long)pGift->dwPriceEP * (unsigned long long)bCount;
	if (ullTotal == 0 || ullTotal > 0xFFFFFFFFULL)
	{
		fnResult(GIFT_SEND_INVALID_COUNT, 0);
		return;
	}
	const DWORD dwTotal = (DWORD)ullTotal;

	// 6) hedef karakter (offline dahil) + kendine/kendi hesabina engel
	DWORD dwTargetPID = 0, dwTargetAID = 0;
	if (!GetTargetByName(c_szName, dwTargetPID, dwTargetAID))
	{
		fnResult(GIFT_SEND_TARGET_NOT_FOUND, 0);
		return;
	}
	const DWORD dwSenderAID = ch->GetDesc()->GetAccountTable().id;
	if (dwTargetPID == ch->GetPlayerID() || dwTargetAID == dwSenderAID)
	{
		fnResult(GIFT_SEND_SELF, 0);
		return;
	}

	// 7) mesaji temizle (goruntuleme icin) ve SQL icin ayrica escape et
	char szMsg[GIFT_MESSAGE_MAX_LEN + 1];
	SanitizeMessage(c_szMessage, szMsg, sizeof(szMsg));

	// 8) EP'yi ATOMIK dus (gonderenin hesabi). 0 satir = yetersiz bakiye.
	DWORD dwNewEP = 0;
	if (!DeductEP(dwSenderAID, dwTotal, dwNewEP))
	{
		fnResult(GIFT_SEND_NOT_ENOUGH_EP, 0);
		return;
	}

	// 9) hediye puanini alicida ATOMIK arttir. Basarisizsa EP'yi iade et.
	if (!AddGiftPoint(dwTargetPID, dwTotal))
	{
		DBManager::instance().DirectQuery("UPDATE account.account SET cash = cash + %u WHERE id = %u", dwTotal, dwSenderAID);
		fnResult(GIFT_SEND_DB_ERROR, 0);
		return;
	}

	// 9b) gonderen siralamasi icin gonderilen puani biriktir (best-effort)
	AddGiftSentPoint(ch->GetPlayerID(), dwTotal);

	// alicinin yeni toplam puanini oku (canli bildirimde gostermek icin)
	DWORD dwTotalPoint = dwTotal;
	{
		std::unique_ptr<SQLMsg> pMsgTP(DBManager::instance().DirectQuery(
			"SELECT total_point FROM player.gift_point WHERE pid = %u", dwTargetPID));
		if (pMsgTP && pMsgTP->Get() && pMsgTP->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row = mysql_fetch_row(pMsgTP->Get()->pSQLResult);
			if (row && row[0])
				str_to_number(dwTotalPoint, row[0]);
		}
	}

	const bool bAnonymous = (bFlags & GIFT_FLAG_ANONYMOUS) ? true : false;
	const char* szSenderName = ch->GetName();

	// 10) bildirim kaydi (offline teslimat). insertId'yi al ki online teslimatta
	//     ayni satiri okunmus isaretleyip loginde tekrar gostermeyelim.
	std::string strEscMsg = EscapeSQL(szMsg);
	std::string strEscSender = EscapeSQL(szSenderName);
	DWORD dwNotifyId = 0;
	{
		std::unique_ptr<SQLMsg> pMsgN(DBManager::instance().DirectQuery(
			"INSERT INTO player.gift_notify (target_pid, gift_id, sender_name, message, is_anonymous, point, is_read, send_time) "
			"VALUES (%u, %u, '%s', '%s', %d, %u, 0, NOW())",
			dwTargetPID, pGift->dwId, strEscSender.c_str(), strEscMsg.c_str(),
			bAnonymous ? 1 : 0, dwTotal));
		if (pMsgN && pMsgN->Get())
			dwNotifyId = pMsgN->Get()->uiInsertID;
	}

	// 11) canli teslimat
	LPCHARACTER pTarget = CHARACTER_MANAGER::instance().FindByPID(dwTargetPID);
	if (pTarget)
	{
		// alici bu core'da online: bellek puanini senkronize et + canli bildirim
		pTarget->SetGiftPoint(dwTotalPoint);
		DeliverNotify(pTarget, szSenderName, pGift->stName.c_str(), szMsg, bAnonymous, dwTotal, dwTotalPoint);
		if (dwNotifyId != 0)
			DBManager::instance().DirectQuery("UPDATE player.gift_notify SET is_read = 1 WHERE id = %u", dwNotifyId);
	}
	else
	{
		// baska core'da online olabilir: P2P ile yay. Hicbir core teslim etmezse
		// (offline) gift_notify satiri loginde gosterilir.
		TPacketGGGiftNotify gg;
		memset(&gg, 0, sizeof(gg));
		gg.bHeader = HEADER_GG_GIFT_NOTIFY;
		gg.dwNotifyId = dwNotifyId;
		gg.dwTargetPID = dwTargetPID;
		gg.bAnonymous = bAnonymous ? 1 : 0;
		gg.dwPoint = dwTotal;
		gg.dwTotalPoint = dwTotalPoint;
		strlcpy(gg.szSenderName, szSenderName, sizeof(gg.szSenderName));
		strlcpy(gg.szGiftName, pGift->stName.c_str(), sizeof(gg.szGiftName));
		strlcpy(gg.szMessage, szMsg, sizeof(gg.szMessage));
		P2P_MANAGER::instance().Send(&gg, sizeof(gg));
	}

	// 12) cooldown baslat
	ch->SetGiftSendTime();

	// 13) log (EP gercek para karsiligi -> zorunlu)
	char szType[32];
	snprintf(szType, sizeof(szType), "GIFT%s%s",
		(bFlags & GIFT_FLAG_PACKAGE) ? "|PKG" : "",
		bAnonymous ? "|ANON" : "");
	LogManager::instance().GiftLog(ch->GetPlayerID(), szSenderName, dwTargetPID, c_szName, pGift->dwId, bCount, szType);

	// 14) gonderene sonuc + guncel EP
	fnResult(GIFT_SEND_OK, dwNewEP);
}

void CGiftManager::LoadGiftData(LPCHARACTER ch)
{
	if (!ch || !ch->GetDesc())
		return;

	const DWORD dwPID = ch->GetPlayerID();

	// 1) hediye puanini yukle
	DWORD dwPoint = 0;
	{
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"SELECT total_point FROM player.gift_point WHERE pid = %u", dwPID));
		if (pMsg && pMsg->Get() && pMsg->Get()->uiNumRows > 0)
		{
			MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
			if (row && row[0])
				str_to_number(dwPoint, row[0]);
		}
	}
	ch->SetGiftPoint(dwPoint);
	SendGiftPoint(ch);

	// 2) okunmamis bildirimleri teslim et
	if (!m_bLoaded)
		LoadGiftItems();

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"SELECT id, gift_id, sender_name, message, is_anonymous, point FROM player.gift_notify "
		"WHERE target_pid = %u AND is_read = 0 ORDER BY id ASC", dwPID));

	// Sadece bu SELECT'in dondurdugu satirlari okundu isaretle (id ile). Boylece
	// login sirasinda gelen YENI bir bildirim (SELECT sonrasi INSERT) yutulmaz;
	// o satir bir sonraki login'de veya P2P ile teslim edilir.
	std::string strDeliveredIds;
	if (pMsg && pMsg->Get() && pMsg->Get()->uiNumRows > 0)
	{
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
		{
			DWORD dwRowId = 0, dwGiftId = 0, dwNotifyPoint = 0;
			int iAnon = 0;
			str_to_number(dwRowId, row[0] ? row[0] : "0");
			str_to_number(dwGiftId, row[1] ? row[1] : "0");
			const char* szSender = row[2] ? row[2] : "";
			const char* szMsg = row[3] ? row[3] : "";
			str_to_number(iAnon, row[4] ? row[4] : "0");
			str_to_number(dwNotifyPoint, row[5] ? row[5] : "0");

			const TGiftItemDef* pGift = FindGift(dwGiftId);
			const char* szGiftName = pGift ? pGift->stName.c_str() : "?";

			DeliverNotify(ch, szSender, szGiftName, szMsg, iAnon ? true : false, dwNotifyPoint, dwPoint);

			char szId[16];
			snprintf(szId, sizeof(szId), "%u", dwRowId);
			if (!strDeliveredIds.empty())
				strDeliveredIds += ",";
			strDeliveredIds += szId;
		}
	}

	if (!strDeliveredIds.empty())
		DBManager::instance().DirectQuery("UPDATE player.gift_notify SET is_read = 1 WHERE id IN (%s)", strDeliveredIds.c_str());
}

static const char* GiftRankTable(BYTE bBoardType)
{
	return (bBoardType == GIFT_RANK_BOARD_SENDER) ? "gift_sent_point" : "gift_point";
}

const std::vector<TGiftRankEntry>& CGiftManager::GetTopList(BYTE bBoardType)
{
	const int iIdx = (bBoardType == GIFT_RANK_BOARD_SENDER) ? 0 : 1;

	// cache tazeyse dogrudan don
	if (m_aiRankCacheTime[iIdx] != 0 &&
		(thecore_pulse() - m_aiRankCacheTime[iIdx]) < PASSES_PER_SEC(GIFT_RANK_CACHE_SEC))
		return m_avecRankCache[iIdx];

	m_avecRankCache[iIdx].clear();
	m_aiRankCacheTime[iIdx] = thecore_pulse();

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"SELECT p.name, g.total_point FROM player.%s g "
		"JOIN player.player%s p ON p.id = g.pid "
		"WHERE g.total_point > 0 "
		"ORDER BY g.total_point DESC, g.pid ASC LIMIT %d",
		GiftRankTable(bBoardType), get_table_postfix(), GIFT_RANK_MAX));

	if (pMsg && pMsg->Get() && pMsg->Get()->uiNumRows > 0)
	{
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != nullptr)
		{
			TGiftRankEntry e;
			memset(&e, 0, sizeof(e));
			if (row[0])
				strlcpy(e.szName, row[0], sizeof(e.szName));
			DWORD dwPoint = 0;
			if (row[1])
				str_to_number(dwPoint, row[1]);
			e.dwPoint = dwPoint;
			m_avecRankCache[iIdx].push_back(e);
		}
	}

	return m_avecRankCache[iIdx];
}

void CGiftManager::SendRank(LPCHARACTER ch, BYTE bBoardType)
{
	if (!ch || !ch->GetDesc())
		return;

	if (bBoardType > GIFT_RANK_BOARD_RECEIVER)
		bBoardType = GIFT_RANK_BOARD_RECEIVER;

	// Flood korumasi (kendi-siram sorgulari senkron DirectQuery oldugu icin):
	//  - < 0.5 sn: sessiz dusur (paket dongusu / abuse)
	//  - < GIFT_RANK_REQ_COOLTIME_SEC: DB'ye GITMEDEN cevapla (top-10 cache +
	//    karakter uzerindeki son kendi-siram degerleri) -> hizli sekme degisimi
	//    "Yukleniyor..."da takili kalmaz
	//  - degilse: taze hesapla ve karakter cache'ini guncelle
	bool bUseCharCache = false;
	if (ch->GetGiftRankTime() != 0)
	{
		const int iDelta = thecore_pulse() - ch->GetGiftRankTime();
		if (iDelta < PASSES_PER_SEC(1) / 2)
			return;
		if (iDelta < PASSES_PER_SEC(GIFT_RANK_REQ_COOLTIME_SEC))
			bUseCharCache = true;
	}
	ch->SetGiftRankTime();

	TPacketGCGiftRank gc;
	memset(&gc, 0, sizeof(gc));
	gc.bHeader = HEADER_GC_GIFT_RANK;
	gc.bBoardType = bBoardType;

	// ilk 10 (30 sn cache'li)
	const std::vector<TGiftRankEntry>& vec = GetTopList(bBoardType);
	BYTE bCount = 0;
	for (const auto& e : vec)
	{
		if (bCount >= GIFT_RANK_MAX)
			break;
		gc.entries[bCount] = e;
		++bCount;
	}
	gc.bCount = bCount;

	DWORD dwMyRank = 0;		// 0 = siralamada yok ("-")
	DWORD dwMyPoint = 0;

	if (bUseCharCache)
	{
		dwMyRank = ch->GetGiftRankCacheRank(bBoardType);
		dwMyPoint = ch->GetGiftRankCachePoint(bBoardType);
	}
	else
	{
		const DWORD dwPID = ch->GetPlayerID();
		{
			std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"SELECT total_point FROM player.%s WHERE pid = %u", GiftRankTable(bBoardType), dwPID));
			if (pMsg && pMsg->Get() && pMsg->Get()->uiNumRows > 0)
			{
				MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
				if (row && row[0])
					str_to_number(dwMyPoint, row[0]);
			}
		}

		if (dwMyPoint > 0)
		{
			std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"SELECT COUNT(*) FROM player.%s WHERE total_point > %u", GiftRankTable(bBoardType), dwMyPoint));
			if (pMsg && pMsg->Get() && pMsg->Get()->uiNumRows > 0)
			{
				MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);
				DWORD dwAbove = 0;
				if (row && row[0])
					str_to_number(dwAbove, row[0]);
				dwMyRank = dwAbove + 1;
			}
		}

		ch->SetGiftRankCache(bBoardType, dwMyRank, dwMyPoint);
	}

	gc.dwMyRank = dwMyRank;
	gc.dwMyPoint = dwMyPoint;

	ch->GetDesc()->Packet(&gc, sizeof(gc));
}

void CGiftManager::OnP2PGiftNotify(const void* c_pvData)
{
	const TPacketGGGiftNotify* p = (const TPacketGGGiftNotify*)c_pvData;

	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(p->dwTargetPID);
	if (!ch)
		return;		// alici bu core'da degil; baska core teslim eder (ya da offline satir kalir)

	// bellek puanini senkronize et + canli bildirim
	ch->SetGiftPoint(p->dwTotalPoint);
	DeliverNotify(ch, p->szSenderName, p->szGiftName, p->szMessage,
		p->bAnonymous ? true : false, p->dwPoint, p->dwTotalPoint);

	// bu satir teslim edildi; loginde tekrar gosterme
	if (p->dwNotifyId != 0)
		DBManager::instance().DirectQuery("UPDATE player.gift_notify SET is_read = 1 WHERE id = %u", p->dwNotifyId);
}

#endif
