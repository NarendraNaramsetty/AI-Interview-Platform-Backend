from django.core.exceptions import ValidationError

def validate_rating(value):
    """
    Ensures the chat rating score is an integer between 1 and 5.
    """
    if not isinstance(value, int) or value < 1 or value > 5:
        raise ValidationError("Rating must be an integer between 1 and 5.")

def validate_message_length(value):
    """
    Ensures message strings are not empty or only whitespace.
    """
    if not value or len(str(value).strip()) == 0:
        raise ValidationError("Message content cannot be blank.")
