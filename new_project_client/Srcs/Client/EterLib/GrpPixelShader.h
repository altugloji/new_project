#pragma once

#include "GrpBase.h"

class CPixelShader : public CGraphicBase
{
	public:
		CPixelShader();
		virtual ~CPixelShader();

		void Destroy();
		bool CreateFromDiskFile(const char* c_szFileName);

		void Set() const;

	protected:
		void Initialize();

	protected:
		LPDIRECT3DPIXELSHADER9 m_handle;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
