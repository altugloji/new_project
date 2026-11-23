#pragma once

#ifdef ENABLE_SECURE_MOB_LIST

#include <cstddef>
#include <cstdint>
#include <functional>
#include <utility>
#pragma comment(lib,"SecureMobLib.lib")
class CInstanceBase;

namespace SecureMobDetail
{
uintptr_t EncRawPtrAddress(void* p);
void* DecRawPtrAddress(uintptr_t enc);

template<typename T>
uintptr_t EncRawPtr(T* p)
{
	return EncRawPtrAddress(reinterpret_cast<void*>(p));
}

template<typename T>
T* DecRawPtr(uintptr_t enc)
{
	return reinterpret_cast<T*>(DecRawPtrAddress(enc));
}

class EncryptedDword
{
	DWORD m_enc;
public:
	EncryptedDword();
	explicit EncryptedDword(DWORD v);

	void Set(DWORD v);
	DWORD Get() const;

	operator DWORD() const;
	EncryptedDword& operator=(DWORD v);
};

class EncryptedFloat
{
	DWORD m_enc;
public:
	EncryptedFloat();
	explicit EncryptedFloat(float v);

	void Set(float v);
	float Get() const;

	operator float() const;
	EncryptedFloat& operator=(float v);
	EncryptedFloat& operator+=(float v);
	bool operator==(float rhs) const;
	bool operator!=(float rhs) const;
};
}

class TSecureCharacterInstanceMap
{
public:
	typedef std::pair<DWORD, CInstanceBase*> value_type;

	class iterator
	{
	public:
		typedef value_type value_type;

		iterator();
		iterator(const iterator& rhs);
		~iterator();
		iterator& operator=(const iterator& rhs);

		bool operator==(const iterator& rhs) const;
		bool operator!=(const iterator& rhs) const;

		iterator& operator++();
		iterator operator++(int);

		value_type operator*() const;

		struct pair_proxy
		{
			DWORD first;
			CInstanceBase* second;

			pair_proxy(const value_type& v);
			const pair_proxy* operator->() const;
		};

		pair_proxy operator->() const;

	private:
		struct State;
		State* m_state;

		explicit iterator(State* state);
		friend class TSecureCharacterInstanceMap;
	};

	TSecureCharacterInstanceMap();
	~TSecureCharacterInstanceMap();

	TSecureCharacterInstanceMap(const TSecureCharacterInstanceMap&) = delete;
	TSecureCharacterInstanceMap& operator=(const TSecureCharacterInstanceMap&) = delete;

	iterator begin();
	iterator end();
	iterator find(DWORD key);
	void insert(const value_type& v);
	void Set(DWORD key, CInstanceBase* p);
	void erase(iterator it);
	size_t size() const;
	void clear();

private:
	struct Impl;
	Impl* m_impl;
};

class TSecureInstancePtrVector
{
public:
	TSecureInstancePtrVector();
	~TSecureInstancePtrVector();

	void clear();
	void push_back(CInstanceBase* p);
	size_t size() const;
	CInstanceBase* at(size_t idx) const;

	template<typename TLess>
	void sort(TLess& less);

	template<typename TFunc>
	void for_each(TFunc& func);

private:
	struct Impl;
	Impl* m_impl;

	void SortCompare(const std::function<bool(CInstanceBase*, CInstanceBase*)>& less);
	void ForEachInstance(const std::function<void(CInstanceBase*)>& func);
};

#include "SecureMobLib.inl"

#endif // ENABLE_SECURE_MOB_LIST
