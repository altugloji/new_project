#pragma once

#include "GrpImageInstance.h"
#include "../UserInterface/Locale_inc.h"

class CGraphicExpandedImageInstance : public CGraphicImageInstance
{
	public:
		static DWORD Type();
		static void DeleteExpandedImageInstance(CGraphicExpandedImageInstance * pkInstance)
		{
			pkInstance->Destroy();
			ms_kPool.Free(pkInstance);
		}

		enum ERenderingMode
		{
			RENDERING_MODE_NORMAL,
			RENDERING_MODE_SCREEN,
			RENDERING_MODE_COLOR_DODGE,
			RENDERING_MODE_MODULATE,
		};

	public:
		CGraphicExpandedImageInstance();
		virtual ~CGraphicExpandedImageInstance();

		void Destroy();

		void SetDepth(float fDepth);
		void SetOrigin();
		void SetOrigin(float fx, float fy);
		void SetRotation(float fRotation);
		void SetScale(float fx, float fy);
		void SetRenderingRect(float fLeft, float fTop, float fRight, float fBottom);
		void SetRenderingMode(int iMode);
#if defined(__BL_MULTI_LANGUAGE_PREMIUM__)
		bool IsMouseOverIn(int mx, int my);
		int GetScaledHeight() const;
		int GetScaledWidth() const;
#endif

	protected:
		void Initialize();

#if defined(__BL_CLIP_MASK__)
		void OnRender(RECT* rMask) override;
#else
		void OnRender();
#endif
		void OnSetImagePointer();

		BOOL OnIsType(DWORD dwType);

	protected:
		float m_fDepth;
		D3DXVECTOR2 m_v2Origin;
		D3DXVECTOR2 m_v2Scale;
		float m_fRotation;
		RECT m_RenderingRect;
		int m_iRenderingMode;

	public:
		static void CreateSystem(UINT uCapacity);
		static void DestroySystem();

		static CGraphicExpandedImageInstance* New();
		static void Delete(CGraphicExpandedImageInstance* pkImgInst);

		static CDynamicPool<CGraphicExpandedImageInstance>		ms_kPool;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
