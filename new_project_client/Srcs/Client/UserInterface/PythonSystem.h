#pragma once

class CPythonSystem : public CSingleton<CPythonSystem>
{
	public:
		enum EWindow
		{
			WINDOW_STATUS,
			WINDOW_INVENTORY,
			WINDOW_ABILITY,
			WINDOW_SOCIETY,
			WINDOW_JOURNAL,
			WINDOW_COMMAND,

			WINDOW_QUICK,
			WINDOW_GAUGE,
			WINDOW_MINIMAP,
			WINDOW_CHAT,

			WINDOW_MAX_NUM,
		};

		enum
		{
			FREQUENCY_MAX_NUM  = 30,
			RESOLUTION_MAX_NUM = 100
		};

		typedef struct SResolution
		{
			DWORD	width;
			DWORD	height;
			DWORD	bpp;		// bits per pixel (high-color = 16bpp, true-color = 32bpp)

			DWORD	frequency[20];
			BYTE	frequency_count;
		} TResolution;

		typedef struct SWindowStatus
		{
			int		isVisible;
			int		isMinimized;

			int		ixPosition;
			int		iyPosition;
			int		iHeight;
		} TWindowStatus;

		typedef struct SConfig
		{
			DWORD			width;
			DWORD			height;
			DWORD			bpp;
			DWORD			frequency;

			bool			is_software_cursor;
			bool			is_object_culling;
			int				iDistance;
			int				iShadowLevel;
#ifdef ENABLE_DYNAMIC_SHADOW
			bool			bDynamicShadow{true};
#endif
			int				iAntialiasing;

			FLOAT			music_volume;
			BYTE			voice_volume;

			int				gamma;

			int				isSaveID;
			char			SaveID[20];

			bool			bWindowed;
			bool			bDecompressDDS;
			bool			bNoSoundCard;
			bool			bUseDefaultIME;
			BYTE			bSoftwareTiling;
			bool			bViewChat;
			bool			bAlwaysShowName;
			bool			bShowDamage;
			bool			bShowSalesText;
#if defined(WJ_SHOW_MOB_INFO) && defined(ENABLE_SHOW_MOBAIFLAG)
			bool			bShowMobAIFlag;
#endif
#if defined(WJ_SHOW_MOB_INFO) && defined(ENABLE_SHOW_MOBLEVEL)
			bool			bShowMobLevel;
#endif
#ifdef __BL_FOG_FIX__
			bool			bFogMode;
#endif
#if defined(__BL_MULTI_LANGUAGE_ULTIMATE__)
			bool			bAnonymousCountryMode;
			bool			bShowCountryFlag;
			bool			bShowEmpireFlag;
#endif

		} TConfig;

	public:
		CPythonSystem();
		virtual ~CPythonSystem();

		void Clear();
		void SetInterfaceHandler(PyObject * poHandler);
		void DestroyInterfaceHandler();

		// Config
		void							SetDefaultConfig();
		bool							LoadConfig();
		bool							SaveConfig();
		void							ApplyConfig();
		void							SetConfig(TConfig * set_config);
		TConfig *						GetConfig();
		void							ChangeSystem() const;

		// Interface
		bool							LoadInterfaceStatus();
		void							SaveInterfaceStatus() const;
		bool							isInterfaceConfig() const;
		const TWindowStatus &			GetWindowStatusReference(int iIndex) const;

		DWORD							GetWidth() const;
		DWORD							GetHeight() const;
		DWORD							GetBPP() const;
		DWORD							GetFrequency() const;
		bool							IsSoftwareCursor() const;
		bool							IsWindowed() const;
		bool							IsViewChat() const;
		bool							IsAlwaysShowName() const;
		bool							IsShowDamage() const;
		bool							IsShowSalesText() const;
		bool							IsUseDefaultIME() const;
		bool							IsNoSoundCard() const;
		bool							IsAutoTiling() const;
		bool							IsSoftwareTiling() const;
		void							SetSoftwareTiling(bool isEnable);
		void							SetViewChatFlag(int iFlag);
		void							SetAlwaysShowNameFlag(int iFlag);
		void							SetShowDamageFlag(int iFlag);
		void							SetShowSalesTextFlag(int iFlag);
#if defined(WJ_SHOW_MOB_INFO) && defined(ENABLE_SHOW_MOBAIFLAG)
		bool							IsShowMobAIFlag() const;
		void							SetShowMobAIFlagFlag(int iFlag);
#endif
#if defined(WJ_SHOW_MOB_INFO) && defined(ENABLE_SHOW_MOBLEVEL)
		bool							IsShowMobLevel() const;
		void							SetShowMobLevelFlag(int iFlag);
#endif
#ifdef __BL_FOG_FIX__
		void							SetFogMode(bool bEnable);
		bool							GetFogMode() const;
#endif

#if defined(__BL_MULTI_LANGUAGE_ULTIMATE__)
		void							SetAnonymousCountryMode(bool isEnable);
		bool							GetAnonymousCountryMode() const;

		void							SetShowCountryFlag(bool isEnable);
		bool							IsShowCountryFlag() const;

		void							SetShowEmpireFlag(bool isEnable);
		bool							IsShowEmpireFlag() const;

		void							AddChatFilterCountry(const std::string& country);
		void							RemoveChatFilterCountry(const std::string& country);
		bool							IsChatFilterCountry(const std::string& country) const;

		void							AddChatFilterEmpire(BYTE bEmpire);
		void							RemoveChatFilterEmpire(BYTE bEmpire);
		bool							IsChatFilterEmpire(BYTE bEmpire) const;

		void							LoadChatFilterSettings();
		void							SaveChatFilterSettings() const;
#endif

		// Window
		void							SaveWindowStatus(int iIndex, int iVisible, int iMinimized, int ix, int iy, int iHeight);

		// SaveID
		int								IsSaveID() const;
		const char *					GetSaveID() const;
		void							SetSaveID(int iValue, const char * c_szSaveID);

		/// Display
		void							GetDisplaySettings();

		int								GetResolutionCount() const;
		int								GetFrequencyCount(int index) const;
		bool							GetResolution(int index, OUT DWORD *width, OUT DWORD *height, OUT DWORD *bpp) const;
		bool							GetFrequency(int index, int freq_index, OUT DWORD *frequncy) const;
		int								GetResolutionIndex(DWORD width, DWORD height, DWORD bpp) const;
		int								GetFrequencyIndex(int res_index, DWORD frequency) const;
		bool							isViewCulling() const;

		// Sound
		float							GetMusicVolume() const;
		int								GetSoundVolume() const;
		void							SetMusicVolume(float fVolume);
		void							SetSoundVolumef(float fVolume);

		int								GetDistance() const;
		int								GetShadowLevel() const;
		void							SetShadowLevel(unsigned int level);
#ifdef ENABLE_DYNAMIC_SHADOW
		bool							GetDynamicShadow();
		void							SetDynamicShadow(bool bEnable);
#endif
		int								GetAntialiasing();
		void							SetAntialiasing(int level);

	protected:
		TResolution						m_ResolutionList[RESOLUTION_MAX_NUM];
		int								m_ResolutionCount;

		TConfig							m_Config;
		TConfig							m_OldConfig;

		bool							m_isInterfaceConfig;
		PyObject *						m_poInterfaceHandler;
		TWindowStatus					m_WindowStatus[WINDOW_MAX_NUM];
#if defined(__BL_MULTI_LANGUAGE_ULTIMATE__)
		std::set<std::string>			m_setFilterCountry;
		DWORD							m_dwFilterEmpireFlag;
#endif
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
