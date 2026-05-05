class CHorseNameManager : public singleton<CHorseNameManager>
{
	private :
		std::map<DWORD, std::string> m_mapHorseNames;

		void BroadcastHorseName(DWORD dwPlayerID, const char* szHorseName) const;

	public :
		CHorseNameManager();

		const char* GetHorseName(DWORD dwPlayerID);

		void UpdateHorseName(DWORD dwPlayerID, const char* szHorseName, bool broadcast=false);

		void Validate(LPCHARACTER pChar);
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
