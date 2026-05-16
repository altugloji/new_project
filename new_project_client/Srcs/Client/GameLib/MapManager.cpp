#include "StdAfx.h"
#include "../eterLib/StateManager.h"
#include "../EterPack/EterPackManager.h"

#include "MapManager.h"
#include "MapOutdoor.h"

#include "PropertyLoader.h"

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////

bool CMapManager::IsMapOutdoor() const
{
	if (m_pkMap)
		return true;

	return false;
}

CMapOutdoor& CMapManager::GetMapOutdoorRef() const
{
	assert(nullptr!=m_pkMap);
	return *m_pkMap;
}

CMapManager::CMapManager() : mc_pcurEnvironmentData(nullptr)
{
	m_pkMap = nullptr;
	m_isSoftwareTilingEnableReserved=false;
#ifdef __BL_FOG_FIX__
	m_isFogModeEnabled = false;
#endif

//	Initialize();
}

#ifdef __BL_FOG_FIX__
void CMapManager::SetFogMode(bool bEnable)
{
	m_isFogModeEnabled = bEnable;
}

bool CMapManager::GetFogMode() const
{
	return m_isFogModeEnabled;
}
#endif

CMapManager::~CMapManager()
{
	Destroy();
}

bool CMapManager::IsSoftwareTilingEnable() const
{
	return CTerrainPatch::SOFTWARE_TRANSFORM_PATCH_ENABLE;
}

void CMapManager::ReserveSoftwareTilingEnable(bool isEnable)
{
	m_isSoftwareTilingEnableReserved=isEnable;
}

void CMapManager::Initialize()
{
	mc_pcurEnvironmentData = nullptr;
	__LoadMapInfoVector();
}

void CMapManager::Create()
{
	assert(nullptr==m_pkMap && "CMapManager::Create");
	if (m_pkMap)
	{
		Clear();
		return;
	}

	CTerrainPatch::SOFTWARE_TRANSFORM_PATCH_ENABLE=m_isSoftwareTilingEnableReserved;

	m_pkMap = (CMapOutdoor*)AllocMap();

	assert(nullptr!=m_pkMap && "CMapManager::Create MAP is nullptr");
}

void CMapManager::Destroy()
{
	stl_wipe_second(m_EnvironmentDataMap);

	if (m_pkMap)
	{
		m_pkMap->Clear();
		delete m_pkMap;
		m_pkMap = nullptr;
	}
}

void CMapManager::Clear()
{
	if (m_pkMap)
		m_pkMap->Clear();
}

CMapBase * CMapManager::AllocMap()
{
	return new CMapOutdoor;
}

//////////////////////////////////////////////////////////////////////////
// Map
//////////////////////////////////////////////////////////////////////////
void CMapManager::LoadProperty()
{
	CPropertyLoader PropertyLoader;
	PropertyLoader.SetPropertyManager(&m_PropertyManager);
	PropertyLoader.Create("*.*", "Property");
}

bool CMapManager::LoadMap(const std::string & c_rstrMapName, float x, float y, float z)
{
	CMapOutdoor& rkMap = GetMapOutdoorRef();

	rkMap.Leave();
	rkMap.SetName(c_rstrMapName);
	rkMap.LoadProperty();

	if ( CMapBase::MAPTYPE_INDOOR == rkMap.GetType())
	{
		TraceError("CMapManager::LoadMap() Indoor Map Load Failed");
		return false;
	}
	else if (CMapBase::MAPTYPE_OUTDOOR == rkMap.GetType())
	{
		if (!rkMap.Load(x, y, z))
		{
			TraceError("CMapManager::LoadMap() Outdoor Map Load Failed");
			return false;
		}

		RegisterEnvironmentData(0, rkMap.GetEnvironmentDataName().c_str());

		SetEnvironmentData(0);
	}
	else
	{
		TraceError("CMapManager::LoadMap() Invalid Map Type");
		return false;
	}

	rkMap.Enter();
	return true;
}

