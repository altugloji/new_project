#ifndef __INC_METIN2_COMMON_DEFINES_H__
#define __INC_METIN2_COMMON_DEFINES_H__
#pragma once

//#define ENABLE_QUEST_CATEGORY
#define ENABLE_NO_MOUNT_CHECK
#define ENABLE_D_NJGUILD
#define ENABLE_FULL_NOTICE
#define ENABLE_NEWSTUFF
#define ENABLE_PORT_SECURITY
// #define ENABLE_BELT_INVENTORY_EX
#define ENABLE_CMD_WARP_IN_DUNGEON
// #define ENABLE_ITEM_ATTR_COSTUME
#define ENABLE_PLAYER_PER_ACCOUNT5
// #define ENABLE_DICE_SYSTEM
#define ENABLE_EXTEND_INVEN_SYSTEM
#define ENABLE_MOUNT_COSTUME_SYSTEM
#define ENABLE_WEAPON_COSTUME_SYSTEM
#define ENABLE_QUEST_DIE_EVENT
#define ENABLE_QUEST_BOOT_EVENT
#define ENABLE_QUEST_DND_EVENT
#define ENABLE_DUNGEON_ELIMINATE_EVENT
#define ENABLE_SKILL_FLAG_PARTY
#define ENABLE_NO_DSS_QUALIFICATION
// #define ENABLE_NO_SELL_PRICE_DIVIDED_BY_5
#define ENABLE_CHECK_SELL_PRICE
#define ENABLE_GOTO_LAG_FIX
#define ENABLE_MOUNT_COSTUME_EX_SYSTEM
// #define ENABLE_PENDANT_SYSTEM
#define ENABLE_GLOVE_SYSTEM // Eldiven altyapisi: item_attr/item_attr_rare 'glove' kolonu + ATTRIBUTE_SET_GLOVE. ONCE src_server/sql/glove_system.sql uygulanmali; db+game BIRLIKTE derlenmeli!
#ifdef ENABLE_GLOVE_SYSTEM
	// Nazar Tilsimi: 71202 her uretildiginde item_attr_rare 'glove' havuzundan prob-agirlikli 5 rastgele efsunla dogar (seviye 1..glove tavani arasi rastgele)
	#define ENABLE_GLOVE_RANDOM_ATTR
	#define GLOVE_RANDOM_ATTR_VNUM		71202
	#define GLOVE_RANDOM_ATTR_COUNT	5
#endif
#define ENABLE_COSTUME_PERMA_AND_REFRESHING // Kostum/tilsim sure uzatma + perma sistemi (itemler 71400-71407; hak sayaci socket2, perma=socket2>=4; GLOVE_RANDOM_ATTR ile 71202 de kapsanir; CreateItem REAL_TIME socket0 guard'i bu define ile geri geldi)
#define ENABLE_MOVE_CHANNEL
// #define ENABLE_QUIVER_SYSTEM
#define ENABLE_REDUCED_ENTITY_VIEW
#define ENABLE_GUILD_TOKEN_AUTH
#define ENABLE_ITEM_AUTOSTACK_EX
#define ENABLE_ITEM_DS_INVENTORY_PROCESS
// #define ENABLE_REGEN_RENEWAL
#define ENABLE_DS_GRADE_MYTH
#define ENABLE_CHANNEL_STATUS_CACHE
#define ENABLE_MESSENGER_REMOVE_SYNC
#define ENABLE_DB_SQL_LOG
#define ENABLE_ITEM_SAFE_FLUSH
#define ENABLE_ITEM_GROUND_EX
// #define NEW_SELECT_CHARACTER
#define __BL_CLIENT_LOCALE_STRING__
#define ENABLE_BUFFER_SECURITY

#define __PET_SYSTEM__
#ifdef __PET_SYSTEM__
#define USE_ACTIVE_PET_SEAL_EFFECT
#define PET_SEAL_ACTIVE_SOCKET_IDX 2
#define USE_PET_SEAL_ON_LOGIN
#define ENABLE_PET_SYSTEM_EX
#endif

enum eCommonDefines {
	MAP_ALLOW_LIMIT = 32, // 32 default
};

// #define ENABLE_WOLFMAN_CHARACTER
#ifdef ENABLE_WOLFMAN_CHARACTER
// #define DISABLE_WOLFMAN_ON_CREATE
#define USE_MOB_BLEEDING_AS_POISON
#define USE_MOB_CLAW_AS_DAGGER
// #define USE_ITEM_BLEEDING_AS_POISON
// #define USE_ITEM_CLAW_AS_DAGGER
#define USE_WOLFMAN_STONES
#define USE_WOLFMAN_BOOKS
#endif

