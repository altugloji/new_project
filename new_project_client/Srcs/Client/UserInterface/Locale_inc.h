#pragma once

//////////////////////////////////////////////////////////////////////////
// ### ServiceDefs Macros ###
// ### ServiceDefs Macros ###
//////////////////////////////////////////////////////////////////////////

#define ENABLE_RENDER_TARGET
#define ENABLE_WIKI
#define __GEM_SHOP__

//////////////////////////////////////////////////////////////////////////
// ### Default Ymir Macros ###
#define LOCALE_SERVICE_EUROPE
#define ENABLE_COSTUME_SYSTEM
// #define ENABLE_ENERGY_SYSTEM
// #define ENABLE_DRAGON_SOUL_SYSTEM
// #define ENABLE_NEW_EQUIPMENT_SYSTEM
// ### Default Ymir Macros ###
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
// ### New From LocaleInc ###
#define ENABLE_PACK_GET_CHECK
#define ENABLE_CANSEEHIDDENTHING_FOR_GM
#define ENABLE_PROTOSTRUCT_AUTODETECT
#define ENABLE_PLAYER_PER_ACCOUNT5
#define ENABLE_LEVEL_IN_TRADE
// #define ENABLE_DICE_SYSTEM
#define ENABLE_EXTEND_INVEN_SYSTEM
#define ENABLE_LVL115_ARMOR_EFFECT
#define ENABLE_SLOT_WINDOW_EX
#define ENABLE_TEXT_LEVEL_REFRESH
#define ENABLE_USE_COSTUME_ATTR
// #define ENABLE_MAGIC_REDUCTION_SYSTEM
#define ENABLE_MOUNT_COSTUME_SYSTEM
#define ENABLE_WEAPON_COSTUME_SYSTEM
#define ENABLE_DISCORD_RPC
#define ENABLE_PET_SYSTEM_EX
#define ENABLE_LOCALE_COMMON
#define ENABLE_NO_DSS_QUALIFICATION
//#define ENABLE_NO_SELL_PRICE_DIVIDED_BY_5
// #define ENABLE_PENDANT_SYSTEM
// #define ENABLE_GLOVE_SYSTEM
#define ENABLE_MOVE_CHANNEL
// #define ENABLE_QUIVER_SYSTEM
#define ENABLE_RACE_HEIGHT
// #define ENABLE_ELEMENTAL_TARGET
#define ENABLE_INGAME_CONSOLE
#define ENABLE_4TH_AFF_SKILL_DESC
#define ENABLE_GUILD_TOKEN_AUTH
#define ENABLE_EMOTION_HIDE_WEAPON
#define ENABLE_MULTI_ITEM_PICK
//#define ENABLE_CONQUEROR_UI
#define ENABLE_DS_GRADE_MYTH
#define ENABLE_MESSENGER_REMOVE_SYNC
// #define ENABLE_MODEL_LOD_LOAD
#define ENABLE_ITEM_GROUND_EX
// #define NEW_SELECT_CHARACTER

#define ENABLE_NEW_EVENT_STRUCT
#ifdef ENABLE_NEW_EVENT_STRUCT
#define USE_NEW_EVENT_TEXT_AUTO_Y
#endif

//#define WJ_SHOW_MOB_INFO
#ifdef WJ_SHOW_MOB_INFO
#define ENABLE_SHOW_MOBAIFLAG
#define ENABLE_SHOW_MOBLEVEL
#define WJ_SHOW_MOB_INFO_EX
#endif

// #define ENABLE_WOLFMAN_CHARACTER
#ifdef ENABLE_WOLFMAN_CHARACTER
// #define DISABLE_WOLFMAN_ON_CREATE
#endif
// ### New From LocaleInc ###
//////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////////////
// ### New System Defines - Extended Version ###
// #define ENABLE_ACCE_COSTUME_SYSTEM
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
// #define USE_ACCE_ABSORB_WITH_NO_NEGATIVE_BONUS
#endif

#define ENABLE_HIGHLIGHT_NEW_ITEM //if you want to see highlighted a new item when dropped or when exchanged
#ifdef ENABLE_HIGHLIGHT_NEW_ITEM
#define BL_ENABLE_PICKUP_ITEM_EFFECT // enable some extra highlight features from official
#define __BL_ENABLE_PICKUP_ITEM_EFFECT__ // alias
#endif

