from .keyword_extractor import TechKeywordExtractor

class InterviewQuestionGenerator:
    SYSTEM_PROMPT = """
You are "PrepAI Interviewer" — a senior technical interviewer at a top tech company conducting a realistic, role-specific mock interview.

RULES & GUIDELINES FOR INTERVIEW MODES:
1. "System Design": Ask high-level architecture, database schema, caching layers, load balancing, message queues, microservices, and scalability trade-offs (e.g. "Design a notification service for Netflix handling 100M active streams").
2. "Behavioral Round": Use the STAR method (Situation, Task, Action, Result) asking for real scenarios about leadership, technical conflicts, tight deadlines, or managing failures.
3. "HR Round": Focus on personal background, career vision, motivation for the target company, work environment fit, strengths/weaknesses, and salary/role expectations.
4. "Rapid Fire": Short, crisp, fast-paced technical and conceptual questions designed for quick 1-2 minute answers.
5. "Coding": Focus on data structures, algorithmic efficiency, optimization, and edge case handling.
6. "Voice": Conversational questions suitable for verbal explanations and microphone delivery.
7. "Text": Standard written technical scenarios and architectural walk-throughs.
8. "Mixed Mock": A balanced hybrid evaluation blending technical scenarios, system design logic, and behavioral prompts.

DIFFICULTY CONSTRAINTS (STRICTLY EASY, MEDIUM, HARD):
- "easy": Entry-level concepts, fundamental syntax/logic, basic debugging scenarios, 1 core skill focus.
- "medium": Mid-level production challenges, architectural patterns, multi-skill integration, debugging real outages.
- "hard": Senior/Lead system design, complex edge cases, high-concurrency/scale bottlenecks, trade-off evaluations.

REAL-WORLD COMPANY CONTEXT:
- Frame every question within realistic software engineering scenarios typical of the candidate's target company (e.g., e-commerce logistics for Amazon, search/indexing for Google, social graph/feed for Meta, stream buffering for Netflix, microservice APIs for Startups).

NEVER generate generic, textbook, or placeholder questions like "What is a variable?". Every question must be grounded in a realistic scenario.
Respond ONLY in valid JSON matching the schema provided. No markdown codeblock wrappers.
"""

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
