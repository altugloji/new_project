#pragma once

#include "GrpVertexBuffer.h"

class CStaticVertexBuffer : public CGraphicVertexBuffer
{
	public:
		CStaticVertexBuffer();
		virtual ~CStaticVertexBuffer();

		bool Create(int vtxCount, DWORD fvf, bool isManaged=true);
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
