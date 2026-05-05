#include "stdafx.h"
#include "config.h"
#include "utils.h"
#include "desc.h"
#include "desc_client.h"
#include "desc_manager.h"
#include "char.h"
#include "protocol.h"
#include "packet.h"
#include "messenger_manager.h"
#include "sectree_manager.h"
#include "p2p.h"
#include "buffer_manager.h"
#include "guild.h"
#include "guild_manager.h"
#include "locale_service.h"
#include "log.h"


extern int max_bytes_written;
extern int current_bytes_written;
extern int total_bytes_written;

DESC::DESC()
{
	Initialize();
}

DESC::~DESC()
{
}

void DESC::Initialize()
{
	m_bDestroyed = false;

#ifdef ENABLE_BUFFER_SECURITY
	m_dwConnectTime = 0;
	m_dwPacketTick = 0;
	m_iPacketCounter = 0;
#endif

	m_pInputProcessor = nullptr;
	m_lpFdw = nullptr;
	m_sock = INVALID_SOCKET;
	m_iPhase = PHASE_CLOSE;
	m_dwHandle = 0;

	m_wPort = 0;
	m_LastTryToConnectTime = 0;

	m_lpInputBuffer = nullptr;
	m_iMinInputBufferLen = 0;

	m_dwHandshake = 0;
	m_dwHandshakeSentTime = 0;
	m_iHandshakeRetry = 0;
	m_dwClientTime = 0;
	m_bHandshaking = false;

	m_lpBufferedOutputBuffer = nullptr;
	m_lpOutputBuffer = nullptr;

	m_pkPingEvent = nullptr;
	m_lpCharacter = nullptr;
	memset( &m_accountTable, 0, sizeof(m_accountTable) );

	memset( &m_SockAddr, 0, sizeof(m_SockAddr) );

	m_pLogFile = nullptr;


	m_wP2PPort = 0;
	m_bP2PChannel = 0;

	m_bAdminMode = false;
	m_bPong = true;
	m_bChannelStatusRequested = false;


	m_pkLoginKey = nullptr;
	m_dwLoginKey = 0;
	m_dwPanamaKey = 0;


	m_bCRCMagicCubeIdx = 0;
	m_dwProcCRC = 0;
	m_dwFileCRC = 0;
	m_bHackCRCQuery = 0;

	m_outtime = 0;
	m_playtime = 0;
	m_offtime = 0;

	m_pkDisconnectEvent = nullptr;

}

void DESC::Destroy()
{
	if (m_bDestroyed) {
		return;
	}
	m_bDestroyed = true;

	if (m_pkLoginKey)
		m_pkLoginKey->Expire();

	if (GetAccountTable().id)
		DESC_MANAGER::instance().DisconnectAccount(GetAccountTable().login);

	if (m_pLogFile)
	{
		fclose(m_pLogFile);
		m_pLogFile = nullptr;
	}

	bool bCanUseLoginByKey = true; // @fixme353
	if (m_lpCharacter)
	{
		bCanUseLoginByKey = m_lpCharacter->CanUseLoginByKey(); // @fixme353
		m_lpCharacter->Disconnect("DESC::~DESC");
		m_lpCharacter = nullptr;
	}

	SAFE_BUFFER_DELETE(m_lpOutputBuffer);
	SAFE_BUFFER_DELETE(m_lpInputBuffer);

	event_cancel(&m_pkPingEvent);
	event_cancel(&m_pkDisconnectEvent);

	if (!g_bAuthServer)
	{
		if (m_accountTable.login[0] && m_accountTable.passwd[0])
		{
			TLogoutPacket pack;

			pack.bCanUseLoginByKey = bCanUseLoginByKey; // @fixme353
			strlcpy(pack.login, m_accountTable.login, sizeof(pack.login));
			strlcpy(pack.passwd, m_accountTable.passwd, sizeof(pack.passwd));

			db_clientdesc->DBPacket(HEADER_GD_LOGOUT, m_dwHandle, &pack, sizeof(TLogoutPacket));
		}
	}

	if (m_sock != INVALID_SOCKET)
	{
		sys_log(0, "SYSTEM: closing socket. DESC #%d", m_sock);
		Log("SYSTEM: closing socket. DESC #%d", m_sock);
		fdwatch_del_fd(m_lpFdw, m_sock);


		socket_close(m_sock);
		m_sock = INVALID_SOCKET;
	}

}

