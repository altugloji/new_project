#include "stdafx.h"

#ifdef ENABLE_FFA_EVENT

#include "constants.h"
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "desc.h"
#include "desc_manager.h"
#include "buffer_manager.h"
#include "char.h"
#include "char_manager.h"
#include "item.h"
#include "affect.h"
#ifdef USE_PET_SEAL_ON_LOGIN
#include "PetSystem.h"
#endif
#include "party.h"
#include "p2p.h"
#include "db.h"
#include "log.h"
#include "event.h"
#include "questmanager.h"
#include "sectree_manager.h"
#include "start_position.h"
#include "cmd.h"
#include "ffa_event.h"

// ============================================================================
// tick eventi
// ============================================================================

EVENTINFO(TFFATickEventInfo)
{
	int iDummy;

	TFFATickEventInfo()
	: iDummy(0)
	{
	}
};

EVENTFUNC(ffa_tick_event)
{
	if (event == nullptr || event->info == nullptr)
		return 0;

	// Tick() 0 donerse manager kendi pointer'ini zaten temizlemistir (UAF onlemi)
	return CFFAManager::instance().Tick();
}

// ============================================================================
// harita oyunculari uzerinde dolasma yardimcilari
// ============================================================================

namespace
{
	struct FFFACollectPlayers
	{
		std::vector<LPCHARACTER> * m_pvec;

		FFFACollectPlayers(std::vector<LPCHARACTER> * pvec) : m_pvec(pvec) {}

		void operator()(LPENTITY ent)
		{
			if (!ent->IsType(ENTITY_CHARACTER))
				return;

			LPCHARACTER ch = (LPCHARACTER) ent;

			if (!ch->IsPC() || ch->GetDesc() == nullptr)
				return;

			m_pvec->push_back(ch);
		}
	};

	bool FFARankLess(const std::pair<DWORD, const TFFAEntry *> & a, const std::pair<DWORD, const TFFAEntry *> & b)
	{
		if (a.second->iKills != b.second->iKills)
			return a.second->iKills > b.second->iKills;

		if (a.second->iDeaths != b.second->iDeaths)
			return a.second->iDeaths < b.second->iDeaths;

		return a.second->stName < b.second->stName;
	}
}

// ============================================================================
// yasam dongusu
// ============================================================================

CFFAManager::CFFAManager()
	: m_tEndTime(0)
	, m_tFightStart(0)
	, m_bFightAnnounced(false)
	, m_tLastBroadcast(0)
	, m_pkTickEvent(nullptr)
{
}

CFFAManager::~CFFAManager()
{
	Destroy();
}

void CFFAManager::Initialize()
{
	// DB/SQL bagimliligi yok; bayrak durumu boot'ta input_db'den SetEventFlag ile
	// gelir ve OnEventFlagChange yukselen kenarda tick'i baslatir (crash-recovery:
	// bayrak acik kalmissa etkinlik taze sureyle yeniden baslar - bilincli karar).
	if (HasMap())
		sys_log(0, "FFA: manager hazir (map %d bu core'da)", FFA_EVENT_MAP_INDEX);
}

void CFFAManager::Destroy()
{
	StopTick();
}

bool CFFAManager::HasMap() const
{
	return SECTREE_MANAGER::instance().GetMap(FFA_EVENT_MAP_INDEX) != nullptr;
}

bool CFFAManager::IsOpen() const
{
	return quest::CQuestManager::instance().GetEventFlag("ffa_open") != 0;
}

void CFFAManager::StartTick()
{
	if (m_pkTickEvent)
		return;

	TFFATickEventInfo * info = AllocEventInfo<TFFATickEventInfo>();
	m_pkTickEvent = event_create(ffa_tick_event, info, PASSES_PER_SEC(FFA_TICK_SECONDS));
}

void CFFAManager::StopTick()
{
	if (m_pkTickEvent)
		event_cancel(&m_pkTickEvent);
}

