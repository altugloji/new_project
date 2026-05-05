#include "StdAfx.h"
#include "../eterLib/StateManager.h"
#include "../eterlib/Camera.h"

#include "MapOutdoor.h"

static int recreate = false;

void CMapOutdoor::SetShadowTextureSize(WORD size)
{
	if (m_wShadowMapSize != size)
	{
		recreate = true;
		Tracenf("ShadowTextureSize changed %d -> %d", m_wShadowMapSize, size);
	}

	m_wShadowMapSize = size;
}

void CMapOutdoor::CreateCharacterShadowTexture()
{
	extern bool GRAPHICS_CAPS_CAN_NOT_DRAW_SHADOW;

	if (GRAPHICS_CAPS_CAN_NOT_DRAW_SHADOW)
		return;

	ReleaseCharacterShadowTexture();

	if (IsLowTextureMemory())
		SetShadowTextureSize(128);

	m_ShadowMapViewport.X = 1;
	m_ShadowMapViewport.Y = 1;
	m_ShadowMapViewport.Width = m_wShadowMapSize - 2;
	m_ShadowMapViewport.Height = m_wShadowMapSize - 2;
	m_ShadowMapViewport.MinZ = 0.0f;
	m_ShadowMapViewport.MaxZ = 1.0f;

	if (FAILED(ms_lpd3dDevice->CreateTexture(m_wShadowMapSize, m_wShadowMapSize, 1, D3DUSAGE_RENDERTARGET, D3DFMT_R5G6B5, D3DPOOL_DEFAULT, &m_lpCharacterShadowMapTexture, nullptr)))
	{
		TraceError("CMapOutdoor Unable to create Character Shadow render target texture\n");
		return;
	}

	if (FAILED(m_lpCharacterShadowMapTexture->GetSurfaceLevel(0, &m_lpCharacterShadowMapRenderTargetSurface)))
	{
		TraceError("CMapOutdoor Unable to GetSurfaceLevel Character Shadow render target texture\n");
		return;
	}

	IDirect3DSurface9* pBackBufferSurface;
	ms_lpd3dDevice->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &pBackBufferSurface);
	D3DSURFACE_DESC kDesc;
	pBackBufferSurface->GetDesc(&kDesc);
	pBackBufferSurface->Release();
	if (FAILED(ms_lpd3dDevice->CreateDepthStencilSurface(m_wShadowMapSize, m_wShadowMapSize, D3DFMT_D16, kDesc.MultiSampleType, kDesc.MultiSampleQuality, FALSE, &m_lpCharacterShadowMapDepthSurface, nullptr)))
	{
		TraceError("CMapOutdoor Unable to create Character Shadow depth Surface\n");
		return;
	}
}

void CMapOutdoor::ReleaseCharacterShadowTexture()
{
	SAFE_RELEASE(m_lpCharacterShadowMapRenderTargetSurface);
	SAFE_RELEASE(m_lpCharacterShadowMapDepthSurface);
	SAFE_RELEASE(m_lpCharacterShadowMapTexture);
}

DWORD dwLightEnable = FALSE;

