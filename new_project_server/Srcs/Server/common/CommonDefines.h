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
// #define ENABLE_GLOVE_SYSTEM
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
#define EXP_DEC_IN_DUNGEON											// Zindanlarda %90 Daha Az EXP
#define DISABLE_EXTRA_PROB_FOR_REFINE								// Lonca demiricis ekstra şans azaltma
#define DISABLE_PARTY_EXP_WITH_LEVEL								// Grup exp bug fix
#define DISABLE_ITEM_LEVEL_FOR_GM									// GM her level itemi giyebilir.
#define FAST_PACKET_BLOCK											// Paket buglarını önlemek için süre engelleri
#define HANDSHAKE_PACKET_ANTI_FLOOD									// Auth / Game socket attack fix
#define PARTY_EXP_FIX												// Grup bugu. Karakteri ortaya alma.
#define __AUTO_SKILL_READER__										// Otomatik bk okuma 
#define ENABLE_EXCHANGE_LOG											// Oyun içi ticaret log ekranı
#define KYGN_CHEST_INFO												// Sandık İçeriğini Görme
#define __SEND_TARGET_INFO__										// Mob target info
#define UPDATE_ITEM_MESSAGE											// Item +basma duyurusu
#define ENABLE_USER_REPORT_SYSTEM 									// Target oyuncu report
#define ENABLE_ITEM_SHOP_SYSTEM										// Nesne market
#define ENABLE_CUBE_RENEWAL											// Yeni Cube penceresi
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
#define SKILL_SELECT												// Uzaktan skill seçme
#define COLLECTIVE_DAMAGE_INFO										// Toplu hasar pc & npc

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
