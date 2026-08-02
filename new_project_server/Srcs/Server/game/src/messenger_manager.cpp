#include "stdafx.h"
#include "constants.h"
#include "gm.h"
#include "messenger_manager.h"
#include "buffer_manager.h"
#include "desc_client.h"
#include "log.h"
#include "config.h"
#include "p2p.h"
#include "crc32.h"
#include "char.h"
#include "char_manager.h"
#include "questmanager.h"

// @fixme142 BEGIN
static char	__account[CHARACTER_NAME_MAX_LEN*2+1];
static char	__companion[CHARACTER_NAME_MAX_LEN*2+1];
// @fixme142 END

MessengerManager::MessengerManager()
{
}

MessengerManager::~MessengerManager()
{
}

void MessengerManager::Initialize() const
{
}

void MessengerManager::Destroy() const
{
}

void MessengerManager::P2PLogin(MessengerManager::keyA account)
{
	Login(account);
}

void MessengerManager::P2PLogout(MessengerManager::keyA account)
{
	Logout(account);
}

void MessengerManager::Login(MessengerManager::keyA account)
{
	if (m_set_loginAccount.contains(account))
		return;

	// @fixme142 BEGIN
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	if (account.compare(__account))
		return;
	// @fixme142 END

	DBManager::instance().FuncQuery(msl::bind1st(std::mem_fn(&MessengerManager::LoadList), this),
			"SELECT account, companion FROM messenger_list%s WHERE account='%s'", get_table_postfix(), __account);

#ifdef ENABLE_MESSENGER_BLOCK
	DBManager::instance().FuncQuery(msl::bind1st(std::mem_fn(&MessengerManager::LoadBlockList), this),
			"SELECT account, companion FROM messenger_block_list%s WHERE account='%s'", get_table_postfix(), __account);

	// Onu engelleyen online oyunculara 'online oldu' bildirimi: LoadBlockList kendi listesi
	// bos oldugunda erken donup account bilgisini kaybettigi icin bildirim burada, senkron yapilir
	// (inverse harita engelleyenlerin kendi login'lerinde dolar; P2PLogin ile her core'da calisir)
	{
		const auto itInv = m_InverseBlockRelation.find(account);
		if (itInv != m_InverseBlockRelation.end())
		{
			for (const auto & rBlocker : itInv->second)
				SendBlockLogin(rBlocker, account);
		}
	}
#endif

	m_set_loginAccount.emplace(account);
}

void MessengerManager::LoadList(SQLMsg * msg)
{
	if (nullptr == msg)
		return;

	if (nullptr == msg->Get())
		return;

	if (msg->Get()->uiNumRows == 0)
		return;

	std::string account;

	sys_log(1, "Messenger::LoadList");

	for (uint i = 0; i < msg->Get()->uiNumRows; ++i)
	{
		const MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);

		if (row[0] && row[1])
		{
			if (account.length() == 0)
				account = row[0];

			m_Relation[row[0]].emplace(row[1]);
			m_InverseRelation[row[1]].emplace(row[0]);
		}
	}

	SendList(account);

	std::set<MessengerManager::keyT>::iterator it;

	for (it = m_InverseRelation[account].begin(); it != m_InverseRelation[account].end(); ++it)
		SendLogin(*it, account);
}

