#include "StdAfx.h"
#include "InstanceBase.h"
#include "PythonBackground.h"
#include "PythonCharacterManager.h"
#include "../PRTerrainLib/Terrain.h"

float NEW_UnsignedDegreeToSignedDegree(float fUD)
{
	float fSD;
	if (fUD>180.0f)
		fSD=-(360.0f-fUD);
	else if (fUD<-180.0f)
		fSD=+(360.0f+fUD);
	else
		fSD=fUD;

	return fSD;
}

float NEW_GetSignedDegreeFromDirPixelPosition(const TPixelPosition& kPPosDir)
{
	D3DXVECTOR3 vtDir(kPPosDir.x, -kPPosDir.y, kPPosDir.z);
	D3DXVECTOR3 vtDirNormal;
	D3DXVec3Normalize(&vtDirNormal, &vtDir);

	const D3DXVECTOR3 vtDirNormalStan(0, -1, 0);
	float dotProduct = D3DXVec3Dot(&vtDirNormal, &vtDirNormalStan);
	if (dotProduct > 1.0f)
		dotProduct = 1.0f;
	else if (dotProduct < -1.0f)
		dotProduct = -1.0f;

	float fDirRot = D3DXToDegree(acosf(dotProduct));

	if (vtDirNormal.x<0.0f)
		fDirRot=-fDirRot;

	return fDirRot;
}

bool CInstanceBase::IsFlyTargetObject()
{
	return M_GTI.IsFlyTargetObject();
}

float CInstanceBase::GetFlyTargetDistance()
{
	return M_GTI.GetFlyTargetDistance();
}

void CInstanceBase::ClearFlyTargetInstance()
{
	M_GTI.ClearFlyTarget();
}

void CInstanceBase::SetFlyTargetInstance(CInstanceBase& rkInstDst)
{
//	if (isLock())
//		return;

	M_GTI.SetFlyTarget(rkInstDst.GetGraphicThingInstancePtr());
}

void CInstanceBase::AddFlyTargetPosition(const TPixelPosition& c_rkPPosDst)
{
	M_GTI.AddFlyTarget(c_rkPPosDst);
}

void CInstanceBase::AddFlyTargetInstance(CInstanceBase& rkInstDst)
{
	M_GTI.AddFlyTarget(rkInstDst.GetGraphicThingInstancePtr());
}

float CInstanceBase::NEW_GetDistanceFromDestInstance(CInstanceBase& rkInstDst)
{
	TPixelPosition kPPosDst;
	rkInstDst.NEW_GetPixelPosition(&kPPosDst);

	return NEW_GetDistanceFromDestPixelPosition(kPPosDst);
}

float CInstanceBase::NEW_GetDistanceFromDestPixelPosition(const TPixelPosition& c_rkPPosDst)
{
	TPixelPosition kPPosCur;
	NEW_GetPixelPosition(&kPPosCur);

	TPixelPosition kPPosDir;
	kPPosDir=c_rkPPosDst-kPPosCur;

	return NEW_GetDistanceFromDirPixelPosition(kPPosDir);
}

float CInstanceBase::NEW_GetDistanceFromDirPixelPosition(const TPixelPosition& c_rkPPosDir) const
{
	return sqrtf(c_rkPPosDir.x*c_rkPPosDir.x+c_rkPPosDir.y*c_rkPPosDir.y);
}

float CInstanceBase::NEW_GetRotation()
{
	const float fCurRot=GetRotation();
	return NEW_UnsignedDegreeToSignedDegree(fCurRot);
}

float CInstanceBase::NEW_GetRotationFromDirPixelPosition(const TPixelPosition& c_rkPPosDir) const
{
	return NEW_GetSignedDegreeFromDirPixelPosition(c_rkPPosDir);
}

float CInstanceBase::NEW_GetRotationFromDestPixelPosition(const TPixelPosition& c_rkPPosDst)
{
	TPixelPosition kPPosCur;
	NEW_GetPixelPosition(&kPPosCur);

	TPixelPosition kPPosDir;
	kPPosDir=c_rkPPosDst-kPPosCur;

	return NEW_GetRotationFromDirPixelPosition(kPPosDir);
}

