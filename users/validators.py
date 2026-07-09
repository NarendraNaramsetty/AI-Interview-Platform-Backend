import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime

def validate_cgpa(value):
    """
    Validates that CGPA is a positive float between 0.0 and 10.0.
    """
    if value is not None:
        if value < 0.0 or value > 10.0:
            raise ValidationError(
                _('CGPA must be a decimal value between 0.0 and 10.0.'),
                code='invalid_cgpa'
            )

def validate_graduation_year(value):
    """
    Validates that the graduation year is between 1950 and 10 years in the future.
    """
    if value is not None:
        current_year = datetime.now().year
        max_year = current_year + 10
        if value < 1950 or value > max_year:
            raise ValidationError(
                _('Graduation year must be between 1950 and %(max_year)s.'),
                params={'max_year': max_year},
                code='invalid_graduation_year'
            )

def validate_json_string_list(value):
    """
    Validates that a JSON field is a list containing only strings.
    """
    if value is not None:
        if not isinstance(value, list):
            raise ValidationError(
                _('This field must be a JSON array of strings.'),
                code='invalid_json_format'
            )
        for item in value:
            if not isinstance(item, str):
                raise ValidationError(
                    _('All items inside the JSON array must be string elements.'),
                    code='invalid_json_type'
                )

def validate_github_profile_url(value):
    """
    Validates that a URL points to github.com if provided.
    """
    if value:
        if 'github.com' not in value.lower():
            raise ValidationError(
                _('Enter a valid GitHub profile URL.'),
                code='invalid_github_url'
            )

def validate_linkedin_profile_url(value):
    """
    Validates that a URL points to linkedin.com if provided.
    """
    if value:
        if 'linkedin.com' not in value.lower():
            raise ValidationError(
                _('Enter a valid LinkedIn profile URL.'),
                code='invalid_linkedin_url'
            )