EVENTFUNC(ping_event)
{
	const auto info = dynamic_cast<DESC::desc_event_info*>( event->info );

	if ( info == nullptr)
	{
		sys_err( "ping_event> <Factor> Null pointer" );
		return 0;
	}

	const LPDESC desc = info->desc;

	if (desc->IsAdminMode())
		return (ping_event_second_cycle);

	if (!desc->IsPong())
	{
		sys_log(0, "PING_EVENT: no pong %s", desc->GetHostName());

		DESC_MANAGER::instance().DestroyLoginKey(desc); // @fixme319
		desc->SetPhase(PHASE_CLOSE);

		return (ping_event_second_cycle);
	}
	else
	{
		TPacketGCPing p;
		p.header = HEADER_GC_PING;
		desc->Packet(&p, sizeof(struct packet_ping));
		desc->SetPong(false);
	}

	desc->SendHandshake(get_dword_time(), 0);

	return (ping_event_second_cycle);
}

bool DESC::IsPong() const
{
	return m_bPong;
}

void DESC::SetPong(bool b)
{
	m_bPong = b;
}

bool DESC::Setup(LPFDWATCH _fdw, socket_t _fd, const struct sockaddr_in & c_rSockAddr, DWORD _handle, DWORD _handshake)
{
	m_lpFdw		= _fdw;
	m_sock		= _fd;

#ifdef ENABLE_BUFFER_SECURITY
	m_dwConnectTime = get_dword_time();
#endif

	m_stHost		= inet_ntoa(c_rSockAddr.sin_addr);
	m_wPort			= c_rSockAddr.sin_port;
	m_dwHandle		= _handle;

	m_lpOutputBuffer = buffer_new(DEFAULT_PACKET_BUFFER_SIZE * 2);

	m_iMinInputBufferLen = MAX_INPUT_LEN >> 1;
	m_lpInputBuffer = buffer_new(MAX_INPUT_LEN);

	m_SockAddr = c_rSockAddr;

	fdwatch_add_fd(m_lpFdw, m_sock, this, FDW_READ, false);

	// Ping Event
	desc_event_info* info = AllocEventInfo<desc_event_info>();

	info->desc = this;
	assert(m_pkPingEvent == nullptr);

	m_pkPingEvent = event_create(ping_event, info, ping_event_second_cycle);


	// Set Phase to handshake
	SetPhase(PHASE_HANDSHAKE);
	StartHandshake(_handshake);

	sys_log(0, "SYSTEM: new connection from [%s] fd: %d handshake %u output input_len %d, ptr %p",
			m_stHost.c_str(), m_sock, m_dwHandshake, buffer_size(m_lpInputBuffer), this);

	Log("SYSTEM: new connection from [%s] fd: %d handshake %u ptr %p", m_stHost.c_str(), m_sock, m_dwHandshake, this);
	return true;
}

#ifdef ENABLE_BUFFER_SECURITY
bool DESC::CheckPacketRate()
{
	// --- Packet flood detection (clients only) ---
	if (GetType() == DESC_TYPE_CONNECTOR || m_iPhase == PHASE_P2P)
		return false; // exemption for internal connections

	const DWORD dwNow = get_dword_time();

	if (dwNow - m_dwPacketTick >= 1000)
	{
		m_dwPacketTick = dwNow;
		m_iPacketCounter = 0;
	}

	if (++m_iPacketCounter > 256)
	{
		sys_err("DESC::CheckPacketRate: packet flood from %s (%d packets/sec)", GetHostName(), m_iPacketCounter);
		return true; // flood detected
	}

	return false;
}
#endif