float CInstanceBase::NEW_GetRotationFromDestInstance(CInstanceBase& rkInstDst)
{
	TPixelPosition kPPosDst;
	rkInstDst.NEW_GetPixelPosition(&kPPosDst);

	return NEW_GetRotationFromDestPixelPosition(kPPosDst);
}

void CInstanceBase::NEW_GetRandomPositionInFanRange(CInstanceBase& rkInstTarget, TPixelPosition* pkPPosDst)
{
	const float fDstDirRot=NEW_GetRotationFromDestInstance(rkInstTarget);

	const float fRot=frandom(fDstDirRot-10.0f, fDstDirRot+10.0f);

	D3DXMATRIX kMatRot;
	D3DXMatrixRotationZ(&kMatRot, D3DXToRadian(-fRot));

	const D3DXVECTOR3 v3Src(0.0f, 8000.0f, 0.0f);
	D3DXVECTOR3 v3Pos;
	D3DXVec3TransformCoord(&v3Pos, &v3Src, &kMatRot);

	const TPixelPosition& c_rkPPosCur=NEW_GetCurPixelPositionRef();
	//const TPixelPosition& c_rkPPosFront=rkInstTarget.NEW_GetCurPixelPositionRef();

	pkPPosDst->x=c_rkPPosCur.x+v3Pos.x;
	pkPPosDst->y=c_rkPPosCur.y+v3Pos.y;
	pkPPosDst->z=__GetBackgroundHeight(c_rkPPosCur.x, c_rkPPosCur.y);
}

bool CInstanceBase::NEW_GetFrontInstance(CInstanceBase ** ppoutTargetInstance, float fDistance)
{
	constexpr float HALF_FAN_ROT_MIN = 10.0f;
	constexpr float HALF_FAN_ROT_MAX = 50.0f;
	constexpr float HALF_FAN_ROT_MIN_DISTANCE = 1000.0f;
	constexpr float RPM = (HALF_FAN_ROT_MAX-HALF_FAN_ROT_MIN)/HALF_FAN_ROT_MIN_DISTANCE;

	const float fDstRot=NEW_GetRotation();

	std::multimap<float, CInstanceBase*> kMap_pkInstNear;
	{
		CPythonCharacterManager& rkChrMgr=CPythonCharacterManager::Instance();
		CPythonCharacterManager::CharacterIterator i;
		for(i = rkChrMgr.CharacterInstanceBegin(); i!=rkChrMgr.CharacterInstanceEnd(); ++i)
		{
			CInstanceBase* pkInstEach=*i;
			if (pkInstEach==this)
				continue;

			if (!IsAttackableInstance(*pkInstEach))
				continue;

			if (NEW_GetDistanceFromDestInstance(*pkInstEach) > fDistance)
				continue;

			float fEachInstDistance=min(NEW_GetDistanceFromDestInstance(*pkInstEach), HALF_FAN_ROT_MIN_DISTANCE);
			const float fEachInstDirRot=NEW_GetRotationFromDestInstance(*pkInstEach);

			const float fHalfFanRot=(HALF_FAN_ROT_MAX-HALF_FAN_ROT_MIN)-RPM*fEachInstDistance+HALF_FAN_ROT_MIN;

			const float fMinDstDirRot=fDstRot-fHalfFanRot;
			const float fMaxDstDirRot=fDstRot+fHalfFanRot;

			if (fEachInstDirRot>=fMinDstDirRot && fEachInstDirRot<=fMaxDstDirRot)
				kMap_pkInstNear.insert(std::multimap<float, CInstanceBase*>::value_type(fEachInstDistance, pkInstEach));
		}
	}

	if (kMap_pkInstNear.empty())
		return false;

	*ppoutTargetInstance = kMap_pkInstNear.begin()->second;

	return true;
}

