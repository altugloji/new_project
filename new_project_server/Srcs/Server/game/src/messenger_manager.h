#ifndef __INC_MESSENGER_MANAGER_H
#define __INC_MESSENGER_MANAGER_H

#include "db.h"

class MessengerManager : public singleton<MessengerManager>
{
	public:
		typedef std::string keyT;
		typedef const std::string & keyA;

		MessengerManager();
		virtual ~MessengerManager();

	public:
		void	P2PLogin(keyA account);
		void	P2PLogout(keyA account);

		void	Login(keyA account);
		void	Logout(keyA account);

		void	RequestToAdd(LPCHARACTER ch, LPCHARACTER target);
		bool	AuthToAdd(keyA account, keyA companion, bool bDeny); // @fixme130 void -> bool

		void	__AddToList(keyA account, keyA companion);
		void	AddToList(keyA account, keyA companion);

		void	__RemoveFromList(keyA account, keyA companion);
		void	RemoveFromList(keyA account, keyA companion);

		void	RemoveAllList(keyA account);

#ifdef ENABLE_MESSENGER_BLOCK
		void	__AddToBlockList(keyA account, keyA companion);
		void	AddToBlockList(keyA account, keyA companion);
		void	__RemoveFromBlockList(keyA account, keyA companion);
		void	RemoveFromBlockList(keyA account, keyA companion);
		void	RemoveAllBlockList(keyA account);

		// type: SYST_BLOCK -> bellek-ici cift yonlu kontrol (SQL yok, chat/whisper sicak yolu),
		//       SYST_FRIEND -> bellek + offline iliskiler icin DB nokta sorgusu fallback'i
		bool	CheckMessengerList(keyA account, keyA companion, BYTE type);
#endif

		void	Initialize() const;

	private:
		void	SendList(keyA account);
		void	SendLogin(keyA account, keyA companion) const;
		void	SendLogout(keyA account, keyA companion) const;

		void	LoadList(SQLMsg * pmsg);

		void	Destroy() const;

#ifdef ENABLE_MESSENGER_BLOCK
		void	SendBlockList(keyA account);
		void	SendBlockLogin(keyA account, keyA companion) const;
		void	SendBlockLogout(keyA account, keyA companion) const;

		void	LoadBlockList(SQLMsg * pmsg);
#endif

		std::set<keyT>			m_set_loginAccount;
		std::map<keyT, std::set<keyT> >	m_Relation;
		std::map<keyT, std::set<keyT> >	m_InverseRelation;
		std::set<DWORD>			m_set_requestToAdd;
#ifdef ENABLE_MESSENGER_BLOCK
		std::map<keyT, std::set<keyT> >	m_BlockRelation;		// account -> engelledikleri (login'de DB'den yuklenir, tum core'larda P2P ile senkron)
		std::map<keyT, std::set<keyT> >	m_InverseBlockRelation;	// account -> onu engelleyenler
#endif
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
