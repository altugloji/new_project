#include <unordered_map>

#include "../../common/stl.h"

class CDragonLair
{
	public:
		CDragonLair (DWORD dwGuildID, long BaseMapID, long PrivateMapID);
		virtual ~CDragonLair ();

		DWORD GetEstimatedTime () const;

		void OnDragonDead (LPCHARACTER pDragon) const;

	private:
		DWORD StartTime_;
		DWORD GuildID_;
		[[maybe_unused]] long BaseMapIndex_;
		[[maybe_unused]] long PrivateMapIndex_;
};

class CDragonLairManager : public singleton<CDragonLairManager>
{
	public:
		CDragonLairManager ();
		virtual ~CDragonLairManager ();

		bool Start (long MapIndexFrom, long BaseMapIndex, DWORD GuildID);
		void OnDragonDead (LPCHARACTER pDragon, DWORD KillerGuildID);

		size_t GetLairCount () const { return LairMap_.size(); }

	private:
		std::unordered_map<DWORD, CDragonLair*> LairMap_;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
