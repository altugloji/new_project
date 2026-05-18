#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "item.h"
#include "item_addon.h"

namespace
{
// After rolling addon bonuses, scale by this percent (100 = unchanged). 85 ~= 15% weaker.
	enum
	{
		ADDON_BONUS_SCALE_PCT = 85
	};
}

CItemAddonManager::CItemAddonManager()
{
}

CItemAddonManager::~CItemAddonManager()
{
}

void CItemAddonManager::ApplyAddonTo(int iAddonType, LPITEM pItem) const
{
	if (!pItem)
	{
		sys_err("ITEM pointer null");
		return;
	}

	const int iSkillBonusRaw = MINMAX(-30, (int) (gauss_random(0, 5) + 0.5f), 30);
	int iNormalHitBonus = 0;
	if (abs(iSkillBonusRaw) <= 20)
		iNormalHitBonus = -2 * iSkillBonusRaw + abs(number(-8, 8) + number(-8, 8)) + number(1, 4);
	else
		iNormalHitBonus = -2 * iSkillBonusRaw + number(1, 5);

	const int iSkillBonus = MINMAX(-30, iSkillBonusRaw * ADDON_BONUS_SCALE_PCT / 100, 30);
	iNormalHitBonus = iNormalHitBonus * ADDON_BONUS_SCALE_PCT / 100;

	pItem->RemoveAttributeType(APPLY_SKILL_DAMAGE_BONUS);
	pItem->RemoveAttributeType(APPLY_NORMAL_HIT_DAMAGE_BONUS);
	pItem->AddAttribute(APPLY_NORMAL_HIT_DAMAGE_BONUS, iNormalHitBonus);
	pItem->AddAttribute(APPLY_SKILL_DAMAGE_BONUS, iSkillBonus);
}
//archive's 6b9a24beef838d9382c750a6b44ccdb4
