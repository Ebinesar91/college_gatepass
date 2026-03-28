import re
from django import forms
from django.core.exceptions import ValidationError

from .models import CustomUser, Application, DEPARTMENT_CHOICES, YEAR_CHOICES


# ─────────────────────────────────────────────
#  Password Strength Helper
# ─────────────────────────────────────────────
def validate_strong_password(password):
    """Enforce: min 8 chars, at least one uppercase, one digit, one special char."""
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one digit.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
        raise ValidationError('Password must contain at least one special character (!@#$%^&* etc.).')


# ─────────────────────────────────────────────
#  Student Registration Form
# ─────────────────────────────────────────────
class StudentRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input form-input-with-icon',
            'placeholder': 'Min 8 chars, uppercase, digit & special char',
            'id': 'id_password1',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input form-input-with-icon',
            'placeholder': 'Re-enter your password',
            'id': 'id_password2',
        })
    )

    class Meta:
        model = CustomUser
        fields = ['student_name', 'register_number', 'email', 'department']
        widgets = {
            'student_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Full Name',
                'id': 'id_student_name',
            }),
            'register_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. 22CSE001',
                'id': 'id_register_number',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'student@college.edu',
                'id': 'id_email',
            }),
            'department': forms.Select(attrs={
                'class': 'form-input form-select',
                'id': 'id_department',
            }),
        }

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            validate_strong_password(password)
        return password

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_register_number(self):
        reg = self.cleaned_data.get('register_number')
        if CustomUser.objects.filter(register_number=reg).exists():
            raise forms.ValidationError('This register number is already in use.')
        return reg

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = user.email.lower().strip()
        user.set_password(self.cleaned_data['password1'])
        user.role = 'student'
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
#  Login Form
# ─────────────────────────────────────────────
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your@email.com',
            'autofocus': True,
            'id': 'id_login_email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input form-input-with-icon',
            'placeholder': 'Your password',
            'id': 'id_login_password',
        })
    )


# ─────────────────────────────────────────────
#  Forgot Password Form
# ─────────────────────────────────────────────
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Registered Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your registered email',
            'autofocus': True,
            'id': 'id_forgot_email',
        })
    )


# ─────────────────────────────────────────────
#  Reset Password Form
# ─────────────────────────────────────────────
class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input form-input-with-icon',
            'placeholder': 'New password (min 8 chars)',
            'id': 'id_new_password1',
        })
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input form-input-with-icon',
            'placeholder': 'Confirm new password',
            'id': 'id_new_password2',
        })
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            validate_strong_password(password)
        return password

    def clean_new_password2(self):
        p1 = self.cleaned_data.get('new_password1')
        p2 = self.cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2


# ─────────────────────────────────────────────
#  Application Form
# ─────────────────────────────────────────────
class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'type', 'year', 'section', 'department', 'reason',
            'from_date', 'to_date',
            'out_time', 'in_time', 'destination', 'event_name',
            'parent_contact', 'attachment', 'teacher',
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-input form-select', 'id': 'app_type'}),
            'year': forms.Select(attrs={'class': 'form-input form-select'}),
            'section': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. A'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'State your reason clearly...'
            }),
            'from_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'out_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time', 'id': 'out_time'}),
            'in_time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time', 'id': 'in_time'}),
            'destination': forms.TextInput(attrs={'class': 'form-input', 'id': 'destination', 'placeholder': 'Destination'}),
            'event_name': forms.TextInput(attrs={'class': 'form-input', 'id': 'event_name', 'placeholder': 'Event name (optional)'}),
            'parent_contact': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+91 XXXXXXXXXX'}),
            'attachment': forms.FileInput(attrs={'class': 'form-input-file'}),
            'department': forms.Select(attrs={'class': 'form-input form-select', 'id': 'student_dept'}),
            'teacher': forms.Select(attrs={'class': 'form-input form-select', 'id': 'teacher_select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = CustomUser.objects.filter(role='teacher')
        self.fields['teacher'].label = 'Select Your Class Teacher'
        self.fields['teacher'].empty_label = '— Select Teacher —'
        
        # Add department info to teacher dropdown choices manually for JS filtering
        # We can't easily add data-attributes to ModelChoiceField options without a custom widget,
        # so we'll just include Dept in the label (already done in __str__), 
        # but let's make it super explicit.
        self.fields['out_time'].required = False
        self.fields['in_time'].required = False
        self.fields['destination'].required = False
        self.fields['event_name'].required = False
        self.fields['parent_contact'].required = False
        self.fields['attachment'].required = False

    def clean(self):
        cleaned_data = super().clean()
        app_type = cleaned_data.get('type')
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if from_date and to_date and to_date < from_date:
            self.add_error('to_date', 'To date cannot be before From date.')

        if app_type == 'gatepass':
            if not cleaned_data.get('out_time'):
                self.add_error('out_time', 'Out time is required for Gate Pass.')
            if not cleaned_data.get('in_time'):
                self.add_error('in_time', 'In time is required for Gate Pass.')
            if not cleaned_data.get('destination'):
                self.add_error('destination', 'Destination is required for Gate Pass.')

        if app_type == 'od':
            if not cleaned_data.get('destination'):
                self.add_error('destination', 'Destination is required for OD.')

        return cleaned_data


# ─────────────────────────────────────────────
#  Approval Form (for teacher/hod/principal review)
# ─────────────────────────────────────────────
class ApprovalForm(forms.Form):
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.HiddenInput())
    remark = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 3,
            'placeholder': 'Add your remarks (optional)...',
        })
    )
