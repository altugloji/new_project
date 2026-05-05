#pragma once

#include "../eterlib/GrpTextInstance.h"
#include "../eterlib/GrpMarkInstance.h"
#include "../eterlib/GrpImageInstance.h"
#include "../eterlib/GrpExpandedImageInstance.h"

#include "../eterGrnLib/ThingInstance.h"

class CPythonGraphic : public CScreen, public CSingleton<CPythonGraphic>
{
	public:
		CPythonGraphic();
		virtual ~CPythonGraphic();

		void Destroy() const;

		void PushState();
		void PopState();

		LPDIRECT3D9EX GetD3D() const;

		float GetOrthoDepth() const;
		void SetInterfaceRenderState() const;
		void SetGameRenderState() const;

		void SetCursorPosition(int x, int y) const;

		void SetOmniLight() const;

		void SetViewport(float fx, float fy, float fWidth, float fHeight);
		void RestoreViewport() const;

		long GenerateColor(float r, float g, float b, float a) const;
		void RenderDownButton(float sx, float sy, float ex, float ey) const;
		void RenderUpButton(float sx, float sy, float ex, float ey) const;

		void RenderImage(CGraphicImageInstance* pImageInstance, float x, float y) const;
		void RenderAlphaImage(CGraphicImageInstance* pImageInstance, float x, float y, float aLeft, float aRight) const;
		void RenderCoolTimeBox(float fxCenter, float fyCenter, float fRadius, float fTime) const;

		bool SaveScreenShot(const char *szFileName) const;

		DWORD GetAvailableMemory() const;
		void SetGamma(float fGammaFactor = 1.0f) const;

	protected:
		typedef struct SState
		{
			D3DXMATRIX matView;
			D3DXMATRIX matProj;
		} TState;

		DWORD		m_lightColor;
		DWORD		m_darkColor;

	protected:
		std::stack<TState>						m_stateStack;

		D3DXMATRIX								m_SaveWorldMatrix;

		CCullingManager							m_CullingManager;

		D3DVIEWPORT9							m_backupViewport;

		float									m_fOrthoDepth;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
