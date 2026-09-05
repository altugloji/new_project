#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "packet.h"
#include "desc.h"
#include "buffer_manager.h"
#include "start_position.h"
#include "questmanager.h"
#include "char.h"
#include "char_manager.h"
#include "arena.h"
#ifdef ENABLE_WS_TOURNAMENT
#include "ws_tournament.h"
#endif
#include <cstdarg>

CArena::CArena(WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y)
{
	m_StartPointA.x = startA_X;
	m_StartPointA.y = startA_Y;
	m_StartPointA.z = 0;

	m_StartPointB.x = startB_X;
	m_StartPointB.y = startB_Y;
	m_StartPointB.z = 0;

	m_ObserverPoint.x = (startA_X + startB_X) / 2;
	m_ObserverPoint.y = (startA_Y + startB_Y) / 2;
	m_ObserverPoint.z = 0;

	m_pEvent = nullptr;
	m_pTimeOutEvent = nullptr;

	Clear();
}

void CArena::Clear()
{
	m_dwPIDA = 0;
	m_dwPIDB = 0;

	if (m_pEvent != nullptr)
	{
		event_cancel(&m_pEvent);
	}

	if (m_pTimeOutEvent != nullptr)
	{
		event_cancel(&m_pTimeOutEvent);
	}

	m_dwSetCount = 0;
	m_dwSetPointOfA = 0;
	m_dwSetPointOfB = 0;
}

bool CArenaManager::AddArena(DWORD mapIdx, WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y)
{
	CArenaMap *pArenaMap = nullptr;
	auto iter = m_mapArenaMap.find(mapIdx);

	if (iter == m_mapArenaMap.end())
	{
		pArenaMap = M2_NEW CArenaMap;
		m_mapArenaMap.emplace(mapIdx, pArenaMap);
	}
	else
	{
		pArenaMap = iter->second;
	}

	if (pArenaMap->AddArena(mapIdx, startA_X, startA_Y, startB_X, startB_Y) == false)
	{
		sys_log(0, "CArenaManager::AddArena - AddMap Error MapID: %d", mapIdx);
		return false;
	}

	return true;
}

bool CArenaMap::AddArena(DWORD mapIdx, WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y)
{
	for (const auto & iter : m_listArena)
	{
		if (!iter->CheckArea(startA_X, startA_Y, startB_X, startB_Y))
		{
			sys_log(0, "CArenaMap::AddArena - Same Start Position set. stA(%d, %d) stB(%d, %d)", startA_X, startA_Y, startB_X, startB_Y);
			return false;
		}
	}

	m_dwMapIndex = mapIdx;

	auto * pArena = M2_NEW CArena(startA_X, startA_Y, startB_X, startB_Y);
	m_listArena.emplace_back(pArena);

	return true;
}

void CArenaManager::Destroy()
{
	for (auto & iter : m_mapArenaMap)
	{
		auto * pArenaMap = iter.second;
		pArenaMap->Destroy();
		M2_DELETE(pArenaMap);
	}
	m_mapArenaMap.clear();
}

void CArenaMap::Destroy()
{
	sys_log(0, "ARENA: ArenaMap will be destroy. mapIndex(%d)", m_dwMapIndex);

	for (auto & pArena : m_listArena)
	{
		pArena->EndDuel();
		M2_DELETE(pArena);
	}
	m_listArena.clear();
}

bool CArena::CheckArea(WORD startA_X, WORD startA_Y, WORD startB_X, WORD startB_Y) const
{
	if (m_StartPointA.x == startA_X && m_StartPointA.y == startA_Y &&
			m_StartPointB.x == startB_X && m_StartPointB.y == startB_Y)
		return false;
	return true;
}

void CArenaManager::SendArenaMapListTo(LPCHARACTER pChar)
{
	for (auto & iter : m_mapArenaMap)
	{
		auto * pArena = iter.second;
		pArena->SendArenaMapListTo(pChar, iter.first);
	}
}

void CArenaMap::SendArenaMapListTo(LPCHARACTER pChar, DWORD mapIdx)
{
	if (pChar == nullptr) return;

	for (auto & iter : m_listArena)
	{
		pChar->ChatPacket(CHAT_TYPE_INFO, "ArenaMapInfo Map: %d stA(%d, %d) stB(%d, %d)", mapIdx,
				iter->GetStartPointA().x, iter->GetStartPointA().y,
				iter->GetStartPointB().x, iter->GetStartPointB().y);
	}
}

bool CArenaManager::StartDuel(LPCHARACTER pCharFrom, LPCHARACTER pCharTo, int nSetPoint, int nMinute)
{
	if (pCharFrom == nullptr || pCharTo == nullptr) return false;

	for (auto & iter : m_mapArenaMap)
	{
		auto * pArenaMap = iter.second;
		if (pArenaMap->StartDuel(pCharFrom, pCharTo, nSetPoint, nMinute) == true)
			return true;
	}

	return false;
}

bool CArenaMap::StartDuel(LPCHARACTER pCharFrom, LPCHARACTER pCharTo, int nSetPoint, int nMinute)
{
	for (auto & pArena : m_listArena)
	{
		if (pArena->IsEmpty() == true)
			return pArena->StartDuel(pCharFrom, pCharTo, nSetPoint, nMinute);
	}

	return false;
}

EVENTINFO(TArenaEventInfo)
{
	CArena *pArena;
	BYTE state;

	TArenaEventInfo()
	: pArena(nullptr)
	, state(0)
	{
	}
};

