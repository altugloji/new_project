#include "Base.h"

CBase::CBase()
{
    id = 0;
}

CBase::~CBase()
{
}

bool CBase::isNumber() const
{
    return (id & MID_NUMBER);
}

bool CBase::isVar() const
{
    return (id & MID_VARIABLE);
}

bool CBase::isSymbol() const
{
    return (id & MID_SYMBOL);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
