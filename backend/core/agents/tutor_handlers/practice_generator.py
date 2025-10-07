import json
import asyncio
import time
import re
from typing import Dict, Any, Optional, List
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from backend.core.agents.base_handler import BaseHandler
from backend.models.llms.groq_llm import GroqLLM
from backend.database.repositories.learning_unit_repo import LearningUnitRepository
from backend.database.db import NeonDatabase
from backend.utils.logger_config import get_logger


class PracticeGeneratorHandler(BaseHandler):
    """
    Generates practice problems and assessments based on learning units and learner progress
    Adapts difficulty based on learner performance and preferences
    """

    def __init__(self):
        super().__init__()
        self.llm = GroqLLM().llm
        
        # Define practice types and their characteristics
        self.practice_types = {
            "problems": {
                "description": "Mathematical or conceptual problems to solve",
                "format": "numbered_problems",
                "include_solutions": True
            },
            "quiz": {
                "description": "Multiple choice or short answer questions",
                "format": "quiz_format",
                "include_solutions": True
            },
            "exercises": {
                "description": "Hands-on activities and applied practice",
                "format": "step_by_step",
                "include_solutions": False
            },
            "assessment": {
                "description": "Comprehensive evaluation questions",
                "format": "formal_assessment",
                "include_solutions": True
            },
            "flashcards": {
                "description": "Question-answer pairs for memorization",
                "format": "card_format",
                "include_solutions": True
            }
        }
        
        # Difficulty level characteristics
        self.difficulty_levels = {
            "easy": {
                "complexity": "Basic concepts and straightforward applications",
                "thinking_level": "Knowledge and comprehension",
                "steps": "1-2 steps to solve",
                "vocabulary": "Simple, everyday language"
            },
            "medium": {
                "complexity": "Moderate complexity with some analysis required",
                "thinking_level": "Application and analysis",
                "steps": "3-4 steps to solve",
                "vocabulary": "Standard academic vocabulary"
            },
            "hard": {
                "complexity": "Complex problems requiring synthesis",
                "thinking_level": "Synthesis and evaluation",
                "steps": "5+ steps, multi-step reasoning",
                "vocabulary": "Advanced technical terminology"
            }
        }
        
    def tool(self) -> Tool:
        """Return configured LangChain Tool for practice generation"""
        return Tool(
            name="generate_practice",
            description="Generate practice problems, exercises, or assessments based on topics. Adapts difficulty to learner level.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, practice_request: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            return asyncio.run(self._process(practice_request))
        except Exception as e:
            return self._handle_error(e, "practice_generation")
    
    async def _process(self, practice_request: str) -> str:
        """Process practice generation request"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting practice generation: {practice_request}")

            if not self._validate_state():
                return "Unable to generate practice - no learner context available"

            # Parse the practice request
            request_data = self._parse_practice_request(practice_request)
            if not request_data:
                return "Invalid practice request format. Please specify the topic and type of practice needed."

            # Get learner profile from current state
            learner_profile = self.current_state.get("learner_profile", {})
            if not learner_profile:
                self.logger.warning("No learner profile available, using default difficulty")
                learner_profile = self._get_default_profile()

            # Determine appropriate difficulty level
            difficulty = self._determine_difficulty_level(
                learner_profile, 
                request_data.get("difficulty_level")
            )

            # Fetch topic content if learning unit provided
            topic_content = await self._fetch_topic_content(
                request_data.get("learning_unit_id"),
                request_data.get("topic")
            )

            # Generate practice items
            practice_items = await self._generate_practice_items(
                request_data["topic"],
                topic_content,
                difficulty,
                request_data.get("num_items", 5),
                request_data["practice_type"]
            )

            # Format the practice output
            include_answers = request_data.get("include_answers", True)
            formatted_practice = self._format_practice_output(practice_items, include_answers)

            # Store practice in state for future reference
            if "interaction_history" not in self.current_state:
                self.current_state["interaction_history"] = []
            
            self.current_state["interaction_history"].append({
                "type": "practice_generation",
                "topic": request_data["topic"],
                "practice_type": request_data["practice_type"],
                "difficulty": difficulty,
                "num_items": len(practice_items),
                "practice_set": practice_items,
                "timestamp": time.time()
            })

            processing_time = time.time() - start_time
            self.logger.info(f"Practice generated in {processing_time:.2f}s: {len(practice_items)} {difficulty} {request_data['practice_type']}")
            
            return formatted_practice

        except Exception as e:
            self.logger.error(f"Error generating practice: {e}")
            return self._handle_error(e, "practice_generation")

    def _parse_practice_request(self, request: str) -> Optional[Dict[str, Any]]:
        """Parse practice request string into structured data"""
        try:
            # Try to parse as JSON first
            if request.strip().startswith('{'):
                return json.loads(request)
            
            # Parse natural language request
            request_lower = request.lower()
            parsed_request = {
                "topic": "",
                "practice_type": "problems",
                "num_items": 5,
                "difficulty_level": None,
                "learning_unit_id": None,
                "include_answers": True
            }
            
            # Extract topic
            topic_patterns = [
                r"(?:practice|problems|quiz|exercises?|assessment)\s+(?:for|on|about)\s+(.+?)(?:\s+using|\s+with|\s+\d+|$)",
                r"generate\s+(.+?)\s+(?:practice|problems|quiz|exercises?|assessment)",
                r"topic:\s*(.+?)(?:\s+type:|\s+difficulty:|\s+items:|,|$)",
                r"(.+?)\s+(?:practice|problems|quiz|exercises?|assessment)"
            ]
            
            topic_found = False
            for pattern in topic_patterns:
                match = re.search(pattern, request_lower)
                if match:
                    parsed_request["topic"] = match.group(1).strip()
                    topic_found = True
                    break
            
            # If no pattern matched, try to extract topic differently
            if not topic_found:
                # Remove common instruction words and extract remaining content
                topic = re.sub(r'^(generate|create|make|give me)\s+', '', request, flags=re.IGNORECASE)
                topic = re.sub(r'\s+(practice|problems|quiz|exercises?|assessment).*$', '', topic, flags=re.IGNORECASE)
                if topic.strip():
                    parsed_request["topic"] = topic.strip()
            
            # Extract practice type
            type_mapping = {
                "problem": "problems", "problems": "problems", "math": "problems",
                "quiz": "quiz", "test": "quiz", "questions": "quiz",
                "exercise": "exercises", "exercises": "exercises", "activity": "exercises",
                "assessment": "assessment", "exam": "assessment", "evaluation": "assessment",
                "flashcard": "flashcards", "cards": "flashcards", "memorize": "flashcards"
            }
            
            for keyword, ptype in type_mapping.items():
                if keyword in request_lower:
                    parsed_request["practice_type"] = ptype
                    break
            
            # Extract number of items
            num_match = re.search(r'(\d+)\s+(?:items?|problems?|questions?|exercises?)', request_lower)
            if num_match:
                parsed_request["num_items"] = int(num_match.group(1))
            
            # Extract difficulty level
            if any(word in request_lower for word in ["easy", "simple", "basic"]):
                parsed_request["difficulty_level"] = "easy"
            elif any(word in request_lower for word in ["medium", "moderate", "intermediate"]):
                parsed_request["difficulty_level"] = "medium"
            elif any(word in request_lower for word in ["hard", "difficult", "advanced", "challenging"]):
                parsed_request["difficulty_level"] = "hard"
            
            # Extract learning unit ID
            unit_match = re.search(r"unit[_\s]*id[:\s]*([^\s,]+)", request_lower)
            if unit_match:
                parsed_request["learning_unit_id"] = unit_match.group(1)
            
            # Check if answers should be included
            if any(phrase in request_lower for phrase in ["no answers", "without answers", "hide answers"]):
                parsed_request["include_answers"] = False
            
            self.logger.info(f"Parsed practice request: {parsed_request}")
            return parsed_request if parsed_request["topic"] else None
            
        except Exception as e:
            self.logger.error(f"Error parsing practice request: {e}")
            return None

    def _determine_difficulty_level(self, learner_profile: Dict[str, Any], requested_difficulty: str = None) -> str:
        """Determine appropriate difficulty level based on learner profile and request"""
        
        # If specific difficulty requested and it's valid, use it
        if requested_difficulty and requested_difficulty in self.difficulty_levels:
            self.logger.info(f"Using requested difficulty level: {requested_difficulty}")
            return requested_difficulty
        
        # Get learner characteristics
        performance_metrics = learner_profile.get("performance_metrics", {})
        accuracy_rate = performance_metrics.get("accuracy_rate", 0.5)
        grade_level = learner_profile.get("grade_level", "Unknown")
        learning_struggles = learner_profile.get("learning_struggles", [])
        mastered_topics = learner_profile.get("mastered_topics", [])
        difficulty_preference = learner_profile.get("difficulty_preference", "medium")
        
        # Difficulty determination logic
        
        # 1. Check for learning struggles - use easier content
        if learning_struggles:
            self.logger.info("Using easy difficulty due to learning struggles")
            return "easy"
        
        # 2. Use accuracy rate as primary indicator
        if accuracy_rate < 0.6:  # Struggling
            self.logger.info(f"Using easy difficulty due to low accuracy rate: {accuracy_rate}")
            return "easy"
        elif accuracy_rate > 0.85:  # Performing well
            self.logger.info(f"Using hard difficulty due to high accuracy rate: {accuracy_rate}")
            return "hard"
        
        # 3. Consider grade level for appropriate baseline
        grade_num = self._extract_grade_number(grade_level)
        if grade_num:
            if grade_num <= 6:  # Elementary
                baseline = "easy"
            elif grade_num <= 9:  # Middle school
                baseline = "medium"
            else:  # High school and above
                baseline = "medium"  # Can scale to hard based on performance
            
            # Adjust baseline based on performance
            if accuracy_rate > 0.75 and baseline != "hard":
                baseline = "hard" if baseline == "medium" else "medium"
            elif accuracy_rate < 0.65 and baseline != "easy":
                baseline = "easy" if baseline == "medium" else "medium"
            
            self.logger.info(f"Using {baseline} difficulty based on grade level {grade_level} and performance")
            return baseline
        
        # 4. Use explicit difficulty preference if available
        if difficulty_preference in self.difficulty_levels:
            self.logger.info(f"Using learner's preferred difficulty: {difficulty_preference}")
            return difficulty_preference
        
        # 5. Default to medium
        self.logger.info("Using default medium difficulty")
        return "medium"

    async def _fetch_topic_content(self, learning_unit_id: str = None, topic: str = None) -> Dict[str, Any]:
        """Fetch topic content from learning units or provide default structure"""
        content = {
            "title": topic or "General Topic",
            "detailed_explanation": "",
            "key_points": [],
            "learning_objectives": [],
            "keywords": [],
            "difficulty_level": "medium",
            "subject": "General"
        }
        
        if learning_unit_id:
            try:
                async with NeonDatabase.get_session() as session:
                    repo = LearningUnitRepository(session)
                    unit = await repo.get_by_id(learning_unit_id)
                    
                    if unit:
                        content.update({
                            "title": unit.title,
                            "detailed_explanation": unit.detailed_explanation or "",
                            "key_points": unit.key_points or [],
                            "learning_objectives": unit.learning_objectives or [],
                            "keywords": unit.keywords or [],
                            "difficulty_level": unit.difficulty_level or "medium",
                            "subject": unit.subject or "General"
                        })
                        self.logger.info(f"Fetched content for learning unit: {unit.title}")
                    else:
                        self.logger.warning(f"Learning unit {learning_unit_id} not found")
                        
            except Exception as e:
                self.logger.error(f"Error fetching learning unit content: {e}")
        
        return content

    async def _generate_practice_items(self, topic: str, content: Dict[str, Any], difficulty: str, num_items: int, practice_type: str) -> List[Dict[str, Any]]:
        """Generate practice items using LLM"""
        try:
            # Create generation prompt
            prompt = self._create_practice_prompt(topic, content, difficulty, num_items, practice_type)
            
            # Generate practice items using LLM
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            
            # Extract text content from response
            if hasattr(response, 'content'):
                practice_text = response.content
            else:
                practice_text = str(response)
            
            # Parse the generated practice items
            practice_items = self._parse_generated_practice(practice_text, practice_type)
            
            self.logger.info(f"Generated {len(practice_items)} practice items")
            return practice_items
            
        except Exception as e:
            self.logger.error(f"Error generating practice items with LLM: {e}")
            # Fallback practice items
            return self._create_fallback_practice(topic, difficulty, num_items, practice_type)

    def _create_practice_prompt(self, topic: str, content: Dict[str, Any], difficulty: str, num_items: int, practice_type: str) -> str:
        """Create practice generation prompt for LLM"""
        
        difficulty_info = self.difficulty_levels[difficulty]
        practice_info = self.practice_types[practice_type]
        
        prompt = f"""You are an expert educational content creator. Generate {num_items} {practice_type} for the topic "{topic}".

Topic Content:
- Title: {content['title']}
- Subject: {content['subject']}
- Key Points: {', '.join(content['key_points']) if content['key_points'] else 'Not specified'}
- Learning Objectives: {', '.join(content['learning_objectives']) if content['learning_objectives'] else 'Not specified'}

Difficulty Level: {difficulty.upper()}
- Complexity: {difficulty_info['complexity']}
- Thinking Level: {difficulty_info['thinking_level']}
- Solution Steps: {difficulty_info['steps']}
- Vocabulary: {difficulty_info['vocabulary']}

Practice Type: {practice_type.upper()}
- Description: {practice_info['description']}
- Format: {practice_info['format']}

Generation Guidelines:"""
        
        if practice_type == "problems":
            prompt += f"""
- Create {num_items} mathematical or conceptual problems
- Include clear problem statements
- Provide step-by-step solutions
- Vary problem types and approaches
- Use real-world contexts when appropriate"""
            
        elif practice_type == "quiz":
            prompt += f"""
- Create {num_items} multiple choice or short answer questions
- Include 4 answer choices for multiple choice (A, B, C, D)
- Mark the correct answer clearly
- Include brief explanations for correct answers
- Cover different aspects of the topic"""
            
        elif practice_type == "exercises":
            prompt += f"""
- Create {num_items} hands-on activities or practical exercises
- Include clear instructions and steps
- Specify materials or tools needed
- Provide learning objectives for each exercise
- Focus on application and practice"""
            
        elif practice_type == "assessment":
            prompt += f"""
- Create {num_items} comprehensive evaluation questions
- Include different question types (short answer, essay, problem-solving)
- Provide rubrics or answer guidelines
- Cover key learning objectives
- Ensure questions test understanding, not just memorization"""
            
        elif practice_type == "flashcards":
            prompt += f"""
- Create {num_items} question-answer pairs for memorization
- Keep questions concise and focused
- Provide clear, accurate answers
- Include key terms and definitions
- Cover important concepts and facts"""
        
        prompt += f"""

Output Format:
Please structure your response as a JSON array where each item has:
{{
  "id": "item_number",
  "question": "the question or problem statement",
  "answer": "the correct answer or solution",
  "explanation": "brief explanation of the answer",
  "difficulty": "{difficulty}",
  "type": "{practice_type}"
}}

Generate exactly {num_items} items following this format. Ensure variety and educational value.

Begin generation now:"""
        
        return prompt

    def _parse_generated_practice(self, practice_text: str, practice_type: str) -> List[Dict[str, Any]]:
        """Parse generated practice text into structured items"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\[.*\]', practice_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                practice_items = json.loads(json_str)
                return practice_items
            
            # Fallback: parse text format
            return self._parse_text_format(practice_text, practice_type)
            
        except Exception as e:
            self.logger.error(f"Error parsing generated practice: {e}")
            return []

    def _parse_text_format(self, text: str, practice_type: str) -> List[Dict[str, Any]]:
        """Parse text format when JSON parsing fails"""
        items = []
        
        # Split by numbered items
        sections = re.split(r'\n\s*\d+\.', text)
        
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            if section.strip():
                lines = section.strip().split('\n')
                question = lines[0].strip()
                
                # Extract answer from common patterns
                answer = ""
                explanation = ""
                
                for line in lines[1:]:
                    if line.strip():
                        if any(pattern in line.lower() for pattern in ["answer:", "solution:", "correct:"]):
                            answer = re.sub(r'^.*?(?:answer|solution|correct):\s*', '', line, flags=re.IGNORECASE).strip()
                        elif any(pattern in line.lower() for pattern in ["explanation:", "because:", "reason:"]):
                            explanation = re.sub(r'^.*?(?:explanation|because|reason):\s*', '', line, flags=re.IGNORECASE).strip()
                
                if question:
                    items.append({
                        "id": f"item_{i}",
                        "question": question,
                        "answer": answer or "Answer not provided",
                        "explanation": explanation or "Explanation not provided",
                        "difficulty": "medium",
                        "type": practice_type
                    })
        
        return items

    def _format_practice_output(self, items: List[Dict[str, Any]], include_answers: bool = True) -> str:
        """Format practice items for output"""
        if not items:
            return "No practice items were generated. Please try rephrasing your request."
        
        practice_type = items[0].get("type", "practice")
        difficulty = items[0].get("difficulty", "medium")
        
        # Format header
        formatted = f"**{practice_type.title()} - {difficulty.title()} Difficulty**\n"
        formatted += f"*{len(items)} items generated*\n\n"
        
        # Format items based on type
        for i, item in enumerate(items, 1):
            formatted += f"**{i}. {item['question']}**\n"
            
            if include_answers:
                formatted += f"   *Answer:* {item['answer']}\n"
                if item.get('explanation'):
                    formatted += f"   *Explanation:* {item['explanation']}\n"
            
            formatted += "\n"
        
        # Add practice tips
        if include_answers:
            formatted += "---\n"
            formatted += f"*💡 Practice Tips for {difficulty} level:*\n"
            
            if difficulty == "easy":
                formatted += "- Take your time and work through each step\n"
                formatted += "- Don't worry if you make mistakes - that's how you learn!\n"
            elif difficulty == "medium":
                formatted += "- Break complex problems into smaller steps\n"
                formatted += "- Check your work and reasoning\n"
            else:  # hard
                formatted += "- Think carefully about the approach before starting\n"
                formatted += "- Consider multiple solution methods\n"
            
            formatted += "- Review explanations to understand the concepts better\n"
        
        return formatted

    def _create_fallback_practice(self, topic: str, difficulty: str, num_items: int, practice_type: str) -> List[Dict[str, Any]]:
        """Create fallback practice items when LLM generation fails"""
        fallback_items = []
        
        for i in range(1, min(num_items + 1, 4)):  # Limit fallback to 3 items
            fallback_items.append({
                "id": f"fallback_{i}",
                "question": f"Practice question {i} about {topic}. Please work through this concept step by step.",
                "answer": f"Please work through this {topic} problem systematically, applying the key concepts.",
                "explanation": f"This question tests your understanding of {topic}. Take time to think through the approach.",
                "difficulty": difficulty,
                "type": practice_type
            })
        
        return fallback_items

    def _extract_grade_number(self, grade_level: str) -> Optional[int]:
        """Extract numeric grade level from grade string"""
        if not grade_level:
            return None
            
        # Look for numeric patterns
        grade_patterns = [
            r'(\d+)(?:th|st|nd|rd)?\s+grade',
            r'grade\s+(\d+)',
            r'^(\d+)$',
            r'year\s+(\d+)',
            r'level\s+(\d+)'
        ]
        
        for pattern in grade_patterns:
            match = re.search(pattern, grade_level.lower())
            if match:
                return int(match.group(1))
        
        # Handle special cases
        special_grades = {
            "kindergarten": 0, "k": 0,
            "elementary": 4, "primary": 4,
            "middle": 7, "intermediate": 7,
            "high": 10, "secondary": 10,
            "university": 13, "college": 13
        }
        
        for key, value in special_grades.items():
            if key in grade_level.lower():
                return value
        
        return None

    def _get_default_profile(self) -> Dict[str, Any]:
        """Get default learner profile when none is available"""
        return {
            "grade_level": "General",
            "difficulty_preference": "medium",
            "performance_metrics": {"accuracy_rate": 0.7},
            "learning_struggles": [],
            "mastered_topics": []
        }

    def _validate_state(self) -> bool:
        """Validate that current state is available"""
        if not self.current_state:
            self.logger.warning("No current state available for practice generation")
            return False
        return True