int CFFAManager::Tick()
{
	if (!HasMap() || !IsOpen())
	{
		// kapanis normalde OnEventFlagChange'de islenir; bu dal guvenlik agi
		m_pkTickEvent = nullptr;
		return 0;
	}

	const time_t tNow = get_global_time();

	if (m_tFightStart != 0 && tNow < m_tFightStart)
	{
		// isinma evresi: haritadakilere ekran-ortasi sayac komutu (client kendi sayar,
		// bu yayin ara senkron); savas suresi geri sayimi henuz baslamadi
		char szCmd[64];
		snprintf(szCmd, sizeof(szCmd), "ffa_warmup %d", (int) (m_tFightStart - tNow));
		BroadcastCommandToMap(szCmd);
	}
	else if (!m_bFightAnnounced)
	{
		// isinma bitti: savasi baslat (tek kez)
		m_bFightAnnounced = true;
		BroadcastCommandToMap("ffa_start");
		SendNoticeMap("Kaos Savasi BASLADI! Herkes dusman, kimseye guvenme!", FFA_EVENT_MAP_INDEX, true);
		sys_log(0, "FFA: savas basladi (map %d)", FFA_EVENT_MAP_INDEX);
	}

	if (m_tEndTime != 0 && tNow >= m_tEndTime)
	{
		// sure doldu: bayragi cluster genelinde dusur; dusus OnEventFlagChange ->
		// FinishEvent zincirini tetikler. Birden fazla kanal core'u ayni anda
		// istese de sonuc ayni (0'a set idempotent).
		m_tEndTime = 0;
		quest::CQuestManager::instance().RequestSetEventFlag("ffa_open", 0);
	}
	else
		BroadcastScoreboard(false);

	return PASSES_PER_SEC(FFA_TICK_SECONDS);
}

void CFFAManager::OnEventFlagChange(int iPrev, int iNow)
{
	if (!HasMap())
		return;

	if (iPrev == 0 && iNow != 0)
	{
		ResetScores();

		int iMinutes = quest::CQuestManager::instance().GetEventFlag("ffa_minutes");

		if (iMinutes <= 0)
			iMinutes = FFA_DEFAULT_MINUTES;

		iMinutes = MINMAX(1, iMinutes, 180);
		// isinma evresi: giris serbest, saldiri kapali; savas suresi isinmadan SONRA baslar
		m_tFightStart = get_global_time() + FFA_WARMUP_SECONDS;
		m_tEndTime = m_tFightStart + (time_t) iMinutes * 60;
		m_bFightAnnounced = false;
		m_tLastBroadcast = 0;
		StartTick();
		sys_log(0, "FFA: etkinlik acildi, isinma %d sn + savas %d dk (map %d)", FFA_WARMUP_SECONDS, iMinutes, FFA_EVENT_MAP_INDEX);

		// cluster-geneli buyuk duyuru; 6 kanal core'u da bu kenari gorur, tek kanal duyursun
		if (g_bChannel == 1)
		{
			char szNotice[192];
			snprintf(szNotice, sizeof(szNotice),
					"Kaos Savasi basliyor! Sehirdeki Savas Sorumlusundan katilabilirsiniz. Savas %d saniye sonra baslar!",
					FFA_WARMUP_SECONDS);
			BroadcastNotice(szNotice, true);
		}
	}
	else if (iPrev != 0 && iNow == 0)
	{
		sys_log(0, "FFA: etkinlik kapatildi (map %d)", FFA_EVENT_MAP_INDEX);
		FinishEvent();
	}
}

void CFFAManager::ResetScores()
{
	m_mapScore.clear();
}

// ============================================================================
// saldiri / maske / etkilesim kapilari
// ============================================================================