int DESC::ProcessInput()
{
	ssize_t bytes_read;

	if (!m_lpInputBuffer)
	{
		sys_err("DESC::ProcessInput : nil input buffer");
		return -1;
	}

	buffer_adjust_size(m_lpInputBuffer, m_iMinInputBufferLen);

#ifdef ENABLE_BUFFER_SECURITY
	// --- Handshake timeout ---
	if (m_iPhase == PHASE_HANDSHAKE)
	{
		if (get_dword_time() - m_dwConnectTime > 10000)
		{
			sys_err("DESC::ProcessInput: handshake timeout from %s", GetHostName());
			return -1;
		}
	}
#endif

	bytes_read = socket_read(m_sock, (char *) buffer_write_peek(m_lpInputBuffer), buffer_has_space(m_lpInputBuffer));

	if (bytes_read < 0)
		return -1;
	else if (bytes_read == 0)
		return 0;

	buffer_write_proceed(m_lpInputBuffer, bytes_read);

#ifdef ENABLE_BUFFER_SECURITY
	// --- Input buffer size cap (2 MB, clients only) ---
	if (GetType() != DESC_TYPE_CONNECTOR && m_iPhase != PHASE_P2P)
	{
		if (buffer_size(m_lpInputBuffer) > (2 * 1024 * 1024))
		{
			sys_err("DESC::ProcessInput: input buffer too large (%u) from %s", (unsigned)buffer_size(m_lpInputBuffer), GetHostName());
			return -1;
		}
	}
#endif

	if (!m_pInputProcessor)
		sys_err("no input processor");
	int iBytesProceed = 0;
	while (!m_pInputProcessor->Process(this, buffer_read_peek(m_lpInputBuffer), buffer_size(m_lpInputBuffer), iBytesProceed))
	{
		buffer_read_proceed(m_lpInputBuffer, iBytesProceed);
		iBytesProceed = 0;
	}
	buffer_read_proceed(m_lpInputBuffer, iBytesProceed);

	return (bytes_read);
}

int DESC::ProcessOutput()
{
	if (buffer_size(m_lpOutputBuffer) <= 0)
		return 0;

	const int buffer_left = fdwatch_get_buffer_size(m_lpFdw, m_sock);

	if (buffer_left <= 0)
		return 0;

	const int bytes_to_write = MIN(buffer_left, buffer_size(m_lpOutputBuffer));

	if (bytes_to_write == 0)
		return 0;

	const int result = socket_write(m_sock, (const char *) buffer_read_peek(m_lpOutputBuffer), bytes_to_write);

	if (result == 0)
	{
		//sys_log(0, "%d bytes written to %s first %u", bytes_to_write, GetHostName(), *(BYTE *) buffer_read_peek(m_lpOutputBuffer));
		//Log("%d bytes written", bytes_to_write);
		max_bytes_written = MAX(bytes_to_write, max_bytes_written);

		total_bytes_written += bytes_to_write;
		current_bytes_written += bytes_to_write;

		buffer_read_proceed(m_lpOutputBuffer, bytes_to_write);

		if (buffer_size(m_lpOutputBuffer) != 0)
			fdwatch_add_fd(m_lpFdw, m_sock, this, FDW_WRITE, true);
	}

	return (result);
}

void DESC::BufferedPacket(const void * c_pvData, int iSize)
{
	if (m_iPhase == PHASE_CLOSE)
		return;

	if (!m_lpBufferedOutputBuffer)
		m_lpBufferedOutputBuffer = buffer_new(MAX(1024, iSize));

	buffer_write(m_lpBufferedOutputBuffer, c_pvData, iSize);
}

void DESC::Packet(const void * c_pvData, int iSize)
{
	assert(iSize > 0);

	if (m_iPhase == PHASE_CLOSE)
		return;

#ifdef ENABLE_SYSLOG_PACKET_SENT
	std::string stName = GetCharacter()? GetCharacter()->GetName() : GetHostName();
	sys_log(0, "SENT HEADER : %u to %s  (size %d) ", *(static_cast<const BYTE*>(c_pvData)) , stName.c_str(), iSize );
#endif

	if (m_stRelayName.length() != 0)
	{
		TPacketGGRelay p;

		p.bHeader = HEADER_GG_RELAY;
		strlcpy(p.szName, m_stRelayName.c_str(), sizeof(p.szName));
		p.lSize = iSize;

		if (!packet_encode(m_lpOutputBuffer, &p, sizeof(p)))
		{
			m_iPhase = PHASE_CLOSE;
			return;
		}

		m_stRelayName.clear();

		if (!packet_encode(m_lpOutputBuffer, c_pvData, iSize))
		{
			m_iPhase = PHASE_CLOSE;
			return;
		}
	}
	else
	{
		if (m_lpBufferedOutputBuffer)
		{
			buffer_write(m_lpBufferedOutputBuffer, c_pvData, iSize);

			c_pvData = buffer_read_peek(m_lpBufferedOutputBuffer);
			iSize = buffer_size(m_lpBufferedOutputBuffer);
		}

		// @fixme325 BEGIN (buffer adjust size, even without +8 is ok)
		if (buffer_has_space(m_lpOutputBuffer) < iSize + 8)
			buffer_adjust_size(m_lpOutputBuffer, iSize + 8);

		if (!packet_encode(m_lpOutputBuffer, c_pvData, iSize))
			m_iPhase = PHASE_CLOSE;
		// @fixme325 END

		SAFE_BUFFER_DELETE(m_lpBufferedOutputBuffer);
	}

	//sys_log(0, "%d bytes written (first byte %d)", iSize, *(BYTE *) c_pvData);
	if (m_iPhase != PHASE_CLOSE)
		fdwatch_add_fd(m_lpFdw, m_sock, this, FDW_WRITE, true);
}

