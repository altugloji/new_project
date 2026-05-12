#pragma once

#ifdef __GEM_SHOP__
enum EGem
{
	GEM_X_GRID = 3,
	GEM_Y_GRID = 3,
	GEM_SLOT_COUNT = GEM_X_GRID * GEM_Y_GRID,
	GEM_PAGE_COUNT = 3,

	GEM_CONVERT_X_GRID = 20,
	GEM_CONVERT_Y_GRID = 4,
};
class CPythonGem : public CSingleton<CPythonGem>
{
public:
	CPythonGem();
	void Clear();

	bool	IsSlotOpened(BYTE bPos);
	BYTE	GetSlotCount() { return m_bSlotCount; }
	void	SetSlotCount(BYTE bVal) { m_bSlotCount = bVal; }

	int		GetRefreshTime() { return m_iRefreshTime; }
	void	SetRefreshTime(int iVal) { m_iRefreshTime = iVal; }

	TGemItem* GetItem(BYTE bPos);
	std::vector<TGemItem>& GetItemVector() { return m_vecGemItems; }

	TGemConvertItem* GetConvertItem(BYTE bPos);
	std::vector<TGemConvertItem>& GetConvertItemVector() { return m_vecGemConvertItems; }

protected:
	BYTE m_bSlotCount;
	int	m_iRefreshTime;
	std::vector<TGemItem> m_vecGemItems;
	std::vector<TGemConvertItem> m_vecGemConvertItems;
};
#endif