int CFFAManager::CheckAttack(LPCHARACTER ch, LPCHARACTER victim) const
{
	if (!ch || !victim || !ch->IsPC() || !victim->IsPC())
		return 0;

	if (!IsFFAMap(ch->GetMapIndex()) || !IsFFAMap(victim->GetMapIndex()))
		return 0;

	if (ch->IsObserverMode() || victim->IsObserverMode())
		return -1;

	// GM her seyi vurabilir (test/mudahale); GM'e vurulamaz
	if (ch->GetGMLevel() > GM_PLAYER)
		return 1;

	if (victim->GetGMLevel() > GM_PLAYER)
		return -1;

	// isinma evresi: savas baslayana kadar PC-PC saldiri iki yonlu kapali
	if (m_tFightStart != 0 && get_global_time() < m_tFightStart)
		return -1;

	// dogus korumasi cift yonlu: korumali olan ne vurabilir ne vurulamaz
	// (server-side; client gorunmezligi tek basina alan hasarini kesmiyor)
	if (ch->IsAffectFlag(AFF_REVIVE_INVISIBLE) || victim->IsAffectFlag(AFF_REVIVE_INVISIBLE))
		return -1;

	return 1;
}

bool CFFAManager::ShouldMask(const CHARACTER * pkTarget, LPENTITY pkViewer) const
{
	if (!pkTarget || !pkViewer)
		return false;

	if (!pkTarget->IsPC() || !IsFFAMap(pkTarget->GetMapIndex()))
		return false;

	// GM karakterleri maskelenmez (oyuncular iceride GM'i GM olarak gorur)
	if (pkTarget->GetGMLevel() > GM_PLAYER)
		return false;

	if (!pkViewer->IsType(ENTITY_CHARACTER))
		return false;

	const CHARACTER * pkChViewer = (const CHARACTER *) pkViewer;

	if (pkChViewer == pkTarget)
		return false;	// kendine gercek kimlik

	if (!pkChViewer->IsPC() || pkChViewer->GetGMLevel() > GM_PLAYER)
		return false;	// GM izleyici gercek kimlik gorur

	return true;
}

DWORD CFFAManager::GetUniformArmorPart(LPCHARACTER ch) const
{
	if (!ch)
		return 0;

	switch (ch->GetJob())
	{
		case JOB_WARRIOR:	return FFA_UNIFORM_ARMOR_WARRIOR;
		case JOB_ASSASSIN:	return FFA_UNIFORM_ARMOR_ASSASSIN;
		case JOB_SURA:		return FFA_UNIFORM_ARMOR_SURA;
		case JOB_SHAMAN:	return FFA_UNIFORM_ARMOR_SHAMAN;
	}

	return 0;	// bilinmeyen sinif (orn. lycan): varsayilan govde
}

DWORD CFFAManager::GetUniformWeaponPart(LPCHARACTER ch) const
{
	if (!ch)
		return 0;

	LPITEM pkWeapon = ch->GetWear(WEAR_WEAPON);

	if (pkWeapon == nullptr || pkWeapon->GetType() != ITEM_WEAPON)
		return 0;	// silahsiz: yumruk gorunumu

	switch (pkWeapon->GetSubType())
	{
		case WEAPON_SWORD:		return FFA_UNIFORM_WEAPON_SWORD;
		case WEAPON_DAGGER:		return FFA_UNIFORM_WEAPON_DAGGER;
		case WEAPON_BOW:		return FFA_UNIFORM_WEAPON_BOW;
		case WEAPON_TWO_HANDED:	return FFA_UNIFORM_WEAPON_TWOHAND;
		case WEAPON_BELL:		return FFA_UNIFORM_WEAPON_BELL;
		case WEAPON_FAN:		return FFA_UNIFORM_WEAPON_FAN;
	}

	return 0;	// pence/mizrak vb. esleme disi turler: yumruk gorunumu
}

