#pragma once

#include "../../common/CommonDefines.h"

#ifdef ENABLE_PHANTOM_METIN_TRAP

#include "typedef.h"

// Phantom metin tuzagi (sahte tas honeypot, tar-pit):
// Her tas kesiminde (SADECE seviye 16 ve alti karakterlerde) katile unicast edilir:
// GERCEK tas vnum'u (8003 veya 8007, kesilen tasa gore) + bType=STONE + BOS affect bayraklari ile sahte bir
// CHARACTER_ADD paketi gonderilir: phantom pakette gercek bir tastan AYIRT EDILEMEZ.
// NOT: gorunmezlik biti KALDIRILDI (wire'da goruluyordu + taslarda STONE_SMOKE2 ile
// ayni bit oldugu icin duman aciyordu) -> insan oyuncu da tasi GORUR, bu yuzden
// enforce yalniz gozlem log'u temiz cikinca acilmali.
// Tas ASLA olmez: vurana sahte hasar/HP% paketi gonderilir (HP %1 tabanina iner), boylece
// bot oyalanip vurmaya devam eder; vuruldukca kaybolmaz (omru her vuruSta tazelenir).
// HIC saldirilmazsa 10sn sonra kaybolur (mesru oyuncuda isim/efekt artigi kisa kalsin).
// Tespit olcutu: oyuncunun phantom'lara harcadigi KUMULATIF AKTIF saldiri suresi
// (c_iSustainLogSec=75sn; zincir halkalari boyunca tasinir) -> phantom_trap.log + sys_err.
// Enforce (/phantom_trap_enforce) ACIKsa esik asilinca account BLOCK + aninda DC.
// Ana anahtar: /phantom_trap, CONFIG: phantom_trap / phantom_trap_enforce.

// Tas oldugunde tetikleyici (char_battle.cpp CHARACTER::Dead icinden cagrilir).
void PhantomTrap_OnStoneKilled(LPCHARACTER pkStone, LPCHARACTER pkKiller);

// Client'tan hedef VID tasiyan paketlerde CHARACTER_MANAGER::Find'dan ONCE cagrilir.
// dwVID kayitli bir phantom'a aitse loglar/cezalandirir ve true doner (paket yutulur).
bool PhantomTrap_CheckHit(LPCHARACTER ch, DWORD dwVID, const char* c_pszPacket);

#endif
