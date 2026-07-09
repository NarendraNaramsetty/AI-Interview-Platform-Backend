from django.core.exceptions import ValidationError
from .constants import PROGRAMMING_LANGUAGE_CHOICES

def validate_programming_language(value):
    """
    Validates that the selected language is one of our supported programming languages.
    """
    valid_langs = [choice[0] for choice in PROGRAMMING_LANGUAGE_CHOICES]
    if value not in valid_langs:
        raise ValidationError(f"Programming language '{value}' is not supported. Supported: {valid_langs}")

def validate_source_code_length(value):
    """
    Enforces minimum source code input size constraints.
    """
    if not value or len(str(value).strip()) < 10:
        raise ValidationError("Source code must be at least 10 characters long.")

def validate_submission_ownership(user, submission):
    """
    Ensures that standard users cannot view/edit drafts of other candidates.
    """
    if not user.is_staff and submission.user != user:
        raise ValidationError("You do not have permission to access this submission.")
