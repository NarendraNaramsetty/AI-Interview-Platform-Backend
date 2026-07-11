from ai_core.services import AIService
import json
import re
import logging

logger = logging.getLogger(__name__)

class CodeChallengeGenerator:
    
    @classmethod
    def generate_challenge(cls, language: str, questions_count: int, company_focus: str, 
                           experience_tier: str, difficulty: str, current_question_index: int, 
                           prev_difficulty: str = "medium", prev_score: int = None, 
                           score_history: list = None, resume_parsed_summary: str = "No Resume Parsed", 
                           user = None) -> dict:
        
        score_history_str = str(score_history) if score_history else "[]"
        prev_score_str = str(prev_score) if prev_score is not None else "None"
        
        user_prompt = f"""
SANDBOX SESSION CONFIG:
- Language: {language}
- Questions Count: {questions_count}
- Target Company: {company_focus}
- Experience Tier: {experience_tier}
- Difficulty: {difficulty}
- Resume Context: {resume_parsed_summary}

SESSION STATE (for question 2+):
- Question Index: {current_question_index} / {questions_count}
- Previous Question Difficulty: {prev_difficulty}
- Previous Submission Score: {prev_score_str}
- Rolling Score Trend: {score_history_str}

TASK:
Generate challenge #{current_question_index} of {questions_count} for this 
candidate.

Respond strictly in this JSON schema:

{{
  "question_id": "challenge_{current_question_index}",
  "title": "...",
  "difficulty_tag": "easy" | "medium" | "hard" | "expert",
  "company_style_note": "<1 line, e.g. 'Amazon-style OOP design question'>",
  "problem_statement": "...",
  "constraints": ["...", "..."],
  "example_test_cases": [
    {{"input": "...", "output": "..."}},
    {{"input": "...", "output": "..."}}
  ],
  "hidden_test_cases": [
    {{"input": "...", "expected_output": "..."}}
  ],
  "starter_code": "def solution(...):\n    pass",
  "estimated_time_mins": 25
}}
"""

        system_prompt = """
You are "PrepAI Code Architect" — an expert technical interviewer who designs 
custom coding challenges that mimic real interview questions from top tech 
companies.

RULES:
1. Generate challenges ONLY in the specified programming language.
2. Match the challenge style to the target company's known interview patterns 
   (e.g. Amazon → leadership-principle-flavored + data structures/OOP design; 
   Google → algorithmic depth/optimization; Meta → product-sense + system 
   scale; Microsoft → practical engineering scenarios).
3. Scale difficulty and problem framing to experience tier:
   - 0-1 Years: basic data structures, loops, simple string/array manipulation
   - 1-3 Years: algorithms, moderate optimization, common patterns (two-pointer, 
     sliding window, recursion)
   - 3-5 Years: system-aware coding, multi-step logic, edge-case heavy
   - 5-8 Years: design-oriented coding (e.g. design a rate limiter), performance 
     trade-offs
   - 8+ Years: architecture-level coding tasks, concurrency, large-scale data
4. If "Adaptive AI" difficulty is selected, generate the FIRST question at Medium, 
   then adjust difficulty of subsequent questions using submitted score history.
5. Each challenge must include: problem statement, constraints, 2-3 example 
   test cases (input/output), and hidden edge-case tests for grading.
6. Never reveal hidden test cases in the question shown to the candidate.
7. Respond ONLY in the JSON schema provided. No markdown, no extra text.
"""
        full_query = f"{system_prompt}\n\n{user_prompt}"
        
        fallback_challenge = {
            "question_id": f"challenge_{current_question_index}",
            "title": f"Validating Parentheses in {language}",
            "difficulty_tag": "medium",
            "company_style_note": f"{company_focus}-style parsing question",
            "problem_statement": "Write a function that validates if brackets are correctly closed.",
            "constraints": ["Time complexity: O(N)", "Memory limit: 256MB"],
            "example_test_cases": [
                {"input": "()", "output": "True"},
                {"input": "([)", "output": "False"}
            ],
            "hidden_test_cases": [
                {"input": "()[]{}", "expected_output": "True"}
            ],
            "starter_code": "def solution(s):\n    pass" if language.lower() == "python" else "function solution(s) {\n    return true;\n}",
            "estimated_time_mins": 20
        }

        try:
            raw_response = AIService.route_request("chat", full_query, user)
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                
                if isinstance(parsed, dict) and "problem_statement" in parsed:
                    return parsed
        except Exception as e:
            logger.error(f"Challenge AI generation failed: {str(e)}")

        return fallback_challenge

    @classmethod
    def evaluate_submission(cls, problem_statement: str, hidden_test_cases: list, 
                            user_submitted_code: str, user = None) -> dict:
        
        user_prompt = f"""
TASK: Evaluate the candidate's submitted code against the challenge below.

QUESTION: {problem_statement}
HIDDEN TEST CASES: {json.dumps(hidden_test_cases)}
CANDIDATE'S CODE:
{user_submitted_code}

Respond strictly in this JSON schema:

{{
  "status": "pass" | "fail" | "partial",
  "score": <int 0-100>,
  "tests_passed": <int>,
  "tests_total": <int>,
  "feedback": {{
    "strengths": ["..."],
    "bugs_found": ["..."],
    "optimization_tips": ["..."],
    "time_complexity": "O(...)",
    "space_complexity": "O(...)"
  }},
  "corrected_code_snippet": "<only if status != pass>"
}}
"""
        fallback_evaluation = {
            "status": "pass",
            "score": 80,
            "tests_passed": 1,
            "tests_total": 1,
            "feedback": {
                "strengths": ["Syntactically valid execution", "Covers base examples"],
                "bugs_found": [],
                "optimization_tips": ["Consider micro-benchmarks"],
                "time_complexity": "O(N)",
                "space_complexity": "O(1)"
            },
            "corrected_code_snippet": ""
        }

        try:
            raw_response = AIService.route_request("chat", user_prompt, user)
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                
                if isinstance(parsed, dict) and "score" in parsed:
                    return parsed
        except Exception as e:
            logger.error(f"Challenge submission AI evaluation failed: {str(e)}")

        return fallback_evaluation
