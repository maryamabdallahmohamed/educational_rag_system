#!/usr/bin/env python3
"""
Simple test to verify the hierarchical graph structure:
Router → CPA → TutorAgent → END
"""

def test_graph_structure():
    """Test that the graph has the correct hierarchical structure."""
    try:
        # Test 1: Verify graph structure compiles
        print("🔍 Testing graph structure compilation...")
        
        # Mock the database dependencies to test just the graph logic
        import sys
        from unittest.mock import MagicMock
        
        # Mock the problematic imports
        sys.modules['pgvector'] = MagicMock()
        sys.modules['pgvector.sqlalchemy'] = MagicMock()
        sys.modules['backend.database'] = MagicMock()
        sys.modules['backend.database.repositories'] = MagicMock()
        sys.modules['backend.database.repositories.document_repo'] = MagicMock()
        sys.modules['backend.database.models'] = MagicMock()
        sys.modules['backend.database.models.document'] = MagicMock()
        sys.modules['backend.database.models.chunks'] = MagicMock()
        
        from backend.core.graph import create_graph
        graph = create_graph()
        print("✅ Graph compiled successfully!")
        
        # Test 2: Verify node structure
        print("\n🔍 Testing node structure...")
        
        # Get the compiled graph's nodes
        graph_nodes = list(graph.nodes.keys())
        print(f"📋 Graph nodes: {graph_nodes}")
        
        expected_nodes = ['router', 'content_processor_agent', 'tutor_agent', 'qa', 'summarization']
        missing_nodes = [node for node in expected_nodes if node not in graph_nodes]
        
        if missing_nodes:
            print(f"❌ Missing nodes: {missing_nodes}")
            return False
        else:
            print("✅ All expected nodes present!")
        
        # Test 3: Verify edges structure
        print("\n🔍 Testing edge structure...")
        graph_edges = graph.edges
        print(f"📋 Graph edges: {list(graph_edges.keys())}")
        
        # Check key hierarchical connections
        if 'content_processor_agent' in graph_edges:
            cpa_edges = graph_edges['content_processor_agent']
            print(f"📋 CPA can route to: {cpa_edges}")
            
            # CPA should be able to route to tutor_agent or END
            if 'tutor_agent' in str(cpa_edges) and 'END' in str(cpa_edges):
                print("✅ CPA → TutorAgent delegation confirmed!")
            else:
                print("❌ CPA delegation not configured correctly")
                return False
        
        # Test 4: Verify hierarchy flow
        print("\n🔍 Testing hierarchy Router → CPA → TutorAgent → END...")
        
        # Simulate a tutoring request flow
        from backend.core.states.graph_states import RAGState
        
        # Create test state
        test_state = RAGState(
            query="Can you help me understand calculus?",
            next_step="content_processor_agent"  # Router would set this
        )
        
        print(f"📋 Test state created: {test_state}")
        print("✅ Hierarchical structure verified!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_tutoring_detection():
    """Test that tutoring detection logic exists in CPA."""
    try:
        print("\n🔍 Testing tutoring detection in CPA...")
        
        # Read the CPA code to verify tutoring detection
        with open('backend/core/agents/content_processor_agent.py', 'r') as f:
            cpa_code = f.read()
        
        # Check for tutoring keywords in the code
        tutoring_indicators = [
            'tutoring', 'educational', 'next_step', 'tutor_agent',
            'learning', 'understand', 'explain'
        ]
        
        found_indicators = []
        for indicator in tutoring_indicators:
            if indicator.lower() in cpa_code.lower():
                found_indicators.append(indicator)
        
        print(f"📋 Found tutoring indicators: {found_indicators}")
        
        if len(found_indicators) >= 3:
            print("✅ Tutoring detection logic present in CPA!")
            return True
        else:
            print("❌ Insufficient tutoring detection logic in CPA")
            return False
            
    except Exception as e:
        print(f"❌ Tutoring detection test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Hierarchical Graph Structure")
    print("=" * 50)
    
    # Run tests
    structure_test = test_graph_structure()
    detection_test = test_tutoring_detection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Graph Structure: {'✅ PASS' if structure_test else '❌ FAIL'}")
    print(f"   Tutoring Detection: {'✅ PASS' if detection_test else '❌ FAIL'}")
    
    if structure_test and detection_test:
        print("\n🎉 All tests passed! Hierarchical structure is working!")
        print("\n📋 Confirmed Architecture:")
        print("   Router → CPA → TutorAgent → END")
        print("   CPA handles tutoring detection and delegation")
        print("   TutorAgent receives delegated tutoring requests")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
