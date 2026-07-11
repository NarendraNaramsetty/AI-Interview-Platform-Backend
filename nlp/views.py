from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import (
    CodingSandboxSession, CodingChallengeResult, 
    InterviewSession, InterviewQuestionResult,
    CoachChatSession, CoachChatMessage,
    ResumeAuditResult
)
from .serializers import (
    CodingSandboxSessionSerializer, CodingChallengeResultSerializer,
    ResumeAuditResultSerializer
)
from .services import CodingSandboxService, NLPService

# ... [keep all intermediate views exactly intact] ...
class CodingSandboxGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        language = request.data.get("language", "Python")
        questions_count = int(request.data.get("questions_count", 5))
        company_focus = request.data.get("company_focus", "General")
        experience_tier = request.data.get("experience_tier", "1-3 Years")
        difficulty = request.data.get("difficulty", "Medium")

        try:
            # 1. Create session
            session = CodingSandboxService.create_session(
                user=request.user,
                language=language,
                questions_count=questions_count,
                company_focus=company_focus,
                experience_tier=experience_tier,
                difficulty=difficulty
            )
            # 2. Generate the first challenge
            challenge = CodingSandboxService.generate_next_question(session)
            
            return Response({
                "success": True,
                "session_id": session.id,
                "challenge": CodingChallengeResultSerializer(challenge).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to start sandbox: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CodingSandboxNextQuestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(CodingSandboxSession, pk=session_id, user=request.user)
        try:
            challenge = CodingSandboxService.generate_next_question(session)
            return Response({
                "success": True,
                "challenge": CodingChallengeResultSerializer(challenge).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to generate challenge: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CodingChallengeSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        result = get_object_or_404(CodingChallengeResult, pk=id, session__user=request.user)
        user_code = request.data.get("user_submitted_code", "")

        try:
            evaluated = CodingSandboxService.evaluate_question_submission(result, user_code)
            return Response({
                "success": True,
                "challenge": CodingChallengeResultSerializer(evaluated).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to evaluate submission: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NLPAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({
            "success": True,
            "message": "NLP analysis query completed."
        }, status=status.HTTP_200_OK)


class InterviewSessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        selected_skills = request.data.get("selected_skills", ["Python"])
        session_config = {
            "target_role": request.data.get("target_role", "Backend Engineer"),
            "experience_level": request.data.get("experience_level", "Mid-Level"),
            "difficulty": request.data.get("difficulty", "Medium"),
            "interview_mode": request.data.get("interview_mode", "Text"),
            "selected_skills_list": selected_skills,
            "score_goal": int(request.data.get("score_goal", 85)),
            "total_questions": int(request.data.get("total_questions", 5)),
            "adaptive_mode_enabled": request.data.get("adaptive_mode_enabled", True)
        }
        
        session_state = {
            "session_id": None,
            "current_question_index": 1,
            "previous_questions_list": [],
            "last_answer_text": "",
            "last_score": None
        }

        try:
            ai_question = NLPService.generate_interview_question(request.user, session_config, session_state)
            return Response({
                "success": True,
                "session_id": ai_question["session_id"],
                "question": ai_question
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to start AI interview: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InterviewSessionAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(InterviewSession, pk=session_id, user=request.user)
        user_answer = request.data.get("user_answer", "")
        question_id = request.data.get("question_id")

        question_result = get_object_or_404(InterviewQuestionResult, pk=question_id, session=session)

        try:
            # 1. Evaluate answer
            eval_feedback = NLPService.evaluate_interview_answer(question_result, user_answer)
            
            # 2. Check if remaining questions exist
            next_q_num = question_result.question_number + 1
            has_next = next_q_num <= session.total_questions
            next_question_data = None

            if has_next:
                # Gather details for next prompt turn
                session_config = {
                    "target_role": session.target_role,
                    "experience_level": session.experience_level,
                    "difficulty": session.difficulty,
                    "interview_mode": session.interview_mode,
                    "selected_skills_list": session.selected_skills,
                    "score_goal": session.score_goal,
                    "total_questions": session.total_questions,
                    "adaptive_mode_enabled": True
                }
                
                previous_questions = list(session.questions.values_list('question_text', flat=True))
                session_state = {
                    "session_id": session.id,
                    "current_question_index": next_q_num,
                    "previous_questions_list": previous_questions,
                    "last_answer_text": user_answer,
                    "last_score": eval_feedback.get("score")
                }
                next_question_data = NLPService.generate_interview_question(request.user, session_config, session_state)

            return Response({
                "success": True,
                "feedback": eval_feedback,
                "has_next": has_next,
                "next_question": next_question_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to submit answer: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoachChatStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            session = CoachChatSession.objects.create(user=request.user)
            return Response({
                "success": True,
                "session_id": session.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to start coach session: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoachChatMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(CoachChatSession, pk=session_id, user=request.user)
        user_message = request.data.get("message_text", "")
        context = request.data.get("context", {})

        try:
            ai_reply = NLPService.handle_coach_chat_message(
                user=request.user,
                session_id=session.id,
                user_message=user_message,
                context=context
            )
            return Response({
                "success": True,
                "data": ai_reply
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to get coach reply: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CoachChatClearView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(CoachChatSession, pk=session_id, user=request.user)
        try:
            session.messages.all().delete()
            return Response({
                "success": True,
                "message": "Conversation history cleared successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Failed to clear history: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeUploadAndAuditView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({
                "success": False,
                "message": "No file uploaded. Please select a resume file."
            }, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        target_role = request.data.get('target_role')

        # 1. File type validation
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext not in ['pdf', 'docx']:
            return Response({
                "success": False,
                "message": "Unsupported file format. Please upload a PDF or DOCX file."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. File size validation (Max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return Response({
                "success": False,
                "message": "File exceeds the 5MB size limit."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            audit_result = NLPService.audit_resume(
                user=request.user,
                uploaded_file=uploaded_file,
                target_role=target_role
            )
            return Response({
                "success": True,
                "audit": audit_result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"ATS Audit Failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeAuditDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, audit_id):
        audit = get_object_or_404(ResumeAuditResult, pk=audit_id, user=request.user)
        serializer = ResumeAuditResultSerializer(audit)
        return Response({
            "success": True,
            "audit": serializer.data
        }, status=status.HTTP_200_OK)