#define __BL_OFFICIAL_LOOT_FILTER__
#if defined(__BL_OFFICIAL_LOOT_FILTER__)
//#define ENABLE_PREMIUM_LOOT_FILTER // Enable Premium Usage of the Loot Filter System
#endif

#define ENABLE_MOUSEWHEEL_EVENT // if you want use SetMouseWheelScrollEvent or you want use mouse wheel to move the scrollbar
#define ENABLE_EMOJI_SYSTEM // it shows emojis in the textlines
#define __ENABLE_STEALTH_FIX__ // effects while hidden won't show up
// #define ENABLE_MINIMAP_WHITEMARK_CIRCLE // circle dots in minimap instead of squares
// #define ENABLE_PRINT_RECV_PACKET_DEBUG // for debug: print received packets
#define ENABLE_MINIMAP_TELEPORT_CLICK // click on minimap as gm to warp directly
#define ENABLE_ATLAS_MARK_ON_WARP_SCROLLS // warp scrolls tooltips will show the mark on the atlas

// enable the won system as a currency
// #define ENABLE_CHEQUE_SYSTEM
#ifdef ENABLE_CHEQUE_SYSTEM
#define DISABLE_CHEQUE_DROP
#define ENABLE_WON_EXCHANGE_WINDOW
#endif

// reversed official code
#define ENABLE_PLAYER_CHECKAFFECT
#define ENABLE_BL_APP_GET_TEXT
#define ENABLE_BL_TRACEBACK
#define __BL_MOUSE_WHEEL_TOP_WINDOW__
#define ENABLE_UI_CIRCLE
#define ENABLE_UI_MOVING
#define ENABLE_FONT_EX
#define __BL_CLIP_MASK__
#define ENABLE_AUTO_L2R
#define __BL_FOG_FIX__
#define __BL_FLY_TARGET_POSITION__
#define __BL_CLIENT_LOCALE_STRING__
#define ENABLE_AREA_OPTIMIZATION
//#define ENABLE_DYNAMIC_SHADOW

//ML_Full
#define __BL_MULTI_LANGUAGE__
#define ENABLE_GF_ATLAS_MARK_INFO // https://metin2.dev/topic/23474-gf-loadatlasmarkinfo/
#define __BL_MULTI_LANGUAGE_PREMIUM__
#define __BL_MULTILANGUAGE_CHATTING__
#define __BL_MULTI_LANGUAGE_ULTIMATE__

#define GUILD_LARGE_ICON
#define TASKBAR_SKILL_COOLDOWN_TEXT
#define ITEM_SLOT_REFINE_TEXT
#define ENABLE_EXCHANGE_LOG
#define KYGN_CHEST_INFO													// Sandık İçeriğini Görme
#define ENABLE_SEND_TARGET_INFO											// Mob target info
#define ENABLE_USER_REPORT_SYSTEM 										//Official User Report System
#define ENABLE_ITEM_SHOP_SYSTEM											// Nesne Market Sistemi
#define __RENEWAL_SKILL_BOOK__
#define ENABLE_CUBE_RENEWAL
#define ENABLE_CHARACTER_CHEST
#define ENABLE_BULK_POTION_PANEL
#define ENABLE_MULTISHOP
#define WJ_NEW_DROP_DIALOG
#define FAST_LOGIN_CHARACTER_SAVE
#define ENABLE_NIGHT_MODE_OPTION
#define AUTO_CHAT_ENABLE
#define BOSS_EFFECT
#define ENABLE_REFINE_RENEWAL
#define ENABLE_GM_PLAYER_PANEL
#define ENABLE_SAFE_TRADE_SYSTEM										// Güvenli Ticaret
#define ENABLE_ITEM_UPGRADE_OWNER
#define ENABLE_ITEM_ENCHANT_USE_COUNT
#define ENABLE_EFSUN_CHANGE_DIALOG
#define NEW_AFFECT_BLEND_ICON
#define ENABLE_STATUS_ADD_BY_INPUT											// Toplu statü verme
#define ENABLE_OFFLINE_SHOP													// Offline pazar / çevrimdışı dükkan
// #define METIN35_ADMIN_PANEL												// Yönetim Paneli
#ifdef METIN35_ADMIN_PANEL
	#define CUR_CLIENT_VERSION 17										//versiyon key
#endif

// ### New System Defines - Extended Version ###
//////////////////////////////////////////////////////////////////////////
//archive's 6b9a24beef838d9382c750a6b44ccdb4
