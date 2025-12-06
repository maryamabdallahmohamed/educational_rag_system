from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.tool_output import ToolOutput    
from typing import Optional
import uuid

class ToolOutputRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tool_name, input_state, output, tutor_result_id):
        tool_output = ToolOutput(
            tool_output_id=uuid.uuid4(),
            tool_name=tool_name,
            input_state=input_state,
            output=output,
            tutor_result_id=tutor_result_id
        )
        self.db.add(tool_output)
        await self.db.commit()    
        await self.db.refresh(tool_output) 
        return tool_output

    async def get_by_id(self, tool_output_id: uuid.UUID) -> Optional[ToolOutput]:
        result = await self.db.get(ToolOutput, tool_output_id)
        return result