bool CMapManager::IsMapReady() const
{
	if (!m_pkMap)
		return false;

	return m_pkMap->IsReady();
}

bool CMapManager::UnloadMap(const std::string c_strMapName)
{
	const CMapOutdoor& rkMap=GetMapOutdoorRef();
	if (c_strMapName != rkMap.GetName() && "" != rkMap.GetName())
	{
		LogBoxf("%s: Unload Map Failed", c_strMapName.c_str());
		return false;
	}

	Clear();
	return true;
}

bool CMapManager::UpdateMap(float fx, float fy, float fz) const
{
	if (!m_pkMap)
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.Update(fx, -fy, fz);
}

void CMapManager::UpdateAroundAmbience(float fx, float fy, float fz) const
{
	if (!m_pkMap)
		return;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	rkMap.UpdateAroundAmbience(fx, -fy, fz);
}

float CMapManager::GetHeight(float fx, float fy) const
{
	if (!m_pkMap)
	{
		TraceError("CMapManager::GetHeight(%f, %f) - Accessing in a not initialized map", fx, fy);
		return 0.0f;
	}
	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetHeight(fx, fy);
}

float CMapManager::GetTerrainHeight(float fx, float fy) const
{
	if (!m_pkMap)
	{
		TraceError("CMapManager::GetTerrainHeight(%f, %f) - Accessing in a not initialized map", fx, fy);
		return 0.0f;
	}
	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetTerrainHeight(fx, fy);
}

bool CMapManager::GetWaterHeight(int iX, int iY, long * plWaterHeight) const
{
	if (!m_pkMap)
	{
		TraceError("CMapManager::GetTerrainHeight(%f, %f) - Accessing in a not initialized map", iX, iY);
		return false;
	}

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetWaterHeight(iX, iY, plWaterHeight);
}

//////////////////////////////////////////////////////////////////////////
// Environment
//////////////////////////////////////////////////////////////////////////
void CMapManager::BeginEnvironment()
{
	if (!m_pkMap)
		return;

	if (!mc_pcurEnvironmentData)
		return;

	CMapOutdoor& rkMap=GetMapOutdoorRef();

	// Light always on
 	STATEMANAGER.SaveRenderState(D3DRS_LIGHTING, TRUE);

	// Fog
#ifdef __BL_FOG_FIX__
	STATEMANAGER.SaveRenderState(D3DRS_FOGENABLE, m_isFogModeEnabled ? mc_pcurEnvironmentData->bFogEnable : 0);
#else
 	STATEMANAGER.SaveRenderState(D3DRS_FOGENABLE, mc_pcurEnvironmentData->bFogEnable);
#endif

	// Material
	STATEMANAGER.SetMaterial(&mc_pcurEnvironmentData->Material);

	// Directional Light
	if (mc_pcurEnvironmentData->bDirLightsEnable[ENV_DIRLIGHT_BACKGROUND])
	{
		ms_lpd3dDevice->LightEnable(0, TRUE);

		rkMap.ApplyLight((DWORD)mc_pcurEnvironmentData, mc_pcurEnvironmentData->DirLights[ENV_DIRLIGHT_BACKGROUND]);
	}
	else
		ms_lpd3dDevice->LightEnable(0, FALSE);

	if (mc_pcurEnvironmentData->bFogEnable)
	{
		const DWORD dwFogColor = mc_pcurEnvironmentData->FogColor;
		STATEMANAGER.SetRenderState(D3DRS_FOGCOLOR, dwFogColor);

		if (mc_pcurEnvironmentData->bDensityFog)
		{
			float fDensity = 0.00015f;
			STATEMANAGER.SetRenderState(D3DRS_FOGVERTEXMODE, D3DFOG_EXP);					// pixel fog
			STATEMANAGER.SetRenderState(D3DRS_FOGDENSITY, *((DWORD *) &fDensity));			// vertex fog
		}
		else
		{
			CSpeedTreeForest& rkForest = CSpeedTreeForest::Instance();
			rkForest.SetFog(
				mc_pcurEnvironmentData->GetFogNearDistance(),
				mc_pcurEnvironmentData->GetFogFarDistance()
			);

			float fFogNear=mc_pcurEnvironmentData->GetFogNearDistance();
			float fFogFar=mc_pcurEnvironmentData->GetFogFarDistance();
			STATEMANAGER.SetRenderState(D3DRS_FOGVERTEXMODE, D3DFOG_LINEAR);								// vertex fox
			STATEMANAGER.SetRenderState(D3DRS_RANGEFOGENABLE, TRUE);											// vertex fox
			STATEMANAGER.SetRenderState(D3DRS_FOGSTART, *((DWORD *) &fFogNear));	// USED BY D3DFOG_LINEAR
			STATEMANAGER.SetRenderState(D3DRS_FOGEND, *((DWORD *) &fFogFar));		// USED BY D3DFOG_LINEAR
		}
	}

	rkMap.OnBeginEnvironment();
}

