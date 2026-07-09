from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_question_count(value):
    """
    Validates that total questions requested for a session is between 1 and 30.
    """
    if value < 1 or value > 30:
        raise ValidationError(
            _('Total questions must be a value between 1 and 30.'),
            code='invalid_question_count'
        )

def validate_duration_range(value):
    """
    Validates that duration requested is between 5 and 180 minutes.
    """
    if value < 5 or value > 180:
        raise ValidationError(
            _('Interview duration must be between 5 and 180 minutes.'),
            code='invalid_duration_range'
        )

def validate_audio_file_size(file):
    """
    Validates that a voice answer file does not exceed 10 MB.
    """
    if file:
        max_size_bytes = 10 * 1024 * 1024  # 10 MB
        if file.size > max_size_bytes:
            raise ValidationError(
                _('Audio response size exceeds maximum threshold of 10 MB.'),
                code='audio_too_large'
            )
            
        filename = file.name.lower()
        allowed_extensions = ['.mp3', '.wav', '.m4a', '.webm', '.ogg']
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                _('Unsupported audio format. Accepts MP3, WAV, M4A, WEBM, OGG only.'),
                code='unsupported_audio_extension'
            )
