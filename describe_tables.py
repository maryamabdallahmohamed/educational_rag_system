import asyncio
from backend.database.db import NeonDatabase
from sqlalchemy import text

async def describe_tables():
    db = NeonDatabase()
    engine = db.init()
    async with engine.begin() as conn:
        # Get column info for existing tables
        tables = ['learner_profiles', 'tutoring_sessions', 'learner_interactions']
        for table in tables:
            print(f'\n=== {table} ===')
            result = await conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            for col in columns:
                print(f'  {col[0]}: {col[1]} (nullable: {col[2]})')

if __name__ == "__main__":
    asyncio.run(describe_tables())
