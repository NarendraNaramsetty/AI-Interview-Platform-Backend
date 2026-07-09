from django.core.exceptions import ValidationError
import datetime

def validate_percentage_range(value):
    """
    Enforces progress percentage range boundary limits (0.0 to 100.0).
    """
    if value < 0.0 or value > 100.0:
        raise ValidationError("Progress percentage must be between 0.0 and 100.0.")

def validate_reminder_time(value):
    """
    Validates reminder time format (ensure time is provided).
    """
    if not isinstance(value, (datetime.time, datetime.datetime)):
        raise ValidationError("A valid time value is required.")