// #define ENABLE_MAGIC_REDUCTION_SYSTEM
#ifdef ENABLE_MAGIC_REDUCTION_SYSTEM
// #define USE_MAGIC_REDUCTION_STONES
#endif

#define DISABLE_STOP_RIDING_WHEN_DIE //								if DISABLE_TOP_RIDING_WHEN_DIE is defined, the player doesn't lose the horse after dying
// #define ENABLE_ACCE_COSTUME_SYSTEM								//fixed version
// #define USE_ACCE_ABSORB_WITH_NO_NEGATIVE_BONUS					//enable only positive bonus in acce absorb
#define ENABLE_HIGHLIGHT_NEW_ITEM									//if you want to see highlighted a new item when dropped or when exchanged
#define ENABLE_KILL_EVENT_FIX										//if you want to fix the 0 exp problem about the when kill lua event (recommended)
// #define ENABLE_SYSLOG_PACKET_SENT								// debug purposes
#define ENABLE_MOB_DROP_POLY										// enable drop type 'poly' for special_item_group.txt (idx drop mobvnum pct customitemvnum)
	
#define ENABLE_EXTEND_ITEM_AWARD									//slight adjustement
#ifdef ENABLE_EXTEND_ITEM_AWARD										
	// #define USE_ITEM_AWARD_CHECK_ATTRIBUTES						//it prevents bonuses higher than item_attr lvl1-lvl5 min-max range limit
#endif

#define __BL_OFFICIAL_LOOT_FILTER__
#if defined(__BL_OFFICIAL_LOOT_FILTER__)
// #define __PREMIUM_LOOT_FILTER__									// Enable Premium Usage of the Loot Filter System
#endif

// #define ENABLE_CHEQUE_SYSTEM
#ifdef ENABLE_CHEQUE_SYSTEM
#define ENABLE_SHOP_USE_CHEQUE
#define DISABLE_CHEQUE_DROP
#define ENABLE_WON_EXCHANGE_WINDOW
#endif

//ML
#define __BL_MULTI_LANGUAGE__										// Multi dil sistemi
#define __BL_MULTI_LANGUAGE_PREMIUM__								// Multi dil sistemi
#define __BL_MULTI_LANGUAGE_ULTIMATE__								// Multi dil sistemi
#define ENABLE_GF_ATLAS_MARK_INFO									// Multi dil sistemi ekstra
//ML

#define GUILD_LARGE_ICON											// 24x16 lonca simgesi boyutu
#define ENABLE_SPAMDB_REFRESH										// spam_db otomatik chat ban
#define DC_P2P_UPDATE												// Farklı CH'de ki oyuncuyu dc atmak için
#define WARP_CH_UPDATE												// Farklı CH'de ki oyuncunun yanına gitmek için
#define DISABLE_EXTRA_PROB_FOR_REFINE								// Lonca demiricis ekstra şans azaltma
#define DISABLE_PARTY_EXP_WITH_LEVEL								// Grup exp bug fix
#define DISABLE_ITEM_LEVEL_FOR_GM									// GM her level itemi giyebilir.
#define FAST_PACKET_BLOCK											// Paket buglarını önlemek için süre engelleri
#define HANDSHAKE_PACKET_ANTI_FLOOD									// Auth / Game socket attack fix
#define PARTY_EXP_FIX												// Grup bugu. Karakteri ortaya alma.
#define ENABLE_EXCHANGE_LOG											// Oyun içi ticaret log ekranı
#define KYGN_CHEST_INFO												// Sandık İçeriğini Görme
#define __SEND_TARGET_INFO__										// Mob target info
#define UPDATE_ITEM_MESSAGE											// Item +basma duyurusu
#define ENABLE_USER_REPORT_SYSTEM 									// Target oyuncu report
#define ENABLE_ITEM_SHOP_SYSTEM										// Nesne market
#define ENABLE_CUBE_RENEWAL											// Yeni Cube penceresi
#ifdef ENABLE_CUBE_RENEWAL
	#define ENABLE_CUBE_RENEWAL_DISABLE_BULK						// Cube toplu uretim kapali: istemci kac parti isterse istesin server tek parti uretir (toplu uretimde hatali uretim onlemi)
