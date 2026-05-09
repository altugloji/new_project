#include "StdAfx.h"
#ifdef ENABLE_RENDER_TARGET
#include "../EterBase/Stl.h"
#include "GrpRenderTargetTexture.h"
#include "StateManager.h"

CGraphicRenderTargetTexture::CGraphicRenderTargetTexture(): m_d3dFormat{ D3DFMT_A8R8G8B8 }, m_depthStencilFormat{ D3DFMT_UNKNOWN }
{
	Initialize();
	memset(&m_renderRect, 0, sizeof(m_renderRect));
}

CGraphicRenderTargetTexture::~CGraphicRenderTargetTexture()
{
	Reset();
}

void CGraphicRenderTargetTexture::ReleaseTextures()
{
	safe_release(m_lpd3dRenderTexture);
	safe_release(m_lpd3dRenderTargetSurface);
	safe_release(m_lpd3dDepthSurface);
	safe_release(m_lpd3dDepthSurface);
	safe_release(m_lpd3dOriginalRenderTarget);
	safe_release(m_lpd3dOldDepthBufferSurface);
	memset(&m_renderRect, 0, sizeof(m_renderRect));
}

bool CGraphicRenderTargetTexture::Create(const int width, const int height, const D3DFORMAT texFormat, const D3DFORMAT depthFormat)
{
	Reset();
	m_height = height;
	m_width = width;
	if (!CreateRenderTexture(width, height, texFormat))
		return false;
	if (!CreateRenderDepthStencil(width, height, depthFormat))
		return false;
	return true;
}

void CGraphicRenderTargetTexture::CreateTextures()
{
	if (CreateRenderTexture(m_width, m_height, m_d3dFormat))
		CreateRenderDepthStencil(m_width, m_height, m_depthStencilFormat);
}

bool CGraphicRenderTargetTexture::CreateRenderTexture(const int width, const int height, const D3DFORMAT format)
{
	m_d3dFormat = format;
	if (FAILED(ms_lpd3dDevice->CreateTexture(width, height, 0, D3DUSAGE_RENDERTARGET, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, &m_lpd3dRenderTexture, nullptr)))
		return false;
	if (FAILED(m_lpd3dRenderTexture->GetSurfaceLevel(0, &m_lpd3dRenderTargetSurface)))
		return false;
	return true;
}

bool CGraphicRenderTargetTexture::CreateRenderDepthStencil(const int width, const int height, const D3DFORMAT format)
{
	m_depthStencilFormat = format;

	return (ms_lpd3dDevice->CreateDepthStencilSurface(width, height, m_depthStencilFormat, D3DMULTISAMPLE_NONE, 0, false, &m_lpd3dDepthSurface, nullptr)) == D3D_OK;
}

void CGraphicRenderTargetTexture::SetRenderTarget()
{
	ms_lpd3dDevice->GetRenderTarget(0, &m_lpd3dOriginalRenderTarget);
	ms_lpd3dDevice->GetDepthStencilSurface(&m_lpd3dOldDepthBufferSurface);

	ms_lpd3dDevice->SetRenderTarget(0, m_lpd3dRenderTargetSurface);
	ms_lpd3dDevice->SetDepthStencilSurface(m_lpd3dDepthSurface);
}

void CGraphicRenderTargetTexture::ResetRenderTarget()
{
	ms_lpd3dDevice->SetRenderTarget(0, m_lpd3dOriginalRenderTarget);
	ms_lpd3dDevice->SetDepthStencilSurface(m_lpd3dOldDepthBufferSurface);

	safe_release(m_lpd3dOriginalRenderTarget);
	safe_release(m_lpd3dOldDepthBufferSurface);
}

void CGraphicRenderTargetTexture::Clear()
{
	ms_lpd3dDevice->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, D3DCOLOR_ARGB(0, 0, 0, 0), 1.0f, 0);
}