bool CInstanceBase::NEW_GetInstanceVectorInFanRange(float fSkillDistance, CInstanceBase& rkInstTarget, std::vector<CInstanceBase*>* pkVct_pkInst)
{
	constexpr float HALF_FAN_ROT_MIN = 20.0f;
	constexpr float HALF_FAN_ROT_MAX = 40.0f;
	constexpr float HALF_FAN_ROT_MIN_DISTANCE = 1000.0f;
	constexpr float RPM = (HALF_FAN_ROT_MAX-HALF_FAN_ROT_MIN)/HALF_FAN_ROT_MIN_DISTANCE;

	const float fDstDirRot=NEW_GetRotationFromDestInstance(rkInstTarget);

	std::multimap<float, CInstanceBase*> kMap_pkInstNear;
	{
		CPythonCharacterManager& rkChrMgr=CPythonCharacterManager::Instance();
		CPythonCharacterManager::CharacterIterator i;
		for(i = rkChrMgr.CharacterInstanceBegin(); i!=rkChrMgr.CharacterInstanceEnd(); ++i)
		{
			CInstanceBase* pkInstEach=*i;
			if (pkInstEach==this)
				continue;

			if (!IsAttackableInstance(*pkInstEach))
				continue;

			if (M_GTI.IsClickableDistanceDestInstance(pkInstEach->GetGraphicThingInstanceRef(), fSkillDistance))
			{
				float fEachInstDistance=min(NEW_GetDistanceFromDestInstance(*pkInstEach), HALF_FAN_ROT_MIN_DISTANCE);
				const float fEachInstDirRot=NEW_GetRotationFromDestInstance(*pkInstEach);

				const float fHalfFanRot=(HALF_FAN_ROT_MAX-HALF_FAN_ROT_MIN)-RPM*fEachInstDistance+HALF_FAN_ROT_MIN;

				const float fMinDstDirRot=fDstDirRot-fHalfFanRot;
				const float fMaxDstDirRot=fDstDirRot+fHalfFanRot;

				if (fEachInstDirRot>=fMinDstDirRot && fEachInstDirRot<=fMaxDstDirRot)
					kMap_pkInstNear.insert(std::multimap<float, CInstanceBase*>::value_type(fEachInstDistance, pkInstEach));
			}
		}
	}

	{
		auto i=kMap_pkInstNear.begin();
		for (i=kMap_pkInstNear.begin(); i!=kMap_pkInstNear.end(); ++i)
			pkVct_pkInst->push_back(i->second);
	}

	if (pkVct_pkInst->empty())
		return false;

	return true;
}

bool CInstanceBase::NEW_GetInstanceVectorInCircleRange(float fSkillDistance, std::vector<CInstanceBase*>* pkVct_pkInst)
{
	std::multimap<float, CInstanceBase*> kMap_pkInstNear;

	{
		CPythonCharacterManager& rkChrMgr=CPythonCharacterManager::Instance();
		CPythonCharacterManager::CharacterIterator i;
		for(i = rkChrMgr.CharacterInstanceBegin(); i!=rkChrMgr.CharacterInstanceEnd(); ++i)
		{
			CInstanceBase* pkInstEach=*i;

			if (pkInstEach==this)
				continue;

			if (!IsAttackableInstance(*pkInstEach))
				continue;

			if (M_GTI.IsClickableDistanceDestInstance(pkInstEach->GetGraphicThingInstanceRef(), fSkillDistance))
			{
				float fEachInstDistance=NEW_GetDistanceFromDestInstance(*pkInstEach);
				kMap_pkInstNear.emplace(fEachInstDistance, pkInstEach);
			}
		}
	}

	{
		auto i=kMap_pkInstNear.begin();
		for (i=kMap_pkInstNear.begin(); i!=kMap_pkInstNear.end(); ++i)
			pkVct_pkInst->push_back(i->second);
	}

	if (pkVct_pkInst->empty())
		return false;

	return true;
}

BOOL CInstanceBase::NEW_IsClickableDistanceDestPixelPosition(const TPixelPosition& c_rkPPosDst)
{
	const float fDistance=NEW_GetDistanceFromDestPixelPosition(c_rkPPosDst);

	if (fDistance>150.0f)
		return FALSE;

	return TRUE;
}

