#include "stdafx.h"
#include <sstream>

#include "desc.h"
#include "desc_manager.h"
#include "char.h"
#include "buffer_manager.h"
#include "config.h"
#include "profiler.h"
#include "p2p.h"
#include "log.h"
#include "db.h"
#include "questmanager.h"
#include "desc_client.h"
#include "fishing.h"
#include "priv_manager.h"
#include "../../common/CommonDefines.h"

#include "utils.h"
#include "../../common/PulseManager.h"

bool IsEmptyAdminPage()
{
	return g_stAdminPageIP.empty();
}

bool IsAdminPage(const char * ip)
{
	for (size_t n = 0; n < g_stAdminPageIP.size(); ++n)
	{
		if (g_stAdminPageIP[n] == ip)
			return 1;
	}
	return 0;
}

void ClearAdminPages()
{
	for (size_t n = 0; n < g_stAdminPageIP.size(); ++n)
		g_stAdminPageIP[n].clear();

	g_stAdminPageIP.clear();
}

CInputProcessor::CInputProcessor() : m_pPacketInfo(nullptr), m_iBufferLeft(0)
{
	if (!m_pPacketInfo)
		BindPacketInfo(&m_packetInfoCG);
}

void CInputProcessor::BindPacketInfo(CPacketInfo * pPacketInfo)
{
	m_pPacketInfo = pPacketInfo;
}

bool CInputProcessor::Process(LPDESC lpDesc, const void * c_pvOrig, int iBytes, int & r_iBytesProceed)
{
	auto c_pData = (const char *) c_pvOrig;

	BYTE	bLastHeader = 0;
	int		iLastPacketLen = 0;
	int		iPacketLen;

	if (!m_pPacketInfo)
	{
		sys_err("No packet info has been binded to");
		return true;
	}

	for (m_iBufferLeft = iBytes; m_iBufferLeft > 0;)
	{
#ifdef ENABLE_BUFFER_SECURITY
		if (lpDesc->CheckPacketRate())
		{
			lpDesc->SetPhase(PHASE_CLOSE);
			r_iBytesProceed = iBytes;
			return true;
		}
#endif

		BYTE bHeader = (BYTE) *(c_pData);
		const char * c_pszName;

		if (bHeader == 0)
			iPacketLen = 1;
		else if (!m_pPacketInfo->Get(bHeader, &iPacketLen, &c_pszName))
		{
			sys_err("UNKNOWN HEADER: %d, LAST HEADER: %d(%d), REMAIN BYTES: %d, fd: %d",
					bHeader, bLastHeader, iLastPacketLen, m_iBufferLeft, lpDesc->GetSocket());
			//printdata((BYTE *) c_pvOrig, m_iBufferLeft);
			lpDesc->SetPhase(PHASE_CLOSE);
			return true;
		}

		if (m_iBufferLeft < iPacketLen)
			return true;

		if (bHeader)
		{
			if (test_server && bHeader != HEADER_CG_MOVE)
				sys_log(0, "Packet Analyze [Header %d][bufferLeft %d] ", bHeader, m_iBufferLeft);

			m_pPacketInfo->Start();

			const int iExtraPacketSize = Analyze(lpDesc, bHeader, c_pData);

			if (iExtraPacketSize < 0)
				return true;

			iPacketLen += iExtraPacketSize;
			lpDesc->Log("%s %d", c_pszName, iPacketLen);
			m_pPacketInfo->End();
		}


		c_pData	+= iPacketLen;
		m_iBufferLeft -= iPacketLen;
		r_iBytesProceed += iPacketLen;

		iLastPacketLen = iPacketLen;
		bLastHeader	= bHeader;

		if (GetType() != lpDesc->GetInputProcessor()->GetType())
			return false;
	}

	return true;
}

void CInputProcessor::Pong(LPDESC d) const
{
	d->SetPong(true);
}