void CMapManager::EndEnvironment() const
{
	if (!mc_pcurEnvironmentData)
		return;

	STATEMANAGER.RestoreRenderState(D3DRS_LIGHTING);
	STATEMANAGER.RestoreRenderState(D3DRS_FOGENABLE);
}

void CMapManager::SetEnvironmentData(int nEnvDataIndex)
{
	const TEnvironmentData * c_pEnvironmenData;

	if (GetEnvironmentData(nEnvDataIndex, &c_pEnvironmenData))
		SetEnvironmentDataPtr(c_pEnvironmenData);
}

void CMapManager::SetEnvironmentDataPtr(const TEnvironmentData * c_pEnvironmentData)
{
	if (!m_pkMap)
		return;

	if (!c_pEnvironmentData)
	{
		assert(!"null environment data");
		TraceError("null environment data");
		return;
	}

	CMapOutdoor& rkMap=GetMapOutdoorRef();

	mc_pcurEnvironmentData = c_pEnvironmentData;

	rkMap.SetEnvironmentDataPtr(mc_pcurEnvironmentData);
}

void CMapManager::ResetEnvironmentDataPtr(const TEnvironmentData * c_pEnvironmentData)
{
	if (!m_pkMap)
		return;

	if (!c_pEnvironmentData)
	{
		assert(!"null environment data");
		TraceError("null environment data");
		return;
	}

	CMapOutdoor& rkMap=GetMapOutdoorRef();

	mc_pcurEnvironmentData = c_pEnvironmentData;
	rkMap.ResetEnvironmentDataPtr(mc_pcurEnvironmentData);
}

void CMapManager::BlendEnvironmentData(const TEnvironmentData * c_pEnvironmentData, int iTransitionTime) const
{
}

#ifdef ENABLE_NIGHT_MODE_OPTION
namespace
{
	float ClampBlend(float fBlend)
	{
		if (fBlend < 0.0f)
			return 0.0f;
		if (fBlend > 1.0f)
			return 1.0f;
		return fBlend;
	}

	float LerpFloat(float fStart, float fEnd, float fBlend)
	{
		return fStart + (fEnd - fStart) * fBlend;
	}

	void LerpColorValue(D3DCOLORVALUE& rkOut, const D3DCOLORVALUE& rkDay, const D3DCOLORVALUE& rkNight, float fBlend)
	{
		const D3DXCOLOR cDay(rkDay);
		const D3DXCOLOR cNight(rkNight);
		D3DXCOLOR cOut;
		D3DXColorLerp(&cOut, &cDay, &cNight, fBlend);
		rkOut = cOut;
	}

