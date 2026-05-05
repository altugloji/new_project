#pragma once

#include "../eterLib/TextFileLoader.h"

#include "EffectElementBase.h"
#include "EmitterProperty.h"
#include "ParticleProperty.h"
//#include "ParticleInstance.h"

class CParticleInstance;

class CParticleSystemData : public CEffectElementBase
{
	public:
		virtual ~CParticleSystemData();
		CParticleSystemData();

		CEmitterProperty * GetEmitterPropertyPointer();
		CParticleProperty * GetParticlePropertyPointer();

		void ChangeTexture(const char * c_szFileName);

		void BuildDecorator(CParticleInstance * pInstance);
	protected:
		BOOL OnLoadScript(CTextFileLoader & rTextFileLoader);

		void OnClear();
		bool OnIsData();

		CEmitterProperty m_EmitterProperty;
		CParticleProperty m_ParticleProperty;

	public:
		static void DestroySystem();

		static CParticleSystemData* New();
		static void Delete(CParticleSystemData* pkData);

		static CDynamicPool<CParticleSystemData>		ms_kPool;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
