"""Prompt templates for LLM interactions."""

from typing import Any


class PromptTemplates:
    """Collection of prompt templates for question generation and evaluation."""

    def get_question_generation_prompt(
        self,
        context: str,
        difficulty: str = "medium",
        question_type: str = "multiple_choice",
        topic: str | None = None,
    ) -> str:
        """Generate prompt for question generation."""

        topic_instruction = f" Focus on the topic: {topic}." if topic else ""

        prompt = f"""
You are an expert educational content creator. Generate a high-quality {difficulty} difficulty {question_type} question based on the provided context.

Context:
{context}

Requirements:
- Create a {difficulty} difficulty question
- Question type: {question_type}
- Question should test understanding, not just memorization
- Include clear, unambiguous answer options (A, B, C, D)
- Provide a detailed explanation for the correct answer
- Classify according to Bloom's taxonomy{topic_instruction}

Response format (JSON):
{{
    "question_text": "Clear, specific question text",
    "question_type": "{question_type}",
    "options": [
        {{"label": "A", "text": "First option"}},
        {{"label": "B", "text": "Second option"}},
        {{"label": "C", "text": "Third option"}},
        {{"label": "D", "text": "Fourth option"}}
    ],
    "correct_answer": "A",
    "explanation": "Detailed explanation of why this is correct",
    "difficulty_level": "{difficulty}",
    "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
    "topic": "Main topic covered"
}}

Generate one high-quality question:
"""
        return prompt

    def get_evaluation_prompt(
        self,
        question_text: str,
        options: list[dict[str, str]],
        correct_answer: str,
        explanation: str,
    ) -> str:
        """Generate prompt for question evaluation."""

        options_text = "\n".join([f"{opt['label']}. {opt['text']}" for opt in options])

        prompt = f"""
You are an expert educational assessment evaluator. Evaluate the quality of this quiz question on a scale of 0-100.

Question: {question_text}

Options:
{options_text}

Correct Answer: {correct_answer}
Explanation: {explanation}

Evaluation Criteria:
1. Clarity (25 points): Is the question clear and unambiguous?
2. Factual Accuracy (25 points): Is the content accurate and the correct answer truly correct?
3. Educational Value (25 points): Does it test meaningful understanding?
4. Option Quality (25 points): Are distractors plausible but clearly incorrect?

Additional Checks:
- No trick questions or overly technical language
- Appropriate difficulty level
- Complete and helpful explanation
- No bias or controversial content

Response format (JSON):
{{
    "quality_score": 85,
    "feedback": {{
        "clarity": "Good|Needs Improvement|Excellent",
        "factual_accuracy": "Accurate|Questionable|Excellent",
        "educational_value": "High|Medium|Low",
        "option_quality": "Good|Poor|Excellent"
    }},
    "issues": ["List specific issues found"],
    "suggestions": ["List specific improvement suggestions"],
    "is_acceptable": true
}}

Evaluate this question:
"""
        return prompt

    def get_context_retrieval_prompt(self, query: str, max_chunks: int = 3) -> str:
        """Generate prompt for context retrieval and ranking."""

        prompt = f"""
Given the query: "{query}"

Rank the following text chunks by relevance to generating educational questions about this topic.
Return the top {max_chunks} most relevant chunks with relevance scores.

Consider:
- Factual content that can be tested
- Concepts that students should understand
- Information that allows for meaningful questions
- Avoid purely descriptive or obvious content

Response format (JSON):
{{
    "relevant_chunks": [
        {{
            "chunk_id": "chunk_identifier",
            "relevance_score": 0.95,
            "reason": "Why this chunk is relevant"
        }}
    ]
}}
"""
        return prompt

    def get_difficulty_adjustment_prompt(
        self, question: str, target_difficulty: str
    ) -> str:
        """Generate prompt for adjusting question difficulty."""

        prompt = f"""
Adjust the following question to {target_difficulty} difficulty level:

Original Question: {question}

Guidelines for {target_difficulty} difficulty:
- Easy: Basic recall, simple concepts, straightforward language
- Medium: Application of concepts, moderate complexity, some analysis required
- Hard: Complex reasoning, synthesis, evaluation, advanced concepts

Maintain the core learning objective while adjusting complexity.

Response format (JSON):
{{
    "adjusted_question": "Modified question text",
    "difficulty_level": "{target_difficulty}",
    "changes_made": ["List of specific changes"],
    "bloom_level": "Updated Bloom's level"
}}
"""
        return prompt

    def get_batch_generation_prompt(
        self, context: str, num_questions: int, requirements: dict[str, Any]
    ) -> str:
        """Generate prompt for batch question generation."""

        difficulty = requirements.get("difficulty", "medium")
        topics = requirements.get("topics", [])
        question_types = requirements.get("question_types", ["multiple_choice"])

        topics_text = (
            f"Focus on these topics: {', '.join(topics)}"
            if topics
            else "Cover various topics from the content"
        )

        prompt = f"""
Generate {num_questions} diverse, high-quality quiz questions from the following context.

Context:
{context}

Requirements:
- Difficulty: {difficulty}
- Question types: {', '.join(question_types)}
- {topics_text}
- Ensure questions cover different aspects of the content
- Avoid repetitive or similar questions
- Each question should be educational and meaningful

Response format (JSON):
{{
    "questions": [
        {{
            "question_text": "Question text",
            "question_type": "multiple_choice",
            "options": [
                {{"label": "A", "text": "Option A"}},
                {{"label": "B", "text": "Option B"}},
                {{"label": "C", "text": "Option C"}},
                {{"label": "D", "text": "Option D"}}
            ],
            "correct_answer": "A",
            "explanation": "Explanation",
            "difficulty_level": "{difficulty}",
            "bloom_level": "Bloom's level",
            "topic": "Question topic"
        }}
    ]
}}

Generate {num_questions} questions:
"""
        return prompt
