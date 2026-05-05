#pragma once

#include <deque>
#include <string>

class CPathStack
{
	public:
		CPathStack();
		virtual ~CPathStack();

		void SetBase();

		void MoveBase() const;

		void Push();

		bool Pop();

		void Move(const char* c_szPathName) const;
		void GetCurrentPathName(std::string* pstCurPathName) const;

	protected:
		std::string				m_stBasePathName;
		std::deque<std::string>	m_stPathNameDeque;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
