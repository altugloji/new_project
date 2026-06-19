#ifndef __INC_ETERLIB_SINGLETON_H__
#define __INC_ETERLIB_SINGLETON_H__
#pragma once

#include <cassert>

#ifdef URIEL_ANTI_CHEAT
#include "../UserInterface/urielacsdk.h"
#endif

#if !defined(WIN32) && !defined(__forceinline)
#define __forceinline __attribute__((always_inline))
#endif

#ifdef URIEL_ANTI_CHEAT
template <typename T> class CSingleton
{
	static safe_variable_weak<T*>* ms_singleton;

public:
	CSingleton()
	{
		assert(!ms_singleton);

		T* p = static_cast<T*>(this);
		ms_singleton = new safe_variable_weak<T*>(p);
	}

	virtual ~CSingleton()
	{
		assert(ms_singleton);
		delete ms_singleton;
		ms_singleton = 0;
	}

	__forceinline static T& Instance()
	{
		assert(ms_singleton);
		return *(T*)(ms_singleton->get());
	}

	__forceinline static T* InstancePtr()
	{
		return (T*)(ms_singleton->get());
	}

	__forceinline static T& instance()
	{
		assert(ms_singleton);
		return *(T*)(ms_singleton->get());
	}

	__forceinline static T* instance_ptr()
	{
		return (T*)(ms_singleton->get());
	}

	// prevent manager 0x0 by deleting copy/assignment operators
	CSingleton(const CSingleton&) = delete;
	CSingleton& operator=(const CSingleton&) = delete;
	CSingleton(CSingleton&&) = delete;
	CSingleton& operator=(CSingleton&&) = delete;
};

template <typename T> safe_variable_weak<T*>* CSingleton <T>::ms_singleton = 0;
#else
template <typename T> class CSingleton
{
	static inline T * ms_singleton = nullptr;

public:
	CSingleton()
	{
		assert(!ms_singleton);
		ms_singleton = static_cast<T*>(this);
	}

	virtual ~CSingleton()
	{
		assert(ms_singleton);
		ms_singleton = nullptr;
	}

	__forceinline static T & Instance()
	{
		assert(ms_singleton);
		return (*ms_singleton);
	}

	__forceinline static T * InstancePtr()
	{
		return (ms_singleton);
	}

	__forceinline static T & instance()
	{
		assert(ms_singleton);
		return (*ms_singleton);
	}

	__forceinline static T * instance_ptr()
	{
		return (ms_singleton);
	}

	// prevent manager 0x0 by deleting copy/assignment operators
	CSingleton(const CSingleton&) = delete;
	CSingleton& operator=(const CSingleton&) = delete;
	CSingleton(CSingleton&&) = delete;
	CSingleton& operator=(CSingleton&&) = delete;
};
#endif

template <typename T>
using singleton = CSingleton<T>;

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
