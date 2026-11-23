#pragma once

#include "../UserInterface/Locale_inc.h"

#include <algorithm>
#include <map>
#include <vector>

class CInstanceBase;

#ifdef ENABLE_SECURE_MOB_LIST
#include "SecureMobLib.h"

namespace SecureMob
{
typedef TSecureCharacterInstanceMap TAliveInstanceMap;
typedef TSecureInstancePtrVector TAliveInstanceSortBuffer;

template<typename T>
struct TPoolStorage
{
	typedef uintptr_t TStored;
	static TStored Store(T* p) { return SecureMobDetail::EncRawPtr(p); }
	static T* Load(TStored enc) { return SecureMobDetail::DecRawPtr<T>(enc); }
};
}

namespace SecureMobDetail
{
typedef EncryptedDword TRaceDword;
typedef EncryptedFloat TRaceFloat;
}

#else

namespace SecureMob
{
typedef std::map<DWORD, CInstanceBase*> TAliveInstanceMap;

class TAliveInstanceSortBuffer
{
public:
	void clear()
	{
		m_data.clear();
	}

	void push_back(CInstanceBase* p)
	{
		m_data.push_back(p);
	}

	template<typename TLess>
	void sort(TLess& less)
	{
		std::sort(m_data.begin(), m_data.end(), less);
	}

	template<typename TFunc>
	void for_each(TFunc& func)
	{
		std::for_each(m_data.begin(), m_data.end(), func);
	}

private:
	std::vector<CInstanceBase*> m_data;
};

template<typename T>
struct TPoolStorage
{
	typedef T* TStored;
	static TStored Store(T* p) { return p; }
	static T* Load(TStored enc) { return enc; }
};
}

namespace SecureMobDetail
{
typedef DWORD TRaceDword;
typedef float TRaceFloat;
}

#endif

// ENABLE_SECURE_MOB_LIST -> Locale_inc.h uzerinden acilir/kapanir.
// Acik : TSecureCharacterInstanceMap + SecureMobLib.lib
// Kapali: std::map<DWORD,CInstanceBase*> (vanilla)
