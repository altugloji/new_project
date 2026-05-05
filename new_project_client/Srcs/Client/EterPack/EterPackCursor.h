#ifndef __INC_ETERPACKCURSOR_H__
#define __INC_ETERPACKCURSOR_H__

#include "EterPack.h"

class CEterPackCursor
{
	public:
		CEterPackCursor(CEterPack * pack);
		~CEterPackCursor();

		bool		Open(const char* filename);
		void		Close();
		void		Seek(long offset);
		bool		Read(LPVOID data, long size);
		long		Size() const;

	private:
		CEterPack * m_pPack;
		CMappedFile m_file;
		LPCVOID 	m_pData;
		long		m_ReadPoint;
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