bool CFFAManager::BlocksInteraction(LPCHARACTER a, LPCHARACTER b)
{
	if (!a || !b || !a->IsPC() || !b->IsPC())
		return false;

	if (!IsFFAMap(a->GetMapIndex()) && !IsFFAMap(b->GetMapIndex()))
		return false;

	a->ChatPacket(CHAT_TYPE_INFO, "Savas alaninda bu islem kullanilamaz.");
	return true;
}

// ============================================================================
// giris / olum / dogus akislari
// ============================================================================

bool CFFAManager::OnPlayerEnterMap(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !IsFFAMap(ch->GetMapIndex()))
		return false;

	if (!IsOpen())
		return ch->GetGMLevel() > GM_PLAYER;	// kapaliyken sadece GM kalabilir

	// aktif donusum kaldirilir: polymorph gorunumu (dwRaceNum) uniforma maskesini deler
	if (ch->IsPolymorphed())
	{
		ch->RemoveAffect(AFFECT_POLYMORPH);
		ch->SetPolymorph(0);
	}

	// binekten indir (at + kostum/EX binek) ve at/pet NPC'lerini geri cagir
	// (at/pet isimleri sahibinin gercek adini tasir - kimlik sizintisi; review bulgusu)
	if (ch->IsHorseRiding())
		ch->StopRiding();

	if (ch->GetMountVnum())
	{
		// kostum/EX binek: EnterMount her giriste yeniden bindirir, burada sokulur
		ch->RemoveAffect(AFFECT_MOUNT_BONUS);
		ch->MountVnum(0);
	}

	ch->HorseSummon(false);

#ifdef USE_PET_SEAL_ON_LOGIN
	if (ch->GetPetSystem())
		ch->GetPetSystem()->UnsummonAll();
#endif

	if (ch->GetGMLevel() == GM_PLAYER)
	{
		// partiyi dagit (arena/duellist girisiyle ayni desen)
		LPPARTY pParty = ch->GetParty();

		if (pParty != nullptr)
		{
			if (pParty->GetMemberCount() == 2)
				CPartyManager::instance().DeleteParty(pParty);
			else
				pParty->Quit(ch->GetPlayerID());
		}

		// katilimci kaydi (0 kill ile listede gorunsun); karsilama sadece ilk giriste
		const bool bNewEntry = m_mapScore.find(ch->GetPlayerID()) == m_mapScore.end();
		TFFAEntry & rkEntry = m_mapScore[ch->GetPlayerID()];
		rkEntry.stName = ch->GetName();
		rkEntry.iRace = (int) ch->GetRaceNum();

		if (bNewEntry)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Kaos Savasina hos geldin! Herkes dusman, kimseye guvenme.");

			if (m_tEndTime != 0)
			{
				// isinma dahil edilmez: savas penceresinin kendi suresi gosterilir
				const time_t tRef = MAX(get_global_time(), m_tFightStart);
				ch->ChatPacket(CHAT_TYPE_INFO, "Savas suresi: %d dakika.", (int) MAX(0, (m_tEndTime - tRef) / 60));
			}
		}

		// spawn cevresi disinda beliren oyuncu spawn'a alinir: olu-relog olum noktasinda
		// dirilmeyi ve haritada saklanip relog etmeyi kapatir (review bulgusu).
		// Kendi warp'imiz spawn +-600'e indigi icin dongusuz sonlanir.
		if (DISTANCE_APPROX(ch->GetX() - FFA_SPAWN_X, ch->GetY() - FFA_SPAWN_Y) > FFA_SPAWN_SPREAD * 5)
		{
			WarpToSpawn(ch);
			return true;
		}
	}

	SendScoreboard(ch);

	// isinma evresindeyse ekran-ortasi sayaci hemen gonder (tick beklemeden)
	if (m_tFightStart != 0 && get_global_time() < m_tFightStart)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "ffa_warmup %d", (int) (m_tFightStart - get_global_time()));

	return true;
}