BOOL CInstanceBase::NEW_IsClickableDistanceDestInstance(CInstanceBase& rkInstDst)
{
	float fDistance = 150.0f;

	if (IsBowMode())
		fDistance = __GetBowRange();

	if (rkInstDst.IsNPC())
		fDistance = 500.0f;

	if (rkInstDst.IsResource())
		fDistance = 100.0f;

	return M_GTI.IsClickableDistanceDestInstance(rkInstDst.GetGraphicThingInstanceRef(), fDistance);
}

bool CInstanceBase::NEW_UseSkill(UINT uSkill, UINT uMot, UINT uMotLoopCount, bool isMovingSkill)
{
	if (IsDead())
		return false;

	if (IsStun())
		return false;

	if (IsKnockDown())
		return false;

	if (isMovingSkill)
	{
		if (!IsWalking())
			StartWalking();

		m_isGoing = TRUE;
	}
	else
	{
		if (IsWalking())
			EndWalking();

		m_isGoing = FALSE;
	}

	const float fCurRot=M_GTI.GetTargetRotation();
	SetAdvancingRotation(fCurRot);

	M_GTI.InterceptOnceMotion(CRaceMotionData::NAME_SKILL + uMot, 0.1f, uSkill, 1.0f);

	M_GTI.__OnUseSkill(uMot, uMotLoopCount, isMovingSkill);

	if (uMotLoopCount > 0)
		M_GTI.SetMotionLoopCount(uMotLoopCount);

	return true;
}

void CInstanceBase::NEW_Attack()
{
	const float fDirRot=GetRotation();
	NEW_Attack(fDirRot);
}

void CInstanceBase::NEW_Attack(float fDirRot)
{
	if (IsDead())
		return;

	if (IsStun())
		return;

	if (IsKnockDown())
		return;

	if (IsUsingSkill())
		return;

	if (IsWalking())
		EndWalking();

	m_isGoing = FALSE;

	if (IsPoly())
	{
		InputNormalAttack(fDirRot);
	}
	else
	{
		if (m_kHorse.IsMounting())
		{
			InputComboAttack(fDirRot);
		}
		else
		{
			InputComboAttack(fDirRot);
		}
	}
}

void CInstanceBase::NEW_AttackToDestPixelPositionDirection(const TPixelPosition& c_rkPPosDst)
{
	const float fDirRot=NEW_GetRotationFromDestPixelPosition(c_rkPPosDst);

	NEW_Attack(fDirRot);
}

bool CInstanceBase::NEW_AttackToDestInstanceDirection(CInstanceBase& rkInstDst, IFlyEventHandler* pkFlyHandler)
{
	return NEW_AttackToDestInstanceDirection(rkInstDst);
}

bool CInstanceBase::NEW_AttackToDestInstanceDirection(CInstanceBase& rkInstDst)
{
	TPixelPosition kPPosDst;
	rkInstDst.NEW_GetPixelPosition(&kPPosDst);
	NEW_AttackToDestPixelPositionDirection(kPPosDst);

	return true;
}

void CInstanceBase::AttackProcess()
{
	if (!M_GTI.CanCheckAttacking())
		return;

	CInstanceBase * pkInstLast = nullptr;
	CPythonCharacterManager& rkChrMgr = CPythonCharacterManager::Instance();
	CPythonCharacterManager::CharacterIterator i = rkChrMgr.CharacterInstanceBegin();
	while (rkChrMgr.CharacterInstanceEnd()!=i)
	{
		CInstanceBase* pkInstEach=*i;
		++i;

		if (!IsAttackableInstance(*pkInstEach))
			continue;

		if (pkInstEach!=this)
		{
			if (CheckAttacking(*pkInstEach))
			{
				pkInstLast=pkInstEach;
			}
		}
	}

	if (pkInstLast)
	{
		m_dwLastDmgActorVID=pkInstLast->GetVirtualID();
	}
}

