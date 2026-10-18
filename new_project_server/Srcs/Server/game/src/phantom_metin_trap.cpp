#include "stdafx.h"
#include "../../common/CommonDefines.h"

#ifdef ENABLE_PHANTOM_METIN_TRAP

#include "constants.h"
#include "config.h"
#include "utils.h"
#include "../../common/tables.h"
#include "packet.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "desc_manager.h"
#include "sectree_manager.h"
#include "event.h"
#include "db.h"
#include "phantom_metin_trap.h"

#include <cmath>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <map>

namespace
{
	// GERCEK tas vnum'u (client pack'te VAR): bot hem vnum hem "tas mi" (bType) kontrolu
	// yaptigi icin phantom onun whitelist'ine denk gelmeli -> gercek vnum + bType=STONE sart.
	// Gizleme YOK (bkz. dwAffectFlag notu): phantom pakette gercek bir tastan ayirt edilemez,
	// bedeli insan oyuncunun da onu gormesidir. SADECE katile unicast edilir; client src'ye
	// DOKUNULMAZ. Birden fazla gercek metin vnum'u eklenebilir (dizi genisletilir).
	// 8007 (metinstone_07, mob_proto seviye 35) 2026-09-29'da eklendi. Tuzak YALNIZ bu
	// listedeki bir tas kesilince tetiklenir ve phantom kesilen tasla AYNI vnum'u tasir.
	const DWORD c_adwPhantomStoneVnums[] = { 8003, 8007 };

	// Tar-pit omru: tas OLMEZ. Vuruldukca yasar; vurus kesilince kisa sure sonra silinir.
	const int c_iFirstExpireSec    = 10;   // HIC saldirilmazsa tam bu surede kaybolur (mesru
	                                       // oyuncu tasi en fazla 10sn gorur, sonra silinir)
	const int c_iPollSec           = 5;    // yasarken expire-eventi yeniden kurma araligi
	const int c_iIdleRemoveSec     = 10;   // son etkilesimden beri bu kadar gecerse "birakildi" -> sil
	const int c_iHardMaxSec        = 600;  // mutlak tavan: surekli vurulsa bile 10 dk sonra biter (sonsuz-omur sigortasi)
	const int c_iGraceSec          = 30;   // silindikten sonra kayit bu kadar kalir (gec gelen vuruslari da yakala)

	// Tespit olcutu: AYNI phantom tasa kesintisiz SALDIRI suresi.
	// KRITIK: bu deger c_iHpDrainSec'ten KUCUK olmali; yoksa esigi gecmeden once sahte can
	// tabana oturur, bot "can azalmiyor" deyip birakir ve tespit hic tetiklenmez.
	const int c_iSustainLogSec     = 75;

	// Hedef kitle: phantom SADECE bu seviye ve altindaki karakterlerde uretilir.
	// Ust seviyeler hic test edilmez -> FP yuzeyi ve gorsel artik cok daralir.
	const int c_iMaxTargetLevel    = 35;	// 2026-09-29: 16->35 (8007/a3-b3 bolgesini kapsasin)

	// Emniyet: vnum yanlislikla client-pack'e girerse kitlesel ban'i onleyen saatlik tavan.
	const int c_iMaxBansPerHour    = 20;
	// Sweep'i her tas kesiminde degil en fazla bu araliklarla calistir (throughput).
	const int c_iSweepIntervalSec  = 30;

	// Sahte can: tas ASLA olmez; HP ZAMANA bagli iner ve %1 tabanina oturur.
	// Vurus sayisina degil zamana bagli: saldiri hizi (sinif/buf/beceri) egriyi bozmasin.
	// c_iHpDrainSec gercek 8003 kesim suresine (~70-90sn) esitlenir ki bot farki anlamasin.
	const int c_iHpStartPct        = 100;
	const int c_iHpFloorPct        = 1;
	const int c_iHpDrainSec        = 90;	// 100% -> 1% tam bu surede iner

	// Dovus tiki: saldiri surerken saniyede bir HP% guncellemesi.
	const int c_iCombatTickSec     = 1;
	// NOT: "tas oyuncuya hasar versin" fikri KALDIRILDI - bu server'da gercek metin taslari
	// saldirana ASLA hasar vermez (char_battle.cpp'de boyle bir yol yok), dolayisiyla
	// tastan gelen hasar paketi binary'de baska hicbir yerde olmayan bir sinyal = botu
	// dogrudan uyaran mukemmel bir ayrac olurdu. Gercek HP dususu de regen'in altinda
	// kaldigi icin degersizdi ve PointChange yayini ucuncu sahislara tuzagi sizdiriyordu.

