#include "stdafx.h"

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <ctime>

#if defined(_WIN32)
#include <fcntl.h>
#include <io.h>
#include <sys/stat.h>
#else
#include <fcntl.h>
#include <unistd.h>
#endif

#include "item_pickup_auth.h"
#include "../../common/tables.h"
#include "packet.h"
#include "char.h"
#include "desc.h"
#include "db.h"
#include "config.h"
#include "locale_service.h"

bool g_bItemPickupAuthEnabled = true;
bool g_bItemPickupAutoBlockEnabled = true;

namespace
{
	constexpr BYTE ITEM_PICKUP_AUTH_BAD_HASH = 1;
	constexpr BYTE ITEM_PICKUP_AUTH_BAD_SEQUENCE = 2;
	constexpr BYTE ITEM_PICKUP_AUTH_LEGACY_PACKET = 3;

	// Must stay byte-for-byte compatible with EterResourceLruTick in the client
	// (the VMProtect-target hash; its name is deliberately innocuous).
	DWORD ComputeItemPickupPacketHash(const void* data, size_t size, DWORD sessionNonce)
	{
		if (!data)
			return 0;

		const auto* bytes = static_cast<const std::uint8_t*>(data);
		const std::uint64_t session = (static_cast<std::uint64_t>(sessionNonce) << 32) | sessionNonce;
		const std::uint64_t k0 = 0xED9DE0801B44BE27ULL ^ session;
		const std::uint64_t k1 = 0x485B6527237AB93AULL ^ ((session << 17) | (session >> 47));

		std::uint64_t v0 = 0x736f6d6570736575ULL ^ k0;
		std::uint64_t v1 = 0x646f72616e646f6dULL ^ k1;
		std::uint64_t v2 = 0x6c7967656e657261ULL ^ k0;
		std::uint64_t v3 = 0x7465646279746573ULL ^ k1;

#define ITEM_PICKUP_SIPROUND() \
	do { \
		v0 += v1; v1 = (v1 << 13) | (v1 >> 51); v1 ^= v0; v0 = (v0 << 32) | (v0 >> 32); \
		v2 += v3; v3 = (v3 << 16) | (v3 >> 48); v3 ^= v2; \
		v0 += v3; v3 = (v3 << 21) | (v3 >> 43); v3 ^= v0; \
		v2 += v1; v1 = (v1 << 17) | (v1 >> 47); v1 ^= v2; v2 = (v2 << 32) | (v2 >> 32); \
	} while (0)

		size_t offset = 0;
		while (size - offset >= 8)
		{
			std::uint64_t block = 0;
			for (size_t i = 0; i < 8; ++i)
				block |= static_cast<std::uint64_t>(bytes[offset + i]) << (i * 8);

			v3 ^= block;
			ITEM_PICKUP_SIPROUND();
			ITEM_PICKUP_SIPROUND();
			v0 ^= block;
			offset += 8;
		}

		std::uint64_t tail = static_cast<std::uint64_t>(size & 0xff) << 56;
		for (size_t i = 0; i < size - offset; ++i)
			tail |= static_cast<std::uint64_t>(bytes[offset + i]) << (i * 8);

		v3 ^= tail;
		ITEM_PICKUP_SIPROUND();
		ITEM_PICKUP_SIPROUND();
		v0 ^= tail;
		v2 ^= 0xff;
		ITEM_PICKUP_SIPROUND();
		ITEM_PICKUP_SIPROUND();
		ITEM_PICKUP_SIPROUND();
		ITEM_PICKUP_SIPROUND();

#undef ITEM_PICKUP_SIPROUND

		const std::uint64_t tag = v0 ^ v1 ^ v2 ^ v3;
		std::uint32_t folded = static_cast<std::uint32_t>(tag ^ (tag >> 32));
		folded ^= folded >> 16;
		folded *= 0x7feb352dU;
		folded ^= folded >> 15;
		folded *= 0x846ca68bU;
		folded ^= folded >> 16;
		return static_cast<DWORD>(folded);
	}

