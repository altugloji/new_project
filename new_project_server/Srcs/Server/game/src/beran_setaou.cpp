#include "stdafx.h"

#ifdef BERAN_SETAOU
#include "beran_setaou.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "char_manager.h"
#include "buffer_manager.h"
#include "char.h"
#include "config.h"
#include "p2p.h"
#include "db.h"
#include "guild_manager.h"
#include "guild.h"
#include "regen.h"
#include "utils.h"
#include "log.h"
#include <algorithm>
#include <cstring>

#define BRN_CD_QF "beran_setaou.join_time"

#define CODING_PHASE
#ifdef CODING_PHASE
void BS_SendDebugMessageToDeveloper(uint8_t type, const char* format, ...)
{
	LPCHARACTER adminCh = CHARACTER_MANAGER::Instance().FindByPID(1);	//developer pid
	if (!adminCh) { return; }
	LPDESC d = adminCh->GetDesc();

	if (!d || !format) { return; }

	char chatbuf[CHAT_MAX_LEN + 1];
	va_list args;

	va_start(args, format);
	int len = vsnprintf(chatbuf, sizeof(chatbuf), format, args);
	va_end(args);

	struct packet_chat pack_chat;

	pack_chat.header = HEADER_GC_CHAT;
	pack_chat.size = sizeof(struct packet_chat) + len;
	pack_chat.type = type;
	pack_chat.id = 0;
	pack_chat.bEmpire = d->GetEmpire();

	TEMP_BUFFER buf;
	buf.write(&pack_chat, sizeof(struct packet_chat));
	buf.write(chatbuf, len);

	d->Packet(buf.read_peek(), buf.size());
}
#endif

EVENTINFO(bs_destroy_event_info) {
	CBeranSetaou* myClass;
	uint8_t  updateInterval;
	uint32_t elapsedTime;
	bs_destroy_event_info() : myClass(nullptr), updateInterval(0), elapsedTime(0) {}
};
EVENTFUNC(bs_destroy_event) {
	bs_destroy_event_info* info = dynamic_cast<bs_destroy_event_info*>(event->info);
	if (info == nullptr) { return 0; }
	if (info->myClass == nullptr) { return 0; }

	info->elapsedTime += info->updateInterval;

#ifdef CODING_PHASE
	BS_SendDebugMessageToDeveloper(1, "bs_destroy_event > Timer tick start, info->elapsedTime: %d, cntPlayer: %d", info->elapsedTime, info->myClass->GetCountPlayerInMap());
#endif
	if (info->myClass->GetCountPlayerInMap() > 0) {
		info->myClass->StartDestroyEvent(true);
#ifdef CODING_PHASE
		BS_SendDebugMessageToDeveloper(1, "StartDestroyEvent(true)");
#endif
		return 0;
	}

	if (info->elapsedTime >= BS_DESTROY_TIME_WHEN_NO_PLAYER) {
		if (info->myClass->GetRoomState() == BS_STATE_BUSY) {
			info->myClass->EndDungeon(false);
			info->myClass->ClearRoom(true);
#ifdef CODING_PHASE
			BS_SendDebugMessageToDeveloper(1, "bs_destroy_event > Timer tick info->myClass->GetRoomState() == BS_STATE_BUSY");
#endif
			return 0;
		}
	}

	return PASSES_PER_SEC(info->updateInterval);
}