void CFFAManager::OnKill(LPCHARACTER pkKiller, LPCHARACTER pkVictim)
{
	if (!pkKiller || !pkVictim || !pkKiller->IsPC() || !pkVictim->IsPC())
		return;

	// kurbanin olumu, kurban haritadaysa HER durumda sayilir (katil sehre donmus/
	// cikmis olsa bile - zehir/DoT olumleri; review bulgusu). GM olumleri sayilmaz.
	if (!IsFFAMap(pkVictim->GetMapIndex()) || !IsOpen() || pkVictim->GetGMLevel() > GM_PLAYER)
		return;

	TFFAEntry & rkVictim = m_mapScore[pkVictim->GetPlayerID()];
	rkVictim.stName = pkVictim->GetName();
	rkVictim.iRace = (int) pkVictim->GetRaceNum();
	++rkVictim.iDeaths;

	// kill kredisi yalniz katil de haritadayken ve GM degilken islenir
	if (!IsFFAMap(pkKiller->GetMapIndex()) || pkKiller->GetGMLevel() > GM_PLAYER)
	{
		BroadcastScoreboard(false);
		return;
	}

	TFFAEntry & rkKiller = m_mapScore[pkKiller->GetPlayerID()];
	rkKiller.stName = pkKiller->GetName();
	rkKiller.iRace = (int) pkKiller->GetRaceNum();

	// ayni-kurban cooldown'u kullanici istegiyle KALDIRILDI: her kill sayilir
	++rkKiller.iKills;

	pkKiller->ChatPacket(CHAT_TYPE_INFO, "Kill! Toplam: %d", rkKiller.iKills);
	sys_log(0, "FFA_KILL: %s -> %s (kill %d)", pkKiller->GetName(), pkVictim->GetName(), rkKiller.iKills);

	BroadcastScoreboard(false);
}

void CFFAManager::WarpToSpawn(LPCHARACTER ch)
{
	const long x = FFA_SPAWN_X + number(-FFA_SPAWN_SPREAD, FFA_SPAWN_SPREAD);
	const long y = FFA_SPAWN_Y + number(-FFA_SPAWN_SPREAD, FFA_SPAWN_SPREAD);

	PIXEL_POSITION pos;

	if (SECTREE_MANAGER::instance().GetMovablePosition(FFA_EVENT_MAP_INDEX, x, y, pos))
		ch->WarpSet(pos.x, pos.y);
	else
		ch->WarpSet(FFA_SPAWN_X, FFA_SPAWN_Y);
}

bool CFFAManager::OnDeadRespawn(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || ch->GetDesc() == nullptr)
		return false;

	if (!IsFFAMap(ch->GetMapIndex()))
		return false;

	// dead_event akisinin kanitli-guvenli sirasi: PHASE_GAME -> POS_STANDING -> WarpSet
	ch->GetDesc()->SetPhase(PHASE_GAME);
	ch->SetPosition(POS_STANDING);

	if (IsOpen())
	{
		WarpToSpawn(ch);
		ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
		ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
		ch->ReviveInvisible(5);
	}
	else
	{
		// etkinlik kapanmis: olu yakalanan oyuncu sehre gonderilir
		ch->WarpSet(EMPIRE_START_X(ch->GetEmpire()), EMPIRE_START_Y(ch->GetEmpire()));
		ch->PointChange(POINT_HP, (ch->GetMaxHP() / 2) - ch->GetHP(), true);
	}

	ch->StartRecoveryEvent();
	return true;
}

bool CFFAManager::OnRestart(LPCHARACTER ch, bool bTown)
{
	if (!ch || !IsFFAMap(ch->GetMapIndex()))
		return false;

	if (bTown || !IsOpen())
	{
		// sehre don = etkinlikten cikis (skorlar durur, geri gelirse devam eder)
		ch->WarpSet(EMPIRE_START_X(ch->GetEmpire()), EMPIRE_START_Y(ch->GetEmpire()));
		ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
		ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
	}
	else
	{
		// buradan devam = spawn noktasi (olum yerinde dirilme yok; camp/istismar onlemi)
		WarpToSpawn(ch);
		ch->PointChange(POINT_HP, ch->GetMaxHP() - ch->GetHP());
		ch->PointChange(POINT_SP, ch->GetMaxSP() - ch->GetSP());
		ch->ReviveInvisible(5);
	}

	return true;
}