	// Bot birakirsa yeni phantom ile dongude tut; kacak bir zincir olmasin diye tavan.
	// Inceleme: 20 cok yuksekti (mesru oyuncuda artik suresini 20x uzatiyordu) -> 3.
	const int c_iMaxChainSpawns    = 3;
	// Ayni oyuncuya ayni anda birden fazla phantom verilmez (paket amplifikasyonu onlemi).
	const int c_iMaxLivePerPlayer  = 1;
	// Tik sadece GERCEKTEN saldiri surerken calissin (bos tik = parmak izi).
	const int c_iTickActiveMs      = 2500;
	// Aktif saldiri sayacina eklenecek maksimum tek adim (ara verirse sure sayilmasin).
	const DWORD c_dwActiveStepCapMs = 3000;
	// Saldirgan istatistigi bu kadar sessizlikten sonra dusurulur (sayac sifirlanir).
	const DWORD c_dwAttackerStatTtlMs = 1800000;	// 30 dk

	// Yerlesim: melee suprumesi 300, splash 1000 birim (client analizi) -> disinda kaliyoruz.
	// Stok client zaten instance etmez; bu bant sadece inandiricilik + savunma derinligi.
	const int c_iSpawnDistMin      = 1500;
	const int c_iSpawnDistMax      = 3500;

	struct SPhantomStone
	{
		DWORD	dwVID;
		DWORD	dwVnum;
		long	lMapIndex;
		long	x, y;
		DWORD	dwSpawnTime;	// get_dword_time (ms)
		DWORD	dwKillerPID;
		DWORD	dwAttackerPID;	// phantom'a ILK saldiran PID; sustain/ban YALNIZ buna atfedilir
		int		iHpPct;			// sahte can yuzdesi (100 -> 1 tabani)
		DWORD	dwFirstHitMs;	// ilk SALDIRI zamani (0 = hic saldirilmadi)
		DWORD	dwLastHitMs;	// son etkilesim zamani (tar-pit keepalive)
		DWORD	dwHitCount;		// saldiri sayisi (log zenginligi)
		DWORD	dwActiveMs;		// bu phantom'a harcanan AKTIF saldiri suresi (can egrisi)
		DWORD	dwLastAttackMs;	// son SALDIRI paketi (aktif sure adimi icin)
		int		iLastSentHpPct;	// client'a EN SON gonderilen HP% (gereksiz paket gonderme)
		int		iChainCount;	// bu phantom kacinci zincir halkasi (dongu tavani)
		bool	bFlagged;		// surekli-saldiri esigi asildi, log dusuldu (tekrar log/ban yok)
		bool	bExpired;		// silindi, grace penceresinde

		SPhantomStone()
			: dwVID(0), dwVnum(0), lMapIndex(0), x(0), y(0),
			  dwSpawnTime(0), dwKillerPID(0), dwAttackerPID(0), iHpPct(c_iHpStartPct),
			  dwFirstHitMs(0), dwLastHitMs(0), dwHitCount(0), dwActiveMs(0), dwLastAttackMs(0),
			  iLastSentHpPct(c_iHpStartPct), iChainCount(0),
			  bFlagged(false), bExpired(false)
		{
		}
	};

	// PID bazli saldirgan durumu: tespit sayaci ZINCIR BOYUNCA TASINIR (yoksa bot her
	// halkada sifirdan baslar ve 75sn esigine hic ulasmadan sonsuza dek oyalanir) ve ayni
	// oyuncuya ayni anda birden fazla phantom verilmez (paket amplifikasyonu onlemi).
	struct SAttackerStat
	{
		DWORD	dwActiveMs;		// kumulatif AKTIF saldiri suresi (tum phantom'lar)
		DWORD	dwLastSeenMs;	// son etkilesim (temizlik icin)
		int		iLive;			// su an canli phantom sayisi
		int		iChain;			// zincir halkasi sayaci
		bool	bFlagged;		// esik asildi + loglandi (tekrar log/ban yok)

		SAttackerStat() : dwActiveMs(0), dwLastSeenMs(0), iLive(0), iChain(0), bFlagged(false) {}
	};

	std::map<DWORD, SAttackerStat> s_mapAttackers;		// PID -> saldirgan durumu
	std::map<DWORD, SPhantomStone> s_mapPhantoms;		// phantom VID -> kayit

	// Phantom silinirken sahibinin canli-phantom sayacini birak.
	void ReleasePhantomSlot(const SPhantomStone& rPh)
	{
		if (rPh.dwKillerPID == 0)
			return;
		std::map<DWORD, SAttackerStat>::iterator itA = s_mapAttackers.find(rPh.dwKillerPID);
		if (itA != s_mapAttackers.end() && itA->second.iLive > 0)
			--itA->second.iLive;
	}
	DWORD s_dwLastSweepSec      = 0;	// son sweep zamani (saniye) - throughput icin seyreklestirme
	DWORD s_dwBanWindowStartSec = 0;	// saatlik ban penceresi baslangici
	int   s_iBansInWindow       = 0;	// bu pencerede uygulanan ban sayisi