EVENTINFO(bs_update_event_info) {
	uint8_t  updateInterval;
	uint32_t elapsedTime;
	uint8_t  passCount;
	CBeranSetaou* myClass;
	uint8_t  noticeIdx;	// kalan sure uyarisinda hangi esige kadar duyuru yapildi
	bs_update_event_info() : updateInterval(0), elapsedTime(0), passCount(0), myClass(nullptr), noticeIdx(0) {}
};
EVENTFUNC(bs_update_event) {
	bs_update_event_info* info = dynamic_cast<bs_update_event_info*>(event->info);
	if (info == nullptr) { return 0; }
	if (info->myClass == nullptr) { return 0; }

	info->elapsedTime += info->updateInterval;

#ifdef CODING_PHASE
	BS_SendDebugMessageToDeveloper(1, "bs_update_event > Timer tick elapsedTime: %d, info->passCount: %d, GetCountPlayerInMap: %d(%s)",
		info->elapsedTime, info->passCount, info->myClass->GetCountPlayerInMap(),
		(info->myClass->IsDestroyEventActivated() ? "true" : "false"));
#endif

	if (info->myClass->GetRoomState() == BS_STATE_EMPTY)
		return 0;

	if (info->myClass->GetRoomState() == BS_STATE_BUSY) {
		if (info->myClass->GetRemainTime() <= 0) {
			info->myClass->EndDungeon(false);
			info->myClass->BSNotice(BS_NOTICE_DRAGON_STILL_LIVING);
			return PASSES_PER_SEC(info->updateInterval);
		}

	// --- kalan sure uyarisi: esikler gecildikce odadaki oyunculara bir kez bildir ---
	static const int s_bsRemainNotice[] = { 5 * 60, 3 * 60, 60, 30 }; // saniye
	static const int s_bsRemainNoticeCount = sizeof(s_bsRemainNotice) / sizeof(s_bsRemainNotice[0]);
	const int64_t remainSec = info->myClass->GetRemainTime();
	while (info->noticeIdx < s_bsRemainNoticeCount && remainSec <= s_bsRemainNotice[info->noticeIdx])
	{
		const int th = s_bsRemainNotice[info->noticeIdx];
		char szRemain[256];
		if (th >= 60)
			snprintf(szRemain, sizeof(szRemain), "Mavi Ejderha'yi oldurmek icin %d dakikaniz kaldi!", th / 60);
		else
			snprintf(szRemain, sizeof(szRemain), "Mavi Ejderha'yi oldurmek icin %d saniyeniz kaldi!", th);
			SendNoticeMap(szRemain, CRYSTAL_ROOM_MAP_IDX, true);
			info->noticeIdx++;
	}

#ifdef CODING_PHASE
		if (info->myClass->GetCountPlayerInMap() == 0 && !info->myClass->IsDestroyEventActivated()) {
			BS_SendDebugMessageToDeveloper(1, "info->myClass->GetCountPlayerInMap() == 0");
			info->myClass->StartDestroyEvent();
		}
#endif
	}

	if (info->myClass->GetRoomState() == BS_STATE_FINISHED) {
		if (info->passCount >= BS_CLEAR_DELAY_AFTER_FINISH) {
			info->myClass->ClearRoom(true);
			return 0;
		}
		info->passCount += info->updateInterval;
		return PASSES_PER_SEC(info->updateInterval);
	}

	return PASSES_PER_SEC(info->updateInterval);
}

struct FCountPC
{
	uint8_t chCount = 0;
	void operator()(LPENTITY ent)
	{
		if (ent->IsType(ENTITY_CHARACTER)) {
			LPCHARACTER ch = static_cast<LPCHARACTER>(ent);
			if (ch->IsPC() && ch->GetDesc())
				chCount++;
		}
	}
};
struct FBSPurgeMonsters
{
	void operator()(LPENTITY ent)
	{
		if (!ent->IsType(ENTITY_CHARACTER)) { return; }

		LPCHARACTER lpChar = static_cast<LPCHARACTER>(ent);
		if ((lpChar->IsMonster() || lpChar->IsStone())
			&& !lpChar->IsPet()
			&& lpChar->GetMobTable().dwVnum != BERAN_SETAOU_VNUM)
		{
			sys_log(0, "FBSPurgeMonsters: destroying: %d", lpChar->GetRaceNum());
			lpChar->Dead(nullptr, true);
		}
	}
};

CBeranSetaou::CBeranSetaou()
{
	Initialize();
}

CBeranSetaou::~CBeranSetaou()
{
	Destroy();
}

void CBeranSetaou::Initialize()
{
	if (m_updateTimer)  { event_cancel(&m_updateTimer); }
	if (m_destroyTimer) { event_cancel(&m_destroyTimer); }

	m_updateTimer  = nullptr;
	m_destroyTimer = nullptr;
	m_crystalRoom  = nullptr;
	vec_Players.clear();

	m_bsVID = 0;

	m_roomState   = BS_STATE_EMPTY;
	m_dwPasswd    = 0;
	m_dwMasterPID = 0;
	m_dwStartTime = 0;

	m_crystalRoom = SECTREE_MANAGER::instance().GetMap(CRYSTAL_ROOM_MAP_IDX);
	if (!m_crystalRoom) {
		sys_err("CBeranSetaou::Initialize > map could not found %d", CRYSTAL_ROOM_MAP_IDX);
		return;
	}
}

