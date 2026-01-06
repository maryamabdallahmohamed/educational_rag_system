import os
import re
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

"""
Migration script to add 'session_id' and 'document_id' columns to the 'notes' table if they are missing.
"""

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback to loading .env if needed, though usually env is loaded by runner
        from dotenv import load_dotenv
        load_dotenv()
        database_url = os.getenv("DATABASE_URL")
        
    if not database_url:
        print("DATABASE_URL environment variable is not set.")
        return

    # Ensure asyncpg driver
    if "postgresql+asyncpg" not in database_url and "postgresql" in database_url:
        async_url = re.sub(r"^postgresql:", "postgresql+asyncpg:", database_url)
    else:
        async_url = database_url

    engine = create_async_engine(async_url, echo=True, future=True)

    async with engine.begin() as conn:
        print("Checking 'notes' table schema...")
        
        # 1. Add session_id if missing
        try:
            await conn.execute(text("ALTER TABLE notes ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES sessions(id);"))
            print("Added session_id column.")
        except Exception as e:
            print(f"Error adding session_id: {e}")

        # 2. Add document_id if missing (just in case)
        try:
            await conn.execute(text("ALTER TABLE notes ADD COLUMN IF NOT EXISTS document_id UUID REFERENCES documents(id);"))
            print("Added document_id column.")
        except Exception as e:
            print(f"Error adding document_id: {e}")

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(main())
