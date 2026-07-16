"""
Roadmap Generator - PrepAI Roadmap Architect
Generates personalized, simple, genuinely useful learning roadmaps based on user interest.
Uses LLM to infer starting level and create 4-6 focused milestones.
"""

import json
import re
from typing import Optional, Dict, Any
import anthropic


def generate_roadmap(
    user_interest_text: str,
    self_described_experience: Optional[str] = None,
    resume_context_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a simplified, personalized learning roadmap based on user interest.

    Args:
        user_interest_text: What the user wants to become/learn (e.g., "QA Engineer")
        self_described_experience: Optional - user's self-described background
        resume_context_summary: Optional - summary from connected resume

    Returns:
        Dict with pathway_title, inferred_starting_level, milestones, etc.
        Matches the JSON schema exactly.
    """

    # Build context for the LLM
    context_parts = [
        f"User Interest: {user_interest_text}"
    ]

    if self_described_experience:
        context_parts.append(f"Self-Described Experience: {self_described_experience}")

    if resume_context_summary:
        context_parts.append(f"Resume Context: {resume_context_summary}")

    context_str = "\n".join(context_parts)

    # System prompt - the "PrepAI Roadmap Architect" persona
    system_prompt = """You are "PrepAI Roadmap Architect" — an expert career mentor who designs simple, genuinely useful, personalized learning roadmaps based on a candidate's stated interest or target role.

RULES:
1. Keep it SIMPLE. Do not over-engineer the roadmap with excessive nodes, sub-tracks, or jargon. A good roadmap has 4-6 clear milestones, not 15.
2. Every milestone must be GENUINELY USEFUL — something the candidate would actually need to learn/practice for real job readiness, not filler topics added just to make the roadmap look comprehensive.
3. Infer the right starting difficulty tier from how the user describes themselves (e.g. "I'm new to testing" → Beginner; "I've done manual QA for 2 years, want to move to automation" → Intermediate).
4. Order milestones in a logical learning sequence — foundational concepts first, then tools/frameworks, then real-world application, then interview readiness.
5. Each milestone must include a short reason WHY it matters for the target role, not just a title — this is what makes it feel genuine vs generic.
6. Avoid duplicate or overlapping milestones. Each one should teach something distinct.
7. Give a realistic estimated learning time per milestone, based on typical part-time self-study pace (5-8 hrs/week).
8. Respond ONLY in the JSON schema provided. No markdown, no preamble."""

    # User prompt with the task
    user_prompt = f"""Based on the following context, generate a SIMPLE, genuine, 4-6 milestone learning roadmap.

{context_str}

TASK: Generate a realistic roadmap that will prepare them for their stated goal. Infer the appropriate starting difficulty automatically.

Respond STRICTLY in this JSON schema (no markdown, no preamble):
{{
  "pathway_title": "...",
  "inferred_starting_level": "Beginner" | "Intermediate" | "Advanced",
  "inferred_level_reason": "<1 line explaining why>",
  "overall_readiness_estimate_percent": <int 0-100>,
  "milestones": [
    {{
      "milestone_number": 1,
      "title": "...",
      "difficulty_tag": "Beginner" | "Intermediate" | "Advanced",
      "description": "...",
      "why_it_matters": "<1-2 lines, genuine real-world relevance>",
      "estimated_hours": <int>,
      "key_topics": ["...", "...", "..."]
    }}
  ]
}}"""

    # Call AI Service router
    from ai_core.services import AIService
    
    full_prompt = f"{system_prompt}\n\n[USER INPUT]:\n{user_prompt}"

    try:
        res = AIService.route_request("Chat", full_prompt)
        response_text = res.get("response", "").strip()

        # Try to parse JSON - handle potential markdown formatting
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group()

        roadmap_data = json.loads(response_text)

        # Validate schema
        roadmap_data = _validate_and_normalize_roadmap(roadmap_data)

        return roadmap_data

    except json.JSONDecodeError as e:
        # Fallback: return error response
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        raise ValueError(f"API error calling AI Service: {type(e).__name__}: {str(e)}")


def _validate_and_normalize_roadmap(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate roadmap data matches schema and normalize it.
    Ensures all required fields are present and correctly typed.
    """

    # Required top-level fields
    required_fields = [
        "pathway_title",
        "inferred_starting_level",
        "inferred_level_reason",
        "overall_readiness_estimate_percent",
        "milestones"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate levels
    valid_levels = ["Beginner", "Intermediate", "Advanced"]
    if data["inferred_starting_level"] not in valid_levels:
        raise ValueError(f"Invalid starting level: {data['inferred_starting_level']}")

    # Validate readiness percent
    readiness = data["overall_readiness_estimate_percent"]
    if not isinstance(readiness, int) or readiness < 0 or readiness > 100:
        raise ValueError(f"Readiness percent must be 0-100, got {readiness}")

    # Validate milestones
    if not isinstance(data["milestones"], list) or len(data["milestones"]) == 0:
        raise ValueError("Milestones must be a non-empty list")

    if len(data["milestones"]) > 6:
        raise ValueError("Roadmap should have 4-6 milestones, got more than 6")

    for i, milestone in enumerate(data["milestones"]):
        _validate_milestone(milestone, i + 1)

    return data


def _validate_milestone(milestone: Dict[str, Any], expected_number: int) -> None:
    """Validate a single milestone entry."""

    required_fields = [
        "milestone_number",
        "title",
        "difficulty_tag",
        "description",
        "why_it_matters",
        "estimated_hours",
        "key_topics"
    ]

    for field in required_fields:
        if field not in milestone:
            raise ValueError(f"Milestone missing required field: {field}")

    # Validate types
    if not isinstance(milestone["milestone_number"], int):
        raise ValueError("milestone_number must be an integer")

    if not isinstance(milestone["title"], str) or len(milestone["title"]) == 0:
        raise ValueError("title must be a non-empty string")

    valid_levels = ["Beginner", "Intermediate", "Advanced"]
    if milestone["difficulty_tag"] not in valid_levels:
        raise ValueError(f"Invalid difficulty_tag: {milestone['difficulty_tag']}")

    if not isinstance(milestone["description"], str) or len(milestone["description"]) == 0:
        raise ValueError("description must be a non-empty string")

    if not isinstance(milestone["why_it_matters"], str) or len(milestone["why_it_matters"]) == 0:
        raise ValueError("why_it_matters must be a non-empty string")

    if not isinstance(milestone["estimated_hours"], int) or milestone["estimated_hours"] <= 0:
        raise ValueError("estimated_hours must be a positive integer")

    if not isinstance(milestone["key_topics"], list) or len(milestone["key_topics"]) == 0:
        raise ValueError("key_topics must be a non-empty list of strings")

    for topic in milestone["key_topics"]:
        if not isinstance(topic, str) or len(topic) == 0:
            raise ValueError("Each key_topic must be a non-empty string")


def calculate_total_hours(milestones: list) -> int:
    """Calculate total estimated hours for all milestones."""
    return sum(m.get("estimated_hours", 0) for m in milestones)