	void LerpLight(D3DLIGHT9& rkOut, const D3DLIGHT9& rkDay, const D3DLIGHT9& rkNight, float fBlend)
	{
		rkOut = rkDay;
		LerpColorValue(rkOut.Diffuse, rkDay.Diffuse, rkNight.Diffuse, fBlend);
		LerpColorValue(rkOut.Ambient, rkDay.Ambient, rkNight.Ambient, fBlend);
		LerpColorValue(rkOut.Specular, rkDay.Specular, rkNight.Specular, fBlend);
		rkOut.Direction.x = LerpFloat(rkDay.Direction.x, rkNight.Direction.x, fBlend);
		rkOut.Direction.y = LerpFloat(rkDay.Direction.y, rkNight.Direction.y, fBlend);
		rkOut.Direction.z = LerpFloat(rkDay.Direction.z, rkNight.Direction.z, fBlend);
		rkOut.Range = LerpFloat(rkDay.Range, rkNight.Range, fBlend);
	}
}

void CMapManager::SetNightModeBlend(float fBlend)
{
	if (!m_pkMap)
		return;

	const float fClampedBlend = ClampBlend(fBlend);

	const TEnvironmentData* pDay = nullptr;
	const TEnvironmentData* pNight = nullptr;
	const bool bHasDay = GetEnvironmentData(0, &pDay);
	const bool bHasNight = GetEnvironmentData(1, &pNight);

	if (!bHasDay && !bHasNight)
		return;

	if (fClampedBlend <= 0.0f)
	{
		if (bHasDay)
			SetEnvironmentDataPtr(pDay);
		return;
	}

	if (fClampedBlend >= 1.0f)
	{
		if (bHasNight)
			SetEnvironmentDataPtr(pNight);
		else if (bHasDay)
			SetEnvironmentDataPtr(pDay);
		return;
	}

	if (!bHasDay || !bHasNight)
	{
		if (bHasNight)
			SetEnvironmentDataPtr(pNight);
		else if (bHasDay)
			SetEnvironmentDataPtr(pDay);
		return;
	}

	static TEnvironmentData s_BlendedEnvironment;
	const TEnvironmentData& rkDay = *pDay;
	const TEnvironmentData& rkNight = *pNight;
	TEnvironmentData& rkOut = s_BlendedEnvironment;

	rkOut = rkDay;

	for (int i = 0; i < ENV_DIRLIGHT_NUM; ++i)
	{
		rkOut.bDirLightsEnable[i] = rkDay.bDirLightsEnable[i] || rkNight.bDirLightsEnable[i];
		LerpLight(rkOut.DirLights[i], rkDay.DirLights[i], rkNight.DirLights[i], fClampedBlend);
	}

	LerpColorValue(rkOut.Material.Ambient, rkDay.Material.Ambient, rkNight.Material.Ambient, fClampedBlend);
	LerpColorValue(rkOut.Material.Diffuse, rkDay.Material.Diffuse, rkNight.Material.Diffuse, fClampedBlend);
	LerpColorValue(rkOut.Material.Emissive, rkDay.Material.Emissive, rkNight.Material.Emissive, fClampedBlend);
	LerpColorValue(rkOut.Material.Specular, rkDay.Material.Specular, rkNight.Material.Specular, fClampedBlend);
	rkOut.Material.Power = LerpFloat(rkDay.Material.Power, rkNight.Material.Power, fClampedBlend);

	rkOut.bFogEnable = (fClampedBlend >= 0.5f) ? rkNight.bFogEnable : rkDay.bFogEnable;
	rkOut.bDensityFog = (fClampedBlend >= 0.5f) ? rkNight.bDensityFog : rkDay.bDensityFog;
	rkOut.m_fFogNearDistance = LerpFloat(rkDay.m_fFogNearDistance, rkNight.m_fFogNearDistance, fClampedBlend);
	rkOut.m_fFogFarDistance = LerpFloat(rkDay.m_fFogFarDistance, rkNight.m_fFogFarDistance, fClampedBlend);
	LerpColorValue(rkOut.FogColor, rkDay.FogColor, rkNight.FogColor, fClampedBlend);

	rkOut.bFilteringEnable = rkDay.bFilteringEnable || rkNight.bFilteringEnable;
	LerpColorValue(rkOut.FilteringColor, rkDay.FilteringColor, rkNight.FilteringColor, fClampedBlend);
	rkOut.byFilteringAlphaSrc = (BYTE) LerpFloat((float) rkDay.byFilteringAlphaSrc, (float) rkNight.byFilteringAlphaSrc, fClampedBlend);
	rkOut.byFilteringAlphaDest = (BYTE) LerpFloat((float) rkDay.byFilteringAlphaDest, (float) rkNight.byFilteringAlphaDest, fClampedBlend);

	rkOut.fWindStrength = LerpFloat(rkDay.fWindStrength, rkNight.fWindStrength, fClampedBlend);
	rkOut.fWindRandom = LerpFloat(rkDay.fWindRandom, rkNight.fWindRandom, fClampedBlend);

	rkOut.bLensFlareEnable = (fClampedBlend >= 0.5f) ? rkNight.bLensFlareEnable : rkDay.bLensFlareEnable;
	LerpColorValue(rkOut.LensFlareBrightnessColor, rkDay.LensFlareBrightnessColor, rkNight.LensFlareBrightnessColor, fClampedBlend);
	rkOut.fLensFlareMaxBrightness = LerpFloat(rkDay.fLensFlareMaxBrightness, rkNight.fLensFlareMaxBrightness, fClampedBlend);
	rkOut.bMainFlareEnable = (fClampedBlend >= 0.5f) ? rkNight.bMainFlareEnable : rkDay.bMainFlareEnable;
	rkOut.fMainFlareSize = LerpFloat(rkDay.fMainFlareSize, rkNight.fMainFlareSize, fClampedBlend);

	const TEnvironmentData& rkSkySource = (fClampedBlend >= 0.5f) ? rkNight : rkDay;
	rkOut.v3SkyBoxScale = rkSkySource.v3SkyBoxScale;
	rkOut.bSkyBoxTextureRenderMode = rkSkySource.bSkyBoxTextureRenderMode;
	rkOut.bySkyBoxGradientLevelUpper = rkSkySource.bySkyBoxGradientLevelUpper;
	rkOut.bySkyBoxGradientLevelLower = rkSkySource.bySkyBoxGradientLevelLower;
	for (int i = 0; i < 6; ++i)
		rkOut.strSkyBoxFaceFileName[i] = rkSkySource.strSkyBoxFaceFileName[i];
	rkOut.v2CloudScale = rkSkySource.v2CloudScale;
	rkOut.fCloudHeight = rkSkySource.fCloudHeight;
	rkOut.v2CloudTextureScale = rkSkySource.v2CloudTextureScale;
	rkOut.v2CloudSpeed = rkSkySource.v2CloudSpeed;
	rkOut.strCloudTextureFileName = rkSkySource.strCloudTextureFileName;
	rkOut.CloudGradientColor = rkSkySource.CloudGradientColor;
	rkOut.SkyBoxGradientColorVector = rkSkySource.SkyBoxGradientColorVector;
	rkOut.strMainFlareTextureFileName = rkSkySource.strMainFlareTextureFileName;

	SetEnvironmentDataPtr(&rkOut);
}
#endif

