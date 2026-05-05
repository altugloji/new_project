#ifndef __INC_METIN_II_ASYNCSQL_H__
#define __INC_METIN_II_ASYNCSQL_H__

#include "../libthecore/include/stdafx.h"
#include "../libthecore/include/log.h"

#include <string>
#include <queue>
#include <vector>
#include <map>
#include <mysql/mysql.h>
#include <mysql/errmsg.h>
#include <mysql/mysqld_error.h>
#include <memory>
#include <cassert>
#include <charconv>
#include <cstring>
#include <string_view>
#include <type_traits>

#include "Semaphore.h"

#define QUERY_MAX_LEN 8192

// Safe query builder: replaces ? placeholders with escaped/formatted values.
// Strings (const char*, std::string) are escaped and single-quoted.
// Integers/floats formatted via std::to_chars (zero allocation).
// Bool becomes 0/1. Skips ? inside single-quoted SQL string literals.
// Single-pass scan with post-assert on placeholder count.
namespace SqlQuery
{
	// --- Value formatters (zero-allocation for numerics) ---
	inline void AppendValue(std::string& dst, MYSQL&, bool v) { dst += (v ? '1' : '0'); }

	template<typename T>
	requires std::is_arithmetic_v<T> && (!std::is_same_v<T, bool>)
	inline void AppendValue(std::string& dst, MYSQL&, T v)
	{
		char buf[32];
		auto [ptr, ec] = std::to_chars(buf, buf + sizeof(buf), v);
		dst.append(buf, ptr - buf);
	}

	inline void AppendValue(std::string& dst, MYSQL& hDB, const char* v)
	{
		if (!v) { dst += "NULL"; return; }
		const size_t len = strlen(v);
		const size_t pos = dst.size();
		dst += '\'';
		dst.resize(pos + 1 + len * 2 + 1);
		const size_t escaped = mysql_real_escape_string(&hDB, &dst[pos + 1], v, len);
		dst.resize(pos + 1 + escaped);
		dst += '\'';
	}

	inline void AppendValue(std::string& dst, MYSQL& hDB, const std::string& v)
	{
		const size_t len = v.size();
		const size_t pos = dst.size();
		dst += '\'';
		dst.resize(pos + 1 + len * 2 + 1);
		const size_t escaped = mysql_real_escape_string(&hDB, &dst[pos + 1], v.data(), len);
		dst.resize(pos + 1 + escaped);
		dst += '\'';
	}

	inline void AppendValue(std::string& dst, MYSQL& hDB, std::string_view v)
	{
		const size_t len = v.size();
		const size_t pos = dst.size();
		dst += '\'';
		dst.resize(pos + 1 + len * 2 + 1);
		const size_t escaped = mysql_real_escape_string(&hDB, &dst[pos + 1], v.data(), len);
		dst.resize(pos + 1 + escaped);
		dst += '\'';
	}

	// --- Advance cursor past quoted/escaped sections, return ptr to next unquoted '?' or end ---
	// Handles: 'single quotes', "double quotes", `backticks`, and backslash escapes (\' \" \`)
	inline const char* AdvanceToPlaceholder(const char* p)
	{
		while (*p)
		{
			if (*p == '\\' && *(p + 1)) // backslash escape: skip next char
			{
				p += 2;
				continue;
			}
			if (*p == '\'' || *p == '"' || *p == '`') // quoted section
			{
				const char quote = *p++;
				while (*p && *p != quote)
				{
					if (*p == '\\' && *(p + 1)) // escape inside quotes
						++p;
					++p;
				}
				if (*p) ++p; // skip closing quote
				continue;
			}
			if (*p == '?')
				return p;
			++p;
		}
		return p; // end of string
	}

	// --- Single-pass builder using fold expression ---
	// Scans template exactly once. Asserts placeholder count matches arg count after the scan.
	template<typename... Args>
	std::string Build(MYSQL& hDB, const char* tpl, Args&&... args)
	{
		if constexpr (sizeof...(args) == 0)
		{
			return std::string(tpl);
		}
		else
		{
			std::string result;
			result.reserve(strlen(tpl) + sizeof...(args) * 24);

			const char* cursor = tpl;
			[[maybe_unused]] size_t placeholders = 0;

			// Fold: for each arg, advance to next ?, append text before it, append value
			(([&] {
				const char* ph = AdvanceToPlaceholder(cursor);
				result.append(cursor, ph - cursor);
				if (*ph == '?')
				{
					AppendValue(result, hDB, std::forward<Args>(args));
					cursor = ph + 1;
					++placeholders;
				}
				else
				{
					cursor = ph; // at end, no more placeholders
				}
			}()), ...);

			// Append remaining text after last placeholder
			if (*cursor)
				result.append(cursor);

			assert(placeholders == sizeof...(args) &&
				"SqlQuery::Build: ? placeholder count does not match argument count");

			return result;
		}
	}
} // namespace SqlQuery