	bool AppendLogLine(const char* path, const char* line, size_t length)
	{
#if defined(_WIN32)
		const int fd = _open(path, _O_WRONLY | _O_APPEND | _O_CREAT | _O_BINARY, _S_IREAD | _S_IWRITE);
		if (fd == -1)
			return false;

		int written = -1;
		do
		{
			written = _write(fd, line, static_cast<unsigned int>(length));
		} while (written == -1 && errno == EINTR);

		int savedError = written == static_cast<int>(length)
			? 0
			: (written == -1 ? errno : EIO);
		if (_close(fd) == -1 && savedError == 0)
			savedError = errno;

		if (savedError != 0)
		{
			errno = savedError;
			return false;
		}
		return true;
#else
		const int fd = open(path, O_WRONLY | O_APPEND | O_CREAT, 0640);
		if (fd == -1)
			return false;

		ssize_t written = -1;
		do
		{
			written = write(fd, line, length);
		} while (written == -1 && errno == EINTR);

		int savedError = written == static_cast<ssize_t>(length)
			? 0
			: (written == -1 ? errno : EIO);
		if (close(fd) == -1 && savedError == 0)
			savedError = errno;

		if (savedError != 0)
		{
			errno = savedError;
			return false;
		}
		return true;
#endif
	}

	bool BlockItemPickupAccount(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc())
			return false;

		const LPDESC desc = ch->GetDesc();
		const char* login = desc->GetAccountTable().login;
		const size_t loginLength = strnlen(login, LOGIN_MAX_LEN);
		if (loginLength == 0)
		{
			sys_err("ITEM_PICKUP_AUTH_ACCOUNT_BLOCK missing login aid=%u player=%s ip=%s",
				desc->GetAccountTable().id,
				ch->GetName(),
				desc->GetHostName());
			return false;
		}

		char escapedLogin[LOGIN_MAX_LEN * 2 + 1]{};
		DBManager::instance().EscapeString(
			escapedLogin,
			sizeof(escapedLogin),
			login,
			loginLength);

		const auto result = DBManager::instance().DirectQuery(
			"UPDATE account.account SET status = 'BLOCK' WHERE login = '%s'",
			escapedLogin);

		if (!result || result->uiSQLErrno != 0 || !result->Get() ||
			result->Get()->uiAffectedRows == static_cast<std::uint32_t>(-1))
		{
			sys_err("ITEM_PICKUP_AUTH_ACCOUNT_BLOCK failed login=%s aid=%u player=%s ip=%s sql_errno=%u",
				login,
				desc->GetAccountTable().id,
				ch->GetName(),
				desc->GetHostName(),
				result ? result->uiSQLErrno : 0U);
			return false;
		}

		sys_err("ITEM_PICKUP_AUTH_ACCOUNT_BLOCK applied login=%s aid=%u player=%s ip=%s affected_rows=%u",
			login,
			desc->GetAccountTable().id,
			ch->GetName(),
			desc->GetHostName(),
			static_cast<unsigned int>(result->Get()->uiAffectedRows));
		return true;
	}

	void ReportItemPickupAuthFailure(LPCHARACTER ch, BYTE reason, DWORD vid,
		DWORD receivedSequence, DWORD expectedSequence, DWORD receivedHash, DWORD expectedHash)
	{
		if (!ch || !ch->GetDesc())
			return;

		const LPDESC desc = ch->GetDesc();
		const char* reasonText = "hash";
		if (reason == ITEM_PICKUP_AUTH_BAD_SEQUENCE)
			reasonText = "sequence";
		else if (reason == ITEM_PICKUP_AUTH_LEGACY_PACKET)
			reasonText = "legacy";
		const bool blockableViolation =
			(reason == ITEM_PICKUP_AUTH_BAD_HASH || reason == ITEM_PICKUP_AUTH_LEGACY_PACKET);
		const unsigned int blockRequested =
			(blockableViolation && g_bItemPickupAutoBlockEnabled) ? 1U : 0U;

		sys_err("ITEM_PICKUP_AUTH_FAILURE reason=%s block_requested=%u login=%s player=%s ip=%s vid=%u "
			"sequence=%u expected_sequence=%u hash=%08x expected_hash=%08x",
			reasonText,
			blockRequested,
			desc->GetAccountTable().login,
			ch->GetName(),
			desc->GetHostName(),
			vid,
			receivedSequence,
			expectedSequence,
			receivedHash,
			expectedHash);

		const time_t now = time(nullptr);
		struct tm localTime{};
#if defined(_WIN32)
		if (localtime_s(&localTime, &now) != 0)
			return;
#else
		if (!localtime_r(&now, &localTime))
			return;
#endif

		char timestamp[32]{};
		char date[16]{};
		strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", &localTime);
		strftime(date, sizeof(date), "%Y%m%d", &localTime);

		char line[1024]{};
		const int lineLength = snprintf(
			line,
			sizeof(line),
			"[%s] reason=%s block_requested=%u core=%s channel=%u aid=%u pid=%u login=%s player=%s ip=%s "
			"vid=%u sequence=%u expected_sequence=%u hash=%08x expected_hash=%08x\n",
			timestamp,
			reasonText,
			blockRequested,
			g_stHostname.c_str(),
			static_cast<unsigned int>(g_bChannel),
			desc->GetAccountTable().id,
			ch->GetPlayerID(),
			desc->GetAccountTable().login,
			ch->GetName(),
			desc->GetHostName(),
			vid,
			receivedSequence,
			expectedSequence,
			receivedHash,
			expectedHash);

		if (lineLength <= 0)
			return;

		const size_t bytesToWrite = lineLength < static_cast<int>(sizeof(line))
			? static_cast<size_t>(lineLength)
			: sizeof(line) - 1;

		char path[256]{};
		snprintf(
			path,
			sizeof(path),
			"%s/pickup_auth_failures_%s.log",
			LocaleService_GetBasePath().c_str(),
			date);
		if (!AppendLogLine(path, line, bytesToWrite))
			sys_err("ITEM_PICKUP_AUTH_FAILURE cannot append %s: %s", path, strerror(errno));
	}
}

