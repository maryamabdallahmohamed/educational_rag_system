from backend.core.states.graph_states import  Summary, QAResponse , LearningUnit

def extract_data_from_summary(summary: Summary) -> dict:
    return {
        "summary": summary.summary,
        "learning_units": summary.learning_units,
    }

def extract_data_from_qa_response(qa_response: QAResponse) -> dict:
    return {
        "qa_pairs": qa_response.qa_pairs,
        "total_questions": qa_response.total_questions,
    }

def extract_data_from_learning_unit(learning_unit: LearningUnit) -> dict:
    return {
        "title": learning_unit.title,
        "subtopics": learning_unit.subtopics,
        "detailed_explanation": learning_unit.detailed_explanation,
        "key_points": learning_unit.key_points,
        "difficulty_level": learning_unit.difficulty_level,
        "learning_objectives": learning_unit.learning_objectives,
        "keywords": learning_unit.keywords,
    }