#endif
#define ENABLE_SKILL_FLAG_PARTY										// Şaman grup kutsama
#define ENABLE_MULTISHOP											// İtem ile npcde ürün satma
#define WJ_NEW_DROP_DIALOG											// Hızlı sil sat
#define __GEM_SYSTEM__												// Gaya mağazası
#define ENABLE_GM_MOB_FIND_CMD										// /mob_find <vnum> ile mapte mob arama
#define UPDATE_AUTO_POT_1K_HP										// Otopot ekstra 1K sabit hp
#define ENABLE_CHARACTER_CHEST										// Karakter sandık
#define ENABLE_BULK_POTION_PANEL									// Hızlı şebnem penceresi
#define ENABLE_NEW_MOB_TIMER										// Saatli boss spawn
#define AUTO_CHAT_ENABLE											// Otochat
#define ENABLE_ITEM_UPGRADE_OWNER									// Tooltip +9'a basan kişi
#define ENABLE_ITEM_ENCHANT_USE_COUNT								// Tooltip efsun sayısı
#define ENABLE_GM_PLAYER_PANEL										// GM paneli TAB
#define ATTBONUS_ELEXIR												// Sürgüne karşı saldırı ve savunma efsunu
#define ENABLE_ELEXIR_MISSING_DAMAGE_PENALTY						// Elexir bonusu olmayan surgunde (72/73/208) canavardan 3 kat hasar yer
#define SKILL_SELECT												// Uzaktan skill seçme
#define COLLECTIVE_DAMAGE_INFO										// Toplu hasar pc & npc
#define METIN35_ADMIN_PANEL											// Yönetim Paneli
#define ENABLE_STATUS_ADD_BY_INPUT									// Stat puanini tek komutla toplu verme
#define ENABLE_GREEN_ENCHANT_LV5_LIMIT								// Yeşil efsunda lv5 efsun gelmez
#define BERAN_SETAOU												// Mavi Ejderha
#define ENABLE_SAFE_TRADE_SYSTEM									// Güvenli Ticaret
#define ENABLE_PC_NPC_DAMAGE_BONUS									// Moblara %30 daha fazla hasar
#define ENABLE_NPC_MAX_HP_BONUS										// Moblarda %30 daha fazla HP
#define ENABLE_RELOAD_ETC_DROP_ITEM									// Etc_drop_item.txt yenileme
#define ENABLE_RELOAD_MOB_DROP_ITEM									// Mob_drop_item.txt canli yenileme (/reload m, tum core'lara P2P; drop_item_group.txt ile birlikte okunur)
#define ENABLE_RELOAD_SPAM_DB										// spam_db canli yenileme (/reload s, tum core'lara GG50 P2P; kelimeler COMMON_SQL veritabanindaki spam_db tablosundan asenkron okunur)
#define ENABLE_MOUNT_SKILL_DELAY_BYPASS								// Bazı skillerde at binme engelini kapatma (kutsama hava vb.)
#define ENABLE_HORSE_RIDE_SKILL_DELAY								// Normal ata binerken de (StartRiding) skill sonrası 1500ms bekleme — özel binek ile parite, bypass listesi ortak
#define ENABLE_DUNGEON_REJOIN_SYSTEM 								// Kuleye geri dönüş sistemi
#define ENABLE_SCROLL_76016_LV_LIMIT								// Basit Kutsama Kagidi (30 level alti itemler icin)
#define ENABLE_GM_ONLY_LOGIN										// GM girisi
#define ENABLE_KADIM_EFSUN_SYSTEM									// Kadim Efsun Sistemi
#define EXP_DEC_IN_DUNGEON											// Zindanlarda %90 Daha Az EXP
#define ENABLE_LEVEL_MAP_EXP_LIMIT									// 45-75 ve 75-99 harita exp engelleri
#define ENABLE_FISHING_ANTI_MACRO									// Balik makro engeli: envanterde solucan varken yeni solucan alinamaz + NPC penceresi acikken balik tutulamaz
#define ENABLE_FISHING_KILL_QUEST									// Balik bot onlemi: cekis sayisi esiginde mob kesme gorevi; gorev bitmeden yeni olta atilamaz
// #define ENABLE_HORSE_ADDITIVE_STATS									// At statlarinin karakter statlarina + eklenmesi
#define FISHING_TIME_LOG											// Balik sure
#define ENABLE_MOUNT_PVP_DAMAGE_REDUCTION							// At üzerinde pvp'de %30 hasar azaltma
#define ENABLE_MARRIAGE_RING_COOLTIME								// Yuzuk tekrar kullanim suresi
#define ENABLE_BOT_CONTROL											// Bot Kontrol Sistemi (periyodik bot taramasi + dogrulama kodu)
#ifdef ENABLE_BOT_CONTROL
	#define ENABLE_BOT_CONTROL_SOFT_MODE		// GECICI gozlem modu: panel + log calisir, hasar/kanal/cikis bloklari ve DC devre disi; /bot_control_enforce ile ac/kapa, acilis varsayilani CONFIG "BOT_CONTROL_ENFORCE: 1"