EVENTFUNC(ready_to_start_event)
{
	if (event == nullptr)
		return 0;

	if (event->info == nullptr)
		return 0;

	const auto info = dynamic_cast<TArenaEventInfo*>(event->info);

	if ( info == nullptr)
	{
		sys_err( "ready_to_start_event> <Factor> Null pointer" );
		return 0;
	}

	auto * pArena = info->pArena;
	if (pArena == nullptr)
	{
		sys_err("ARENA: Arena start event info is null.");
		return 0;
	}

	const LPCHARACTER chA = pArena->GetPlayerA();
	const LPCHARACTER chB = pArena->GetPlayerB();

	if (chA == nullptr || chB == nullptr)
	{
		sys_err("ARENA: Player err in event func ready_start_event");

#ifdef ENABLE_WS_TOURNAMENT
		CWSTournamentManager::instance().OnArenaMatchAborted(pArena->GetPlayerAPID(), pArena->GetPlayerBPID(), chA != nullptr, chB != nullptr, pArena->GetSetPointA(), pArena->GetSetPointB());
#endif

		if (chA != nullptr)
		{
			chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련 상대가 사라져 대련을 종료합니다."));
			sys_log(0, "ARENA: Oppernent is disappered. MyPID(%d) OppPID(%d)", pArena->GetPlayerAPID(), pArena->GetPlayerBPID());
		}

		if (chB != nullptr)
		{
			chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련 상대가 사라져 대련을 종료합니다."));
			sys_log(0, "ARENA: Oppernent is disappered. MyPID(%d) OppPID(%d)", pArena->GetPlayerBPID(), pArena->GetPlayerAPID());
		}

		pArena->SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("대련 상대가 사라져 대련을 종료합니다."));

		pArena->EndDuel();
		return 0;
	}

	switch (info->state)
	{
		case 0:
			{
				chA->SetArena(pArena);
				chB->SetArena(pArena);

#ifndef ENABLE_WS_TOURNAMENT	// pot engeli kaldirildi (WS)
				const int count = quest::CQuestManager::instance().GetEventFlag("arena_potion_limit_count");

				if (count > 10000)
				{
					chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("물약 제한이 없습니다."));
					chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("물약 제한이 없습니다."));
				}
				else
				{
					chA->SetPotionLimit(count);
					chB->SetPotionLimit(count);

					chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("물약을 %d 개 까지 사용 가능합니다."), chA->GetPotionLimit());
					chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("물약을 %d 개 까지 사용 가능합니다."), chB->GetPotionLimit());
				}
#endif
				chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("10초뒤 대련이 시작됩니다."));
				chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("10초뒤 대련이 시작됩니다."));
				pArena->SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("10초뒤 대련이 시작됩니다."));

#ifdef ENABLE_WS_TOURNAMENT
				// turnuva maci: 10 sn hazirlik - hareket kilitli, beceri serbest
				if (CWSTournamentManager::instance().BeginMatchPrep(pArena->GetPlayerAPID(), pArena->GetPlayerBPID()))
				{
					chA->WSResetAllSkillCooldowns();	// raunt basi taze baslangic (client GC 231 ile senkron)
					chB->WSResetAllSkillCooldowns();
					chA->ChatPacket(CHAT_TYPE_NOTICE, "WS: 10 saniye hazirlik! Becerilerini simdi kullan - hareket kilitli.");
					chB->ChatPacket(CHAT_TYPE_NOTICE, "WS: 10 saniye hazirlik! Becerilerini simdi kullan - hareket kilitli.");
				}
#endif
				info->state++;
				return PASSES_PER_SEC(10);
			}
			break;

		case 1:
			{
#ifdef ENABLE_WS_TOURNAMENT
				if (CWSTournamentManager::instance().EndMatchPrep(pArena->GetPlayerAPID(), pArena->GetPlayerBPID()))
				{
					// kilit boyunca dusurulen hareketlere karsi son konum duzeltmesi
					chA->SyncPacket();
					chB->SyncPacket();
					chA->ChatPacket(CHAT_TYPE_NOTICE, "WS: DOVUS BASLADI!");
					chB->ChatPacket(CHAT_TYPE_NOTICE, "WS: DOVUS BASLADI!");
				}
#endif
				chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련이 시작되었습니다."));
				chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련이 시작되었습니다."));
				pArena->SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("대련이 시작되었습니다."));

				TPacketGCDuelStart duelStart;
				duelStart.header = HEADER_GC_DUEL_START;
				duelStart.wSize = sizeof(TPacketGCDuelStart) + 4;

				DWORD dwOppList[8];

				dwOppList[0] = (DWORD)chB->GetVID();
				TEMP_BUFFER buf;

				buf.write(&duelStart, sizeof(TPacketGCDuelStart));
				buf.write(&dwOppList[0], 4);
				chA->GetDesc()->Packet(buf.read_peek(), buf.size());

				dwOppList[0] = (DWORD)chA->GetVID();
				TEMP_BUFFER buf2;

				buf2.write(&duelStart, sizeof(TPacketGCDuelStart));
				buf2.write(&dwOppList[0], 4);
				chB->GetDesc()->Packet(buf2.read_peek(), buf2.size());

				return 0;
			}
			break;

		case 2:
			{
				pArena->EndDuel();
				return 0;
			}
			break;

		case 3:
			{
				chA->Show(chA->GetMapIndex(), pArena->GetStartPointA().x * 100, pArena->GetStartPointA().y * 100);
				chB->Show(chB->GetMapIndex(), pArena->GetStartPointB().x * 100, pArena->GetStartPointB().y * 100);

				chA->GetDesc()->SetPhase(PHASE_GAME);
				chA->StartRecoveryEvent();
				chA->SetPosition(POS_STANDING);
				chA->PointChange(POINT_HP, chA->GetMaxHP() - chA->GetHP());
				chA->PointChange(POINT_SP, chA->GetMaxSP() - chA->GetSP());
				chA->ViewReencode();

				chB->GetDesc()->SetPhase(PHASE_GAME);
				chB->StartRecoveryEvent();
				chB->SetPosition(POS_STANDING);
				chB->PointChange(POINT_HP, chB->GetMaxHP() - chB->GetHP());
				chB->PointChange(POINT_SP, chB->GetMaxSP() - chB->GetSP());
				chB->ViewReencode();

#ifdef ENABLE_WS_TOURNAMENT
				// turnuva: set arasinda da 10 sn hazirlik; sure bitince case 1 DUEL_START gonderir
				if (CWSTournamentManager::instance().BeginMatchPrep(pArena->GetPlayerAPID(), pArena->GetPlayerBPID()))
				{
					chA->WSResetAllSkillCooldowns();	// raunt basi taze baslangic (client GC 231 ile senkron)
					chB->WSResetAllSkillCooldowns();
					chA->ChatPacket(CHAT_TYPE_NOTICE, "WS: 10 saniye hazirlik! Becerilerini simdi kullan - hareket kilitli.");
					chB->ChatPacket(CHAT_TYPE_NOTICE, "WS: 10 saniye hazirlik! Becerilerini simdi kullan - hareket kilitli.");
					info->state = 1;
					return PASSES_PER_SEC(WS_PREP_SECONDS);
				}
#endif
				TEMP_BUFFER buf;
				TEMP_BUFFER buf2;
				DWORD dwOppList[8];
				TPacketGCDuelStart duelStart;
				duelStart.header = HEADER_GC_DUEL_START;
				duelStart.wSize = sizeof(TPacketGCDuelStart) + 4;

				dwOppList[0] = (DWORD)chB->GetVID();
				buf.write(&duelStart, sizeof(TPacketGCDuelStart));
				buf.write(&dwOppList[0], 4);
				chA->GetDesc()->Packet(buf.read_peek(), buf.size());

				dwOppList[0] = (DWORD)chA->GetVID();
				buf2.write(&duelStart, sizeof(TPacketGCDuelStart));
				buf2.write(&dwOppList[0], 4);
				chB->GetDesc()->Packet(buf2.read_peek(), buf2.size());

				chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련이 시작되었습니다."));
				chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련이 시작되었습니다."));
				pArena->SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("대련이 시작되었습니다."));

				pArena->ClearEvent();

				return 0;
			}
			break;

		default:
			{
				chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련장 문제로 인하여 대련을 종료합니다."));
				chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련장 문제로 인하여 대련을 종료합니다."));
				pArena->SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("대련장 문제로 인하여 대련을 종료합니다."));

				sys_log(0, "ARENA: Something wrong in event func. info->state(%d)", info->state);

				pArena->EndDuel();

				return 0;
			}
	}
}

