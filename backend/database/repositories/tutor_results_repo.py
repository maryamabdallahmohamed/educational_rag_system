from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.tutor_results import TutorResults    
from typing import Optional
import uuid

class TutorResultsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, cpa_result, tutor_result_text):
        new_result = TutorResults(
            result_id=uuid.uuid4(),
            cpa_result=cpa_result,
            tutor_result=tutor_result_text
        )
        self.db.add(new_result)
        await self.db.commit()    
        await self.db.refresh(new_result) 
        return new_result

    async def get_by_id(self, tutor_result_id: uuid.UUID) -> Optional[TutorResults]:
        result = await self.db.get(TutorResults, tutor_result_id)
        return result

