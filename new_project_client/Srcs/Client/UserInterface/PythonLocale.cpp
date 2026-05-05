#include "StdAfx.h"
#include <format>
#include "PythonLocale.h"
#include "PythonNonPlayer.h"
#include "PythonSkill.h"
#include "../eterPack/EterPackManager.h"
#include "../GameLib/ItemManager.h"
#if defined(__BL_MULTI_LANGUAGE__)
#include "PythonApplication.h"
#endif

CPythonLocale::CPythonLocale() = default;

CPythonLocale::~CPythonLocale() = default;

bool CPythonLocale::LoadLocaleFile(ELOCALE_STRING_TYPE eType, const char* c_szFileName, const char* c_szFuncName,
									DWORD dwExpectedTokens, DWORD dwKeyIndex, DWORD dwValueIndex)
{
#if defined(__BL_MULTI_LANGUAGE__)
	if (CPythonApplication::Instance().GetReloadLocale())
		m_LocaleStringMap[eType].clear();
#endif

	if (!m_LocaleStringMap[eType].empty())
		return true;

	const VOID* pvData;
	CMappedFile kFile;
	if (!CEterPackManager::Instance().Get(kFile, c_szFileName, &pvData)) {
		TraceError("CPythonLocale::%s(c_szFileName: %s) - Load Error", c_szFuncName, c_szFileName);
		return false;
	}

	CMemoryTextFileLoader kTextFileLoader;
	kTextFileLoader.Bind(kFile.Size(), pvData);

	CTokenVector kTokenVector;
	for (DWORD i = 0; i < kTextFileLoader.GetLineCount(); ++i)
	{
		const std::string& c_rstLine = kTextFileLoader.GetLineString(i);
		if (c_rstLine.empty() || c_rstLine[0] == '#')
			continue;

		if (!kTextFileLoader.SplitLineByTab(i, &kTokenVector))
			continue;

		if (kTokenVector.size() != dwExpectedTokens)
			continue;

		m_LocaleStringMap[eType][kTokenVector[dwKeyIndex]] = kTokenVector[dwValueIndex];
	}

	return true;
}

bool CPythonLocale::LoadLocaleString(const char* c_szFileName)
{
	return LoadLocaleFile(LOCALE_STRING, c_szFileName, "LoadLocaleString", 2, 0, 1);
}

bool CPythonLocale::LoadQuestLocaleString(const char* c_szFileName)
{
	return LoadLocaleFile(LOCALE_QUEST_STRING, c_szFileName, "LoadQuestLocaleString", 2, 0, 1);
}

bool CPythonLocale::LoadOXQuizLocaleString(const char* c_szFileName)
{
	return LoadLocaleFile(LOCALE_OXQUIZ_STRING, c_szFileName, "LoadOXQuizLocaleString", 3, 1, 2);
}

bool CPythonLocale::LoadLocaleFormatString(const char* c_szFileName)
{
	return LoadLocaleFile(LOCALE_FORMAT_STRING, c_szFileName, "LoadLocaleFormatString", 2, 0, 1);
}

void CPythonLocale::FormatString(std::string& sMessage) const
{
	ReplaceNameTag(sMessage, "[SN;", "ReplaceSkillName", [](DWORD dwVnum) -> const char* {
		CPythonSkill::TSkillData* pSkillData;
		if (!CPythonSkill::Instance().GetSkillData(dwVnum, &pSkillData))
			return nullptr;
		return pSkillData->strName.c_str();
	});

	ReplaceNameTag(sMessage, "[MN;", "ReplaceMobName", [](DWORD dwVnum) -> const char* {
		const char* c_szName;
		if (!CPythonNonPlayer::Instance().GetName(dwVnum, &c_szName))
			return nullptr;
		return c_szName;
	});

	ReplaceNameTag(sMessage, "[IN;", "ReplaceItemName", [](DWORD dwVnum) -> const char* {
		CItemData* pItemData;
		if (!CItemManager::Instance().GetItemDataPointer(dwVnum, &pItemData))
			return nullptr;
		return pItemData->GetName();
	});

	ReplaceLocaleString(sMessage);
	ReplaceQuestLocaleString(sMessage);
	ReplaceOXQuizLocaleString(sMessage);
	ReplaceLocaleFormatString(sMessage);
}

void CPythonLocale::FormatString(char* c, size_t size) const
{
	std::string sFormat{c};
	FormatString(sFormat);

	strncpy(c, sFormat.c_str(), size);
	c[size - 1] = '\0';
}