EVENTFUNC(duel_time_out)
{
	if (event == nullptr) return 0;
	if (event->info == nullptr) return 0;

	const auto info = dynamic_cast<TArenaEventInfo*>(event->info);

	if ( info == nullptr)
	{
		sys_err( "duel_time_out> <Factor> Null pointer" );
		return 0;
	}

	auto * pArena = info->pArena;
	if (pArena == nullptr)
	{
		sys_err("ARENA: Time out event error");
		return 0;
	}

	const LPCHARACTER chA = pArena->GetPlayerA();
	const LPCHARACTER chB = pArena->GetPlayerB();

	if (chA == nullptr || chB == nullptr)
	{
		if (chA != nullptr)
		{
			chA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련 상대가 사라져 대련을 종료합니다."));
			sys_log(0, "ARENA: Oppernent is disappered. MyPID(%d) OppPID(%d)", pArena->GetPlayerAPID(), pArena->GetPlayerBPID());
		}

		if (chB != nullptr)
		{
			chB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("대련 상대가 사라져 대련을 종료합니다."));
			sys_log(0, "ARENA: Oppernent is disappered. MyPID(%d) OppPID(%d)", pArena->GetPlayerBPID(), pArena->GetPlayerAPID());
		}

		pArena->SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("대련 상대가 사라져 대련을 종료합니다."));

#ifdef ENABLE_WS_TOURNAMENT
		CWSTournamentManager::instance().OnArenaMatchAborted(pArena->GetPlayerAPID(), pArena->GetPlayerBPID(), chA != nullptr, chB != nullptr, pArena->GetSetPointA(), pArena->GetSetPointB());
#endif
		pArena->EndDuel();
		return 0;
	}
	else
	{
		switch (info->state)
		{
			case 0:
				pArena->SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("대련 시간 초과로 대련을 중단합니다."));
				pArena->SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("10초뒤 마을로 이동합니다."));

				chA->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("대련 시간 초과로 대련을 중단합니다."));
				chA->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("10초뒤 마을로 이동합니다."));

				chB->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("대련 시간 초과로 대련을 중단합니다."));
				chB->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("10초뒤 마을로 이동합니다."));

				TPacketGCDuelStart duelStart;
				duelStart.header = HEADER_GC_DUEL_START;
				duelStart.wSize = sizeof(TPacketGCDuelStart);

				chA->GetDesc()->Packet(&duelStart, sizeof(TPacketGCDuelStart));
				chB->GetDesc()->Packet(&duelStart, sizeof(TPacketGCDuelStart));

#ifdef ENABLE_WS_TOURNAMENT
				CWSTournamentManager::instance().OnArenaTimeout(pArena->GetPlayerAPID(), pArena->GetPlayerBPID(), pArena->GetSetPointA(), pArena->GetSetPointB(), chA, chB);
#endif
				info->state++;

				sys_log(0, "ARENA: Because of time over, duel is end. PIDA(%d) vs PIDB(%d)", pArena->GetPlayerAPID(), pArena->GetPlayerBPID());

				return PASSES_PER_SEC(10);
				break;

			case 1:
				pArena->EndDuel();
				break;
		}
	}

	return 0;
}

bool CArena::StartDuel(LPCHARACTER pCharFrom, LPCHARACTER pCharTo, int nSetPoint, int nMinute)
{
	this->m_dwPIDA = pCharFrom->GetPlayerID();
	this->m_dwPIDB = pCharTo->GetPlayerID();
	this->m_dwSetCount = nSetPoint;

	pCharFrom->WarpSet(GetStartPointA().x * 100, GetStartPointA().y * 100);
	pCharTo->WarpSet(GetStartPointB().x * 100, GetStartPointB().y * 100);

	if (m_pEvent != nullptr) {
		event_cancel(&m_pEvent);
	}

	TArenaEventInfo* info = AllocEventInfo<TArenaEventInfo>();

	info->pArena = this;
	info->state = 0;

	m_pEvent = event_create(ready_to_start_event, info, PASSES_PER_SEC(10));

	if (m_pTimeOutEvent != nullptr) {
		event_cancel(&m_pTimeOutEvent);
	}

	info = AllocEventInfo<TArenaEventInfo>();

	info->pArena = this;
	info->state = 0;

	m_pTimeOutEvent = event_create(duel_time_out, info, PASSES_PER_SEC(nMinute*60));

	pCharFrom->PointChange(POINT_HP, pCharFrom->GetMaxHP() - pCharFrom->GetHP());
	pCharFrom->PointChange(POINT_SP, pCharFrom->GetMaxSP() - pCharFrom->GetSP());

	pCharTo->PointChange(POINT_HP, pCharTo->GetMaxHP() - pCharTo->GetHP());
	pCharTo->PointChange(POINT_SP, pCharTo->GetMaxSP() - pCharTo->GetSP());

	sys_log(0, "ARENA: Start Duel with PID_A(%d) vs PID_B(%d)", GetPlayerAPID(), GetPlayerBPID());
	return true;
}

