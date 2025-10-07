"""
Verification script to test tutor handler imports
Run with: python verify_tutor_imports.py
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def verify_tutor_handler_imports():
    """Verify that all tutor handler imports work correctly"""
    print("🔍 Verifying tutor handler imports...")
    
    try:
        # Test individual handler imports
        print("\n📦 Testing individual handler imports:")
        
        from backend.core.agents.tutor_handlers.session_manager import SessionManagerHandler
        print("   ✅ SessionManagerHandler imported successfully")
        
        from backend.core.agents.tutor_handlers.learner_model_manager import LearnerModelManagerHandler
        print("   ✅ LearnerModelManagerHandler imported successfully")
        
        from backend.core.agents.tutor_handlers.interaction_logger import InteractionLoggerHandler
        print("   ✅ InteractionLoggerHandler imported successfully")
        
        from backend.core.agents.tutor_handlers.cpa_bridge_handler import CPABridgeHandler
        print("   ✅ CPABridgeHandler imported successfully")
        
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        print("   ✅ ExplanationEngineHandler imported successfully")
        
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        print("   ✅ PracticeGeneratorHandler imported successfully")
        
        # Test module-level imports
        print("\n📦 Testing module-level imports:")
        
        from backend.core.agents.tutor_handlers import (
            SessionManagerHandler,
            LearnerModelManagerHandler,
            InteractionLoggerHandler,
            CPABridgeHandler,
            ExplanationEngineHandler,
            PracticeGeneratorHandler
        )
        print("   ✅ All handlers imported from module successfully")
        
        # Test __all__ contains expected items
        from backend.core.agents import tutor_handlers
        expected_handlers = [
            "SessionManagerHandler",
            "LearnerModelManagerHandler", 
            "InteractionLoggerHandler",
            "CPABridgeHandler",
            "ExplanationEngineHandler",
            "PracticeGeneratorHandler"
        ]
        
        print("\n📋 Verifying __all__ exports:")
        for handler_name in expected_handlers:
            if handler_name in tutor_handlers.__all__:
                print(f"   ✅ {handler_name} in __all__")
            else:
                print(f"   ❌ {handler_name} missing from __all__")
        
        # Test agent imports
        print("\n🤖 Testing agent imports:")
        
        from backend.core.agents import TutorAgent, ContentProcessorAgent
        print("   ✅ TutorAgent and ContentProcessorAgent imported from agents module")
        
        print("\n🎉 All imports working correctly!")
        print("✨ Tutor handlers are properly exposed and ready for use!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    verify_tutor_handler_imports()
