#include "desc.h"

class DESC_P2P : public DESC
{
	public:
		virtual ~DESC_P2P();

		virtual void	Destroy();
		virtual void	SetPhase(int iPhase);
		bool		Setup(LPFDWATCH _fdw, socket_t fd, const char * host, WORD wPort);
};
//archive's 6b9a24beef838d9382c750a6b44ccdb4