#ifdef ENABLE_WS_TOURNAMENT
bool CArena::WSPauseIfMember(DWORD dwPID)
{
	if (m_dwPIDA != dwPID && m_dwPIDB != dwPID)
		return false;

	// eventler durdurulur (hazirlik/mac saati); arena ve skorlar CANLI kalir,
	// rakip ringde serbest bekler (kopma-bekleme: Eski_A modeli)
	if (m_pEvent != nullptr)
		event_cancel(&m_pEvent);
	if (m_pTimeOutEvent != nullptr)
		event_cancel(&m_pTimeOutEvent);

	return true;
}

bool CArena::WSResumeDuelIfMember(DWORD dwPID, int iRemainSec)
{
	if (m_dwPIDA != dwPID && m_dwPIDB != dwPID)
		return false;

	const LPCHARACTER chA = GetPlayerA();
	const LPCHARACTER chB = GetPlayerB();

	if (chA == nullptr || chB == nullptr || chA->GetDesc() == nullptr || chB->GetDesc() == nullptr)
		return false;

	// relog sonrasi arena uyeligi ve duello anahtarlari (VID degisir) iki tarafta da tazelenir
	chA->SetArena(this);
	chB->SetArena(this);

	// set arasi kopus: taraflardan biri olu ise seti bastan kur - pause bekleyen ready
	// eventini iptal etmisti; state 3 zinciri revive + kose warp + prep yapar ve
	// DUEL_START'i case 1 gonderir (in-place resume olu oyuncuyu asla canlandiramazdi)
	if (chA->IsDead() || chB->IsDead())
	{
		if (m_pEvent != nullptr)
			event_cancel(&m_pEvent);

		TArenaEventInfo* info0 = AllocEventInfo<TArenaEventInfo>();
		info0->pArena = this;
		info0->state = 3;
		m_pEvent = event_create(ready_to_start_event, info0, PASSES_PER_SEC(2));
	}
	else
	{
		TPacketGCDuelStart duelStart;
		duelStart.header = HEADER_GC_DUEL_START;
		duelStart.wSize = sizeof(TPacketGCDuelStart) + 4;

		DWORD dwOppList[1];

		TEMP_BUFFER buf;
		dwOppList[0] = (DWORD) chB->GetVID();
		buf.write(&duelStart, sizeof(TPacketGCDuelStart));
		buf.write(&dwOppList[0], 4);
		chA->GetDesc()->Packet(buf.read_peek(), buf.size());

		TEMP_BUFFER buf2;
		dwOppList[0] = (DWORD) chA->GetVID();
		buf2.write(&duelStart, sizeof(TPacketGCDuelStart));
		buf2.write(&dwOppList[0], 4);
		chB->GetDesc()->Packet(buf2.read_peek(), buf2.size());
	}

	// mac saati kalan sureyle yeniden kurulur
	if (m_pTimeOutEvent != nullptr)
		event_cancel(&m_pTimeOutEvent);

	TArenaEventInfo* info = AllocEventInfo<TArenaEventInfo>();
	info->pArena = this;
	info->state = 0;
	m_pTimeOutEvent = event_create(duel_time_out, info, PASSES_PER_SEC(iRemainSec > 30 ? iRemainSec : 30));

	sys_log(0, "ARENA: WS resume duel PID_A(%d) vs PID_B(%d) remain(%d)", GetPlayerAPID(), GetPlayerBPID(), iRemainSec);
	return true;
}

bool CArena::WSSendDuelStartIfMember(DWORD dwPID)
{
	if (m_dwPIDA != dwPID && m_dwPIDB != dwPID)
		return false;

	const LPCHARACTER chA = GetPlayerA();
	const LPCHARACTER chB = GetPlayerB();

	// relog sonrasi arena uyeligi tazelenir (vanilla MEMBER_DUELIST SetArena yapmaz);
	// tek tarafli donuste bile: ikinci kopusun DC sayacina islenmesi GetArena'ya bagli
	if (chA != nullptr)
		chA->SetArena(this);
	if (chB != nullptr)
		chB->SetArena(this);

	if (chA == nullptr || chB == nullptr)
		return false;

	TPacketGCDuelStart duelStart;
	duelStart.header = HEADER_GC_DUEL_START;
	duelStart.wSize = sizeof(TPacketGCDuelStart) + 4;

	DWORD dwOppList[1];

	if (chA->GetDesc() != nullptr)
	{
		TEMP_BUFFER buf;
		dwOppList[0] = (DWORD) chB->GetVID();
		buf.write(&duelStart, sizeof(TPacketGCDuelStart));
		buf.write(&dwOppList[0], 4);
		chA->GetDesc()->Packet(buf.read_peek(), buf.size());
	}

	if (chB->GetDesc() != nullptr)
	{
		TEMP_BUFFER buf2;
		dwOppList[0] = (DWORD) chA->GetVID();
		buf2.write(&duelStart, sizeof(TPacketGCDuelStart));
		buf2.write(&dwOppList[0], 4);
		chB->GetDesc()->Packet(buf2.read_peek(), buf2.size());
	}

	sys_log(0, "ARENA: WS resend duel start PID_A(%d) vs PID_B(%d)", GetPlayerAPID(), GetPlayerBPID());
	return true;
}
#endif

