# public/public_apply_forms.py
from django import forms
from Human_Resources.models import PublicApplication, validate_resume_file

COMMON_INPUT_CLASSES = "mt-1 block w-full rounded-md border-gray-200 shadow-sm focus:ring-2 focus:ring-[var(--brand-green)]"

class PublicApplyForm(forms.ModelForm):
    resume = forms.FileField(
        required=False,
        validators=[validate_resume_file],
        widget=forms.ClearableFileInput(attrs={
            "class": "mt-1 block w-full text-sm",
            "accept": ".pdf,.doc,.docx,.pdf"
        })
    )

    class Meta:
        model = PublicApplication
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone",
            "recommended_role",
            "resume",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": COMMON_INPUT_CLASSES, "placeholder": "First name"}),
            "middle_name": forms.TextInput(attrs={"class": COMMON_INPUT_CLASSES, "placeholder": "Middle name (optional)"}),
            "last_name": forms.TextInput(attrs={"class": COMMON_INPUT_CLASSES, "placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"class": COMMON_INPUT_CLASSES, "placeholder": "you@example.com"}),
            "phone": forms.TextInput(attrs={"class": COMMON_INPUT_CLASSES, "placeholder": "+233 20 123 4567"}),
            "recommended_role": forms.Select(attrs={"class": COMMON_INPUT_CLASSES}),
            "notes": forms.Textarea(attrs={"class": COMMON_INPUT_CLASSES, "rows": 4, "placeholder": "Tell us about your experience..."}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            return email.strip().lower()
        return email

    def clean(self):
        cleaned = super().clean()
        # at least one contact method
        if not cleaned.get("email") and not cleaned.get("phone"):
            raise forms.ValidationError("Please provide either an email address or a phone number.")
        return cleaned
