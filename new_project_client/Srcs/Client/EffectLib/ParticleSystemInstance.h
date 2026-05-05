#pragma once

#include "EffectElementBaseInstance.h"
#include "ParticleInstance.h"
#include "ParticleProperty.h"

#include "../eterlib/GrpScreen.h"
#include "../eterlib/StateManager.h"
#include "../eterLib/GrpImageInstance.h"
#include "../eterLib/GrpVertexBuffer.h"
#include "EmitterProperty.h"

struct TParticleBatchVertex
{
	D3DXVECTOR3 position;
	DWORD diffuse;
	D3DXVECTOR2 texCoord;
};

inline void CopyParticleQuad(TParticleBatchVertex* pDst, const TPTVertex* mesh, DWORD color)
{
	pDst[0].position = mesh[0].position; pDst[0].diffuse = color; pDst[0].texCoord = mesh[0].texCoord;
	pDst[1].position = mesh[1].position; pDst[1].diffuse = color; pDst[1].texCoord = mesh[1].texCoord;
	pDst[2].position = mesh[2].position; pDst[2].diffuse = color; pDst[2].texCoord = mesh[2].texCoord;
	pDst[3].position = mesh[2].position; pDst[3].diffuse = color; pDst[3].texCoord = mesh[2].texCoord;
	pDst[4].position = mesh[1].position; pDst[4].diffuse = color; pDst[4].texCoord = mesh[1].texCoord;
	pDst[5].position = mesh[3].position; pDst[5].diffuse = color; pDst[5].texCoord = mesh[3].texCoord;
}

#ifdef ENABLE_RENDER_PREVIEW_EFFECTS
inline bool& GetIgnoreFrustrumFlag() {
	static bool s_IgnoreFrustrum;
	return s_IgnoreFrustrum;
}
#endif

class CParticleSystemInstance : public CEffectElementBaseInstance
{
	public:
		static void DestroySystem();

		static CParticleSystemInstance* New();
		static void Delete(CParticleSystemInstance* pkData);

		static CDynamicPool<CParticleSystemInstance>	ms_kPool;
		static CGraphicVertexBuffer ms_kParticleVB;
		static const UINT PARTICLE_VB_MAX_VERTS = 6144;

	public:
		template <typename T>
		inline void ForEachParticleRendering(T && FunObj)
		{
			if (ms_kParticleVB.GetD3DVertexBuffer() == NULL)
				ms_kParticleVB.Create(PARTICLE_VB_MAX_VERTS, D3DFVF_XYZ | D3DFVF_DIFFUSE | D3DFVF_TEX1,
					D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY, D3DPOOL_DEFAULT);

			DWORD dwFrameIndex;
			for (dwFrameIndex = 0; dwFrameIndex < m_kVct_pkImgInst.size(); dwFrameIndex++)
			{
				STATEMANAGER.SetTexture(0, m_kVct_pkImgInst[dwFrameIndex]->GetTextureReference().GetD3DTexture());

				TParticleBatchVertex* pVerts = NULL;
				ms_kParticleVB.GetD3DVertexBuffer()->Lock(0, 0,
					reinterpret_cast<void**>(&pVerts), D3DLOCK_DISCARD | D3DLOCK_NOSYSLOCK);
				UINT nVerts = 0;
				bool bAbort = false;

				TParticleInstanceList::iterator itor = m_ParticleInstanceListVector[dwFrameIndex].begin();
				for (; itor != m_ParticleInstanceListVector[dwFrameIndex].end(); ++itor)
				{
#ifdef ENABLE_RENDER_PREVIEW_EFFECTS
					if (!GetIgnoreFrustrumFlag() && !InFrustum(*itor))
#else
					if (!InFrustum(*itor))
#endif
					{
						bAbort = true;
						break;
					}

					UINT nAdded = FunObj(*itor, pVerts + nVerts);
					nVerts += nAdded;

					if (nVerts + 18 > PARTICLE_VB_MAX_VERTS)
					{
						ms_kParticleVB.GetD3DVertexBuffer()->Unlock();
						ms_kParticleVB.SetStream(sizeof(TParticleBatchVertex));
						STATEMANAGER.DrawPrimitive(D3DPT_TRIANGLELIST, 0, nVerts / 3);
						ms_kParticleVB.GetD3DVertexBuffer()->Lock(0, 0,
							reinterpret_cast<void**>(&pVerts), D3DLOCK_DISCARD | D3DLOCK_NOSYSLOCK);
						nVerts = 0;
					}
				}

				ms_kParticleVB.GetD3DVertexBuffer()->Unlock();

				if (nVerts > 0)
				{
					ms_kParticleVB.SetStream(sizeof(TParticleBatchVertex));
					STATEMANAGER.DrawPrimitive(D3DPT_TRIANGLELIST, 0, nVerts / 3);
				}

				if (bAbort)
					return;
			}
		}

		CParticleSystemInstance();
		virtual ~CParticleSystemInstance();

		void OnSetDataPointer(CEffectElementBase * pElement);

		void CreateParticles(float fElapsedTime);

		inline bool InFrustum(CParticleInstance * pInstance) const
		{
			if (m_pParticleProperty->m_bAttachFlag)
				return CScreen::GetFrustum().ViewVolumeTest(Vector3d(
					pInstance->m_v3Position.x + mc_pmatLocal->_41,
					pInstance->m_v3Position.y + mc_pmatLocal->_42,
					pInstance->m_v3Position.z + mc_pmatLocal->_43
					),pInstance->GetRadiusApproximation())!=VS_OUTSIDE;
			else
				return CScreen::GetFrustum().ViewVolumeTest(Vector3d(pInstance->m_v3Position.x,pInstance->m_v3Position.y,pInstance->m_v3Position.z),pInstance->GetRadiusApproximation())!=VS_OUTSIDE;
		}

		DWORD GetEmissionCount() const;

	protected:
		void OnInitialize();
		void OnDestroy();

		bool OnUpdate(float fElapsedTime);
		void OnRender();

	protected:
		float m_fEmissionResidue;

		DWORD m_dwCurrentEmissionCount;
		int	m_iLoopCount;

		typedef std::list<CParticleInstance*> TParticleInstanceList;
		typedef std::vector<TParticleInstanceList> TParticleInstanceListVector;
		TParticleInstanceListVector m_ParticleInstanceListVector;

		typedef std::vector<CGraphicImageInstance*> TImageInstanceVector;
		TImageInstanceVector m_kVct_pkImgInst;

		CParticleSystemData * m_pData;

		CParticleProperty * m_pParticleProperty;
		CEmitterProperty * m_pEmitterProperty;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
