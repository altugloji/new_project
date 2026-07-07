#pragma once

#include "MSWindow.h"

class CMSApplication : public CMSWindow
{
	public:
		CMSApplication();
		virtual ~CMSApplication();

		void Initialize(HINSTANCE hInstance) const;

		void MessageLoop();

		bool IsMessage() const;
		bool MessageProcess() const;
#include "../UserInterface/Locale_inc.h"
#ifdef ENABLE_RASCAL_ANTICHEAT_V2
            static int DThreadId;
#endif

	protected:
		void ClearWindowClass();

		LRESULT WindowProcedure(HWND hWnd, UINT uiMsg, WPARAM wParam, LPARAM lParam);
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
