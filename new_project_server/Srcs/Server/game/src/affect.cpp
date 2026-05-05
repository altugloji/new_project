#include "stdafx.h"

#include "affect.h"

namespace {

template<class T, size_t BlockSize = 256>
class object_pool
{
public:
	object_pool() : m_free(nullptr) {}

	~object_pool()
	{
		for (auto* blk : m_blocks)
			::operator delete(blk);
	}

	T* alloc()
	{
		if (!m_free)
			grow();
		Node* n = m_free;
		m_free = n->next;
		return reinterpret_cast<T*>(n);
	}

	void free(T* p)
	{
		Node* n = reinterpret_cast<Node*>(p);
		n->next = m_free;
		m_free = n;
	}

private:
	union Node
	{
		Node* next;
		alignas(T) char storage[sizeof(T)];
	};

	void grow()
	{
		Node* blk = static_cast<Node*>(::operator new(sizeof(Node) * BlockSize));
		m_blocks.push_back(blk);
		for (size_t i = 0; i < BlockSize - 1; ++i)
			blk[i].next = &blk[i + 1];
		blk[BlockSize - 1].next = nullptr;
		m_free = blk;
	}

	Node* m_free;
	std::vector<Node*> m_blocks;
};

object_pool<CAffect> affect_pool;

} // namespace

CAffect* CAffect::Acquire()
{
	return affect_pool.alloc();
}

void CAffect::Release(CAffect* p)
{
	affect_pool.free(p);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
