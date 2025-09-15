
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend__.models.llms.groq_llm import GroqLLM
from backend__.core.states.graph_states import LearningUnit, RAGState
import uuid
from backend__.db.connect_db import run_query
from langchain_core.runnables import RunnableLambda
from backend__.utils.helpers.language_detection import returnlang

class UnitStructureGenerator:
    def __init__(self):
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm  
        self.parser = JsonOutputParser(pydantic_object=LearningUnit)

        
        # Base prompt template for unit generation
        self.base_prompt = PromptTemplate(
    input_variables=[
        "content", 
        "subject", 
        "grade_level", 
        "adaptation_instruction", 
        "language", 
        "format_instructions"
    ],
    template="""
        You are an expert educational content processor. Your task is to analyze the provided educational content and create structured learning units.

        Document Content:
        {content}

        Subject: {subject}
        Grade Level: {grade_level}

        {adaptation_instruction}

        Instructions:
        1. Identify distinct topics within the content that can stand as separate learning units
        2. For each unit, create a comprehensive structure with all required fields
        3. Ensure titles are clear and descriptive
        4. Generate appropriate subtopics that break down the main topic
        5. Create meaningful question-answer pairs for assessment
        6. Assign appropriate difficulty levels based on complexity and grade level
        7. Extract relevant keywords and learning objectives
        8. Output should be in {language}

        IMPORTANT: 
        - Return a JSON array of learning units
        - Each unit must follow the exact schema provided
        - Ensure consistency across all units
        - Make content age-appropriate for the specified grade level
        - DIFFICULTY LEVELS MUST BE IN ENGLISH: "easy", "medium", or "hard"

        {format_instructions}

        Output JSON Array:
    """
            )

        self.unit_generation_chain = self.base_prompt | self.llm | self.parser

    async def _generate_units(self, content: str, metadata, adaptation_instruction=None) :
        """
        Generate structured learning units from content
        """
        # Prepare inputs for the chain
        chain_input = {
            "content": content,
            "subject": metadata.get("subject", "General"),
            "grade_level": metadata.get("grade_level", "12"),
            "adaptation_instruction": adaptation_instruction,
            "format_instructions": self.parser.get_format_instructions(),
            "language": returnlang(content)
        }
        
        # Generate units using the chain
        try:
            # The chain should return a list of units, but sometimes returns a single unit
            result = await self.unit_generation_chain.ainvoke(chain_input)
            
            # Handle both single unit and array responses
            if isinstance(result, list):
                units = result
            elif isinstance(result, dict):
                units = [result]
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")
            
            return units
            
        except Exception as e:
            # Fallback: try to parse as single unit
            try:
                single_unit = await self._generate_single_unit(content, metadata, adaptation_instruction)
                return [single_unit]
            except:
                raise e

    def _validate_units(self, units, metadata) :
        """
        Validate and ensure consistent schema across all units
        """
        validated_units = []
        
        for unit in units:
            try:
                # Validate using Pydantic model
                validated_unit = LearningUnit(**unit)
                
                # Add metadata and IDs
                unit_dict = validated_unit.dict()
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
                # Handle validation errors by fixing common issues
                fixed_unit = self._fix_unit_schema(unit, metadata)
                validated_units.append(fixed_unit)
        
        return validated_units
    
    async def _store_units(self, units):
        """
        Store generated units in PostgreSQL using run_query
        """
        stored_units = []

        for unit in units:
            # 1. Store in learning_units table
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

            # 3. Store explanations
            query = """
                INSERT INTO explanations (unit_id, explanation_text, difficulty_variant)
                VALUES (%s, %s, %s)
            """
            params = (unit["unit_id"], unit["detailed_explanation"], "base")
            run_query(query, params, fetch=False)

            # 4. Store key points
            for i, key_point in enumerate(unit["key_points"]):
                query = """
                    INSERT INTO key_points (unit_id, key_point_text, point_order, difficulty_variant)
                    VALUES (%s, %s, %s, %s)
                """
                params = (unit["unit_id"], key_point, i + 1, "base")
                run_query(query, params, fetch=False)

            stored_units.append(unit)

        return stored_units

    def _fix_unit_schema(self, unit, metadata):
        """Fix common schema issues in generated units"""
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

    async def unit_structure_generator_node(self, state: RAGState) -> RAGState:
        """
        LangGraph node that converts document content into structured learning units
        """
        try:
            # Extract documents from RAGState
            documents = state.get("documents", [])
            new_documents = state.get("new_documents", [])
            
            # Combine all documents
            all_documents = documents + new_documents
            
            if not all_documents:
                state["answer"] = "No documents available to generate learning units."
                return state
            
            # Combine all document content
            content = "\n\n".join(doc.page_content for doc in all_documents)
            
            # Create metadata from the first document
            metadata = all_documents[0].metadata if all_documents else {}
            metadata.update({
                "subject": metadata.get("subject", "General"),
                "grade_level": metadata.get("grade_level", "12"),
                "document_id": metadata.get("source", "unknown")
            })
            
            adaptation_instruction = state.get("query", "")
            
            # Generate structured units
            units = await self._generate_units(content, metadata, adaptation_instruction)
            
            # Validate and clean units
            validated_units = self._validate_units(units, metadata)
            
            # Store units in database
            stored_units = await self._store_units(validated_units)
            
            # Update state
            state["generated_units"] = stored_units
            state["answer"] = f"Successfully generated {len(stored_units)} learning units."
            
            return state
            
        except Exception as e:
            state["answer"] = f"Error generating learning units: {str(e)}"
            return state
        


