"""Profile Builder - AI-powered interactive profile creation for MooAId."""

from dataclasses import dataclass, field
from typing import Literal

from mooaid.core import AIProvider, GenerationResult
from mooaid.profile import ProfileData


@dataclass
class QuestionCategory:
    """A category of questions for profile building."""

    name: str
    description: str
    field: Literal["preferences", "values", "personality", "context"]
    question_count: int = 3


@dataclass
class ProfileBuilderState:
    """State for the profile building session."""

    profile_name: str
    current_question: str = ""
    current_category: str = ""
    answers: list[str] = field(default_factory=list)
    question_history: list[dict] = field(default_factory=list)
    is_complete: bool = False
    profile_data: ProfileData | None = None


class ProfileBuilder:
    """AI-powered profile builder that asks questions and psychoanalyzes answers."""

    # Question categories for profile building
    CATEGORIES = [
        QuestionCategory(
            name="Interests & Hobbies",
            description="What you enjoy doing in your free time",
            field="preferences",
            question_count=3,
        ),
        QuestionCategory(
            name="Core Values",
            description="Your fundamental beliefs and principles",
            field="values",
            question_count=3,
        ),
        QuestionCategory(
            name="Personality Traits",
            description="How you think and interact with the world",
            field="personality",
            question_count=3,
        ),
        QuestionCategory(
            name="Life Context",
            description="Your background, work, and environment",
            field="context",
            question_count=2,
        ),
    ]

    # System prompt for the profile builder AI
    SYSTEM_PROMPT = """You are MooAId's Profile Builder, an AI psychologist designed to understand a person's personality, preferences, values, and context.

Your role is to:
1. Ask thoughtful, open-ended questions that reveal insights about the person
2. Analyze their answers to extract key traits, preferences, values, and context
3. Build a comprehensive psychological profile

QUESTION ASKING GUIDELINES:
- Ask one question at a time
- Questions should be open-ended (not yes/no)
- Adapt follow-up questions based on previous answers
- Be conversational, friendly, and genuinely curious
- Avoid repetitive or overly personal questions
- Make questions relevant to understanding their worldview

PSYCHOANALYSIS GUIDELINES:
When analyzing answers, look for:
- PREFERENCES: Things they like/dislike, enjoy, prefer
- VALUES: Core beliefs, principles, what matters to them
- PERSONALITY: How they think, make decisions, interact (analytical, creative, pragmatic, etc.)
- CONTEXT: Their background, work, environment, life situation

Be nuanced in your analysis. People often reveal multiple traits in a single answer.
Look for patterns, contradictions, and unique perspectives.

IMPORTANT: Always be respectful and never make assumptions about sensitive topics."""

    # Prompt for generating the next question
    QUESTION_PROMPT = """You are building a psychological profile for a user named "{profile_name}".

Current session state:
- Category: {category} ({category_desc})
- Questions asked so far: {questions_asked}
- Previous answers: {answers}

Your task: Generate the next question to ask.

Guidelines:
1. The question should help reveal information relevant to the "{field}" category
2. If this is the first question in the category, start broad
3. If there are previous answers, ask a follow-up that digs deeper
4. Keep the question conversational and natural
5. Avoid yes/no questions - ask "what", "how", "why" questions
6. Reference their previous answers when relevant to show you're listening

Generate ONE question only. Do not add any commentary or explanation."""

    # Prompt for psychoanalyzing answers and extracting profile data
    ANALYSIS_PROMPT = """You are analyzing a user's answers to build their psychological profile.

Profile name: {profile_name}

Category being analyzed: {category} ({field})

Questions and Answers:
{qa_pairs}

Your task: Extract profile information from these answers.

Analyze the answers and extract:
1. PREFERENCES: Specific likes, dislikes, interests, hobbies mentioned
2. VALUES: Core beliefs, principles, or ideals expressed
3. PERSONALITY: Traits about how they think, decide, or interact
4. CONTEXT: Background information, work, life situation

Be specific and quote directly from their answers when possible.
Don't over-interpret - only extract what's reasonably supported by their words.

Respond in the following JSON format:
{{
    "preferences": ["preference1", "preference2", ...],
    "values": ["value1", "value2", ...],
    "personality": ["trait1", "trait2", ...],
    "context": ["context1", "context2", ...],
    "summary": "A brief 1-2 sentence summary of what you learned about this person"
}}

Only include items that are actually supported by the answers. Empty arrays are fine."""

    def __init__(self, provider: AIProvider, model: str | None = None) -> None:
        """Initialize the profile builder.

        Args:
            provider: The AI provider to use for generation.
            model: Optional model override.
        """
        self.provider = provider
        self.model = model
        self.state: ProfileBuilderState | None = None

    async def start_session(self, profile_name: str) -> ProfileBuilderState:
        """Start a new profile building session.

        Args:
            profile_name: Name for the profile being created.

        Returns:
            ProfileBuilderState: The initial session state.
        """
        self.state = ProfileBuilderState(profile_name=profile_name)
        return self.state

    async def generate_question(self) -> str:
        """Generate the next question to ask.

        Returns:
            str: The generated question.

        Raises:
            RuntimeError: If no session is active.
        """
        if self.state is None:
            raise RuntimeError("No active session. Call start_session() first.")

        # Determine current category and question count
        category_index = len(self.state.question_history) // 3  # 3 questions per category
        if category_index >= len(self.CATEGORIES):
            self.state.is_complete = True
            return ""

        category = self.CATEGORIES[category_index]
        question_in_category = len(self.state.question_history) % category.question_count

        self.state.current_category = category.name

        # Count questions asked in this category
        questions_asked = sum(
            1 for qh in self.state.question_history
            if qh.get("category") == category.name
        )

        # Build the prompt
        prompt = self.QUESTION_PROMPT.format(
            profile_name=self.state.profile_name,
            category=category.name,
            category_desc=category.description,
            field=category.field,
            questions_asked=questions_asked,
            answers=self.state.answers[-3:] if self.state.answers else "None yet",
        )

        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"

        # Generate the question
        result: GenerationResult = await self.provider.generate(full_prompt, model=self.model)
        question = result.content.strip() if result.content else "Tell me more about yourself."

        # Update state
        self.state.current_question = question
        self.state.question_history.append({
            "category": category.name,
            "field": category.field,
            "question": question,
        })

        return question

    async def submit_answer(self, answer: str) -> dict:
        """Submit an answer and get analysis.

        Args:
            answer: The user's answer to the question.

        Returns:
            dict: Analysis results with extracted profile data.

        Raises:
            RuntimeError: If no session is active.
        """
        if self.state is None:
            raise RuntimeError("No active session. Call start_session() first.")

        # Store the answer
        self.state.answers.append(answer)

        # Update the last question with the answer
        if self.state.question_history:
            self.state.question_history[-1]["answer"] = answer

        # Get the current category's field
        current_category = None
        for cat in self.CATEGORIES:
            if cat.name == self.state.current_category:
                current_category = cat
                break

        if current_category is None:
            return {"preferences": [], "values": [], "personality": [], "context": [], "summary": ""}

        # Build QA pairs for analysis
        qa_pairs = "\n\n".join([
            f"Q: {qh['question']}\nA: {qh.get('answer', 'No answer')}"
            for qh in self.state.question_history
            if qh.get("category") == current_category.name and qh.get("answer")
        ])

        # Analyze the answers
        prompt = self.ANALYSIS_PROMPT.format(
            profile_name=self.state.profile_name,
            category=current_category.name,
            field=current_category.field,
            qa_pairs=qa_pairs,
        )

        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"

        result: GenerationResult = await self.provider.generate(full_prompt, model=self.model)

        # Parse the JSON response
        import json
        import re

        # Try to extract JSON from the response
        json_match = re.search(r'\{[\s\S]*\}', result.content)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
            except json.JSONDecodeError:
                analysis = {
                    "preferences": [],
                    "values": [],
                    "personality": [],
                    "context": [],
                    "summary": result.content,
                }
        else:
            analysis = {
                "preferences": [],
                "values": [],
                "personality": [],
                "context": [],
                "summary": result.content,
            }

        return analysis

    async def complete_session(self) -> ProfileData:
        """Complete the session and return the final profile.

        Returns:
            ProfileData: The complete profile data.

        Raises:
            RuntimeError: If no session is active.
        """
        if self.state is None:
            raise RuntimeError("No active session. Call start_session() first.")

        # Aggregate all extracted data from answers
        profile_data = ProfileData(
            preferences=[],
            values=[],
            personality=[],
            context=[],
        )

        # Re-analyze all Q&A pairs for final profile
        for category in self.CATEGORIES:
            qa_pairs = "\n\n".join([
                f"Q: {qh['question']}\nA: {qh.get('answer', 'No answer')}"
                for qh in self.state.question_history
                if qh.get("category") == category.name and qh.get("answer")
            ])

            if not qa_pairs:
                continue

            prompt = self.ANALYSIS_PROMPT.format(
                profile_name=self.state.profile_name,
                category=category.name,
                field=category.field,
                qa_pairs=qa_pairs,
            )

            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"
            result: GenerationResult = await self.provider.generate(full_prompt, model=self.model)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', result.content)
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                    # Add to profile, avoiding duplicates
                    for item in analysis.get("preferences", []):
                        if item not in profile_data.preferences:
                            profile_data.preferences.append(item)
                    for item in analysis.get("values", []):
                        if item not in profile_data.values:
                            profile_data.values.append(item)
                    for item in analysis.get("personality", []):
                        if item not in profile_data.personality:
                            profile_data.personality.append(item)
                    for item in analysis.get("context", []):
                        if item not in profile_data.context:
                            profile_data.context.append(item)
                except json.JSONDecodeError:
                    pass

        self.state.is_complete = True
        self.state.profile_data = profile_data

        return profile_data

    def get_progress(self) -> dict:
        """Get the current progress of the session.

        Returns:
            dict: Progress information.
        """
        if self.state is None:
            return {"complete": False, "category": None, "question_count": 0, "total_questions": 11}

        total_questions = sum(cat.question_count for cat in self.CATEGORIES)
        current_category_idx = len(self.state.question_history) // 3

        return {
            "complete": self.state.is_complete,
            "current_category": self.state.current_category,
            "category_index": current_category_idx,
            "total_categories": len(self.CATEGORIES),
            "questions_answered": len([q for q in self.state.question_history if q.get("answer")]),
            "total_questions": total_questions,
            "progress_percent": int(len([q for q in self.state.question_history if q.get("answer")]) / total_questions * 100),
        }
