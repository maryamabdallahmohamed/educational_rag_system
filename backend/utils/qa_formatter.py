"""
Utility module for formatting QA responses into different formats.
"""
from typing import List, Dict, Any


def format_qa_to_markdown(qa_data: List[Dict[str, Any]]) -> str:
    """
    Convert QA JSON data to a nicely formatted Markdown document.
    
    Args:
        qa_data: List of question-answer dictionaries with 'question', 'options', and 'answer' keys
        
    Returns:
        Formatted Markdown string
    """
    if not qa_data:
        return "# Questions and Answers\n\nNo questions available."
    
    markdown_lines = [
        "# Questions",
        "",
        f"**Total Questions:** {len(qa_data)}",
        "",
        "---",
        ""
    ]
    
    for idx, qa_item in enumerate(qa_data, start=1):
        question = qa_item.get("question", "")
        
        # Add question header
        markdown_lines.append(f"## Question {idx}")
        markdown_lines.append("")
        markdown_lines.append(f"**{question}**")
        markdown_lines.append("")
        
    
    return "\n".join(markdown_lines)


def format_qa_to_markdown_compact(qa_data: List[Dict[str, Any]]) -> str:
    """
    Convert QA JSON data to a compact Markdown format.
    
    Args:
        qa_data: List of question-answer dictionaries
        
    Returns:
        Compact formatted Markdown string
    """
    if not qa_data:
        return "# Questions\n\nNo questions available."
    
    markdown_lines = [
        "# Questions",
        "",
        f"*{len(qa_data)} questions total*",
        "",
    ]
    
    for idx, qa_item in enumerate(qa_data, start=1):
        question = qa_item.get("question", "")
        
        markdown_lines.append(f"### {idx}. {question}")
        markdown_lines.append("")
        
    
    return "\n".join(markdown_lines)


def format_qa_to_markdown_quiz(qa_data: List[Dict[str, Any]]) -> str:
    """
    Convert QA JSON data to a quiz-style Markdown format (without showing answers).
    
    Args:
        qa_data: List of question-answer dictionaries
        
    Returns:
        Quiz-style Markdown string
    """
    if not qa_data:
        return "# Quiz\n\nNo questions available."
    
    markdown_lines = [
        "# Quiz",
        "",
        f"**Total Questions:** {len(qa_data)}",
        "",
        "---",
        ""
    ]
    
    # Questions section
    for idx, qa_item in enumerate(qa_data, start=1):
        question = qa_item.get("question", "")
        
        markdown_lines.append(f"**{idx}.** {question}")
        markdown_lines.append("")
    

    return "\n".join(markdown_lines)
