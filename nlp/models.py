from django.db import models
from django.conf import settings

class CodingSandboxSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    language = models.CharField(max_length=30)
    questions_count = models.IntegerField()
    company_focus = models.CharField(max_length=50)
    experience_tier = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sandbox: {self.language} for {self.user.email}"

class CodingChallengeResult(models.Model):
    session = models.ForeignKey(CodingSandboxSession, related_name="results", on_delete=models.CASCADE)
    question_text = models.TextField()
    starter_code = models.TextField(blank=True)
    test_cases = models.JSONField(default=list)
    user_submitted_code = models.TextField(blank=True, null=True)
    ai_score = models.IntegerField(null=True)
    ai_feedback = models.JSONField(default=dict, null=True)
    status = models.CharField(max_length=20, default="pending")  # pending|generated|submitted|evaluated
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Challenge Result of Session {self.session_id} - Score: {self.ai_score}"


class InterviewSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_role = models.CharField(max_length=100)
    experience_level = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=20)
    interview_mode = models.CharField(max_length=20)
    selected_skills = models.JSONField(default=list)
    score_goal = models.IntegerField(default=85)
    total_questions = models.IntegerField(default=5)
    ready_score = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NLP Session: {self.target_role} for {self.user.email}"


class InterviewQuestionResult(models.Model):
    session = models.ForeignKey(InterviewSession, related_name="questions", on_delete=models.CASCADE)
    question_number = models.IntegerField()
    question_text = models.TextField()
    scenario_context = models.TextField(blank=True)
    skill_focus = models.JSONField(default=list)
    difficulty_tag = models.CharField(max_length=20)
    expected_answer_points = models.JSONField(default=list)
    user_answer = models.TextField(blank=True, null=True)
    ai_score = models.IntegerField(null=True)
    ai_feedback = models.JSONField(default=dict, null=True)
    status = models.CharField(max_length=20, default="generated")  # generated|answered|evaluated
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NLP Q#{self.question_number} Result of Session {self.session_id} - Score: {self.ai_score}"


class CoachChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coach Chat: {self.user.email} started at {self.created_at}"


class CoachChatMessage(models.Model):
    session = models.ForeignKey(CoachChatSession, related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # "user" | "assistant"
    message_text = models.TextField()
    intent = models.CharField(max_length=30, blank=True, null=True)
    code_snippet = models.TextField(blank=True, null=True)
    suggested_followups = models.JSONField(default=list, null=True)
    related_app_action = models.JSONField(default=dict, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat Msg from {self.role} in Session {self.session_id}"


class ResumeAuditResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    extracted_text = models.TextField()
    target_role = models.CharField(max_length=100, blank=True, null=True)
    overall_ats_score = models.IntegerField()
    category_scores = models.JSONField(default=dict)
    keyword_analysis = models.JSONField(default=dict)
    formatting_issues = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    detected_sections = models.JSONField(default=list)
    missing_sections = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume Audit: {self.original_filename} - Score: {self.overall_ats_score}"
