import os
import io
import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    InterviewQuestion,
    QuestionCategory,
    Company,
    JobRole,
    Topic,
    QuestionHistory
)

class QuestionBankService:
    """
    Service Layer containing core business logic for importing/exporting questions,
    handling duplications, and future vector embedding generators.
    """

    @classmethod
    @transaction.atomic
    def duplicate_question(cls, question: InterviewQuestion, user) -> InterviewQuestion:
        """
        Creates a copy of a template question and records audit logs.
        """
        duplicate = InterviewQuestion.objects.create(
            question=f"Copy of: {question.question}",
            short_description=question.short_description,
            category=question.category,
            topic=question.topic,
            company=question.company,
            role=question.role,
            difficulty=question.difficulty,
            expected_duration=question.expected_duration,
            answer_type=question.answer_type,
            tags=question.tags.copy() if isinstance(question.tags, list) else [],
            hints=question.hints.copy() if isinstance(question.hints, list) else [],
            reference_links=question.reference_links.copy() if isinstance(question.reference_links, list) else [],
            expected_answer=question.expected_answer,
            explanation=question.explanation,
            source='Manual',
            created_by=user
        )

        # Set custom history overrides before post_save signal
        duplicate._history_action = 'Duplicated'
        duplicate._history_description = f"Duplicated copy from parent question ID {question.id}."
        duplicate.save(update_fields=['question'])

        return duplicate

    @classmethod
    def import_questions_from_file(cls, file, user) -> dict:
        """
        Parses CSV or Excel sheets using pandas, resolves category/company names,
        creates questions inside a database transaction, and lists errors.
        """
        filename = file.name.lower()
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            raise ValidationError(
                _("Unable to parse spreadsheet file: %(err)s") % {'err': str(e)},
                code='invalid_spreadsheet_structure'
            )

        # Trim columns headers
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Verify required columns
        required_cols = ['question', 'category', 'difficulty', 'expected_duration']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValidationError(
                _("Spreadsheet is missing required columns: %(cols)s") % {'cols': ", ".join(missing_cols)},
                code='missing_import_columns'
            )

        success_count = 0
        errors = []

        with transaction.atomic():
            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel 1-based indexing + header row
                
                try:
                    question_text = str(row.get('question', '')).strip()
                    category_name = str(row.get('category', '')).strip()
                    difficulty = str(row.get('difficulty', 'Medium')).strip().capitalize()
                    
                    try:
                        expected_duration = int(row.get('expected_duration', 5))
                    except (ValueError, TypeError):
                        expected_duration = 5

                    if not question_text or len(question_text) < 10:
                        errors.append(f"Row {row_num}: Question text must be at least 10 characters.")
                        continue
                        
                    if not category_name:
                        errors.append(f"Row {row_num}: Category name is required.")
                        continue

                    # Lookups Category
                    category, _ = QuestionCategory.objects.get_or_create(
                        name=category_name,
                        defaults={'description': f"Auto-created from import file '{file.name}'."}
                    )

                    # Lookups optional relations (Topic, Company, JobRole)
                    topic = None
                    topic_name = str(row.get('topic', '')).strip() if 'topic' in df.columns else ''
                    if topic_name:
                        topic, _ = Topic.objects.get_or_create(
                            category=category,
                            name=topic_name
                        )

                    company = None
                    company_name = str(row.get('company', '')).strip() if 'company' in df.columns else ''
                    if company_name:
                        company, _ = Company.objects.get_or_create(
                            name=company_name
                        )

                    role = None
                    role_name = str(row.get('role', '')).strip() if 'role' in df.columns else ''
                    if role_name:
                        exp_level = str(row.get('experience_level', 'Any')).strip() if 'experience_level' in df.columns else 'Any'
                        role, _ = JobRole.objects.get_or_create(
                            title=role_name,
                            experience_level=exp_level,
                            defaults={'category': category}
                        )

                    # Save question
                    q = InterviewQuestion.objects.create(
                        question=question_text,
                        short_description=str(row.get('short_description', ''))[:255] if 'short_description' in df.columns else '',
                        category=category,
                        topic=topic,
                        company=company,
                        role=role,
                        difficulty=difficulty if difficulty in ['Easy', 'Medium', 'Hard'] else 'Medium',
                        expected_duration=expected_duration,
                        answer_type=str(row.get('answer_type', 'Text')).strip() if 'answer_type' in df.columns else 'Text',
                        expected_answer=str(row.get('expected_answer', '')) if 'expected_answer' in df.columns else '',
                        explanation=str(row.get('explanation', '')) if 'explanation' in df.columns else '',
                        source='CSV' if filename.endswith('.csv') else 'Excel',
                        created_by=user
                    )

                    success_count += 1
                except Exception as ex:
                    errors.append(f"Row {row_num}: Unexpected error: {str(ex)}")

        return {
            "success_count": success_count,
            "failed_count": len(errors),
            "errors": errors
        }

    @classmethod
    def export_questions_to_bytes(cls, queryset, export_format: str = 'csv') -> tuple:
        """
        Serializes a question bank queryset to Pandas dataframe, and returns bytes and content types.
        """
        data = []
        for q in queryset:
            data.append({
                'id': q.id,
                'uuid': str(q.uuid),
                'question': q.question,
                'short_description': q.short_description,
                'category': q.category.name,
                'topic': q.topic.name if q.topic else '',
                'company': q.company.name if q.company else '',
                'role': q.role.title if q.role else '',
                'experience_level': q.role.experience_level if q.role else '',
                'difficulty': q.difficulty,
                'expected_duration': q.expected_duration,
                'answer_type': q.answer_type,
                'expected_answer': q.expected_answer,
                'explanation': q.explanation,
                'source': q.source,
                'is_active': q.is_active,
                'created_at': q.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        df = pd.DataFrame(data)

        if export_format.lower() == 'csv':
            # Export to CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue().encode('utf-8'), 'text/csv'
        else:
            # Export to Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Question Bank')
            excel_buffer.seek(0)
            return excel_buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    # ----------------------------------------------------
    # Future AI Integration Placeholders
    # ----------------------------------------------------

    @staticmethod
    def generate_embeddings(question_text: str) -> list:
        """
        Placeholder service generating sentence-transformer vectors.
        """
        return [0.0] * 384

    @classmethod
    def semantic_search(cls, query: str, limit: int = 10):
        """
        Placeholder RAG search returning matching InterviewQuestion IDs.
        """
        return InterviewQuestion.objects.filter(is_active=True)[:limit]

    @classmethod
    def find_similar_questions(cls, question_id: int):
        """
        Placeholder similar search based on category and tags overlap.
        """
        q = InterviewQuestion.objects.get(id=question_id)
        return InterviewQuestion.objects.filter(category=q.category).exclude(id=q.id)[:5]

    @staticmethod
    def generate_followup_questions(question_id: int) -> list:
        """
        Placeholder generating followup prompts.
        """
        return [
            "Can you elaborate on your response with a real-world coding scenario?",
            "What would be the time complexity trade-offs of your proposed solution?"
        ]

    @staticmethod
    def store_in_qdrant(question_id: int, embeddings: list) -> bool:
        """
        Placeholder Qdrant insertion.
        """
        return True

    @classmethod
    def retrieve_similar(cls, embeddings: list) -> list:
        """
        Placeholder retrieve matches using mock vectors.
        """
        return []
class CategoryManager:
    pass