	void PhantomTrapLog(const char* c_pszFormat, ...)
	{
		FILE* fp = fopen("phantom_trap.log", "a");
		if (!fp)
			return;

		const time_t ct = time(0);
		struct tm tmNow = *localtime(&ct);
		char szTime[32];
		strftime(szTime, sizeof(szTime), "%Y-%m-%d %H:%M:%S", &tmNow);
		fprintf(fp, "[%s] ", szTime);

		va_list args;
		va_start(args, c_pszFormat);
		vfprintf(fp, c_pszFormat, args);
		va_end(args);

		fprintf(fp, "\n");
		fclose(fp);
	}

	// item_pickup_auth.cpp BlockItemPickupAccount'un sertlestirilmis kopyasi
	// (SQL errno + affected-rows dogrulamali account BLOCK).
	bool BlockPhantomTrapAccount(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc())
			return false;

		const LPDESC desc = ch->GetDesc();
		const char* login = desc->GetAccountTable().login;
		const size_t loginLength = strnlen(login, LOGIN_MAX_LEN);
		if (loginLength == 0)
		{
			sys_err("PHANTOM_TRAP_ACCOUNT_BLOCK missing login aid=%u player=%s ip=%s",
				desc->GetAccountTable().id, ch->GetName(), desc->GetHostName());
			return false;
		}

		char escapedLogin[LOGIN_MAX_LEN * 2 + 1]{};
		DBManager::instance().EscapeString(escapedLogin, sizeof(escapedLogin), login, loginLength);

		const auto result = DBManager::instance().DirectQuery(
			"UPDATE account.account SET status = 'BLOCK' WHERE login = '%s'",
			escapedLogin);

		if (!result || result->uiSQLErrno != 0 || !result->Get() ||
			result->Get()->uiAffectedRows == static_cast<std::uint32_t>(-1))
		{
			sys_err("PHANTOM_TRAP_ACCOUNT_BLOCK failed login=%s aid=%u player=%s ip=%s sql_errno=%u",
				login, desc->GetAccountTable().id, ch->GetName(), desc->GetHostName(),
				result ? result->uiSQLErrno : 0U);
			return false;
		}

