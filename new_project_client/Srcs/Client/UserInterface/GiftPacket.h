// GiftPacket.h
// Client-only packet definitions for the gift-send system (ENABLE_GIFT_SEND_SYSTEM).
// Keep wire layout in EXACT sync with server game/src/packet.h (TGiftItemEntry /
// TPacketCGGift* / TPacketGCGift*). Header NUMBERS must match server Packet.h.
#pragma once

#pragma pack(push, 1)

#ifdef ENABLE_GIFT_SEND_SYSTEM

// --- boyut sabitleri (server ile ayni olmali) ---
#define GIFT_NAME_MAX_LEN			32
#define GIFT_DESC_MAX_LEN			128
#define GIFT_MESSAGE_MAX_LEN		120
#define GIFT_LIST_MAX				120
#define GIFT_LIST_GC_MAX_SIZE		32768
#define GIFT_SEND_MAX_COUNT			99

// --- flag bitleri ---
#define GIFT_FLAG_PACKAGE			1
#define GIFT_FLAG_ANONYMOUS			2

// Bir hediye tanimi (katalog satiri)
typedef struct SGiftItemEntry
{
	WORD	wIndex;							// gift_item.id
	DWORD	dwIconVnum;						// ikon item vnum'u
	DWORD	dwPriceEP;						// birim EP fiyati
	BYTE	bPage;
	BYTE	bSlot;
	char	szName[GIFT_NAME_MAX_LEN + 1];
	char	szDesc[GIFT_DESC_MAX_LEN + 1];
} TGiftItemEntry;

// ---------------------------------------------------------------------
// CG (client -> game)
// ---------------------------------------------------------------------
typedef struct SPacketCGGiftList
{
	BYTE	bHeader;						// HEADER_CG_GIFT_LIST
} TPacketCGGiftList;

typedef struct SPacketCGGiftFind
{
	BYTE	bHeader;						// HEADER_CG_GIFT_FIND
	char	szName[CHARACTER_NAME_MAX_LEN + 1];
} TPacketCGGiftFind;

typedef struct SPacketCGGiftSend
{
	BYTE	bHeader;						// HEADER_CG_GIFT_SEND
	char	szName[CHARACTER_NAME_MAX_LEN + 1];
	WORD	wGiftIndex;
	BYTE	bCount;
	BYTE	bFlags;							// bit0 paket, bit1 anonim
	char	szMessage[GIFT_MESSAGE_MAX_LEN + 1];
} TPacketCGGiftSend;

// ---------------------------------------------------------------------
// GC (game -> client)
// ---------------------------------------------------------------------

// Dinamik boyutlu katalog paketi (wSize surer)
typedef struct SPacketGCGiftList
{
	BYTE	bHeader;						// HEADER_GC_GIFT_LIST
	WORD	wSize;							// dinamik toplam boyut
	BYTE	bCount;							// entry sayisi
	union
	{
		TGiftItemEntry	entries[GIFT_LIST_MAX];
		BYTE			abPayload[GIFT_LIST_GC_MAX_SIZE];
	};
} TPacketGCGiftList;

// Isim dogrulama sonucu (sabit)
typedef struct SPacketGCGiftFindResult
{
	BYTE	bHeader;						// HEADER_GC_GIFT_FIND_RESULT
	BYTE	bResult;						// 0 yok, 1 gecerli, 2 kendisi/hesabi
	char	szName[CHARACTER_NAME_MAX_LEN + 1];
} TPacketGCGiftFindResult;

// Gonderim sonucu (sabit)
typedef struct SPacketGCGiftSendResult
{
	BYTE	bHeader;						// HEADER_GC_GIFT_SEND_RESULT
	BYTE	bResult;						// EGiftSendResult
	DWORD	dwNewEP;						// gonderim sonrasi guncel EP
	WORD	wGiftIndex;
	BYTE	bCount;
} TPacketGCGiftSendResult;

// Guncel EP bakiyesi (sabit)
typedef struct SPacketGCGiftEP
{
	BYTE	bHeader;						// HEADER_GC_GIFT_EP
	DWORD	dwEP;
} TPacketGCGiftEP;

// Oyuncunun kendi hediye puani (sabit)
typedef struct SPacketGCGiftPoint
{
	BYTE	bHeader;						// HEADER_GC_GIFT_POINT
	DWORD	dwPoint;
} TPacketGCGiftPoint;

// Hediye alma bildirimi (sabit; tum alanlar sabit dizi)
typedef struct SPacketGCGiftNotify
{
	BYTE	bHeader;						// HEADER_GC_GIFT_NOTIFY
	BYTE	bAnonymous;
	DWORD	dwPoint;						// bu hediyeden gelen puan
	DWORD	dwTotalPoint;					// yeni toplam puan
	char	szSenderName[CHARACTER_NAME_MAX_LEN + 1];
	char	szGiftName[GIFT_NAME_MAX_LEN + 1];
	char	szMessage[GIFT_MESSAGE_MAX_LEN + 1];
} TPacketGCGiftNotify;

// --- Hediye Siralamasi (rank) ---
#define GIFT_RANK_MAX				10
#define GIFT_RANK_BOARD_SENDER		0				// en cok hediye gonderen
#define GIFT_RANK_BOARD_RECEIVER	1				// en cok hediye alan

typedef struct SGiftRankEntry
{
	char	szName[CHARACTER_NAME_MAX_LEN + 1];
	DWORD	dwPoint;
} TGiftRankEntry;

typedef struct SPacketCGGiftRank
{
	BYTE	bHeader;						// HEADER_CG_GIFT_RANK
	BYTE	bBoardType;						// GIFT_RANK_BOARD_*
} TPacketCGGiftRank;

typedef struct SPacketGCGiftRank
{
	BYTE	bHeader;						// HEADER_GC_GIFT_RANK (sabit boyut)
	BYTE	bBoardType;
	BYTE	bCount;							// gecerli entry sayisi
	DWORD	dwMyRank;						// 0 = siralamada yok ("-")
	DWORD	dwMyPoint;
	TGiftRankEntry	entries[GIFT_RANK_MAX];
} TPacketGCGiftRank;

#endif

#pragma pack(pop)
