#include "stdafx.h"

#ifdef ENABLE_IKASHOP_SEARCH

#include "constants.h"
#include "config.h"
#include "utils.h"
#include "desc.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "item_manager.h"
#include "shop.h"
#include "shop_manager.h"
#include "db.h"
#include "log.h"
#include "questmanager.h"
#include "p2p.h"
#include "buffer_manager.h"
#include "../../common/PulseManager.h"
#include "ikashop_search.h"

#include <algorithm>
#include <random>

// ============================================================================
// Yardimcilar
// ============================================================================

static void __LowerAscii(char * s)
{
	for (; *s; ++s)
		if (*s >= 'A' && *s <= 'Z')
			*s = *s - 'A' + 'a';
}

CIkaShopSearchManager & CIkaShopSearchManager::Instance()
{
	static CIkaShopSearchManager s_kInstance;
	return s_kInstance;
}

CIkaShopSearchManager::CIkaShopSearchManager()
	: m_bProtoCacheReady(false)
{
}

// ============================================================================
// Proto onbellegi: ilk aramada bir kez kurulur (boot'ta protolar zaten yuklu)
// ============================================================================

void CIkaShopSearchManager::BuildProtoCache()
{
	if (m_bProtoCacheReady)
		return;

	const std::vector<TItemTable> & c_rVec = ITEM_MANAGER::instance().GetTable();

	m_vecProtoCache.clear();
	m_vecProtoCache.reserve(c_rVec.size());

	for (DWORD i = 0; i < c_rVec.size(); ++i)
	{
		const TItemTable & r = c_rVec[i];

		if (r.dwVnum == 0)
			continue;

		SProtoCacheEntry entry;
		entry.dwVnum = r.dwVnum;
		entry.bType = r.bType;
		entry.bSubType = r.bSubType;
		entry.iLevelLimit = 0;

		for (int L = 0; L < ITEM_LIMIT_MAX_NUM; ++L)
		{
			if (r.aLimits[L].bType == LIMIT_LEVEL)
			{
				entry.iLevelLimit = (int) r.aLimits[L].lValue;
				break;
			}
		}

		// Client locale ismiyle aranir (kucuk-harf; Turkce ASCII disi karakterler oldugu gibi kalir)
		char szLower[ITEM_NAME_MAX_LEN + 1];
		strlcpy(szLower, r.szLocaleName, sizeof(szLower));
		__LowerAscii(szLower);
		entry.stLowerName.assign(szLower);

		m_vecProtoCache.push_back(entry);
	}

	m_mapProtoByVnum.clear();
	for (DWORD i = 0; i < m_vecProtoCache.size(); ++i)
		m_mapProtoByVnum[m_vecProtoCache[i].dwVnum] = &m_vecProtoCache[i];

	m_bProtoCacheReady = true;
	sys_log(0, "IKASEARCH: proto onbellegi kuruldu (%u kayit)", (DWORD) m_vecProtoCache.size());
}

bool CIkaShopSearchManager::MatchProtoFilters(DWORD dwVnum, const TIkaSearchFilterCopy & filter) const
{
	const auto it = m_mapProtoByVnum.find(dwVnum);

	if (it == m_mapProtoByVnum.end())
		return false;	// proto'su olmayan item aramada gorunmez

	const SProtoCacheEntry * p = it->second;

	if (filter.bType != 0xFF)
	{
		if (p->bType != filter.bType)
			return false;

		if (filter.bSubType != 0xFF && p->bSubType != filter.bSubType)
			return false;
	}

	if (filter.iLevelMin > 0 || filter.iLevelMax > 0)
	{
		if (p->iLevelLimit < filter.iLevelMin)
			return false;

		if (filter.iLevelMax > 0 && p->iLevelLimit > filter.iLevelMax)
			return false;
	}

	if (filter.szName[0] != '\0')
	{
		if (p->stLowerName.find(filter.szName) == std::string::npos)
			return false;
	}

	return true;
}

// Donus: 0 = isim/tip/seviye filtresi yok, 1 = IN listesi hazir, 2 = aday cok (IN kullanma), 3 = hic aday yok
bool CIkaShopSearchManager::CollectCandidateVnums(const TIkaSearchFilterCopy & filter, std::vector<DWORD> & vecOut) const
{
	vecOut.clear();

	const bool bNameFilter = (filter.szName[0] != '\0');
	const bool bTypeFilter = (filter.bType != 0xFF);
	const bool bLevelFilter = (filter.iLevelMin > 0 || filter.iLevelMax > 0);

	if (!bNameFilter && !bTypeFilter && !bLevelFilter)
		return false;

	for (DWORD i = 0; i < m_vecProtoCache.size(); ++i)
	{
		if (!MatchProtoFilters(m_vecProtoCache[i].dwVnum, filter))
			continue;

		vecOut.push_back(m_vecProtoCache[i].dwVnum);

		if (vecOut.size() > (size_t) IKASEARCH_VNUM_IN_MAX)
			break;	// tavan asildi; IN kullanilmayacak (isaret: boyut > MAX)
	}

	return true;
}

