#include <stdio.h>

void WriteVersion()
{
#ifndef __WIN32__
	FILE* fp = fopen("VERSION.txt", "w");

	if (fp)
	{
		fprintf(fp, "__GAME_VERSION__: %s\n", __GAME_VERSION__);
		fprintf(fp, "%s@%s:%s\n", "bWV5cmE=", __HOSTNAME__, __PWD__);
		fclose(fp);
	}
#endif
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
