import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.play_session import PlaySession
from ..models.scenario import Scenario
from ..models.scenario_competency import ScenarioCompetency
from ..schemas.scenario import ScenarioDetailResponse, ScenarioListItem, ScenarioListResponse


async def get_active_scenarios(db: AsyncSession, user_id: uuid.UUID) -> ScenarioListResponse:
    scenarios = (await db.execute(select(Scenario).where(Scenario.is_active == True))).scalars().all()
    if not scenarios:
        return ScenarioListResponse(items=[], total=0)

    scenario_ids = [s.id for s in scenarios]
    competencies_rows = (await db.execute(select(ScenarioCompetency).where(ScenarioCompetency.scenario_id.in_(scenario_ids)))).scalars().all()
    competencies_map = defaultdict(list)

    for row in competencies_rows:
        competencies_map[row.scenario_id].append(row.competency_code)

    best_scores_rows = (
        await db.execute(
            select(PlaySession.scenario_id,func.max(PlaySession.score))
            .where(
                PlaySession.user_id == user_id,
                PlaySession.state.in_(['completed', 'failed']),
            ).group_by(PlaySession.scenario_id)
        )
    ).all()
    best_scores_map = {row[0]: row[1] for row in best_scores_rows}

    items = [
        ScenarioListItem(id=s.id, title=s.title, description=s.description, difficulty=s.difficulty,
            competencies=competencies_map.get(s.id, []),
            best_score=best_scores_map.get(s.id))
        for s in scenarios
    ]
    return ScenarioListResponse(items=items, total=len(items))


async def get_scenario_detail(db: AsyncSession, scenario_id: str, user_id: uuid.UUID) -> ScenarioDetailResponse:
    pass
