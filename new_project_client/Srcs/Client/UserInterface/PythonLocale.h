#pragma once

class CPythonLocale : public CSingleton<CPythonLocale>
{
public:
	CPythonLocale();
	virtual ~CPythonLocale();

	enum ELOCALE_STRING_TYPE
	{
		LOCALE_STRING,
		LOCALE_QUEST_STRING,
		LOCALE_OXQUIZ_STRING,
		LOCALE_FORMAT_STRING,

		LOCALE_STRING_MAX
	};

	bool		LoadLocaleString(const char* c_szFileName);
	bool		LoadQuestLocaleString(const char* c_szFileName);
	bool		LoadOXQuizLocaleString(const char* c_szFileName);
	bool		LoadLocaleFormatString(const char* c_szFileName);

	void		FormatString(std::string& sMessage) const;
	void		FormatString(char* c, size_t size) const;

	void		MultiLineSplit(const std::string& sMessage, TTokenVector& vec) const;

	static std::string FormatWithArgs(std::string_view fmt, const CTokenVector& args, size_t argStart);

private:
	using FNameLookup = std::function<const char*(DWORD dwVnum)>;

	bool		LoadLocaleFile(ELOCALE_STRING_TYPE eType, const char* c_szFileName, const char* c_szFuncName,
								DWORD dwExpectedTokens, DWORD dwKeyIndex, DWORD dwValueIndex);
	void		ReplaceNameTag(std::string& sMessage, const char* szTag, const char* szErrorLabel,
								FNameLookup fnLookup) const;

	void		ReplaceLocaleString(std::string& sMessage) const;
	void		ReplaceQuestLocaleString(std::string& sMessage) const;
	void		ReplaceOXQuizLocaleString(std::string& sMessage) const;
	void		ReplaceLocaleFormatString(std::string& sMessage) const;

	std::unordered_map<std::string, std::string> m_LocaleStringMap[LOCALE_STRING_MAX];
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