#ifdef ENABLE_MESSENGER_BLOCK
bool MessengerManager::CheckMessengerList(keyA account, keyA companion, BYTE type)
{
	if (account.empty() || companion.empty())
		return false;

	// once bellek: iki yonlu kontrol (online oyuncularin listeleri P2PLogin ile tum core'larda yuklu)
	const std::map<keyT, std::set<keyT> > & rkMap = (type == SYST_BLOCK) ? m_BlockRelation : m_Relation;

	{
		const auto it = rkMap.find(account);
		if (it != rkMap.end() && it->second.find(companion) != it->second.end())
			return true;
	}
	{
		const auto it = rkMap.find(companion);
		if (it != rkMap.end() && it->second.find(account) != it->second.end())
			return true;
	}

	// SYST_BLOCK sicak yolda calisir (chat/whisper, alici basina) -> asla SQL'e inme.
	// Engel listeleri login'de her core'a yuklendigi icin bellek yeterlidir.
	if (type == SYST_BLOCK)
		return false;

	// SYST_FRIEND: offline iliski bellekte olmayabilir -> escape'li nokta sorgusu (LIMIT 1)
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	DBManager::instance().EscapeString(__companion, sizeof(__companion), companion.c_str(), companion.size());
	if (account.compare(__account) || companion.compare(__companion))
		return false;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"SELECT 1 FROM messenger_list%s WHERE (account='%s' AND companion='%s') OR (account='%s' AND companion='%s') LIMIT 1",
			get_table_postfix(), __account, __companion, __companion, __account));

	if (!pMsg || !pMsg->Get())
		return false;

	return pMsg->Get()->uiNumRows > 0;
}

void MessengerManager::LoadBlockList(SQLMsg * msg)
{
	if (nullptr == msg || nullptr == msg->Get() || msg->Get()->uiNumRows == 0)
		return;

	std::string account;

	for (uint i = 0; i < msg->Get()->uiNumRows; ++i)
	{
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);

		if (row[0] && row[1])
		{
			if (account.length() == 0)
				account = row[0];

			m_BlockRelation[row[0]].emplace(row[1]);
			m_InverseBlockRelation[row[1]].emplace(row[0]);
		}
	}

	SendBlockList(account);
}

void MessengerManager::SendBlockList(MessengerManager::keyA account)
{
	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());

	if (!ch)
		return;

	LPDESC d = ch->GetDesc();

	if (!d)
		return;

	if (m_BlockRelation.find(account) == m_BlockRelation.end())
		return;

	if (m_BlockRelation[account].empty())
		return;

	TPacketGCMessenger pack;

	pack.header		= HEADER_GC_MESSENGER;
	pack.subheader	= MESSENGER_SUBHEADER_GC_BLOCK_LIST;
	pack.size		= sizeof(TPacketGCMessenger);

	TPacketGCMessengerBlockListOffline pack_offline;
	TPacketGCMessengerBlockListOnline pack_online;

	TEMP_BUFFER buf(128 * 1024); // 128k

	auto it = m_BlockRelation[account].begin(), eit = m_BlockRelation[account].end();

	while (it != eit)
	{
		if (m_set_loginAccount.find(*it) != m_set_loginAccount.end())
		{
			pack_online.connected = 1;
			pack_online.length = it->size();

			buf.write(&pack_online, sizeof(TPacketGCMessengerBlockListOnline));
			buf.write(it->c_str(), it->size());
		}
		else
		{
			pack_offline.connected = 0;
			pack_offline.length = it->size();

			buf.write(&pack_offline, sizeof(TPacketGCMessengerBlockListOffline));
			buf.write(it->c_str(), it->size());
		}

		++it;
	}

	pack.size += buf.size();

	d->BufferedPacket(&pack, sizeof(TPacketGCMessenger));
	d->Packet(buf.read_peek(), buf.size());
}

void MessengerManager::SendBlockLogin(MessengerManager::keyA account, MessengerManager::keyA companion) const
{
	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (!d)
		return;

	if (!d->GetCharacter())
		return;

	BYTE bLen = companion.size();

	TPacketGCMessenger pack;

	pack.header		= HEADER_GC_MESSENGER;
	pack.subheader	= MESSENGER_SUBHEADER_GC_BLOCK_LOGIN;
	pack.size		= sizeof(TPacketGCMessenger) + sizeof(BYTE) + bLen;

	d->BufferedPacket(&pack, sizeof(TPacketGCMessenger));
	d->BufferedPacket(&bLen, sizeof(BYTE));
	d->Packet(companion.c_str(), companion.size());
}

