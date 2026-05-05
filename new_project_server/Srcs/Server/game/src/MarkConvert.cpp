#include "stdafx.h"
#include "MarkManager.h"

#ifdef __WIN32__
#include <direct.h>
#endif

#define OLD_MARK_INDEX_FILENAME "guild_mark.idx"
#define OLD_MARK_DATA_FILENAME "guild_mark.tga"

static Pixel * LoadOldGuildMarkImageFile()
{
	FILE * fp = fopen(OLD_MARK_DATA_FILENAME, "rb");

	if (!fp)
	{
		sys_err("cannot open %s", OLD_MARK_INDEX_FILENAME);
		return nullptr;
	}

	const int dataSize = 512 * 512 * sizeof(Pixel);
	const auto dataPtr = (Pixel *) malloc(dataSize);

	fread(dataPtr, dataSize, 1, fp);

	fclose(fp);

	return dataPtr;
}

bool GuildMarkConvert(const std::vector<DWORD> & vecGuildID)
{
#ifndef __WIN32__
	mkdir("mark", S_IRWXU);
#else
	_mkdir("mark");
#endif

#ifndef __WIN32__
	if (0 != access(OLD_MARK_INDEX_FILENAME, F_OK))
#else
	if (0 != _access(OLD_MARK_INDEX_FILENAME, 0))
#endif
		return true;

	FILE* fp = fopen(OLD_MARK_INDEX_FILENAME, "r");

	if (nullptr == fp)
		return false;

	Pixel * oldImagePtr = LoadOldGuildMarkImageFile();

	if (nullptr == oldImagePtr)
	{
		fclose(fp);
		return false;
	}

	sys_log(0, "Guild Mark Converting Start.");

	char line[256];
	DWORD guild_id;
	DWORD mark_id;
	Pixel mark[SGuildMark::SIZE];

	while (fgets(line, sizeof(line)-1, fp))
	{
		sscanf(line, "%u %u", &guild_id, &mark_id);

		if (find(vecGuildID.begin(), vecGuildID.end(), guild_id) == vecGuildID.end())
		{
			sys_log(0, "  skipping guild ID %u", guild_id);
			continue;
		}

		const uint row = mark_id / 32;
		const uint col = mark_id % 32;

		if (row >= 42)
		{
			sys_err("invalid mark_id %u", mark_id);
			continue;
		}

#ifdef GUILD_LARGE_ICON
		const uint OLD_MARK_WIDTH = 16;
		const uint OLD_MARK_HEIGHT = 12;
		const uint OLD_IMAGE_WIDTH = 512;

		const uint sx = col * OLD_MARK_WIDTH;
		const uint sy = row * OLD_MARK_HEIGHT;

		Pixel * src = oldImagePtr + sy * OLD_IMAGE_WIDTH + sx;
#else
		const uint sx = col * 16;
		const uint sy = row * 12;

		Pixel * src = oldImagePtr + sy * 512 + sx;
#endif
		Pixel * dst = mark;

#ifdef GUILD_LARGE_ICON
		memset(mark, 0, sizeof(mark));

		for (uint y = 0; y != OLD_MARK_HEIGHT; ++y)
#else
		for (int y = 0; y != SGuildMark::HEIGHT; ++y)
#endif
		{
#ifdef GUILD_LARGE_ICON
			for (uint x = 0; x != OLD_MARK_WIDTH; ++x)
#else
			for (int x = 0; x != SGuildMark::WIDTH; ++x)
#endif
				*(dst++) = *(src+x);
#ifdef GUILD_LARGE_ICON
			dst += (SGuildMark::WIDTH - OLD_MARK_WIDTH);
			src += OLD_IMAGE_WIDTH;
#else
			src += 512;
#endif
		}

		CGuildMarkManager::instance().SaveMark(guild_id, (BYTE *) mark);
		line[0] = '\0';
	}

	free(oldImagePtr);
	fclose(fp);

#ifndef __WIN32__
	system("mv -f guild_mark.idx guild_mark.idx.removable");
	system("mv -f guild_mark.tga guild_mark.tga.removable");
#else
	system("move /Y guild_mark.idx guild_mark.idx.removable");
	system("move /Y guild_mark.tga guild_mark.tga.removable");
#endif

	sys_log(0, "Guild Mark Converting Complete.");

	return true;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
