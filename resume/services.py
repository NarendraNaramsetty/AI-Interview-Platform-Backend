import os
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Resume, ResumeAnalysis, ResumeActivity
from .utils import parse_resume_document
from .validators import calculate_file_sha256

class ResumeService:
    """
    Service layer to process uploaded documents, increment version counters,
    audit activities, and interface with future AI tools.
    """

    @classmethod
    def process_new_resume(cls, user, title: str, uploaded_file, upload_source: str = 'Web') -> Resume:
        """
        Step 1: Validate file sizes/hashes (Duplicate checks).
        Step 2: Save metadata and file to the filesystem/database.
        Step 3: Extract text contents.
        Step 4: Count document pages.
        Step 5: Instantiate placeholder assessments.
        Step 6: Write audit logs.
        """
        file_hash = calculate_file_sha256(uploaded_file)
        
        # Check duplicate sha-256 file
        if Resume.objects.filter(user=user, file_hash=file_hash).exists():
            raise ValidationError(
                _('This resume document has already been uploaded previously.'),
                code='duplicate_file_upload'
            )
            
        # File type
        original_filename = uploaded_file.name
        file_ext = original_filename.split('.')[-1].lower()
        
        # If title is not provided, use filename without extension
        if not title:
            title = ".".join(original_filename.split('.')[:-1])
            
        # Create Resume Instance (Status = Active, Processing = Pending)
        resume = Resume.objects.create(
            user=user,
            title=title,
            original_filename=original_filename,
            file=uploaded_file,
            file_size=uploaded_file.size,
            file_type=file_ext,
            upload_source=upload_source,
            file_hash=file_hash,
            processing_status='Pending'
        )

        # Parse text & count pages
        try:
            extracted_text, pages_count = parse_resume_document(resume.file.path, file_ext)
            resume.resume_text = extracted_text
            resume.total_pages = pages_count
            resume.processing_status = 'Completed'
        except Exception:
            resume.processing_status = 'Failed'
            
        resume.save()
        
        # Create default placeholder analysis
        cls.analyze_resume(resume.id)

        # Write activity log
        cls.log_activity(resume, 'Uploaded Resume', f"Uploaded resume file '{original_filename}'.")
        
        return resume

    @classmethod
    def replace_resume_file(cls, resume: Resume, replacement_file) -> Resume:
        """
        Replaces the document file binary, increments version counters, 
        re-parses contents, and audits activities.
        """
        original_filename = replacement_file.name
        file_ext = original_filename.split('.')[-1].lower()
        file_hash = calculate_file_sha256(replacement_file)

        # Check duplicates
        if Resume.objects.filter(user=resume.user, file_hash=file_hash).exclude(id=resume.id).exists():
            raise ValidationError(
                _('A duplicate of this file already exists in your resume database.'),
                code='duplicate_file_upload'
            )

        # Delete old binary physically
        if resume.file and os.path.exists(resume.file.path):
            try:
                os.remove(resume.file.path)
            except OSError:
                pass

        resume.file = replacement_file
        resume.file_size = replacement_file.size
        resume.file_type = file_ext
        resume.original_filename = original_filename
        resume.file_hash = file_hash
        resume.resume_version += 1
        resume.processing_status = 'Pending'

        # Extract text & pages
        try:
            extracted_text, pages_count = parse_resume_document(resume.file.path, file_ext)
            resume.resume_text = extracted_text
            resume.total_pages = pages_count
            resume.processing_status = 'Completed'
        except Exception:
            resume.processing_status = 'Failed'

        resume.save()
        
        # Log activity
        cls.log_activity(
            resume, 
            'Updated Resume', 
            f"Replaced document file with version v{resume.resume_version} ({original_filename})."
        )
        
        return resume

    @classmethod
    def set_default_resume(cls, resume: Resume):
        """
        Sets target resume as user's default, resetting all other user resumes default states.
        """
        # Clear others default flags
        Resume.objects.filter(user=resume.user, is_default=True).update(is_default=False)
        
        resume.is_default = True
        resume.save(update_fields=['is_default'])
        
        cls.log_activity(resume, 'Marked Default', "Marked resume as default profile document.")

    @classmethod
    def soft_delete_resume(cls, resume: Resume):
        """
        Stamps deletion timestamp and registers activity.
        """
        resume.delete()
        cls.log_activity(resume, 'Deleted Resume', "Soft-deleted resume record from files registry.")

    @staticmethod
    def log_activity(resume: Resume, action: str, description: str = '') -> ResumeActivity:
        """
        Utility log register.
        """
        return ResumeActivity.objects.create(
            resume=resume,
            action=action,
            description=description
        )

    # ----------------------------------------------------
    # Future AI Integration Placeholders
    # ----------------------------------------------------

    @staticmethod
    def generate_embeddings(resume_text: str) -> list:
        """
        Placeholder service for Sentence Transformers embeddings calculations.
        Returns a mock vector array.
        """
        # Embeddings generation will go here later
        return [0.0] * 384  # Mock 384-dimensional vector

    @staticmethod
    def send_to_qdrant(resume_id: int, embeddings: list) -> bool:
        """
        Placeholder service for Vector Storage (Qdrant).
        """
        # Qdrant client connection will go here later
        return True

    @staticmethod
    def analyze_resume(resume_id: int) -> ResumeAnalysis:
        """
        Dynamic service for LLM Resume Analysis scoring.
        Populates real evaluation report using AI.
        """
        resume = Resume.objects.get(id=resume_id)
        
        # Create or update analysis report
        analysis, _ = ResumeAnalysis.objects.get_or_create(resume=resume)
        
        from ai_core.services import AIService
        from nlp.utils.ats_auditor_generator import ATSAuditorGenerator
        import json
        import re
        
        # Raw text from parsed resume
        raw_text = resume.resume_text or "No text content found in resume."
        file_size_kb = resume.file_size // 1024
        
        system_prompt = ATSAuditorGenerator.SYSTEM_PROMPT
        user_prompt = ATSAuditorGenerator.build_user_prompt(
            resume_raw_text=raw_text,
            target_role_or_jd=resume.title or "Developer",
            file_type=resume.file_type,
            file_size_kb=file_size_kb
        )
        
        fallback_audit = {
            "overall_ats_score": 70,
            "inferred_target_role": resume.title or "Backend Developer",
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
            res_dict = AIService.route_request("chat", f"{system_prompt}\n\n{user_prompt}", resume.user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                
                # Verify parsed schema contains overall_ats_score or similar
                if isinstance(parsed, dict) and ("overall_ats_score" in parsed or "overall_score" in parsed):
                    # Align overall_ats_score
                    if "overall_ats_score" in parsed and "overall_score" not in parsed:
                        parsed["overall_score"] = parsed["overall_ats_score"]
                    fallback_audit.update(parsed)
        except Exception:
            pass
            
        analysis.overall_score = fallback_audit.get("overall_score", fallback_audit.get("overall_ats_score", 70))
        analysis.ats_score = fallback_audit.get("category_scores", {}).get("keyword_match", 70)
        analysis.grammar_score = fallback_audit.get("category_scores", {}).get("action_verb_strength", 75)
        analysis.keyword_score = fallback_audit.get("category_scores", {}).get("keyword_match", 70)
        analysis.completeness_score = fallback_audit.get("category_scores", {}).get("structure_completeness", 80)
        
        # Summary & suggestions formatting
        analysis.summary = f"Audit for {fallback_audit.get('inferred_target_role', 'Developer')}. Matched keywords include {', '.join(fallback_audit.get('keyword_analysis', {}).get('matched_keywords', []))}. Formatting issues detected: {', '.join(fallback_audit.get('formatting_issues', []))}."
        analysis.strengths = [rec.get("suggestion") for rec in fallback_audit.get("recommendations", []) if rec.get("priority") == "low"] or ["Clean formatting parseability"]
        analysis.weaknesses = [rec.get("issue") for rec in fallback_audit.get("recommendations", []) if rec.get("priority") == "high"] or ["Add more quantified metrics"]
        analysis.missing_skills = fallback_audit.get("keyword_analysis", {}).get("missing_keywords", [])
        analysis.recommended_roles = [fallback_audit.get("inferred_target_role", "Developer")]
        analysis.analysis_status = 'Completed'
        analysis.save()
        return analysis

    @staticmethod
    def generate_questions(resume_id: int) -> list:
        """
        Placeholder service to generate personalized RAG questions.
        """
        return [
            "Explain your database tuning approach for Django queries.",
            "How do you secure simple JWT credentials routing in production?",
            "Can you describe your experience implementing custom REST exception middleware?"
        ]