void MessengerManager::SendBlockLogout(MessengerManager::keyA account, MessengerManager::keyA companion) const
{
	if (!companion.size())
		return;

	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (!d)
		return;

	BYTE bLen = companion.size();

	TPacketGCMessenger pack;

	pack.header		= HEADER_GC_MESSENGER;
	pack.subheader	= MESSENGER_SUBHEADER_GC_BLOCK_LOGOUT;
	pack.size		= sizeof(TPacketGCMessenger) + sizeof(BYTE) + bLen;

	d->BufferedPacket(&pack, sizeof(TPacketGCMessenger));
	d->BufferedPacket(&bLen, sizeof(BYTE));
	d->Packet(companion.c_str(), companion.size());
}

void MessengerManager::AddToBlockList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	if (companion.size() == 0)
		return;

	if (m_BlockRelation[account].find(companion) != m_BlockRelation[account].end())
		return;

	// @fixme142 tarzi escape (SQL injection onlemi)
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	DBManager::instance().EscapeString(__companion, sizeof(__companion), companion.c_str(), companion.size());
	if (account.compare(__account) || companion.compare(__companion))
		return;

	sys_log(0, "Messenger Block Add %s %s", account.c_str(), companion.c_str());
	DBManager::instance().Query("INSERT INTO messenger_block_list%s VALUES ('%s', '%s', NOW())",
			get_table_postfix(), __account, __companion);

	__AddToBlockList(account, companion);

	TPacketGGMessenger p2ppck;

	p2ppck.bHeader = HEADER_GG_MESSENGER_BLOCK_ADD;
	strlcpy(p2ppck.szAccount, account.c_str(), sizeof(p2ppck.szAccount));
	strlcpy(p2ppck.szCompanion, companion.c_str(), sizeof(p2ppck.szCompanion));
	P2P_MANAGER::instance().Send(&p2ppck, sizeof(TPacketGGMessenger));
}

void MessengerManager::__AddToBlockList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	m_BlockRelation[account].emplace(companion);
	m_InverseBlockRelation[companion].emplace(account);

	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (d)
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s engellendi."), companion.c_str());

	// online durumu core-yerel FindPC yerine P2P-senkron m_set_loginAccount'tan oku (kanal fark etmez)
	if (m_set_loginAccount.find(companion) != m_set_loginAccount.end())
		SendBlockLogin(account, companion);
	else
		SendBlockLogout(account, companion);
}

void MessengerManager::RemoveFromBlockList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	if (companion.size() == 0)
		return;

	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	DBManager::instance().EscapeString(__companion, sizeof(__companion), companion.c_str(), companion.size());
	if (account.compare(__account) || companion.compare(__companion))
		return;

	sys_log(0, "Messenger Block Remove %s %s", account.c_str(), companion.c_str());
	DBManager::instance().Query("DELETE FROM messenger_block_list%s WHERE account='%s' AND companion='%s'",
			get_table_postfix(), __account, __companion);

	__RemoveFromBlockList(account, companion);

	TPacketGGMessenger p2ppck;

	p2ppck.bHeader = HEADER_GG_MESSENGER_BLOCK_REMOVE;
	strlcpy(p2ppck.szAccount, account.c_str(), sizeof(p2ppck.szAccount));
	strlcpy(p2ppck.szCompanion, companion.c_str(), sizeof(p2ppck.szCompanion));
	P2P_MANAGER::instance().Send(&p2ppck, sizeof(TPacketGGMessenger));
}

void MessengerManager::__RemoveFromBlockList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	m_BlockRelation[account].erase(companion);
	m_InverseBlockRelation[companion].erase(account);

	LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (d)
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("%s icin engel kaldirildi."), companion.c_str());
}

void MessengerManager::RemoveAllBlockList(keyA account)
{
	// @fixme142 tarzi escape
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	if (account.compare(__account))
		return;

	DBManager::instance().Query("DELETE FROM messenger_block_list%s WHERE account='%s' OR companion='%s'",
			get_table_postfix(), __account, __account);

	std::set<keyT> company(m_BlockRelation[account]);

	for (std::set<keyT>::iterator iter = company.begin(); iter != company.end(); ++iter)
		RemoveFromBlockList(account, *iter);

	std::set<keyT> invCompany(m_InverseBlockRelation[account]);

	for (std::set<keyT>::iterator iter = invCompany.begin(); iter != invCompany.end(); ++iter)
		RemoveFromBlockList(*iter, account);

	m_BlockRelation.erase(account);
	m_InverseBlockRelation.erase(account);
}

