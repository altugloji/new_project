#ifndef RASCAL_CLIENT_H
#define RASCAL_CLIENT_H

#include <Windows.h>
#include <vector>
#include <string>
#include <intrin.h>
#include <wininet.h>
#include <sstream>
#include <iomanip>
#include <fstream>
#include <TlHelp32.h>
#include <psapi.h>
#include <unordered_set>
#include <chrono>
#include <map>

#include <skCrypter.h>
#include "rascal_protect.h"
#include "SecureMobLibTypes.h"

#pragma comment(lib, "rascal_client.lib")
#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "psapi.lib")

#define ImageNtHeaders(smodule) \
    (reinterpret_cast<PIMAGE_NT_HEADERS>(\
        reinterpret_cast<SIZE_T>(smodule) + \
        static_cast<SIZE_T>((reinterpret_cast<PIMAGE_DOS_HEADER>(smodule))->e_lfanew)\
    ))

static uintptr_t __fastcall getcalleraddr()
{
    const int max_frames = 62;
    void* frames[max_frames];
    const int frame_count = CaptureStackBackTrace(1, max_frames, frames, NULL);
    if (frame_count > 1)
        return reinterpret_cast<uintptr_t>(frames[1]);
    return 0;
}

namespace rascal {
    void FunctionProtect(void* Address);
    void GetRascalThreadID(void* thisptr);
    void WLog(std::string Content);
    void getunknown(int type);
    void RascalProtectRTypes(Protect atype, void* addr, int previousvalue);
    void InitializeRascal(std::string ServerIP, int MaxClient, std::string key);
    void RascalCallback(int unknown);

    bool RequireLiveSession();
    bool TryKeepSessionAlive();
    bool PingWorkerThread(DWORD threadId);
    void MaintainWorkerLink(DWORD threadId);
    bool VerifyDllFingerprints();
    bool VerifySignedRascalDll();
    uint32_t GetSessionHeartbeat();

    void CheckRascalThreads();
    bool CheckRascalExports(void* address);
    void ListModulesForTheVMPSections();

    void DetectIATHooks();
    bool DetectHooks(const char* moduleName, const char* funcName);
    void RunStartupHookChecks();

    template<typename A>
    static void __forceinline EncryptDecryptPointer(A& ptr) {
        uint32_t key = 0xDEADBEEF;
        uintptr_t addr = reinterpret_cast<uintptr_t>(ptr);
        addr ^= key;
        ptr = reinterpret_cast<A>(addr);
    }

    template<typename T>
    static void __forceinline EncryptDecryptPointerVector(std::vector<T>& vec) {
        uint32_t key = 0xDEADBEEF;
        for (auto& ptr : vec) {
            uintptr_t addr = reinterpret_cast<uintptr_t>(ptr);
            addr ^= key;
            ptr = reinterpret_cast<T>(addr);
        }
    }

    static uint32_t crc32_table[256];
    static const char* CRCListLink = "";

    static void GenerateCRC32Table() {
        uint32_t polynomial = 0xEDB88320;
        for (uint32_t i = 0; i < 256; ++i) {
            uint32_t crc = i;
            for (uint32_t j = 0; j < 8; ++j)
                crc = (crc & 1) ? (crc >> 1) ^ polynomial : crc >> 1;
            crc32_table[i] = crc;
        }
    }

    static uint32_t CalculateCRC32(const std::string& filename) {
        std::ifstream file(filename, std::ios::binary);
        if (!file)
            return 0;
        uint32_t crc = 0xFFFFFFFF;
        char buffer[4096];
        while (file.read(buffer, sizeof(buffer)) || file.gcount() > 0) {
            const std::streamsize n = file.gcount();
            for (std::streamsize i = 0; i < n; ++i)
                crc = (crc >> 8) ^ crc32_table[(crc ^ static_cast<uint8_t>(buffer[i])) & 0xFF];
        }
        return crc ^ 0xFFFFFFFF;
    }

    static float gamerecievedAtkSpeed = 0.0f;
    static std::map<DWORD, std::chrono::steady_clock::time_point> client_attack_map;
}

void WINAPI initialiseRascal(LPARAM lParam);

#endif
