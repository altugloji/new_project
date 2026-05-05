#pragma once

#include "Ref.h"
#include "Resource.h"
#include "../eterImageLib/TGAImage.h"

class CTargaResource : public CResource
{
	public:
		typedef CRef<CTargaResource> TRef;

	public:
		static TType Type();

	public:
		CTargaResource(const char * c_pszFileName);
		virtual ~CTargaResource();

		DWORD *			GetMemPtr() const;
		void			GetRect(DWORD & w, DWORD & h) const;

		TGA_HEADER &	GetTgaHeader();

	protected:
		virtual bool OnLoad(int iSize, const void * c_pvBuf);
		virtual void OnClear();
		virtual bool OnIsEmpty() const;
		virtual bool OnIsType(TType type);

	protected:
		CTGAImage	image;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
