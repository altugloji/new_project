#pragma once

class CPythonExceptionSender : public IPythonExceptionSender
{
	public:
		CPythonExceptionSender();
		virtual ~CPythonExceptionSender();

		void Send();

	protected:
		std::set<DWORD> m_kSet_dwSendedExceptionCRC;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