void DESC::LargePacket(const void * c_pvData, int iSize)
{
	buffer_adjust_size(m_lpOutputBuffer, iSize);
	sys_log(0, "LargePacket Size %d / %d", iSize, buffer_size(m_lpOutputBuffer)); // @warme016 buffer size added

	Packet(c_pvData, iSize);
}

void DESC::SetPhase(int _phase)
{
	m_iPhase = _phase;

	TPacketGCPhase pack;
	pack.header = HEADER_GC_PHASE;
	pack.phase = _phase;
	Packet(&pack, sizeof(TPacketGCPhase));

	switch (m_iPhase)
	{
		case PHASE_CLOSE:

			//MessengerManager::instance().Logout(GetAccountTable().login);
			m_pInputProcessor = &m_inputClose;
			break;

		case PHASE_HANDSHAKE:
			m_pInputProcessor = &m_inputHandshake;
			break;

		case PHASE_SELECT:

		case PHASE_LOGIN:
		case PHASE_LOADING:
			m_pInputProcessor = &m_inputLogin;
			break;

		case PHASE_GAME:
		case PHASE_DEAD:
			m_pInputProcessor = &m_inputMain;
			break;

		case PHASE_AUTH:
			m_pInputProcessor = &m_inputAuth;
			sys_log(0, "AUTH_PHASE %p", this);
			break;
	}
}

void DESC::BindAccountTable(TAccountTable * pAccountTable)
{
	assert(pAccountTable != nullptr);
	thecore_memcpy(&m_accountTable, pAccountTable, sizeof(TAccountTable));
	DESC_MANAGER::instance().ConnectAccount(m_accountTable.login, this);
}

void DESC::Log(const char * format, ...) const
{
	if (!m_pLogFile)
		return;

	va_list args;

	const time_t ct = get_global_time();
	const struct tm tm = *localtime(&ct);

	fprintf(m_pLogFile,
			"%02d %02d %02d:%02d:%02d | ",
			tm.tm_mon + 1,
			tm.tm_mday,
			tm.tm_hour,
			tm.tm_min,
			tm.tm_sec);

	va_start(args, format);
	vfprintf(m_pLogFile, format, args);
	va_end(args);

	fputs("\n", m_pLogFile);

	fflush(m_pLogFile);
}

void DESC::StartHandshake(DWORD _handshake)
{
	// Handshake
	m_dwHandshake = _handshake;

	SendHandshake(get_dword_time(), 0);

	m_iHandshakeRetry = 0;
}

void DESC::SendHandshake(DWORD dwCurTime, long lNewDelta)
{
	TPacketGCHandshake pack;

	pack.bHeader		= HEADER_GC_HANDSHAKE;
	pack.dwHandshake	= m_dwHandshake;
	pack.dwTime			= dwCurTime;
	pack.lDelta			= lNewDelta;

	Packet(&pack, sizeof(TPacketGCHandshake));

	m_dwHandshakeSentTime = dwCurTime;
	m_bHandshaking = true;
}

bool DESC::HandshakeProcess(DWORD dwTime, long lDelta, bool bInfiniteRetry)
{
	const DWORD dwCurTime = get_dword_time();

	if (lDelta < 0)
	{
		sys_err("Desc::HandshakeProcess : value error (lDelta %d, ip %s)", lDelta, m_stHost.c_str());
		return false;
	}

	const int bias = (int) (dwCurTime - (dwTime + lDelta));

	if (bias >= 0 && bias <= 50)
	{
		if (bInfiniteRetry)
		{
			const BYTE bHeader = HEADER_GC_TIME_SYNC;
			Packet(&bHeader, sizeof(BYTE));
		}

		if (GetCharacter())
			sys_log(0, "Handshake: client_time %u server_time %u name: %s", m_dwClientTime, dwCurTime, GetCharacter()->GetName());
		else
			sys_log(0, "Handshake: client_time %u server_time %u, delta: %ld", m_dwClientTime, dwCurTime, lDelta); // @warme016 missing delta

		m_dwClientTime = dwCurTime;
		m_bHandshaking = false;
		return true;
	}

	long lNewDelta = (long) (dwCurTime - dwTime) / 2;

	if (lNewDelta < 0)
	{
		sys_log(0, "Handshake: lower than zero %d", lNewDelta);
		lNewDelta = (dwCurTime - m_dwHandshakeSentTime) / 2;
	}

	sys_log(1, "Handshake: ServerTime %u dwTime %u lDelta %d SentTime %u lNewDelta %d", dwCurTime, dwTime, lDelta, m_dwHandshakeSentTime, lNewDelta);

	if (!bInfiniteRetry)
		if (++m_iHandshakeRetry > HANDSHAKE_RETRY_LIMIT)
		{
			sys_err("handshake retry limit reached! (limit %d character %s)",
					HANDSHAKE_RETRY_LIMIT, GetCharacter() ? GetCharacter()->GetName() : "!NO CHARACTER!");
			SetPhase(PHASE_CLOSE);
			return false;
		}

	SendHandshake(dwCurTime, lNewDelta);
	return false;
}