		sys_err("PHANTOM_TRAP_ACCOUNT_BLOCK applied login=%s aid=%u player=%s ip=%s affected_rows=%u",
			login, desc->GetAccountTable().id, ch->GetName(), desc->GetHostName(),
			static_cast<unsigned int>(result->Get()->uiAffectedRows));
		return true;
	}

	// Phantom DEL paketini SADECE katile gonder (ADD da yalniz ona unicast edilmisti;
	// baska kimse bu VID'i bilmiyor). Katil cevrimdisi/warp ise onun client'i zaten yok.
	void SendPhantomDeleteToKiller(const SPhantomStone& rPh)
	{
		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(rPh.dwKillerPID);
		if (!ch || !ch->GetDesc())
			return;

		TPacketGCCharacterDelete pack;
		pack.header = HEADER_GC_CHARACTER_DEL;
		pack.id = rPh.dwVID;
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	// AKTIF saldiri suresine bagli sahte can: c_iHpDrainSec boyunca 100% -> 1%.
	// Gecen takvim suresi DEGIL aktif dovus suresi kullanilir; yoksa bot vurmayi kesti
	// halde can inmeye devam eder ve bu, degistirdigimiz hatadan daha bariz bir ipucu olur.
	int ComputePhantomHpPct(const SPhantomStone& rPh)
	{
		const DWORD dwDrainMs = (DWORD)c_iHpDrainSec * 1000;
		if (rPh.dwActiveMs >= dwDrainMs)
			return c_iHpFloorPct;

		const DWORD dwSpan = (DWORD)(c_iHpStartPct - c_iHpFloorPct);
		return c_iHpStartPct - (int)((dwSpan * rPh.dwActiveMs) / dwDrainMs);
	}

	// Hedef HP% (GC_TARGET). Gercek server bunu HP her degistiginde yollar; biz de yalniz
	// deger DEGISTIYSE yolluyoruz (gereksiz paket = parmak izi).
	void SendPhantomHp(LPCHARACTER ch, SPhantomStone& rPh, bool bForce)
	{
		LPDESC d = ch->GetDesc();
		if (!d)
			return;

		if (!bForce && rPh.iHpPct == rPh.iLastSentHpPct)
			return;

		TPacketGCTarget tp;
		tp.header = HEADER_GC_TARGET;
		tp.dwVID = rPh.dwVID;
		tp.bHPPercent = (BYTE) rPh.iHpPct;
		d->Packet(&tp, sizeof(tp));
		rPh.iLastSentHpPct = rPh.iHpPct;
	}

	// Oyuncunun TASA vurdugu hasar sayisi (dwVID = tasin VID'i).
	// Sayi SALDIRGANIN gucunden turetilir: sabit 800-4000 bandi dusuk seviye bir karakterin
	// gercekte vurabilecegi degerin 10-100 katiydi ve tek basina en ucuz ele-veren ipucuydu.
	void SendPhantomHitNumber(LPCHARACTER ch, const SPhantomStone& rPh)
	{
		LPDESC d = ch->GetDesc();
		if (!d)
			return;

		int iBase = ch->GetPoint(POINT_ATT_GRADE);
		if (iBase < 10)
			iBase = 10 + ch->GetLevel() * 2;	// emniyet: proto/stat yoksa seviyeye gore

		const int iLow  = (iBase * 60) / 100;
		const int iHigh = (iBase * 140) / 100;

		TPacketGCDamageInfo dp;
		dp.header = HEADER_GC_DAMAGE_INFO;
		dp.dwVID = rPh.dwVID;
		dp.flag = 1;	// DAMAGE_NORMAL
		dp.damage = number(iLow, (iHigh > iLow) ? iHigh : iLow + 1);
		d->Packet(&dp, sizeof(dp));
	}

	// Ileri bildirim: zincir (dongu) spawn'i expire event'inden cagriliyor.
	void SpawnPhantomNear(LPCHARACTER pkKiller, int iChainCount, DWORD dwPreferVnum);
	bool IsPhantomStoneVnum(DWORD dwVnum);

	// Saldiri GERCEKTEN surerken saniyede bir HP% guncellemesi yollar (gercek server da
	// HP degistikce yolluyor). Saldirgan uzaklastiysa/haritayi degistirdiyse/olduyse sus:
	// olmayan bir tasla dovus paketi akmasi baslibasina ipucudur.
	void PhantomCombatTick(SPhantomStone& rPh, DWORD dwNowMs)
	{
		if (rPh.dwAttackerPID == 0)
			return;

		// yalniz son saldiridan hemen sonraki pencerede tik at
		if (rPh.dwLastHitMs == 0 || (dwNowMs - rPh.dwLastHitMs) > (DWORD)c_iTickActiveMs)
			return;

		LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(rPh.dwAttackerPID);
		if (!ch || !ch->GetDesc() || ch->IsDead() || ch->IsStun())
			return;

		if (ch->GetMapIndex() != rPh.lMapIndex || ch->GetDungeon())
			return;

		if (DISTANCE_APPROX((int)(ch->GetX() - rPh.x), (int)(ch->GetY() - rPh.y)) > 5000)
			return;

		rPh.iHpPct = ComputePhantomHpPct(rPh);
		SendPhantomHp(ch, rPh, false);
	}

	// TTL/grace suresi coktan gecmis kayitlari sup (event kaybi ihtimaline karsi emniyet).
	void SweepStalePhantoms()
	{
		const DWORD dwNow = get_dword_time();
		std::map<DWORD, SPhantomStone>::iterator it = s_mapPhantoms.begin();
		while (it != s_mapPhantoms.end())
		{
			// hardMax + 2*grace'ten eski her kayit copluk sayilir
			// (cikarma idiomu: 49.7 gunluk dword-time sarmasina dayanikli)
			if (dwNow - it->second.dwSpawnTime > (DWORD)(c_iHardMaxSec + 2 * c_iGraceSec) * 1000)
			{
				ReleasePhantomSlot(it->second);
				s_mapPhantoms.erase(it++);
			}
			else
				++it;
		}

		// Saldirgan istatistikleri de sonsuza dek birikmesin: canli phantom'u olmayan ve
		// uzun suredir sessiz kayitlar dusurulur (tespit sayaci da boylece sifirlanir).
		std::map<DWORD, SAttackerStat>::iterator itA = s_mapAttackers.begin();
		while (itA != s_mapAttackers.end())
		{
			if (itA->second.iLive <= 0 &&
				(dwNow - itA->second.dwLastSeenMs) > (DWORD)c_dwAttackerStatTtlMs)
				s_mapAttackers.erase(itA++);
			else
				++itA;
		}
	}

	EVENTINFO(phantom_expire_info)
	{
		DWORD dwVID;
		bool bGraceDone;

		phantom_expire_info() : dwVID(0), bGraceDone(false) {}
	};

	EVENTFUNC(phantom_expire_event)
	{
		phantom_expire_info* info = dynamic_cast<phantom_expire_info*>(event->info);
		if (info == NULL)
			return 0;

		std::map<DWORD, SPhantomStone>::iterator it = s_mapPhantoms.find(info->dwVID);
		if (it == s_mapPhantoms.end())
			return 0;

		SPhantomStone& rPh = it->second;
		const DWORD dwNow = get_dword_time();

		if (!info->bGraceDone)
		{
			// Hic etkilesim yoksa ilk kontrolde (c_iFirstExpireSec) KESIN sil: boylece mesru
			// oyuncunun gordugu isim/efekt artigi tam 10sn ile sinirli kalir (zamanlama
			// jitter'ina bagli degil). Vurulduysa tar-pit: son vurustan c_iIdleRemoveSec gecene dek yasar.
			const bool bRecentlyHit = (rPh.dwLastHitMs != 0) &&
				((dwNow - rPh.dwLastHitMs) < (DWORD)(c_iIdleRemoveSec * 1000));
			const bool bUnderHardCap = (dwNow - rPh.dwSpawnTime) < (DWORD)(c_iHardMaxSec * 1000);

			// Tar-pit: vurulmaya devam ediyorsa yasat (olmez, kaybolmaz) ve saldiri
			// suruyorsa saniyelik dovus tiki ile can egrisini ilerlet + hasar hissi ver.
			if (bRecentlyHit && bUnderHardCap)
			{
				if (rPh.dwAttackerPID != 0)
				{
					PhantomCombatTick(rPh, dwNow);
					return PASSES_PER_SEC(c_iCombatTickSec);
				}
				return PASSES_PER_SEC(c_iPollSec);
			}

			// Artik vurulmuyor (ya da tavan asildi): katile DEL gonder, grace'e gec
			rPh.bExpired = true;
			SendPhantomDeleteToKiller(rPh);

			// DONGU (kullanici karari): saldirmis olan biri birakirsa hemen yeni bir
			// phantom ver ki bot bos kalmasin. Kacak zinciri onlemek icin tavanli.
			// Hard-cap dalinda (10dk dolmus) ZINCIRLEME YOK: o zaten patolojik bir durum.
			const DWORD dwChainPID = bUnderHardCap ? rPh.dwAttackerPID : 0;
			const int   iNextChain = rPh.iChainCount + 1;
			const DWORD dwChainVnum = rPh.dwVnum;	// zincir halkasi ayni vnum'la devam eder

			info->bGraceDone = true;

			// NOT: bundan sonra rPh'ye DOKUNMA - SpawnPhantomNear haritaya ekleme yapar.
			if (g_bPhantomTrap && dwChainPID != 0 && iNextChain <= c_iMaxChainSpawns)
			{
				LPCHARACTER chAtk = CHARACTER_MANAGER::instance().FindByPID(dwChainPID);
				if (chAtk && chAtk->GetDesc() && !chAtk->IsDead() &&
					chAtk->GetGMLevel() <= GM_PLAYER &&
					chAtk->GetLevel() <= c_iMaxTargetLevel &&
					!chAtk->GetDungeon() &&
					chAtk->GetMapIndex() < 10000)
				{
					SpawnPhantomNear(chAtk, iNextChain, dwChainVnum);
				}
			}

			return PASSES_PER_SEC(c_iGraceSec);
		}

		ReleasePhantomSlot(rPh);
		s_mapPhantoms.erase(it);
		return 0;
	}

	bool IsPhantomStoneVnum(DWORD dwVnum)
	{
		const int iVnumCount = (int) (sizeof(c_adwPhantomStoneVnums) / sizeof(c_adwPhantomStoneVnums[0]));
		for (int i = 0; i < iVnumCount; ++i)
			if (c_adwPhantomStoneVnums[i] == dwVnum)
				return true;
		return false;
	}

	void SpawnPhantomNear(LPCHARACTER pkKiller, int iChainCount, DWORD dwPreferVnum)
	{
		if (!pkKiller->GetDesc())
			return;	// unicast icin desc sart (cagiran zaten kontrol ediyor; savunma amacli)

		// Yurunebilir kare ara (8 deneme); bulunamazsa bu testi sessizce iptal et
		long x = 0, y = 0;
		bool bFound = false;
		for (int i = 0; i < 8; ++i)
		{
			const float fAngle = (float) number(0, 359) * 3.14159265f / 180.0f;
			const int iDist = number(c_iSpawnDistMin, c_iSpawnDistMax);
			x = pkKiller->GetX() + (long) (cosf(fAngle) * (float) iDist);
			y = pkKiller->GetY() + (long) (sinf(fAngle) * (float) iDist);

			if (SECTREE_MANAGER::instance().IsMovablePosition(pkKiller->GetMapIndex(), x, y))
			{
				bFound = true;
				break;
			}
		}

		if (!bFound)
			return;

		// Sweep'i seyreklestir: per-phantom expire event'leri zaten temizliyor, bu yalnizca
		// kayip-event backstop'u. Her tas kesiminde O(n) taramayi onle.
		// SIRA ONEMLI: sweep s_mapAttackers'tan kayit silebilir, bu yuzden asagidaki
		// SAttackerStat referansi sweep'ten SONRA alinir (aksi halde dangling referans).
		const DWORD dwNowSec = (DWORD) get_global_time();
		if (dwNowSec - s_dwLastSweepSec >= (DWORD) c_iSweepIntervalSec)
		{
			s_dwLastSweepSec = dwNowSec;
			SweepStalePhantoms();
		}

		// Ayni oyuncuya ayni anda birden fazla phantom verme (paket amplifikasyonu +
		// mesru oyuncuda gorsel artik). Zincir halkasi da burada sayilir.
		SAttackerStat& rStat = s_mapAttackers[pkKiller->GetPlayerID()];
		rStat.dwLastSeenMs = get_dword_time();	// yeni kayitsa hemen taze isaretle
		if (rStat.iLive >= c_iMaxLivePerPlayer)
			return;

		// Phantom VID'i GERCEK AllocVID'den: wire'da gercek bir varlik VID'inden AYIRT
		// EDILEMEZ (monoton, asla tekrar kullanilmaz -> carpisma yok, out-of-band imza yok).
		// Kayit edilmez; hook zaten Find'dan once yakalar, Find null doner.
		const DWORD dwVID = CHARACTER_MANAGER::instance().AllocVID();
		const int iVnumCount = (int) (sizeof(c_adwPhantomStoneVnums) / sizeof(c_adwPhantomStoneVnums[0]));
		// Phantom = kesilen tasla AYNI vnum (cagiran listede oldugunu garanti eder);
		// savunma amacli: listede degilse rastgele bir liste uyesi.
		DWORD dwVnum = IsPhantomStoneVnum(dwPreferVnum)
			? dwPreferVnum
			: c_adwPhantomStoneVnums[number(0, iVnumCount - 1)];

		TPacketGCCharacterAdd pack;
		memset(&pack, 0, sizeof(pack));
		pack.header = HEADER_GC_CHARACTER_ADD;
		pack.dwVID = dwVID;
		pack.angle = 0.0f;
		pack.x = x;
		pack.y = y;
		pack.z = 0;
		pack.bType = CHAR_TYPE_STONE;	// bot "tas mi" (bType) diye de baktigi icin STONE kalir
		pack.wRaceNum = dwVnum;
		pack.bMovingSpeed = 100;
		pack.bAttackSpeed = 100;
		pack.bStateFlag = 0;
		// AFFECT BAYRAKLARI BOS = TAM NORMAL TAS (kullanici karari 2026-09-12).
		// Onceki surumde AFF_INVISIBILITY (0x02) set ediliyordu; iki nedenle kaldirildi:
		//  1) Wire'da goruluyordu: gercek bir tas %100 canda hicbir affect biti tasimaz,
		//     dolayisiyla 0x02 botun bakabilecegi en temiz ipucuydu.
		//  2) Taslarda bit 1 ayni zamanda STONE_SMOKE2 (InstanceBase.h:220-228) -> gorunmezlik
		//     bitiyle birlikte istemeden duman-kademe-2 aciliyordu; gercek tasta olmayan
		//     bir duman = ikinci bir parmak izi. Ayni bit oldugu icin ayrilmasi imkansizdi.
		// Sonuc: phantom artik pakette gercek bir 8003 tasindan AYIRT EDILEMEZ.
		// BEDELI: insan oyuncu da onu normal tas gibi GORUR -> enforce'u ancak gozlem
		// log'u temiz cikarsa ac (bkz. phantom_trap.log).
		pack.dwAffectFlag[0] = 0;
		pack.dwAffectFlag[1] = 0;
#ifdef OFFLINE_SHOP
		pack.byIsMyShop = 0;
#endif

		// SADECE KATILE unicast (PacketAround DEGIL): gercek(8003)+gorunmez tas client'ta
		// INSTANCE edilir; alana yayilsa cevredeki HERKESTE gorunmez-duvar (carpisma) +
		// oto-tarama FP'si olurdu. Unicast ile (a) yan etki test edilen tek oturumla sinirli,
		// (b) VID yalniz katilde bulunur -> atif kusursuz (bu VID'i baska kimse bilmez/vuramaz).
		// Bedeli: iki-hesap paket-diff karsilastirmasi bota ipucu verebilir (kabul edildi).
		pkKiller->GetDesc()->Packet(&pack, sizeof(pack));

		SPhantomStone ph;
		ph.dwVID = dwVID;
		ph.dwVnum = dwVnum;
		ph.lMapIndex = pkKiller->GetMapIndex();
		ph.x = x;
		ph.y = y;
		ph.dwSpawnTime = get_dword_time();
		ph.dwKillerPID = pkKiller->GetPlayerID();
		ph.iChainCount = iChainCount;
		s_mapPhantoms[dwVID] = ph;

		++rStat.iLive;
		rStat.iChain = iChainCount;
		rStat.dwLastSeenMs = get_dword_time();

		// Ilk expire: hic saldirilmazsa 10sn sonra kaybolur. Saldirilirsa tar-pit
		// yeniden-kurma ile (c_iPollSec) yasamaya devam eder (bkz. phantom_expire_event).
		phantom_expire_info* einfo = AllocEventInfo<phantom_expire_info>();
		einfo->dwVID = dwVID;
		event_create(phantom_expire_event, einfo, PASSES_PER_SEC(c_iFirstExpireSec));

		// SPAWN her tas kesiminde olur -> canli log'u kirletmesin; sadece test_server'da yaz.
		if (test_server)
			PhantomTrapLog("SPAWN vid=%u vnum=%u map=%ld x=%ld y=%ld pid=%u player=%s",
				dwVID, dwVnum, ph.lMapIndex, x, y, ph.dwKillerPID, pkKiller->GetName());
	}

}