bool CMapOutdoor::BeginRenderCharacterShadowToTexture()
{
	D3DXMATRIX matLightView, matLightProj;

	const CCamera* pCurrentCamera = CCameraManager::Instance().GetCurrentCamera();

	if (!pCurrentCamera)
		return false;

	if (recreate)
	{
		CreateCharacterShadowTexture();
		recreate = false;
	}

	const D3DXVECTOR3 v3Target = pCurrentCamera->GetTarget();

#ifdef ENABLE_DYNAMIC_SHADOW
	static const float SHADOW_BASE = 6250.0f;
	static const float SHADOW_ORTHO = 12750.0f;
	static const float SHADOW_ZFAR = 75000.0f;
#else
	static const float SHADOW_BASE = 1250.0f;
	static const float SHADOW_ORTHO = 2550.0f;
	static const float SHADOW_ZFAR = 15000.0f;
#endif

	const D3DXVECTOR3 v3Eye(v3Target.x - 1.732f * SHADOW_BASE,
	                        v3Target.y - SHADOW_BASE,
	                        v3Target.z + 2.0f * 1.732f * SHADOW_BASE);

	const auto val = D3DXVECTOR3(0.0f, 0.0f, 1.0f);
	D3DXMatrixLookAtRH(&matLightView,
					   &v3Eye,
					   &v3Target,
					   &val);

	D3DXMatrixOrthoRH(&matLightProj, SHADOW_ORTHO, SHADOW_ORTHO, 1.0f, SHADOW_ZFAR);

	// Snap light-view translation to texel grid to prevent shadow swimming on movement
	const float fTexelSnap = SHADOW_ORTHO / (float)m_wShadowMapSize;
	matLightView._41 = floorf(matLightView._41 / fTexelSnap) * fTexelSnap;
	matLightView._42 = floorf(matLightView._42 / fTexelSnap) * fTexelSnap;

	STATEMANAGER.SaveTransform(D3DTS_VIEW, &matLightView);
	STATEMANAGER.SaveTransform(D3DTS_PROJECTION, &matLightProj);

	dwLightEnable = STATEMANAGER.GetRenderState(D3DRS_LIGHTING);
	STATEMANAGER.SetRenderState(D3DRS_LIGHTING, FALSE);

	STATEMANAGER.SaveRenderState(D3DRS_TEXTUREFACTOR, 0xFF808080);
	STATEMANAGER.SetTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
	STATEMANAGER.SetTextureStageState(0, D3DTSS_COLORARG1, D3DTA_TFACTOR);
	STATEMANAGER.SetTextureStageState(0, D3DTSS_ALPHAOP, D3DTOP_DISABLE);
	STATEMANAGER.SetTextureStageState(1, D3DTSS_COLOROP, D3DTOP_DISABLE);

	bool bSuccess = true;

	// Backup Device Context
	if (FAILED(ms_lpd3dDevice->GetRenderTarget(0, &m_lpBackupRenderTargetSurface)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Save Window Render Target\n");
		bSuccess = false;
	}

	if (FAILED(ms_lpd3dDevice->GetDepthStencilSurface(&m_lpBackupDepthSurface)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Save Window Depth Surface\n");
		bSuccess = false;
	}

	if (FAILED(ms_lpd3dDevice->SetRenderTarget(0, m_lpCharacterShadowMapRenderTargetSurface)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Set Shadow Map Render Target\n");
		bSuccess = false;
	}

	if (FAILED(ms_lpd3dDevice->SetDepthStencilSurface(m_lpCharacterShadowMapDepthSurface)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Set Shadow Map Render Target\n");
		bSuccess = false;
	}

	if (FAILED(ms_lpd3dDevice->Clear(0L, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, D3DCOLOR_XRGB(0xFF, 0xFF, 0xFF), 1.0f, 0)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Clear Render Target");
		bSuccess = false;
	}

	if (FAILED(ms_lpd3dDevice->GetViewport(&m_BackupViewport)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Save Window Viewport\n");
		bSuccess = false;
	}

	if (FAILED(ms_lpd3dDevice->SetViewport(&m_ShadowMapViewport)))
	{
		TraceError("CMapOutdoor::BeginRenderCharacterShadowToTexture : Unable to Set Shadow Map viewport\n");
		bSuccess = false;
	}

	return bSuccess;
}

void CMapOutdoor::EndRenderCharacterShadowToTexture()
{
	ms_lpd3dDevice->SetViewport(&m_BackupViewport);

	ms_lpd3dDevice->SetRenderTarget(0, m_lpBackupRenderTargetSurface);
	ms_lpd3dDevice->SetDepthStencilSurface(m_lpBackupDepthSurface);

	SAFE_RELEASE(m_lpBackupRenderTargetSurface);
	SAFE_RELEASE(m_lpBackupDepthSurface);

	STATEMANAGER.RestoreTransform(D3DTS_VIEW);
	STATEMANAGER.RestoreTransform(D3DTS_PROJECTION);

	// Restore Device Context
	STATEMANAGER.SetRenderState(D3DRS_LIGHTING, dwLightEnable);
	STATEMANAGER.RestoreRenderState(D3DRS_TEXTUREFACTOR);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
