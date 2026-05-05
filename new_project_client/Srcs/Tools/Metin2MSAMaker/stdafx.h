// stdafx.h : include file for standard system include files,
// or project specific include files that are used frequently, but
// are changed infrequently
//

#pragma once

#include "targetver.h"

#include <stdio.h>
#include <tchar.h>
#include <locale.h>

#include <granny.h>

#include <locale>
#include <list>
#include <vector>
#include <string>
#include <cstring>

#include <cassert>
#include <unordered_map>
#include <algorithm>
#include <filesystem>
#include <fstream>

namespace fs = std::filesystem;

inline std::string to_lower_copy(const std::string& s)
{
	std::string result = s;
	std::transform(result.begin(), result.end(), result.begin(),
		[](unsigned char c) { return std::tolower(c); });
	return result;
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
