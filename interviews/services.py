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
                        duration_minutes: int, resume=None) -> InterviewSession:
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
        role = session.target_role
        company = session.target_company
        difficulty = session.difficulty

        # Set default generic tech/HR mock prompts
        mock_prompts = [
            f"Introduce yourself and highlight your experience as a {role}.",
            f"What do you know about the engineering culture at {company} and why do you want to join?",
            f"How do you handle debugging complex production issues? Explain your process.",
            f"Describe a situation where you had a technical disagreement with a team member. How did you resolve it?",
            f"What is your approach to learning new programming concepts or technical stacks?"
        ]

        questions_list = []
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