void CInputProcessor::Handshake(LPDESC d, const char * c_pData) const
{
	const auto p = (TPacketCGHandshake *) c_pData;

	if (d->GetHandshake() != p->dwHandshake)
	{
		sys_err("Invalid Handshake on %d", d->GetSocket());
		d->SetPhase(PHASE_CLOSE);
	}
	else
	{
		if (d->IsPhase(PHASE_HANDSHAKE))
		{
			if (d->HandshakeProcess(p->dwTime, p->lDelta, false))
			{
				d->ResetItemPickupSequence();
				if (g_bAuthServer)
					d->SetPhase(PHASE_AUTH);
				else
					d->SetPhase(PHASE_LOGIN);
			}
		}
		else
			d->HandshakeProcess(p->dwTime, p->lDelta, true);
	}
}

void CInputProcessor::Version(LPCHARACTER ch, const char* c_pData) const
{
	if (!ch)
		return;

	const auto p = (TPacketCGClientVersion2 *) c_pData;
	sys_log(0, "VERSION: %s %s %s", ch->GetName(), p->timestamp, p->filename);
	ch->GetDesc()->SetClientVersion(p->timestamp);
}

void LoginFailure(LPDESC d, const char * c_pszStatus)
{
	if (!d)
		return;

	TPacketGCLoginFailure failurePacket;

	failurePacket.header = HEADER_GC_LOGIN_FAILURE;
	strlcpy(failurePacket.szStatus, c_pszStatus, sizeof(failurePacket.szStatus));

	d->Packet(&failurePacket, sizeof(failurePacket));
}

CInputHandshake::CInputHandshake()
{
	auto pkPacketInfo = M2_NEW CPacketInfoCG;
	m_pMainPacketInfo = m_pPacketInfo;
	BindPacketInfo(pkPacketInfo);
}

CInputHandshake::~CInputHandshake()
{
	if(nullptr != m_pPacketInfo )
	{
		M2_DELETE(m_pPacketInfo);
		m_pPacketInfo = nullptr;
	}
}

std::vector<TPlayerTable> g_vec_save;

// BLOCK_CHAT
ACMD(do_block_chat);
// END_OF_BLOCK_CHAT

