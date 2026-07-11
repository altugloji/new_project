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
#ifdef ENABLE_OFFLINE_SHOP_SOLD_RED
			BYTE	sold;		// 1 = satildi; item slotta KIRMIZI hayalet olarak kalir, tekrar satilamaz
#endif

			LPITEM	pkItem;
			int		itemid;

			shop_item()
			{
				vnum = 0;
				price = 0;
#ifdef ENABLE_OFFLINE_SHOP_SOLD_RED
				sold = 0;
#endif
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
		// Yok edilmekte olan item'in vector'deki pointer'ini temizler; yoksa bayat pkItem
		// pazar aramasi / dukkan paketlerinde serbest birakilmis bellek okur (UAF crash)
		void			ClearItemPointer(LPITEM pkItem);

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
#ifdef ENABLE_OFFLINE_SHOP_SOLD_RED
		// Boot'ta DB'den yuklenen satilmis (sold=1) item'i kirmizi hayalet olarak isaretle (itemid = player_shop_items.id)
		void		SetItemSoldByItemID(DWORD itemid);
		// Verilen item bu dukkanda satilmis (sold=1) kirmizi hayalet mi?
		bool		IsSoldGhost(LPITEM pkItem) const;
#endif
#ifdef ENABLE_IKASHOP_SEARCH
		// Uzak satis (GG 42): itemid'li slotu sold=1 isaretle + misafirlere UPDATE_ITEM yayinla.
		// Donus: bulunan slot pozisyonu; -1 = bu dukkanda yok (bayat bildirim, zararsiz)
		int			MarkSoldAndBroadcast(DWORD itemid);
#endif
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