DWORD MessengerManager::GetGuildIDByName(keyA name)
{
	// farkli core'daki (baska kanal/harita) hedefin lonca id'si; sadece kullanici
	// eyleminde (isimle engelleme) calisir, sicak yolda kullanilmaz
	DBManager::instance().EscapeString(__account, sizeof(__account), name.c_str(), name.size());
	if (name.compare(__account))
		return 0;

	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
			"SELECT g.guild_id FROM guild_member%s g, player%s p WHERE p.name='%s' AND g.pid=p.id LIMIT 1",
			get_table_postfix(), get_table_postfix(), __account));

	if (!pMsg || !pMsg->Get() || pMsg->Get()->uiNumRows == 0)
		return 0;

	MYSQL_ROW row = mysql_fetch_row(pMsg->Get()->pSQLResult);

	if (!row || !row[0])
		return 0;

	return (DWORD) strtoul(row[0], nullptr, 10);
}
#endif

void MessengerManager::Logout(MessengerManager::keyA account)
{
	if (!m_set_loginAccount.contains(account))
		return;

	m_set_loginAccount.erase(account);

	std::set<MessengerManager::keyT>::iterator it;

	for (it = m_InverseRelation[account].begin(); it != m_InverseRelation[account].end(); ++it)
	{
		SendLogout(*it, account);
	}

	auto it2 = m_Relation.begin();

	while (it2 != m_Relation.end())
	{
		it2->second.erase(account);
		++it2;
	}


#ifdef ENABLE_MESSENGER_BLOCK
	std::set<MessengerManager::keyT>::iterator itb;

	for (itb = m_InverseBlockRelation[account].begin(); itb != m_InverseBlockRelation[account].end(); ++itb)
		SendBlockLogout(*itb, account);

	// NOT: bilerek sadece oyuncunun kendi listesi dusuruluyor; digerlerinin m_BlockRelation
	// setlerine dokunulmuyor ki bellek-ici CheckMessengerList online oyuncular icin tam kalsin
	m_BlockRelation.erase(account);
#endif

	m_Relation.erase(account);
}

void MessengerManager::RequestToAdd(LPCHARACTER ch, LPCHARACTER target)
{
	if (!ch->IsPC() || !target->IsPC())
		return;

	if (quest::CQuestManager::instance().GetPCForce(ch->GetPlayerID())->IsRunning() == true)
	{
	    ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("상대방이 친구 추가를 받을 수 없는 상태입니다."));
	    return;
	}

	if (quest::CQuestManager::instance().GetPCForce(target->GetPlayerID())->IsRunning() == true)
		return;

	const DWORD dw1 = GetCRC32(ch->GetName(), strlen(ch->GetName()));
	const DWORD dw2 = GetCRC32(target->GetName(), strlen(target->GetName()));

	char buf[64];
	snprintf(buf, sizeof(buf), "%u:%u", dw1, dw2);
	DWORD dwComplex = GetCRC32(buf, strlen(buf));

	m_set_requestToAdd.emplace(dwComplex);

	target->ChatPacket(CHAT_TYPE_COMMAND, "messenger_auth %s", ch->GetName());
}

// @fixme130 void -> bool
bool MessengerManager::AuthToAdd(MessengerManager::keyA account, MessengerManager::keyA companion, bool bDeny)
{
	const DWORD dw1 = GetCRC32(companion.c_str(), companion.length());
	const DWORD dw2 = GetCRC32(account.c_str(), account.length());

	char buf[64];
	snprintf(buf, sizeof(buf), "%u:%u", dw1, dw2);
	const DWORD dwComplex = GetCRC32(buf, strlen(buf));

	if (!m_set_requestToAdd.contains(dwComplex))
	{
		sys_log(0, "MessengerManager::AuthToAdd : request not exist %s -> %s", companion.c_str(), account.c_str());
		return false;
	}

	m_set_requestToAdd.erase(dwComplex);

	if (!bDeny)
	{
		AddToList(companion, account);
		AddToList(account, companion);
	}
	return true;
}

