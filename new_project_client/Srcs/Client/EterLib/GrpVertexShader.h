#pragma once

#include "GrpBase.h"

class CVertexShader : public CGraphicBase
{
	public:
		CVertexShader();
		virtual ~CVertexShader();

		void Destroy();
		bool CreateFromDiskFile(const char* c_szFileName, const DWORD* c_pdwVertexDecl);

		void Set() const;

	protected:
		void Initialize();

	protected:
		LPDIRECT3DVERTEXSHADER9 m_handle;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
