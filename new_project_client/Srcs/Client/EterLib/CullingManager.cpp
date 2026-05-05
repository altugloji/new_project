#include "StdAfx.h"
#include "CullingManager.h"
#include "GrpObjectInstance.h"
#include "../eterBase/Timer.h"

void CCullingManager::RayTraceCallback(const Vector3d &/*p1*/,          // source pos of ray
							  const Vector3d &/*dir*/,          // dest pos of ray
							  float distance,
							  const Vector3d &/*sect*/,
							  SpherePack *sphere)
{
	//if (state!=VS_OUTSIDE)
	//{
	if (m_RayFarDistance<=0.0f || m_RayFarDistance>=distance)
	{
		m_list.push_back((CGraphicObjectInstance *)sphere->GetUserData());
	}
		//f((CGraphicObjectInstance *)sphere->GetUserData());
	//}
}

void CCullingManager::VisibilityCallback(const Frustum &/*f*/,SpherePack *sphere,ViewState state)
{
	auto pInstance = (CGraphicObjectInstance*)sphere->GetUserData();
	/*if (state == VS_PARTIAL)
	{
		Vector3d v;
		float r;
		pInstance->GetBoundingSphere(v,r);
		state = f.ViewVolumeTest(v,r);
	}*/
	if (state == VS_OUTSIDE)
	{
		pInstance->Hide();
	}
	else
	{
		pInstance->Show();
	}
}

void CCullingManager::RangeTestCallback(const Vector3d &/*p*/,float /*distance*/,SpherePack *sphere,ViewState state)
{
	if (state!=VS_OUTSIDE)
	{
		m_list.push_back((CGraphicObjectInstance *)sphere->GetUserData());
		//f((CGraphicObjectInstance *)sphere->GetUserData());
	}
	//assert(false && "NOT REACHED");
}

void CCullingManager::Reset() const
{
	m_Factory->Reset();
	m_dwLastUpdateFrameStamp = static_cast<DWORD>(-1);
}

void CCullingManager::Update() const
{
	const DWORD dwFrameStamp = ELTimer_GetFrameMSec();

	if (m_dwLastUpdateFrameStamp == dwFrameStamp)
		return;

	m_dwLastUpdateFrameStamp = dwFrameStamp;
	m_Factory->Process();
}

void CCullingManager::Process()
{
	//DWORD time = ELTimer_GetMSec();
	//Frustum f;
	UpdateViewMatrix();
	UpdateProjMatrix();
	BuildViewFrustum();
	m_Factory->FrustumTest(GetFrustum(), this);
	//Tracef("cull process : %3d  ",ELTimer_GetMSec()-time);
}

CCullingManager::CullingHandle CCullingManager::Register(CGraphicObjectInstance * obj) const
{
	assert(obj);
	Vector3d center;
	float radius;
	obj->GetBoundingSphere(center,radius);
	return m_Factory->AddSphere_(center,radius,obj, false);
}

void CCullingManager::Unregister(CullingHandle h) const
{
	m_Factory->Remove(h);
}

CCullingManager::CCullingManager()
{
	m_Factory = new SpherePackFactory(
		10000,	// maximum count
		6400,	// root radius
		1600,	// leaf radius
		400		// extra radius
		);
	m_dwLastUpdateFrameStamp = static_cast<DWORD>(-1);
}

CCullingManager::~CCullingManager()
{
	delete m_Factory;
}

void CCullingManager::FindRange(const Vector3d &p, float radius)
{
	m_list.clear();
	m_Factory->RangeTest(p, radius, this);
}

void CCullingManager::FindRay(const Vector3d &p1, const Vector3d &dir)
{
	m_RayFarDistance = -1;
	m_list.clear();
	m_Factory->RayTrace(p1,dir,this);
}

void CCullingManager::FindRayDistance(const Vector3d &p1, const Vector3d &dir, float distance)
{
	m_RayFarDistance = distance;
	m_list.clear();
	m_Factory->RayTrace(p1,dir,this);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
