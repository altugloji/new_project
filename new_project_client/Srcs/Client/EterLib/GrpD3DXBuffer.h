#pragma once

class CDirect3DXBuffer
{
	public:
		CDirect3DXBuffer();
		CDirect3DXBuffer(LPD3DXBUFFER lpd3dxBuffer);
		virtual ~CDirect3DXBuffer();

		void Destroy();
		void Create(LPD3DXBUFFER lpd3dxBuffer);

		void*GetPointer() const;
		int  GetSize() const;

	protected:
		LPD3DXBUFFER m_lpd3dxBuffer;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
