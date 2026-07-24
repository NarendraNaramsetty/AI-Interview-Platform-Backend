from django.shortcuts import get_object_or_404
from .models import CodingSandboxSession, CodingChallengeResult, InterviewSession, InterviewQuestionResult
from .utils.code_challenge_generator import CodeChallengeGenerator
from .utils.question_generator import InterviewQuestionGenerator

class CodingSandboxService:

    @classmethod
    def create_session(cls, user, language: str, questions_count: int, 
                       company_focus: str, experience_tier: str, difficulty: str) -> CodingSandboxSession:
        
        return CodingSandboxSession.objects.create(
            user=user,
            language=language,
            questions_count=questions_count,
            company_focus=company_focus,
            experience_tier=experience_tier,
            difficulty=difficulty
        )

    @classmethod
    def generate_next_question(cls, session: CodingSandboxSession) -> CodingChallengeResult:
        results = session.results.all().order_by('created_at')
        current_idx = results.count() + 1
        
        prev_difficulty = "medium"
        prev_score = None
        score_history = []
        
        if results.exists():
            last_result = results.last()
            prev_difficulty = last_result.ai_feedback.get("difficulty_tag", "medium") if last_result.ai_feedback else "medium"
            prev_score = last_result.ai_score
            score_history = [r.ai_score for r in results if r.ai_score is not None]

        # Fetch resume parsed summary from the resume app
        resume_summary = "No Resume Parsed"
        try:
            from resume.models import Resume
            latest_resume = Resume.objects.filter(user=session.user).order_by('-created_at').first()
            if latest_resume:
                parsed_text = getattr(latest_resume, 'parsed_text', '') or getattr(latest_resume, 'extracted_skills', '')
                if parsed_text:
                    resume_summary = str(parsed_text)[:800]
        except Exception:
            pass

        challenge_data = CodeChallengeGenerator.generate_challenge(
            language=session.language,
            questions_count=session.questions_count,
            company_focus=session.company_focus,
            experience_tier=session.experience_tier,
            difficulty=session.difficulty,
            current_question_index=current_idx,
            prev_difficulty=prev_difficulty,
            prev_score=prev_score,
            score_history=score_history,
            resume_parsed_summary=resume_summary,
            user=session.user,
            session_id=str(session.id)
        )

        return CodingChallengeResult.objects.create(
            session=session,
            question_text=challenge_data.get("problem_statement", "Write a coding solution."),
            starter_code=challenge_data.get("starter_code", ""),
            test_cases=challenge_data.get("example_test_cases", []),
            ai_feedback={
                "title": challenge_data.get("title", "Coding Challenge"),
                "difficulty_tag": challenge_data.get("difficulty_tag", "medium"),
                "company_style_note": challenge_data.get("company_style_note", ""),
                "constraints": challenge_data.get("constraints", []),
                "hidden_test_cases": challenge_data.get("hidden_test_cases", [])
            },
            status="generated"
        )

    @classmethod
    def evaluate_question_submission(cls, result: CodingChallengeResult, user_submitted_code: str) -> CodingChallengeResult:
        # Retrieve stored details
        feedback_meta = result.ai_feedback or {}
        problem_statement = result.question_text
        hidden_test_cases = feedback_meta.get("hidden_test_cases", [])

        eval_data = CodeChallengeGenerator.evaluate_submission(
            problem_statement=problem_statement,
            hidden_test_cases=hidden_test_cases,
            user_submitted_code=user_submitted_code,
            user=result.session.user
        )

        result.user_submitted_code = user_submitted_code
        result.ai_score = eval_data.get("score", 0)
        
        # Merge evaluation response keys into result meta
        result.ai_feedback = {
            **feedback_meta,
            "evaluation": eval_data
        }
        result.status = "evaluated"
        result.save()
        
        return result


