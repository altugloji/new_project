#pragma once

#ifdef URIEL_ANTI_CHEAT
#include "urielacsdk.h"

template <typename T>
class TAbstractSingleton
{
	static safe_variable_weak<T*>* ms_singleton;

public:
	TAbstractSingleton()
	{
		assert(!ms_singleton);
		int offset = (int) (T*) 1 - (int) (CSingleton <T>*) (T*) 1;
		T* p = (T*)((int)this + offset);
		ms_singleton = new safe_variable_weak<T*>(p);
	}

	virtual ~TAbstractSingleton()
	{
		assert(ms_singleton);
		delete ms_singleton;
		ms_singleton = 0;
	}

	__forceinline static T & GetSingleton()
	{
		assert(ms_singleton!=NULL);
		return *(T*)(ms_singleton->get());
	}
};

template <typename T> safe_variable_weak<T*>* TAbstractSingleton <T>::ms_singleton = 0;
#else
template <typename T>
class TAbstractSingleton
{
	static T * ms_singleton;

public:
	TAbstractSingleton()
	{
		assert(!ms_singleton);
		const int offset = (int) (T*) 1 - (int) (CSingleton <T>*) (T*) 1;
		ms_singleton = (T*) ((int) this + offset);
	}

	virtual ~TAbstractSingleton()
	{
		assert(ms_singleton);
		ms_singleton = 0;
	}

	__forceinline static T & GetSingleton()
	{
		assert(ms_singleton!=nullptr);
		return (*ms_singleton);
	}
};

template <typename T> T * TAbstractSingleton <T>::ms_singleton = nullptr;
#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