bool DESC::IsHandshaking() const
{
	return m_bHandshaking;
}

DWORD DESC::GetClientTime() const
{
	return m_dwClientTime;
}


void DESC::SetRelay(const char * c_pszName)
{
	m_stRelayName = c_pszName;
}

void DESC::BindCharacter(LPCHARACTER ch)
{
	m_lpCharacter = ch;
}

void DESC::FlushOutput()
{
	if (m_sock == INVALID_SOCKET) {
		return;
	}

	if (buffer_size(m_lpOutputBuffer) <= 0)
		return;

	struct timeval sleep_tv, now_tv, start_tv;
	int event_triggered = false;

	gettimeofday(&start_tv, nullptr);

	socket_block(m_sock);
	sys_log(0, "FLUSH START %d", buffer_size(m_lpOutputBuffer));

	while (buffer_size(m_lpOutputBuffer) > 0)
	{
		gettimeofday(&now_tv, nullptr);

		const int iSecondsPassed = now_tv.tv_sec - start_tv.tv_sec;

		if (iSecondsPassed > 10)
		{
			if (!event_triggered || iSecondsPassed > 20)
			{
				SetPhase(PHASE_CLOSE);
				break;
			}
		}

		sleep_tv.tv_sec = 0;
		sleep_tv.tv_usec = 10000;

		const int num_events = fdwatch(m_lpFdw, &sleep_tv);

		if (num_events < 0)
		{
			sys_err("num_events < 0 : %d", num_events);
			break;
		}

		int event_idx;

		for (event_idx = 0; event_idx < num_events; ++event_idx)
		{
			const auto d2 = (LPDESC) fdwatch_get_client_data(m_lpFdw, event_idx);

			if (d2 != this)
				continue;

			switch (fdwatch_check_event(m_lpFdw, m_sock, event_idx))
			{
				case FDW_WRITE:
					event_triggered = true;

					if (ProcessOutput() < 0)
					{
						sys_err("Cannot flush output buffer");
						SetPhase(PHASE_CLOSE);
					}
					break;

				case FDW_EOF:
					SetPhase(PHASE_CLOSE);
					break;
			}
		}

		if (IsPhase(PHASE_CLOSE))
			break;
	}

	if (buffer_size(m_lpOutputBuffer) == 0)
		sys_log(0, "FLUSH SUCCESS");
	else
		sys_log(0, "FLUSH FAIL");

	usleep(250000);
}

EVENTFUNC(disconnect_event)
{
	const auto info = dynamic_cast<DESC::desc_event_info*>( event->info );

	if ( info == nullptr)
	{
		sys_err( "disconnect_event> <Factor> Null pointer" );
		return 0;
	}

	const LPDESC d = info->desc;

	DESC_MANAGER::instance().DestroyLoginKey(d); // @fixme319
	d->m_pkDisconnectEvent = nullptr;
	d->SetPhase(PHASE_CLOSE);
	return 0;
}

bool DESC::DelayedDisconnect(int iSec)
{
	if (m_pkDisconnectEvent != nullptr) {
		return false;
	}

	desc_event_info* info = AllocEventInfo<desc_event_info>();
	info->desc = this;

	m_pkDisconnectEvent = event_create(disconnect_event, info, PASSES_PER_SEC(iSec));
	return true;
}

void DESC::DisconnectOfSameLogin()
{
	if (GetCharacter())
	{
		if (m_pkDisconnectEvent)
			return;

		GetCharacter()->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("다른 컴퓨터에서 로그인 하여 접속을 종료 합니다."));
		DelayedDisconnect(5);
	}
	else
	{
		SetPhase(PHASE_CLOSE);
	}
}