// ============================================================================
// kapanis + supurme
// ============================================================================

void CFFAManager::CollectMapPlayers(std::vector<LPCHARACTER> & vecOut) const
{
	LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(FFA_EVENT_MAP_INDEX);

	if (pMap == nullptr)
		return;

	FFFACollectPlayers f(&vecOut);
	pMap->for_each(f);
}

void CFFAManager::BroadcastCommandToMap(const char * c_pszCommand)
{
	std::vector<LPCHARACTER> vecPlayers;
	CollectMapPlayers(vecPlayers);

	for (size_t i = 0; i < vecPlayers.size(); ++i)
		vecPlayers[i]->ChatPacket(CHAT_TYPE_COMMAND, "%s", c_pszCommand);
}

void CFFAManager::FinishEvent()
{
	StopTick();
	m_tEndTime = 0;
	m_tFightStart = 0;
	m_bFightAnnounced = false;

	if (!HasMap())
		return;

	// final siralamasi
	std::vector<std::pair<DWORD, const TFFAEntry *> > vecRank;
	BuildSortedRank(vecRank);

	// haritadakilere duyuru + supurme (kopya-listede dolas: WarpSet sectree'yi degistirir)
	std::vector<LPCHARACTER> vecPlayers;
	CollectMapPlayers(vecPlayers);

	for (size_t i = 0; i < vecPlayers.size(); ++i)
	{
		LPCHARACTER ch = vecPlayers[i];

		ch->ChatPacket(CHAT_TYPE_INFO, "Kaos Savasi sona erdi!");

		for (size_t r = 0; r < vecRank.size() && r < 3; ++r)
			ch->ChatPacket(CHAT_TYPE_INFO, "%d) %s - %d kill / %d olum",
					(int) r + 1, vecRank[r].second->stName.c_str(), vecRank[r].second->iKills, vecRank[r].second->iDeaths);
	}

	for (size_t r = 0; r < vecRank.size() && r < FFA_RANK_TOP_COUNT; ++r)
		sys_log(0, "FFA_FINAL: %d) %s kills %d deaths %d",
				(int) r + 1, vecRank[r].second->stName.c_str(), vecRank[r].second->iKills, vecRank[r].second->iDeaths);

	for (size_t i = 0; i < vecPlayers.size(); ++i)
	{
		LPCHARACTER ch = vecPlayers[i];

		// olu oyuncular OnDeadRespawn kapali-dalindan sehre gider; GM'ler haritada kalir
		if (ch->IsDead() || ch->GetGMLevel() > GM_PLAYER)
			continue;

		ch->WarpSet(EMPIRE_START_X(ch->GetEmpire()), EMPIRE_START_Y(ch->GetEmpire()));
	}
}

// ============================================================================
// skor tablosu
// ============================================================================

void CFFAManager::BuildSortedRank(std::vector<std::pair<DWORD, const TFFAEntry *> > & vecOut) const
{
	vecOut.clear();
	vecOut.reserve(m_mapScore.size());

	for (std::map<DWORD, TFFAEntry>::const_iterator it = m_mapScore.begin(); it != m_mapScore.end(); ++it)
		vecOut.push_back(std::make_pair(it->first, &it->second));

	std::sort(vecOut.begin(), vecOut.end(), FFARankLess);
}

