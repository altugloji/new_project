#pragma once

#ifdef __GEM_SYSTEM__
struct SGemShopItem
{
	DWORD	dwVnum;
	DWORD	dwCount;
	DWORD	dwPrice;
	BYTE	bLuck;
};
enum EGem
{
	GEM_X_GRID = 3,
	GEM_Y_GRID = 3,
	GEM_SLOT_COUNT = GEM_X_GRID * GEM_Y_GRID,
	GEM_PAGE_COUNT = 3,
	GEM_SLOT_COUNT_MAX = GEM_PAGE_COUNT * GEM_SLOT_COUNT,

	GEM_FREE_PAGE_COUNT = 1,
	GEM_PREMUM_SLOT_COUNT = (GEM_PAGE_COUNT- GEM_FREE_PAGE_COUNT) * GEM_SLOT_COUNT,

	GEM_RESET_ITEM = 39063,
	GEM_OPEN_SLOT_ITEM = 39064,
	GEM_REFRESH_TIME = 60 * 60 * 5,
};
class CGayaManager : public singleton<CGayaManager>
{
public:
	bool Load(bool is_p2p);
	void ResetPlayerShop(LPCHARACTER ch, std::vector<TGemItem>& vecItems);
	void Reset(LPCHARACTER ch);

	void OpenConvertShop(LPCHARACTER ch);

	const TGemConvertItem* GetConvertItem(BYTE bPos);
	void Convert(LPCHARACTER ch, BYTE bPos, int iCount);
protected:
	std::vector<SGemShopItem> m_vecItems;
	std::vector<TGemConvertItem> m_vecConvertItems;
};
#endif