void CInstanceBase::InputNormalAttack(float fAtkDirRot)
{
	M_GTI.InputNormalAttackCommand(fAtkDirRot);
}

void CInstanceBase::InputComboAttack(float fAtkDirRot)
{
	M_GTI.InputComboAttackCommand(fAtkDirRot);
	__ComboProcess();
}

void CInstanceBase::RunNormalAttack(float fAtkDirRot)
{
	EndGoing();
	M_GTI.NormalAttack(fAtkDirRot);
}

void CInstanceBase::RunComboAttack(float fAtkDirRot, DWORD wMotionIndex)
{
	EndGoing();
	M_GTI.ComboAttack(wMotionIndex, fAtkDirRot);
}

BOOL CInstanceBase::CheckAdvancing()
{
#ifdef __MOVIE_MODE__
	if (IsMovieMode())
		return FALSE;
#endif
	if (!__IsMainInstance() && !IsAttacking())
	{
		if (IsPC() && IsWalking())
		{
			CPythonCharacterManager& rkChrMgr=CPythonCharacterManager::Instance();
			for(CPythonCharacterManager::CharacterIterator i = rkChrMgr.CharacterInstanceBegin(); i!=rkChrMgr.CharacterInstanceEnd();++i)
			{
				CInstanceBase* pkInstEach=*i;
				if (pkInstEach==this)
					continue;
				if (!pkInstEach->IsDoor())
					continue;

				if (M_GTI.TestActorCollision(pkInstEach->GetGraphicThingInstanceRef()))
				{
					BlockMovement();
					return true;
				}
			}
		}
		return FALSE;
	}

	if (M_GTI.CanSkipCollision())
	{
		return FALSE;
	}

	const BOOL bUsingSkill = M_GTI.IsUsingSkill();

	m_dwAdvActorVID = 0;
	UINT uCollisionCount=0;

	CPythonCharacterManager& rkChrMgr=CPythonCharacterManager::Instance();
	for(CPythonCharacterManager::CharacterIterator i = rkChrMgr.CharacterInstanceBegin(); i!=rkChrMgr.CharacterInstanceEnd();++i)
	{
		CInstanceBase* pkInstEach=*i;
		if (pkInstEach==this)
			continue;

		CActorInstance& rkActorSelf=M_GTI;
		CActorInstance& rkActorEach=pkInstEach->GetGraphicThingInstanceRef();

		if( bUsingSkill && !rkActorEach.IsDoor() )
			continue;

		if (rkActorSelf.TestActorCollision(rkActorEach))
		{
			uCollisionCount++;
			if (uCollisionCount==2)
			{
				rkActorSelf.BlockMovement();
				return TRUE;
			}
			rkActorSelf.AdjustDynamicCollisionMovement(&rkActorEach);

			if (rkActorSelf.TestActorCollision(rkActorEach))
			{
				rkActorSelf.BlockMovement();
				return TRUE;
			}
			else
			{
				NEW_MoveToDestPixelPositionDirection(NEW_GetDstPixelPositionRef());
			}
		}
	}

	CPythonBackground& rkBG=CPythonBackground::Instance();
	const D3DXVECTOR3 & rv3Position = M_GTI.GetPosition();
	const D3DXVECTOR3 & rv3MoveDirection = M_GTI.GetMovementVectorRef();

	const int iStep = int(D3DXVec3Length(&rv3MoveDirection) / 10.0f);
	const D3DXVECTOR3 v3CheckStep = rv3MoveDirection / float(iStep);
	D3DXVECTOR3 v3CheckPosition = rv3Position;
	for (int j = 0; j < iStep; ++j)
	{
		v3CheckPosition += v3CheckStep;

		// Check
		if (rkBG.isAttrOn(v3CheckPosition.x, -v3CheckPosition.y, CTerrainImpl::ATTRIBUTE_BLOCK))
		{
			BlockMovement();
			//return TRUE;
		}
	}

	// Check
	const D3DXVECTOR3 v3NextPosition = rv3Position + rv3MoveDirection;
	if (rkBG.isAttrOn(v3NextPosition.x, -v3NextPosition.y, CTerrainImpl::ATTRIBUTE_BLOCK))
	{
		BlockMovement();
		return TRUE;
	}

	return FALSE;
}

