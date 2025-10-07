from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func, and_, or_
from sqlalchemy.orm import selectinload
from backend.database.models.learner_interaction import LearnerInteraction
from backend.database.models.tutoring_session import TutoringSession
from backend.database.models.learning_unit import LearningUnit
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid


class LearnerInteractionRepository:
    """Repository for LearnerInteraction operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_interaction(
        self,
        session_id: UUID,
        interaction_type: str,
        query_text: str,
        response_text: str,
        **kwargs
    ) -> LearnerInteraction:
        """Create new interaction record"""
        interaction = LearnerInteraction(
            session_id=session_id,
            interaction_type=interaction_type,
            query_text=query_text,
            response_text=response_text,
            learning_unit_id=kwargs.get("learning_unit_id"),
            response_time_seconds=kwargs.get("response_time_seconds"),
            difficulty_rating=kwargs.get("difficulty_rating"),
            was_helpful=kwargs.get("was_helpful"),
            adaptation_requested=kwargs.get("adaptation_requested", False),
            metadata=kwargs.get("metadata")
        )
        self.session.add(interaction)
        await self.session.commit()
        await self.session.refresh(interaction)
        return interaction

    async def get_session_interactions(self, session_id: UUID) -> List[LearnerInteraction]:
        """Get all interactions for a session ordered by created_at asc"""
        result = await self.session.execute(
            select(LearnerInteraction)
            .where(LearnerInteraction.session_id == session_id)
            .order_by(LearnerInteraction.created_at.asc())
        )
        return result.scalars().all()

    async def update_feedback(
        self,
        interaction_id: UUID,
        was_helpful: bool,
        difficulty_rating: int = None
    ) -> bool:
        """Update learner feedback on an interaction"""
        try:
            updates = {"was_helpful": was_helpful}
            if difficulty_rating is not None:
                updates["difficulty_rating"] = difficulty_rating

            result = await self.session.execute(
                update(LearnerInteraction)
                .where(LearnerInteraction.id == interaction_id)
                .values(**updates)
            )
            
            if result.rowcount > 0:
                await self.session.commit()
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_recent_struggles(self, learner_id: UUID, limit: int = 20) -> List[LearnerInteraction]:
        """Get recent interactions where learner struggled"""
        result = await self.session.execute(
            select(LearnerInteraction)
            .join(TutoringSession, LearnerInteraction.session_id == TutoringSession.id)
            .where(
                and_(
                    TutoringSession.learner_id == learner_id,
                    or_(
                        LearnerInteraction.was_helpful == False,
                        LearnerInteraction.difficulty_rating >= 4
                    )
                )
            )
            .order_by(desc(LearnerInteraction.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def analyze_learning_patterns(self, learner_id: UUID) -> Dict[str, Any]:
        """Aggregate statistics for learning pattern analysis"""
        try:
            # Most common interaction types
            interaction_types_result = await self.session.execute(
                select(
                    LearnerInteraction.interaction_type,
                    func.count(LearnerInteraction.id).label('count')
                )
                .join(TutoringSession, LearnerInteraction.session_id == TutoringSession.id)
                .where(TutoringSession.learner_id == learner_id)
                .group_by(LearnerInteraction.interaction_type)
                .order_by(desc(func.count(LearnerInteraction.id)))
            )
            interaction_types = [
                {"type": row.interaction_type, "count": row.count}
                for row in interaction_types_result.fetchall()
            ]

            # Average response times by interaction type
            response_times_result = await self.session.execute(
                select(
                    LearnerInteraction.interaction_type,
                    func.avg(LearnerInteraction.response_time_seconds).label('avg_response_time'),
                    func.count(LearnerInteraction.id).label('count')
                )
                .join(TutoringSession, LearnerInteraction.session_id == TutoringSession.id)
                .where(
                    and_(
                        TutoringSession.learner_id == learner_id,
                        LearnerInteraction.response_time_seconds.isnot(None)
                    )
                )
                .group_by(LearnerInteraction.interaction_type)
            )
            response_times = [
                {
                    "type": row.interaction_type,
                    "avg_response_time": float(row.avg_response_time) if row.avg_response_time else 0.0,
                    "count": row.count
                }
                for row in response_times_result.fetchall()
            ]

            # Topics with most struggles (by learning_unit_id)
            struggles_result = await self.session.execute(
                select(
                    LearningUnit.title,
                    LearnerInteraction.learning_unit_id,
                    func.count(LearnerInteraction.id).label('struggle_count')
                )
                .join(TutoringSession, LearnerInteraction.session_id == TutoringSession.id)
                .join(LearningUnit, LearnerInteraction.learning_unit_id == LearningUnit.id)
                .where(
                    and_(
                        TutoringSession.learner_id == learner_id,
                        or_(
                            LearnerInteraction.was_helpful == False,
                            LearnerInteraction.difficulty_rating >= 4,
                            LearnerInteraction.adaptation_requested == True
                        )
                    )
                )
                .group_by(LearningUnit.title, LearnerInteraction.learning_unit_id)
                .order_by(desc(func.count(LearnerInteraction.id)))
            )
            struggle_topics = [
                {
                    "learning_unit_id": str(row.learning_unit_id),
                    "title": row.title,
                    "struggle_count": row.struggle_count
                }
                for row in struggles_result.fetchall()
            ]

            # Overall helpfulness rate
            helpfulness_result = await self.session.execute(
                select(
                    func.count(LearnerInteraction.id).label('total_interactions'),
                    func.sum(
                        func.case((LearnerInteraction.was_helpful == True, 1), else_=0)
                    ).label('helpful_interactions')
                )
                .join(TutoringSession, LearnerInteraction.session_id == TutoringSession.id)
                .where(
                    and_(
                        TutoringSession.learner_id == learner_id,
                        LearnerInteraction.was_helpful.isnot(None)
                    )
                )
            )
            helpfulness_row = helpfulness_result.fetchone()
            
            total_interactions = helpfulness_row.total_interactions or 0
            helpful_interactions = helpfulness_row.helpful_interactions or 0
            helpfulness_rate = (helpful_interactions / total_interactions) if total_interactions > 0 else 0.0

            return {
                "interaction_types": interaction_types,
                "response_times_by_type": response_times,
                "struggle_topics": struggle_topics,
                "helpfulness_rate": float(helpfulness_rate),
                "total_interactions": total_interactions,
                "helpful_interactions": helpful_interactions
            }

        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_content_effectiveness(self, learning_unit_id: UUID) -> Dict[str, Any]:
        """Calculate effectiveness metrics for a specific learning unit"""
        try:
            # Total interactions for this learning unit
            total_result = await self.session.execute(
                select(func.count(LearnerInteraction.id))
                .where(LearnerInteraction.learning_unit_id == learning_unit_id)
            )
            total_interactions = total_result.scalar() or 0

            if total_interactions == 0:
                return {
                    "learning_unit_id": str(learning_unit_id),
                    "total_interactions": 0,
                    "helpfulness_rate": 0.0,
                    "avg_difficulty_rating": 0.0,
                    "struggle_patterns": []
                }

            # Helpfulness rate
            helpfulness_result = await self.session.execute(
                select(
                    func.count(LearnerInteraction.id).label('total_with_feedback'),
                    func.sum(
                        func.case((LearnerInteraction.was_helpful == True, 1), else_=0)
                    ).label('helpful_count')
                )
                .where(
                    and_(
                        LearnerInteraction.learning_unit_id == learning_unit_id,
                        LearnerInteraction.was_helpful.isnot(None)
                    )
                )
            )
            help_row = helpfulness_result.fetchone()
            total_with_feedback = help_row.total_with_feedback or 0
            helpful_count = help_row.helpful_count or 0
            helpfulness_rate = (helpful_count / total_with_feedback) if total_with_feedback > 0 else 0.0

            # Average difficulty rating
            difficulty_result = await self.session.execute(
                select(func.avg(LearnerInteraction.difficulty_rating))
                .where(
                    and_(
                        LearnerInteraction.learning_unit_id == learning_unit_id,
                        LearnerInteraction.difficulty_rating.isnot(None)
                    )
                )
            )
            avg_difficulty = difficulty_result.scalar() or 0.0

            # Common struggle patterns from metadata and interaction types
            patterns_result = await self.session.execute(
                select(
                    LearnerInteraction.interaction_type,
                    func.count(LearnerInteraction.id).label('count')
                )
                .where(
                    and_(
                        LearnerInteraction.learning_unit_id == learning_unit_id,
                        or_(
                            LearnerInteraction.was_helpful == False,
                            LearnerInteraction.difficulty_rating >= 4,
                            LearnerInteraction.adaptation_requested == True
                        )
                    )
                )
                .group_by(LearnerInteraction.interaction_type)
                .order_by(desc(func.count(LearnerInteraction.id)))
            )
            struggle_patterns = [
                {"pattern": row.interaction_type, "frequency": row.count}
                for row in patterns_result.fetchall()
            ]

            return {
                "learning_unit_id": str(learning_unit_id),
                "total_interactions": total_interactions,
                "helpfulness_rate": float(helpfulness_rate),
                "avg_difficulty_rating": float(avg_difficulty),
                "struggle_patterns": struggle_patterns,
                "feedback_coverage": (total_with_feedback / total_interactions) if total_interactions > 0 else 0.0
            }

        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_interactions_with_context(self, session_id: UUID) -> List[LearnerInteraction]:
        """Get session interactions with learning unit context loaded"""
        result = await self.session.execute(
            select(LearnerInteraction)
            .options(selectinload(LearnerInteraction.learning_unit))
            .where(LearnerInteraction.session_id == session_id)
            .order_by(LearnerInteraction.created_at.asc())
        )
        return result.scalars().all()