#endif
// #define ENABLE_STONE_DROP_TOP_DAMAGER								// Taslarda en cok hasar vuran oyuncu tum droplari alir
#define ENABLE_WHISPER_LEVEL_LIMIT									// 10 seviye alti oyuncular oyunculara PM gonderemez, PM penceresinde uyari (GM'e gonderim serbest)
#ifdef ENABLE_WHISPER_LEVEL_LIMIT
	#define WHISPER_LEVEL_LIMIT 10									// PM gonderebilmek icin gereken minimum seviye
#endif
// #define ENABLE_GIFT_SEND_SYSTEM										// Hediye gonderme sistemi (oyuncudan oyuncuya kozmetik hediye, EP -> hediye puani; item verilmez). NOT: mevcut GIFT_SYSTEM'den ayridir.
#define ENABLE_HORSE_MONSTER_DAMAGE_BONUS								// At seviyesine gore canavara ek guc: seviye 11-21 arasi her seviye +%1 (21'de +%10)
#define ENABLE_CLIENTLESS_HANDSHAKE_TRAP							// Clientless bot honeypot: eski handshake header'i (0xff) tuzak; gercek client 0xa0 gonderir
#define ENABLE_PHANTOM_METIN_TRAP									// Phantom metin tuzagi: tas kesiminden sonra client pack'inde olmayan vnum'lu sahte tas yayinlanir; ona paket atan = stok-disi client (bot). /phantom_trap ac-kapa, /phantom_trap_enforce otoban (2. vurusta account BLOCK + DC)
#define ENABLE_IP_BAN
#define ENABLE_NEXT_REFINE_SUCCESS									// GM komutu /refine_success <oyuncu> [off]: hedefin SADECE bir sonraki +basma denemesi %100 basarili olur (tek seferlik; quest flag'te tutulur, warp/relog'da kaybolmaz, zar aninda tuketilir)
#define NEW_PASSIVE_SKILLS											// Pasif Beceriler: Ilham (141) proto formulu yerine sabit +62.5 HP/seviye (lvl*125/2, maks 40 lvl = 2500 HP); 49102 Pasif Beceri Kitabi TEK kitapla 141 + 144 birlikte gelistirir (server rebuild + client rebuild/repack birlikte)
#define ENABLE_MONSTER_HUNTER_SKILL							// Canavar Avcisi pasifi (144): canavara ve metin tasina +seviye/2 %% hasar (IsStone 2026-10-17); ayri kitabi YOK, 49102 ile Ilham'la birlikte gelisir. NEW_PASSIVE_SKILLS gerektirir
#define ENABLE_LUCKY_DRAW											// Sansli Cekilis etkinligi: /lucky_draw ile bilet alinir (item ve/veya yang), sure bitince 3 rastgele kazanan belirlenir, oduller /lucky_draw 3 ile teslim alinir. GM: /lucky_draw_manage. (server rebuild + client rebuild/repack birlikte; player DB'ye sql/luckydraw.sql uygulanmali; GC 246 / GG 44)
#ifdef ENABLE_LUCKY_DRAW
	#define LD_MAX_WINNERS 5										// kazanan sayisi (SQL luckydraw_winners satir sayisi ile ayni olmali)
	#define LD_MAX_REWARDS 5										// kazanan basina odul kolonu (reward1..5_vnum)
	#define LD_MAX_REQ_ITEMS 5										// katilim icin istenebilecek farkli item sayisi
	#define LD_MAX_JOINER_LIST 20									// pencerede gosterilen katilimci sayisi (en cok bileti olanlar)
#endif

