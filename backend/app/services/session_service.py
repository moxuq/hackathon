import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.play_session import PlaySession, PlaySessionStates
from ..models.scenario import Scenario
from ..models.scenario_node import ScenarioNode
from ..schemas.session import (
    ChoiceItem,
    ChoiceRequest,
    ChoiceResultResponse,
    NodeResponse,
    SessionDebriefResponse,
    SessionEventItem,
    SessionResponse,
    SessionStartRequest,
)
from .scenario_service import get_active_scenarios


async def start_session(db: AsyncSession, user_id: uuid.UUID,data: SessionStartRequest) -> tuple[SessionResponse, bool]:
    scenario = (await db.execute(select(Scenario)
        .where(Scenario.id == data.scenario_id, Scenario.is_active.is_(True)))
    ).scalar_one_or_none()

    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Scenario not found')

    existing_session = (await db.execute(select(PlaySession)
        .where(PlaySession.user_id == user_id, PlaySession.scenario_id == data.scenario_id, PlaySession.state == PlaySessionStates.ACTIVE))
    ).scalar_one_or_none()
    if existing_session is not None:
        response = SessionResponse(
            session_id=existing_session.id,
            scenario_id=existing_session.scenario_id,
            current_node_key=existing_session.current_node_key,
            state=existing_session.state.value,
            loyalty=existing_session.loyalty,
            safety=existing_session.safety,
            score=existing_session.score,
            deadline=existing_session.deadline,
            started_at=existing_session.started_at,
            is_restarted=True,
        )
        return response, True
    start_node = (await db.execute(select(ScenarioNode)
        .where(ScenarioNode.scenario_id == scenario.id, ScenarioNode.is_start.is_(True)))
    ).scalar_one_or_none()
    if start_node is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Start node not found for scenario')
    new_session = PlaySession(user_id=user_id, scenario_id=scenario.id, current_node_key=start_node.node_key)
    db.add(new_session)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(new_session)
    response = SessionResponse(
        session_id=new_session.id,
        scenario_id=new_session.scenario_id,
        current_node_key=new_session.current_node_key,
        state=new_session.state.value,
        loyalty=new_session.loyalty,
        safety=new_session.safety,
        score=new_session.score,
        deadline=new_session.deadline,
        started_at=new_session.started_at,
        is_restarted=False,
    )
    return response, False
