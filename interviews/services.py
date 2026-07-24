from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewProgress,
    InterviewResult,
    InterviewTimeline
)
from .constants import (
    STATUS_IN_PROGRESS,
    STATUS_PAUSED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
    STATUS_SCHEDULED,
    SOURCE_DATABASE
)

class InterviewService:
    """
    Service Layer containing core state flow and auditing for mock interview sessions.
    """

    @classmethod
    def start_interview(cls, user, target_role: str, target_company: str, interview_type: str,
                        difficulty: str, interview_mode: str, language: str, total_questions: int,
                        duration_minutes: int, resume=None, tech_stack: list = None, adaptive_mode: bool = True) -> InterviewSession:
        """
        Creates a new interview session, loads mock questions, sets started dates,
        and starts progress tracking.
        """
        title = f"Mock {target_role} Interview at {target_company}"
        
        session = InterviewSession.objects.create(
            user=user,
            resume=resume,
            title=title,
            target_role=target_role,
            target_company=target_company,
            interview_type=interview_type,
            difficulty=difficulty,
            interview_mode=interview_mode,
            language=language,
            total_questions=total_questions,
            duration_minutes=duration_minutes,
            tech_stack=tech_stack if tech_stack else [],
            adaptive_mode=adaptive_mode,
            status=STATUS_IN_PROGRESS,
            started_at=timezone.now()
        )

        # Load and save questions
        questions = cls.generate_questions(session)
        
        # Set first question in progress tracking
        progress = session.progress
        if questions:
            progress.current_question = questions[0]
            progress.save()

        cls.log_event(session, 'Interview Started', f"Session started. Loaded {len(questions)} questions.")
        return session

    @classmethod
    def save_answer(cls, session: InterviewSession, question: InterviewQuestion,
                    answer_text: str, audio_file=None, answer_duration: int = 0) -> InterviewAnswer:
        """
        Saves a question response, increments answered counts, recalculates progress completeness,
        and logs timeline events.
        """
        answer_type = 'Voice' if audio_file else 'Text'
        
        # If voice format, transcribe mock text
        if audio_file and not answer_text:
            answer_text = cls.transcribe_audio(audio_file)

        # Create answer object
        answer = InterviewAnswer.objects.create(
            session=session,
            question=question,
            answer_text=answer_text,
            answer_type=answer_type,
            audio_file=audio_file,
            answer_duration=answer_duration
        )

        # Run mock score computation
        cls.evaluate_answer(answer.id)

        # Update stats
        answered_count = session.answers.count()
        session.answered_questions = answered_count
        
        # Move sequence index pointer to next sequence if possible
        if session.current_question_index < session.total_questions - 1:
            session.current_question_index += 1
        session.save(update_fields=['answered_questions', 'current_question_index'])

        # Recalculate progress percentages
        progress = session.progress
        progress.percentage_completed = min(float((answered_count / session.total_questions) * 100), 100.0)
        progress.remaining_questions = max(session.total_questions - answered_count, 0)
        
        # Fetch current question based on current sequence pointer index
        current_seq = session.current_question_index + 1
        curr_q = session.questions.filter(sequence_number=current_seq).first()
        if curr_q:
            progress.current_question = curr_q
            
        progress.save()

        cls.log_event(
            session, 
            'Question Answered', 
            f"Answer submitted for question seq #{question.sequence_number} ({answer_type})."
        )
        return answer

    @classmethod
    def pause_interview(cls, session: InterviewSession):
        if session.status != STATUS_IN_PROGRESS:
            raise ValidationError(_("Can only pause interviews that are currently In Progress."))
        
        session.status = STATUS_PAUSED
        session.save(update_fields=['status'])
        cls.log_event(session, 'Interview Paused', "Interview progress paused by user.")

    @classmethod
    def resume_interview(cls, session: InterviewSession):
        if session.status != STATUS_PAUSED:
            raise ValidationError(_("Can only resume interviews that are currently Paused."))
        
        session.status = STATUS_IN_PROGRESS
        session.save(update_fields=['status'])
        cls.log_event(session, 'Interview Resumed', "Interview progress resumed by user.")

    @classmethod
    def end_interview(cls, session: InterviewSession) -> InterviewResult:
        if session.status in [STATUS_COMPLETED, STATUS_CANCELLED]:
            raise ValidationError(_("Interview has already terminated."))
        
        session.status = STATUS_COMPLETED
        session.completed_at = timezone.now()
        session.save(update_fields=['status', 'completed_at'])

        # Update progress percentage to 100%
        progress = session.progress
        progress.percentage_completed = 100.0
        progress.remaining_questions = 0
        progress.save()

        # Update empty scorecard results with mock parameters
        cls.calculate_score(session.id)
        cls.generate_feedback(session.id)

        cls.log_event(session, 'Interview Completed', "Interview completed. AI score evaluation generated.")
        return session.result

    @classmethod
    def duplicate_session(cls, session: InterviewSession) -> InterviewSession:
        """
        Creates a scheduled replication copy of a template session.
        """
        duplicated = InterviewSession.objects.create(
            user=session.user,
            resume=session.resume,
            title=f"Replication: {session.title}",
            target_role=session.target_role,
            target_company=session.target_company,
            interview_type=session.interview_type,
            difficulty=session.difficulty,
            interview_mode=session.interview_mode,
            language=session.language,
            total_questions=session.total_questions,
            duration_minutes=session.duration_minutes,
            status=STATUS_SCHEDULED
        )

        # Copy original questions sequence structures
        for q in session.questions.all():
            InterviewQuestion.objects.create(
                session=duplicated,
                question_text=q.question_text,
                topic=q.topic,
                category=q.category,
                difficulty=q.difficulty,
                sequence_number=q.sequence_number,
                source=q.source,
                expected_answer_placeholder=q.expected_answer_placeholder
            )

        cls.log_event(duplicated, 'Interview Duplicated', f"Duplicated config settings from session ID {session.id}.")
        return duplicated

    @staticmethod
    def log_event(session: InterviewSession, action: str, description: str = ''):
        InterviewTimeline.objects.create(
            session=session,
            action=action,
            description=description
        )

    # ----------------------------------------------------
    # Future AI Integration Placeholders
    # ----------------------------------------------------

    @staticmethod
    def generate_questions(session: InterviewSession) -> list:
        """
        Generates role-specific mock InterviewQuestions, inserting them in the database.
        """
        import time
        overall_start = time.time()
        role = session.target_role
        company = session.target_company
        difficulty = session.difficulty

        # 1. Try to generate custom questions via AI in real-time first
        try:
            from nlp.utils.ai_runner import execute_ai_call_with_retry
            import json
            import re

            from nlp.utils.question_generator import InterviewQuestionGenerator
            
            resume_summary = "No Resume Connected"
            if session.resume:
                resume_text = getattr(session.resume, "parsed_text", "") or getattr(session.resume, "extracted_skills", "")
                resume_summary = str(resume_text)[:800]

            system_prompt, user_prompt = InterviewQuestionGenerator.build_prompts(
                role=role,
                company=company,
                difficulty=difficulty,
                mode=session.interview_mode,
                skills=session.tech_stack,
                question_count=session.total_questions,
                experience_level=getattr(session, "experience_level", "Mid-Level"),
                resume_summary=resume_summary
            )
            user_id_str = str(session.user.id) if session.user else "unknown"
            session_id_str = str(session.id) if session else "unknown"
            
            metadata = {
                "difficulty": str(difficulty).lower(),
                "company": company,
                "mode": session.interview_mode,
                "role": role
            }

            def validator_func(raw_response: str) -> list:
                if not raw_response:
                    raise ValueError("Response is empty")
                json_match = re.search(r'(\[.*\]|\{.*\})', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                
                if not isinstance(parsed, list) or len(parsed) == 0:
                    raise ValueError("Parsed JSON is not a non-empty list of questions")
                return parsed

            parsed_questions = execute_ai_call_with_retry(
                request_type="chat",
                prompt=f"{system_prompt}\n\n{user_prompt}",
                user=session.user,
                feature="interview",
                session_id=session_id_str,
                user_id=user_id_str,
                metadata=metadata,
                validator_func=validator_func,
                fallback_tier=2
            )

            questions_list = []
            for idx, q_data in enumerate(parsed_questions[:session.total_questions]):
                q = InterviewQuestion.objects.create(
                    session=session,
                    question_text=q_data.get("question_text", "Explain your experience."),
                    topic=q_data.get("topic", "General"),
                    category=q_data.get("category", "Technical"),
                    difficulty=difficulty,
                    sequence_number=idx + 1,
                    source='AI_Core',
                    expected_answer_placeholder=q_data.get("expected_answer_placeholder", "Demonstrate standard principles.")
                )
                questions_list.append(q)
            
            if len(questions_list) > 0:
                return questions_list
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Interview AI question generation failed and fell back to Tier 2: {str(e)}")

        # Try to load matching questions from the main InterviewQuestion bank
        try:
            from questions.models import InterviewQuestion as BankQuestion
            from django.db.models import Q
            
            # Start query set
            qs = BankQuestion.objects.filter(is_active=True)
            
            # Normalize difficulty string (Easy, Medium, Hard)
            target_diff = str(difficulty or 'Medium').capitalize()

            # 1. Apply difficulty filter
            diff_qs = qs.filter(difficulty__iexact=target_diff)
            if not diff_qs.exists():
                diff_qs = qs  # fallback if specified difficulty has no questions

            # 2. Check Interview Mode-specific Category Overrides
            mode_str = str(session.interview_mode or '').lower()
            
            if 'behavioral' in mode_str:
                mode_qs = diff_qs.filter(category__name__icontains='Behavioral')
                if not mode_qs.exists():
                    mode_qs = qs.filter(category__name__icontains='Behavioral')
                bank_qs = list(mode_qs.order_by('?')[:session.total_questions])
            elif 'hr' in mode_str:
                mode_qs = diff_qs.filter(category__name__icontains='HR')
                if not mode_qs.exists():
                    mode_qs = qs.filter(category__name__icontains='HR')
                bank_qs = list(mode_qs.order_by('?')[:session.total_questions])
            elif 'rapid' in mode_str:
                mode_qs = diff_qs.filter(Q(category__name__icontains='Behavioral') | Q(category__name__icontains='HR') | Q(category__name__icontains='Technical'))
                if not mode_qs.exists():
                    mode_qs = diff_qs
                bank_qs = list(mode_qs.order_by('?')[:session.total_questions])
            elif 'mixed' in mode_str:
                mode_qs = diff_qs
                bank_qs = list(mode_qs.order_by('?')[:session.total_questions])
            elif 'design' in mode_str:
                mode_qs = diff_qs.filter(category__name__icontains='System Design')
                if not mode_qs.exists():
                    mode_qs = qs.filter(category__name__icontains='System Design')
                bank_qs = list(mode_qs.order_by('?')[:session.total_questions])
            elif 'coding' in mode_str:
                mode_qs = diff_qs.filter(category__name__icontains='DSA')
                if not mode_qs.exists():
                    mode_qs = qs.filter(category__name__icontains='DSA')
                bank_qs = list(mode_qs.order_by('?')[:session.total_questions])
            elif session.tech_stack:
                skills = [str(s).strip() for s in session.tech_stack if str(s).strip()]
                num_skills = len(skills)
                total_req = session.total_questions
                
                # Proportionally allocate questions across selected skills/categories
                base_per_skill = max(1, total_req // num_skills) if num_skills > 0 else total_req
                remainder = total_req % num_skills if num_skills > 0 else 0
                
                collected_qs = []
                seen_q_ids = set()
                
                for idx, tech in enumerate(skills):
                    quota = base_per_skill + (1 if idx < remainder else 0)
                    if quota <= 0:
                        continue
                    
                    tech_q = (
                        Q(tags__icontains=tech) |
                        Q(topic__name__icontains=tech) |
                        Q(category__name__icontains=tech) |
                        Q(question__icontains=tech) |
                        Q(short_description__icontains=tech) |
                        Q(expected_answer__icontains=tech)
                    )
                    
                    # Priority A: Match tech skill AND target difficulty
                    skill_diff_qs = diff_qs.filter(tech_q).exclude(id__in=seen_q_ids)
                    chosen = list(skill_diff_qs.order_by('?')[:quota])
                    
                    # Priority B: Fallback to match tech skill across any difficulty if needed
                    if len(chosen) < quota:
                        needed = quota - len(chosen)
                        already_ids = seen_q_ids.union(set(q.id for q in chosen))
                        skill_any_diff = qs.filter(tech_q).exclude(id__in=already_ids)
                        chosen.extend(list(skill_any_diff.order_by('?')[:needed]))
                        
                    for q in chosen:
                        seen_q_ids.add(q.id)
                        collected_qs.append(q)
                
                # Fill remaining slots from difficulty-matched questions if needed
                if len(collected_qs) < total_req:
                    needed = total_req - len(collected_qs)
                    fillers = list(diff_qs.exclude(id__in=seen_q_ids).order_by('?')[:needed])
                    for q in fillers:
                        seen_q_ids.add(q.id)
                        collected_qs.append(q)

                final_qs = collected_qs
                bank_qs = final_qs[:total_req]
            else:
                # If no specific tech stack specified, filter by target role or category
                role_qs = diff_qs.filter(role__title__icontains=role)
                if not role_qs.exists() and "frontend" in role.lower():
                    role_qs = diff_qs.filter(category__name__icontains="frontend")
                elif not role_qs.exists() and "backend" in role.lower():
                    role_qs = diff_qs.filter(category__name__icontains="backend")
                    
                if not role_qs.exists():
                    role_qs = diff_qs
                final_qs = role_qs
                bank_qs = list(final_qs.order_by('?')[:session.total_questions])
        except Exception as err:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to query from Question Bank: {err}")
            bank_qs = []

        questions_list = []

        if bank_qs:
            for idx, bq in enumerate(bank_qs):
                q = InterviewQuestion.objects.create(
                    session=session,
                    question_text=bq.question,
                    topic=bq.topic.name if bq.topic else "General",
                    category=bq.category.name if bq.category else "Technical",
                    difficulty=bq.difficulty,
                    sequence_number=idx + 1,
                    source=SOURCE_DATABASE,
                    expected_answer_placeholder=bq.expected_answer or "Candidate should demonstrate standard technical layout."
                )
                questions_list.append(q)
            
            # If we need more questions than matched, generate fillers
            if len(questions_list) < session.total_questions:
                for idx in range(len(questions_list), session.total_questions):
                    q = InterviewQuestion.objects.create(
                        session=session,
                        question_text=f"Filler Question {idx + 1}: Explain web standards, architecture, and REST principles.",
                        topic="Web Engineering",
                        category="Technical",
                        difficulty=difficulty,
                        sequence_number=idx + 1,
                        source=SOURCE_DATABASE,
                        expected_answer_placeholder="Explain HTTP methods and routing."
                    )
                    questions_list.append(q)
        else:
            # Set default generic tech/HR mock prompts (Tier 3 fallback reached)
            tracker_logger = logging.getLogger("ai_generation_tracker")
            from nlp.utils.metrics import MetricsCollector
            user_id_str = str(session.user.id) if session.user else "unknown"
            session_id_str = str(session.id) if session else "unknown"
            latency_ms = int((time.time() - overall_start) * 1000)
            
            log_data = {
                "tier_reached": 3,
                "failure_reason": "no_db_match",
                "latency_ms": latency_ms,
                "role": role,
                "company": company,
                "difficulty": difficulty,
                "mode": session.interview_mode,
                "session_id": session_id_str,
                "user_id": user_id_str
            }
            tracker_logger.error(json.dumps(log_data))
            MetricsCollector.increment_counter("generation_tier_result_total", {"tier": "3", "failure_reason": "no_db_match", "feature": "interview"})
            MetricsCollector.record_histogram("generation_latency_ms", latency_ms, {"tier": "3", "feature": "interview"})

            mock_prompts = [
                f"Introduce yourself and highlight your experience as a {role}.",
                f"What do you know about the engineering culture at {company} and why do you want to join?",
                f"How do you handle debugging complex production issues? Explain your process.",
                f"Describe a situation where you had a technical disagreement with a team member. How did you resolve it?",
                f"What is your approach to learning new programming concepts or technical stacks?"
            ]

            for idx, text in enumerate(mock_prompts[:session.total_questions]):
                q = InterviewQuestion.objects.create(
                    session=session,
                    question_text=text,
                    topic="Introduction" if idx < 2 else "Technical Problem Solving",
                    category="Behavioral" if idx in [0, 3] else "Technical",
                    difficulty=difficulty,
                    sequence_number=idx + 1,
                    source=SOURCE_DATABASE,
                    expected_answer_placeholder="Candidate should demonstrate professional communication and structuring."
                )
                questions_list.append(q)
                
            # In case total_questions requested exceeds default list, generate fillers
            if session.total_questions > len(mock_prompts):
                for idx in range(len(mock_prompts), session.total_questions):
                    q = InterviewQuestion.objects.create(
                        session=session,
                        question_text=f"Filler Question {idx + 1}: Explain web standards and REST principles.",
                        topic="Web Engineering",
                        category="Technical",
                        difficulty=difficulty,
                        sequence_number=idx + 1,
                        source=SOURCE_DATABASE,
                        expected_answer_placeholder="Explain HTTP methods and routing."
                    )
                    questions_list.append(q)

        return questions_list

    @staticmethod
    def evaluate_answer(answer_id: int) -> str:
        """
        Mock LLM evaluator rating specific answers.
        """
        return "Answer shows clear layout structure. Keyword matching satisfies baseline thresholds."

    @staticmethod
    def transcribe_audio(audio_file) -> str:
        """
        Mock audio Whisper transcriber.
        """
        return "This is a mock audio transcript from speech-to-text conversion."

    @staticmethod
    def generate_feedback(session_id: int):
        """
        Updates the final result assessment summary.
        """
        session = InterviewSession.objects.get(id=session_id)
        result = session.result
        result.feedback_placeholder = (
            f"The session for {session.target_role} showed solid technical execution. "
            "Great communication skills on situational questions, with minor room for improvement "
            "on explaining concurrency topics."
        )
        result.save()

    @staticmethod
    def calculate_score(session_id: int):
        """
        Mock updates for score indicators.
        """
        session = InterviewSession.objects.get(id=session_id)
        result = session.result
        result.technical_score = 80
        result.communication_score = 85
        result.confidence_score = 78
        result.grammar_score = 90
        result.overall_score = 83
        result.status = 'Completed'
        result.save()

    @staticmethod
    def retrieve_from_qdrant(resume_id: int, query: str) -> list:
        return []

    @staticmethod
    def generate_followup(session_id: int, question_id: int) -> list:
        return []

    @classmethod
    def get_next_question_ai(cls, session: InterviewSession) -> dict:
        """
        Invokes Gemini/Claude router to adaptively fetch the next interview question and evaluate the last candidate response.
        """
        # Gather answers so far to extract scores and candidate answers
        answers = session.answers.order_by('submitted_at')
        questions_asked_count = answers.count()

        # Last candidate response
        last_answer = answers.last()
        last_answer_text = last_answer.answer_text if last_answer else ""

        # Rolling performance scores (last 3 scores)
        scored_answers = [ans.score for ans in answers if ans.score is not None]
        last_3_scores = scored_answers[-3:]

        # Time remaining
        time_elapsed_mins = int(session.elapsed_time_seconds / 60)
        time_remaining_mins = max(0, session.duration_minutes - time_elapsed_mins)

        # Technical skills stack
        selected_skills_list = session.tech_stack if session.tech_stack else [session.target_role]

        # Formatting user turn prompt
        user_prompt = f"""
INTERVIEW SESSION CONTEXT:
- Target Role: {session.target_role}
- Experience Level: {session.difficulty}
- Difficulty: {session.difficulty}
- Interview Mode: {session.interview_mode}
- Mock Duration Remaining: {time_remaining_mins} mins
- Score Goal: 80%
- Selected Tech Stack: {selected_skills_list}

SESSION STATE:
- Questions Asked So Far: {questions_asked_count}
- Candidate's Last Answer: "{last_answer_text}"
- Rolling Performance Trend: {last_3_scores}
- Adaptive Mode: {session.adaptive_mode}

TASK:
Based on the context above, generate the NEXT interview question (or, if this 
is the first turn, generate the OPENING question). If evaluating a previous 
answer, include feedback and a score.

Respond strictly in this JSON schema:

{{
  "action": "ask_question" | "give_feedback_and_ask_next" | "end_interview",
  "feedback": {{
    "score": <int 0-100 or null>,
    "strengths": ["..."],
    "improvements": ["..."],
    "correct_answer_summary": "<1-2 lines, only if candidate missed key points>"
  }},
  "next_question": {{
    "question_text": "...",
    "category": "<one of the selected tech stack items>",
    "difficulty_tag": "easy" | "medium" | "hard",
    "expected_answer_points": ["...", "..."]
  }},
  "session_meta": {{
    "current_ready_score": <int 0-100>,
    "questions_remaining_estimate": <int>
  }}
}}
"""

        system_prompt = """
You are "PrepAI Interviewer" — an expert technical interviewer and AI coach 
conducting a simulated job interview. You adapt question difficulty in real 
time based on the candidate's previous answers.

RULES:
1. Stay strictly within the candidate's selected technology stack and target role.
2. Never ask about technologies NOT in the provided skill list unless the 
   candidate mentions them first.
3. Match question difficulty to the selected experience level:
   - Fresher: fundamentals, definitions, simple "what is X" / "how does Y work"
   - Junior: applied usage, small scenarios, basic debugging
   - Mid-Level: system design lite, trade-offs, real-world scenarios, optimization
   - Senior: architecture decisions, scalability, failure modes, leadership calls
   - Lead: cross-team trade-offs, org-level architecture, mentoring/decision framing
4. If ADAPTIVE MODE is enabled, increase difficulty after 2 consecutive strong 
   answers, and decrease after 2 consecutive weak/incorrect answers.
5. Ask ONE question at a time. Never bundle multiple questions in a single turn.
6. After each candidate answer, silently score it (0-100) against correctness, 
   depth, and clarity — do not reveal the score mid-interview unless asked.
7. Keep tone professional, encouraging, and concise — like a real interviewer, 
   not a lecturer.
8. Respond ONLY in the JSON schema provided. No markdown, no preamble.
"""
        full_query = f"{system_prompt}\n\n{user_prompt}"

        fallback_next_question = f"Can you explain your experience building systems with {', '.join(selected_skills_list[:2])}?"
        ai_response_dict = {
            "action": "ask_question",
            "feedback": {
                "score": None,
                "strengths": [],
                "improvements": [],
                "correct_answer_summary": ""
            },
            "next_question": {
                "question_text": fallback_next_question,
                "category": selected_skills_list[0] if selected_skills_list else "General",
                "difficulty_tag": session.difficulty.lower(),
                "expected_answer_points": ["Detailing technical architecture", "Correct syntax usage"]
            },
            "session_meta": {
                "current_ready_score": 75,
                "questions_remaining_estimate": session.total_questions - questions_asked_count
            }
        }

        try:
            from ai_core.services import AIService
            import json
            import re
            
            res_dict = AIService.route_request("chat", full_query, session.user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                
                if isinstance(parsed, dict) and "next_question" in parsed:
                    ai_response_dict = parsed
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Interview dynamic question AI generation failed, utilizing fallback: {str(e)}")

        if last_answer and ai_response_dict.get("feedback"):
            feedback_data = ai_response_dict["feedback"]
            last_answer.score = feedback_data.get("score")
            last_answer.feedback = feedback_data
            last_answer.save()

        q_data = ai_response_dict.get("next_question", {})
        new_seq_num = questions_asked_count + 1
        
        question = InterviewQuestion.objects.create(
            session=session,
            question_text=q_data.get("question_text", fallback_next_question),
            topic=q_data.get("category", "General"),
            category="Technical",
            difficulty=session.difficulty,
            sequence_number=new_seq_num,
            source="AI",
            expected_answer_placeholder=", ".join(q_data.get("expected_answer_points", []))
        )

        progress = session.progress
        progress.current_question = question
        progress.save()

        return ai_response_dict