void CBeranSetaou::Destroy()
{
	if (m_updateTimer)  { event_cancel(&m_updateTimer); }
	if (m_destroyTimer) { event_cancel(&m_destroyTimer); }

	m_updateTimer  = nullptr;
	m_destroyTimer = nullptr;
	m_crystalRoom  = nullptr;
	vec_Players.clear();

	m_bsVID = 0;

	m_roomState   = BS_STATE_EMPTY;
	m_dwPasswd    = 0;
	m_dwMasterPID = 0;
	m_dwStartTime = 0;
}

void CBeranSetaou::StartDungeon(LPCHARACTER masterCh, uint32_t roomPasswd, bool isWithParty)
{
	if (GetRoomState() != BS_STATE_EMPTY) { return; }
	if (!masterCh)                        { return; }
	if (!masterCh->GetDesc())             { return; }
	if (!m_crystalRoom) {
		sys_err("CBeranSetaou::StartDungeon > no m_crystalRoom !!!");
		return;
	}

	LPCHARACTER bossCh = CHARACTER_MANAGER::instance().SpawnMob(
		BERAN_SETAOU_VNUM, CRYSTAL_ROOM_MAP_IDX,
		m_crystalRoom->m_setting.iBaseX + STONE_POS_X * 100,
		m_crystalRoom->m_setting.iBaseY + STONE_POS_Y * 100,
		0, false);
	if (!bossCh) { return; }

	m_roomState = BS_STATE_BUSY;
	m_dwMasterPID = masterCh->GetPlayerID();
	vec_Players.push_back(m_dwMasterPID);
	m_dwPasswd = roomPasswd;
	m_bsVID = static_cast<uint32_t>(bossCh->GetVID());
	masterCh->ChatPacket(CHAT_TYPE_NOTICE, "Oda sifresi %d", m_dwPasswd);

	regen_load_in_file(BS_CRYSTAL_ROOM_REGEN_FILE, CRYSTAL_ROOM_MAP_IDX,
		m_crystalRoom->m_setting.iBaseX, m_crystalRoom->m_setting.iBaseY);

	for (uint8_t i = 0; i < MAX_METIN_COUNT; i++) {
		CHARACTER_MANAGER::instance().SpawnMob(
			STONE_VNUM_START + i, CRYSTAL_ROOM_MAP_IDX,
			m_crystalRoom->m_setting.iBaseX + ((STONE_POS_X + number(-STONE_POS_RND_EX, STONE_POS_RND_EX)) * 100),
			m_crystalRoom->m_setting.iBaseY + ((STONE_POS_Y + number(-STONE_POS_RND_EX, STONE_POS_RND_EX)) * 100),
			0, false);
#ifdef CODING_PHASE
		BS_SendDebugMessageToDeveloper(1, "%d spawned.", STONE_VNUM_START + i);
#endif
	}

	m_dwStartTime = get_global_time();
	BSNotice(BS_NOTICE_JOIN);
	StartUpdateEvent();
	masterCh->RemoveSpecifyItem(JOIN_TICKET_VNUM, JOIN_TICKET_COUNT);
	masterCh->SetQuestFlag(BRN_CD_QF, get_global_time() + DUNGEON_COOLDOWN);
	// LogManager::Instance().DungeonHwidLog(masterCh->GetPlayerID(), masterCh->GetAID(), BERAN_SETAOU_DUNGEON_ID, masterCh->GetDesc()->GetHwid());
	// LogManager::Instance().DungeonHwidLog(masterCh->GetPlayerID(), masterCh->GetAID(), BERAN_SETAOU_DUNGEON_ID, masterCh->GetDesc()->GetHostName());
	WarpPlayer(masterCh, true);
}

