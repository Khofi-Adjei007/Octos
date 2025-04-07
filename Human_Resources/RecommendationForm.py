# Human_Resources/forms.py
from django import forms
from .models import Recommendation  # Removed Role import
from branches.models import Branch

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
            self.fields['branch'].initial = user.userprofile.managed_branch
            self.fields['branch'].widget.attrs['readonly'] = True
            self.fields['branch'].queryset = Branch.objects.filter(id=user.userprofile.managed_branch.id)
        else:
            self.fields['branch'].queryset = Branch.objects.all()
        # Removed: self.fields['recommended_role'].queryset = Role.objects.all()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Recommendation.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered. Please use a different email.")
        from employees.models import Employee
        if Employee.objects.filter(employee_email=email).exists():
            raise forms.ValidationError("This email is already associated with an employee.")
        return email

    # Removed clean_resume method since the model validator handles this