void MessengerManager::__AddToList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	m_Relation[account].emplace(companion);
	m_InverseRelation[companion].emplace(account);

	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	const LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (d)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("<메신져> %s 님을 친구로 추가하였습니다."), companion.c_str());
	}

	const LPCHARACTER tch = CHARACTER_MANAGER::instance().FindPC(companion.c_str());

	if (tch)
		SendLogin(account, companion);
	else
		SendLogout(account, companion);
}

void MessengerManager::AddToList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	if (companion.size() == 0)
		return;

	if (m_Relation[account].contains(companion))
		return;

	// @fixme142 BEGIN
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	DBManager::instance().EscapeString(__companion, sizeof(__companion), companion.c_str(), companion.size());
	if (account.compare(__account) || companion.compare(__companion))
		return;
	// @fixme142 END

	sys_log(0, "Messenger Add %s %s", account.c_str(), companion.c_str());
	DBManager::instance().Query("INSERT INTO messenger_list%s VALUES ('%s', '%s')",
			get_table_postfix(), __account, __companion);

	__AddToList(account, companion);

	TPacketGGMessenger p2ppck;

	p2ppck.bHeader = HEADER_GG_MESSENGER_ADD;
	strlcpy(p2ppck.szAccount, account.c_str(), sizeof(p2ppck.szAccount));
	strlcpy(p2ppck.szCompanion, companion.c_str(), sizeof(p2ppck.szCompanion));
	P2P_MANAGER::instance().Send(&p2ppck, sizeof(TPacketGGMessenger));
}

void MessengerManager::__RemoveFromList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	m_Relation[account].erase(companion);
	m_InverseRelation[companion].erase(account);

	#ifdef ENABLE_MESSENGER_REMOVE_SYNC
	m_Relation[companion].erase(account);
	m_InverseRelation[account].erase(companion);
	#endif

	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	const LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (d)
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("<메신져> %s 님을 메신저에서 삭제하였습니다."), companion.c_str());

	#ifdef ENABLE_MESSENGER_REMOVE_SYNC
	auto tch = CHARACTER_MANAGER::Instance().FindPC(companion.c_str());
	if (tch && tch->GetDesc())
	{
		TPacketGCMessenger p;
		p.header		= HEADER_GC_MESSENGER;
		p.subheader		= MESSENGER_SUBHEADER_GC_REMOVE_FRIEND;
		p.size			= sizeof(TPacketGCMessenger) + sizeof(BYTE) + account.size();

		BYTE bLen		= account.size();
		tch->GetDesc()->BufferedPacket(p);
		tch->GetDesc()->BufferedPacket(bLen);
		tch->GetDesc()->Packet(account.c_str(), account.size());
	}
	#endif
}

void MessengerManager::RemoveFromList(MessengerManager::keyA account, MessengerManager::keyA companion)
{
	if (companion.size() == 0)
		return;

	// @fixme142 BEGIN
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	DBManager::instance().EscapeString(__companion, sizeof(__companion), companion.c_str(), companion.size());
	if (account.compare(__account) || companion.compare(__companion))
		return;
	// @fixme142 END

	sys_log(1, "Messenger Remove %s %s", account.c_str(), companion.c_str());
	DBManager::instance().Query("DELETE FROM messenger_list%s WHERE account='%s' AND companion = '%s'",
			get_table_postfix(), __account, __companion);

	__RemoveFromList(account, companion);

	TPacketGGMessenger p2ppck;

	p2ppck.bHeader = HEADER_GG_MESSENGER_REMOVE;
	strlcpy(p2ppck.szAccount, account.c_str(), sizeof(p2ppck.szAccount));
	strlcpy(p2ppck.szCompanion, companion.c_str(), sizeof(p2ppck.szCompanion));
	P2P_MANAGER::instance().Send(&p2ppck, sizeof(TPacketGGMessenger));
}

