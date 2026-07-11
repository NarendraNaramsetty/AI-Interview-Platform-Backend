from .keyword_extractor import TechKeywordExtractor

class InterviewQuestionGenerator:
    SYSTEM_PROMPT = """
You are "PrepAI Interviewer" — a senior technical interviewer at a top tech 
company conducting a realistic, role-specific mock interview.

RULES:
1. NEVER generate generic, textbook, or placeholder questions like 
   "What is a variable?" or "Explain OOP". Every question must reflect a 
   REAL scenario a candidate at the given experience level would actually 
   face on the job.
2. Base every question ONLY on the candidate's selected tech stack. Do not 
   ask about tools/frameworks not selected.
3. Question style must match experience level:
   - Fresher/Junior: "Walk me through how you'd build X using {skill}"
   - Mid-Level: "You're seeing {symptom} in production — how do you 
     debug/design around it?"
   - Senior/Lead: "Design a {system} that handles {constraint} — what 
     trade-offs do you make?"
4. Prefer scenario-based framing over definitional framing.
5. Only ONE question per response. No multi-part bundling.
6. Respond ONLY in the JSON schema provided. No markdown, no preamble.
"""

    @classmethod
    def build_user_prompt(cls, session_config: dict, session_state: dict) -> str:
        return f"""
SESSION CONFIG:
- Target Role: {session_config['target_role']}
- Experience Level: {session_config['experience_level']}
- Difficulty: {session_config['difficulty']}
- Interview Mode: {session_config['interview_mode']}
- Selected Skills: {session_config['selected_skills_list']}
- Score Goal: {session_config['score_goal']}%
- Total Questions: {session_config['total_questions']}

SESSION STATE:
- Current Question Number: {session_state['current_question_index']} of {session_config['total_questions']}
- Previously Asked Questions: {session_state['previous_questions_list']}
- Last Answer Submitted: "{session_state.get('last_answer_text', '')}"
- Last Answer Score: {session_state.get('last_score')}
- Adaptive Mode: {session_config.get('adaptive_mode_enabled', False)}

TASK:
Generate question #{session_state['current_question_index']}. It must be a 
REALISTIC, scenario-based question grounded in the selected skills. Do NOT 
repeat any question in previous_questions_list.

Respond strictly in this JSON schema:
{{
  "question_id": "q_{session_state['current_question_index']}",
  "question_number": {session_state['current_question_index']},
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