void PhantomTrap_OnStoneKilled(LPCHARACTER pkStone, LPCHARACTER pkKiller)
{
	if (!g_bPhantomTrap)
		return;

	if (!pkStone || !pkKiller || !pkKiller->IsPC() || !pkKiller->GetDesc())
		return;

	if (pkKiller->GetGMLevel() > GM_PLAYER)
		return;		// GM'ler test edilmez

	if (pkKiller->GetLevel() > c_iMaxTargetLevel)
		return;		// kullanici karari: yalniz 35 ve alti seviyeler test edilir

	if (pkKiller->GetDungeon())
		return;		// zindan icinde habersiz tas belirmesi inandirici degil

	if (pkKiller->GetMapIndex() >= 10000)
		return;		// ozel/instance harita kopyalari

	// Kullanici karari (2026-09-29): YALNIZ listedeki taslar (8003/8007) kesilince tetiklenir;
	// diger taslarda phantom uretilmez. Phantom kesilen tasla ayni vnum'dur.
	if (!IsPhantomStoneVnum(pkStone->GetRaceNum()))
		return;

	// Olasilik/cooldown/gecikme YOK - listedeki her tas kesiminde aninda %100 test.
	// Phantom yalniz katile unicast edilir (bkz. SpawnPhantomNear).
	SpawnPhantomNear(pkKiller, 0, pkStone->GetRaceNum());
}

