from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Application


# ── Custom Admin Forms for User Model ──
class CustomUserCreationForm(forms.ModelForm):
    """Admin form for creating new users."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'student_name', 'register_number', 'department', 'role', 'is_staff')
        help_texts = {
            'register_number': 'Required for Students only. Leave blank for Principal, HOD, or Teachers.',
            'is_staff': 'Allows the user to log into this Admin Panel.',
            'is_active': 'Set to False to ban or temporarily disable this user.',
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
#  Custom User Admin
# ─────────────────────────────────────────────
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Manage students and staff accounts via Django Admin."""
    model = CustomUser
    add_form = CustomUserCreationForm
    list_display = ('email', 'student_name', 'register_number', 'role', 'department', 'is_active', 'is_staff')
    list_filter = ('role', 'department', 'is_active', 'is_staff')
    search_fields = ('email', 'student_name', 'register_number')
    ordering = ('email',)

    fieldsets = (
        ('Login Info', {'fields': ('email', 'password')}),
        ('Personal Details', {'fields': ('student_name', 'register_number', 'department')}),
        ('System Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Activity Timeline', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'student_name', 'register_number', 'department', 'role', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )

    def save_model(self, request, obj, form, change):
        # ── Principal Constraint (Only ONE principal allowed) ──
        if obj.role == 'principal' and (not change or CustomUser.objects.filter(id=obj.id, role='principal').count() == 0):
            if CustomUser.objects.filter(role='principal').exclude(id=obj.id).exists():
                from django.contrib import messages
                messages.error(request, 'Error: A Principal account already exists. Only one is allowed.')
                return # Prevent saving
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────
#  Application Admin
# ─────────────────────────────────────────────
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Review and manage all student applications from the backend."""
    list_display = (
        'id', 'student_name', 'register_number', 'type',
        'status', 'current_stage', 'created_at'
    )
    list_filter = ('type', 'status', 'current_stage', 'department')
    search_fields = ('student_name', 'register_number', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Student Reference', {
            'fields': ('student', 'student_name', 'register_number', 'year', 'section', 'department')
        }),
        ('Request Body', {
            'fields': ('type', 'reason', 'from_date', 'to_date', 'out_time', 'in_time',
                       'destination', 'event_name', 'parent_contact', 'attachment')
        }),
        ('Multi-Stage Auth', {
            'fields': ('teacher', 'hod', 'principal')
        }),
        ('Status Tracker', {
            'fields': ('status', 'current_stage', 'teacher_status', 'teacher_remark',
                       'hod_status', 'hod_remark', 'principal_status', 'principal_remark')
        }),
    )


    # ── Global Admin Site Customization ──
admin.site.site_header = "College Permission Admin — Advanced Console"
admin.site.site_title = "Admin Console"
admin.site.index_title = "User & Workflow Management"
