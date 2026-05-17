#pragma once

#ifdef ENABLE_ITEM_SHOP_SYSTEM
enum EItemShopEmBind
{
	ITEM_SHOP_EM_BIND_ATTR_INDEX	= 6,
	ITEM_SHOP_EM_BIND_ATTR_VALUE	= 31337,
};
#endif

class CItemShopManager : public singleton<CItemShopManager>
{
	typedef struct SItemShopTable
	{
		DWORD	category;
		DWORD	sub_category;
		DWORD	id;
		DWORD	vnum;
		DWORD	count;
		DWORD	coinsold;
		DWORD	coins;
		DWORD	socketzero;
		DWORD	mark;
		DWORD	socket0, socket1, socket2, socket3, socket4, socket5;
		DWORD	type0, type1, type2, type3, type4, type5, type6;
		DWORD	value0, value1, value2, value3, value4, value5, value6;
	} TItemShopTable;

	typedef std::map<DWORD, TItemShopTable*> TItemShopDataMap;
public:
	CItemShopManager(void);
	virtual ~CItemShopManager(void);

	const TItemShopTable* GetTable(DWORD id);

	bool LoadItemShopTable();
	bool Buy(LPCHARACTER ch, DWORD id, DWORD count, BYTE bPayType = 2);
	
	void SendClientPacket(LPCHARACTER ch);
	
	
	void Destroy();
protected:
	TItemShopDataMap	m_ItemShopDataMap;
};