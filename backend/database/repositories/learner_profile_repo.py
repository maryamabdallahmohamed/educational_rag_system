from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from backend.database.models.learner_profile import LearnerProfile
from typing import Optional
from uuid import UUID
import uuid
from datetime import datetime

class LearnerProfileRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_profile(
        self,
        grade_level: int,
        learning_style: str = None,
        **kwargs
    ) -> LearnerProfile:
        """Create a new learner profile"""
        profile = LearnerProfile(
            grade_level=grade_level,
            learning_style=learning_style,
            preferred_language=kwargs.get("preferred_language", "en"),
            difficulty_preference=kwargs.get("difficulty_preference", "medium"),
            avg_response_time=kwargs.get("avg_response_time", 0.0),
            accuracy_rate=kwargs.get("accuracy_rate", 0.0),
            completion_rate=kwargs.get("completion_rate", 0.0),
            total_sessions=kwargs.get("total_sessions", 0),
            interaction_patterns=kwargs.get("interaction_patterns"),
            learning_struggles=kwargs.get("learning_struggles"),
            mastered_topics=kwargs.get("mastered_topics"),
            preferred_explanation_styles=kwargs.get("preferred_explanation_styles")
        )
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_by_id(self, profile_id: UUID) -> Optional[LearnerProfile]:
        """Get a learner profile by ID"""
        result = await self.session.execute(
            select(LearnerProfile).where(LearnerProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, profile_id: UUID, **updates) -> Optional[LearnerProfile]:
        """Update profile fields"""
        try:
            # Add updated_at timestamp
            updates['updated_at'] = func.now()
            
            result = await self.session.execute(
                update(LearnerProfile)
                .where(LearnerProfile.id == profile_id)
                .values(**updates)
                .returning(LearnerProfile)
            )
            updated_profile = result.scalar_one_or_none()
            
            if updated_profile:
                await self.session.commit()
                await self.session.refresh(updated_profile)
            
            return updated_profile
        except Exception as e:
            await self.session.rollback()
            raise e

    async def update_performance_metrics(
        self,
        profile_id: UUID,
        new_accuracy: float,
        new_response_time: float,
        session_completed: bool
    ) -> Optional[LearnerProfile]:
        """Incrementally update running averages"""
        try:
            profile = await self.get_by_id(profile_id)
            if not profile:
                return None

            # Calculate new averages using formula: new_avg = (old_avg * n + new_value) / (n + 1)
            current_sessions = profile.total_sessions
            
            new_avg_accuracy = (profile.accuracy_rate * current_sessions + new_accuracy) / (current_sessions + 1)
            new_avg_response_time = (profile.avg_response_time * current_sessions + new_response_time) / (current_sessions + 1)
            
            updates = {
                'accuracy_rate': new_avg_accuracy,
                'avg_response_time': new_avg_response_time,
                'updated_at': func.now()
            }
            
            if session_completed:
                new_total_sessions = current_sessions + 1
                updates['total_sessions'] = new_total_sessions
                # Assuming completion_rate is percentage of completed sessions
                updates['completion_rate'] = (new_total_sessions / new_total_sessions) * 100  # This can be adjusted based on actual completion logic

            result = await self.session.execute(
                update(LearnerProfile)
                .where(LearnerProfile.id == profile_id)
                .values(**updates)
                .returning(LearnerProfile)
            )
            updated_profile = result.scalar_one_or_none()
            
            if updated_profile:
                await self.session.commit()
                await self.session.refresh(updated_profile)
            
            return updated_profile
        except Exception as e:
            await self.session.rollback()
            raise e

    async def add_mastered_topic(self, profile_id: UUID, topic: str) -> bool:
        """Add topic to mastered_topics JSONB array"""
        try:
            profile = await self.get_by_id(profile_id)
            if not profile:
                return False

            # Get current mastered topics or initialize empty list
            current_topics = profile.mastered_topics or []
            
            # Add topic if not already present
            if topic not in current_topics:
                current_topics.append(topic)
                
                await self.session.execute(
                    update(LearnerProfile)
                    .where(LearnerProfile.id == profile_id)
                    .values(
                        mastered_topics=current_topics,
                        updated_at=func.now()
                    )
                )
                await self.session.commit()
            
            return True
        except Exception as e:
            await self.session.rollback()
            raise e

    async def add_learning_struggle(self, profile_id: UUID, topic: str, struggle_type: str) -> bool:
        """Add struggle record to learning_struggles JSONB"""
        try:
            profile = await self.get_by_id(profile_id)
            if not profile:
                return False

            # Get current struggles or initialize empty list
            current_struggles = profile.learning_struggles or []
            
            # Create new struggle record
            struggle_record = {
                "topic": topic,
                "type": struggle_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            current_struggles.append(struggle_record)
            
            await self.session.execute(
                update(LearnerProfile)
                .where(LearnerProfile.id == profile_id)
                .values(
                    learning_struggles=current_struggles,
                    updated_at=func.now()
                )
            )
            await self.session.commit()
            
            return True
        except Exception as e:
            await self.session.rollback()
            raise e
