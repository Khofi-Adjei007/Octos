# Human_Resources/forms.py
from django import forms
from .models import Recommendation, Role
from branches.models import Branch  # Import Branch model

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'recommended_role', 'branch', 'notes', 'resume']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md',
                'placeholder': 'First Name',
                'required': 'required'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md',
                'placeholder': 'Middle Name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-md',
                'placeholder': 'Last Name',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-2 border rounded-md',
                'placeholder': 'Email Address',
                'required': 'required'
            }),
            'recommended_role': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-md',
                'required': 'required'
            }),
            'branch': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-md',
                'required': 'required'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded-md',
                'rows': 3,
                'placeholder': 'Additional Notes (optional)'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'w-full p-2 border rounded-md',
                'accept': 'application/pdf'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'middle_name': 'Middle Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'recommended_role': 'Recommended Role',
            'branch': 'Branch',
            'notes': 'Notes',
            'resume': 'Resume (PDF)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the logged-in user
        super().__init__(*args, **kwargs)
        # Pre-fill branch based on the branch manager's managed_branch
        if user and hasattr(user, 'userprofile') and user.userprofile.managed_branch:
            # Use a QuerySet with filter to include only the manager's branch
            self.fields['branch'].initial = user.userprofile.managed_branch
            self.fields['branch'].widget.attrs['readonly'] = True  # Make branch read-only
            self.fields['branch'].queryset = Branch.objects.filter(id=user.userprofile.managed_branch.id)
        else:
            self.fields['branch'].queryset = Branch.objects.all()
        # Set queryset for recommended_role
        self.fields['recommended_role'].queryset = Role.objects.all()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email already exists in Recommendation
        if Recommendation.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered. Please use a different email.")
        # Check if email exists in Employee model
        from employees.models import Employee
        if Employee.objects.filter(employee_email=email).exists():
            raise forms.ValidationError("This email is already associated with an employee.")
        return email

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if not resume.name.endswith('.pdf'):
                raise forms.ValidationError("Only PDF files are allowed.")
            if resume.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError("File size must be less than 10MB.")
        return resume