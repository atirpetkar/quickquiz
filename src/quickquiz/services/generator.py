"""Question generation service using LangChain and OpenAI."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..models.database import Question, Document, DocumentChunk
from ..models.schemas import GenerationRequest, QuestionCreate, DifficultyLevel
from ..core.exceptions import QuestionGenerationError
from ..utils.prompts import PromptTemplates
from .embeddings import EmbeddingService


class GeneratorService:
    """Service for generating quiz questions from document content."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.prompts = PromptTemplates()
    
    async def generate_questions(
        self, 
        db: AsyncSession, 
        request: GenerationRequest
    ) -> List[Question]:
        """Generate quiz questions for a document."""
        
        try:
            # Retrieve document
            document = await self._get_document(db, request.document_id)
            if not document:
                raise QuestionGenerationError(f"Document {request.document_id} not found")
            
            # Get relevant chunks for context
            context_chunks = await self._get_relevant_chunks(db, request.document_id)
            
            if not context_chunks:
                raise QuestionGenerationError("No content chunks found for document")
            
            # Generate questions
            questions = []
            for i in range(request.num_questions):
                question = await self._generate_single_question(
                    context_chunks,
                    request.difficulty_level,
                    request.question_types[0] if request.question_types else None,
                    request.topics
                )
                
                if question:
                    # Create database record
                    question_record = Question(
                        document_id=request.document_id,
                        question_text=question["question_text"],
                        question_type=question["question_type"],
                        options=question.get("options"),
                        correct_answer=question["correct_answer"],
                        explanation=question.get("explanation"),
                        difficulty_level=question.get("difficulty_level"),
                        bloom_level=question.get("bloom_level"),
                        topic=question.get("topic"),
                        metadata={"generation_request_id": str(uuid.uuid4())}
                    )
                    
                    db.add(question_record)
                    questions.append(question_record)
            
            await db.commit()
            return questions
            
        except Exception as e:
            await db.rollback()
            raise QuestionGenerationError(f"Failed to generate questions: {str(e)}")
    
    async def _get_document(self, db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        """Retrieve document by ID."""
        # TODO: Implement database query
        return None
    
    async def _get_relevant_chunks(self, db: AsyncSession, document_id: uuid.UUID) -> List[DocumentChunk]:
        """Get relevant content chunks for the document."""
        # TODO: Implement database query to get chunks
        # For now, return empty list
        return []
    
    async def _generate_single_question(
        self,
        context_chunks: List[DocumentChunk],
        difficulty_level: Optional[DifficultyLevel],
        question_type: Optional[str],
        topics: Optional[List[str]]
    ) -> Optional[dict]:
        """Generate a single question using LLM."""
        
        # Combine context from chunks
        context = "\n\n".join([chunk.content for chunk in context_chunks[:3]])  # Use top 3 chunks
        
        # Create prompt
        prompt = self.prompts.get_question_generation_prompt(
            context=context,
            difficulty=difficulty_level.value if difficulty_level else "medium",
            question_type=question_type or "multiple_choice",
            topic=topics[0] if topics else None
        )
        
        # TODO: Implement LLM call with LangChain
        # For now, return a mock question
        mock_question = {
            "question_text": "What is the main concept discussed in the given context?",
            "question_type": "multiple_choice",
            "options": [
                {"label": "A", "text": "Option A"},
                {"label": "B", "text": "Option B"},
                {"label": "C", "text": "Option C"},
                {"label": "D", "text": "Option D"}
            ],
            "correct_answer": "A",
            "explanation": "This is the correct answer based on the context.",
            "difficulty_level": difficulty_level.value if difficulty_level else "medium",
            "bloom_level": "Understanding",
            "topic": topics[0] if topics else "General"
        }
        
        return mock_question