bool CMapManager::RegisterEnvironmentData(DWORD dwIndex, const char * c_szFileName)
{
	TEnvironmentData * pEnvironmentData = AllocEnvironmentData();

	if (!LoadEnvironmentData(c_szFileName, pEnvironmentData))
	{
		DeleteEnvironmentData(pEnvironmentData);
		return false;
	}

	const auto f=m_EnvironmentDataMap.find(dwIndex);
	if (m_EnvironmentDataMap.end()==f)
	{
		m_EnvironmentDataMap.insert(TEnvironmentDataMap::value_type(dwIndex, pEnvironmentData));
	}
	else
	{
		delete f->second;
		f->second=pEnvironmentData;
	}
	return true;
}

void CMapManager::GetCurrentEnvironmentData(const TEnvironmentData ** c_ppEnvironmentData) const
{
	*c_ppEnvironmentData = mc_pcurEnvironmentData;
}

bool CMapManager::GetEnvironmentData(DWORD dwIndex, const TEnvironmentData ** c_ppEnvironmentData)
{
	const auto itor = m_EnvironmentDataMap.find(dwIndex);

	if (m_EnvironmentDataMap.end() == itor)
	{
		*c_ppEnvironmentData = nullptr;
		return false;
	}

	*c_ppEnvironmentData = itor->second;
	return true;
}