bool ValidateItemPickupAuth(LPCHARACTER ch, const char* data, DWORD& outVID)
{
	outVID = 0;
	if (!ch || !data || !ch->GetDesc())
		return false;

	DWORD vid = 0;
	DWORD receivedSequence = 0;
	DWORD receivedHash = 0;
	std::memcpy(&vid, data + offsetof(TPacketCGItemPickupAuth, vid), sizeof(vid));
	std::memcpy(&receivedSequence, data + offsetof(TPacketCGItemPickupAuth, sequence), sizeof(receivedSequence));
	std::memcpy(&receivedHash, data + offsetof(TPacketCGItemPickupAuth, hash), sizeof(receivedHash));

	const LPDESC desc = ch->GetDesc();
	const DWORD expectedSequence = desc->GetItemPickupSequence();
	const DWORD expectedHash = ComputeItemPickupPacketHash(
		data,
		offsetof(TPacketCGItemPickupAuth, hash),
		desc->GetHandshake());

	if (receivedHash != expectedHash)
	{
		ReportItemPickupAuthFailure(
			ch,
			ITEM_PICKUP_AUTH_BAD_HASH,
			vid,
			receivedSequence,
			expectedSequence,
			receivedHash,
			expectedHash);
		if (g_bItemPickupAutoBlockEnabled)
			BlockItemPickupAccount(ch);
		desc->SetPhase(PHASE_CLOSE);
		return false;
	}

	if (receivedSequence != expectedSequence)
	{
		ReportItemPickupAuthFailure(
			ch,
			ITEM_PICKUP_AUTH_BAD_SEQUENCE,
			vid,
			receivedSequence,
			expectedSequence,
			receivedHash,
			expectedHash);
		desc->SetPhase(PHASE_CLOSE);
		return false;
	}

	desc->AdvanceItemPickupSequence();
	outVID = vid;
	return true;
}

bool DecodeItemPickupAuthFallback(LPCHARACTER ch, const char* data, DWORD& outVID)
{
	outVID = 0;
	if (!ch || !data || !ch->GetDesc())
		return false;

	DWORD vid = 0;
	DWORD receivedSequence = 0;
	std::memcpy(&vid, data + offsetof(TPacketCGItemPickupAuth, vid), sizeof(vid));
	std::memcpy(&receivedSequence, data + offsetof(TPacketCGItemPickupAuth, sequence), sizeof(receivedSequence));

	ch->GetDesc()->SetItemPickupSequence(receivedSequence + 1);
	outVID = vid;
	return true;
}

void RejectLegacyItemPickup(LPCHARACTER ch, DWORD vid)
{
	if (!ch || !ch->GetDesc())
		return;

	const LPDESC desc = ch->GetDesc();
	ReportItemPickupAuthFailure(
		ch,
		ITEM_PICKUP_AUTH_LEGACY_PACKET,
		vid,
		0,
		desc->GetItemPickupSequence(),
		0,
		0);

	if (g_bItemPickupAutoBlockEnabled)
		BlockItemPickupAccount(ch);

	desc->SetPhase(PHASE_CLOSE);
}
