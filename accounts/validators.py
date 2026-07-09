import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date

def validate_strong_password(value):
    """
    Validates that a password has at least 8 characters, one uppercase letter,
    one lowercase letter, one digit, and one special character.
    """
    if len(value) < 8:
        raise ValidationError(
            _('Password must contain at least 8 characters.'),
            code='password_too_short'
        )
    if not re.search(r'[A-Z]', value):
        raise ValidationError(
            _('Password must contain at least one uppercase letter.'),
            code='password_no_upper'
        )
    if not re.search(r'[a-z]', value):
        raise ValidationError(
            _('Password must contain at least one lowercase letter.'),
            code='password_no_lower'
        )
    if not re.search(r'\d', value):
        raise ValidationError(
            _('Password must contain at least one digit.'),
            code='password_no_digit'
        )
    if not re.search(r'[^A-Za-z0-9]', value):
        raise ValidationError(
            _('Password must contain at least one special character.'),
            code='password_no_special'
        )

def validate_phone_number(value):
    """
    Validates standard global phone format: +[country_code][number] (e.g. +1234567890)
    Accepts 10 to 15 digits overall.
    """
    pattern = r'^\+?1?\d{9,15}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Enter a valid phone number. e.g. +1234567890 (9 to 15 digits).'),
            code='invalid_phone_number'
        )

def validate_profile_picture_file(file):
    """
    Validates file size (max 5MB) and format (JPG, PNG, WEBP).
    """
    # Max size = 5MB
    max_size_bytes = 5 * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(
            _('Profile picture size exceeds maximum threshold of 5 MB.'),
            code='file_too_large'
        )

    # Format verification
    filename = file.name.lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise ValidationError(
            _('Only JPG, PNG, and WEBP image formats are supported.'),
            code='unsupported_image_extension'
        )

def validate_date_of_birth(value):
    """
    Validates that DOB is not in the future and user is at least 13 years old.
    """
    if value > date.today():
        raise ValidationError(
            _('Date of birth cannot be in the future.'),
            code='future_dob'
        )
    
    # Calculate age
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 13:
        raise ValidationError(
            _('User must be at least 13 years of age to register.'),
            code='under_age'
        )

def validate_linkedin_url(value):
    """
    Validates that a URL points to linkedin.com.
    """
    if value and 'linkedin.com' not in value.lower():
        raise ValidationError(
            _('Enter a valid LinkedIn profile URL.'),
            code='invalid_linkedin_url'
        )

def validate_github_url(value):
    """
    Validates that a URL points to github.com.
    """
    if value and 'github.com' not in value.lower():
        raise ValidationError(
            _('Enter a valid GitHub profile URL.'),
            code='invalid_github_url'
        )
