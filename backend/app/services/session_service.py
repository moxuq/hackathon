from collections import defaultdict
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.achievement import Achievement
from backend.app.models.user_achievement import UserAchievement

from ..models.play_session import PlaySession, PlaySessionStates
from ..models.scenario import Scenario
from ..models.scenario_node import ScenarioNode
from ..models.session_event import SessionEvent
from ..schemas.session import (
    AchievementItem,
    ChoiceItem,
    ChoiceRequest,
    ChoiceResultResponse,
    CompetencyProgressItem,
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


async def get_session_debrief(db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionDebriefResponse:
    session = (await db.execute(select(PlaySession).where(PlaySession.id == session_id))).scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
    if session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access')
    if session.state == PlaySessionStates.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Session is active')

    events = (await db.execute(select(SessionEvent).where(SessionEvent.session_id == session_id))).scalars().all()

    if session.finished_at and session.started_at:
        duration_sec = int((session.finished_at - session.started_at).total_seconds())
    else:
        duration_sec = 0

    event_items = [SessionEventItem(
        event_type=e.event_type.value if hasattr(e.event_type, 'values') else str(e.event_type),
        node_key=e.node_key,
        choice_key=e.choice_key,
        loyalty_after=e.loyalty_after,
        safety_after=e.safety_after,
        score_delta=e.score_delta,
        created_at=e.created_at,
    ) for e in events]

    competency_deltas = defaultdict(lambda: {'title': '', 'delta': 0})

    for event in events:
        if event.competency_effects:
            for effect in event.competency_effects:
                code = effect.get('code')
                if code:
                    competency_deltas[code]['title'] = effect.get('title', '')
                    competency_deltas[code]['delta'] += effect.get('delta', 0)

    competency_progress = [
        CompetencyProgressItem(
            code=code,
            title=data['title'],
            delta=data['delta'],
            total_score=data['delta'],
        )
        for code, data in competency_deltas.items()
    ]

    achievements_rows = (await db.execute(select(Achievement)
        .join(UserAchievement, Achievement.code == UserAchievement.achievement_code)
        .where(UserAchievement.user_id == user_id, UserAchievement.session_id == session_id))
    ).scalars().all()

    achievements_unlocked = [
        AchievementItem(
            code=a.code,
            title=a.title,
            description=a.description,
            icon=a.icon,
        )
        for a in achievements_rows
    ]

    reccomendations = []
    for cp in competency_progress:
        if cp.delta <= 0:
            reccomendations.append(f'Рекомендуется повторить сценарий для улучшения компетенции «{cp.title}»')

    if session.state == PlaySessionStates.FAILED:
        reccomendations.append('Сценарий не завершён успешно. Попробуйте ещё раз, обращая внимание на безопасность')

    return SessionDebriefResponse(
            session_id=session.id,
            scenario_id=session.scenario_id,
            state=session.state.value if hasattr(session.state, 'value') else str(session.state),
            final_score=session.score,
            loyalty=session.loyalty,
            safety=session.safety,
            duration_sec=duration_sec,
            events=event_items,
            competency_progress=competency_progress,
            achievements_unlocked=achievements_unlocked,
            recommendations=reccomendations
        )