class NLPService:
    
    @classmethod
    def generate_interview_question(cls, user, session_config: dict, session_state: dict) -> dict:
        system_prompt = InterviewQuestionGenerator.SYSTEM_PROMPT
        user_prompt = InterviewQuestionGenerator.build_user_prompt(session_config, session_state)

        # Call AI service router
        ai_response = cls._call_llm(system_prompt, user_prompt, user)

        session, _ = InterviewSession.objects.get_or_create(
            id=session_state.get("session_id"),
            defaults={
                "user": user,
                "target_role": session_config.get("target_role", ""),
                "experience_level": session_config.get("experience_level", ""),
                "difficulty": session_config.get("difficulty", ""),
                "interview_mode": session_config.get("interview_mode", ""),
                "selected_skills": session_config.get("selected_skills_list", []),
                "score_goal": session_config.get("score_goal", 85),
                "total_questions": session_config.get("total_questions", 5),
                "ready_score": 75
            }
        )
        
        question = InterviewQuestionResult.objects.create(
            session=session,
            question_number=ai_response.get("question_number", session_state.get("current_question_index", 1)),
            question_text=ai_response.get("question_text", "Explain your experience."),
            scenario_context=ai_response.get("scenario_context", ""),
            skill_focus=ai_response.get("skill_focus", []),
            difficulty_tag=ai_response.get("difficulty_tag", "medium"),
            expected_answer_points=ai_response.get("expected_answer_points", []),
        )
        
        ai_response["db_question_id"] = question.id
        ai_response["session_id"] = session.id
        return ai_response

    @classmethod
    def evaluate_interview_answer(cls, question_result: InterviewQuestionResult, user_answer: str) -> dict:
        from ai_core.services import AIService
        import json
        import re

        eval_prompt = f"""
Evaluate the candidate's answer to this mock interview question.

QUESTION: {question_result.question_text}
SCENARIO CONTEXT: {question_result.scenario_context}
EXPECTED POINTS: {json.dumps(question_result.expected_answer_points)}
CANDIDATE'S ANSWER:
{user_answer}

Respond strictly in this JSON schema:
{{
  "score": <int 0-100>,
  "strengths": ["..."],
  "improvements": ["..."],
  "correct_answer_summary": "..."
}}
"""
        fallback_evaluation = {
            "score": 80,
            "strengths": ["Good baseline syntax", "Addresses context requirements"],
            "improvements": ["Elaborate on production scalability constraints"],
            "correct_answer_summary": "The candidate has demonstrated normal system debugging principles."
        }

        try:
            res_dict = AIService.route_request("chat", eval_prompt, question_result.session.user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and "score" in parsed:
                    fallback_evaluation = parsed
        except Exception:
            pass

        question_result.user_answer = user_answer
        question_result.ai_score = fallback_evaluation.get("score", 80)
        question_result.ai_feedback = fallback_evaluation
        question_result.status = "evaluated"
        question_result.save()

        return fallback_evaluation

    @staticmethod
    def _call_llm(system_prompt: str, user_prompt: str, user) -> dict:
        from ai_core.services import AIService
        import json
        import re
        
        full_query = f"{system_prompt}\n\n{user_prompt}"
        fallback = {
            "question_id": "fallback_q",
            "question_number": 1,
            "question_text": "Describe a challenging engineering issue you recently debugged and resolved.",
            "scenario_context": "Production incident analysis",
            "skill_focus": ["General"],
            "difficulty_tag": "medium",
            "expected_answer_points": ["Debugging approach", "Resolution validation"],
            "time_suggestion_mins": 10
        }
        
        try:
            res_dict = AIService.route_request("chat", full_query, user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and "question_text" in parsed:
                    return parsed
        except Exception:
            pass
        return fallback

    @classmethod
    def handle_coach_chat_message(cls, user, session_id, user_message: str, context: dict) -> dict:
        from .utils.coach_chat_generator import CoachChatGenerator
        from .models import CoachChatSession, CoachChatMessage

        session, _ = CoachChatSession.objects.get_or_create(id=session_id, defaults={"user": user})

        # Save user message
        CoachChatMessage.objects.create(session=session, role="user", message_text=user_message)

        # Retrieve chat history
        history = list(session.messages.order_by("created_at").values("role", "message_text"))[-10:]
        system_prompt = CoachChatGenerator.SYSTEM_PROMPT
        user_prompt = CoachChatGenerator.build_user_prompt(user_message, history, context)

        ai_response_dict = {
            "intent": "general_advice",
            "response_text": "I am here to guide you in your technical career prep! Ask me about system design, coding challenges, or behavioral questions.",
            "code_snippet": None,
            "suggested_followups": [
                "How do I answer a behavioral question using STAR framework?",
                "Can you help me design a rate limiter?"
            ],
            "related_app_action": {
                "label": "Practice in Coding Sandbox",
                "route": "/coding"
            }
        }

        try:
            from ai_core.services import AIService
            import json
            import re
            
            res_dict = AIService.route_request("chat", f"{system_prompt}\n\n{user_prompt}", user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and "response_text" in parsed:
                    ai_response_dict = parsed
        except Exception:
            pass

        # Save assistant message response
        CoachChatMessage.objects.create(
            session=session,
            role="assistant",
            message_text=ai_response_dict["response_text"],
            intent=ai_response_dict["intent"],
            code_snippet=ai_response_dict.get("code_snippet"),
            suggested_followups=ai_response_dict.get("suggested_followups", []),
            related_app_action=ai_response_dict.get("related_app_action", {}),
        )
        return ai_response_dict

    @classmethod
    def audit_resume(cls, user, uploaded_file, target_role=None) -> dict:
        from .utils.resume_parser import ResumeParser
        from .utils.ats_auditor_generator import ATSAuditorGenerator
        from .models import ResumeAuditResult
        import os
        from django.conf import settings
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile

        file_type = uploaded_file.name.split(".")[-1].lower()
        file_size_kb = uploaded_file.size // 1024

        # Save to temp path safely to allow local file parsing via docx/pdfplumber
        temp_path = default_storage.save(f"temp_resumes/{uploaded_file.name}", ContentFile(uploaded_file.read()))
        absolute_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        try:
            raw_text = ResumeParser.extract_text(absolute_temp_path, file_type)
        finally:
            # Cleanup temp file
            if default_storage.exists(temp_path):
                default_storage.delete(temp_path)

        system_prompt = ATSAuditorGenerator.SYSTEM_PROMPT
        user_prompt = ATSAuditorGenerator.build_user_prompt(raw_text, target_role, file_type, file_size_kb)

        fallback_audit = {
            "overall_ats_score": 70,
            "inferred_target_role": target_role or "Backend Developer",
            "category_scores": {
                "keyword_match": 65,
                "formatting_parseability": 85,
                "quantified_impact": 60,
                "structure_completeness": 80,
                "action_verb_strength": 70
            },
            "keyword_analysis": {
                "matched_keywords": ["Python", "REST APIs"],
                "missing_keywords": ["Docker", "Kubernetes", "AWS"],
                "keyword_density_percent": 2.0
            },
            "formatting_issues": ["Resume uses columns layout which might break some ATS parsing engines."],
            "recommendations": [
                {
                    "priority": "high",
                    "issue": "Missing modern container deployment keywords.",
                    "suggestion": "Include cloud orchestrator tools explicitly if applicable.",
                    "example_rewrite": "Deployed app → Deployed containerized backend app to AWS."
                }
            ],
            "detected_sections": ["Summary", "Experience", "Skills", "Education"],
            "missing_sections": ["Certifications"]
        }

        try:
            from ai_core.services import AIService
            import json
            import re
            
            res_dict = AIService.route_request("chat", f"{system_prompt}\n\n{user_prompt}", user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and "overall_ats_score" in parsed:
                    fallback_audit = parsed
        except Exception:
            pass

        # Save result
        result = ResumeAuditResult.objects.create(
            user=user,
            original_filename=uploaded_file.name,
            file_type=file_type,
            extracted_text=raw_text,
            target_role=target_role,
            overall_ats_score=fallback_audit["overall_ats_score"],
            category_scores=fallback_audit["category_scores"],
            keyword_analysis=fallback_audit["keyword_analysis"],
            formatting_issues=fallback_audit["formatting_issues"],
            recommendations=fallback_audit["recommendations"],
            detected_sections=fallback_audit["detected_sections"],
            missing_sections=fallback_audit.get("missing_sections", []),
        )

        fallback_audit["id"] = result.id
        return fallback_audit