#define OFFLINE_SHOP												// Offline shops system
#ifdef OFFLINE_SHOP
	#define GIFT_SYSTEM												// gift system enable
	#define SHOP_TIME_REFRESH 1*60									// time for cycle checking older shops
	#define SHOP_BLOCK_GAME99										// Blocking create shops on channel 99
	#define SHOP_AUTO_CLOSE											// Enable auto closing shop after sell last item
	#define SHOP_GM_PRIVILEGES GM_IMPLEMENTOR						// Minimum GM privileges to using Shop GM Panel
	#define ENABLE_OFFLINE_SHOP_REMOTE								// 50200 itemi ile pazara gitmeden uzaktan yonetim
	#define ENABLE_OFFLINE_SHOP_SOLD_RED							// Satilan item pazardan silinmesin
	#define ENABLE_SHOP_SEARCH_ITEM_SELECT						// Pazar Arama: grid'den item secip SADECE secilenleri arama (secim yoksa eski kategori-geneli davranis)
	#define ENABLE_OFFLINE_SHOP_REMOTE_VIEW
	#define ENABLE_OFFLINE_SHOP_WARP_COUNTDOWN
	#define ENABLE_IKASHOP_SEARCH									// IKASHOP tarzi global Pazar Arama: kanal/harita bagimsiz filtreli arama + uzaktan satin alma + dukkan goruntuleme (CG 84 / GC 139 / GG 42; wire degisti -> server+client rebuild + repack BIRLIKTE)
	#define SHOP_ALLOWED_MAP_INDEXES 1, 21, 41, 3, 23, 43, 61, 64, 65	// Pazar kurulabilen harita indexleri; listede olmayan haritalarda (private kopyalar dahil) pazar acilamaz
	#define ENABLE_OFFLINE_SHOP_BAN_CLOSE						// Banli hesabin pazarini otomatik kapat: 60 dk'da bir account.status/availDt toplu kontrolu (async FuncQuery); banli sahibin pazari DeleteMyShop ile kapanir, itemlar player_gift'e gider (server-only rebuild)
	#define ENABLE_SHOP_SEARCH_CLASS_SUBCAT						// Pazar Arama: Zirh/Silah/Taki'de sinif-grup alt-kategorileri (sub 10..15) + arti secimi (+1..+9) + vnum grid'i; "Bonuslu Ara" bu kategorilerden kaldirildi. Arti seviyesi paketteki mevcut socket0 alaniyla tasinir -> WIRE DEGISMEDI: server rebuild + root repack yeter, client exe rebuild GEREKMEZ. Tablolar: shop_manager.cpp + offlineshopsearch.py (uretec: _plan_shopsearch_subcat/gen_wearable_filters.py)
	#if defined(ENABLE_IKASHOP_SEARCH) && !defined(ENABLE_OFFLINE_SHOP_SOLD_RED)
		#error "ENABLE_IKASHOP_SEARCH icin ENABLE_OFFLINE_SHOP_SOLD_RED acik olmali (uzak alim kilidi sold kolonuna dayanir)"
	#endif
	#if defined(ENABLE_SHOP_SEARCH_CLASS_SUBCAT) && !defined(ENABLE_SHOP_SEARCH_ITEM_SELECT)
		#error "ENABLE_SHOP_SEARCH_CLASS_SUBCAT icin ENABLE_SHOP_SEARCH_ITEM_SELECT acik olmali (grid secimli arama ayni paket alanlarina dayanir)"
	#endif
#endif

#define ENABLE_MESSENGER_BLOCK										// Oyuncu Engelleme sistemi: PM/ticaret/parti/lonca/duello/duygu blok + messenger Engellendi grubu (wire degisti -> server+client rebuild + repack BIRLIKTE; SQL: messenger_block_list)
#define ENABLE_BOW_FLAT_DAMAGE_PERCENT 90							// Okcu mesafe cezasi iptal: ok hasari her mesafede sabit %75 (eski: 0-5m %100, 5m sonrasi her metre -%5, 25m ustu 0 vururdu; normal ok atisi + tum okcu skillerini kapsar, battle.cpp CalcArrowDamage) (server-only rebuild)
#define ENABLE_SPINED_ITEM_COUNT									// her kullanildiginda hesabin account.account.spined kolonu 1 artar, item 1 adet tukenir (SQL sart: ALTER TABLE account.account ADD COLUMN spined INT UNSIGNED NOT NULL DEFAULT 0) (server-only rebuild)
#ifdef ENABLE_SPINED_ITEM_COUNT
	#define SPINED_COUNT_ITEM_VNUM 71122							// sayaci artiran item vnum
#endif