void CPythonLocale::MultiLineSplit(const std::string& sMessage, TTokenVector& vec) const
{
	if (sMessage.find("[ENTER]") == std::string::npos)
		return;

	size_t pos = 0;
	while (true) {
		const size_t found = sMessage.find("[ENTER]", pos);
		if (found == std::string::npos)
			break;

		vec.push_back(sMessage.substr(pos, found - pos));
		pos = found + 7;
	}

	if (pos < sMessage.size())
		vec.push_back(sMessage.substr(pos));
}

// Replaces printf-style placeholders (%s, %d, %.2f, etc.) sequentially
// with string args. All args are strings so the specifier type is skipped
// and the arg text is inserted verbatim, matching boost::format behavior.
std::string CPythonLocale::FormatWithArgs(std::string_view fmt, const CTokenVector& args, size_t argStart)
{
	std::string result;
	result.reserve(fmt.size() + args.size() * 8);

	size_t argIdx = argStart;
	for (size_t i = 0; i < fmt.size(); ++i)
	{
		if (fmt[i] != '%') {
			result += fmt[i];
			continue;
		}

		if (i + 1 < fmt.size() && fmt[i + 1] == '%') {
			result += '%';
			++i;
			continue;
		}

		// Skip the full printf specifier: %[-+ 0#]*[width|*][.prec|.*][hlLz]*type
		size_t j = i + 1;
		while (j < fmt.size() && (fmt[j] == '-' || fmt[j] == '+' || fmt[j] == ' ' || fmt[j] == '0' || fmt[j] == '#'))
			++j;
		if (j < fmt.size() && fmt[j] == '*') ++j;
		else while (j < fmt.size() && fmt[j] >= '0' && fmt[j] <= '9') ++j;
		if (j < fmt.size() && fmt[j] == '.') {
			++j;
			if (j < fmt.size() && fmt[j] == '*') ++j;
			else while (j < fmt.size() && fmt[j] >= '0' && fmt[j] <= '9') ++j;
		}
		while (j < fmt.size() && (fmt[j] == 'h' || fmt[j] == 'l' || fmt[j] == 'L' || fmt[j] == 'z'))
			++j;
		if (j < fmt.size() && ((fmt[j] >= 'a' && fmt[j] <= 'z') || (fmt[j] >= 'A' && fmt[j] <= 'Z')))
			++j;

		if (argIdx < args.size())
			result += args[argIdx++];
		else
			result.append(fmt.data() + i, j - i);

		i = j - 1;
	}
	return result;
}

void CPythonLocale::ReplaceNameTag(std::string& sMessage, const char* szTag, const char* szErrorLabel,
									FNameLookup fnLookup) const
{
	size_t searchPos = 0;
	while (true)
	{
		const size_t pos_begin = sMessage.find(szTag, searchPos);
		if (pos_begin == std::string::npos)
			break;

		const size_t pos_mid = sMessage.find(';', pos_begin) + 1;
		const size_t pos_end = sMessage.find(']', pos_mid);
		if (pos_end == std::string::npos)
			break;

		DWORD dwVnum{};
		try {
			dwVnum = std::stoul(sMessage.substr(pos_mid, pos_end - pos_mid));
		}
		catch (const std::exception& ex) {
			TraceError("CPythonLocale::%s: Error: %s", szErrorLabel, ex.what());
			break;
		}

		const char* c_szName = fnLookup(dwVnum);
		if (!c_szName) {
			TraceError("CPythonLocale::%s: can't find vnum: %lu", szErrorLabel, dwVnum);
			break;
		}

		const size_t nameLen = strlen(c_szName);
		sMessage.replace(pos_begin, (pos_end + 1) - pos_begin, c_szName);
		searchPos = pos_begin + nameLen;
	}
}

static void ReplaceLocaleTag(
	std::string& sMessage,
	const char* szTag,
	const std::unordered_map<std::string, std::string>& localeMap,
	const char* szErrorLabel)
{
	for (int safety = 0; safety < 64; ++safety)
	{
		const size_t pos_1 = sMessage.rfind(szTag);
		if (pos_1 == std::string::npos)
			break;

		size_t pos_2 = sMessage.find(';', pos_1);
		if (pos_2 == std::string::npos)
			break;
		++pos_2;

		const size_t pos_3 = sMessage.find('[', pos_2);
		size_t pos_4 = sMessage.find(']', pos_2);
		if (pos_4 == std::string::npos)
			break;

		if (pos_3 != std::string::npos && pos_3 < pos_4)
			pos_4 = sMessage.find(']', pos_4 + 1);

		std::string sArgs = sMessage.substr(pos_2, pos_4 - pos_2);

		CTokenVector kTokenVector;
		SplitLine(sArgs.c_str(), ";", &kTokenVector);

		if (kTokenVector.empty())
			break;

		auto it = localeMap.find(kTokenVector[0]);
		if (it == localeMap.end()) {
			TraceError("CPythonLocale::%s wrong id: %s", szErrorLabel, kTokenVector[0].c_str());
			break;
		}

		if (kTokenVector.size() > 1)
			sMessage.replace(pos_1, (pos_4 + 1) - pos_1, CPythonLocale::FormatWithArgs(it->second, kTokenVector, 1));
		else
			sMessage.replace(pos_1, (pos_4 + 1) - pos_1, it->second);
	}
}