int CInputHandshake::Analyze(LPDESC d, BYTE bHeader, const char * c_pData)
{
	if (bHeader == 10)
		return 0;

#ifdef HANDSHAKE_PACKET_ANTI_FLOOD
	if (d)
	{
		if (thecore_pulse() > d->GetPacketAntiFloodPulse() + PASSES_PER_SEC(1))
		{
			d->SetPacketAntiFloodCount(0);
			d->SetPacketAntiFloodPulse(thecore_pulse());
		}
		if (d->IncreasePacketAntiFloodCount() >= 100)
		{
			sys_err("<Flood packet> header(%d) host(%s:%u)", bHeader, d->GetHostName(), d->GetPort());
			d->SetPhase(PHASE_CLOSE);
			return 0;
		}
	}
#endif

	if (bHeader == HEADER_CG_TEXT)
	{
#ifdef ENABLE_PORT_SECURITY
		if (IsEmptyAdminPage() || !IsAdminPage(inet_ntoa(d->GetAddr().sin_addr))) // block if adminpage is not set or if not admin
		{
			sys_log(0, "SOCKET_CMD: BLOCK FROM(%s)", d->GetHostName());
			d->SetPhase(PHASE_CLOSE);
			return 0;
		}
#endif
		++c_pData;
		const char * c_pSep;

		if (!(c_pSep = strchr(c_pData, '\n')))
		{
			d->SetPhase(PHASE_CLOSE); // @fixme187 setphase+ret0
			return 0;
		}

		if (*(c_pSep - 1) == '\r')
			--c_pSep;

		std::string stResult;
		std::string stBuf;
		stBuf.assign(c_pData, 0, c_pSep - c_pData);

		sys_log(0, "SOCKET_CMD: FROM(%s) CMD(%s)", d->GetHostName(), stBuf.c_str());

		if (!stBuf.compare("IS_SERVER_UP"))
		{
			if (g_bNoMoreClient)
				stResult = "NO";
			else
				stResult = "YES";
		}
		else if (stBuf == g_stAdminPagePassword)
		{
			if (!IsEmptyAdminPage())
			{
				if (!IsAdminPage(inet_ntoa(d->GetAddr().sin_addr)))
				{
					char szTmp[64];
					snprintf(szTmp, sizeof(szTmp), "WEBADMIN : Wrong Connector : %s", inet_ntoa(d->GetAddr().sin_addr));
					stResult += szTmp;
				}
				else
				{
					d->SetAdminMode();
					stResult = "UNKNOWN";
				}
			}
			else
			{
				d->SetAdminMode();
				stResult = "UNKNOWN";
			}
		}
		else if (!stBuf.compare("USER_COUNT"))
		{
			char szTmp[64];

			if (!IsEmptyAdminPage())
			{
				if (!IsAdminPage(inet_ntoa(d->GetAddr().sin_addr)))
				{
					snprintf(szTmp, sizeof(szTmp), "WEBADMIN : Wrong Connector : %s", inet_ntoa(d->GetAddr().sin_addr));
				}
				else
				{
					int iTotal;
					int * paiEmpireUserCount;
					int iLocal;
					DESC_MANAGER::instance().GetUserCount(iTotal, &paiEmpireUserCount, iLocal);
					snprintf(szTmp, sizeof(szTmp), "%d %d %d %d %d", iTotal, paiEmpireUserCount[1], paiEmpireUserCount[2], paiEmpireUserCount[3], iLocal);
				}
			}
			else
			{
				int iTotal;
				int * paiEmpireUserCount;
				int iLocal;
				DESC_MANAGER::instance().GetUserCount(iTotal, &paiEmpireUserCount, iLocal);
				snprintf(szTmp, sizeof(szTmp), "%d %d %d %d %d", iTotal, paiEmpireUserCount[1], paiEmpireUserCount[2], paiEmpireUserCount[3], iLocal);
			}
			stResult += szTmp;
		}
		else if (!stBuf.compare("CHECK_P2P_CONNECTIONS"))
		{
			std::ostringstream oss(std::ostringstream::out);

			oss << "P2P CONNECTION NUMBER : " << P2P_MANAGER::instance().GetDescCount() << "\n";
			std::string hostNames;
			P2P_MANAGER::Instance().GetP2PHostNames(hostNames);
			oss << hostNames;
			stResult = oss.str();
			TPacketGGCheckAwakeness packet;
			packet.bHeader = HEADER_GG_CHECK_AWAKENESS;

			P2P_MANAGER::instance().Send(&packet, sizeof(packet));
		}
		else if (!stBuf.compare("PACKET_INFO"))
		{
			m_pMainPacketInfo->Log("packet_info.txt");
			stResult = "OK";
		}
		else if (!stBuf.compare("PROFILE"))
		{
			CProfiler::instance().Log("profile.txt");
			stResult = "OK";
		}
		//gift notify delete command
		else if (!stBuf.compare(0,15,"DELETE_AWARDID "))
			{
				char szTmp[64];
				std::string msg = stBuf.substr(15,26);

				TPacketDeleteAwardID p;
				p.dwID = (DWORD)(atoi(msg.c_str()));
				snprintf(szTmp,sizeof(szTmp),"Sent to DB cache to delete ItemAward, id: %d",p.dwID);
				//sys_log(0,"%d",p.dwID);
				// strlcpy(p.login, msg.c_str(), sizeof(p.login));
				db_clientdesc->DBPacket(HEADER_GD_DELETE_AWARDID, 0, &p, sizeof(p));
				stResult += szTmp;
			}
		else
		{
			stResult = "UNKNOWN";

			if (d->IsAdminMode())
			{
				if (!stBuf.compare(0, 7, "NOTICE "))
				{
					std::string msg = stBuf.substr(7, 50);
					LogManager::instance().CharLog(0, 0, 0, 1, "NOTICE", msg.c_str(), d->GetHostName());
					BroadcastNotice(msg.c_str());
				}
#ifdef ENABLE_FULL_NOTICE
				else if (!stBuf.compare(0, 11, "BIG_NOTICE "))
				{
					std::string msg = stBuf.substr(11, 50);
					LogManager::instance().CharLog(0, 0, 0, 1, "BIG_NOTICE", msg.c_str(), d->GetHostName());
					BroadcastNotice(msg.c_str(), true);
				}
#endif
				else if (!stBuf.compare("SHUTDOWN"))
				{
					LogManager::instance().CharLog(0, 0, 0, 2, "SHUTDOWN", "", d->GetHostName());
					TPacketGGShutdown p;
					p.bHeader = HEADER_GG_SHUTDOWN;
					P2P_MANAGER::instance().Send(&p, sizeof(TPacketGGShutdown));
					sys_err("Accept shutdown command from %s.", d->GetHostName());
					Shutdown(10);
				}
				else if (!stBuf.compare("SHUTDOWN_ONLY"))
				{
					LogManager::instance().CharLog(0, 0, 0, 2, "SHUTDOWN", "", d->GetHostName());
					sys_err("Accept shutdown only command from %s.", d->GetHostName());
					Shutdown(10);
				}
				else if (!stBuf.compare(0, 3, "DC "))
				{
					std::string msg = stBuf.substr(3, LOGIN_MAX_LEN);

					TPacketGGDisconnect pgg;

					pgg.bHeader = HEADER_GG_DISCONNECT;
					strlcpy(pgg.szLogin, msg.c_str(), sizeof(pgg.szLogin));

					P2P_MANAGER::instance().Send(&pgg, sizeof(TPacketGGDisconnect));
					DESC_MANAGER::instance().DestroyLoginKey(msg); // @fixme319 (only wrapped)
				}
				else if (!stBuf.compare(0, 10, "RELOAD_CRC"))
				{
					LoadValidCRCList();

					BYTE bHeader = HEADER_GG_RELOAD_CRC_LIST;
					P2P_MANAGER::instance().Send(&bHeader, sizeof(BYTE));
					stResult = "OK";
				}
				else if (!stBuf.compare(0, 20, "CHECK_CLIENT_VERSION"))
				{
					CheckClientVersion();

					BYTE bHeader = HEADER_GG_CHECK_CLIENT_VERSION;
					P2P_MANAGER::instance().Send(&bHeader, sizeof(BYTE));
					stResult = "OK";
				}
				else if (!stBuf.compare(0, 6, "RELOAD"))
				{
					if (stBuf.size() == 6)
					{
						LoadStateUserCount();
						db_clientdesc->DBPacket(HEADER_GD_RELOAD_PROTO, 0, nullptr, 0);
					}
					else
					{
						char c = stBuf[7];

						switch (LOWER(c))
						{
							case 'u':
								LoadStateUserCount();
								break;

							case 'p':
								db_clientdesc->DBPacket(HEADER_GD_RELOAD_PROTO, 0, nullptr, 0);
								break;

							case 'q':
								quest::CQuestManager::instance().Reload();
								break;

							case 'f':
								fishing::Initialize();
								break;

							case 'a':
								db_clientdesc->DBPacket(HEADER_GD_RELOAD_ADMIN, 0, nullptr, 0);
								sys_log(0, "Reloading admin infomation.");
								break;
						}
					}
				}
				else if (!stBuf.compare(0, 6, "EVENT "))
				{
					std::istringstream is(stBuf);
					std::string strEvent, strFlagName;
					long lValue;
					is >> strEvent >> strFlagName >> lValue;

					if (!is.fail())
					{
						sys_log(0, "EXTERNAL EVENT FLAG name %s value %d", strFlagName.c_str(), lValue);
						quest::CQuestManager::instance().RequestSetEventFlag(strFlagName, lValue);
						stResult = "EVENT FLAG CHANGE ";
						stResult += strFlagName;
					}
					else
					{
						stResult = "EVENT FLAG FAIL";
					}
				}
				// BLOCK_CHAT
				else if (!stBuf.compare(0, 11, "BLOCK_CHAT "))
				{
					std::istringstream is(stBuf);
					std::string strBlockChat, strCharName;
					long lDuration;
					is >> strBlockChat >> strCharName >> lDuration;

					if (!is.fail())
					{
						sys_log(0, "EXTERNAL BLOCK_CHAT name %s duration %d", strCharName.c_str(), lDuration);

						do_block_chat(nullptr, const_cast<char*>(stBuf.c_str() + 11), 0, 0);

						stResult = "BLOCK_CHAT ";
						stResult += strCharName;
					}
					else
					{
						stResult = "BLOCK_CHAT FAIL";
					}
				}
				// END_OF_BLOCK_CHAT
				else if (!stBuf.compare(0, 12, "PRIV_EMPIRE "))
				{
					int	empire, type, value, duration;
					std::istringstream is(stBuf);
					std::string strPrivEmpire;
					is >> strPrivEmpire >> empire >> type >> value >> duration;

					value = MINMAX(0, value, 1000);
					stResult = "PRIV_EMPIRE FAIL";

					if (!is.fail())
					{
						// check parameter
						if (empire < 0 || 3 < empire);
						else if (type < 1 || 4 < type);
						else if (value < 0);
						else if (duration < 0);
						else
						{
							stResult = "PRIV_EMPIRE SUCCEED";

							duration = duration * (60 * 60);

							sys_log(0, "_give_empire_privileage(empire=%d, type=%d, value=%d, duration=%d) by web",
									empire, type, value, duration);
							CPrivManager::instance().RequestGiveEmpirePriv(empire, type, value, duration);
						}
					}
				}
			}
		}

		sys_log(1, "TEXT %s RESULT %s", stBuf.c_str(), stResult.c_str());
		stResult += "\n";
		d->Packet(stResult.c_str(), stResult.length());
		return (c_pSep - c_pData) + 1;
	}
	else if (bHeader == HEADER_CG_MARK_LOGIN)
	{
		if (!guild_mark_server)
		{
			sys_err("Guild Mark login requested but i'm not a mark server!");
			d->SetPhase(PHASE_CLOSE);
			return 0;
		}

		sys_log(0, "MARK_SERVER: Login");
		d->SetPhase(PHASE_LOGIN);
		return 0;
	}
	else if (bHeader == HEADER_CG_STATE_CHECKER)
	{
		if (d->isChannelStatusRequested()) {
			return 0;
		}
		#ifdef ENABLE_CHANNEL_STATUS_CACHE
		if (!PulseManager::Instance().IncreaseClock(0, ePulse::ChannelStatus, std::chrono::milliseconds(1000)))
		{
			if (!cachedChannelStatus.empty()) // first time check
			{
				d->Packet(cachedChannelStatus.data(), cachedChannelStatus.size());
				return 0;
			}
		}
		#endif
		d->SetChannelStatusRequested(true);
		db_clientdesc->DBPacket(HEADER_GD_REQUEST_CHANNELSTATUS, d->GetHandle(), nullptr, 0);
	}
	else if (bHeader == HEADER_CG_PONG)
		Pong(d);
#ifdef ENABLE_CLIENTLESS_HANDSHAKE_TRAP
	else if (bHeader == HEADER_CG_HANDSHAKE_REAL)	// gercek client (rebuild) bu header'i gonderir
		Handshake(d, c_pData);
	else if (bHeader == HEADER_CG_HANDSHAKE)		// eski header = clientless bot tuzagi
	{
		if (g_bClientlessTrap && !d->IsClientlessTrap())
		{
			d->SetClientlessTrap(true);
			sys_err("CLIENTLESS_TRAP: eski handshake(0x%02x) IP=%s port=%u fd=%d flagged enforce=%d",
					HEADER_CG_HANDSHAKE, d->GetHostName(), d->GetPort(), d->GetSocket(),
					g_bClientlessTrapEnforce ? 1 : 0);
			FILE* fpTrap = fopen("clientless_trap.log", "a");
			if (fpTrap)
			{
				time_t nowTrap = time(0);
				char szTrapTime[64];
				strftime(szTrapTime, sizeof(szTrapTime), "%Y-%m-%d %H:%M:%S", localtime(&nowTrap));
				fprintf(fpTrap, "[%s] FLAG ip=%s port=%u fd=%d header=0x%02x\n",
						szTrapTime, d->GetHostName(), d->GetPort(), d->GetSocket(), HEADER_CG_HANDSHAKE);
				fclose(fpTrap);
			}
		}
		// ACIK ise botu sessizce login fazina birak (account orada BLOCK edilir); KAPALI ise orijinal handshake
		Handshake(d, c_pData);
	}
#else
	else if (bHeader == HEADER_CG_HANDSHAKE)
		Handshake(d, c_pData);
#endif
	else
		sys_err("Handshake phase does not handle packet %d (fd %d) from %s:%u", bHeader, d->GetSocket(), d->GetHostName(), d->GetPort()); //@warme016 host and port

	return 0;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
