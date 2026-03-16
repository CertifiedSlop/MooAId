"""Opinion prediction engine for MooAId."""

from dataclasses import dataclass
from typing import Any

from mooaid.core import AIProvider, GenerationResult
from mooaid.profile import ProfileData


@dataclass
class OpinionResult:
    """Result from opinion prediction."""

    predicted_opinion: str
    reasoning: str
    model: str
    provider: str
    profile_used: str | None = None


class OpinionEngine:
    """Engine for predicting opinions based on user profiles."""

    # System prompt that defines the AI's role
    SYSTEM_PROMPT = """You are MooAId, an AI opinion prediction system.

Your purpose is to predict what a specific person's opinion would likely be on a given topic.
You are NOT providing your own opinion or general advice.
You are analyzing the person's profile and predicting THEIR likely opinion.

Always frame your response as:
"Based on what I know about you, your likely opinion is..."

Be honest about uncertainties. If the profile doesn't provide enough context,
acknowledge that and make your best inference based on related traits.

LOCATION AWARENESS:
When the question involves travel, destinations, or locations, you may use your general knowledge
about popular places, travel destinations, and geographic information to make informed predictions
about where the person might want to visit or what they might think about certain locations.
Use your training data about:
- Popular tourist destinations
- Travel trends and preferences
- Geographic and cultural information
- Climate and seasonal considerations
- Activity-based destinations (beaches, mountains, cities, etc.)

IF NO PROFILE INFORMATION EXISTS:
If the person has NO profile information (no preferences, values, personality, or context):
1. First, provide your own balanced, unbiased AI perspective on the topic
2. Frame it as: "I don't have enough information about you yet, but here's a balanced perspective..."
3. Optionally, ask 1-2 relevant questions that would help you understand their preferences better
4. Make the questions friendly and optional - don't require answers
5. Example: "I don't have enough information about you yet. From a balanced perspective, [give unbiased view].
   If you'd like more personalized insights, you could tell me about [relevant topic]."

IMPORTANT: Never make up silly or absurd opinions. Always be helpful and respectful."""

    # Opinion prompt template
    OPINION_TEMPLATE = """
## Person Profile

{profile_data}

## Question

{question}

## Task

Predict what this person's opinion would likely be on the question above.

Requirements:
1. Start with: "Based on what I know about you, your likely opinion is..."
2. Explain the reasoning based on their profile traits
3. If the profile lacks relevant context, acknowledge this uncertainty
4. Be specific and reference their actual preferences/values/personality

Provide your response in the following format:

PREDICTED OPINION:
[Your prediction of their opinion]

REASONING:
[Your explanation of why they would likely hold this opinion]
"""

    def __init__(self, provider: AIProvider, model: str | None = None) -> None:
        """Initialize the opinion engine.

        Args:
            provider: The AI provider to use for generation.
            model: Optional model override. If provided, this model will be used
                  instead of the provider's default model.
        """
        self.provider = provider
        self.model = model

    def build_prompt(self, profile: ProfileData, question: str) -> str:
        """Build the prompt for opinion prediction.

        Args:
            profile: The user's profile data.
            question: The question to predict opinion on.

        Returns:
            str: The formatted prompt.
        """
        profile_data = profile.format_for_prompt()

        # Check if profile is empty
        is_empty = (
            len(profile.preferences) == 0 and
            len(profile.values) == 0 and
            len(profile.personality) == 0 and
            len(profile.context) == 0
        )

        if is_empty:
            # Add special instruction for empty profiles
            profile_data = "**NO PROFILE INFORMATION AVAILABLE**\n\nThis person has not provided any preferences, values, personality traits, or context. Please provide your balanced AI perspective and optionally ask questions to help build their profile."

        return self.OPINION_TEMPLATE.format(
            profile_data=profile_data, question=question
        )

    def parse_response(self, response: str) -> tuple[str, str]:
        """Parse the AI response into opinion and reasoning.

        Args:
            response: The raw AI response.

        Returns:
            tuple[str, str]: (opinion, reasoning)
        """
        opinion = response
        reasoning = ""

        # Try to extract structured sections
        if "PREDICTED OPINION:" in response and "REASONING:" in response:
            parts = response.split("REASONING:")
            opinion_part = parts[0].replace("PREDICTED OPINION:", "").strip()
            reasoning = parts[1].strip() if len(parts) > 1 else ""
            opinion = opinion_part
        elif "PREDICTED OPINION:" in response:
            opinion = response.split("PREDICTED OPINION:")[1].strip()
            # Try to find reasoning even without the marker
            if "because" in opinion.lower() or "since" in opinion.lower():
                # Split on common reasoning indicators
                for indicator in [" because ", " since ", " as ", " given "]:
                    if indicator in opinion.lower():
                        idx = opinion.lower().find(indicator)
                        reasoning = opinion[idx:].strip()
                        opinion = opinion[:idx].strip()
                        break
        else:
            # If no structured format, try to split on newlines
            lines = response.strip().split("\n\n")
            if len(lines) >= 2:
                opinion = lines[0].strip()
                reasoning = "\n\n".join(lines[1:]).strip()

        # Ensure opinion starts with the expected phrase
        if not opinion.lower().startswith("based on what i know about you"):
            opinion = f"Based on what I know about you, your likely opinion is: {opinion}"

        return opinion, reasoning

    async def predict(
        self, question: str, profile: ProfileData, profile_name: str | None = None
    ) -> OpinionResult:
        """Predict an opinion for the given question and profile.

        Args:
            question: The question to predict opinion on.
            profile: The user's profile data.
            profile_name: Optional profile name for reference.

        Returns:
            OpinionResult: The prediction result.
        """
        # Build the full prompt with system instruction
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{self.build_prompt(profile, question)}"

        # Generate response from AI using the selected model
        result: GenerationResult = await self.provider.generate(full_prompt, model=self.model)

        # Parse the response
        opinion, reasoning = self.parse_response(result.content)

        return OpinionResult(
            predicted_opinion=opinion,
            reasoning=reasoning,
            model=result.model,  # This will be the actual model used
            provider=result.provider,
            profile_used=profile_name,
        )

    async def predict_with_context(
        self,
        question: str,
        profile: ProfileData,
        additional_context: list[str],
        profile_name: str | None = None,
    ) -> OpinionResult:
        """Predict an opinion with additional temporary context.

        Args:
            question: The question to predict opinion on.
            profile: The user's profile data.
            additional_context: Additional context for this prediction only.
            profile_name: Optional profile name for reference.

        Returns:
            OpinionResult: The prediction result.
        """
        # Create a modified profile with additional context
        modified_profile = ProfileData(
            preferences=profile.preferences.copy(),
            values=profile.values.copy(),
            personality=profile.personality.copy(),
            context=profile.context.copy() + additional_context,
        )

        return await self.predict(question, modified_profile, profile_name)
