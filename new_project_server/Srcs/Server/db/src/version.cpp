#include <stdio.h>
#include <stdlib.h>

void WriteVersion()
{
#ifndef __WIN32__
	FILE* fp(fopen("VERSION.txt", "w"));

	if (nullptr != fp)
	{
		fprintf(fp, "__DB_VERSION__: %s\n", __DB_VERSION__);
		fprintf(fp, "%s@%s:%s\n", "bWV5cmE=", __HOSTNAME__, __PWD__);
		fclose(fp);
	}
	else
	{
		fprintf(stderr, "cannot open VERSION.txt\n");
		exit(0);
	}
#endif
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
