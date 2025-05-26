"""Question evaluation service for quality assessment."""

from typing import Dict, Any, List
import uuid

from ..models.schemas import EvaluationRequest, EvaluationResponse
from ..core.exceptions import EvaluationError
from ..utils.prompts import PromptTemplates


class EvaluatorService:
    """Service for evaluating question quality using LLM-as-Judge."""
    
    def __init__(self):
        self.prompts = PromptTemplates()
        self.quality_threshold = 90.0  # Minimum quality score for approval
    
    async def evaluate_question(self, request: EvaluationRequest) -> EvaluationResponse:
        """Evaluate a question for quality and accuracy."""
        
        try:
            # Extract question components
            question_text = request.question_text
            options = request.options
            correct_answer = request.correct_answer
            explanation = request.explanation
            
            # Validate input
            if not question_text or not correct_answer:
                raise EvaluationError("Question text and correct answer are required")
            
            # Create evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(
                question_text, options, correct_answer, explanation
            )
            
            # TODO: Implement LLM evaluation call
            # For now, return mock evaluation
            mock_evaluation = await self._mock_evaluate_question(
                question_text, options, correct_answer, explanation
            )
            
            return EvaluationResponse(
                quality_score=mock_evaluation["quality_score"],
                is_approved=mock_evaluation["quality_score"] >= self.quality_threshold,
                feedback=mock_evaluation["feedback"],
                suggestions=mock_evaluation["suggestions"],
                issues=mock_evaluation["issues"]
            )
            
        except Exception as e:
            raise EvaluationError(f"Failed to evaluate question: {str(e)}")
    
    async def batch_evaluate(self, questions: List[EvaluationRequest]) -> List[EvaluationResponse]:
        """Evaluate multiple questions in batch."""
        results = []
        
        for question in questions:
            try:
                result = await self.evaluate_question(question)
                results.append(result)
            except EvaluationError as e:
                # Create error response
                results.append(EvaluationResponse(
                    quality_score=0.0,
                    is_approved=False,
                    feedback={"error": str(e)},
                    suggestions=["Fix the question and try again"],
                    issues=["Evaluation failed"]
                ))
        
        return results
    
    def _create_evaluation_prompt(
        self, 
        question_text: str, 
        options: List[Any], 
        correct_answer: str, 
        explanation: str
    ) -> str:
        """Create evaluation prompt for LLM."""
        
        return self.prompts.get_evaluation_prompt(
            question_text=question_text,
            options=[{"label": opt.label, "text": opt.text} for opt in options] if options else [],
            correct_answer=correct_answer,
            explanation=explanation
        )
    
    async def _mock_evaluate_question(
        self, 
        question_text: str, 
        options: List[Any], 
        correct_answer: str, 
        explanation: str
    ) -> Dict[str, Any]:
        """Mock evaluation for testing purposes."""
        
        # Simple heuristic-based evaluation
        quality_score = 85.0
        issues = []
        suggestions = []
        
        # Check question length
        if len(question_text) < 10:
            quality_score -= 15
            issues.append("Question too short")
            suggestions.append("Make the question more detailed")
        
        # Check if explanation exists
        if not explanation:
            quality_score -= 10
            issues.append("Missing explanation")
            suggestions.append("Add explanation for the correct answer")
        
        # Check number of options for MCQ
        if options and len(options) < 4:
            quality_score -= 10
            issues.append("Insufficient answer options")
            suggestions.append("Provide 4 answer options for multiple choice questions")
        
        # Ensure minimum score
        quality_score = max(quality_score, 0.0)
        
        feedback = {
            "clarity": "Good" if len(question_text) > 20 else "Needs improvement",
            "difficulty": "Appropriate",
            "factual_accuracy": "Cannot verify without context",
            "answer_quality": "Good" if explanation else "Missing explanation"
        }
        
        return {
            "quality_score": quality_score,
            "feedback": feedback,
            "suggestions": suggestions,
            "issues": issues
        }