void CBeranSetaou::EndDungeon(bool isSuccess)
{
	BSNotice(BS_NOTICE_CLEAR_DELAY);
	m_roomState = BS_STATE_FINISHED;
	BSNotice(isSuccess ? BS_NOTICE_DRAGON_KILLED : BS_NOTICE_DRAGON_STILL_LIVING);

	sys_log(0, "EndDungeon, isSuccess: %s", (isSuccess ? "true" : "false"));

	FBSPurgeMonsters f;
	if (LPSECTREE_MAP pSectree = SECTREE_MANAGER::instance().GetMap(CRYSTAL_ROOM_MAP_IDX)) {
		pSectree->for_each(f);
	}

	if (!isSuccess) {
		if (LPCHARACTER chBeran = CHARACTER_MANAGER::Instance().Find(m_bsVID)) {
			chBeran->SetNoRewardFlag();
			chBeran->Dead(nullptr, true);
		}
	} else {
		bool isEndLogWroten = false;
		if (strcmp(GetMasterName(), "[Bilinmeyen]") != 0) {
			std::unique_ptr<SQLMsg> sqlQuery(DBManager::instance().DirectQuery(
				"INSERT INTO log.dungeon_log(dungeon_id, leader_name, leader_pid, finish_time) VALUES(%u, '%s', %u, %u);",
				3, GetMasterName(), m_dwMasterPID, get_global_time() - m_dwStartTime));
			if (sqlQuery->Get()->uiInsertID != 0) {
				sys_log(0, "WriteFinishLog end log by player PID success beranSetaou");
			}
			isEndLogWroten = true;
		}

		for (const auto& chPID : vec_Players) {
			LPCHARACTER logCh = CHARACTER_MANAGER::Instance().FindByPID(chPID);
			if (!logCh) { continue; }

			if (logCh->GetMapIndex() == CRYSTAL_ROOM_MAP_IDX) {
				logCh->SetQuestFlag(BRN_CD_QF, get_global_time() + DUNGEON_COOLDOWN_W_KILL);
			}
			// CDungeonSystem::Instance().WriteEndLog(3, logCh->GetPlayerID(), logCh->GetName());
			if (!isEndLogWroten) {
				std::unique_ptr<SQLMsg> sqlQuery(DBManager::instance().DirectQuery(
					"INSERT INTO log.dungeon_log(dungeon_id, leader_name, leader_pid, finish_time) VALUES(%u, '%s', %u, %u);",
					3, logCh->GetName(), logCh->GetPlayerID(), get_global_time() - m_dwStartTime));
				if (sqlQuery->Get()->uiInsertID != 0) {
					sys_log(0, "WriteFinishLog end log by player PID success beranSetaou");
				}
				isEndLogWroten = true;
			}
		}
	}

	m_bsVID = 0;
	sys_log(0, "EndDungeon, end");
}

void CBeranSetaou::ClearRoom(bool bAll)
{
	StartUpdateEvent(true);
	StartDestroyEvent(true);
	WarpPlayer(false);

	vec_Players.clear();
	m_bsVID = 0;
	m_dwPasswd = 0;
	m_dwMasterPID = 0;
	m_dwStartTime = 0;
	m_roomState = BS_STATE_EMPTY;

	BSNotice(BS_NOTICE_DRAGON_RETURN_BACK);
}

void CBeranSetaou::StartUpdateEvent(bool bOnlyCancel)
{
	if (m_updateTimer) { event_cancel(&m_updateTimer); }
	if (bOnlyCancel)   { return; }

	bs_update_event_info* info = AllocEventInfo<bs_update_event_info>();
	info->myClass        = this;
	info->updateInterval = BS_TIMER_TICK_INVERVAL;
	info->elapsedTime    = 0;
	info->passCount      = 0;
	m_updateTimer = event_create(bs_update_event, info, PASSES_PER_SEC(info->updateInterval));
}

void CBeranSetaou::StartDestroyEvent(bool bOnlyCancel)
{
#ifdef CODING_PHASE
	BS_SendDebugMessageToDeveloper(1, "StartDestroyEvent");
#endif
	if (m_destroyTimer) { event_cancel(&m_destroyTimer); }
	if (bOnlyCancel)    { return; }

	bs_destroy_event_info* info = AllocEventInfo<bs_destroy_event_info>();
	info->myClass        = this;
	info->updateInterval = BS_TIMER_TICK_INVERVAL;
	info->elapsedTime    = 0;
	m_destroyTimer = event_create(bs_destroy_event, info, PASSES_PER_SEC(info->updateInterval));
}

uint8_t CBeranSetaou::CanJoin(LPCHARACTER joinCh)
{
	if (!joinCh)                                                          { return BS_JOIN_ERR_NONE; }
	if (!joinCh->GetDesc())                                               { return BS_JOIN_ERR_NONE; }
	if (joinCh->CountSpecifyItem(JOIN_TICKET_VNUM) < JOIN_TICKET_COUNT)   { return BS_JOIN_ERR_NO_ITEM; }
	if (joinCh->GetQuestFlag(BRN_CD_QF) >= get_global_time())             { return BS_JOIN_ERR_HAS_CD; }
	if (m_roomState != BS_STATE_EMPTY) {
		return (m_roomState == BS_STATE_BUSY) ? BS_JOIN_ERR_BUSY : BS_JOIN_ERR_WAITING_FOR_RETURN;
	}
	return BS_JOIN_OK;
}

