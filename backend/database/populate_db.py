import asyncio
from sqlalchemy import text
from dotenv import load_dotenv
from backend.database.db import NeonDatabase
from backend.database.models import Base
# Import all models to ensure they're registered with SQLAlchemy metadata
from backend.database.models import (
    Document, Chunk, Conversation, RouterDecision, 
    ContentProcessorAgent, LearningUnit, QuestionAnswer, 
    QuestionAnswerItem, SummaryRecord,
    # New Tutor Agent models
    LearnerProfile, TutoringSession, LearnerInteraction
)
load_dotenv()

# Initialize your custom Database wrapper
Db =NeonDatabase()
engine = Db.init()

async def init_db():
    async with engine.begin() as conn:
        # Enable pgvector extension if not already
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception as e:
            print(f"⚠️ Skipping extension creation: {e}")
        
        # Create tables from your models
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized")
    
    # Verify new tutor agent tables are created
    async with engine.connect() as conn:
        try:
            # Check if new tables exist
            tables_to_check = [
                'learner_profiles',
                'tutoring_sessions', 
                'learner_interactions'
            ]
            
            for table_name in tables_to_check:
                result = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    );
                """))
                exists = result.scalar()
                if exists:
                    print(f"✅ Table '{table_name}' created successfully")
                else:
                    print(f"❌ Table '{table_name}' not found")
                    
        except Exception as e:
            print(f"⚠️ Could not verify table creation: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