void CArenaManager::EndAllDuel()
{
	for (auto & iter : m_mapArenaMap)
	{
		auto * pArenaMap = iter.second;
		if (pArenaMap != nullptr)
			pArenaMap->EndAllDuel();
	}

	return;
}

void CArenaMap::EndAllDuel()
{
	for (auto & pArena : m_listArena)
	{
		if (pArena != nullptr)
			pArena->EndDuel();
	}
}

void CArena::EndDuel()
{
	if (m_pEvent != nullptr) {
		event_cancel(&m_pEvent);
	}
	if (m_pTimeOutEvent != nullptr) {
		event_cancel(&m_pTimeOutEvent);
	}

	const LPCHARACTER playerA = GetPlayerA();
	const LPCHARACTER playerB = GetPlayerB();

	if (playerA != nullptr)
	{
		playerA->SetPKMode(PK_MODE_PEACE);
		playerA->StartRecoveryEvent();
		playerA->SetPosition(POS_STANDING);
		playerA->PointChange(POINT_HP, playerA->GetMaxHP() - playerA->GetHP());
		playerA->PointChange(POINT_SP, playerA->GetMaxSP() - playerA->GetSP());

		playerA->SetArena(nullptr);

#ifdef ENABLE_WS_TOURNAMENT
		// turnuva: turlar arasinda sehre degil haritadaki baslangic noktasina don
		long lWsAX = 0, lWsAY = 0;
		if (CWSTournamentManager::instance().GetIntermissionPoint(GetPlayerAPID(), lWsAX, lWsAY))
			playerA->WarpSet(lWsAX, lWsAY);
		else
#endif
		playerA->WarpSet(ARENA_RETURN_POINT_X(playerA->GetEmpire()), ARENA_RETURN_POINT_Y(playerA->GetEmpire()));
	}

	if (playerB != nullptr)
	{
		playerB->SetPKMode(PK_MODE_PEACE);
		playerB->StartRecoveryEvent();
		playerB->SetPosition(POS_STANDING);
		playerB->PointChange(POINT_HP, playerB->GetMaxHP() - playerB->GetHP());
		playerB->PointChange(POINT_SP, playerB->GetMaxSP() - playerB->GetSP());

		playerB->SetArena(nullptr);

#ifdef ENABLE_WS_TOURNAMENT
		long lWsBX = 0, lWsBY = 0;
		if (CWSTournamentManager::instance().GetIntermissionPoint(GetPlayerBPID(), lWsBX, lWsBY))
			playerB->WarpSet(lWsBX, lWsBY);
		else
#endif
		playerB->WarpSet(ARENA_RETURN_POINT_X(playerB->GetEmpire()), ARENA_RETURN_POINT_Y(playerB->GetEmpire()));
	}

	for (auto & iter : m_mapObserver)
	{
		const LPCHARACTER pChar = CHARACTER_MANAGER::instance().FindByPID(iter.first);
		if (pChar != nullptr)
		{
#ifdef ENABLE_WS_TOURNAMENT
			// turnuva seyircileri de haritada kalir
			long lWsOX = 0, lWsOY = 0;
			if (CWSTournamentManager::instance().GetSpectatorIntermissionPoint(lWsOX, lWsOY))
			{
				pChar->WarpSet(lWsOX, lWsOY);
				continue;
			}
#endif
			pChar->WarpSet(ARENA_RETURN_POINT_X(pChar->GetEmpire()), ARENA_RETURN_POINT_Y(pChar->GetEmpire()));
		}
	}

	m_mapObserver.clear();

	#ifdef ENABLE_WS_TOURNAMENT
	CWSTournamentManager::instance().OnArenaClosed(m_dwPIDA, m_dwPIDB, m_dwSetPointOfA, m_dwSetPointOfB);
#endif
	sys_log(0, "ARENA: End Duel PID_A(%d) vs PID_B(%d)", GetPlayerAPID(), GetPlayerBPID());

	Clear();
}

void CArenaManager::GetDuelList(lua_State* L)
{
	int index = 1;
	lua_newtable(L);

	for (auto & iter : m_mapArenaMap)
	{
		auto * pArenaMap = iter.second;
		if (pArenaMap != nullptr)
			index = pArenaMap->GetDuelList(L, index);
	}
}

int CArenaMap::GetDuelList(lua_State* L, int index)
{
	for (auto & pArena : m_listArena)
	{
		if (pArena == nullptr) continue;

		if (pArena->IsEmpty() == false)
		{
			const LPCHARACTER chA = pArena->GetPlayerA();
			const LPCHARACTER chB = pArena->GetPlayerB();

			if (chA != nullptr && chB != nullptr)
			{
				lua_newtable(L);

				lua_pushstring(L, chA->GetName());
				lua_rawseti(L, -2, 1);

				lua_pushstring(L, chB->GetName());
				lua_rawseti(L, -2, 2);

				lua_pushnumber(L, m_dwMapIndex);
				lua_rawseti(L, -2, 3);

				lua_pushnumber(L, pArena->GetObserverPoint().x);
				lua_rawseti(L, -2, 4);

				lua_pushnumber(L, pArena->GetObserverPoint().y);
				lua_rawseti(L, -2, 5);

				lua_rawseti(L, -2, index++);
			}
		}
	}

	return index;
}

bool CArenaManager::CanAttack(LPCHARACTER pCharAttacker, LPCHARACTER pCharVictim)
{
	if (pCharAttacker == nullptr || pCharVictim == nullptr) return false;

	if (pCharAttacker == pCharVictim) return false;

	const long mapIndex = pCharAttacker->GetMapIndex();
	if (mapIndex != pCharVictim->GetMapIndex()) return false;

	auto iter = m_mapArenaMap.find(mapIndex);
	if (iter == m_mapArenaMap.end()) return false;

	auto * pArenaMap = iter->second;
	return pArenaMap->CanAttack(pCharAttacker, pCharVictim);
}

