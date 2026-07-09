from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_question_text_length(value):
    """
    Enforces that question prompt text contains at least 10 characters.
    """
    if len(value.strip()) < 10:
        raise ValidationError(
            _('Question text must be at least 10 characters long.'),
            code='question_too_short'
        )

def validate_expected_duration(value):
    """
    Ensures expected answer duration in minutes is a positive value.
    """
    if value < 1 or value > 60:
        raise ValidationError(
            _('Expected duration must be between 1 and 60 minutes.'),
            code='invalid_expected_duration'
        )

def validate_attachment_file_size(file):
    """
    Enforces a strict 10 MB limit on question supporting attachments.
    """
    if file:
        max_size_bytes = 10 * 1024 * 1024  # 10 MB
        if file.size > max_size_bytes:
            raise ValidationError(
                _('Attachment size exceeds the maximum limit of 10 MB.'),
                code='attachment_too_large'
            )

def validate_import_file_format(file):
    """
    Verifies that imports are exclusively CSV or Excel sheets formats.
    """
    if file:
        filename = file.name.lower()
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                _('Unsupported file format. Please upload a valid CSV or Excel spreadsheet.'),
                code='invalid_import_file_type'
            )
