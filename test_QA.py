import asyncio
from backend.database.db import NeonDatabase, Base
from backend.database.models.questionanswer import QuestionAnswer
from backend.database.models.qa_Item import QuestionAnswerItem
from backend.database.repositories.qa_item_repo import QuestionAnswerItemRepository
from backend.database.repositories.qa_repo import QuestionAnswerRepository


async def create_tables():
    """Create all database tables."""
    engine = NeonDatabase.init()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables created successfully")


async def test_basic_insert():
    """Test basic insertion into QuestionAnswer table."""
    session = NeonDatabase.get_session()
    
    try:
        # Create a QuestionAnswer
        qa_data = {
            "questions": [
                {"id": 1, "question": "What is Python?", "answer": "A programming language"},
                {"id": 2, "question": "What is SQLAlchemy?", "answer": "An ORM for Python"}
            ]
        }
        
        qa = QuestionAnswer(qa_data=qa_data)
        session.add(qa)
        await session.commit()
        await session.refresh(qa)
        
        print(f"✓ Created QuestionAnswer with ID: {qa.id}")
        print(f"  Data: {qa.qa_data}")
        
        return qa.id
        
    except Exception as e:
        print(f"✗ Error in basic insert: {e}")
        await session.rollback()
        return None
    finally:
        await session.close()


async def test_with_items(qa_id):
    """Test creating QuestionAnswerItems."""
    session = NeonDatabase.get_session()
    
    try:
        # Create items for each question
        item1 = QuestionAnswerItem(
            question_answer_id=qa_id,
            qa_index=0,
            question_text="What is Python?",
            answer_text="A programming language"
        )
        
        item2 = QuestionAnswerItem(
            question_answer_id=qa_id,
            qa_index=1,
            question_text="What is SQLAlchemy?",
            answer_text="An ORM for Python"
        )
        
        session.add_all([item1, item2])
        await session.commit()
        
        print(f"✓ Created 2 QuestionAnswerItems for QuestionAnswer {qa_id}")
        print(f"  Item 1 ID: {item1.id}")
        print(f"  Item 2 ID: {item2.id}")
        
    except Exception as e:
        print(f"✗ Error creating items: {e}")
        await session.rollback()
    finally:
        await session.close()


async def test_repository():
    """Test using repositories."""
    session = NeonDatabase.get_session()
    
    try:
        qa_repo = QuestionAnswerRepository(session)
        item_repo = QuestionAnswerItemRepository(session)
        
        # Create using repository
        qa_data = {
            "survey": "Customer Feedback",
            "responses": [
                {"q": "Rate our service", "a": "5/5"},
                {"q": "Would you recommend us?", "a": "Yes"}
            ]
        }
        
        qa = qa_repo.create(qa_data)
        await session.commit()
        print(f"✓ Repository created QuestionAnswer with ID: {qa.id}")
        
        # Create items using repository
        item = item_repo.create(
            question_answer_id=qa.id,
            qa_index=0,
            question_text="Rate our service",
            answer_text="5/5"
        )
        await session.commit()
        print(f"✓ Repository created QuestionAnswerItem with ID: {item.id}")
        
        # Get by ID
        retrieved = qa_repo.get_by_id(qa.id)
        print(f"✓ Retrieved QuestionAnswer: {retrieved.qa_data['survey']}")
        
        # Get all items for this QA
        items = item_repo.get_by_question_answer_id(qa.id)
        print(f"✓ Found {len(items)} items for QuestionAnswer {qa.id}")
        
    except Exception as e:
        print(f"✗ Error in repository test: {e}")
        await session.rollback()
    finally:
        await session.close()


async def test_query_all():
    """Test querying all records."""
    session = NeonDatabase.get_session()
    
    try:
        from sqlalchemy import select
        
        # Query all QuestionAnswers
        result = await session.execute(select(QuestionAnswer))
        all_qas = result.scalars().all()
        print(f"\n✓ Total QuestionAnswers in database: {len(all_qas)}")
        
        for qa in all_qas:
            print(f"  - ID: {qa.id}")
            print(f"    Created: {qa.created_at}")
            print(f"    Data keys: {list(qa.qa_data.keys())}")
        
        # Query all items
        result = await session.execute(select(QuestionAnswerItem))
        all_items = result.scalars().all()
        print(f"\n✓ Total QuestionAnswerItems in database: {len(all_items)}")
        
        for item in all_items:
            print(f"  - ID: {item.id}")
            print(f"    Question: {item.question_text}")
            print(f"    Answer: {item.answer_text}")
        
    except Exception as e:
        print(f"✗ Error querying: {e}")
    finally:
        await session.close()


async def cleanup():
    """Dispose database connection."""
    await NeonDatabase.dispose()
    print("\n✓ Database connection closed")


async def main():
    """Run all tests."""
    print("Starting database tests...\n")
    
    # Create tables
    await create_tables()
    print()
    
    # Test basic insert
    qa_id = await test_basic_insert()
    print()
    
    # Test with items
    if qa_id:
        await test_with_items(qa_id)
        print()
    
    # Test repository pattern
    await test_repository()
    print()
    
    # Query all records
    await test_query_all()
    
    # Cleanup
    await cleanup()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())