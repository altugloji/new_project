#ifndef __INC_METIN_II_MARKIMAGE_H__
#define __INC_METIN_II_MARKIMAGE_H__

#include <IL/il.h>
#include "minilzo.h"

#ifdef GUILD_LARGE_ICON
	#include <cstdint>

namespace GuildMarkDef
{
	// ---- Edit these to resize guild marks ----
	inline constexpr int MARK_WIDTH			= 24;
	inline constexpr int MARK_HEIGHT		= 16;
	inline constexpr int ATLAS_WIDTH		= 1024;
	inline constexpr int ATLAS_HEIGHT		= 1024;
	inline constexpr int MARKS_PER_BLOCK_X	= 4;
	inline constexpr int MARKS_PER_BLOCK_Y	= 4;

	// ---- Derived (do not edit) ----
	inline constexpr int MARK_SIZE			= MARK_WIDTH * MARK_HEIGHT;
	inline constexpr int MARK_PIXEL_BYTES	= MARK_SIZE * 4;

	inline constexpr int BLOCK_WIDTH		= MARK_WIDTH * MARKS_PER_BLOCK_X;
	inline constexpr int BLOCK_HEIGHT		= MARK_HEIGHT * MARKS_PER_BLOCK_Y;
	inline constexpr int BLOCK_SIZE			= BLOCK_WIDTH * BLOCK_HEIGHT;

	inline constexpr int BLOCK_COL_COUNT	= ATLAS_WIDTH / BLOCK_WIDTH;
	inline constexpr int BLOCK_ROW_COUNT	= ATLAS_HEIGHT / BLOCK_HEIGHT;
	inline constexpr int BLOCK_TOTAL		= BLOCK_COL_COUNT * BLOCK_ROW_COUNT;

	inline constexpr int MARK_COL_COUNT		= BLOCK_COL_COUNT * MARKS_PER_BLOCK_X;
	inline constexpr int MARK_ROW_COUNT		= BLOCK_ROW_COUNT * MARKS_PER_BLOCK_Y;
	inline constexpr int MARK_TOTAL			= MARK_COL_COUNT * MARK_ROW_COUNT;

	static_assert(BLOCK_COL_COUNT > 0, "atlas too narrow for one block column");
	static_assert(BLOCK_ROW_COUNT > 0, "atlas too short for one block row");
	static_assert(MARK_WIDTH > 0 && MARK_HEIGHT > 0);
}
#endif

typedef unsigned long Pixel;

struct SGuildMark
{
	enum
	{
#ifdef GUILD_LARGE_ICON
		WIDTH	= GuildMarkDef::MARK_WIDTH,
		HEIGHT	= GuildMarkDef::MARK_HEIGHT,
		SIZE	= GuildMarkDef::MARK_SIZE,
#else
		WIDTH = 16,
		HEIGHT = 12,
		SIZE = WIDTH * HEIGHT,
#endif
	};

	///////////////////////////////////////////////////////////////////////////////
	Pixel m_apxBuf[SIZE];

	///////////////////////////////////////////////////////////////////////////////
	void Clear();
	bool IsEmpty() const;
};

struct SGuildMarkBlock
{
	enum
	{
#ifdef GUILD_LARGE_ICON
		MARK_PER_BLOCK_WIDTH	= GuildMarkDef::MARKS_PER_BLOCK_X,
		MARK_PER_BLOCK_HEIGHT	= GuildMarkDef::MARKS_PER_BLOCK_Y,

		WIDTH	= GuildMarkDef::BLOCK_WIDTH,
		HEIGHT	= GuildMarkDef::BLOCK_HEIGHT,

		SIZE	= GuildMarkDef::BLOCK_SIZE,
#else
		MARK_PER_BLOCK_WIDTH = 4,
		MARK_PER_BLOCK_HEIGHT = 4,

		WIDTH = SGuildMark::WIDTH * MARK_PER_BLOCK_WIDTH,
		HEIGHT = SGuildMark::HEIGHT * MARK_PER_BLOCK_HEIGHT,

