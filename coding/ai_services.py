import json
import logging
import re
import requests
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)

class AISandboxService:
    @staticmethod
    def get_api_key():
        # Load keys from environment
        return config('Gemini_API_KEY', default='') or config('OPENAI_API_KEY', default='')

    @staticmethod
    def call_gemini(prompt: str) -> str:
        api_key = AISandboxService.get_api_key()
        if not api_key:
            raise ValueError("No valid AI API Key configured in backend .env file.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                logger.error(f"Gemini API returned error: {response.text}")
                raise ValueError("Failed to query Gemini API.")
        except Exception as e:
            logger.error(f"Error connecting to Gemini API: {str(e)}")
            raise ValueError(f"AI Service Unavailable: {str(e)}")

    @staticmethod
    def parse_json_response(raw_text: str) -> dict:
        """
        Safely strips markdown block code wrapping and parses raw JSON response text.
        """
        cleaned = raw_text.strip()
        
        # Regex to strip ```json ... ``` blocks if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()
            
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {str(e)} - Raw: {raw_text}")
            raise ValueError("AI response failed JSON structure parsing.")

    @classmethod
    def generate_coding_challenge(cls, params: dict) -> dict:
        """
        Builds dynamic instructions and queries Gemini to create a unique coding challenge.
        """
        role = params.get('role', 'Backend Engineer')
        experience = params.get('experience', 'Junior')
        language = params.get('programming_language', 'python')
        difficulty = params.get('difficulty', 'Medium')
        company = params.get('company', 'Startup')
        focus_areas = ", ".join(params.get('focus_areas', [])) or 'General Architecture'
        goal = params.get('interview_goal', 'Practice')
        resume_context = params.get('resume_context', '')

        # Construct prompt
        prompt = f"""
        Generate one unique coding interview challenge matching the following target candidate parameters.
        You must return a JSON object ONLY. Do not write any other conversational text.

        Candidate Target Settings:
        - Target Role: {role}
        - Experience Level: {experience}
        - Programming Language: {language}
        - Target Company Style: {company} (Tailor question context: Google=Heavy algorithms/trees/graphs; Amazon=Practical REST APIs/Scalability; Startup=Fast CRUD APIs/database/caching)
        - Session Difficulty: {difficulty}
        - Focus Areas: {focus_areas}
        - Interview Goal: {goal}
        {f"- Resume Skills & Projects Context: {resume_context}" if resume_context else ""}

        Output JSON format spec:
        {{
            "title": "A short, descriptive, professional title (Do not use standard LeetCode question names like Two Sum. Create a new real-world scenario name.)",
            "description": "Exhaustive markdown description of the problem background, input guidelines, constraints, and business logic.",
            "starter_code": "Starter function declaration matching the parameters for the chosen language ({language}). Provide comments.",
            "test_cases": [
                {{ "input": "sample_input_value_1", "expected_output": "expected_result_1" }},
                {{ "input": "sample_input_value_2", "expected_output": "expected_result_2" }}
            ],
            "hints": [
                "Tiny hint explaining context",
                "Conceptual guide / reference design pattern",
                "Full conceptual solution approach"
            ],
            "optimal_solution": "Perfect optimal code solution in {language}."
        }}
        """

        raw_resp = cls.call_gemini(prompt)
        return cls.parse_json_response(raw_resp)

    @classmethod
    def review_user_code(cls, attempt_data: dict) -> dict:
        """
        Submits candidate code for AI review.
        """
        title = attempt_data.get('title')
        problem_desc = attempt_data.get('description')
        code = attempt_data.get('source_code')
        lang = attempt_data.get('programming_language')
        run_status = attempt_data.get('status')
        test_passed = attempt_data.get('passed_test_cases', 0)
        test_total = attempt_data.get('total_test_cases', 0)

        prompt = f"""
        You are a Staff Software Engineer conducting an API Code Review.
        Evaluate the candidate's solution for the challenge: "{title}".
        You must return a JSON object ONLY. Do not write any other conversational text.

        Problem Description:
        {problem_desc}

        Candidate Code ({lang}):
        ```
        {code}
        ```

        Virtual Compiler Execution Results:
        - Compilation Status: {run_status}
        - Passed Test Cases: {test_passed} / {test_total}

        Output JSON format spec:
        {{
            "score": 85, // Integer score out of 100 based on efficiency, readability, and correct test cases
            "correctness": "Feedback on logic correctness",
            "performance": "Feedback on time and space complexity",
            "code_quality": "Feedback on naming, structures, and best practices",
            "edge_cases": "Evaluation of boundary values, errors handling, and exceptions",
            "alternative_solution": "Markdown block containing an alternative clean implementation approach",
            "suggestions": [
                "Improvement tip 1",
                "Improvement tip 2"
            ],
            "follow_up_questions": [
                "How would you scale this to handle 10k requests per second?",
                "How does memory complexity behave if list length increases?",
                "How would you integrate a caching database layer here?"
            ]
        }}
        """

        raw_resp = cls.call_gemini(prompt)
        return cls.parse_json_response(raw_resp)