void CPythonLocale::ReplaceLocaleString(std::string& sMessage) const
{
	ReplaceLocaleTag(sMessage, "[LS;", m_LocaleStringMap[LOCALE_STRING], "ReplaceLocaleString");
}

void CPythonLocale::ReplaceQuestLocaleString(std::string& sMessage) const
{
	ReplaceLocaleTag(sMessage, "[LC;", m_LocaleStringMap[LOCALE_QUEST_STRING], "ReplaceQuestLocaleString");
}

void CPythonLocale::ReplaceOXQuizLocaleString(std::string& sMessage) const
{
	ReplaceLocaleTag(sMessage, "[LOX;", m_LocaleStringMap[LOCALE_OXQUIZ_STRING], "ReplaceOXQuizLocaleString");
}

static void ReplaceLocaleFormatTag(
	std::string& sMessage,
	const char* szTag,
	const std::unordered_map<std::string, std::string>& localeMap,
	const char* szErrorLabel)
{
	for (int safety = 0; safety < 64; ++safety)
	{
		const size_t pos_1 = sMessage.rfind(szTag);
		if (pos_1 == std::string::npos)
			break;

		size_t pos_2 = sMessage.find(';', pos_1);
		if (pos_2 == std::string::npos)
			break;
		++pos_2;

		const size_t pos_3 = sMessage.find('[', pos_2);
		size_t pos_4 = sMessage.find(']', pos_2);
		if (pos_4 == std::string::npos)
			break;

		if (pos_3 != std::string::npos && pos_3 < pos_4)
			pos_4 = sMessage.find(']', pos_4 + 1);

		std::string sArgs = sMessage.substr(pos_2, pos_4 - pos_2);

		CTokenVector kTokenVector;
		SplitLine(sArgs.c_str(), ";", &kTokenVector);

		if (kTokenVector.empty())
			break;

		auto it = localeMap.find(kTokenVector[0]);
		if (it == localeMap.end()) {
			TraceError("CPythonLocale::%s wrong id: %s", szErrorLabel, kTokenVector[0].c_str());
			break;
		}

		if (kTokenVector.size() > 1) {
			try {
				std::vector<std::string_view> fmtArgs;
				for (size_t i = 1; i < kTokenVector.size(); ++i)
					fmtArgs.emplace_back(kTokenVector[i]);

				std::string formatted;
				switch (fmtArgs.size()) {
					case 1: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0])); break;
					case 2: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1])); break;
					case 3: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1], fmtArgs[2])); break;
					case 4: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1], fmtArgs[2], fmtArgs[3])); break;
					case 5: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1], fmtArgs[2], fmtArgs[3], fmtArgs[4])); break;
					case 6: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1], fmtArgs[2], fmtArgs[3], fmtArgs[4], fmtArgs[5])); break;
					case 7: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1], fmtArgs[2], fmtArgs[3], fmtArgs[4], fmtArgs[5], fmtArgs[6])); break;
					case 8: formatted = std::vformat(it->second, std::make_format_args(fmtArgs[0], fmtArgs[1], fmtArgs[2], fmtArgs[3], fmtArgs[4], fmtArgs[5], fmtArgs[6], fmtArgs[7])); break;
					default: formatted = it->second; break;
				}
				sMessage.replace(pos_1, (pos_4 + 1) - pos_1, formatted);
			}
			catch (const std::format_error& ex) {
				TraceError("CPythonLocale::%s format error: %s", szErrorLabel, ex.what());
				break;
			}
		}
		else
			sMessage.replace(pos_1, (pos_4 + 1) - pos_1, it->second);
	}
}

void CPythonLocale::ReplaceLocaleFormatString(std::string& sMessage) const
{
	ReplaceLocaleFormatTag(sMessage, "[LF;", m_LocaleStringMap[LOCALE_FORMAT_STRING], "ReplaceLocaleFormatString");
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
