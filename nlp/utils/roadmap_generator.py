"""
Roadmap Generator - PrepAI Roadmap Architect
Generates personalized, comprehensive, genuinely useful learning roadmaps based on user interest.
Uses LLM to infer starting level and create structured milestones, prerequisites, and a complete role preparation guide.
"""

import json
import re
from typing import Optional, Dict, Any


def generate_roadmap(
    user_interest_text: str,
    self_described_experience: Optional[str] = None,
    resume_context_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive, personalized learning roadmap based on user interest.

    Args:
        user_interest_text: What the user wants to become/learn (e.g., "QA Engineer")
        self_described_experience: Optional - user's self-described background
        resume_context_summary: Optional - summary from connected resume

    Returns:
        Dict with pathway_title, inferred_starting_level, prerequisites, preparation_guide, milestones, etc.
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
    system_prompt = """You are "PrepAI Roadmap Architect" — an expert career mentor who designs comprehensive, highly detailed, personalized learning roadmaps and preparation documentation based on a candidate's stated interest or target role.

RULES:
1. Provide a COMPREHENSIVE learning roadmap. Do not make it too simple. A complete roadmap should have 5-10 detailed milestones to fully prepare a candidate from core basics to advanced/interview-ready levels.
2. Every milestone must be GENUINELY USEFUL — including real-world relevance, estimated commitment hours, and key topics.
3. Infer the right starting difficulty tier (Beginner, Intermediate, or Advanced) from how the user describes themselves.
4. Order milestones in a logical learning sequence: foundations first, then tools/frameworks, then real-world application, then interview readiness.
5. Provide "Prerequisites & Basics" (what he wants to know earlier / basic knowledge they should check off before starting).
6. Provide a complete "Role Preparation Guide" detailing a concrete strategy, key focus areas, mock interview advice, and recommended learning resources to help them prepare completely for that role.
7. Respond ONLY in the JSON schema provided. No markdown block wrapper, no preamble."""

    # User prompt with the task
    user_prompt = f"""Based on the following context, generate a complete learning roadmap and preparation documentation.

{context_str}

TASK: Generate a realistic, detailed roadmap with prerequisites and a prep guide that will prepare them completely for their target goal.

Respond STRICTLY in this JSON schema (no markdown block wrapper, no preamble, no tail):
{{
  "pathway_title": "...",
  "inferred_starting_level": "Beginner" | "Intermediate" | "Advanced",
  "inferred_level_reason": "<1 line explaining why>",
  "overall_readiness_estimate_percent": <int 0-100>,
  "prerequisites": [
    "Prerequisite skill or basic concept 1",
    "Prerequisite skill or basic concept 2"
  ],
  "preparation_guide": {{
    "strategy": "Detailed strategy explanation on how to completely prepare for the role.",
    "focus_areas": ["Focus area 1", "Focus area 2", "Focus area 3"],
    "interview_tips": ["Interview tip 1", "Interview tip 2"],
    "recommended_resources": ["Official documentation link or book 1", "Practice resource 2"]
  }},
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

    # Normalize/Validate prerequisites
    if "prerequisites" not in data or not isinstance(data["prerequisites"], list):
        data["prerequisites"] = []
    
    # Normalize/Validate preparation_guide
    if "preparation_guide" not in data or not isinstance(data["preparation_guide"], dict):
        data["preparation_guide"] = {
            "strategy": "No strategy provided.",
            "focus_areas": [],
            "interview_tips": [],
            "recommended_resources": []
        }
    else:
        guide = data["preparation_guide"]
        if "strategy" not in guide or not isinstance(guide["strategy"], str):
            guide["strategy"] = "No strategy provided."
        if "focus_areas" not in guide or not isinstance(guide["focus_areas"], list):
            guide["focus_areas"] = []
        if "interview_tips" not in guide or not isinstance(guide["interview_tips"], list):
            guide["interview_tips"] = []
        if "recommended_resources" not in guide or not isinstance(guide["recommended_resources"], list):
            guide["recommended_resources"] = []

    # Validate milestones
    if not isinstance(data["milestones"], list) or len(data["milestones"]) == 0:
        raise ValueError("Milestones must be a non-empty list")

    if len(data["milestones"]) > 10:
        raise ValueError("Roadmap should have at most 10 milestones")

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