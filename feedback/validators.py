from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from .constants import PRIORITY_CHOICES

def validate_score_range(value):
    """
    Validate that the score is an integer between 0 and 100.
    """
    if not isinstance(value, int) and not isinstance(value, float):
        raise ValidationError("Score must be a numerical value.")
    if value < 0 or value > 100:
        raise ValidationError("Score must be between 0 and 100 inclusive.")

def validate_feedback_length(value):
    """
    Ensures feedback text fields are not empty or purely whitespace.
    """
    if not value or len(str(value).strip()) < 10:
        raise ValidationError("Feedback content must be at least 10 characters long.")

def validate_suggestion_priority(value):
    """
    Validates that priority is one of the choices: Low, Medium, High, Critical.
    """
    valid_priorities = [choice[0] for choice in PRIORITY_CHOICES]
    if value not in valid_priorities:
        raise ValidationError(f"Priority must be one of {valid_priorities}.")

def validate_resource_url(value):
    """
    Validates that a URL is well-formed.
    """
    url_validator = URLValidator()
    try:
        url_validator(value)
    except ValidationError:
        raise ValidationError("Please provide a valid resource URL.")