void CMapManager::RefreshPortal() const
{
	if (!IsMapReady())
		return;

	CMapOutdoor & rMap = GetMapOutdoorRef();
	for (int i = 0; i < AROUND_AREA_NUM; ++i)
	{
		CArea * pArea;
		if (!rMap.GetAreaPointer(i, &pArea))
			continue;

		pArea->RefreshPortal();
	}
}

void CMapManager::ClearPortal() const
{
	if (!IsMapReady())
		return;

	CMapOutdoor & rMap = GetMapOutdoorRef();
	for (int i = 0; i < AROUND_AREA_NUM; ++i)
	{
		CArea * pArea;
		if (!rMap.GetAreaPointer(i, &pArea))
			continue;

		pArea->ClearPortal();
	}
}

void CMapManager::AddShowingPortalID(int iID) const
{
	if (!IsMapReady())
		return;

	CMapOutdoor & rMap = GetMapOutdoorRef();
	for (int i = 0; i < AROUND_AREA_NUM; ++i)
	{
		CArea * pArea;
		if (!rMap.GetAreaPointer(i, &pArea))
			continue;

		pArea->AddShowingPortalID(iID);
	}
}

TEnvironmentData * CMapManager::AllocEnvironmentData() const
{
	const auto pEnvironmentData = new TEnvironmentData;
	Environment_Init(*pEnvironmentData);
	return pEnvironmentData;
}

void CMapManager::DeleteEnvironmentData(TEnvironmentData * pEnvironmentData) const
{
	delete pEnvironmentData;
	pEnvironmentData = nullptr;
}

BOOL CMapManager::LoadEnvironmentData(const char * c_szFileName, TEnvironmentData * pEnvironmentData) const
{
	if (!pEnvironmentData)
		return FALSE;

	return (BOOL)Environment_Load(*pEnvironmentData, c_szFileName);
}

DWORD CMapManager::GetShadowMapColor(float fx, float fy) const
{
	if (!IsMapReady())
		return 0xFFFFFFFF;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetShadowMapColor(fx, fy);
}

std::vector<int> & CMapManager::GetRenderedSplatNum(int * piPatch, int * piSplat, float * pfSplatRatio) const
{
	if (!m_pkMap)
	{
		static std::vector<int> s_emptyVector;
		*piPatch = 0;
		*piSplat = 0;
		return s_emptyVector;
	}

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetRenderedSplatNum(piPatch, piSplat, pfSplatRatio);
}

CArea::TCRCWithNumberVector & CMapManager::GetRenderedGraphicThingInstanceNum(DWORD * pdwGraphicThingInstanceNum, DWORD * pdwCRCNum) const
{
	if (!m_pkMap)
	{
		static CArea::TCRCWithNumberVector s_emptyVector;
		*pdwGraphicThingInstanceNum = 0;
		*pdwCRCNum = 0;
		return s_emptyVector;
	}

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetRenderedGraphicThingInstanceNum(pdwGraphicThingInstanceNum, pdwCRCNum);
}

bool CMapManager::GetNormal(int ix, int iy, D3DXVECTOR3 * pv3Normal) const
{
	if (!IsMapReady())
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetNormal(ix, iy, pv3Normal);
}

bool CMapManager::isPhysicalCollision(const D3DXVECTOR3 & c_rvCheckPosition)
{
	if (!IsMapReady())
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.isAttrOn(c_rvCheckPosition.x, -c_rvCheckPosition.y, CTerrainImpl::ATTRIBUTE_BLOCK);
}