bool CArenaMap::CanAttack(LPCHARACTER pCharAttacker, LPCHARACTER pCharVictim)
{
	if (pCharAttacker == nullptr || pCharVictim == nullptr) return false;

	const DWORD dwPIDA = pCharAttacker->GetPlayerID();
	const DWORD dwPIDB = pCharVictim->GetPlayerID();

	for (const auto & pArena : m_listArena)
	{
		if (pArena->CanAttack(dwPIDA, dwPIDB) == true)
			return true;
	}
	return false;
}

bool CArena::CanAttack(DWORD dwPIDA, DWORD dwPIDB) const
{
	if (m_dwPIDA == dwPIDA && m_dwPIDB == dwPIDB) return true;
	if (m_dwPIDA == dwPIDB && m_dwPIDB == dwPIDA) return true;

	return false;
}

bool CArenaManager::OnDead(LPCHARACTER pCharKiller, LPCHARACTER pCharVictim)
{
	if (pCharKiller == nullptr || pCharVictim == nullptr) return false;

	const long mapIndex = pCharKiller->GetMapIndex();
	if (mapIndex != pCharVictim->GetMapIndex()) return false;

	auto iter = m_mapArenaMap.find(mapIndex);
	if (iter == m_mapArenaMap.end()) return false;

	auto * pArenaMap = iter->second;
	return pArenaMap->OnDead(pCharKiller,  pCharVictim);
}

bool CArenaMap::OnDead(LPCHARACTER pCharKiller, LPCHARACTER pCharVictim)
{
	const DWORD dwPIDA = pCharKiller->GetPlayerID();
	const DWORD dwPIDB = pCharVictim->GetPlayerID();

	for (auto & pArena : m_listArena)
	{
		if (pArena->IsMember(dwPIDA) == true && pArena->IsMember(dwPIDB) == true)
		{
			pArena->OnDead(dwPIDA, dwPIDB);
			return true;
		}
	}
	return false;
}

bool CArena::OnDead(DWORD dwPIDA, DWORD dwPIDB)
{
	bool restart = false;

	const LPCHARACTER pCharA = GetPlayerA();
	const LPCHARACTER pCharB = GetPlayerB();

	if (pCharA == nullptr && pCharB == nullptr)
	{
		SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("대련자 문제로 인하여 대련을 중단합니다."));
		restart = false;
	}
	else if (pCharA == nullptr && pCharB != nullptr)
	{
		pCharB->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("상대방 캐릭터의 문제로 인하여 대련을 종료합니다."));
		SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("대련자 문제로 인하여 대련을 종료합니다."));
		restart = false;
	}
	else if (pCharA != nullptr && pCharB == nullptr)
	{
		pCharA->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("상대방 캐릭터의 문제로 인하여 대련을 종료합니다."));
		SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("대련자 문제로 인하여 대련을 종료합니다."));
		restart = false;
	}
	else if (pCharA != nullptr && pCharB != nullptr)
	{
		if (m_dwPIDA == dwPIDA)
		{
			m_dwSetPointOfA++;

			if (m_dwSetPointOfA >= m_dwSetCount)
			{
				pCharA->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("%s 님이 대련에서 승리하였습니다."), pCharA->GetName());
				pCharB->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("%s 님이 대련에서 승리하였습니다."), pCharA->GetName());
				SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("%s 님이 대련에서 승리하였습니다."), pCharA->GetName());

				sys_log(0, "ARENA: Duel is end. Winner %s(%d) Loser %s(%d)",
						pCharA->GetName(), GetPlayerAPID(), pCharB->GetName(), GetPlayerBPID());

#ifdef ENABLE_WS_TOURNAMENT
				CWSTournamentManager::instance().OnArenaMatchEnd(m_dwPIDA, m_dwPIDB);
#endif
			}
			else
			{
				restart = true;
				pCharA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s 님이 승리하였습니다."), pCharA->GetName());
				pCharA->ChatPacket(CHAT_TYPE_NOTICE, "%s %d : %d %s", pCharA->GetName(), m_dwSetPointOfA, m_dwSetPointOfB, pCharB->GetName());

				pCharB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s 님이 승리하였습니다."), pCharA->GetName());
				pCharB->ChatPacket(CHAT_TYPE_NOTICE, "%s %d : %d %s", pCharA->GetName(), m_dwSetPointOfA, m_dwSetPointOfB, pCharB->GetName());

				SendChatPacketToObserver(CHAT_TYPE_NOTICE, "%s %d : %d %s", pCharA->GetName(), m_dwSetPointOfA, m_dwSetPointOfB, pCharB->GetName());

				sys_log(0, "ARENA: %s(%d) won a round vs %s(%d)",
						pCharA->GetName(), GetPlayerAPID(), pCharB->GetName(), GetPlayerBPID());
			}
		}
		else if (m_dwPIDB == dwPIDA)
		{
			m_dwSetPointOfB++;
			if (m_dwSetPointOfB >= m_dwSetCount)
			{
				pCharA->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("%s 님이 대련에서 승리하였습니다."), pCharB->GetName());
				pCharB->ChatPacket(CHAT_TYPE_NOTICE, LC_TEXT("%s 님이 대련에서 승리하였습니다."), pCharB->GetName());
				SendChatPacketToObserver(CHAT_TYPE_NOTICE, LC_TEXT("%s 님이 대련에서 승리하였습니다."), pCharB->GetName());

				sys_log(0, "ARENA: Duel is end. Winner(%d) Loser(%d)", GetPlayerBPID(), GetPlayerAPID());

#ifdef ENABLE_WS_TOURNAMENT
				CWSTournamentManager::instance().OnArenaMatchEnd(m_dwPIDB, m_dwPIDA);
#endif
			}
			else
			{
				restart = true;
				pCharA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s 님이 승리하였습니다."), pCharB->GetName());
				pCharA->ChatPacket(CHAT_TYPE_NOTICE, "%s %d : %d %s", pCharA->GetName(), m_dwSetPointOfA, m_dwSetPointOfB, pCharB->GetName());

				pCharB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s 님이 승리하였습니다."), pCharB->GetName());
				pCharB->ChatPacket(CHAT_TYPE_NOTICE, "%s %d : %d %s", pCharA->GetName(), m_dwSetPointOfA, m_dwSetPointOfB, pCharB->GetName());

				SendChatPacketToObserver(CHAT_TYPE_NOTICE, "%s %d : %d %s", pCharA->GetName(), m_dwSetPointOfA, m_dwSetPointOfB, pCharB->GetName());

				sys_log(0, "ARENA : PID(%d) won a round. Opp(%d)", GetPlayerBPID(), GetPlayerAPID());
			}
		}
		else
		{
			// wtf
			sys_log(0, "ARENA : OnDead Error (%d, %d) (%d, %d)", m_dwPIDA, m_dwPIDB, dwPIDA, dwPIDB);
		}

		const int potion = quest::CQuestManager::instance().GetEventFlag("arena_potion_limit_count");
		pCharA->SetPotionLimit(potion);
		pCharB->SetPotionLimit(potion);
	}
	else
	{
	}

	if (restart == false)
	{
		if (pCharA != nullptr)
			pCharA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("10초뒤 마을로 되돌아갑니다."));

		if (	pCharB != nullptr)
			pCharB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("10초뒤 마을로 되돌아갑니다."));

		SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("10초뒤 마을로 되돌아갑니다."));

		if (m_pEvent != nullptr) {
			event_cancel(&m_pEvent);
		}

		TArenaEventInfo* info = AllocEventInfo<TArenaEventInfo>();

		info->pArena = this;
		info->state = 2;

		m_pEvent = event_create(ready_to_start_event, info, PASSES_PER_SEC(10));
	}
	else
	{
		if (pCharA != nullptr)
			pCharA->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("10초뒤 다음 판을 시작합니다."));

		if (pCharB != nullptr)
			pCharB->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("10초뒤 다음 판을 시작합니다."));

		SendChatPacketToObserver(CHAT_TYPE_INFO, LC_TEXT("10초뒤 다음 판을 시작합니다."));

		if (m_pEvent != nullptr) {
			event_cancel(&m_pEvent);
		}

		TArenaEventInfo* info = AllocEventInfo<TArenaEventInfo>();

		info->pArena = this;
		info->state = 3;

		m_pEvent = event_create(ready_to_start_event, info, PASSES_PER_SEC(10));
	}

	return true;
}

