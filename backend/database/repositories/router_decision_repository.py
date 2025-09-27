from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.router import RouterDecision, RouteType    
from typing import Optional
import uuid

class RouterDecisionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, query: str, chosen_route: RouteType ) -> RouterDecision:
        decision = RouterDecision(
            query=query,
            chosen_route=chosen_route
        )
        self.db.add(decision)
        await self.db.commit()    
        await self.db.refresh(decision) 
        return decision

    async def get_by_id(self, decision_id: uuid.UUID) -> Optional[RouterDecision]:
        result = await self.db.get(RouterDecision, decision_id)
        return result

