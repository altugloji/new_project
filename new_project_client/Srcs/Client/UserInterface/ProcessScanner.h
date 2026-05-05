#pragma once

typedef std::pair<DWORD, std::string> CRCPair;

void ProcessScanner_Destroy();
bool ProcessScanner_Create();
void ProcessScanner_ReleaseQuitEvent();

bool ProcessScanner_PopProcessQueue(std::vector<CRCPair>* pkVct_crcPair);
//archive's 6b9a24beef838d9382c750a6b44ccdb4