		SIZE = WIDTH * HEIGHT,
#endif
		MAX_COMP_SIZE = (SIZE * sizeof(Pixel)) + ((SIZE * sizeof(Pixel)) >> 4) + 64 + 3
	};

	///////////////////////////////////////////////////////////////////////////////
	Pixel	m_apxBuf[SIZE];

	BYTE 	m_abCompBuf[MAX_COMP_SIZE];
	lzo_uint m_sizeCompBuf;
	DWORD	m_crc;

	///////////////////////////////////////////////////////////////////////////////
	DWORD	GetCRC() const;

	void	CopyFrom(const BYTE * pbCompBuf, DWORD dwCompSize, DWORD crc);
	void	Compress(const Pixel * pxBuf);
};

class CGuildMarkImage
{
	public:
		enum
		{
#ifdef GUILD_LARGE_ICON
			WIDTH	= GuildMarkDef::ATLAS_WIDTH,
			HEIGHT	= GuildMarkDef::ATLAS_HEIGHT,

			BLOCK_ROW_COUNT		= GuildMarkDef::BLOCK_ROW_COUNT,
			BLOCK_COL_COUNT		= GuildMarkDef::BLOCK_COL_COUNT,
			BLOCK_TOTAL_COUNT	= GuildMarkDef::BLOCK_TOTAL,

			MARK_ROW_COUNT		= GuildMarkDef::MARK_ROW_COUNT,
			MARK_COL_COUNT		= GuildMarkDef::MARK_COL_COUNT,
			MARK_TOTAL_COUNT	= GuildMarkDef::MARK_TOTAL,
#else
			WIDTH = 512,
			HEIGHT = 512,

			BLOCK_ROW_COUNT = HEIGHT / SGuildMarkBlock::HEIGHT, // 10
			BLOCK_COL_COUNT = WIDTH / SGuildMarkBlock::WIDTH, // 8

			BLOCK_TOTAL_COUNT = BLOCK_ROW_COUNT * BLOCK_COL_COUNT, // 80

			MARK_ROW_COUNT = BLOCK_ROW_COUNT * SGuildMarkBlock::MARK_PER_BLOCK_HEIGHT, // 40
			MARK_COL_COUNT = BLOCK_COL_COUNT * SGuildMarkBlock::MARK_PER_BLOCK_WIDTH, // 32

			MARK_TOTAL_COUNT = MARK_ROW_COUNT * MARK_COL_COUNT, // 1280
#endif
			INVALID_MARK_POSITION = 0xffffffff,
		};

		CGuildMarkImage();
		virtual ~CGuildMarkImage();

		void Create();
		void Destroy();

		bool Build(const char * c_szFileName);
		bool Save(const char* c_szFileName) const;
		bool Load(const char* c_szFileName);

		void PutData(UINT x, UINT y, UINT width, UINT height, void* data) const;
		void GetData(UINT x, UINT y, UINT width, UINT height, void* data) const;

		bool SaveMark(DWORD posMark, BYTE * pbMarkImage);
		bool DeleteMark(DWORD posMark);
		bool SaveBlockFromCompressedData(DWORD posBlock, const BYTE * pbComp, DWORD dwCompSize);

		DWORD GetEmptyPosition() const;

		void GetBlockCRCList(DWORD * crcList) const;
		void GetDiffBlocks(const DWORD * crcList, std::map<BYTE, const SGuildMarkBlock *> & mapDiffBlocks);

	private:
		enum
		{
			INVALID_HANDLE = 0xffffffff,
		};

		void	BuildAllBlocks();

		SGuildMarkBlock	m_aakBlock[BLOCK_ROW_COUNT][BLOCK_COL_COUNT];
#ifdef GUILD_LARGE_ICON
		Pixel m_apxImage[WIDTH * HEIGHT];
#else
		Pixel m_apxImage[WIDTH * HEIGHT * sizeof(Pixel)];
#endif
		ILuint m_uImg;
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
