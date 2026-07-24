import uuid
from .keyword_extractor import TechKeywordExtractor

class InterviewQuestionGenerator:
    COMPANY_SCENARIO_MAP = {
        "Amazon": "Logistics, fulfillment, scale. (e.g. 'Design a system to reprioritize warehouse pick-paths when a shipment is delayed')",
        "Netflix": "Streaming, recommendation, buffering. (e.g. 'A user's video buffer stutters intermittently on 4G — walk through your debugging approach')",
        "Google": "Search relevance, massive-scale infrastructure. (e.g. 'How would you reduce P99 latency on a query serving 1M req/s?')",
        "Meta": "Social graph, feed ranking, real-time sync. (e.g. 'Design a rate limiter for a comment-spam surge during a live event')",
        "Stripe": "Idempotency, consistency, fraud detection. (e.g. 'A payment webhook fires twice for the same transaction — how do you prevent double-charging?')",
        "Fintech": "Idempotency, consistency, fraud detection. (e.g. 'A payment webhook fires twice for the same transaction — how do you prevent double-charging?')",
        "Uber": "Geospatial, matching, real-time dispatch. (e.g. 'Two drivers get matched to the same rider due to a race condition — diagnose it')",
        "Lyft": "Geospatial, matching, real-time dispatch. (e.g. 'Two drivers get matched to the same rider due to a race condition — diagnose it')",
    }

    MODE_RULES = {
        "Text": "Standard written Q&A. The question text should be answerable in 3-6 sentences. No code is expected.",
        "Voice": "Conversational and shorter (one sentence setup + one sentence ask) since the candidate will speak the answer aloud.",
        "Coding": "Include I/O expectations and constraints (e.g. input size, time limit) since this feeds the Sandbox. Do NOT include full test cases.",
        "System Design": "Specify scale numbers (e.g. '10M DAU', '500 writes/sec') and explicitly ask for tradeoffs, not just a diagram ask.",
        "Behavioral": "Describe an interpersonal or ownership situation ('a teammate's PR breaks prod the night before a launch'), not a technical one. Use STAR-eliciting phrasing ('Tell me about a time when...', 'Walk me through how you handled...').",
        "HR": "Focus on motivation, culture fit, career trajectory — no technical scenario is needed. Keep to well-known HR question archetypes but personalize using the target role and company.",
        "Rapid Fire": "Answerable in <30 seconds. Prefer single-concept, low-ambiguity questions even at Medium/Hard difficulty.",
        "Mixed Mock": "Distribute questions roughly evenly across Technical, Behavioral, and System Design/Coding categories. Do not let one category dominate."
    }

    @classmethod
    def build_prompts(cls, role: str, company: str, difficulty: str, mode: str, skills: list, question_count: int, experience_level: str = "Mid-Level", resume_summary: str = None) -> tuple:
        # Resolve company flavor
        company_flavor = cls.COMPANY_SCENARIO_MAP.get(company, "General tech company engineering scale and operational stability.")
        
        # Resolve mode instructions
        mode_instruction = cls.MODE_RULES.get(mode, "Standard written technical and behavioral evaluation.")
        
        skills_str = ", ".join(skills) if skills else "General software development engineering concepts"
        
        system_prompt = f"""
You are a Staff Engineer at {company} conducting a real {mode} interview for a {role} candidate.
You do not ask generic textbook definition questions. Every question must be grounded in a specific, plausible engineering situation that could actually occur at {company}, matching this domain flavor:
Domain Flavor: {company_flavor}

HARD RULES:
1. Never ask 'What is X?' or 'Explain the difference between X and Y' in isolation. Instead, embed the concept inside a scenario the candidate must reason through.
2. Each question must reference a concrete situation: a metric, a failure mode, a scale number, or a business constraint — not an abstract topic.
3. Do not repeat the same underlying concept twice across the generated questions.
4. Match difficulty ({difficulty}) precisely:
   - Easy: one clear correct approach, minimal ambiguity, single skill area.
   - Medium: 2+ skills combined, one tradeoff to reason about, some missing info.
   - Hard: open-ended, multiple valid approaches, candidate must state assumptions.
5. Apply these mode-specific rules for {mode}:
   {mode_instruction}

DO NOT generate questions like:
- 'What is RAG and how does it work?'
- 'Explain the difference between SQL and NoSQL.'
- 'What is a rate limiter?'

INSTEAD, generate questions that require reasoning, such as:
- 'Your RAG system's retrieval step is fast, but generation quality drops when the corpus doubles — where would you look first?'
- 'A webhook fires twice for the same payment transaction on a high-throughput endpoint — how do you design the consumer to guarantee idempotency under a 50ms processing limit?'
"""

        user_prompt = f"""
Generate exactly {question_count} mock interview questions matching:
- Target Role: {role}
- Target Company: {company}
- Experience Level: {experience_level}
- Difficulty: {difficulty}
- Selected Tech Stack: {skills_str}
- Resume context: {resume_summary or 'No resume provided.'}

Respond strictly in this JSON array schema (no markdown fences, no preamble, no tail):
[
  {{
    "question_text": "Detailed question prompt conforming to the {mode} rules.",
    "topic": "Specific skill/topic name from the selected stack",
    "category": "Technical" | "Behavioral" | "System Design" | "Coding" | "HR",
    "expected_answer_placeholder": "High-level summary of what a strong answer should cover."
  }}
]
"""
        return system_prompt, user_prompt

    @classmethod
    def build_user_prompt(cls, session_config: dict, session_state: dict) -> str:
        mode = session_config.get('interview_mode', 'Text')
        company = session_config.get('target_company', 'Tech Company')
        difficulty = session_config.get('difficulty', 'Medium')
        role = session_config.get('target_role', 'Software Engineer')

        return f"""
SESSION CONFIG:
- Target Role: {role}
- Target Company: {company}
- Experience Level: {session_config.get('experience_level', 'mid')}
- Difficulty: {difficulty} (Strictly easy, medium, or hard)
- Interview Mode: {mode}
- Selected Skills: {session_config.get('selected_skills_list', [])}
- Score Goal: {session_config.get('score_goal', 85)}%
- Total Questions: {session_config.get('total_questions', 5)}

SESSION STATE:
- Current Question Number: {session_state.get('current_question_index', 1)} of {session_config.get('total_questions', 5)}
- Previously Asked Questions: {session_state.get('previous_questions_list', [])}
- Last Answer Submitted: "{session_state.get('last_answer_text', '')}"
- Last Answer Score: {session_state.get('last_score')}

TASK:
Generate question #{session_state.get('current_question_index', 1)} for this candidate in "{mode}" mode, targeting {company} at {difficulty} level for a {role} role.
It MUST strictly follow the format and expectations of the "{mode}" interview mode.

Respond strictly in this JSON schema:
{{
  "question_id": "q_{session_state.get('current_question_index', 1)}",
  "question_number": {session_state.get('current_question_index', 1)},
  "question_text": "...",
  "scenario_context": "...",
  "skill_focus": ["..."],
  "difficulty_tag": "easy" | "medium" | "hard",
  "expected_answer_points": ["...", "...", "..."],
  "time_suggestion_mins": 10
}}
"""

    @classmethod
    def enrich_skills_from_resume(cls, resume_text: str) -> list:
        """Optional: auto-fill selected_skills_list from Resume Sync using
        the existing TechKeywordExtractor."""
        return TechKeywordExtractor.extract_keywords(resume_text)["keywords"]
