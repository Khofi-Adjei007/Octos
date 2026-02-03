from django.core.exceptions import ValidationError

# ============================================================
# Helpers & Validators
# ============================================================

def validate_resume_file(value):
    """
    Validate uploaded resume files.
    Allowed formats: PDF, DOC, DOCX
    Max size: 10MB
    """
    name = value.name.lower()
    allowed_extensions = ('.pdf', '.doc', '.docx')

    if not name.endswith(allowed_extensions):
        raise ValidationError('Only PDF, DOC, DOCX files are allowed.')

    if value.size > 10 * 1024 * 1024:
        raise ValidationError('File size must be less than 10MB.')