void CFFAManager::SendScoreboard(LPCHARACTER ch)
{
	if (!ch || ch->GetDesc() == nullptr)
		return;

	std::vector<std::pair<DWORD, const TFFAEntry *> > vecRank;
	BuildSortedRank(vecRank);

	// satirlar: <sira>|<isim>|<kill>|<olum>|<irk>;...
	std::string stRows;
	char szRow[96];

	for (size_t r = 0; r < vecRank.size() && r < FFA_RANK_TOP_COUNT; ++r)
	{
		snprintf(szRow, sizeof(szRow), "%s%d|%s|%d|%d|%d",
				stRows.empty() ? "" : ";",
				(int) r + 1, vecRank[r].second->stName.c_str(), vecRank[r].second->iKills, vecRank[r].second->iDeaths,
				vecRank[r].second->iRace);

		if (stRows.size() + strlen(szRow) > 380)
			break;	// CHAT_MAX_LEN emniyeti

		stRows += szRow;
	}

	// kendi satiri
	int iMyRank = 0, iMyKills = 0, iMyDeaths = 0;

	for (size_t r = 0; r < vecRank.size(); ++r)
	{
		if (vecRank[r].first == ch->GetPlayerID())
		{
			iMyRank = (int) r + 1;
			iMyKills = vecRank[r].second->iKills;
			iMyDeaths = vecRank[r].second->iDeaths;
			break;
		}
	}

	// isinma sirasinda savas suresi henuz akmiyor: gosterilen kalan sure isinmayi ICERMEZ
	const time_t tRef = MAX(get_global_time(), m_tFightStart);
	const int iRemain = (m_tEndTime != 0) ? (int) MAX(0, m_tEndTime - tRef) : 0;

	ch->ChatPacket(CHAT_TYPE_COMMAND, "ffa_rank %d#%s#%d|%d|%d", iRemain, stRows.c_str(), iMyRank, iMyKills, iMyDeaths);
}

void CFFAManager::BroadcastScoreboard(bool bForce)
{
	if (!HasMap())
		return;

	const time_t tNow = get_global_time();

	if (!bForce && m_tLastBroadcast != 0 && tNow - m_tLastBroadcast < FFA_BROADCAST_MIN_INTERVAL)
		return;

	m_tLastBroadcast = tNow;

	std::vector<LPCHARACTER> vecPlayers;
	CollectMapPlayers(vecPlayers);

	for (size_t i = 0; i < vecPlayers.size(); ++i)
		SendScoreboard(vecPlayers[i]);
}

// ============================================================================
// GM komutu
// ============================================================================

void CFFAManager::ShowStatus(LPCHARACTER ch)
{
	if (!ch)
		return;

	if (!HasMap())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "FFA: bu cekirdek map %d'i host etmiyor (dogru core'a baglanin).", FFA_EVENT_MAP_INDEX);
		return;
	}

	if (IsOpen())
	{
		const int iRemain = (m_tEndTime != 0) ? (int) MAX(0, m_tEndTime - get_global_time()) : 0;
		ch->ChatPacket(CHAT_TYPE_INFO, "FFA: ACIK - kalan sure %d dk %d sn, katilimci %d.",
				iRemain / 60, iRemain % 60, (int) m_mapScore.size());
	}
	else
		ch->ChatPacket(CHAT_TYPE_INFO, "FFA: KAPALI (acmak icin /e ffa_open 1). Son skorlar:");

	std::vector<std::pair<DWORD, const TFFAEntry *> > vecRank;
	BuildSortedRank(vecRank);

	for (size_t r = 0; r < vecRank.size() && r < FFA_RANK_TOP_COUNT; ++r)
		ch->ChatPacket(CHAT_TYPE_INFO, "%d) %s - %d kill / %d olum",
				(int) r + 1, vecRank[r].second->stName.c_str(), vecRank[r].second->iKills, vecRank[r].second->iDeaths);
}

ACMD(do_ffa)
{
	CFFAManager::instance().ShowStatus(ch);
}

#endif // ENABLE_FFA_EVENT