bool CArenaManager::AddObserver(LPCHARACTER pChar, DWORD mapIdx, WORD ObserverX, WORD ObserverY)
{
	auto iter = m_mapArenaMap.find(mapIdx);
	if (iter == m_mapArenaMap.end()) return false;

	auto * pArenaMap = iter->second;
	return pArenaMap->AddObserver(pChar, ObserverX, ObserverY);
}

bool CArenaMap::AddObserver(LPCHARACTER pChar, WORD ObserverX, WORD ObserverY)
{
	for (auto & pArena : m_listArena)
	{
		if (pArena->IsMyObserver(ObserverX, ObserverY) == true)
		{
			pChar->SetArena(pArena);
			return pArena->AddObserver(pChar);
		}
	}

	return false;
}

bool CArena::IsMyObserver(WORD ObserverX, WORD ObserverY) const
{
	return ((ObserverX == m_ObserverPoint.x) && (ObserverY == m_ObserverPoint.y));
}

bool CArena::AddObserver(LPCHARACTER pChar)
{
	DWORD pid = pChar->GetPlayerID();

	m_mapObserver.emplace(pid, (LPCHARACTER)nullptr);

	pChar->SaveExitLocation();
	pChar->WarpSet(m_ObserverPoint.x * 100, m_ObserverPoint.y * 100);

	return true;
}

bool CArenaManager::IsArenaMap(DWORD dwMapIndex)
{
	return m_mapArenaMap.contains(dwMapIndex);
}

MEMBER_IDENTITY CArenaManager::IsMember(DWORD dwMapIndex, DWORD PID)
{
	auto iter = m_mapArenaMap.find(dwMapIndex);

	if (iter != m_mapArenaMap.end())
	{
		auto * pArenaMap = iter->second;
		return pArenaMap->IsMember(PID);
	}

	return MEMBER_NO;
}

MEMBER_IDENTITY CArenaMap::IsMember(DWORD PID)
{
	for (auto & pArena : m_listArena)
	{
		if (pArena->IsObserver(PID) == true) return MEMBER_OBSERVER;
		if (pArena->IsMember(PID) == true) return MEMBER_DUELIST;
	}
	return MEMBER_NO;
}

bool CArena::IsObserver(DWORD PID)
{
	auto iter = m_mapObserver.find(PID);
	return iter != m_mapObserver.end();
}

void CArena::OnDisconnect(DWORD pid)
{
#ifdef ENABLE_WS_TOURNAMENT
	// turnuva maci: yerinde duraklat (arena kapatilmaz, rakip ringde bekler, kopan donunce devam)
	if ((m_dwPIDA == pid || m_dwPIDB == pid)
			&& CWSTournamentManager::instance().OnArenaPlayerDisconnect(m_dwPIDA, m_dwPIDB, pid))
		return;
#endif
	if (m_dwPIDA == pid)
	{
		if (GetPlayerB() != nullptr)
			GetPlayerB()->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("상대방 캐릭터가 접속을 종료하여 대련을 중지합니다."));

		sys_log(0, "ARENA : Duel is end because of Opp(%d) is disconnect. MyPID(%d)", GetPlayerAPID(), GetPlayerBPID());

		EndDuel();
	}
	else if (m_dwPIDB == pid)
	{
		if (GetPlayerA() != nullptr)
			GetPlayerA()->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("상대방 캐릭터가 접속을 종료하여 대련을 중지합니다."));

		sys_log(0, "ARENA : Duel is end because of Opp(%d) is disconnect. MyPID(%d)", GetPlayerBPID(), GetPlayerAPID());

		EndDuel();
	}
}

void CArena::RemoveObserver(DWORD pid)
{
	auto iter = m_mapObserver.find(pid);

	if (iter != m_mapObserver.end())
		m_mapObserver.erase(iter);
}

void CArena::SendPacketToObserver(const void * c_pvData, int iSize) const
{
	for (const auto & iter : m_mapObserver)
	{
		const LPCHARACTER pChar = CHARACTER_MANAGER::instance().FindByPID(iter.first);
		if (pChar != nullptr && pChar->GetDesc() != nullptr)
			pChar->GetDesc()->Packet(c_pvData, iSize);
	}
}