#define ENABLE_HERB_POTION_USE_COOLTIME							// 50804 (Gango Koku Suyu) & 50816 (Ying Suyu) iksirlerine 1 saniye kullanim bekleme suresi (pulse tabanli bellek-ici, iki item ortak sayac; char_item.cpp 50801-50820 blogu USE_POTION_NODELAY) (server-only rebuild)
#define ENABLE_DROP_LEVEL_PENALTY_EXEMPT						// Seviye-farki drop muafiyeti: muaf hedeflerde (harita + boss listesi) oyuncu seviyesi DROP_LEVEL_PENALTY_EXEMPT_MIN_LEVEL (75) ve uzerindeyse, mobdan yuksek ya da dusuk farketmez, aiPercentByDeltaLev tablo sonucu atlanir ve sabit DROP_LEVEL_PENALTY_EXEMPT_PERCENT (tablonun -15 satiri = %180) sayilir; 75 alti oyuncu normal tablo; altin dususu degismez (item_manager.cpp GetDropPct choke) (server-only rebuild)
#ifdef ENABLE_DROP_LEVEL_PENALTY_EXEMPT
	#define DROP_LEVEL_PENALTY_EXEMPT_MAP	68						// Kizil Orman (metin2_map_trent02) - haritadaki tum moblar muaf
	#define DROP_LEVEL_PENALTY_EXEMPT_MOBS	{ 1093, 1192, 2491, 2492, 2493, 2598 }	// her haritada muaf bosslar: Lusifer, Buz Cadisi, Komutan, General, Beran-Setaou, Azrail
	#define DROP_LEVEL_PENALTY_EXEMPT_PERCENT	180					// muaf hedefte sabit drop yuzdesi (180 = tablonun -15 satiri; oyuncu mobdan 15 seviye dusukmus gibi sayilir)
	#define DROP_LEVEL_PENALTY_EXEMPT_MIN_LEVEL	75				// muafiyet icin oyuncunun (katilin) minimum seviyesi; altindakiler normal aiPercentByDeltaLev tablosunu kullanir
#endif

#define ENABLE_GM_FISH_INFO										// GM Balik Bilgisi: target penceresinde GM'e ozel buton; hedef oyuncunun log DB fishing_log kayitlarini client'ta sayfali pencerede gosterir (/fish_info <isim>; son 500 kayit, 10 sayfa x 50 satir; LogManager::FuncQuery async - oyun donmaz) (game rebuild + root repack; db core GEREKMEZ)

#define ENABLE_SOULBIND_SYSTEM									// Ruha Baglama (soulbind) sistemi: Baglama Parsomeni (50263) silah/zirh/kostumu ruha baglar; ruha bagli esya ticaret / guvenli ticaret / pazar / NPC satis / silme / yere atma / PK dusurme / NPC'ye verme / +basma / efsun degistirme / tas cikarma islemlerine giremez (giyme, kullanma, envanter ici tasima ve depo serbest). Ayirma Parsomeni (50264) bagi SOULBIND_UNBIND_DURATION_SEC sonra cozer; sure dolana kadar esya bagli kalir, 50263 ile ayirma iptal edilir. player.item.sealbind: 0=serbest, -1=kalici bagli, >0=cozulme unix zamani. WIRE DEGISTI: TPlayerItem (game<->db) + GC ITEM_SET / ITEM_UPDATE / SAFEBOX_SET / MALL_SET -> db core + TUM game core'lar + client exe rebuild + root repack BIRLIKTE; ONCE SQL: sql/soulbind_system.sql (ALTER TABLE player.item ADD COLUMN sealbind INT NOT NULL DEFAULT 0)
#ifdef ENABLE_SOULBIND_SYSTEM
	#define SOULBIND_BIND_SCROLL_VNUM		50263	// Baglama Parsomeni
	#define SOULBIND_UNBIND_SCROLL_VNUM		50264	// Ayirma Parsomeni
	#define SOULBIND_UNBIND_DURATION_SEC	(72 * 60 * 60)	// ayirma suresi (sn)