bool PhantomTrap_CheckHit(LPCHARACTER ch, DWORD dwVID, const char* c_pszPacket)
{
	// Sicak yol (her attack/target paketi buradan gecer): once ucuz cikislar
	if (s_mapPhantoms.empty())
		return false;

	if (!g_bPhantomTrap)
		return false;

	if (!ch || !ch->GetDesc())
		return false;

	std::map<DWORD, SPhantomStone>::iterator it = s_mapPhantoms.find(dwVID);
	if (it == s_mapPhantoms.end())
		return false;

	SPhantomStone& rPh = it->second;
	const bool bExpired = rPh.bExpired;	// grace penceresinde: tespit devam ama sahte dovus yok
	const DWORD dwNowMs = get_dword_time();
	const DWORD dwPID = ch->GetPlayerID();

	// Saldiri-tipi paket mi (gercek vurus) yoksa sadece hedefleme mi?
	const bool bAttack =
		(!strcmp(c_pszPacket, "ATTACK") ||
		 !strcmp(c_pszPacket, "USESKILL") ||
		 !strcmp(c_pszPacket, "FLYTARGET"));
	const bool bTargetPkt = (!strcmp(c_pszPacket, "TARGET"));

	// Tar-pit keepalive: phantom'a yonelik her paket omru tazeler (kaybolmaz)
	rPh.dwLastHitMs = dwNowMs;

	// Atif: sustain/ban YALNIZ ilk saldiran PID'e. Boylece ayni phantom'a paket atan
	// baska bir oturum yanlislikla banlanmaz (phantom alan-yayinli, birden fazla bot gorebilir).
	bool bTrackedAttacker = false;
	if (bAttack)
	{
		if (rPh.dwAttackerPID == 0)
		{
			rPh.dwAttackerPID = dwPID;
			rPh.dwFirstHitMs = dwNowMs;
		}
		bTrackedAttacker = (rPh.dwAttackerPID == dwPID);

		if (bTrackedAttacker)
		{
			++rPh.dwHitCount;

			// AKTIF saldiri suresi: iki vurus arasi gecen sure (ara verirse tavanla kirp).
			// Hem can egrisini hem tespit sayacini besler; sayac ZINCIR BOYUNCA tasinir.
			DWORD dwStep = (rPh.dwLastAttackMs != 0) ? (dwNowMs - rPh.dwLastAttackMs) : 0;
			if (dwStep > c_dwActiveStepCapMs)
				dwStep = c_dwActiveStepCapMs;
			rPh.dwLastAttackMs = dwNowMs;
			rPh.dwActiveMs += dwStep;

			SAttackerStat& rStatHit = s_mapAttackers[dwPID];
			rStatHit.dwActiveMs += dwStep;
			rStatHit.dwLastSeenMs = dwNowMs;
		}
	}

	// Sahte can AKTIF saldiri suresine bagli ilerler; saniyelik dovus tiki ayni egriyi kullanir.
	rPh.iHpPct = ComputePhantomHpPct(rPh);

	if (!bExpired)
	{
		// Hedefleme paketinde HP% her zaman gider (SetTarget semantigi); saldirida ise
		// yalniz deger degistiyse. Hasar sayisi her saldirida gider.
		SendPhantomHp(ch, rPh, /*bForce=*/bTargetPkt);
		if (bAttack)
			SendPhantomHitNumber(ch, rPh);
	}

	// Esik: saldirganin phantom'lara harcadigi TOPLAM AKTIF saldiri suresi.
	// Zincir boyunca tasindigi icin "75sn dolmadan birak, yeni tasa gec" taktigi ise yaramaz.
	SAttackerStat& rStat = s_mapAttackers[dwPID];
	const bool bSustained =
		bAttack && bTrackedAttacker &&
		(rStat.dwActiveMs >= (DWORD)(c_iSustainLogSec * 1000));

	if (!bSustained || rStat.bFlagged)
		return true;	// esik yok / zaten loglandi: sessizce yut

	// --- surekli saldiri esigi asildi: ILK ve TEK kez ---
	rStat.bFlagged = true;
	rPh.bFlagged = true;

	const LPDESC desc = ch->GetDesc();
	const DWORD dwSustainSec = rStat.dwActiveMs / 1000;

	sys_err("PHANTOM_TRAP: surekli saldiri esigi asildi vid=%u vnum=%u pid=%u player=%s login=%s ip=%s hits=%u sure=%usn enforce=%d",
		dwVID, rPh.dwVnum, dwPID, ch->GetName(),
		desc->GetAccountTable().login, desc->GetHostName(),
		rPh.dwHitCount, dwSustainSec, g_bPhantomTrapEnforce ? 1 : 0);
	PhantomTrapLog("FLAG vid=%u vnum=%u map=%ld pid=%u player=%s login=%s ip=%s hits=%u sure=%usn enforce=%d",
		dwVID, rPh.dwVnum, rPh.lMapIndex, dwPID, ch->GetName(),
		desc->GetAccountTable().login, desc->GetHostName(),
		rPh.dwHitCount, dwSustainSec, g_bPhantomTrapEnforce ? 1 : 0);

	// GM asla cezalandirilmaz (log yeterli; stok client zaten buraya dusemez)
	if (ch->GetGMLevel() > GM_PLAYER)
		return true;

	if (g_bPhantomTrapEnforce)
	{
		// Emniyet valfi: saatlik ban tavani. vnum yanlislikla client-pack'e girerse
		// bu, kitlesel ban/DC'yi keser (log yine dusulur, ban/DC yapilmaz).
		const DWORD dwNowSec = (DWORD) get_global_time();
		if (dwNowSec - s_dwBanWindowStartSec >= 3600)
		{
			s_dwBanWindowStartSec = dwNowSec;
			s_iBansInWindow = 0;
		}

		if (s_iBansInWindow >= c_iMaxBansPerHour)
		{
			sys_err("PHANTOM_TRAP: ban tavani (%d/saat) doldu, ban ATLANDI pid=%u player=%s",
				c_iMaxBansPerHour, dwPID, ch->GetName());
			PhantomTrapLog("BAN-CAP (%d/saat) doldu - ban/DC atlandi pid=%u player=%s login=%s ip=%s",
				c_iMaxBansPerHour, dwPID, ch->GetName(),
				desc->GetAccountTable().login, desc->GetHostName());
			return true;	// log var, ban/DC YOK (guvenlik valfi)
		}

		++s_iBansInWindow;
		const bool bBlocked = BlockPhantomTrapAccount(ch);
		PhantomTrapLog("BLOCK%s pid=%u player=%s login=%s ip=%s hits=%u sure=%usn",
			bBlocked ? "" : "(SQL-FAIL)", dwPID, ch->GetName(),
			desc->GetAccountTable().login, desc->GetHostName(), rPh.dwHitCount, dwSustainSec);
		desc->SetPhase(PHASE_CLOSE);	// ban sonrasi aninda DC
	}

	return true;	// paket yutulur (Find zaten null donecekti, sessiz kal)
}

#endif
