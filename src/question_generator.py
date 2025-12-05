"""
Question Generator for Sisters-AWS-Coach v2
Generates AWS quiz questions using LLM with character personalities
"""

import random
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.llm import BedrockLLM
from src.database import get_suggested_tags, get_all_categories


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"


# Character configuration
CHARACTERS = {
    "Botan": {
        "prompt_file": "botan_generate_prompt.txt",
        "difficulty": "beginner",
        "focus": "analogies and basics"
    },
    "Kasho": {
        "prompt_file": "kasho_generate_prompt.txt",
        "difficulty": "intermediate",
        "focus": "cost and business"
    },
    "Yuri": {
        "prompt_file": "yuri_generate_prompt.txt",
        "difficulty": "advanced",
        "focus": "technical details and architecture"
    },
    "Ojisan": {
        "prompt_file": "ojisan_generate_prompt.txt",
        "difficulty": "practical",
        "focus": "security and real-world experience"
    }
}


class QuestionGenerator:
    """Generates AWS quiz questions using LLM"""

    def __init__(self):
        self.llm = BedrockLLM()
        self._prompt_cache: Dict[str, str] = {}

    def _load_prompt(self, character: str) -> str:
        """Load character-specific prompt from file"""
        if character in self._prompt_cache:
            return self._prompt_cache[character]

        config = CHARACTERS.get(character)
        if not config:
            raise ValueError(f"Unknown character: {character}")

        prompt_file = PROMPTS_DIR / config["prompt_file"]
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()

        self._prompt_cache[character] = prompt
        return prompt

    def generate_question(
        self,
        character: str,
        user_id: Optional[str] = None,
        focus_tags: Optional[List[str]] = None,
        language: str = "ja"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a question for the specified character.

        Args:
            character: Character name (Botan, Kasho, Yuri, Ojisan)
            user_id: Optional user ID for personalized weakness focus
            focus_tags: Optional specific tags to focus on
            language: 'ja' or 'en'

        Returns:
            Question dict or None if generation failed
        """
        # Load character prompt
        prompt_content = self._load_prompt(character)

        # Get focus tags from weakness analysis if not specified
        if not focus_tags and user_id:
            focus_tags = get_suggested_tags(user_id, count=2)

        # If still no focus tags, pick random categories
        if not focus_tags:
            all_categories = get_all_categories()
            focus_tags = random.sample(all_categories, min(2, len(all_categories)))

        # Generate question using LLM
        question = self.llm.generate_question(
            character=character,
            prompt_content=prompt_content,
            focus_tags=focus_tags,
            language=language
        )

        if question:
            # Add metadata
            question["character"] = character
            question["language"] = language
            question["difficulty"] = CHARACTERS[character]["difficulty"]

        return question

    def generate_explanation(
        self,
        character: str,
        question_text: str,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
        language: str = "ja"
    ) -> str:
        """
        Generate character-specific explanation for the user's answer.

        Args:
            character: Character name
            question_text: The original question
            user_answer: User's selected answer
            correct_answer: The correct answer
            is_correct: Whether the user was correct
            language: 'ja' or 'en'

        Returns:
            Explanation text in character's voice
        """
        prompt_content = self._load_prompt(character)

        return self.llm.generate_explanation(
            character=character,
            prompt_content=prompt_content,
            question_text=question_text,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            language=language
        )


# Singleton instance
_generator: Optional[QuestionGenerator] = None


def get_generator() -> QuestionGenerator:
    """Get singleton QuestionGenerator instance"""
    global _generator
    if _generator is None:
        _generator = QuestionGenerator()
    return _generator


def generate_question(
    character: str,
    user_id: Optional[str] = None,
    focus_tags: Optional[List[str]] = None,
    language: str = "ja"
) -> Optional[Dict[str, Any]]:
    """Convenience function to generate a question"""
    return get_generator().generate_question(
        character=character,
        user_id=user_id,
        focus_tags=focus_tags,
        language=language
    )


def generate_explanation(
    character: str,
    question_text: str,
    user_answer: str,
    correct_answer: str,
    is_correct: bool,
    language: str = "ja"
) -> str:
    """Convenience function to generate explanation"""
    return get_generator().generate_explanation(
        character=character,
        question_text=question_text,
        user_answer=user_answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        language=language
    )
