#ifndef __INC_METIN_II_GAME_SHOP_H__
#define __INC_METIN_II_GAME_SHOP_H__

enum
{
	SHOP_MAX_DISTANCE = 1000
};

class CGrid;

/* ---------------------------------------------------------------------------------- */
class CShop
{
	public:
		typedef struct shop_item
		{
			DWORD	vnum;
			long	price;
#ifdef ENABLE_CHEQUE_SYSTEM
			int		cheque = 0;
#endif
#ifdef ENABLE_MULTISHOP
			DWORD	wPriceVnum;
			DWORD	wPrice;
			DWORD	gemPrice;
#endif
			BYTE	count;

			LPITEM	pkItem;
			int		itemid;

			shop_item()
			{
				vnum = 0;
				price = 0;
#ifdef ENABLE_MULTISHOP
				wPriceVnum = 0;
				wPrice = 0;
				gemPrice = 0;
#endif
				count = 0;
				itemid = 0;
				pkItem = nullptr;
			}
		} SHOP_ITEM;

		CShop();
		virtual ~CShop(); // @fixme139 (+virtual)

		bool			Create(DWORD dwVnum, DWORD dwNPCVnum, TShopItemTable * pItemTable);
		void			SetShopItems(TShopItemTable * pItemTable, BYTE bItemCount);

		virtual void	SetPCShop(LPCHARACTER ch);
		virtual bool	IsPCShop()	{ return m_pkPC ? true : false; }

		virtual bool	AddGuest(LPCHARACTER ch,DWORD owner_vid, bool bOtherEmpire);
		void			RemoveGuest(LPCHARACTER ch);
		virtual int		Buy(LPCHARACTER ch, BYTE pos);
		void			BroadcastUpdateItem(BYTE pos);
		int				GetNumberByVnum(DWORD dwVnum) const;
		virtual bool	IsSellingItem(DWORD itemID);

		DWORD	GetVnum() const { return m_dwVnum; }
		DWORD	GetNPCVnum() const { return m_dwNPCVnum; }

#ifdef OFFLINE_SHOP
		// Pazar Arama (ShopSearch): dukkanin sahibi (online sahis dukkaninda oyuncu,
		// offline dukkanda dukkani tasiyan tezgah-mob'u) + esya eslestirme yardimcilari
		LPCHARACTER	GetOwner() const { return m_pkPC; }
		bool		HasItem(DWORD itemVnum, int socket0 = 0) const;
		bool		HasItemType(BYTE type, BYTE subtype, bool checkAttribute) const;
		bool		HasSoulStoneSocket(BYTE level) const;
#endif

	protected:
		void	Broadcast(const void * data, int bytes);

#ifdef OFFLINE_SHOP
	public:
		int			BuyOffline(LPCHARACTER ch, BYTE pos);
		int			GetItemCount();
		bool		GetItems();
		void		SetPrivShopItems(std::vector<TShopItemTable *> map_shop);
		void		RemoveItemForShop(DWORD dwItemID);
		// Offline dukkan duzenleme: bakanlari kov (sahip haric), sahip duzenlemesini uygula
		void		KickGuestsExcept(LPCHARACTER keep);
		void		ApplyOwnerEdit(LPCHARACTER owner, const BYTE * pbRemovePos, BYTE byRemoveCount, const TShopItemTable * pAdd, BYTE byAddCount, const TOfflineShopPriceUpdate * pUpdate, BYTE byUpdateCount);
		bool		EditWouldExceedLimit(const BYTE * pbRemovePos, BYTE byRemoveCount, const TShopItemTable * pAdd, BYTE byAddCount, const TOfflineShopPriceUpdate * pUpdate, BYTE byUpdateCount) const;
		void		RebuildGrid();
#endif

	protected:
		DWORD				m_dwVnum;
		DWORD				m_dwNPCVnum;

		CGrid *				m_pGrid;

		typedef TR1_NS::unordered_map<LPCHARACTER, bool> GuestMapType;
		GuestMapType m_map_guest;
		std::vector<SHOP_ITEM>		m_itemVector;

		LPCHARACTER			m_pkPC;
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
