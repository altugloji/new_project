#pragma once

// bool GrannyMeshGetTextureAnimation(granny_mesh* pgrnMesh, float* puVelocity, float* pvVelocity);
// bool GrannyMeshIsTextureAnimation(granny_mesh* pgrnMesh);
bool GrannyMeshIsDeform(granny_mesh* pgrnMesh);

class CGraphicImage;

struct SMaterialData
{
	CGraphicImage * pImage;
	float fSpecularPower;
	BOOL isSpecularEnable;
	BYTE bSphereMapIndex;
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
