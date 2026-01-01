import os
import re
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

"""
One-off migration script to align the 'summaries' table with the current SQLAlchemy model
which stores only 'id', 'content', and 'created_at'.

- Drops legacy columns: title, key_points, language (if they exist)
- Ensures 'content' column type is TEXT

Usage:
  1. Ensure DATABASE_URL is set (e.g., in your environment or .env loaded).
  2. Run: python -m backend.database.migrations.fix_summaries_table
"""

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable is not set.")
        return

    async_url = re.sub(r"^postgresql:", "postgresql+asyncpg:", database_url)
    engine = create_async_engine(async_url, echo=True, future=True)

    async with engine.begin() as conn:
        # Drop legacy columns if they exist
        print("Dropping legacy columns (if exist): title, key_points, language")
        await conn.execute(text("ALTER TABLE summaries DROP COLUMN IF EXISTS title"))
        await conn.execute(text("ALTER TABLE summaries DROP COLUMN IF EXISTS key_points"))
        await conn.execute(text("ALTER TABLE summaries DROP COLUMN IF EXISTS language"))

        # Ensure content is TEXT (safe cast from varchar)
        print("Ensuring 'content' column is of type TEXT")
        await conn.execute(text("ALTER TABLE summaries ALTER COLUMN content TYPE text USING content::text"))

    await engine.dispose()
    print("Migration completed: summaries table aligned with model.")

if __name__ == "__main__":
    asyncio.run(main())
