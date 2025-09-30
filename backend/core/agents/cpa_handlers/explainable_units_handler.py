from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.core.states.graph_states import RAGState, LearningUnit
from backend.models.llms.groq_llm import GroqLLM
from backend.utils.helpers.language_detection import returnlang
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from backend.core.rag.rag_retriever import RAGRetriever
from backend.database.repositories.chunk_repo import ChunkRepository
from backend.database.db import NeonDatabase
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.core.builders.document_builder import DocumentBuilder
import uuid
import json
import asyncio


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
        self.embedder = HFEmbedder()
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for explainable units generation"""
        return Tool(
            name="explainable_units",
            description="Generate structured learning units and educational content from documents. Use when user asks to: create units, generate lessons, make tutorials, break down content, structure learning materials, design courses, or create educational modules. This tool creates comprehensive LearningUnit objects with titles, objectives, key points, and structured content.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, query: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            # Use synchronous approach with direct database access
            return self._process_sync(query)
        except Exception as e:
            return self._handle_error(e, "explainable_units")

    def _process_sync(self, query: str, adaptation_instruction=None) -> str:
        """
        Synchronous processing method that generates structured learning units
        """
        try:
            self.logger.info("Starting explainable units generation (sync)")

            # Create a single async coroutine and run it
            async def get_documents_async():
                # Get query embedding
                query_embedding = await self.embedder.embed_query(query)

                # Get documents from database
                async with NeonDatabase.get_session() as session:
                    chunk_repo = ChunkRepository(session=session)
                    chunks = await chunk_repo.get_similar_chunks(query_embedding, top_k=10)

                    # Convert chunks to Documents
                    documents = [
                        DocumentBuilder()
                        .set_content(chunk.content)
                        .set_metadata({
                            "id": str(chunk.id),
                            "source": getattr(chunk, 'source', f"Chunk {chunk.id}"),
                            "similarity_score": getattr(chunk, 'similarity_score', 0.0)
                        })
                        .build()
                        for chunk in chunks
                    ]
                    return documents

            # Get documents using a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                documents = loop.run_until_complete(get_documents_async())
            finally:
                loop.close()

            # Get adaptation instruction from state
            adaptation_instruction = self.current_state.get("adaptation_instruction", adaptation_instruction)

            if not documents:
                return "No documents available to generate learning units. Please upload documents first."

            # Combine all document content
            content = "\n\n".join(doc.page_content for doc in documents)

            # Create metadata from the first document
            metadata = documents[0].metadata if documents else {}
            metadata.update({
                "subject": metadata.get("subject", "General"),
                "grade_level": metadata.get("grade_level", "12"),
                "document_id": metadata.get("source", "unknown")
            })

            # Generate structured units
            units = self._generate_units(query, content, metadata, adaptation_instruction)

            # Validate and clean units
            validated_units = self._validate_units(units, metadata)

            # Update current state
            self.current_state["generated_units"] = validated_units

            self.logger.info(f"Generated {len(validated_units)} learning units")
            return f"Successfully generated {len(validated_units)} learning units with explainable insights."

        except Exception as e:
            self.logger.error(f"Error generating learning units: {e}")
            return f"Error generating learning units: {str(e)}"

    async def _process(self, query: str, adaptation_instruction=None) -> str:
        """
        Main processing method that generates structured learning units
        """
        try:
            self.logger.info("Starting explainable units generation")

            # Get relevant documents from database using retriever
            documents = await self.retriever.retrieve_documents(query, top_k=10)

            # Get adaptation instruction from state
            adaptation_instruction = self.current_state.get("adaptation_instruction", adaptation_instruction)

            if not documents:
                return "No documents available to generate learning units. Please upload documents first."

            # Combine all document content
            content = "\n\n".join(doc.page_content for doc in documents)

            # Create metadata from the first document
            metadata = documents[0].metadata if documents else {}
            metadata.update({
                "subject": metadata.get("subject", "General"),
                "grade_level": metadata.get("grade_level", "12"),
                "document_id": metadata.get("source", "unknown")
            })

            # Generate structured units
            units = self._generate_units(query, content, metadata, adaptation_instruction)

            # Validate and clean units
            validated_units = self._validate_units(units, metadata)

            # Update current state
            self.current_state["generated_units"] = validated_units

            self.logger.info(f"Generated {len(validated_units)} learning units")
            return f"Successfully generated {len(validated_units)} learning units with explainable insights."

        except Exception as e:
            self.logger.error(f"Error generating learning units: {e}")
            return f"Error generating learning units: {str(e)}"

    def _generate_units(self,query ,content, metadata, adaptation_instruction=None):
        """Generate structured learning units from content"""
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
    