bool CMapManager::isAttrOn(float fX, float fY, BYTE byAttr) const
{
	if (!IsMapReady())
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.isAttrOn(fX, fY, byAttr);
}

bool CMapManager::GetAttr(float fX, float fY, BYTE * pbyAttr) const
{
	if (!IsMapReady())
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetAttr(fX, fY, pbyAttr);
}

bool CMapManager::isAttrOn(int iX, int iY, BYTE byAttr) const
{
	if (!IsMapReady())
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.isAttrOn(iX, iY, byAttr);
}

bool CMapManager::GetAttr(int iX, int iY, BYTE * pbyAttr) const
{
	if (!IsMapReady())
		return false;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetAttr(iX, iY, pbyAttr);
}

// 2004.10.14.myevan.TEMP_CAreaLoaderThread
/*
bool CMapManager::BGLoadingEnable()
{
	if (!IsMapReady())
		return false;
	return ((CMapOutdoor*)m_pMap)->BGLoadingEnable();
}

void CMapManager::BGLoadingEnable(bool bBGLoadingEnable)
{
	if (!IsMapReady())
		return;
	((CMapOutdoor*)m_pMap)->BGLoadingEnable(bBGLoadingEnable);
}
*/

void CMapManager::SetTerrainRenderSort(CMapOutdoor::ETerrainRenderSort eTerrainRenderSort) const
{
	if (!IsMapReady())
		return;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	rkMap.SetTerrainRenderSort(eTerrainRenderSort);
}

void CMapManager::SetTransparentTree(bool bTransparenTree) const
{
	if (!IsMapReady())
		return;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	rkMap.SetTransparentTree(bTransparenTree);
}

CMapOutdoor::ETerrainRenderSort CMapManager::GetTerrainRenderSort() const
{
	if (!IsMapReady())
		return CMapOutdoor::DISTANCE_SORT;

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	return rkMap.GetTerrainRenderSort();
}

void CMapManager::GetBaseXY(DWORD * pdwBaseX, DWORD * pdwBaseY) const
{
	if (!IsMapReady())
	{
		*pdwBaseX = 0;
		*pdwBaseY = 0;
	}

	CMapOutdoor& rkMap=GetMapOutdoorRef();
	rkMap.GetBaseXY(pdwBaseX, pdwBaseY);
}

void CMapManager::__LoadMapInfoVector()
{
	CMappedFile kFile;
	LPCVOID pData;
	if (!CEterPackManager::Instance().Get(kFile, m_stAtlasInfoFileName.c_str(), &pData))
		if (!CEterPackManager::Instance().Get(kFile, "AtlasInfo.txt", &pData))
			return;

	CMemoryTextFileLoader textFileLoader;
	textFileLoader.Bind(kFile.Size(), pData);

	char szMapName[256];
	int x, y;
	int width, height;
	for (UINT uLineIndex=0; uLineIndex<textFileLoader.GetLineCount(); ++uLineIndex)
	{
		const std::string& c_rstLine=textFileLoader.GetLineString(uLineIndex);
		sscanf(c_rstLine.c_str(), "%s %d %d %d %d",
			szMapName,
			&x, &y, &width, &height);

		if ('\0'==szMapName[0])
			continue;

		TMapInfo kMapInfo;
		kMapInfo.m_strName = szMapName;
		kMapInfo.m_dwBaseX = x;
		kMapInfo.m_dwBaseY = y;

		kMapInfo.m_dwSizeX = width;
		kMapInfo.m_dwSizeY = height;

		kMapInfo.m_dwEndX = kMapInfo.m_dwBaseX + kMapInfo.m_dwSizeX * CTerrainImpl::TERRAIN_XSIZE;
		kMapInfo.m_dwEndY = kMapInfo.m_dwBaseY + kMapInfo.m_dwSizeY * CTerrainImpl::TERRAIN_YSIZE;

		m_kVct_kMapInfo.push_back(kMapInfo);
	}

	return;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
