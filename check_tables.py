import asyncio
from backend.database.db import NeonDatabase
from sqlalchemy import text

async def check_tables():
    db = NeonDatabase()
    engine = db.init()
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = result.fetchall()
        print('Existing tables:')
        for table in tables:
            print(f'  - {table[0]}')

if __name__ == "__main__":
    asyncio.run(check_tables())