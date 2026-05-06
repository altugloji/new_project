#pragma once

#ifdef KYGN_CHEST_INFO
#include "Packet.h"

class CPythonChestInfo : public CSingleton<CPythonChestInfo>
{
	private:
		DWORD													lastSendingVnum;
		PyObject*												m_ppyGameWindow;
		std::unordered_map<DWORD, std::vector<TChestRewards>>	map_ChestRewardInfo;

	public:
		CPythonChestInfo() {}
		virtual ~CPythonChestInfo() {}

		void	SetGameWindow(PyObject* ppyObject);
		void	GetChestRewardInfo(DWORD dwVnum);
		bool	SetChestRewardData(DWORD dwVnum);

		void	SortChestRewardList(DWORD dwVnum);


		void	AddChestRewardInfo(DWORD dwVnum, const TChestRewards& listItem) { map_ChestRewardInfo[dwVnum].push_back(listItem); }
};
#endif
