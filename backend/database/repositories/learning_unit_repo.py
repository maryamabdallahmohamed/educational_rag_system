from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.database.models.learning_unit import LearningUnit
from typing import Optional, List
import uuid
class LearningUnitRepository:

    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create( self,
        cpa_session_id: uuid.UUID,
        title: str,
        subtopics: Optional[list] = None,
        detailed_explanation: Optional[str] = None,
        key_points: Optional[list] = None,
        difficulty_level: Optional[str] = None,
        learning_objectives: Optional[list] = None,
        keywords: Optional[list] = None,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        source_document_id: Optional[uuid.UUID] = None,
        source_chunks: Optional[list] = None,
        adaptation_applied: Optional[str] = None
    ) -> LearningUnit:
        """Create a new learning unit"""
        unit = LearningUnit(
            cpa_session_id=cpa_session_id,
            title=title,
            subtopics=subtopics,
            detailed_explanation=detailed_explanation,
            key_points=key_points,
            difficulty_level=difficulty_level,
            learning_objectives=learning_objectives,
            keywords=keywords,
            subject=subject,
            grade_level=grade_level,
            source_document_id=source_document_id,
            source_chunks=source_chunks,
            adaptation_applied=adaptation_applied
        )
        self.session.add(unit)
        await self.session.commit()
        await self.session.refresh(unit)
        return unit

    async def create_batch(
        self, 
        cpa_session_id: uuid.UUID, 
        units_data: List[dict]
    ) -> List[LearningUnit]:
        """Create multiple learning units in a batch"""
        units = []
        for unit_data in units_data:
            unit = LearningUnit(
                cpa_session_id=cpa_session_id,
                title=unit_data.get("title"),
                subtopics=unit_data.get("subtopics"),
                detailed_explanation=unit_data.get("detailed_explanation"),
                key_points=unit_data.get("key_points"),
                difficulty_level=unit_data.get("difficulty_level"),
                learning_objectives=unit_data.get("learning_objectives"),
                keywords=unit_data.get("keywords"),
                subject=unit_data.get("subject"),
                grade_level=unit_data.get("grade_level"),
                source_document_id=unit_data.get("source_document_id"),
                source_chunks=unit_data.get("source_chunks"),
                adaptation_applied=unit_data.get("adaptation_applied")
            )
            self.session.add(unit)
            units.append(unit)
        
        await self.session.commit()
        for unit in units:
            await self.session.refresh(unit)
        return units

    async def get_by_id(self, unit_id: uuid.UUID) -> Optional[LearningUnit]:
        """Get a learning unit by ID"""
        result = await self.session.execute(
            select(LearningUnit).where(LearningUnit.id == unit_id)
        )
        return result.scalar_one_or_none()