typedef struct _SQLResult
{
	_SQLResult()
	   	: pSQLResult(nullptr), uiNumRows(0), uiAffectedRows(0), uiInsertID(0)
	{
	}

	~_SQLResult()
	{
		if (pSQLResult)
		{
			mysql_free_result(pSQLResult);
			pSQLResult = nullptr;
		}
	}

	MYSQL_RES *	pSQLResult;
	uint32_t		uiNumRows;
	uint32_t		uiAffectedRows;
	uint32_t		uiInsertID;
} SQLResult;

typedef struct _SQLMsg
{
	_SQLMsg() : m_pkSQL(nullptr), iID(0), uiResultPos(0), pvUserData(nullptr), bReturn(false), uiSQLErrno(0)
	{
	}

	~_SQLMsg()
	{
		auto first = vec_pkResult.begin();
		const auto past = vec_pkResult.end();

		while (first != past)
			delete *(first++);

		vec_pkResult.clear();
	}

	void Store()
	{
		do
		{
			auto pRes = new SQLResult;

			pRes->pSQLResult = mysql_store_result(m_pkSQL);
			pRes->uiInsertID = mysql_insert_id(m_pkSQL);
			pRes->uiAffectedRows = mysql_affected_rows(m_pkSQL);

			if (pRes->pSQLResult)
			{
				pRes->uiNumRows = mysql_num_rows(pRes->pSQLResult);
			}
			else
			{
				pRes->uiNumRows = 0;
			}

			vec_pkResult.push_back(pRes);
		} while (!mysql_next_result(m_pkSQL));
	}

	SQLResult * Get() const
	{
		if (uiResultPos >= vec_pkResult.size())
			return nullptr;

		return vec_pkResult[uiResultPos];
	}

	bool Next()
	{
		if (uiResultPos + 1 >= vec_pkResult.size())
			return false;

		++uiResultPos;
		return true;
	}

	MYSQL *			m_pkSQL;
	int				iID;
	std::string			stQuery;

	std::vector<SQLResult *>	vec_pkResult;
	unsigned int		uiResultPos;

	void *			pvUserData;
	bool			bReturn;

	unsigned int		uiSQLErrno;
} SQLMsg;

class CAsyncSQL
{
	public:
		CAsyncSQL();
		virtual ~CAsyncSQL();

		void		Quit();

		bool   		Setup(const char * c_pszHost, const char * c_pszUser, const char * c_pszPassword, const char * c_pszDB, const char * c_pszLocale,
			bool bNoThread = false, int iPort = 0);
		bool		Setup(CAsyncSQL * sql, bool bNoThread = false);

		bool		Connect();
		bool		IsConnected() const { return m_bConnected; }
		bool		QueryLocaleSet();

		void		AsyncQuery(const char * c_pszQuery);
		void		ReturnQuery(const char * c_pszQuery, void * pvUserData);
		std::unique_ptr<SQLMsg>	DirectQuery(const char * c_pszQuery);

		DWORD		CountQuery() const;
		DWORD		CountResult() const;

		void		PushResult(SQLMsg * p);
		bool		PopResult(SQLMsg ** pp);

		void		ChildLoop();

		MYSQL *		GetSQLHandle();
		MYSQL &		GetMYSQL() { return m_hDB; }

		int			CountQueryFinished() const;
		void		ResetQueryFinished();

		size_t		EscapeString(char* dst, size_t dstSize, const char *src, size_t srcSize);

	protected:
		void		Destroy();

		void		PushQuery(SQLMsg * p);

		bool		PeekQuery(SQLMsg ** pp) const;
		bool		PopQuery(int iID);

		bool		PeekQueryFromCopyQueue(SQLMsg ** pp ) const;
		INT			CopyQuery();
		bool		PopQueryFromCopyQueue();

		bool		ResendQuery(SQLMsg * p);

	public:
		int			GetCopiedQueryCount() const;
		void		ResetCopiedQueryCount();
		void		AddCopiedQueryCount( int iCopiedQuery );

		//private:
	protected:
		MYSQL m_hDB;

		std::string	m_stHost;
		std::string	m_stUser;
		std::string	m_stPassword;
		std::string	m_stDB;
		std::string	m_stLocale;

		int	m_iMsgCount;
		int	m_aiPipe[2];
		int m_iPort;

		std::queue<SQLMsg *> m_queue_query;
		std::queue<SQLMsg *> m_queue_query_copy;
		//std::map<int, SQLMsg *>	m_map_kSQLMsgUnfinished;

		std::queue<SQLMsg *> m_queue_result;

		volatile bool m_bEnd;

#ifndef __WIN32__
		pthread_t m_hThread;
		std::unique_ptr<pthread_mutex_t> m_mtxQuery;
		std::unique_ptr<pthread_mutex_t> m_mtxResult;
#else
		HANDLE m_hThread;
		std::unique_ptr<CRITICAL_SECTION> m_mtxQuery;
		std::unique_ptr<CRITICAL_SECTION> m_mtxResult;
#endif

		CSemaphore m_sem;

		int	m_iQueryFinished;

		unsigned long m_ulThreadID;
		bool m_bConnected;
		int	m_iCopiedQuery;
};

class CAsyncSQL2 : public CAsyncSQL
{
	public:
		void SetLocale ( const std::string & stLocale );
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