#endif

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
#define ENABLE_YANG_FLOW_ANALYTICS									// Harita bazli yang giris analizi: mob altini + NPC satis + quest odulu + altin calma sayaclari RAM'de birikir, saatte bir log DB yang_flow tablosuna yazilir (ONCE sql/yang_flow.sql log DB'ye uygulanmali; server-only game rebuild, db core / client / repack GEREKMEZ)
#define ENABLE_WS_TOURNAMENT									// WS 1v1 Turnuva: kayit ucretli tek eleme turnuvasi, arena map 112 host core'unda calisir (GG 47 relay ile tum kanallardan kayit; odul/iade player.ws_claim idempotent claim; ONCE sql/ws_tournament.sql player DB'ye! TUM game core'lar birlikte rebuild - GG wire; db core/client/repack GEREKMEZ)
#define ENABLE_FFA_EVENT										// Anonim FFA Savas Etkinligi (Kaos Savasi): map 70 herkes-herkese PvP, isimler "Player" maskeli, canli kill siralamasi, 20dk otomatik kapanis; acilis /e ffa_open 1 (sure: ffa_minutes flag); server-only Faz 1 - SQL/wire/client-binary GEREKMEZ (quest systems/ffa_savas.quest derlenmeli; skor penceresi Faz 2 root repack)
#define ENABLE_PLAYER_STATISTICS		// Oyun ici siralama sistemi (kisisel istatistikler + ranking penceresi; SQL: player.player st_* kolonlari ONCE eklenmeli)
#define ENABLE_BOSS_DAMAGE_RANKING								// Boss hasar siralamasi: listedeki bosslar dogunca cevredeki oyunculara canli top-5 hasar tablosu (CHAT_TYPE_COMMAND boss_rank/boss_rank_end; boss_ranking.cpp/h + uibossrank.py; client binary GEREKMEZ - game rebuild + root repack; SQL/quest YOK)
#ifdef ENABLE_BOSS_DAMAGE_RANKING
	#define BOSS_RANKING_VNUMS			1093, 2598, 2491, 2492, 2494, 2495, 1192	// Lusifer, Azrail, 4 General, Cadi (2493 Mavi Ejder BILEREK haric - kullanici karari 2026-09-09)
	#define BOSS_RANKING_TOP_COUNT		10											// yayindaki satir sayisi (isimler wire'da 11 karaktere kesilir - 10 satir CHAT_MAX_LEN butcesine boyle sigar; satir siniri 420B, asiri uc durumda son satir dusebilir, tasma/cokme OLMAZ)
	#define BOSS_RANKING_TICK_SECONDS	3											// yayin araligi (sn)
	#define BOSS_RANKING_DROP_RULES		{ 1192, 30179, 1 }							// (bossVnum, itemVnum, sira) uclu listesi: bossun drop tablosundan o item DUSERSE sahipligi olum-ani siralamasindaki o siradaki oyuncuya verilir (virgulle coklu kural: { 1192, 30179, 1 }, { 2491, 30179, 1 } gibi; AYNI boss+item icin ikinci kural OLU KALIR - ilk eslesme kazanir; listeyi BOS BIRAKMA - sifir-uzunluk dizi derlenmez); sahip cevrimdisi/baska core'daysa item STOK akisla duser (kaybolmaz, alt siraya GECMEZ - kullanici karari 2026-09-10); ayni itemin tum kopyalari ayni sira sahibine
	#define BOSS_RANKING_DROP_OWN_SECS	60											// kural iteminin yerdeki sahiplik suresi (stok 30sn; boss sonrasi kalabalik payi)
#endif
#define ENABLE_NEWBIE_DOUBLE_LEVEL									// Yeni baslayan 1+1 seviye: EXP ile dogal seviye atlayan oyuncu, atladigi seviye NEWBIE_DOUBLE_LEVEL_MAX_LEVEL (40) altindaysa otomatik 1 tam seviye daha alir (3 stat + rastgele HP/SP + beceri puani + quest/lonca/parti/log level kancalari dahil); sonuc seviyesi 40'i GECMEZ (38->39 dogal + 40 bonus; 39->40 dogal atlamada bonus YOK; 1'den baslayan karakter 3,5,...,39 bonus alir). SADECE PointChange(POINT_EXP) yolu tetikler (mob/metin/parti EXP, special_item_group EXP, pc.give_exp2, GM /set exp); GM /level, pc.set_level, pc.set_level0 ikiye KATLANMAZ (char.cpp POINT_EXP choke). Beceri grubu secilmeden gecilen bonus seviyeler puan kaybettirmez (do_get_skills / pc.clear_skill seviye-1'e gore yeniden hesaplar). SKILL_SELECT ile: bonus seviyede ikinci skill_select BASTIRILIR (m_bNewbieBonusLevel; bonus seviye 5 ise HARIC - 1'den baslayan karakterde 5 her zaman bonus seviyedir, dogal 4 hic gondermemisti) + game.py LearnSkillGroup pencere-acikken-yeniden-kurma bugfix'i (root repack). Levelup quest'leri `== N` yerine `>= N` kullanmali (ayni cagrida ikinci levelup tetigi quest calisirken dusebilir). (server-only game rebuild; SQL/db core GEREKMEZ; client exe GEREKMEZ; game.py bugfix icin root repack)
#ifdef ENABLE_NEWBIE_DOUBLE_LEVEL
	#define NEWBIE_DOUBLE_LEVEL_MAX_LEVEL	40						// bonusun verilebilecegi en yuksek sonuc seviyesi (dogal atlamadan SONRA seviye bu degerin ALTINDAYSA +1 verilir)