void CGraphicRenderTargetTexture::Render(RECT* rect, RECT* mask_render) const
{
	if (!rect)
		return;

	STATEMANAGER.SaveRenderState(D3DRS_ALPHABLENDENABLE, STATEMANAGER.GetRenderState(D3DRS_ALPHABLENDENABLE));
	STATEMANAGER.SaveRenderState(D3DRS_SRCBLEND, STATEMANAGER.GetRenderState(D3DRS_SRCBLEND));

	STATEMANAGER.SetRenderState(D3DRS_ALPHABLENDENABLE, TRUE);
	STATEMANAGER.SetRenderState(D3DRS_SRCBLEND, D3DBLEND_INVDESTCOLOR);

	float sx = static_cast<float>(rect->left) - 0.5f;
	float sy = static_cast<float>(rect->top) - 0.5f;
	float ex = static_cast<float>(rect->right) - 0.5f;
	float ey = static_cast<float>(rect->bottom) - 0.5f;

	float su = 0.0f;
	float sv = 0.0f;
	float eu = 1.0f;
	float ev = 1.0f;

	if (mask_render)
	{
		const float width = ex - sx;
		const float height = ey - sy;

		if (width <= 0.0f || height <= 0.0f)
		{
			STATEMANAGER.RestoreRenderState(D3DRS_SRCBLEND);
			STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
			return;
		}

		if (ex < static_cast<float>(mask_render->left))
		{
			STATEMANAGER.RestoreRenderState(D3DRS_SRCBLEND);
			STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
			return;
		}

		if (sx < static_cast<float>(mask_render->left))
		{
			const float cut = static_cast<float>(mask_render->left) - sx;
			su += cut / width;
			sx += cut;
		}

		if (ey < static_cast<float>(mask_render->top))
		{
			STATEMANAGER.RestoreRenderState(D3DRS_SRCBLEND);
			STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
			return;
		}

		if (sy < static_cast<float>(mask_render->top))
		{
			const float cut = static_cast<float>(mask_render->top) - sy;
			sv += cut / height;
			sy += cut;
		}

		if (sx > static_cast<float>(mask_render->right))
		{
			STATEMANAGER.RestoreRenderState(D3DRS_SRCBLEND);
			STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
			return;
		}

		if (ex > static_cast<float>(mask_render->right))
		{
			const float cut = ex - static_cast<float>(mask_render->right);
			eu -= cut / width;
			ex -= cut;
		}

		if (sy > static_cast<float>(mask_render->bottom))
		{
			STATEMANAGER.RestoreRenderState(D3DRS_SRCBLEND);
			STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
			return;
		}

		if (ey > static_cast<float>(mask_render->bottom))
		{
			const float cut = ey - static_cast<float>(mask_render->bottom);
			ev -= cut / height;
			ey -= cut;
		}
	}

	TPDTVertex pVertices[4];

	pVertices[0].position = TPosition(sx, sy, 0.0f);
	pVertices[0].texCoord = TTextureCoordinate(su, sv);
	pVertices[0].diffuse = 0xffffffff;

	pVertices[1].position = TPosition(ex, sy, 0.0f);
	pVertices[1].texCoord = TTextureCoordinate(eu, sv);
	pVertices[1].diffuse = 0xffffffff;

	pVertices[2].position = TPosition(sx, ey, 0.0f);
	pVertices[2].texCoord = TTextureCoordinate(su, ev);
	pVertices[2].diffuse = 0xffffffff;

	pVertices[3].position = TPosition(ex, ey, 0.0f);
	pVertices[3].texCoord = TTextureCoordinate(eu, ev);
	pVertices[3].diffuse = 0xffffffff;

	if (SetPDTStream(pVertices, 4))
	{
		CGraphicBase::SetDefaultIndexBuffer(CGraphicBase::DEFAULT_IB_FILL_RECT);

		STATEMANAGER.SetTexture(0, GetRenderTargetTexture());
		STATEMANAGER.SetTexture(1, NULL);
		STATEMANAGER.SetFVF(D3DFVF_XYZ | D3DFVF_TEX1 | D3DFVF_DIFFUSE);
		STATEMANAGER.DrawIndexedPrimitive(D3DPT_TRIANGLELIST, 0, 4, 0, 2, 0);
	}

	STATEMANAGER.RestoreRenderState(D3DRS_SRCBLEND);
	STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
}

void CGraphicRenderTargetTexture::Reset()
{
	Destroy();
	ReleaseTextures();
	m_d3dFormat = D3DFMT_A8R8G8B8;

	m_depthStencilFormat = D3DFMT_UNKNOWN;
}
#endif

