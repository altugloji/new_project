#pragma once

#include "AbstractSingleton.h"

class IAbstractChat : public TAbstractSingleton<IAbstractChat>
{
	public:
		IAbstractChat() {}
		virtual ~IAbstractChat() {}

#if defined(__BL_CLIENT_LOCALE_STRING__)
		enum ESpecialColorType
		{
			CHAT_SPECIAL_COLOR_NORMAL,
			CHAT_SPECIAL_COLOR_DICE_0,
			CHAT_SPECIAL_COLOR_DICE_1,
		};
#endif

#if defined(__BL_MULTI_LANGUAGE_PREMIUM__)
		virtual void AppendChat(int iType, const char* c_szChat, BYTE bSpecialColorType = ESpecialColorType::CHAT_SPECIAL_COLOR_NORMAL, BYTE bEmpire = 0, const std::string& countryName = "") = 0;
#else
		virtual void AppendChat(int iType, const char* c_szChat, BYTE bSpecialColorType = ESpecialColorType::CHAT_SPECIAL_COLOR_NORMAL) = 0;
#endif
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
