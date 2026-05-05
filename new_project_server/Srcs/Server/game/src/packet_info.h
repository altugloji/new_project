#ifndef __INC_METIN_II_GAME_PACKET_HEADER_INFO_H__
#define __INC_METIN_II_GAME_PACKET_HEADER_INFO_H__

#include "packet.h"

typedef struct SPacketElement
{
	int		iSize;
	std::string	stName;
	int		iCalled;
	DWORD	dwLoad;
} TPacketElement;

class CPacketInfo
{
	public:
		CPacketInfo();
		virtual ~CPacketInfo();

		void Set(int header, int size, const char * c_pszName, bool bSeq=false);
		bool Get(int header, int * size, const char ** c_ppszName);

		void Start();
		void End() const;

		void Log(const char * c_pszFileName);


	private:
		TPacketElement * GetElement(int header);

	protected:
		std::map<int, TPacketElement *> m_pPacketMap;
		TPacketElement * m_pCurrentPacket;
		DWORD m_dwStartTime;
};

class CPacketInfoCG : public CPacketInfo
{
	public:
		CPacketInfoCG();
		virtual ~CPacketInfoCG();
};

// PacketInfo P2P
class CPacketInfoGG : public CPacketInfo
{
	public:
		CPacketInfoGG();
		virtual ~CPacketInfoGG();
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