void DESC::SetAdminMode()
{
	m_bAdminMode = true;
}

bool DESC::IsAdminMode() const
{
	return m_bAdminMode;
}


void DESC::SendLoginSuccessPacket()
{
	TAccountTable & rTable = GetAccountTable();

	TPacketGCLoginSuccess p;

	p.bHeader    = HEADER_GC_LOGIN_SUCCESS_NEWSLOT;

	p.handle     = GetHandle();
	p.random_key = DESC_MANAGER::instance().MakeRandomKey(GetHandle()); // FOR MARK
	thecore_memcpy(p.players, rTable.players, sizeof(rTable.players));

	for (int i = 0; i < PLAYER_PER_ACCOUNT; ++i)
	{
#ifdef ENABLE_NEWSTUFF
		if (!g_stProxyIP.empty())
			rTable.players[i].lAddr=inet_addr(g_stProxyIP.c_str());
#endif
		const CGuild* g = CGuildManager::instance().GetLinkedGuild(rTable.players[i].dwID);

		if (g)
		{
			p.guild_id[i] = g->GetID();
			strlcpy(p.guild_name[i], g->GetName(), sizeof(p.guild_name[i]));
		}
		else
		{
			p.guild_id[i] = 0;
			p.guild_name[i][0] = '\0';
		}
	}

	Packet(&p, sizeof(TPacketGCLoginSuccess));
}

void DESC::SetLoginKey(DWORD dwKey)
{
	m_dwLoginKey = dwKey;
}

void DESC::SetLoginKey(CLoginKey * pkKey)
{
	m_pkLoginKey = pkKey;
	sys_log(0, "SetLoginKey %u", m_pkLoginKey->m_dwKey);
}

DWORD DESC::GetLoginKey() const
{
	if (m_pkLoginKey)
		return m_pkLoginKey->m_dwKey;

	return m_dwLoginKey;
}

const BYTE* GetKey_20050304Myevan()
{
	static bool bGenerated = false;
	static DWORD s_adwKey[1938];

	if (!bGenerated)
	{
		bGenerated = true;
		DWORD seed = 1491971513;

		for (UINT i = 0; i < BYTE(seed); ++i)
		{
			seed ^= 2148941891ul;
			seed += 3592385981ul;

			s_adwKey[i] = seed;
		}
	}

	return (const BYTE*)s_adwKey;
}


void DESC::AssembleCRCMagicCube(BYTE bProcPiece, BYTE bFilePiece)
{
	static BYTE abXORTable[32] =
	{
		102,  30, 0, 0, 0, 0, 0, 0,
		188,  44, 0, 0, 0, 0, 0, 0,
		39, 201, 0, 0, 0, 0, 0, 0,
		43,   5, 0, 0, 0, 0, 0, 0,
	};

	bProcPiece = (bProcPiece ^ abXORTable[m_bCRCMagicCubeIdx]);
	bFilePiece = (bFilePiece ^ abXORTable[m_bCRCMagicCubeIdx+1]);

	m_dwProcCRC |= bProcPiece << m_bCRCMagicCubeIdx;
	m_dwFileCRC |= bFilePiece << m_bCRCMagicCubeIdx;

	m_bCRCMagicCubeIdx += 8;

	if (!(m_bCRCMagicCubeIdx & 31))
	{
		m_dwProcCRC = 0;
		m_dwFileCRC = 0;
		m_bCRCMagicCubeIdx = 0;
	}
}


BYTE DESC::GetEmpire() const
{
	return m_accountTable.bEmpire;
}

void DESC::ChatPacket(BYTE type, const char * format, ...)
{
	char chatbuf[CHAT_MAX_LEN + 1];
	va_list args;

	va_start(args, format);
	const int len = vsnprintf(chatbuf, sizeof(chatbuf), format, args);
	va_end(args);

	struct packet_chat pack_chat;

	pack_chat.header    = HEADER_GC_CHAT;
	pack_chat.size      = sizeof(struct packet_chat) + len;
	pack_chat.type      = type;
	pack_chat.id        = 0;
#if !defined(__BL_MULTI_LANGUAGE_PREMIUM__)
	pack_chat.bEmpire = GetEmpire();
#endif

	TEMP_BUFFER buf;
	buf.write(&pack_chat, sizeof(struct packet_chat));
	buf.write(chatbuf, len);

	Packet(buf.read_peek(), buf.size());
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
