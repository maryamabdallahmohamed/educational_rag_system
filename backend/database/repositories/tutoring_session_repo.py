from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func
from sqlalchemy.orm import selectinload
from backend.database.models.tutoring_session import TutoringSession
from typing import Optional, List
from uuid import UUID
import uuid
from datetime import datetime


class TutoringSessionRepository:
    """Repository for TutoringSession operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        learner_id: UUID,
        cpa_session_id: UUID = None
    ) -> TutoringSession:
        """Create new active tutoring session"""
        session_record = TutoringSession(
            learner_id=learner_id,
            cpa_session_id=cpa_session_id,
            session_state={},
            interaction_history={},
            is_active=True
        )
        self.session.add(session_record)
        await self.session.commit()
        await self.session.refresh(session_record)
        return session_record

    async def get_by_id(self, session_id: UUID) -> Optional[TutoringSession]:
        """Fetch session with learner profile eagerly loaded"""
        result = await self.session.execute(
            select(TutoringSession)
            .options(selectinload(TutoringSession.learner))
            .where(TutoringSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_session(self, learner_id: UUID) -> Optional[TutoringSession]:
        """Find the most recent is_active=True session for this learner"""
        result = await self.session.execute(
            select(TutoringSession)
            .where(
                TutoringSession.learner_id == learner_id,
                TutoringSession.is_active == True
            )
            .order_by(desc(TutoringSession.started_at))
        )
        return result.scalar_one_or_none()

    async def update_session_state(self, session_id: UUID, state_updates: dict) -> bool:
        """Merge state_updates into existing session_state JSONB"""
        try:
            # Get current session
            current_session = await self.get_by_id(session_id)
            if not current_session:
                return False

            # Merge updates with existing state
            current_state = current_session.session_state or {}
            merged_state = {**current_state, **state_updates}

            await self.session.execute(
                update(TutoringSession)
                .where(TutoringSession.id == session_id)
                .values(session_state=merged_state)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            raise e

    async def add_to_interaction_history(self, session_id: UUID, interaction: dict) -> bool:
        """Append interaction to interaction_history JSONB array"""
        try:
            # Get current session
            current_session = await self.get_by_id(session_id)
            if not current_session:
                return False

            # Handle interaction_history as array
            current_history = current_session.interaction_history
            
            # Initialize as empty list if None or empty dict
            if current_history is None or current_history == {}:
                history_list = []
            elif isinstance(current_history, list):
                history_list = current_history
            else:
                # If it's a dict, convert to list with single item
                history_list = [current_history]

            # Add timestamp to interaction if not present
            if 'timestamp' not in interaction:
                interaction['timestamp'] = datetime.utcnow().isoformat()

            # Append new interaction
            history_list.append(interaction)

            await self.session.execute(
                update(TutoringSession)
                .where(TutoringSession.id == session_id)
                .values(interaction_history=history_list)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            raise e

    async def end_session(
        self,
        session_id: UUID,
        performance_summary: dict
    ) -> Optional[TutoringSession]:
        """End session and store performance summary"""
        try:
            result = await self.session.execute(
                update(TutoringSession)
                .where(TutoringSession.id == session_id)
                .values(
                    is_active=False,
                    ended_at=func.now(),
                    performance_summary=performance_summary
                )
                .returning(TutoringSession)
            )
            updated_session = result.scalar_one_or_none()
            
            if updated_session:
                await self.session.commit()
                await self.session.refresh(updated_session)
            
            return updated_session
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_learner_history(
        self,
        learner_id: UUID,
        limit: int = 10
    ) -> List[TutoringSession]:
        """Get recent sessions for analytics"""
        result = await self.session.execute(
            select(TutoringSession)
            .where(TutoringSession.learner_id == learner_id)
            .order_by(desc(TutoringSession.started_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_session_with_interactions(self, session_id: UUID) -> Optional[TutoringSession]:
        """Get session with interactions eagerly loaded"""
        result = await self.session.execute(
            select(TutoringSession)
            .options(
                selectinload(TutoringSession.learner),
                selectinload(TutoringSession.interactions)
            )
            .where(TutoringSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_sessions_count(self, learner_id: UUID) -> int:
        """Count active sessions for a learner"""
        result = await self.session.execute(
            select(func.count(TutoringSession.id))
            .where(
                TutoringSession.learner_id == learner_id,
                TutoringSession.is_active == True
            )
        )
        return result.scalar() or 0
