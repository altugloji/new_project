#include "StdAfx.h"
#include "InstanceBase.h"
#include "PythonBackground.h"

void CInstanceBase::SCRIPT_SetPixelPosition(float fx, float fy)
{
	const float fCurrentZ = M_GTI.NEW_GetCurPixelPositionRef().z;
	const float fz = CPythonBackground::Instance().ResolveHeightForPlacement(fx, fy, fCurrentZ);
	NEW_SetPixelPosition(TPixelPosition(fx, fy, fz));
}

void CInstanceBase::NEW_SetPixelPosition(const TPixelPosition & c_rPixelPosition)
{
	M_GTI.SetCurPixelPosition(c_rPixelPosition);
}

void CInstanceBase::NEW_GetPixelPosition(TPixelPosition * pPixelPosition)
{
	*pPixelPosition=M_GTI.NEW_GetCurPixelPositionRef();
}

void CInstanceBase::SetRotation(float fRotation)
{
	M_GTI.SetRotation(fRotation);
}

void CInstanceBase::BlendRotation(float fRotation, float fBlendTime)
{
	M_GTI.BlendRotation(fRotation, fBlendTime);
}

void CInstanceBase::NEW_LookAtFlyTarget()
{
	M_GTI.LookAtFlyTarget();
}

void CInstanceBase::NEW_LookAtDestPixelPosition(const TPixelPosition& c_rkPPosDst)
{
	M_GTI.LookAt(c_rkPPosDst.x, -c_rkPPosDst.y);
}

void CInstanceBase::NEW_LookAtDestInstance(CInstanceBase& rkInstDst)
{
	M_GTI.LookAt(rkInstDst.GetGraphicThingInstancePtr());
// 	Tracenf("LookAt %f", M_GTI.GetTargetRotation());
}

float CInstanceBase::GetRotation()
{
	return M_GTI.GetRotation();
}

float CInstanceBase::GetAdvancingRotation()
{
	return M_GTI.GetAdvancingRotation();
}

void CInstanceBase::SetDirection(int dir)
{
	const float fDegree = GetDegreeFromDirection(dir);
	SetRotation(fDegree);
	SetAdvancingRotation(fDegree);
}

void CInstanceBase::BlendDirection(int dir, float blendTime)
{
	M_GTI.BlendRotation(GetDegreeFromDirection(dir), blendTime);
}

float CInstanceBase::GetDegreeFromDirection(int dir) const
{
	if (dir < 0)
		return 0.0f;

	if (dir >= DIR_MAX_NUM)
		return 0.0f;

	static float s_dirRot[DIR_MAX_NUM]=
	{
		+45.0f * 4,
		+45.0f * 3,
		+45.0f * 2,
		+45.0f,
		+0.0f,
		360.0f-45.0f,
		360.0f-45.0f * 2,
		360.0f-45.0f * 3,
	};

	return s_dirRot[dir];
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
