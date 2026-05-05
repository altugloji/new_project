#ifndef __MILESLIB_CSOUNDBASE_H__
#define __MILESLIB_CSOUNDBASE_H__

#include <map>
#include <vector>
#include "SoundData.h"

typedef struct SProvider
{
	char*		name;
	HPROVIDER	hProvider;
} TProvider;

typedef std::map<DWORD, CSoundData*> TSoundDataMap;

class CSoundBase
{
	public:
		CSoundBase();
		virtual ~CSoundBase();

		void					Initialize() const;
		void					Destroy() const;

		CSoundData *			AddFile(DWORD dwFileCRC, const char* filename) const;
		DWORD					GetFileCRC(const char* filename) const;

	protected:
		static int								ms_iRefCount;
		static HDIGDRIVER						ms_DIGDriver;
		static TProvider *						ms_pProviderDefault;
		static std::vector<TProvider>			ms_ProviderVector;
		static TSoundDataMap					ms_dataMap;
		static bool								ms_bInitialized;
};

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