uint8_t CBeranSetaou::StartRequest(LPCHARACTER joinCh, uint32_t roomPasswd, bool isWithParty)
{
	if (!joinCh)                                                          { return BS_JOIN_ERR_NONE; }
	if (!joinCh->GetDesc())                                               { return BS_JOIN_ERR_NONE; }
	if (IsHwidCooldown(BERAN_SETAOU_DUNGEON_ID, joinCh))                  { return BS_JOIN_ERR_HAS_HWID_CD; }
	if (joinCh->CountSpecifyItem(JOIN_TICKET_VNUM) < JOIN_TICKET_COUNT)   { return BS_JOIN_ERR_NO_ITEM; }
	if (joinCh->GetQuestFlag(BRN_CD_QF) >= get_global_time())             { return BS_JOIN_ERR_HAS_CD; }
	if (m_roomState != BS_STATE_EMPTY) {
		return (m_roomState == BS_STATE_BUSY) ? BS_JOIN_ERR_BUSY : BS_JOIN_ERR_WAITING_FOR_RETURN;
	}
	StartDungeon(joinCh, roomPasswd, isWithParty);
	return BS_JOIN_OK;
}

void CBeranSetaou::JoinPlayer(LPCHARACTER joinCh)
{
	if (!joinCh)              { return; }
	if (!joinCh->GetDesc())   { return; }

	vec_Players.push_back(joinCh->GetPlayerID());
	joinCh->SetQuestFlag(BRN_CD_QF, get_global_time() + DUNGEON_COOLDOWN);
	// LogManager::Instance().DungeonHwidLog(joinCh->GetPlayerID(), joinCh->GetAID(), BERAN_SETAOU_DUNGEON_ID, joinCh->GetDesc()->GetHwid());
	// LogManager::Instance().DungeonHwidLog(joinCh->GetPlayerID(), joinCh->GetAID(), BERAN_SETAOU_DUNGEON_ID, joinCh->GetDesc()->GetHostName());
	WarpPlayer(joinCh, true);
}

void CBeranSetaou::WarpPlayer(LPCHARACTER warpCh, bool bIsIn)
{
	if (!warpCh)              { return; }
	if (!warpCh->GetDesc())   { return; }

	if (bIsIn) {
		if (!IsInCrystalRoom(warpCh->GetMapIndex())) {
			warpCh->WarpSet(m_crystalRoom->m_setting.iBaseX + (PLAYER_JOIN_X * 100),
			                m_crystalRoom->m_setting.iBaseY + (PLAYER_JOIN_Y * 100));
		}
	} else {
		if (IsInCrystalRoom(warpCh->GetMapIndex())) {
			warpCh->WarpSet(PLAYER_QUIT_X * 100, PLAYER_QUIT_Y * 100);
		}
	}
}

void CBeranSetaou::WarpPlayer(bool bIsIn)
{
	for (const auto& chPID : vec_Players) {
		LPCHARACTER warpCh = CHARACTER_MANAGER::Instance().FindByPID(chPID);
		if (warpCh && IsInCrystalRoom(warpCh->GetMapIndex())) {
			warpCh->WarpSet(PLAYER_QUIT_X * 100, PLAYER_QUIT_Y * 100);
		}
	}
}

void CBeranSetaou::BSNotice(uint8_t noticeType)
{
	char szNotice[256];
	if (noticeType == BS_NOTICE_CLEAR_DELAY) {
		snprintf(szNotice, sizeof(szNotice), "%d saniye icinde disari gonderileceksiniz.", BS_CLEAR_DELAY_AFTER_FINISH);
		SendNoticeMap(szNotice, CRYSTAL_ROOM_MAP_IDX, true);
		return;
	}
	if (noticeType == BS_NOTICE_DRAGON_KILLED) {
		snprintf(szNotice, sizeof(szNotice), "CH:%d - %s ve grubu Mavi Ejderha'yi oldurdu.", g_bChannel, GetMasterName());
	}
	else if (noticeType == BS_NOTICE_DRAGON_STILL_LIVING) {
		snprintf(szNotice, sizeof(szNotice), "CH:%d - Mavi Ejderha hala yasiyor.", g_bChannel);
	}
	else if (noticeType == BS_NOTICE_JOIN) {
		snprintf(szNotice, sizeof(szNotice), "CH:%d - %s ve grubu Mavi Ejderha'yi oldurmeye calisiyor.", g_bChannel, GetMasterName());
	}
	else if (noticeType == BS_NOTICE_DRAGON_RETURN_BACK) {
		snprintf(szNotice, sizeof(szNotice), "CH:%d - Mavi Ejderha geri dondu.", g_bChannel);
	}
	else {
		return;
	}

	BroadcastNotice(szNotice);
}

