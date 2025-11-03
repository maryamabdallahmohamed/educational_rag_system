#!/usr/bin/env python3
"""
Test script for tutoring request detection in ContentProcessorAgent
"""

def _is_tutoring_request(query: str) -> bool:
    """Determine if the query is a tutoring request that should be handled by TutorAgent"""
    tutoring_indicators = [
        # Learning and educational requests
        'explain', 'teach', 'learn', 'understand', 'help me with',
        'how to', 'why does', 'what is', 'can you help',
        
        # Subject-specific terms
        'math', 'mathematics', 'algebra', 'calculus', 'geometry',
        'physics', 'chemistry', 'biology', 'science',
        'history', 'english', 'literature', 'grammar',
        
        # Practice and assessment
        'practice', 'exercise', 'quiz', 'test', 'homework',
        'solve', 'calculate', 'find the answer',
        
        # Tutoring interaction patterns
        'step by step', 'break down', 'simplify', 'make it easier',
        'i don\'t understand', 'confused', 'struggling',
        
        # Personalized learning
        'adapt', 'personalize', 'my level', 'difficulty',
        'visual', 'examples', 'practice problems'
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in tutoring_indicators)


def test_tutoring_detection():
    """Test the tutoring detection logic"""
    
    # Test cases that should route to TutorAgent
    tutoring_queries = [
        "Explain photosynthesis to me",
        "Help me with algebra",
        "I don't understand fractions",
        "Teach me about calculus",
        "Can you help me solve this math problem?",
        "Give me practice problems on quadratic equations",
        "Make this easier to understand",
        "Step by step explanation please",
        "I'm struggling with chemistry",
        "Adapt to my learning style"
    ]
    
    # Test cases that should NOT route to TutorAgent (handled by CPA directly)
    non_tutoring_queries = [
        "Upload this document",
        "Summarize chapter 3",
        "Create learning units from this file",
        "Hello, how are you?",
        "What's the weather today?",
        "Process this document please",
        "Generate structured lessons"
    ]
    
    print("🔍 Testing Tutoring Detection Logic")
    print("=" * 50)
    
    print("\n✅ Tutoring Queries (should detect as tutoring):")
    for i, query in enumerate(tutoring_queries, 1):
        result = _is_tutoring_request(query)
        status = "✓" if result else "✗"
        print(f"  {i:2}. {status} \"{query}\" -> {result}")
    
    print("\n❌ Non-Tutoring Queries (should NOT detect as tutoring):")
    for i, query in enumerate(non_tutoring_queries, 1):
        result = _is_tutoring_request(query)
        status = "✓" if not result else "✗"
        print(f"  {i:2}. {status} \"{query}\" -> {result}")
    
    # Calculate accuracy
    tutoring_correct = sum(1 for q in tutoring_queries if _is_tutoring_request(q))
    non_tutoring_correct = sum(1 for q in non_tutoring_queries if not _is_tutoring_request(q))
    total_correct = tutoring_correct + non_tutoring_correct
    total_queries = len(tutoring_queries) + len(non_tutoring_queries)
    accuracy = (total_correct / total_queries) * 100
    
    print(f"\n📊 Detection Accuracy:")
    print(f"   Tutoring queries correctly identified: {tutoring_correct}/{len(tutoring_queries)}")
    print(f"   Non-tutoring queries correctly identified: {non_tutoring_correct}/{len(non_tutoring_queries)}")
    print(f"   Overall accuracy: {accuracy:.1f}% ({total_correct}/{total_queries})")
    
    if accuracy >= 90:
        print("✅ Detection logic working well!")
    elif accuracy >= 70:
        print("⚠️  Detection logic needs improvement")
    else:
        print("❌ Detection logic needs significant improvement")


if __name__ == "__main__":
    test_tutoring_detection()
