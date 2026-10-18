#include "stdafx.h"

#ifdef ENABLE_BOSS_DAMAGE_RANKING

#include "constants.h"	// tables.h tiplerini packet.h'ten ONCE getirir (ffa_event.cpp sirasi)
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "desc.h"
#include "char.h"
#include "char_manager.h"
#include "sectree.h"
#include "event.h"
#include "log.h"
#include "boss_ranking.h"

// ============================================================================
// tick eventi
// ============================================================================

EVENTINFO(TBossRankTickEventInfo)
{
	int iDummy;

	TBossRankTickEventInfo()
	: iDummy(0)
	{
	}
};

EVENTFUNC(boss_rank_tick_event)
{
	if (event == nullptr || event->info == nullptr)
		return 0;

	return CBossRankingManager::instance().Tick();
}

// ============================================================================
// yardimcilar
// ============================================================================

namespace
{
	const DWORD s_adwRankedBossVnums[] = { BOSS_RANKING_VNUMS };

	// (bossVnum, itemVnum, sira) drop kurallari - CommonDefines.h BOSS_RANKING_DROP_RULES
	struct TBossRankDropRule
	{
		DWORD	dwBossVnum;
		DWORD	dwItemVnum;
		BYTE	bRank;		// 1 tabanli (1 = en cok hasar)
	};

	const TBossRankDropRule s_akRankDropRules[] = { BOSS_RANKING_DROP_RULES };

	// boss cevresindeki (gorus mesafesi) desc'li oyunculari toplar
	struct FBossRankCollectViewers
	{
		int m_iX;
		int m_iY;
		int m_iRange;
		std::vector<LPCHARACTER> * m_pvec;

		FBossRankCollectViewers(int iX, int iY, int iRange, std::vector<LPCHARACTER> * pvec)
			: m_iX(iX), m_iY(iY), m_iRange(iRange), m_pvec(pvec)
		{
		}

		void operator()(LPENTITY ent)
		{
			if (!ent->IsType(ENTITY_CHARACTER))
				return;

			LPCHARACTER ch = (LPCHARACTER) ent;

			if (!ch->IsPC() || ch->GetDesc() == nullptr)
				return;

			if (DISTANCE_APPROX(ch->GetX() - m_iX, ch->GetY() - m_iY) > m_iRange)
				return;

			m_pvec->push_back(ch);
		}
	};

	bool BossRankLess(const std::pair<DWORD, const TBossRankEntry *> & a, const std::pair<DWORD, const TBossRankEntry *> & b)
	{
		if (a.second->ullDamage != b.second->ullDamage)
			return a.second->ullDamage > b.second->ullDamage;

		return a.second->stName < b.second->stName;
	}
}

// ============================================================================
// yasam dongusu
// ============================================================================

CBossRankingManager::CBossRankingManager()
	: m_pkTickEvent(nullptr)
{
}

CBossRankingManager & CBossRankingManager::instance()
{
	static CBossRankingManager s_mgr;
	return s_mgr;
}

bool CBossRankingManager::IsRankedBossVnum(DWORD dwVnum)
{
	for (size_t i = 0; i < sizeof(s_adwRankedBossVnums) / sizeof(s_adwRankedBossVnums[0]); ++i)
		if (s_adwRankedBossVnums[i] == dwVnum)
			return true;

	return false;
}

void CBossRankingManager::StartTickEvent()
{
	if (m_pkTickEvent)
		return;

	TBossRankTickEventInfo * info = AllocEventInfo<TBossRankTickEventInfo>();
	m_pkTickEvent = event_create(boss_rank_tick_event, info, PASSES_PER_SEC(BOSS_RANKING_TICK_SECONDS));
}

void CBossRankingManager::OnSpawn(LPCHARACTER pkBoss)
{
	if (!pkBoss || pkBoss->IsPC())
		return;

	if (!IsRankedBossVnum(pkBoss->GetRaceNum()))
		return;

	TBossRankSession & session = m_mapSessions[(DWORD) pkBoss->GetVID()];
	session.dwBossVnum = pkBoss->GetRaceNum();
	session.mapDamage.clear();
	m_mapFinalRanks.erase((DWORD) pkBoss->GetVID());	// VID-yeniden-kullanim sertlestirmesi: bayat stash kalmasin

	StartTickEvent();

	sys_log(0, "BOSS_RANKING: oturum acildi vnum %u vid %u", pkBoss->GetRaceNum(), (DWORD) pkBoss->GetVID());
}