// ============================================================================
// GC gonderim yardimcilari
// ============================================================================

void CIkaShopSearchManager::SendPopup(LPCHARACTER ch, const char * c_szLocaleKey)
{
	if (!ch || !ch->GetDesc())
		return;

	char szKey[IKASEARCH_POPUP_KEY_LEN];
	memset(szKey, 0, sizeof(szKey));
	strlcpy(szKey, c_szLocaleKey, sizeof(szKey));

	TPacketGCIkaShopSearch pack;
	pack.bHeader = HEADER_GC_NEW_OFFLINESHOP;
	pack.bSubheader = IKASEARCH_GC_POPUP;
	pack.wCount = 0;
	pack.wSize = (WORD) (sizeof(pack) + sizeof(szKey));

	ch->GetDesc()->BufferedPacket(&pack, sizeof(pack));
	ch->GetDesc()->Packet(szKey, sizeof(szKey));
}

void CIkaShopSearchManager::SendResultDelete(LPCHARACTER ch, DWORD dwItemDBID)
{
	if (!ch || !ch->GetDesc())
		return;

	TPacketGCIkaShopSearch pack;
	pack.bHeader = HEADER_GC_NEW_OFFLINESHOP;
	pack.bSubheader = IKASEARCH_GC_RESULT_DELETE;
	pack.wCount = 0;
	pack.wSize = (WORD) (sizeof(pack) + sizeof(DWORD));

	ch->GetDesc()->BufferedPacket(&pack, sizeof(pack));
	ch->GetDesc()->Packet(&dwItemDBID, sizeof(DWORD));
}

void CIkaShopSearchManager::BroadcastSoldP2P(DWORD dwOwnerPID, DWORD dwItemDBID)
{
	TPacketGGIkaShopSold p;
	p.bHeader = HEADER_GG_IKASHOP_SOLD;
	p.dwOwnerPID = dwOwnerPID;
	p.dwItemDBID = dwItemDBID;

	P2P_MANAGER::instance().Send(&p, sizeof(p));
}

// ============================================================================
// CG 84 dispatch
// ============================================================================

void CIkaShopSearchManager::ReceivePacket(LPCHARACTER ch, const TPacketCGIkaShopSearch * p)
{
	if (!ch || !ch->GetDesc() || !p)
		return;

	// Acil kapama: sistem canliyken eventflag ile susturulur (shop_off emsali)
	if (quest::CQuestManager::instance().GetEventFlag("ikasearch_off") == 1)
	{
		SendPopup(ch, "IKASHOP_SEARCH_OFF");
		return;
	}

	switch (p->bSubheader)
	{
		case IKASEARCH_CG_FILTER:
			HandleFilterRequest(ch, p);
			break;

		case IKASEARCH_CG_BUY:
			HandleBuyRequest(ch, p);
			break;

		case IKASEARCH_CG_VIEW_SHOP:
			HandleViewShopRequest(ch, p);
			break;

		default:
			sys_err("IKASEARCH: bilinmeyen subheader %u (pid %u)", p->bSubheader, ch->GetPlayerID());
			break;
	}
}

// ============================================================================
// FILTER: async arama
// ============================================================================

