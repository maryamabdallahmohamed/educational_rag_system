#!/usr/bin/env python3
"""
Database Tables Verification Script

Checks if the required database tables exist for TutorAgent testing.
"""

import asyncio
import sys
import os

def check_database_tables():
    """Check if required database tables exist"""
    
    print("📋 DATABASE TABLES VERIFICATION")
    print("="*60)
    
    try:
        from backend.database.db import NeonDatabase
        from sqlalchemy import text
        
        # Initialize database
        NeonDatabase.init()
        
        print("🔧 Database connection initialized")
        
        # Required tables for TutorAgent
        required_tables = [
            'learner_profiles',
            'tutoring_sessions', 
            'learner_interactions',
            'content_processor_agent',
            'chunks',
            'documents'
        ]
        
        print(f"\n📊 Checking {len(required_tables)} required tables...")
        
        async def check_tables():
            session = NeonDatabase.get_session()
            try:
                table_status = {}
                
                for table in required_tables:
                    try:
                        # Check if table exists
                        result = await session.execute(
                            text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
                        )
                        exists = result.scalar()
                        table_status[table] = exists
                        
                        status = "✅" if exists else "❌"
                        print(f"   {status} {table}")
                        
                    except Exception as e:
                        table_status[table] = False
                        print(f"   ❌ {table} (Error: {e})")
                
                return table_status
                
            finally:
                await session.close()
        
        # Run async check
        table_status = asyncio.run(check_tables())
        
        # Summary
        existing_tables = sum(1 for exists in table_status.values() if exists)
        total_tables = len(required_tables)
        
        print(f"\n📊 Table Status: {existing_tables}/{total_tables} tables exist")
        
        if existing_tables == total_tables:
            print("✅ All required tables are present!")
            return True
        else:
            missing_tables = [table for table, exists in table_status.items() if not exists]
            print(f"❌ Missing tables: {missing_tables}")
            print("\n🔧 To create missing tables:")
            print("   1. Set up your DATABASE_URL in .env file")
            print("   2. Run database migrations/setup script")
            print("   3. Or create tables manually using SQLAlchemy models")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import database modules: {e}")
        print("\n💡 This is expected if pgvector is not installed.")
        print("   The mock profile testing can still work without database.")
        return False
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Possible solutions:")
        print("   • Check DATABASE_URL in .env file")
        print("   • Ensure PostgreSQL database is running") 
        print("   • Install required dependencies (pgvector, asyncpg)")
        return False

def show_testing_options():
    """Show available testing options based on database status"""
    
    print(f"\n" + "="*60)
    print("🧪 AVAILABLE TESTING OPTIONS")
    print("="*60)
    
    print(f"\n✅ Always Available (No Database Required):")
    print(f"   • Mock Profile Testing: python test_personalization.py")
    print(f"   • Hierarchy Verification: python verify_hierarchy.py")
    print(f"   • Profile Generation: python generate_mock_profiles.py")
    print(f"   • View Mock Profiles: type tests\\test_profile_ids.txt")
    
    print(f"\n🔧 Database Required:")
    print(f"   • Real Profile Creation: python generate_test_profiles.py")
    print(f"   • Full TutorAgent Testing: python quick_test_tutor.py")
    print(f"   • Complete Flow Testing: python test_complete_flow.py")
    print(f"   • Manual TutorAgent Tests: python tests/manual_test_tutor.py")
    
    print(f"\n📋 Recommended Testing Sequence:")
    print(f"   1. Start with: python test_personalization.py")
    print(f"   2. Generate profiles: python generate_mock_profiles.py") 
    print(f"   3. Verify routing: python verify_hierarchy.py")
    print(f"   4. (If DB available) Full test: python quick_test_tutor.py")

def main():
    """Main verification function"""
    
    print("🚀 TUTOR AGENT DATABASE VERIFICATION")
    print("="*80)
    
    db_available = check_database_tables()
    show_testing_options()
    
    print(f"\n" + "="*80)
    print("📊 VERIFICATION SUMMARY")
    print("="*80)
    
    if db_available:
        print("✅ Database is ready for full TutorAgent testing!")
        print("\n🎯 You can now:")
        print("   • Create real learner profiles in the database")
        print("   • Test complete Router → CPA → TutorAgent flow")  
        print("   • Verify LangSmith tracing integration")
        print("   • Run comprehensive personalization tests")
    else:
        print("⚠️ Database not available, but mock testing is ready!")
        print("\n🎯 You can still:")
        print("   • Test TutorAgent personalization logic")
        print("   • Verify hierarchical routing decisions")
        print("   • Use mock profiles for development testing")
        print("   • Prepare for database integration later")
    
    print(f"\n📁 Test Files Created:")
    print(f"   • tests/test_profile_ids.txt - Mock learner profile IDs")
    print(f"   • tests/test_scenarios.txt - Personalization test scenarios")
    print(f"   • Test scripts for various components")
    
    print(f"\n🎉 TutorAgent testing infrastructure is ready!")

if __name__ == "__main__":
    main()