void CBossRankingManager::OnDamage(LPCHARACTER pkBoss, LPCHARACTER pkAttacker, int iDam)
{
	// hizli cikis: aktif boss oturumu yokken her mob hasarinda sifira yakin maliyet
	if (m_mapSessions.empty())
		return;

	if (!pkBoss || !pkAttacker || iDam <= 0 || !pkAttacker->IsPC())
		return;

	std::map<DWORD, TBossRankSession>::iterator it = m_mapSessions.find((DWORD) pkBoss->GetVID());

	if (it == m_mapSessions.end())
		return;

	TBossRankEntry & entry = it->second.mapDamage[pkAttacker->GetPlayerID()];

	if (entry.stName.empty())
		entry.stName = pkAttacker->GetName();

	// polymorph aninda GetRaceNum donusum vnum'unu dondurur (Eski_A bug #9: GetJob
	// fallback'i job dondurur, ikon indeksi degil) - irk yalniz normal halde guncellenir
	if (!pkAttacker->IsPolymorphed())
		entry.iRace = (int) pkAttacker->GetRaceNum();

	entry.bEmpire = pkAttacker->GetEmpire();
	entry.bLevel = (BYTE) pkAttacker->GetLevel();

	entry.ullDamage += (uint64_t) iDam;
}

void CBossRankingManager::OnDead(LPCHARACTER pkBoss)
{
	if (m_mapSessions.empty() || !pkBoss)
		return;

	std::map<DWORD, TBossRankSession>::iterator it = m_mapSessions.find((DWORD) pkBoss->GetVID());

	if (it == m_mapSessions.end())
		return;

	std::vector<std::pair<DWORD, const TBossRankEntry *> > vecRank;
	uint64_t ullTotal = 0;
	BuildSortedRank(it->second, vecRank, ullTotal);

	// Reward() drop kurallari icin olum-ani siralamasini sakla (oturum asagida
	// silinir ama Reward ayni Dead() cagri yigininda SONRA calisir; OnDestroy supurur)
	TBossFinalRank & kFinal = m_mapFinalRanks[(DWORD) pkBoss->GetVID()];
	kFinal.dwBossVnum = it->second.dwBossVnum;
	kFinal.vecTopPIDs.clear();
	kFinal.vecTopNames.clear();

	for (size_t r = 0; r < vecRank.size() && r < BOSS_RANKING_TOP_COUNT; ++r)
	{
		kFinal.vecTopPIDs.push_back(vecRank[r].first);
		kFinal.vecTopNames.push_back(vecRank[r].second->stName);
	}

	std::vector<LPCHARACTER> vecViewers;
	CollectViewers(pkBoss, vecViewers);

	for (size_t i = 0; i < vecViewers.size(); ++i)
	{
		LPCHARACTER ch = vecViewers[i];

		if (ullTotal > 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s hasar siralamasi:", pkBoss->GetName());

			for (size_t r = 0; r < vecRank.size() && r < 3; ++r)
				ch->ChatPacket(CHAT_TYPE_INFO, "%d) %s - %llu (%%%.1f)",
						(int) r + 1, vecRank[r].second->stName.c_str(),
						(unsigned long long) vecRank[r].second->ullDamage,
						100.0 * (double) vecRank[r].second->ullDamage / (double) ullTotal);
		}

		// pencereyi aninda kapat (bayat-gizlemeyi beklemeden)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "boss_rank_end %u", (DWORD) pkBoss->GetVID());
	}

	for (size_t r = 0; r < vecRank.size() && r < BOSS_RANKING_TOP_COUNT; ++r)
		sys_log(0, "BOSS_RANKING_FINAL: vnum %u %d) %s dmg %llu",
				it->second.dwBossVnum, (int) r + 1,
				vecRank[r].second->stName.c_str(), (unsigned long long) vecRank[r].second->ullDamage);

	m_mapSessions.erase(it);
}

