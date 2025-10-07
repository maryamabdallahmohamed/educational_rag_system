"""
Verification script to check TutorAgent tool collection
Run with: python verify_tutor_tools.py
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def verify_tutor_agent_tools():
    """Verify that all expected tools are available in TutorAgent"""
    print("🔍 Verifying TutorAgent tool collection...")
    
    try:
        # Mock the LLM to avoid external dependencies
        import unittest.mock
        with unittest.mock.patch('backend.models.llms.groq_llm.GroqLLM'):
            from backend.core.agents.tutor_agent import TutorAgent
            
            # Initialize TutorAgent
            agent = TutorAgent()
            
            print(f"✅ TutorAgent initialized with {len(agent.handlers)} handlers")
            print(f"✅ Collected {len(agent.tools)} tools")
            
            # List all available tools
            print("\n📋 Available Tools:")
            for i, tool in enumerate(agent.tools, 1):
                print(f"   {i}. {tool.name}")
                print(f"      Description: {tool.description}")
                print()
            
            # Verify expected tools
            expected_tools = [
                "manage_tutoring_session",
                "manage_learner_model", 
                "log_interaction",
                "request_content_adaptation",
                "generate_explanation",
                "generate_practice"
            ]
            
            available_tool_names = [tool.name for tool in agent.tools]
            
            print("🎯 Tool Verification:")
            all_present = True
            for expected_tool in expected_tools:
                if expected_tool in available_tool_names:
                    print(f"   ✅ {expected_tool}")
                else:
                    print(f"   ❌ {expected_tool} - MISSING")
                    all_present = False
            
            print("\n🔧 Handler Verification:")
            expected_handlers = [
                "SessionManagerHandler",
                "LearnerModelManagerHandler",
                "InteractionLoggerHandler", 
                "CPABridgeHandler",
                "ExplanationEngineHandler",
                "PracticeGeneratorHandler"
            ]
            
            available_handlers = [type(handler).__name__ for handler in agent.handlers]
            
            for expected_handler in expected_handlers:
                if expected_handler in available_handlers:
                    print(f"   ✅ {expected_handler}")
                else:
                    print(f"   ❌ {expected_handler} - MISSING")
                    all_present = False
            
            if all_present:
                print("\n🎉 All tools and handlers are properly configured!")
                print("TutorAgent is ready for comprehensive tutoring capabilities:")
                print("  • Session management and learner context")
                print("  • Performance tracking and analytics")
                print("  • Personalized explanation generation")
                print("  • Adaptive practice problem creation") 
                print("  • Content adaptation via CPA integration")
                print("  • Detailed interaction logging")
            else:
                print("\n⚠️ Some tools or handlers are missing - check configuration")
            
            return all_present
            
    except Exception as e:
        print(f"❌ TutorAgent verification failed: {e}")
        return False


if __name__ == "__main__":
    verify_tutor_agent_tools()