void CArena::SendChatPacketToObserver(BYTE type, const char * format, ...) const
{
	char szBuf[CHAT_MAX_LEN + 1];

	va_list args;
	va_start(args, format);
	vsnprintf(szBuf, sizeof(szBuf), format, args);
	va_end(args);

	for (const auto & iter : m_mapObserver)
	{
		const LPCHARACTER pChar = CHARACTER_MANAGER::instance().FindByPID(iter.first);
		if (pChar != nullptr)
			pChar->ChatPacket(type, "%s", szBuf);
	}
}

bool CArenaManager::EndDuel(DWORD pid)
{
	for (auto & iter : m_mapArenaMap)
	{
		auto * pArenaMap = iter.second;
		if (pArenaMap->EndDuel(pid) == true) return true;
	}
	return false;
}

bool CArenaMap::EndDuel(DWORD pid)
{
	for (auto & pArena : m_listArena)
	{
		if (pArena->IsMember(pid) == true)
		{
			pArena->EndDuel();
			return true;
		}
	}
	return false;
}

bool CArenaManager::RegisterObserverPtr(LPCHARACTER pChar, DWORD mapIdx, WORD ObserverX, WORD ObserverY)
{
	if (pChar == nullptr) return false;

	auto iter = m_mapArenaMap.find(mapIdx);
	if (iter == m_mapArenaMap.end())
	{
		sys_log(0, "ARENA : Cannot find ArenaMap. %d %d %d", mapIdx, ObserverX, ObserverY);
		return false;
	}

	auto * pArenaMap = iter->second;
	return pArenaMap->RegisterObserverPtr(pChar, mapIdx, ObserverX, ObserverY);
}

bool CArenaMap::RegisterObserverPtr(LPCHARACTER pChar, DWORD mapIdx, WORD ObserverX, WORD ObserverY)
{
	for (auto & pArena : m_listArena)
	{
		if (pArena->IsMyObserver(ObserverX, ObserverY) == true)
			return pArena->RegisterObserverPtr(pChar);
	}

	return false;
}

bool CArena::RegisterObserverPtr(LPCHARACTER pChar)
{
	const DWORD pid = pChar->GetPlayerID();
	auto iter = m_mapObserver.find(pid);

	if (iter == m_mapObserver.end())
	{
		sys_log(0, "ARENA : not in ob list");
		return false;
	}

	m_mapObserver[pid] = pChar;
	return true;
}

#ifdef ENABLE_WS_TOURNAMENT
int CArenaManager::GetArenaCount(DWORD dwMapIndex)
{
	auto iter = m_mapArenaMap.find(dwMapIndex);
	if (iter == m_mapArenaMap.end())
		return 0;

	return (int) iter->second->m_listArena.size();
}

bool CArenaManager::WSPauseDuel(DWORD dwPID)
{
	for (auto & iter : m_mapArenaMap)
		for (auto & pArena : iter.second->m_listArena)
			if (pArena->WSPauseIfMember(dwPID))
				return true;
	return false;
}

bool CArenaManager::WSResumeDuel(DWORD dwPID, int iRemainSec)
{
	for (auto & iter : m_mapArenaMap)
		for (auto & pArena : iter.second->m_listArena)
			if (pArena->WSResumeDuelIfMember(dwPID, iRemainSec))
				return true;
	return false;
}

bool CArenaManager::WSSendDuelStart(DWORD dwPID)
{
	for (auto & iter : m_mapArenaMap)
		for (auto & pArena : iter.second->m_listArena)
			if (pArena->WSSendDuelStartIfMember(dwPID))
				return true;
	return false;
}

bool CArenaManager::WSRestoreSetPoints(DWORD dwPID, DWORD dwOwnPoints, DWORD dwOppPoints)
{
	for (auto & iter : m_mapArenaMap)
	{
		for (auto & pArena : iter.second->m_listArena)
		{
			if (pArena->WSRestoreSetPoints(dwPID, dwOwnPoints, dwOppPoints))
				return true;
		}
	}
	return false;
}

bool CArenaManager::GetObserverPoint(DWORD dwMapIndex, WORD & wX, WORD & wY)
{
	auto iter = m_mapArenaMap.find(dwMapIndex);
	if (iter == m_mapArenaMap.end() || iter->second->m_listArena.empty())
		return false;

	const CArena * pArena = iter->second->m_listArena.front();
	wX = (WORD) pArena->GetObserverPoint().x;
	wY = (WORD) pArena->GetObserverPoint().y;
	return true;
}
#endif

// #ifdef ENABLE_NEWSTUFF
bool IsAllowedPotionOnPVP(DWORD dwVnum)
{
	switch (dwVnum)
	{
		// blue potions
		case 27004:
		case 27005:
		case 27006:
		// auto blue potions
		case 39040:
		case 39041:
		case 39042:
		case 72727:
		case 72728:
		case 72729:
		case 72730:
			return true;
	}
	return false;
}

bool IsLimitedPotionOnPVP(DWORD dwVnum)
{
	return IsLimitedPotion(dwVnum) && !IsAllowedPotionOnPVP(dwVnum);
}

bool IsLimitedPotion(DWORD dwVnum)
{
	// @fixme122
	if ((50801 <= dwVnum) && (dwVnum <= 50826))
		return true;

	// @warme005
	switch (dwVnum)
	{
		case 50020:
		case 50021:
		case 50022:
		case 50801:
		case 50802:
		case 50813:
		case 50814:
		case 50817:
		case 50818:
		case 50819:
		case 50820:
		case 50821:
		case 50822:
		case 50823:
		case 50824:
		case 50825:
		case 50826:
		case 71044:
		case 71055:
			return true;
	}
	return false;
}
// #endif

bool CArenaManager::IsLimitedItem(long lMapIndex, DWORD dwVnum)
{
	if (IsArenaMap(lMapIndex) && IsLimitedPotion(dwVnum))
		return true;

	return false;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
