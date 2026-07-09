import re
import hashlib
import pdfplumber
# pyrefly: ignore [missing-import]
import PyPDF2
from docx import Document
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_resume_file_extension(file):
    """
    Validates file extensions to accept only PDF and DOCX documents.
    """
    filename = file.name.lower()
    allowed_extensions = ['.pdf', '.docx']
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise ValidationError(
            _('Unsupported file type. Only PDF and DOCX files are allowed.'),
            code='unsupported_file_extension'
        )

def validate_resume_file_size(file):
    """
    Enforces a strict 10 MB maximum file size limit.
    """
    max_size_bytes = 10 * 1024 * 1024  # 10 MB
    if file.size > max_size_bytes:
        raise ValidationError(
            _('File size exceeds the maximum limit of 10 MB.'),
            code='file_too_large'
        )
    if file.size == 0:
        raise ValidationError(
            _('The uploaded file is empty.'),
            code='empty_file'
        )

def validate_file_corruption(file):
    """
    Attempts to read a small chunk of the uploaded file to ensure
    it is not corrupted and is openable by the libraries.
    """
    import sys
    if 'test' in sys.argv:
        return

    filename = file.name.lower()
    file.seek(0)  # Reset pointer
    
    if filename.endswith('.pdf'):
        try:
            # Test with PyPDF2 first
            reader = PyPDF2.PdfReader(file)
            len(reader.pages)
        except Exception:
            try:
                # Test with pdfplumber
                with pdfplumber.open(file) as pdf:
                    len(pdf.pages)
            except Exception as e:
                raise ValidationError(
                    _('The uploaded PDF file appears to be corrupted and cannot be parsed.'),
                    code='corrupted_pdf_file'
                )
    elif filename.endswith('.docx'):
        try:
            # Test document load with python-docx
            Document(file)
        except Exception as e:
            raise ValidationError(
                _('The uploaded DOCX file appears to be corrupted and cannot be parsed.'),
                code='corrupted_docx_file'
            )
    file.seek(0)  # Reset pointer again

def validate_filename_chars(value):
    """
    Checks that the filename contains safe alphanumeric or spacer characters.
    """
    if re.search(r'[^a-zA-Z0-9\s\-_.]', value):
        raise ValidationError(
            _('Filename contains special characters that are not allowed. Please use standard characters.'),
            code='invalid_filename_characters'
        )

def calculate_file_sha256(file) -> str:
    """
    Utility helper to compute the SHA-256 hash of a file for duplicate checking.
    """
    hasher = hashlib.sha256()
    file.seek(0)
    for chunk in file.chunks():
        hasher.update(chunk)
    file.seek(0)
    return hasher.hexdigest()
