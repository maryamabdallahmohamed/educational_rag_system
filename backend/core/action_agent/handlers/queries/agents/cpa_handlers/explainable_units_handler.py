from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.core.states.graph_states import RAGState, LearningUnit
from backend.models.llms.groq_llm import GroqLLM
from backend.utils.helpers.language_detection import returnlang
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from backend.core.rag.rag_retriever import RAGRetriever
from backend.database.repositories.learning_unit_repo import LearningUnitRepository
from backend.database.repositories.cpa_repo import ContentProcessorAgentRepository
from backend.database.db import NeonDatabase
import uuid
import json
import time


class ExplainableUnitsHandler(BaseHandler):
    """
    Handler responsible for generating structured learning units with explainable insights
    """
    
    def __init__(self):
        super().__init__()
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm
        self.parser = JsonOutputParser(pydantic_object=LearningUnit)
        self.retriever = RAGRetriever()

        # Load prompt template from YAML file
        prompt_template = PromptLoader.load_system_prompt("prompts/unit_structure_generator.yaml")

        self.base_prompt = PromptTemplate(
            input_variables=[
                "query",
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
        # Create async tool - LangChain will use coroutine attribute when available
        tool = Tool(
            name="explainable_units",
            description="Generate structured learning units and educational content from documents. Use when user asks to: create units, generate lessons, make tutorials, break down content, structure learning materials, design courses, or create educational modules. This tool creates comprehensive LearningUnit objects with titles, objectives, key points, and structured content.",
            func=lambda _: "This tool requires async execution",  # Fallback - should not be used
            coroutine=self._process_async  # This is the async version that will be used
        )
        return tool

    async def _process_async(self, query: str) -> str:
        """Async wrapper for tool execution with error handling"""
        try:
            return await self._process(query)
        except Exception as e:
            return self._handle_error(e, "explainable_units")

    async def _process(self, query: str, adaptation_instruction=None) -> str:
        """
        Async processing method that generates structured learning units.
        """
        start_time = time.time()

        try:
            self.logger.info("Starting explainable units generation")

            # Get relevant documents from database using retriever (cleaner approach)
            documents = await self.retriever.retrieve_documents(query, top_k=10)

            # Track chunk IDs and similarity scores from document metadata
            chunk_ids = [doc.metadata.get("id", doc.metadata.get("chunk_id", "")) for doc in documents]
            similarity_scores = [doc.metadata.get("similarity_score", 0.0) for doc in documents]

            adaptation_instruction = self.current_state.get("adaptation_instruction", adaptation_instruction)

            if not documents:
                return "No documents available to generate learning units. Please upload documents first."

            content = "\n\n".join(doc.page_content for doc in documents)

            metadata = documents[0].metadata if documents else {}

            metadata.update({
                "subject": metadata.get("subject", "General"),
                "grade_level": metadata.get("grade_level", "12"),
                "adaptation_instruction": adaptation_instruction,
                "source_chunks": chunk_ids  # Store chunk IDs for the units
            })

            units = await self._generate_units(query, content, metadata, adaptation_instruction)
            validated_units = self._validate_units(units, metadata)

            self.current_state["generated_units"] = validated_units

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Save to database
            cpa_session_id = await self._save_units_to_database(
                query=query,
                validated_units=validated_units,
                chunk_ids=chunk_ids,
                similarity_scores=similarity_scores,
                processing_time=processing_time
            )

            self.logger.info(f"Generated {len(validated_units)} learning units")

            if cpa_session_id:
                return f"Successfully generated and saved {len(validated_units)} learning units to database."
            else:
                return f"Successfully generated {len(validated_units)} learning units (database save failed, but units are in memory)."

        except Exception as e:
            self.logger.error(f"Error generating learning units: {e}")
            return f"Error generating learning units: {str(e)}"

    async def _save_units_to_database(
        self,
        query: str,
        validated_units: list,
        chunk_ids: list,
        similarity_scores: list,
        processing_time: int
    ) -> uuid.UUID:
        """
        Save learning units to database with CPA session tracking
        Returns the CPA session ID
        """
        try:
            async with NeonDatabase.get_session() as session:
                cpa_repo = ContentProcessorAgentRepository(session=session)

                # Create a summary response string from the generated units
                unit_titles = [unit.get('title', 'Untitled') for unit in validated_units]
                response_summary = f"Generated {len(validated_units)} learning units: " + ", ".join(unit_titles[:3])
                if len(unit_titles) > 3:
                    response_summary += f", and {len(unit_titles) - 3} more"

                cpa_record = await cpa_repo.create(
                    query=query,
                    response=response_summary,  # String summary instead of list
                    tool_used="explainable_units",
                    chunks_used=chunk_ids,
                    similarity_scores=similarity_scores,
                    units_generated_count=str(len(validated_units))
                )

                self.logger.info(f"Created CPA session: {cpa_record.id}")

                # Save learning units linked to CPA session
                learning_unit_repo = LearningUnitRepository(session=session)
                saved_units = await learning_unit_repo.create_batch(
                    cpa_session_id=cpa_record.id,
                    units_data=validated_units
                )

                self.logger.info(f"Saved {len(saved_units)} learning units to database")

                # Store session ID in state for reference
                if self.current_state:
                    self.current_state["cpa_session_id"] = str(cpa_record.id)

                return cpa_record.id

        except Exception as e:
            self.logger.error(f"Error saving units to database: {e}")
            return None

    async def _generate_units(self,query ,content, metadata, adaptation_instruction=None):
        """Generate structured learning units from content (async)"""
        self.logger.info("Generating units from content")

        chain_input = {
            "query":query,
            "content": content,
            "subject": metadata.get("subject", "General"),
            "grade_level": metadata.get("grade_level", "12"),
            "adaptation_instruction": adaptation_instruction or "",
            "format_instructions": self.parser.get_format_instructions(),
            "language": returnlang(content) if returnlang else "English"
        }

        try:
            # Use ainvoke instead of invoke for async execution
            result = await self.unit_generation_chain.ainvoke(chain_input)

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

                # Add metadata (don't include 'id' or 'created_at' - they have DB defaults)
                unit_dict.update({
                    "subject": metadata.get("subject", "General"),
                    "grade_level": str(metadata.get("grade_level", "12")),  # Text field
                    "source_document_id": None,  # Don't reference documents table - use source_chunks instead
                    "source_chunks": metadata.get("source_chunks", []),  # Store chunk IDs as JSONB
                    "adaptation_applied": str(metadata.get("adaptation_instruction") is not None) if metadata.get("adaptation_instruction") else None
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
        
        # Add metadata (don't include 'id' or 'created_at' - they have DB defaults)
        fixed_unit.update({
            "subject": metadata.get("subject", "General"),
            "grade_level": str(metadata.get("grade_level", "12")),  # Text field
            "source_document_id": None,  # Don't reference documents table - use source_chunks instead
            "source_chunks": metadata.get("source_chunks", []),  # Store chunk IDs as JSONB
            "adaptation_applied": str(metadata.get("adaptation_instruction") is not None) if metadata.get("adaptation_instruction") else None
        })
        
        return fixed_unit
    
