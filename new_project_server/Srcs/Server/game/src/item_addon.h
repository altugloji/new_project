#ifndef __ITEM_ADDON_H
#define __ITEM_ADDON_H

class CItemAddonManager : public singleton<CItemAddonManager>
{
	public:
		CItemAddonManager();
		virtual ~CItemAddonManager();

		void ApplyAddonTo(int iAddonType, LPITEM pItem) const;
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
