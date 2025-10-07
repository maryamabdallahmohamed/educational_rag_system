"""
Verification script for Tutor Agent database tables.
Run this after populate_db.py to verify the new tables are created correctly.
"""
import asyncio
from backend.database.db import NeonDatabase
from sqlalchemy import text

async def verify_tutor_tables():
    """Verify that all tutor agent tables are created with correct structure"""
    db = NeonDatabase()
    engine = db.init()
    
    async with engine.connect() as conn:
        print("🔍 Verifying Tutor Agent database tables...\n")
        
        # Check learner_profiles table
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'learner_profiles' 
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            if columns:
                print("✅ learner_profiles table:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"   - {col[0]}: {col[1]} ({nullable})")
            else:
                print("❌ learner_profiles table not found")
        except Exception as e:
            print(f"❌ Error checking learner_profiles: {e}")
        
        print()
        
        # Check tutoring_sessions table  
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'tutoring_sessions' 
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            if columns:
                print("✅ tutoring_sessions table:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"   - {col[0]}: {col[1]} ({nullable})")
            else:
                print("❌ tutoring_sessions table not found")
        except Exception as e:
            print(f"❌ Error checking tutoring_sessions: {e}")
        
        print()
        
        # Check learner_interactions table
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'learner_interactions' 
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            if columns:
                print("✅ learner_interactions table:")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"   - {col[0]}: {col[1]} ({nullable})")
            else:
                print("❌ learner_interactions table not found")
        except Exception as e:
            print(f"❌ Error checking learner_interactions: {e}")
        
        print()
        
        # Check foreign key constraints
        try:
            result = await conn.execute(text("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('learner_profiles', 'tutoring_sessions', 'learner_interactions')
                ORDER BY tc.table_name;
            """))
            constraints = result.fetchall()
            if constraints:
                print("🔗 Foreign Key Constraints:")
                for constraint in constraints:
                    print(f"   {constraint[0]}.{constraint[1]} -> {constraint[2]}.{constraint[3]} (ON DELETE {constraint[4]})")
            else:
                print("⚠️ No foreign key constraints found")
        except Exception as e:
            print(f"❌ Error checking foreign keys: {e}")
        
        print("\n🎯 Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_tutor_tables())
