#pragma once

extern bool GetExeCRC(DWORD & r_dwProcCRC, DWORD & r_dwFileCRC);

extern void BuildProcessCRC();
extern BYTE GetProcessCRCMagicCubePiece();
//archive's 6b9a24beef838d9382c750a6b44ccdb4
