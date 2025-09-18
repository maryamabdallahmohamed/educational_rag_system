from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.core.states.graph_states import RAGState, LearningUnit
from backend.models.llms.groq_llm import GroqLLM
from backend.db.connect_db import run_query
from backend.utils.helpers.language_detection import returnlang
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
import uuid
import json


class ExplainableUnitsHandler(BaseHandler):
    """
    Handler responsible for generating structured learning units with explainable insights
    """
    
    def __init__(self):
        super().__init__()
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm  
        self.parser = JsonOutputParser(pydantic_object=LearningUnit)

        # Load prompt template from YAML file
        prompt_template = PromptLoader.load_system_prompt("prompts/unit_structure_generator.yaml")
        
        self.base_prompt = PromptTemplate(
            input_variables=[
                "content", 
                "subject", 
                "grade_level", 
                "adaptation_instruction", 
                "language", 
                "format_instructions"
            ],
            template=prompt_template
        )

        self.unit_generation_chain = self.base_prompt | self.llm | self.parser
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for explainable units generation"""
        return Tool(
            name="explainable_units",
            description="Generate structured learning units from content. Use when user asks to break down, structure, or create educational content from documents.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, query: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            if not self._validate_state():
                return "No documents available to generate learning units from."
            
            return self._process(query)
        except Exception as e:
            return self._handle_error(e, "unit generation")

    def _process(self, query: str, adaptation_instruction=None) -> str:
        """
        Main processing method that generates structured learning units
        """
        try:
            self.logger.info("Starting explainable units generation")
            
            # Extract documents from current state
            documents = self.current_state.get("documents", [])
            
            # Get adaptation instruction from state
            adaptation_instruction = self.current_state.get("adaptation_instruction", adaptation_instruction)
            
            # Combine all documents
            all_documents = documents
            
            if not all_documents:
                return "No documents available to generate learning units."
            
            # Combine all document content
            content = "\n\n".join(doc.page_content for doc in all_documents)
            
            # Create metadata from the first document
            metadata = all_documents[0].metadata if all_documents else {}
            metadata.update({
                "subject": metadata.get("subject", "General"),
                "grade_level": metadata.get("grade_level", "12"),
                "document_id": metadata.get("source", "unknown")
            })
            
            # Generate structured units (synchronous)
            units = self._generate_units(content, metadata, adaptation_instruction)
            
            # Validate and clean units
            validated_units = self._validate_units(units, metadata)
            
            # Store units in database
            stored_units = self._store_units(validated_units)
            
            # Update current state
            self.current_state["generated_units"] = stored_units
            
            self.logger.info(f"Generated {len(stored_units)} learning units")
            return f"Successfully generated {len(stored_units)} learning units with explainable insights."
            
        except Exception as e:
            self.logger.error(f"Error generating learning units: {e}")
            return f"Error generating learning units: {str(e)}"

    def _generate_units(self, content, metadata, adaptation_instruction=None):
        """Generate structured learning units from content"""
        self.logger.info("Generating units from content")
        
        chain_input = {
            "content": content,
            "subject": metadata.get("subject", "General"),
            "grade_level": metadata.get("grade_level", "12"),
            "adaptation_instruction": adaptation_instruction or "",
            "format_instructions": self.parser.get_format_instructions(),
            "language": returnlang(content) if returnlang else "English"
        }
        
        try:
            result = self.unit_generation_chain.invoke(chain_input)
            
            # Handle both single unit and array responses
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")
                
        except Exception as e:
            self.logger.error(f"Error generating units: {e}")
            raise e

    def _validate_units(self, units, metadata):
        """Validate and ensure consistent schema across all units"""
        self.logger.info(f"Validating {len(units)} units")
        validated_units = []
        
        for unit in units:
            try:
                validated_unit = LearningUnit(**unit)
                unit_dict = validated_unit.dict()
                
                # Add metadata and IDs
                unit_dict.update({
                    "unit_id": str(uuid.uuid4()),
                    "subject": metadata.get("subject", "General"),
                    "grade_level": metadata.get("grade_level", 10),
                    "source_document_id": metadata.get("document_id"),
                    "created_at": "now()",
                    "adaptation_applied": metadata.get("adaptation_instruction") is not None
                })
                
                validated_units.append(unit_dict)
                
            except Exception as e:
                self.logger.warning(f"Validation error for unit: {e}")
                fixed_unit = self._fix_unit_schema(unit, metadata)
                validated_units.append(fixed_unit)
        
        return validated_units

    def _fix_unit_schema(self, unit, metadata):
        """Fix common schema issues in generated units"""
        self.logger.info("Fixing unit schema issues")
        
        # Add default values for missing fields
        fixed_unit = {
            "title": unit.get("title", "Untitled Unit"),
            "subtopics": unit.get("subtopics", []),
            "detailed_explanation": unit.get("detailed_explanation", ""),
            "key_points": unit.get("key_points", []),
            "difficulty_level": unit.get("difficulty_level", "medium"),
            "learning_objectives": unit.get("learning_objectives", []),
            "keywords": unit.get("keywords", [])
        }
        
        # Add metadata and IDs
        fixed_unit.update({
            "unit_id": str(uuid.uuid4()),
            "subject": metadata.get("subject", "General"),
            "grade_level": metadata.get("grade_level", 10),
            "source_document_id": metadata.get("document_id"),
            "created_at": "now()",
            "adaptation_applied": metadata.get("adaptation_instruction") is not None
        })
        
        return fixed_unit
    
    def _store_units(self, units):
        """Store generated units in PostgreSQL using run_query"""
        self.logger.info(f"Storing {len(units)} units in database")
        stored_units = []
        
        try:
            for unit in units:
                # Store in learning_units table
                query = """
                    INSERT INTO learning_units 
                    (unit_id, title, subject, grade_level, base_difficulty_level, learning_objectives, keywords)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    unit["unit_id"],
                    unit["title"],
                    unit["subject"],
                    unit["grade_level"],
                    unit["difficulty_level"],
                    unit["learning_objectives"],
                    unit["keywords"],
                )
                run_query(query, params, fetch=False)

                # Store explanations
                query = """
                    INSERT INTO explanations (unit_id, explanation_text, difficulty_variant)
                    VALUES (%s, %s, %s)
                """
                params = (unit["unit_id"], unit["detailed_explanation"], "base")
                run_query(query, params, fetch=False)

                # Store key points
                for i, key_point in enumerate(unit["key_points"]):
                    query = """
                        INSERT INTO key_points (unit_id, key_point_text, point_order, difficulty_variant)
                        VALUES (%s, %s, %s, %s)
                    """
                    params = (unit["unit_id"], key_point, i + 1, "base")
                    run_query(query, params, fetch=False)

                stored_units.append(unit)
                
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return units  # Return units even if storage fails
            
        self.logger.info(f"Successfully stored {len(stored_units)} units")
        return stored_units