#endif
#define ENABLE_ORB_EVENT												// Kure Avi: her saatin ORB_EVENT_START_MINUTE. dakikasinda 5 dk, oyuncunun etrafinda kisiye ozel kureler (mavi=+2, beyaz=-1 puan), tum core'larda siralama, odul 50253 player_gift ile (GIFT_SYSTEM sart). Server: orb_event.cpp/h + sql/orb_event.sql (ONCE uygulanir) + GG 51 (packet.h ifdef'siz kayit); client: Locale_inc.h ENABLE_ORB_EVENT + effect.CreateWorld + root uiorbevent.py (rebuild+repack birlikte). Acma: /e orb_event 1; test: /orb_admin start; acil: /orb_admin cancel (odulsuz)
#ifdef ENABLE_ORB_EVENT
	#define ORB_EVENT_START_MINUTE		30		// tur her saatin bu dakikasinda baslar (30 = 01:30, 02:30 ...); START_MINUTE*60 + DURATION_SEC <= 3600 olmali
	#define ORB_EVENT_DURATION_SEC		300		// tur suresi (sn), baslangic dakikasindan itibaren (30 -> :30-:35)
	#define ORB_EVENT_ORB_COUNT			25		// oyuncu basina kure sayisi (en fazla 30)
	#define ORB_EVENT_BLUE_PCT			30		// mavi kure yuzdesi (gerisi beyaz)
	#define ORB_EVENT_BLUE_POINTS		2		// mavi kure puani
	#define ORB_EVENT_WHITE_POINTS		(-1)	// beyaz kure puani (eksi = ceza; toplam negatif olabilir, odul icin toplam > 0 sart)
	#define ORB_EVENT_GOLD_POINTS		10		// sari kure puani
	#define ORB_EVENT_GOLD_PCT			10		// her ORB_EVENT_GOLD_INTERVAL_SEC'de sari kure cikma sansi (%); oyuncu basina ayni anda en fazla 1 sari kure
	#define ORB_EVENT_GOLD_INTERVAL_SEC	3		// sari kure sans kontrolu araligi (sn)
	#define ORB_EVENT_GOLD_LIFETIME_SEC	3		// sari kure bu sure icinde alinmazsa kaybolur (sn)
	#define ORB_EVENT_GOLD_MAX_DIST		1500		// sari kurenin oyuncuya en uzak dogma mesafesi (cm; 3 sn'de yetisilebilsin)
	#define ORB_EVENT_PICK_RADIUS		100		// toplama yaricapi (cm)
	#define ORB_EVENT_SPAWN_MIN_DIST	400		// kurenin oyuncuya en yakin dogma mesafesi (cm)
	#define ORB_EVENT_SPAWN_MAX_DIST	1500	// kurenin oyuncuya en uzak dogma mesafesi (cm)
	#define ORB_EVENT_ORB_MIN_GAP		300		// iki kure arasi en az mesafe (cm)
	#define ORB_EVENT_RELOCATE_DIST		2500	// oyuncudan bu kadar uzak kalan kure yeniden dogar (cm)
	#define ORB_EVENT_MAX_MAP_INDEX		1000	// bu degerden BUYUK map index'lerde (zindan kopyalari) kure cikmaz
	#define ORB_EVENT_BLOCKED_MAPS		5, 25, 45, 66, 72, 73, 81, 100, 103, 105, 107, 108, 109, 110, 111, 112, 113, 181, 182, 183, 200, 208, 216, 217, 250, 351	// statik zindan/etkinlik haritalari (kullanici duzenler)
	#define ORB_EVENT_REWARD_VNUM		50253	// odul itemi (player_gift)
	#define ORB_EVENT_REWARD_TOP3		5		// 1-3. sira adet
	#define ORB_EVENT_REWARD_TOP50		3		// 4-50. sira adet
	#define ORB_EVENT_REWARD_REST		1		// 51+ adet
	#define ORB_EVENT_REWARD_MIN_SCORE	50		// odul icin gereken en az toplam puan (altinda kalan siralamada gorunur ama odul almaz)
	#define ORB_EVENT_LINE_MAX			380		// CHAT_TYPE_COMMAND satir siniri (bayt)
#endif