void CIkaShopSearchManager::HandleFilterRequest(LPCHARACTER ch, const TPacketCGIkaShopSearch * p)
{
	const DWORD dwPID = ch->GetPlayerID();

	if (!PulseManager::Instance().IncreaseClock(dwPID, ePulse::IkaShopSearch, std::chrono::milliseconds(IKASEARCH_SEARCH_COOLDOWN_MS)))
	{
		SendPopup(ch, "IKASHOP_SEARCH_COOLDOWN");
		return;
	}

	// Ayni oyuncunun cevabi gelmemis aramasi varsa yenisini baslatma
	const auto itFlight = m_mapInFlight.find(dwPID);
	if (itFlight != m_mapInFlight.end())
	{
		if (get_global_time() - itFlight->second < IKASEARCH_INFLIGHT_TIMEOUT_SEC)
		{
			SendPopup(ch, "IKASHOP_SEARCH_BUSY");
			return;
		}

		m_mapInFlight.erase(itFlight);	// callback kaybolmus; kilidi yenile
	}

	BuildProtoCache();

	// Filtre kopyasini kur (async callback'e tasinacak)
	TIkaSearchFilterCopy filter;
	memset(&filter, 0, sizeof(filter));
	filter.dwPID = dwPID;
	strlcpy(filter.szName, p->szName, sizeof(filter.szName));
	__LowerAscii(filter.szName);
	filter.bType = p->bType;
	filter.bSubType = p->bSubType;
	filter.dwPriceMin = p->dwPriceMin;
	filter.dwPriceMax = p->dwPriceMax;
	filter.iLevelMin = MINMAX(0, p->iLevelMin, 250);
	filter.iLevelMax = MINMAX(0, p->iLevelMax, 250);

	int iAttrCount = 0;
	for (int i = 0; i < IKASEARCH_FILTER_ATTR_NUM; ++i)
	{
		if (p->aFilterAttrs[i].bType != 0 && p->aFilterAttrs[i].sValue > 0)
			filter.aAttrs[iAttrCount++] = p->aFilterAttrs[i];
	}

	// Isim filtresi cok kisa ise yok say (asiri genis taramayi onler)
	if (filter.szName[0] != '\0' && strlen(filter.szName) < 2)
		filter.szName[0] = '\0';

	// FILL modu (IKASHOP SendRandomSearchFillRequest): pencere acilisinda filtresiz vitrin doldurma.
	// iReserved1 == 1 -> filtre zorunlulugu atlanir; en yeni sold=0 itemler doner (callback shuffle'lar).
	const bool bFillMode = (p->iReserved1 == 1);

	const bool bNameTypeLevelFilter = (!bFillMode && (filter.szName[0] != '\0' || filter.bType != 0xFF || filter.iLevelMin > 0 || filter.iLevelMax > 0));
	const bool bPriceFilter = (!bFillMode && (filter.dwPriceMax > 0 || filter.dwPriceMin > 0));

	if (bFillMode)
	{
		// Fill: hicbir filtre uygulanmaz; callback'te post-filter de calismaz
		filter.szName[0] = '\0';
		filter.bType = 0xFF;
		filter.bSubType = 0xFF;
		filter.dwPriceMin = 0;
		filter.dwPriceMax = 0;
		filter.iLevelMin = 0;
		filter.iLevelMax = 0;
		iAttrCount = 0;
		memset(filter.aAttrs, 0, sizeof(filter.aAttrs));
	}
	// Tamamen bos arama (fill degil) kabul edilmez (IKASHOP NO_FILTER_USED davranisi)
	else if (!bNameTypeLevelFilter && !bPriceFilter && iAttrCount == 0)
	{
		SendPopup(ch, "IKASHOP_SEARCH_NO_FILTER");
		return;
	}

	// Aday vnum kumesi (isim/tip/seviye -> IN listesi)
	std::vector<DWORD> vecVnums;
	bool bUseVnumSet = false;

	if (bNameTypeLevelFilter)
	{
		CollectCandidateVnums(filter, vecVnums);

		if (vecVnums.empty())
		{
			// Hicbir proto eslesmedi: SQL'e gitmeye gerek yok
			TPacketGCIkaShopSearch pack;
			pack.bHeader = HEADER_GC_NEW_OFFLINESHOP;
			pack.bSubheader = IKASEARCH_GC_RESULT;
			pack.wCount = 0;
			pack.wSize = sizeof(pack);
			ch->GetDesc()->Packet(&pack, sizeof(pack));
			return;
		}

		bUseVnumSet = (vecVnums.size() <= (size_t) IKASEARCH_VNUM_IN_MAX);
	}

	// SQL kur - kullanici girdisi SQL'e HIC girmez (isim filtresi vnum kumesi uzerinden calisir).
	// Tampon boyutu DBManager::ReturnQuery ic tamponuyla (4096) UYUMLU tutulur; buyugu orada
	// SESSIZCE KIRPILIR ve bozuk SQL uretirdi. Her snprintf ONCE kalan alani kontrol eder
	// (iLen tamponu asarsa sizeof-iLen isaretsiz underflow yapardi -> yigin tasmasi).
	char szQuery[4096];
	int iLen = snprintf(szQuery, sizeof(szQuery),
		"SELECT i.id, i.player_id, i.vnum, i.count, i.price, "
		"i.socket0, i.socket1, i.socket2, "
		"i.attrtype0, i.attrvalue0, i.attrtype1, i.attrvalue1, i.attrtype2, i.attrvalue2, i.attrtype3, i.attrvalue3, "
		"i.attrtype4, i.attrvalue4, i.attrtype5, i.attrvalue5, i.attrtype6, i.attrvalue6, "
		"s.name, s.channel, s.map_index, TIMESTAMPDIFF(MINUTE, NOW(), s.date_close) "
		"FROM player_shop_items i JOIN player_shop s ON s.player_id = i.player_id "
		"WHERE i.sold = 0 AND i.player_id != %u AND s.channel BETWEEN 1 AND 98 AND s.map_index < 10000",
		dwPID);

	// LIMIT eki icin (~20 bayt) rezerv birak; guvenli yazma budcesi
	const int iBudget = (int) sizeof(szQuery) - 24;
	bool bQueryTooLong = (iLen < 0 || iLen >= iBudget);

	// Kalan alani her adimda guvenli hesaplayan ekleme (underflow imkansiz). Basarisizsa iLen
	// degismez -> cagiran, ilgili yan-cumleyi guvenle atlayabilir (post-filter dogrulugu korur).
#define IKASEARCH_APPEND(...) \
	do { \
		if (bQueryTooLong) break; \
		int __rem = iBudget - iLen; \
		if (__rem <= 1) { bQueryTooLong = true; break; } \
		int __n = snprintf(szQuery + iLen, (size_t) __rem, __VA_ARGS__); \
		if (__n < 0 || __n >= __rem) { bQueryTooLong = true; break; } \
		iLen += __n; \
	} while (0)

	if (filter.dwPriceMin > 0)
		IKASEARCH_APPEND(" AND i.price >= %u", filter.dwPriceMin);

	if (filter.dwPriceMax > 0 && filter.dwPriceMax >= filter.dwPriceMin)
		IKASEARCH_APPEND(" AND i.price <= %u", filter.dwPriceMax);

	// Efsun filtreleri: her istenen efsun 7 attr kolonundan birinde min degerle bulunmali
	for (int i = 0; i < iAttrCount && !bQueryTooLong; ++i)
	{
		const int iType = (int) filter.aAttrs[i].bType;
		const int iVal = (int) filter.aAttrs[i].sValue;

		IKASEARCH_APPEND(" AND (");
		for (int c = 0; c < ITEM_ATTRIBUTE_MAX_NUM; ++c)
			IKASEARCH_APPEND("%s(i.attrtype%d = %d AND i.attrvalue%d >= %d)",
				c == 0 ? "" : " OR ", c, iType, c, iVal);
		IKASEARCH_APPEND(")");
	}

	// Efsun filtreleri tampona sigmazsa arama BASARISIZ -> yalniz efsun-siz (base) daralt.
	if (bQueryTooLong)
	{
		sys_err("IKASEARCH: efsun filtreleri tampona sigmadi (pid %u)", dwPID);
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	// vnum IN listesi: TAM sigmazsa yan-cumleyi TAMAMEN atla (post-filter dogrulugu korur;
	// yalniz SQL biraz daha genis tarar, LIMIT 1000 ile sinirli). Boylece bozuk yarim IN olusmaz.
	if (bUseVnumSet)
	{
		const int iLenBeforeIn = iLen;
		IKASEARCH_APPEND(" AND i.vnum IN (");
		for (size_t i = 0; i < vecVnums.size() && !bQueryTooLong; ++i)
			IKASEARCH_APPEND("%s%u", i == 0 ? "" : ",", vecVnums[i]);
		IKASEARCH_APPEND(")");

		if (bQueryTooLong)
		{
			// IN sigmadi: yan-cumleyi geri al, IN'siz devam et (callback post-filter eler)
			iLen = iLenBeforeIn;
			szQuery[iLen] = '\0';
			bQueryTooLong = false;
			if (test_server)
				sys_log(0, "IKASEARCH: vnum IN sigmadi, post-filter'a birakildi (pid %u)", dwPID);
		}
	}

	// Fill modunda en yeni ilanlar gelsin (LIMIT'in hangi 1000 satiri sectigi onemli)
	if (bFillMode)
		IKASEARCH_APPEND(" ORDER BY i.id DESC");

	IKASEARCH_APPEND(" LIMIT %d", (int) IKASEARCH_SQL_LIMIT);

#undef IKASEARCH_APPEND

	if (bQueryTooLong)
	{
		sys_err("IKASEARCH: sorgu tampona sigmadi (pid %u, len %d)", dwPID, iLen);
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	// Filtre kopyasi callback'te post-filter icin tasinir
	TIkaSearchFilterCopy * pFilterCopy = M2_NEW TIkaSearchFilterCopy;
	*pFilterCopy = filter;

	m_mapInFlight[dwPID] = get_global_time();

	// ASYNC: arama yolunda DirectQuery YASAK (pulse stall / 5K launch dersi)
	DBManager::instance().ReturnQuery(QID_IKASEARCH, dwPID, pFilterCopy, "%s", szQuery);

	if (test_server)
		sys_log(0, "IKASEARCH: FILTER pid %u query_len %d vnum_set %s(%u)", dwPID, iLen, bUseVnumSet ? "IN" : "yok", (DWORD) vecVnums.size());
}

// db.cpp AnalyzeReturnQuery -> QID_IKASEARCH
void CIkaShopSearchManager::OnSearchQueryResult(SQLMsg * pMsg, DWORD dwPID, void * pvData)
{
	TIkaSearchFilterCopy * pFilter = (TIkaSearchFilterCopy *) pvData;

	m_mapInFlight.erase(dwPID);

	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(dwPID);

	if (!ch || !ch->GetDesc())
	{
		if (pFilter)
			M2_DELETE(pFilter);
		return;	// oyuncu ciktiysa sonuc coplenir
	}

	std::vector<SIkaSearchResult> vecResults;

	if (pMsg && pMsg->Get() && pMsg->Get()->pSQLResult && pMsg->Get()->uiNumRows > 0)
	{
		vecResults.reserve(MIN(pMsg->Get()->uiNumRows, (DWORD) IKASEARCH_SQL_LIMIT));

		const bool bProtoFilterActive = pFilter &&
			(pFilter->szName[0] != '\0' || pFilter->bType != 0xFF || pFilter->iLevelMin > 0 || pFilter->iLevelMax > 0);

		MYSQL_ROW row;
		while ((row = mysql_fetch_row(pMsg->Get()->pSQLResult)) != NULL)
		{
			int col = 0;

			SIkaSearchResult r;
			memset(&r, 0, sizeof(r));

			str_to_number(r.dwItemDBID, row[col++]);
			str_to_number(r.dwOwnerPID, row[col++]);
			str_to_number(r.dwVnum, row[col++]);

			DWORD dwCount = 0;
			str_to_number(dwCount, row[col++]);
			r.bCount = (BYTE) (dwCount > 255 ? 255 : dwCount);

			str_to_number(r.dwPrice, row[col++]);

			for (int s = 0; s < ITEM_SOCKET_MAX_NUM; ++s)
			{
				int iSocket = 0;
				str_to_number(iSocket, row[col++]);
				r.aiSockets[s] = iSocket;
			}

			for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
			{
				DWORD dwAttrType = 0;
				int iAttrValue = 0;
				str_to_number(dwAttrType, row[col++]);
				str_to_number(iAttrValue, row[col++]);
				r.aAttrs[a].bType = (BYTE) dwAttrType;
				r.aAttrs[a].sValue = (short) iAttrValue;
			}

			if (row[col])
				strlcpy(r.szShopName, row[col], sizeof(r.szShopName));
			col++;

			DWORD dwChannel = 0;
			str_to_number(dwChannel, row[col++]);
			r.bChannel = (BYTE) dwChannel;

			str_to_number(r.iMapIndex, row[col++]);

			int iDurationMin = 0;
			if (row[col])
				str_to_number(iDurationMin, row[col]);
			col++;
			r.iDurationMin = MAX(0, iDurationMin);

			// Post-filter: IN listesi kullanilamadiginda isim/tip/seviye burada elenir;
			// IN kullanildiysa da ucuz bir guvenlik dogrulamasidir
			if (bProtoFilterActive && !MatchProtoFilters(r.dwVnum, *pFilter))
				continue;

			// Kendi dukkani (SQL'de de var; savunma katmani)
			if (r.dwOwnerPID == dwPID)
				continue;

			vecResults.push_back(r);
		}
	}

	if (pFilter)
		M2_DELETE(pFilter);

	// IKASHOP davranisi: sonuclar karistirilir (ilk-sira avantajini kirar), sonra 250'ye kirpilir
	if (vecResults.size() > 1)
	{
		std::mt19937 rng((unsigned int) get_dword_time() ^ dwPID);
		std::shuffle(vecResults.begin(), vecResults.end(), rng);
	}

	if (vecResults.size() > (size_t) IKASEARCH_MAX_RESULTS)
		vecResults.resize(IKASEARCH_MAX_RESULTS);

	TPacketGCIkaShopSearch pack;
	pack.bHeader = HEADER_GC_NEW_OFFLINESHOP;
	pack.bSubheader = IKASEARCH_GC_RESULT;
	pack.wCount = (WORD) vecResults.size();
	pack.wSize = (WORD) (sizeof(pack) + sizeof(SIkaSearchResult) * vecResults.size());

	TEMP_BUFFER buf(32768);
	buf.write(&pack, sizeof(pack));

	for (size_t i = 0; i < vecResults.size(); ++i)
		buf.write(&vecResults[i], sizeof(SIkaSearchResult));

	ch->GetDesc()->Packet(buf.read_peek(), buf.size());

	if (test_server)
		sys_log(0, "IKASEARCH: RESULT pid %u count %u", dwPID, pack.wCount);
}

// ============================================================================
// BUY: uzaktan satin alma (atomik SQL claim)
// ============================================================================

void CIkaShopSearchManager::HandleBuyRequest(LPCHARACTER ch, const TPacketCGIkaShopSearch * p)
{
	const DWORD dwPID = ch->GetPlayerID();
	const DWORD dwOwnerPID = p->dwOwnerPID;
	const DWORD dwItemDBID = p->dwItemDBID;
	const DWORD dwSeenPrice = p->dwSeenPrice;

	if (!PulseManager::Instance().IncreaseClock(dwPID, ePulse::IkaShopBuy, std::chrono::milliseconds(IKASEARCH_BUY_COOLDOWN_MS)))
		return;

	if (dwItemDBID == 0 || dwOwnerPID == 0)
		return;

	// DUPE-3: kendi dukkanindan alim reddi (paket duzeyinde erken kapi; DB dogrulamasi asagida tekrar)
	if (dwOwnerPID == dwPID)
	{
		SendPopup(ch, "IKASHOP_CANT_BUY_OWN_ITEM");
		return;
	}

	// Item tasiyabilecek durumda mi (takas/olum/depo vb.)
	if (!ch->CanHandleItem())
	{
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	// 1) SNAPSHOT: PK uzerinden tek satir (senkron; indeksli, ucuz)
	char szSockets[128];
	char szAttrs[256];
	int socLen = snprintf(szSockets, sizeof(szSockets), "i.socket0");
	int attrLen = snprintf(szAttrs, sizeof(szAttrs), "i.attrtype0, i.attrvalue0");
	for (BYTE i = 1; i < ITEM_SOCKET_MAX_NUM; ++i)
		socLen += snprintf(szSockets + socLen, sizeof(szSockets) - socLen, ", i.socket%d", i);
	for (BYTE i = 1; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		attrLen += snprintf(szAttrs + attrLen, sizeof(szAttrs) - attrLen, ", i.attrtype%d, i.attrvalue%d", i, i);

	auto pkMsg = DBManager::instance().DirectQuery(
		"SELECT i.player_id, i.vnum, i.count, i.price, i.sold, %s, %s, s.player_id "
		"FROM player_shop_items i LEFT JOIN player_shop s ON s.player_id = i.player_id "
		"WHERE i.id = %u",
		szSockets, szAttrs, dwItemDBID);

	if (!pkMsg || !pkMsg->Get() || pkMsg->Get()->uiNumRows == 0)
	{
		SendPopup(ch, "IKASHOP_SHOP_NOT_FOUND");
		SendResultDelete(ch, dwItemDBID);
		return;
	}

	MYSQL_ROW row = mysql_fetch_row(pkMsg->Get()->pSQLResult);
	if (!row)
	{
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	int col = 0;
	DWORD dwRowOwner = 0, dwVnum = 0, dwCount = 0, dwPrice = 0, dwSold = 0;
	str_to_number(dwRowOwner, row[col++]);
	str_to_number(dwVnum, row[col++]);
	str_to_number(dwCount, row[col++]);
	str_to_number(dwPrice, row[col++]);
	str_to_number(dwSold, row[col++]);

	int aiSockets[ITEM_SOCKET_MAX_NUM];
	for (int s = 0; s < ITEM_SOCKET_MAX_NUM; ++s)
	{
		aiSockets[s] = 0;
		str_to_number(aiSockets[s], row[col++]);
	}

	TPlayerItemAttribute aAttrs[ITEM_ATTRIBUTE_MAX_NUM];
	for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
	{
		DWORD dwAttrType = 0;
		int iAttrValue = 0;
		str_to_number(dwAttrType, row[col++]);
		str_to_number(iAttrValue, row[col++]);
		aAttrs[a].bType = (BYTE) dwAttrType;
		aAttrs[a].sValue = (short) iAttrValue;
	}

	const bool bShopRowAlive = (row[col] != NULL);	// LEFT JOIN: dukkan basligi silinmisse NULL

	// 2) DOGRULAMALAR (hicbir sey dusulmeden)
	if (dwRowOwner != dwOwnerPID || !bShopRowAlive)
	{
		SendPopup(ch, "IKASHOP_SHOP_NOT_FOUND");
		SendResultDelete(ch, dwItemDBID);
		return;
	}

	if (dwRowOwner == dwPID)	// DUPE-3 (DB dogrulamasi)
	{
		SendPopup(ch, "IKASHOP_CANT_BUY_OWN_ITEM");
		return;
	}

	if (dwSold != 0)
	{
		SendPopup(ch, "IKASHOP_ITEM_SOLD");
		SendResultDelete(ch, dwItemDBID);
		return;
	}

	if (dwPrice != dwSeenPrice)	// front-run korumasi (1. kontrol; 2.si claim WHERE'inde)
	{
		SendPopup(ch, "IKASHOP_PRICE_CHANGED");
		SendResultDelete(ch, dwItemDBID);
		return;
	}

	// Fiyat GOLD_MAX ustunde ise reddet: (int) cast negatife donup gold kontrolunu bypass eder
	// ve PointChange isaret tersine (gold uretimi) yapardi. Gecerli pazar fiyati GOLD_MAX'i asamaz.
	if (dwPrice > (DWORD) GOLD_MAX)
	{
		sys_err("IKASEARCH: gecersiz fiyat %u (itemdbid %u, pid %u)", dwPrice, dwItemDBID, dwPID);
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	if (ch->GetGold() < (int) dwPrice)
	{
		SendPopup(ch, "IKASHOP_NOT_ENOUGH_MONEY");
		return;
	}

	// 3) ITEM ON-URETIMI + ENVANTER ON-KONTROLU (claim'den ONCE; basarisizlikta hicbir sey dusmedi)
	LPITEM pkNewItem = ITEM_MANAGER::instance().CreateItem(dwVnum, dwCount);

	if (!pkNewItem)
	{
		sys_err("IKASEARCH: CreateItem basarisiz (vnum %u, pid %u)", dwVnum, dwPID);
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	for (int s = 0; s < ITEM_SOCKET_MAX_NUM; ++s)
		pkNewItem->SetSocket(s, aiSockets[s], false);

	for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
		pkNewItem->SetForceAttribute(a, aAttrs[a].bType, aAttrs[a].sValue);

	// Savunma: Nesne market (EmBound 31337) kisitli item pazara zaten konulamaz; yine de
	// crafted paket / bozuk satira karsi uzak alimda da reddet (yerel BuyOffline paritesinin otesi)
	if (pkNewItem->IsItemShopEmBound())
	{
		M2_DESTROY_ITEM(pkNewItem);
		sys_err("IKASEARCH: EmBound item uzak alim reddi (vnum %u, itemdbid %u, pid %u)", dwVnum, dwItemDBID, dwPID);
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	const int iEmptyPos = ch->GetEmptyInventoryEx(pkNewItem);

	if (iEmptyPos < 0)
	{
		M2_DESTROY_ITEM(pkNewItem);
		SendPopup(ch, "IKASHOP_INVENTORY_FULL");
		return;
	}

	// 4) ATOMIK CLAIM: tek otorite MySQL satir kilidi. Fiyat WHERE'de = ikinci seenprice dogrulamasi.
	auto pkClaim = DBManager::instance().DirectQuery(
		"UPDATE player_shop_items SET sold = 1 WHERE id = %u AND sold = 0 AND price = %u",
		dwItemDBID, dwPrice);

	if (!pkClaim || !pkClaim->Get() || pkClaim->Get()->uiAffectedRows != 1)
	{
		// Yaris kaybedildi (baska alici / fiyat degisti); HICBIR SEY dusulmedi
		M2_DESTROY_ITEM(pkNewItem);
		SendPopup(ch, "IKASHOP_ITEM_SOLD");
		SendResultDelete(ch, dwItemDBID);
		return;
	}

	// 5) CLAIM KAZANILDI: para dus + item teslim + kalicilik
	if (dwPrice > 0)
		ch->PointChange(POINT_GOLD, -static_cast<int>(dwPrice), false);

	pkNewItem->AddToCharacter(ch, TItemPos(pkNewItem->GetWindowInventoryEx(), iEmptyPos));
	ITEM_MANAGER::instance().FlushDelayedSave(pkNewItem);	// KALICILIK: relog'da item kaybolmasin (SafeTrade dersi)
	ch->Save();

	// 6) SATICI GELIRI: player_gift (BuyOffline kalibi) + loglar
	DBManager::instance().DirectQuery("INSERT INTO player_gift SET owner_id = %u, vnum = 1, count = %u", dwOwnerPID, dwPrice);

	char buf[512];
	snprintf(buf, sizeof(buf), "REMOTE %s satici_pid %u fiyat %u adet %u itemdbid %u",
		pkNewItem->GetName(), dwOwnerPID, dwPrice, pkNewItem->GetCount(), dwItemDBID);
	LogManager::instance().ItemLog(ch, pkNewItem, "OFFLINE_SHOP_BUY", buf);
	LogManager::instance().ItemLog(dwOwnerPID, 0, 0, pkNewItem->GetID(), "OFFLINE_SHOP_SELL", buf, "", pkNewItem->GetOriginalVnum());

	sys_log(0, "IKASEARCH: BUY pid %u <- owner %u item %s(x%u) dbid %u fiyat %u",
		dwPID, dwOwnerPID, pkNewItem->GetName(), pkNewItem->GetCount(), dwItemDBID, dwPrice);

	// 7) GORSEL SENKRON: bu core'daki canli tezgah + sahip bildirimi, sonra tum core'lara GG 42
	OnShopItemSold(dwOwnerPID, dwItemDBID);
	BroadcastSoldP2P(dwOwnerPID, dwItemDBID);

	// 8) ALICIYA SONUC
	SendPopup(ch, "IKASHOP_BUY_SUCCESS");
	SendResultDelete(ch, dwItemDBID);
}

// ============================================================================
// Uzak satis bildirimi: canli tezgah bu core'daysa kirmizi ghost + oto-kapanis;
// sahip bu core'da online ise gift yenileme + mesaj (GG 42 handler'i + yerel cagri)
// ============================================================================

void CIkaShopSearchManager::OnShopItemSold(DWORD dwOwnerPID, DWORD dwItemDBID)
{
	LPSHOP pkShop = CShopManager::instance().FindPCShop(dwOwnerPID);

	// m_map_pkShopByPC anahtari offline dukkanlarda PID'dir; online sahis dukkani (VID anahtarli)
	// carpismasina karsi tezgah sahibi dogrulanir
	if (pkShop && pkShop->GetOwner() && pkShop->GetOwner()->IsPrivShop() && pkShop->GetOwner()->GetPrivShopOwner() == dwOwnerPID)
	{
		pkShop->MarkSoldAndBroadcast(dwItemDBID);

#ifdef SHOP_AUTO_CLOSE
		if (pkShop->GetItemCount() <= 0)
			pkShop->GetOwner()->DeleteMyShop();
#endif
	}

	LPCHARACTER pkOwnerCh = CHARACTER_MANAGER::instance().FindByPID(dwOwnerPID);

	if (pkOwnerCh && pkOwnerCh->GetDesc())
	{
		pkOwnerCh->RefreshGift();
		pkOwnerCh->ChatPacket(CHAT_TYPE_INFO, "Pazarindaki bir esya satildi! Gelirini Hediye penceresinden alabilirsin.");
	}
}

// ============================================================================
// VIEW_SHOP: dukkanin DB anlik goruntusu (ViewMyShopRemote'un parametrize kardesi;
// byIsMyShop=2 -> client salt-okunur acar; kanal/harita bagimsiz)
// ============================================================================

void CIkaShopSearchManager::HandleViewShopRequest(LPCHARACTER ch, const TPacketCGIkaShopSearch * p)
{
	const DWORD dwOwnerPID = p->dwOwnerPID;

	if (dwOwnerPID == 0)
		return;

	if (!PulseManager::Instance().IncreaseClock(ch->GetPlayerID(), ePulse::IkaShopView, std::chrono::milliseconds(IKASEARCH_VIEW_COOLDOWN_MS)))
		return;

	// Baska bir pencere acikken acilamaz (ViewMyShopRemote ile ayni guard listesi)
	if (ch->GetExchange() || ch->IsOpenSafebox() || ch->IsCubeOpen() || ch->GetMyShop() || ch->GetShop() || ch->GetShopOwner() || ch->IsEditingShop())
	{
		SendPopup(ch, "IKASHOP_GENERIC_FAIL");
		return;
	}

	// OpenShop/ViewMyShopRemote kolon duzeni; 'sold' EN SONDA (kolon kaymasi tuzagi)
	char szSockets[128];
	char szAttrs[256];
	int socLen = snprintf(szSockets, sizeof(szSockets), "socket0");
	int attrLen = snprintf(szAttrs, sizeof(szAttrs), "attrtype0, attrvalue0");
	for (BYTE i = 1; i < ITEM_SOCKET_MAX_NUM; ++i)
		socLen += snprintf(szSockets + socLen, sizeof(szSockets) - socLen, ", socket%d", i);
	for (BYTE i = 1; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		attrLen += snprintf(szAttrs + attrLen, sizeof(szAttrs) - attrLen, ", attrtype%d, attrvalue%d", i, i);

	auto pkMsg = DBManager::instance().DirectQuery(
		"SELECT vnum, count, display_pos, price, %s, %s, sold FROM player_shop_items WHERE player_id = %u",
		szSockets, szAttrs, dwOwnerPID);

	if (!pkMsg || !pkMsg->Get() || pkMsg->Get()->uiNumRows == 0)
	{
		SendPopup(ch, "IKASHOP_SHOP_NOT_FOUND");
		return;
	}

	TPacketGCShop pack;
	pack.header = HEADER_GC_SHOP;
	pack.subheader = SHOP_SUBHEADER_GC_START;

	TPacketGCShopStart pack2;
	memset(&pack2, 0, sizeof(pack2));
	pack2.owner_vid = 0;	// bu core'da tezgah olmayabilir; salt-okunur modda VID kullanilmaz
	pack2.byIsMyShop = 2;	// 2 = uzaktan salt-goruntuleme

	int iValidRows = 0;
	MYSQL_ROW row = NULL;
	while ((row = mysql_fetch_row(pkMsg->Get()->pSQLResult)) != NULL)
	{
		int col = 0;
		DWORD dwVnum = 0, dwCount = 0, dwDisplayPos = 0, dwPrice = 0;
		str_to_number(dwVnum, row[col++]);
		str_to_number(dwCount, row[col++]);
		str_to_number(dwDisplayPos, row[col++]);
		str_to_number(dwPrice, row[col++]);

		if (dwDisplayPos >= SHOP_HOST_ITEM_MAX_NUM)
		{
			sys_err("IKASEARCH: ViewShop gecersiz display_pos %u (owner %u)", dwDisplayPos, dwOwnerPID);
			continue;
		}

		++iValidRows;
		TShopItemData & r_item = pack2.items[dwDisplayPos];
		r_item.vnum = dwVnum;
		r_item.count = (BYTE) (dwCount > 255 ? 255 : dwCount);
		r_item.price = dwPrice;

		for (int s = 0; s < ITEM_SOCKET_MAX_NUM; ++s)
		{
			long lSocket = 0;
			str_to_number(lSocket, row[col++]);
			r_item.alSockets[s] = lSocket;
		}

		for (int at = 0; at < ITEM_ATTRIBUTE_MAX_NUM; ++at)
		{
			DWORD dwAttrType = 0;
			long lAttrValue = 0;
			str_to_number(dwAttrType, row[col++]);
			str_to_number(lAttrValue, row[col++]);
			r_item.aAttr[at].bType = (BYTE) dwAttrType;
			r_item.aAttr[at].sValue = (short) lAttrValue;
		}

		// 'sold' kolonu (SELECT'te en son): satilmis item kirmizi hayalet
		DWORD dwSold = 0;
		str_to_number(dwSold, row[col++]);
		r_item.bSold = dwSold ? 1 : 0;
	}

	if (iValidRows == 0)
	{
		SendPopup(ch, "IKASHOP_SHOP_NOT_FOUND");
		return;
	}

	pack.size = sizeof(pack) + sizeof(pack2);
	ch->GetDesc()->BufferedPacket(&pack, sizeof(TPacketGCShop));
	ch->GetDesc()->Packet(&pack2, sizeof(TPacketGCShopStart));
}

#endif // ENABLE_IKASHOP_SEARCH
//archive's 6b9a24beef838d9382c750a6b44ccdb4
