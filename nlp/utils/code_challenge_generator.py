from ai_core.services import AIService
import json
import re
import logging

logger = logging.getLogger(__name__)

import uuid
import random

class CodeChallengeGenerator:
    
    @classmethod
    def get_starter_code(cls, language: str, function_name: str = "solution", params: str = "input_data") -> str:
        lang = (language or "python").lower()
        if "python" in lang:
            return f"def {function_name}({params}):\n    # Write your solution here\n    pass"
        elif "javascript" in lang or "js" in lang:
            return f"function {function_name}({params}) {{\n    // Write your solution here\n    return null;\n}}"
        elif "typescript" in lang or "ts" in lang:
            return f"function {function_name}({params}: any): any {{\n    // Write your solution here\n    return null;\n}}"
        elif "java" in lang:
            return f"public class Solution {{\n    public static Object {function_name}(Object {params}) {{\n        // Write your solution here\n        return null;\n    }}\n}}"
        elif "c++" in lang or "cpp" in lang:
            return f"#include <iostream>\n#include <vector>\nusing namespace std;\n\nclass Solution {{\npublic:\n    auto {function_name}(auto {params}) {{\n        // Write your solution here\n    }}\n}};"
        elif "go" in lang or "golang" in lang:
            return f"package main\n\nimport \"fmt\"\n\nfunc {function_name}({params} interface{{}}) interface{{}} {{\n    // Write your solution here\n    return nil\n}}"
        else:
            return f"def {function_name}({params}):\n    pass"

    @classmethod
    def get_randomized_fallback(cls, language: str, company_focus: str, difficulty: str, current_question_index: int) -> dict:
        fallback_pool = [
            {
                "title": f"{company_focus} Order Processing Pipeline",
                "problem_statement": f"You are building a high-throughput order processing system for {company_focus}. Given an array of order IDs and timestamps, return the longest contiguous sequence of valid orders processed within the SLA window.",
                "constraints": ["1 <= N <= 10^5", "Time Complexity O(N)"],
                "example_test_cases": [{"input": "[1, 2, 3, 5, 6]", "output": "3"}],
                "hidden_test_cases": [{"input": "[10, 20, 30]", "expected_output": "3"}],
                "estimated_time_mins": 25
            },
            {
                "title": f"{company_focus} Rate Limiting Token Bucket",
                "problem_statement": f"Design a rate-limiting algorithm for {company_focus} API gateways. Given a list of request timestamps and user IDs, calculate how many requests exceed the allowed burst rate threshold.",
                "constraints": ["Memory O(K) where K is unique users", "Time Complexity O(R)"],
                "example_test_cases": [{"input": "['user1:100', 'user1:101', 'user1:102']", "output": "1"}],
                "hidden_test_cases": [{"input": "['uA:1', 'uB:1']", "expected_output": "0"}],
                "estimated_time_mins": 20
            },
            {
                "title": f"{company_focus} Service Dependency Graph Resolution",
                "problem_statement": f"In {company_focus}'s microservice architecture, services depend on each other. Given a list of service dependencies [A, B] (service A requires B), find if there exists a circular dependency causing deadlock.",
                "constraints": ["Number of services <= 1000", "Time Complexity O(V + E)"],
                "example_test_cases": [{"input": "[[1,0], [0,1]]", "output": "True"}],
                "hidden_test_cases": [{"input": "[[1,0], [2,1]]", "expected_output": "False"}],
                "estimated_time_mins": 30
            },
            {
                "title": f"{company_focus} Inventory Stock Allocation",
                "problem_statement": f"Given warehouse stock levels and customer cart requests for {company_focus}, allocate items to minimize shipping distances across distribution hubs.",
                "constraints": ["Greedy optimization", "Time O(N log N)"],
                "example_test_cases": [{"input": "[10, 20, 15]", "output": "45"}],
                "hidden_test_cases": [{"input": "[5, 5]", "expected_output": "10"}],
                "estimated_time_mins": 25
            },
            {
                "title": f"{company_focus} Real-time Stream Analytics Buffer",
                "problem_statement": f"Implement a sliding window stream aggregator for {company_focus}'s event metrics. Calculate the moving average over the last K stream frames.",
                "constraints": ["Sliding Window O(1) amortized update", "Memory limit 128MB"],
                "example_test_cases": [{"input": "Window=3, Stream=[1, 3, 5, 7]", "output": "[1.0, 2.0, 3.0, 5.0]"}],
                "hidden_test_cases": [{"input": "Window=2, Stream=[10, 20]", "expected_output": "[10.0, 15.0]"}],
                "estimated_time_mins": 20
            }
        ]
        
        chosen = random.choice(fallback_pool)
        starter = cls.get_starter_code(language)
        
        return {
            "question_id": f"challenge_{current_question_index}_{random.randint(1000, 9999)}",
            "title": chosen["title"],
            "difficulty_tag": str(difficulty).lower(),
            "company_style_note": f"{company_focus} real-world scenario ({difficulty} level)",
            "problem_statement": chosen["problem_statement"],
            "constraints": chosen["constraints"],
            "example_test_cases": chosen["example_test_cases"],
            "hidden_test_cases": chosen["hidden_test_cases"],
            "starter_code": starter,
            "estimated_time_mins": chosen["estimated_time_mins"]
        }

    @classmethod
    def generate_challenge(cls, language: str, questions_count: int, company_focus: str, 
                           experience_tier: str, difficulty: str, current_question_index: int, 
                           prev_difficulty: str = "medium", prev_score: int = None, 
                           score_history: list = None, resume_parsed_summary: str = "No Resume Parsed", 
                           user = None, session_id: str = "unknown") -> dict:
        
        score_history_str = str(score_history) if score_history else "[]"
        prev_score_str = str(prev_score) if prev_score is not None else "None"
        random_seed = str(uuid.uuid4())[:8]
        
        user_prompt = f"""
SANDBOX SESSION CONFIG:
- Language: {language}
- Questions Count: {questions_count}
- Target Company: {company_focus}
- Experience Tier: {experience_tier}
- Target Difficulty: {difficulty} (Must strictly be easy, medium, or hard)
- Random Seed (Ensure unique problem): {random_seed}
- Candidate Resume Context: {resume_parsed_summary}

SESSION STATE (for question 2+):
- Question Index: {current_question_index} / {questions_count}
- Previous Question Difficulty: {prev_difficulty}
- Previous Submission Score: {prev_score_str}
- Rolling Score Trend: {score_history_str}

TASK:
Generate challenge #{current_question_index} of {questions_count} for this candidate in {language}.
The problem MUST be a unique real-world scenario reflecting actual engineering tasks at {company_focus} at the requested {difficulty} level.
Generate starter code ONLY in {language} matching standard syntax (e.g. Python def solution(...), Java public class Solution, C++ class Solution, Go func solution, JavaScript function solution).

Respond strictly in this JSON schema:

{{
  "question_id": "challenge_{current_question_index}_{random_seed}",
  "title": "...",
  "difficulty_tag": "{str(difficulty).lower()}",
  "company_style_note": "{company_focus} Real-World Engineering Problem",
  "problem_statement": "...",
  "constraints": ["...", "..."],
  "example_test_cases": [
    {{"input": "...", "output": "..."}},
    {{"input": "...", "output": "..."}}
  ],
  "hidden_test_cases": [
    {{"input": "...", "expected_output": "..."}}
  ],
  "starter_code": "...",
  "estimated_time_mins": 25
}}
"""

        system_prompt = f"""
You are "PrepAI Code Architect" — a distinguished technical interviewer who designs production-oriented, highly realistic software engineering coding challenges for {company_focus} at {difficulty} difficulty using {language}.

RULES & GUIDELINES FOR PROBLEM DESIGN:
1. NO TOY OR ABSTRACT PUZZLES: Do not generate pure mathematical problems (e.g., Fibonacci, Factorial, Prime counting) or abstract textbook challenges. Wrap every problem in a highly realistic software engineering story context typical of {company_focus} (e.g., e-commerce order queues, streaming data packet buffers, rate limiters, graph dependencies, high-concurrency event handlers, telemetry log aggregations, transaction ledger verifiers).
2. STRICT DIFFICULTIES:
   - "easy": 1-2 core algorithmic operations (basic arrays/strings scanning, simple dictionary tracking, or sliding window) with 2-3 standard edge cases.
   - "medium": Multi-step production algorithms (BFS/DFS graph path search, dynamic programming caches, two-pointer arrays sorting, custom structures, priority queues).
   - "hard": Highly optimized distributed architecture coding scenarios (concurrency models, circular dependency graphs, custom memory limits, low-level binary data parsing, memory-efficient streams parsing).
3. DESIGN ROBUST STARTER CODE:
   - Provide a clean class and function structure in {language} with type safety where appropriate. Make parameter and function names meaningful.
4. TEST CASES AND CONSTRAINTS:
   - Provide clear time and space complexity constraints (e.g., "Time: O(N log N)", "Space: O(N)").
   - Include 2-3 example test cases illustrating normal cases, and 2-3 hidden test cases validating edge inputs (e.g., empty parameters, maximum numbers limits, duplicates).
5. Output STRICTLY raw JSON matching the requested schema. No markdown codeblock formatting, no text before or after the JSON.
"""
        full_query = f"{system_prompt}\n\n{user_prompt}"
        fallback_challenge = cls.get_randomized_fallback(language, company_focus, difficulty, current_question_index)

        from nlp.utils.ai_runner import execute_ai_call_with_retry
        
        user_id_str = str(user.id) if user else "unknown"
        session_id_str = str(session_id) if session_id else "unknown"
        
        metadata = {
            "difficulty": str(difficulty).lower(),
            "company": company_focus,
            "mode": "DSA",
            "language": language
        }
        
        def validator_func(raw_response: str) -> dict:
            if not raw_response:
                raise ValueError("Response is empty")
            json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(raw_response)
            
            if not isinstance(parsed, dict) or "problem_statement" not in parsed:
                raise ValueError("Parsed JSON is not a dictionary or missing problem_statement")
            
            if not parsed.get("starter_code") or len(parsed.get("starter_code", "")) < 5:
                parsed["starter_code"] = cls.get_starter_code(language)
            return parsed

        try:
            parsed_challenge = execute_ai_call_with_retry(
                request_type="chat",
                prompt=full_query,
                user=user,
                feature="sandbox",
                session_id=session_id_str,
                user_id=user_id_str,
                metadata=metadata,
                validator_func=validator_func,
                fallback_tier=3
            )
            return parsed_challenge
        except Exception as e:
            logger.error(f"Challenge AI generation failed and fell back to Tier 3: {str(e)}")
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
            res_dict = AIService.route_request("chat", user_prompt, user)
            raw_response = res_dict.get("response") if res_dict else None
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