void MessengerManager::RemoveAllList(keyA account)
{
	std::set<keyT>	company(m_Relation[account]);

	// @fixme142 BEGIN
	DBManager::instance().EscapeString(__account, sizeof(__account), account.c_str(), account.size());
	if (account.compare(__account))
		return;
	// @fixme142 END

	DBManager::instance().Query("DELETE FROM messenger_list%s WHERE account='%s' OR companion='%s'",
			get_table_postfix(), __account, __account);

	for (auto iter = company.begin();
	     iter != company.end();
	     iter++ )
	{
		this->RemoveFromList(account, *iter);
		this->RemoveFromList(*iter, account); // @fixme183
	}

	for (auto iter = company.begin();
	     iter != company.end();
	)
	{
		company.erase(iter++);
	}

	company.clear();
}

void MessengerManager::SendList(MessengerManager::keyA account)
{
	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());

	if (!ch)
		return;

	const LPDESC d = ch->GetDesc();

	if (!d)
		return;

	if (!m_Relation.contains(account))
		return;

	if (m_Relation[account].empty())
		return;

	TPacketGCMessenger pack;

	pack.header		= HEADER_GC_MESSENGER;
	pack.subheader	= MESSENGER_SUBHEADER_GC_LIST;
	pack.size		= sizeof(TPacketGCMessenger);

	TPacketGCMessengerListOffline pack_offline;
	TPacketGCMessengerListOnline pack_online;

	TEMP_BUFFER buf(128 * 1024); // 128k

	itertype(m_Relation[account]) it = m_Relation[account].begin(), eit = m_Relation[account].end();

	while (it != eit)
	{
		if (m_set_loginAccount.contains(*it))
		{
			pack_online.connected = 1;

			// Online
			pack_online.length = it->size();

			buf.write(&pack_online, sizeof(TPacketGCMessengerListOnline));
			buf.write(it->c_str(), it->size());
		}
		else
		{
			pack_offline.connected = 0;

			// Offline
			pack_offline.length = it->size();

			buf.write(&pack_offline, sizeof(TPacketGCMessengerListOffline));
			buf.write(it->c_str(), it->size());
		}

		++it;
	}

	pack.size += buf.size();

	d->BufferedPacket(&pack, sizeof(TPacketGCMessenger));
	d->Packet(buf.read_peek(), buf.size());
}

void MessengerManager::SendLogin(MessengerManager::keyA account, MessengerManager::keyA companion) const
{
	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	const LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (!d)
		return;

	if (!d->GetCharacter())
		return;

	if (ch->GetGMLevel() == GM_PLAYER && gm_get_level(companion.c_str()) != GM_PLAYER)
		return;

	const BYTE bLen = companion.size();

	TPacketGCMessenger pack;

	pack.header			= HEADER_GC_MESSENGER;
	pack.subheader		= MESSENGER_SUBHEADER_GC_LOGIN;
	pack.size			= sizeof(TPacketGCMessenger) + sizeof(BYTE) + bLen;

	d->BufferedPacket(&pack, sizeof(TPacketGCMessenger));
	d->BufferedPacket(&bLen, sizeof(BYTE));
	d->Packet(companion.c_str(), companion.size());
}

void MessengerManager::SendLogout(MessengerManager::keyA account, MessengerManager::keyA companion) const
{
	if (!companion.size())
		return;

	const LPCHARACTER ch = CHARACTER_MANAGER::instance().FindPC(account.c_str());
	const LPDESC d = ch ? ch->GetDesc() : nullptr;

	if (!d)
		return;

	const BYTE bLen = companion.size();

	TPacketGCMessenger pack;

	pack.header		= HEADER_GC_MESSENGER;
	pack.subheader	= MESSENGER_SUBHEADER_GC_LOGOUT;
	pack.size		= sizeof(TPacketGCMessenger) + sizeof(BYTE) + bLen;

	d->BufferedPacket(&pack, sizeof(TPacketGCMessenger));
	d->BufferedPacket(&bLen, sizeof(BYTE));
	d->Packet(companion.c_str(), companion.size());
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