void CBeranSetaou::OnDead(LPCHARACTER chDead, LPCHARACTER chKiller)
{
	if (!chDead)   { return; }
	if (!chKiller) { return; }

#ifdef CODING_PHASE
	BS_SendDebugMessageToDeveloper(1, "OnDead: %d ", chDead->GetRaceNum());
#endif

	if (chDead->IsStone()
		&& chDead->GetRaceNum() >= STONE_VNUM_START
		&& chDead->GetRaceNum() <= STONE_VNUM_END)
	{
		SpawnRandomStone();
	}

	if (chDead->GetRaceNum() == BERAN_SETAOU_VNUM) {
		EndDungeon(true);
	}
}

void CBeranSetaou::OnDisconnect(LPCHARACTER ch)
{
#ifdef CODING_PHASE
	BS_SendDebugMessageToDeveloper(1, "OnDisconnect, playerCnt: %d", GetCountPlayerInMap());
#endif
	//(void)ch;
}

void CBeranSetaou::SpawnRandomStone()
{
	const uint32_t stoneVnum = number(STONE_VNUM_START, STONE_VNUM_END);
	CHARACTER_MANAGER::instance().SpawnMob(stoneVnum, CRYSTAL_ROOM_MAP_IDX,
		m_crystalRoom->m_setting.iBaseX + ((STONE_POS_X + number(-STONE_POS_RND_EX, STONE_POS_RND_EX)) * 100),
		m_crystalRoom->m_setting.iBaseY + ((STONE_POS_Y + number(-STONE_POS_RND_EX, STONE_POS_RND_EX)) * 100),
		0, true);
#ifdef CODING_PHASE
	BS_SendDebugMessageToDeveloper(1, "SpawnRandomStone -> %d spawned.", stoneVnum);
#endif
}

bool CBeranSetaou::CanStayInCrystalRoom(LPCHARACTER ch) const
{
	if (!ch || !ch->GetDesc()) { return false; }
	return std::find(vec_Players.begin(), vec_Players.end(), ch->GetPlayerID()) != vec_Players.end();
}

int64_t CBeranSetaou::GetRemainTime() const
{
	return static_cast<int64_t>(m_dwStartTime + BS_MAX_TIME_LIMIT)
	     - static_cast<int64_t>(get_global_time());
}

uint8_t CBeranSetaou::GetCountPlayerInMap()
{
	if (!m_crystalRoom) { return 0; }

	FCountPC f;
	m_crystalRoom->for_each(f);
	return f.chCount;
}

const char* CBeranSetaou::GetMasterName()
{
	LPCHARACTER masterCh = CHARACTER_MANAGER::Instance().FindByPID(m_dwMasterPID);
	if (masterCh) { return masterCh->GetName(); }
	return "[Bilinmeyen]";
}

bool CBeranSetaou::IsHwidCooldown(uint16_t dungeonID, LPCHARACTER ch)
{
	return false;
	/*if (!ch || !ch->GetDesc()) { return true; }

	const uint32_t cooldownMins = DUNGEON_COOLDOWN_W_KILL / 60;
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
		"SELECT player_id FROM log.dungeon_hwid_log WHERE dungeon_id = %d AND hwid = '%s' "
		"AND play_time >= NOW() - INTERVAL %d MINUTE LIMIT 0,1;",
		dungeonID, ch->GetDesc()->GetHwid(), cooldownMins));

	if (ch->IsGM()) {
		ch->ChatPacket(1, "<DEV|BERAN> dungeonID: %d, pcHwid: %s, mins: %d, hasCd: %s",
			dungeonID, ch->GetDesc()->GetHwid(), cooldownMins,
			(pMsg->Get()->uiNumRows > 0 ? "true" : "false"));
	}

	return pMsg->Get()->uiNumRows > 0;*/
}
#endif
