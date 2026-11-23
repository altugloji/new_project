#pragma once

#ifdef ENABLE_SECURE_MOB_LIST

template<typename TLess>
void TSecureInstancePtrVector::sort(TLess& less)
{
	SortCompare([&less](CInstanceBase* a, CInstanceBase* b)
	{
		return less(a, b);
	});
}

template<typename TFunc>
void TSecureInstancePtrVector::for_each(TFunc& func)
{
	ForEachInstance([&func](CInstanceBase* pInstance)
	{
		func(pInstance);
	});
}

#endif // ENABLE_SECURE_MOB_LIST