void CBossRankingManager::OnDestroy(LPCHARACTER pkBoss)
{
	// DIKKAT: iki map birlikte kontrol edilmeli - normal olumde OnDead oturumu
	// coktan silmis olur; ceset yikiminda m_mapSessions bos diye erken donulurse
	// m_mapFinalRanks stash'i HIC temizlenmez (review bulgusu 2026-09-10, sizinti)
	if ((m_mapSessions.empty() && m_mapFinalRanks.empty()) || !pkBoss || pkBoss->IsPC())
		return;

	// olmeden despawn (purge/dungeon temizligi/harita bosalmasi): kapatma paketi
	// gonderilmez (yikim sirasinda guvenilir degil); client bayat-gizleme kapatir
	m_mapSessions.erase((DWORD) pkBoss->GetVID());
	m_mapFinalRanks.erase((DWORD) pkBoss->GetVID());
}

LPCHARACTER CBossRankingManager::GetRankDropOwner(LPCHARACTER pkBoss, DWORD dwItemVnum)
{
	// hizli cikis: bekleyen olum-ani sirasi yokken her drop'ta sifira yakin maliyet
	if (m_mapFinalRanks.empty() || !pkBoss)
		return nullptr;

	std::map<DWORD, TBossFinalRank>::iterator it = m_mapFinalRanks.find((DWORD) pkBoss->GetVID());

	if (it == m_mapFinalRanks.end())
		return nullptr;

	const TBossFinalRank & kFinal = it->second;

	for (size_t i = 0; i < sizeof(s_akRankDropRules) / sizeof(s_akRankDropRules[0]); ++i)
	{
		const TBossRankDropRule & kRule = s_akRankDropRules[i];

		if (kRule.dwBossVnum != kFinal.dwBossVnum || kRule.dwItemVnum != dwItemVnum)
			continue;

		if (kRule.bRank == 0 || (size_t) kRule.bRank > kFinal.vecTopPIDs.size())
			return nullptr;	// o sira bos (katilimci az) -> stok akis

		const DWORD dwPID = kFinal.vecTopPIDs[kRule.bRank - 1];
		LPCHARACTER pkOwner = CHARACTER_MANAGER::instance().FindByPID(dwPID);

		if (!pkOwner)
		{
			// cevrimdisi/baska core: item stok akisla duser (kaybolmaz, alt siraya
			// GECMEZ - kullanici karari 2026-09-10)
			sys_log(0, "BOSS_RANKING_DROP: boss %u item %u sira %d sahibi %s (pid %u) cevrimdisi - stok akis",
					kFinal.dwBossVnum, dwItemVnum, (int) kRule.bRank,
					kFinal.vecTopNames[kRule.bRank - 1].c_str(), dwPID);
			return nullptr;
		}

		sys_log(0, "BOSS_RANKING_DROP: boss %u item %u -> sira %d %s (pid %u)",
				kFinal.dwBossVnum, dwItemVnum, (int) kRule.bRank, pkOwner->GetName(), dwPID);
		return pkOwner;
	}

	return nullptr;
}

// ============================================================================
// periyodik yayin
// ============================================================================

int CBossRankingManager::Tick()
{
	for (std::map<DWORD, TBossRankSession>::iterator it = m_mapSessions.begin(); it != m_mapSessions.end(); )
	{
		LPCHARACTER pkBoss = CHARACTER_MANAGER::instance().Find(it->first);

		if (!pkBoss || pkBoss->IsDead())
		{
			// guvenlik agi: normal kapanis OnDead/OnDestroy'da islenir
			it = m_mapSessions.erase(it);
			continue;
		}

		if (!it->second.mapDamage.empty())
			BroadcastSession(it->first, it->second, pkBoss);

		++it;
	}

	return PASSES_PER_SEC(BOSS_RANKING_TICK_SECONDS);
}

void CBossRankingManager::CollectViewers(LPCHARACTER pkBoss, std::vector<LPCHARACTER> & vecOut) const
{
	LPSECTREE pSectree = pkBoss->GetSectree();

	if (pSectree == nullptr)
		return;

	// gorus mesafesi: entity_view ile ayni taban (VIEW_RANGE + bonus pay)
	FBossRankCollectViewers f(pkBoss->GetX(), pkBoss->GetY(), VIEW_RANGE + 500, &vecOut);
	pSectree->ForEachAround(f);
}

