import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.achievement import Achievement
from ..models.user_achievement import UserAchievement
from ..schemas.achievement import (
    AchievementItem,
    AchievementsResponse,
)


async def get_achievements_progress(db: AsyncSession, user_id: uuid.UUID) -> AchievementsResponse:
    achievements = (await db.execute(select(Achievement))).scalars().all()
    user_achievements = (await db.execute(select(UserAchievement).where(UserAchievement.user_id == user_id))).scalars().all()

    user_achievements_map = {achievement.achievement_code: achievement.unlocked_at for achievement in user_achievements}

    achievement_items = [AchievementItem(
        code=achievement.code,
        title=achievement.title,
        description=achievement.description,
        icon=achievement.icon,
        condition=achievement.condition_code,
        unlocked=achievement.code in user_achievements_map,
        unlocked_at=user_achievements_map.get(achievement.code),
    ) for achievement in achievements]

    total = len(achievements)
    unlocked_count = sum(1 for item in achievement_items if item.unlocked)

    return AchievementsResponse(
        total=total,
        unlocked_count=unlocked_count,
        items=achievement_items,
    )
