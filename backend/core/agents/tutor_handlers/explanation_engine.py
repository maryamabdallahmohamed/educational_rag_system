import json
import asyncio
import time
import re
from typing import Dict, Any, Optional
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from backend.core.agents.base_handler import BaseHandler
from backend.models.llms.groq_llm import GroqLLM
from backend.utils.logger_config import get_logger


class ExplanationEngineHandler(BaseHandler):
    """
    Generates personalized explanations adapted to learner profiles
    Supports multiple explanation styles based on learning preferences
    """

    def __init__(self):
        super().__init__()
        self.llm = GroqLLM().llm
        
        # Define available explanation styles
        self.explanation_styles = {
            "simplified": "Simple, easy-to-understand explanations with basic vocabulary",
            "detailed": "Comprehensive, thorough explanations with full context",
            "analogy": "Explanation using relatable analogies and metaphors",
            "step-by-step": "Structured, sequential breakdown of concepts",
            "visual": "Description-based explanations that help visualize concepts",
            "interactive": "Engaging explanations with questions and examples",
            "practical": "Real-world applications and hands-on examples"
        }
        
    def tool(self) -> Tool:
        """Return configured LangChain Tool for explanation generation"""
        return Tool(
            name="generate_explanation",
            description="Generate personalized explanations adapted to learner's grade level, learning style, and preferences. Supports: simplified, detailed, analogy-based, step-by-step, visual styles.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, explanation_request: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            return asyncio.run(self._process(explanation_request))
        except Exception as e:
            return self._handle_error(e, "explanation_generation")
    
    async def _process(self, explanation_request: str) -> str:
        """Process explanation generation request"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting explanation generation: {explanation_request}")

            if not self._validate_state():
                return "Unable to generate explanation - no learner context available"

            # Parse the explanation request
            request_data = self._parse_explanation_request(explanation_request)
            if not request_data:
                return "Invalid explanation request format. Please specify the topic to explain."

            # Get learner profile from current state
            learner_profile = self.current_state.get("learner_profile", {})
            if not learner_profile:
                self.logger.warning("No learner profile available, using generic explanation")
                learner_profile = self._get_default_profile()

            # Determine best explanation style
            best_style = self._determine_best_explanation_style(
                learner_profile, 
                request_data.get("explanation_style")
            )

            # Generate personalized explanation
            explanation = await self._generate_personalized_explanation(
                request_data["topic"],
                best_style,
                learner_profile
            )

            # Format the explanation output
            formatted_explanation = self._format_explanation_output(explanation, best_style)

            # Store explanation in state for future reference
            if "interaction_history" not in self.current_state:
                self.current_state["interaction_history"] = []
            
            self.current_state["interaction_history"].append({
                "type": "explanation",
                "topic": request_data["topic"],
                "style": best_style,
                "explanation": formatted_explanation,
                "timestamp": time.time()
            })

            processing_time = time.time() - start_time
            self.logger.info(f"Explanation generated in {processing_time:.2f}s using {best_style} style")
            
            return formatted_explanation

        except Exception as e:
            self.logger.error(f"Error generating explanation: {e}")
            return self._handle_error(e, "explanation_generation")

    def _parse_explanation_request(self, request: str) -> Optional[Dict[str, Any]]:
        """Parse explanation request string into structured data"""
        try:
            # Handle different input types
            if isinstance(request, dict):
                # Direct dict input
                return request
            elif isinstance(request, str):
                # Try to parse as JSON first
                if request.strip().startswith('{'):
                    try:
                        return json.loads(request)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to handle malformed JSON strings
                        # Look for dict-like string representation: {"key": "value"}
                        import ast
                        try:
                            return ast.literal_eval(request)
                        except (ValueError, SyntaxError):
                            pass
            
            # Parse natural language request
            request_str = str(request)  # Ensure it's a string
            request_lower = request_str.lower()
            parsed_request = {
                "topic": "",
                "explanation_style": None,
                "learning_unit_id": None
            }
            
            # Extract topic - everything after common phrases
            topic_patterns = [
                r"explain\s+(.+?)(?:\s+using|\s+with|\s+in|$)",
                r"what\s+is\s+(.+?)(?:\s+using|\s+with|\s+in|$)",
                r"how\s+(.+?)(?:\s+works?|\s+using|\s+with|\s+in|$)",
                r"describe\s+(.+?)(?:\s+using|\s+with|\s+in|$)",
                r"topic:\s*(.+?)(?:\s+style:|\s+using:|,|$)"
            ]
            
            topic_found = False
            for pattern in topic_patterns:
                match = re.search(pattern, request_lower)
                if match:
                    parsed_request["topic"] = match.group(1).strip()
                    topic_found = True
                    break
            
            # If no pattern matched, use the entire request as topic
            if not topic_found and request_str.strip():
                # Remove common instruction words and use the rest
                topic = re.sub(r'^(explain|describe|what is|how does?|tell me about)\s+', '', request_str, flags=re.IGNORECASE)
                parsed_request["topic"] = topic.strip()
            
            # Extract style if mentioned
            style_mapping = {
                "simple": "simplified", "easy": "simplified", "basic": "simplified",
                "detail": "detailed", "thorough": "detailed", "comprehensive": "detailed",
                "analogy": "analogy", "metaphor": "analogy", "like": "analogy",
                "step": "step-by-step", "steps": "step-by-step", "sequential": "step-by-step",
                "visual": "visual", "picture": "visual", "diagram": "visual",
                "interactive": "interactive", "engaging": "interactive",
                "practical": "practical", "real-world": "practical", "hands-on": "practical"
            }
            
            for keyword, style in style_mapping.items():
                if keyword in request_lower:
                    parsed_request["explanation_style"] = style
                    break
            
            # Extract learning unit ID if present
            unit_match = re.search(r"unit[_\s]+id[:\s]+([^\s,]+)", request_lower)
            if unit_match:
                parsed_request["learning_unit_id"] = unit_match.group(1)
            
            self.logger.info(f"Parsed explanation request: {parsed_request}")
            return parsed_request if parsed_request["topic"] else None
            
        except Exception as e:
            self.logger.error(f"Error parsing explanation request: {e}")
            return None

    def _determine_best_explanation_style(self, learner_profile: Dict[str, Any], requested_style: str = None) -> str:
        """Determine the best explanation style based on learner profile and request"""
        
        # If specific style requested and it's valid, use it
        if requested_style and requested_style in self.explanation_styles:
            self.logger.info(f"Using requested explanation style: {requested_style}")
            return requested_style
        
        # Get learner characteristics
        grade_level = learner_profile.get("grade_level", "Unknown")
        learning_style = learner_profile.get("learning_style", "General")
        preferred_styles = learner_profile.get("preferred_explanation_styles", [])
        learning_struggles = learner_profile.get("learning_struggles", [])
        accessibility_needs = learner_profile.get("accessibility_needs", {})
        
        # Priority order for style selection
        
        # 1. Check preferred explanation styles from profile
        if preferred_styles:
            for style in preferred_styles:
                if style in self.explanation_styles:
                    self.logger.info(f"Using preferred explanation style from profile: {style}")
                    return style
        
        # 2. Adapt based on grade level
        grade_num = self._extract_grade_number(grade_level)
        if grade_num:
            if grade_num <= 6:  # Elementary
                self.logger.info("Using simplified style for elementary grade level")
                return "simplified"
            elif grade_num <= 9:  # Middle school
                if learning_struggles:
                    return "step-by-step"
                return "analogy"
            elif grade_num <= 12:  # High school
                return "detailed"
            else:  # University/Adult
                return "comprehensive" if "comprehensive" in self.explanation_styles else "detailed"
        
        # 3. Adapt based on learning style
        if learning_style == "Visual":
            self.logger.info("Using visual style for visual learner")
            return "visual"
        elif learning_style == "Kinesthetic":
            self.logger.info("Using practical style for kinesthetic learner")
            return "practical"
        elif learning_style == "Auditory":
            self.logger.info("Using interactive style for auditory learner")
            return "interactive"
        
        # 4. Adapt based on learning struggles
        if learning_struggles:
            self.logger.info("Using simplified style due to learning struggles")
            return "simplified"
        
        # 5. Adapt based on accessibility needs
        if accessibility_needs.get("screen_reader"):
            self.logger.info("Using step-by-step style for screen reader compatibility")
            return "step-by-step"
        
        # Default fallback
        self.logger.info("Using default analogy style")
        return "analogy"

    async def _generate_personalized_explanation(self, topic: str, style: str, profile: Dict[str, Any]) -> str:
        """Generate personalized explanation using LLM"""
        try:
            # Create explanation prompt
            prompt = self._create_explanation_prompt(topic, style, profile)
            
            # Generate explanation using LLM
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            
            # Extract text content from response
            if hasattr(response, 'content'):
                explanation = response.content
            else:
                explanation = str(response)
            
            self.logger.info(f"Generated {len(explanation)} character explanation")
            return explanation.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating explanation with LLM: {e}")
            # Fallback explanation
            return f"I understand you want to learn about {topic}. Let me explain this concept in a way that matches your learning style."

    def _create_explanation_prompt(self, topic: str, style: str, profile: Dict[str, Any]) -> str:
        """Create personalized explanation prompt for LLM"""
        
        # Extract learner characteristics
        grade_level = profile.get("grade_level", "general")
        learning_style = profile.get("learning_style", "general")
        preferred_language = profile.get("preferred_language", "English")
        accessibility_needs = profile.get("accessibility_needs", {})
        mastered_topics = profile.get("mastered_topics", [])
        learning_struggles = profile.get("learning_struggles", [])
        
        # Build contextual prompt
        prompt = f"""You are an expert educational tutor. Generate a personalized explanation about "{topic}" for a learner with the following profile:

Grade Level: {grade_level}
Learning Style: {learning_style}
Preferred Language: {preferred_language}
Explanation Style Requested: {style} - {self.explanation_styles.get(style, 'general explanation')}

Learner Context:
- Previously mastered: {', '.join(mastered_topics) if mastered_topics else 'No prior topics recorded'}
- Areas of difficulty: {', '.join(learning_struggles) if learning_struggles else 'None identified'}
- Accessibility needs: {', '.join([k for k, v in accessibility_needs.items() if v]) if accessibility_needs else 'None'}

Style Guidelines for {style}:"""
        
        # Add style-specific instructions
        if style == "simplified":
            prompt += """
- Use simple, everyday vocabulary
- Break complex ideas into small, digestible parts
- Avoid jargon and technical terms
- Use short sentences and clear structure
- Include reassuring language to build confidence"""
            
        elif style == "detailed":
            prompt += """
- Provide comprehensive coverage of the topic
- Include relevant background context and theory
- Explain the 'why' behind concepts
- Connect to related topics and applications
- Use precise technical vocabulary with definitions"""
            
        elif style == "analogy":
            prompt += """
- Use relatable analogies and metaphors
- Connect abstract concepts to familiar experiences
- Make comparisons to everyday objects or situations
- Help visualize complex ideas through comparison
- Use 'like' and 'similar to' constructions"""
            
        elif style == "step-by-step":
            prompt += """
- Break down into numbered sequential steps
- Show clear progression from basic to advanced
- Include 'First', 'Next', 'Then', 'Finally' transitions
- Provide checkpoints for understanding
- Build each step on the previous one"""
            
        elif style == "visual":
            prompt += """
- Describe visual representations and diagrams
- Use spatial language (above, below, left, right)
- Paint mental pictures with descriptive language
- Organize information visually with clear sections
- Describe colors, shapes, and spatial relationships"""
            
        elif style == "interactive":
            prompt += """
- Include rhetorical questions to engage thinking
- Suggest mental exercises and thought experiments
- Use conversational, engaging tone
- Include 'imagine if' scenarios
- Encourage active participation in learning"""
            
        elif style == "practical":
            prompt += """
- Focus on real-world applications and examples
- Include hands-on activities when possible
- Show how the concept is used in daily life
- Provide concrete, actionable information
- Connect to practical problem-solving"""
        
        # Add accessibility considerations
        if accessibility_needs.get("screen_reader"):
            prompt += """
            
Screen Reader Accessibility:
- Avoid descriptions that rely purely on visual elements
- Use clear, descriptive language for any visual concepts
- Structure content with clear headings and organization
- Avoid phrases like 'as you can see' or 'look at this'"""
        
        # Add language considerations
        if preferred_language == "Arabic":
            prompt += """
            
Language Considerations:
- You may include some Arabic terms if they help understanding
- Be culturally sensitive to Middle Eastern/Egyptian context
- Use examples relevant to Egyptian/Arab culture when appropriate"""
        
        prompt += f"""

Requirements:
- Keep explanation appropriate for {grade_level} level
- Length: 150-300 words for core explanation
- Be encouraging and supportive in tone
- End with a simple question to check understanding
- Make the explanation engaging and memorable

Generate the explanation now:"""
        
        return prompt

    def _format_explanation_output(self, explanation: str, style: str) -> str:
        """Format the explanation output with style indicators"""
        
        # Clean up the explanation
        explanation = explanation.strip()
        
        # Add style header
        style_name = style.replace("-", " ").title()
        formatted = f"**{style_name} Explanation:**\n\n{explanation}"
        
        # Add style-specific formatting
        if style == "step-by-step":
            # Ensure steps are properly numbered if not already
            if not re.search(r'^\d+\.', explanation, re.MULTILINE):
                lines = explanation.split('\n')
                numbered_lines = []
                step_count = 1
                for line in lines:
                    if line.strip() and not line.startswith('**') and not line.startswith('*'):
                        numbered_lines.append(f"{step_count}. {line.strip()}")
                        step_count += 1
                    else:
                        numbered_lines.append(line)
                explanation = '\n'.join(numbered_lines)
                formatted = f"**{style_name} Explanation:**\n\n{explanation}"
        
        elif style == "visual":
            # Add visual indicators
            formatted += "\n\n*💡 Tip: Try to visualize this concept as you read!*"
        
        elif style == "analogy":
            # Add analogy indicator
            formatted += "\n\n*🔗 Remember: Understanding through comparison makes learning easier!*"
        
        elif style == "practical":
            # Add practical application note
            formatted += "\n\n*🛠️ Try to think of other real-world examples where this applies!*"
        
        return formatted

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
            "elementary": 3, "primary": 3,
            "middle": 7, "intermediate": 7,
            "high": 10, "secondary": 10,
            "university": 13, "college": 13,
            "undergraduate": 13, "graduate": 17
        }
        
        for key, value in special_grades.items():
            if key in grade_level.lower():
                return value
        
        return None

    def _get_default_profile(self) -> Dict[str, Any]:
        """Get default learner profile when none is available"""
        return {
            "grade_level": "General",
            "learning_style": "General",
            "preferred_language": "English",
            "accessibility_needs": {},
            "mastered_topics": [],
            "learning_struggles": [],
            "preferred_explanation_styles": ["analogy"]
        }

    def _validate_state(self) -> bool:
        """Validate that current state is available"""
        if not self.current_state:
            self.logger.warning("No current state available for explanation generation")
            return False
        return True