BOOL CInstanceBase::CheckAttacking(CInstanceBase& rkInstVictim)
{
	if (IsInSafe())
		return FALSE;

	if (rkInstVictim.IsInSafe())
		return FALSE;

#ifdef __MOVIE_MODE__
	return FALSE;
#endif

	if (!M_GTI.AttackingProcess(rkInstVictim.GetGraphicThingInstanceRef()))
		return FALSE;

	return TRUE;
}

BOOL CInstanceBase::isNormalAttacking()
{
	return M_GTI.isNormalAttacking();
}

BOOL CInstanceBase::isComboAttacking()
{
	return M_GTI.isComboAttacking();
}

BOOL CInstanceBase::IsUsingSkill()
{
	return M_GTI.IsUsingSkill();
}

BOOL CInstanceBase::IsUsingMovingSkill()
{
	return M_GTI.IsUsingMovingSkill();
}

BOOL CInstanceBase::CanCancelSkill()
{
	return M_GTI.CanCancelSkill();
}

BOOL CInstanceBase::CanAttackHorseLevel() const
{
	if (!IsMountingHorse())
		return FALSE;

	return m_kHorse.CanAttack();
}

bool CInstanceBase::IsAffect(UINT uAffect) const
{
	return m_kAffectFlagContainer.IsSet(uAffect);
}

MOTION_KEY CInstanceBase::GetNormalAttackIndex()
{
	return M_GTI.GetNormalAttackIndex();
}

DWORD CInstanceBase::GetComboIndex()
{
	return M_GTI.GetComboIndex();
}

float CInstanceBase::GetAttackingElapsedTime()
{
	return M_GTI.GetAttackingElapsedTime();
}

void CInstanceBase::ProcessHitting(DWORD dwMotionKey, CInstanceBase * pVictimInstance) const
{
	assert(!"-_-" && "CInstanceBase::ProcessHitting");
	//M_GTI.ProcessSucceedingAttacking(dwMotionKey, pVictimInstance->m_GraphicThingInstance);
}

void CInstanceBase::ProcessHitting(DWORD dwMotionKey, BYTE byEventIndex, CInstanceBase * pVictimInstance) const
{
	assert(!"-_-" && "CInstanceBase::ProcessHitting");
	//M_GTI.ProcessSucceedingAttacking(dwMotionKey, byEventIndex, pVictimInstance->m_GraphicThingInstance);
}

void CInstanceBase::GetBlendingPosition(TPixelPosition * pPixelPosition)
{
	M_GTI.GetBlendingPosition(pPixelPosition);
}

void CInstanceBase::SetBlendingPosition(const TPixelPosition & c_rPixelPosition)
{
	M_GTI.SetBlendingPosition(c_rPixelPosition);
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////

void CInstanceBase::Revive()
{
	m_isGoing=FALSE;
	M_GTI.Revive();

	__AttachHorseSaddle();
}

void CInstanceBase::Stun()
{
	NEW_Stop();
	M_GTI.Stun();

	__AttachEffect(EFFECT_STUN);
}

void CInstanceBase::Die()
{
	__DetachHorseSaddle();

	// if (IsAffect(AFFECT_SPAWN))
		// __AttachEffect(EFFECT_SPAWN_DISAPPEAR);

	////////////////////////////////////////
	__ClearAffects();
	////////////////////////////////////////

	OnUnselected();
	OnUntargeted();

	M_GTI.Die();
}

void CInstanceBase::Hide()
{
	M_GTI.SetAlphaValue(0.0f);
	M_GTI.BlendAlphaValue(0.0f, 0.1f);
}

void CInstanceBase::Show()
{
	M_GTI.SetAlphaValue(1.0f);
	M_GTI.BlendAlphaValue(1.0f, 0.1f);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