void CBossRankingManager::BuildSortedRank(const TBossRankSession & session,
		std::vector<std::pair<DWORD, const TBossRankEntry *> > & vecOut, uint64_t & ullTotal) const
{
	vecOut.clear();
	vecOut.reserve(session.mapDamage.size());
	ullTotal = 0;

	for (std::map<DWORD, TBossRankEntry>::const_iterator it = session.mapDamage.begin(); it != session.mapDamage.end(); ++it)
	{
		if (it->second.ullDamage == 0)
			continue;

		vecOut.push_back(std::make_pair(it->first, &it->second));
		ullTotal += it->second.ullDamage;
	}

	std::sort(vecOut.begin(), vecOut.end(), BossRankLess);
}

void CBossRankingManager::BroadcastSession(DWORD dwBossVID, const TBossRankSession & session, LPCHARACTER pkBoss)
{
	std::vector<std::pair<DWORD, const TBossRankEntry *> > vecRank;
	uint64_t ullTotal = 0;
	BuildSortedRank(session, vecRank, ullTotal);

	if (ullTotal == 0)
		return;

	// satirlar: <sira>|<isim>|<hasar>|<yuzde>;... (bosluk YOK - stringCommander kurali)
	std::string stRows;
	char szRow[96];

	for (size_t r = 0; r < vecRank.size() && r < BOSS_RANKING_TOP_COUNT; ++r)
	{
		const double dPct = 100.0 * (double) vecRank[r].second->ullDamage / (double) ullTotal;

		// isim wire'da 11 karaktere kesilir (kullanici karari 2026-09-10, Eski_A 9'da
		// kesiyordu): 10 satir CHAT_MAX_LEN butcesine boyle sigar. PC isimleri saf
		// alnum (check_name_alphabet) - coklu bayt kesme riski yok.
		snprintf(szRow, sizeof(szRow), "%s%d|%.11s|%llu|%.1f|%d|%d|%d",
				stRows.empty() ? "" : ";",
				(int) r + 1, vecRank[r].second->stName.c_str(),
				(unsigned long long) vecRank[r].second->ullDamage, dPct,
				vecRank[r].second->iRace,
				(int) vecRank[r].second->bEmpire,
				(int) vecRank[r].second->bLevel);

		if (stRows.size() + strlen(szRow) > 420)
			break;	// CHAT_MAX_LEN emniyeti - YUK TASIYAN sinir: ChatPacket vsnprintf'in
					// would-be uzunlugunu clamp'siz pakete yazar (char.cpp), toplam komut
					// 512'yi asarsa OOB okuma olur; sabit alanlar en kotu ~57B ->
					// 420 + 57 = 477 <= 512. Bu siniri ~450 uzerine CIKARMA.
					// Gercekci 10 satir (isim<=11, hasar<=10 hane) ~410B - sigar;
					// asiri uc durumda (20 haneli hasarlar) son satir(lar) dusebilir.

		stRows += szRow;
	}

	std::vector<LPCHARACTER> vecViewers;
	CollectViewers(pkBoss, vecViewers);

	for (size_t i = 0; i < vecViewers.size(); ++i)
	{
		LPCHARACTER ch = vecViewers[i];

		// kendi satiri (siralamada yoksa 0|0|0.0)
		int iMyRank = 0;
		unsigned long long ullMyDamage = 0;
		double dMyPct = 0.0;

		for (size_t r = 0; r < vecRank.size(); ++r)
		{
			if (vecRank[r].first == ch->GetPlayerID())
			{
				iMyRank = (int) r + 1;
				ullMyDamage = (unsigned long long) vecRank[r].second->ullDamage;
				dMyPct = 100.0 * (double) vecRank[r].second->ullDamage / (double) ullTotal;
				break;
			}
		}

		ch->ChatPacket(CHAT_TYPE_COMMAND, "boss_rank %u,%u#%s#%d|%llu|%.1f",
				session.dwBossVnum, dwBossVID, stRows.c_str(), iMyRank, ullMyDamage, dMyPct);
	}
}

#endif // ENABLE_BOSS_DAMAGE_RANKING
