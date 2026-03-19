from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────
#  Custom User Manager
# ─────────────────────────────────────────────
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('student_name', 'System Admin')
        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────────
#  Role Choices
# ─────────────────────────────────────────────
ROLE_CHOICES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
    ('hod', 'HOD'),
    ('principal', 'Principal'),
    ('admin', 'Admin'),
]

DEPARTMENT_CHOICES = [
    ('CSE', 'Computer Science & Engineering'),
    ('ECE', 'Electronics & Communication Engineering'),
    ('EEE', 'Electrical & Electronics Engineering'),
    ('MECH', 'Mechanical Engineering'),
    ('CIVIL', 'Civil Engineering'),
    ('IT', 'Information Technology'),
    ('AIDS', 'Artificial Intelligence & Data Science'),
    ('AIML', 'AI & Machine Learning'),
    ('MBA', 'Master of Business Administration'),
    ('MCA', 'Master of Computer Applications'),
    ('OTHER', 'Other'),
]


# ─────────────────────────────────────────────
#  Custom User Model
# ─────────────────────────────────────────────
class CustomUser(AbstractBaseUser, PermissionsMixin):
    student_name = models.CharField(max_length=150)
    register_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='CSE')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['student_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.student_name} ({self.email}) — Dept: {self.department}"

    def get_full_name(self):
        return self.student_name

    def get_short_name(self):
        return self.student_name


# ─────────────────────────────────────────────
#  Permission Application Model
# ─────────────────────────────────────────────
APPLICATION_TYPE_CHOICES = [
    ('gatepass', 'Gate Pass'),
    ('od', 'On Duty (OD)'),
    ('leave', 'Leave Letter'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('forwarded', 'Forwarded'),
]

STAGE_CHOICES = [
    ('teacher', 'Waiting for Teacher'),
    ('hod', 'Waiting for HOD'),
    ('principal', 'Waiting for Principal'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

YEAR_CHOICES = [
    ('1', '1st Year'),
    ('2', '2nd Year'),
    ('3', '3rd Year'),
    ('4', '4th Year'),
]


class Application(models.Model):
    # Student info
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    student_name = models.CharField(max_length=150)
    register_number = models.CharField(max_length=50)
    year = models.CharField(max_length=5, choices=YEAR_CHOICES)
    section = models.CharField(max_length=10)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='CSE')

    # Request info
    type = models.CharField(max_length=20, choices=APPLICATION_TYPE_CHOICES)
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()

    # Dynamic fields
    out_time = models.TimeField(null=True, blank=True)      # gatepass only
    in_time = models.TimeField(null=True, blank=True)       # gatepass only
    destination = models.CharField(max_length=255, blank=True)  # gatepass + od
    event_name = models.CharField(max_length=255, blank=True)   # od optional

    # Extras
    parent_contact = models.CharField(max_length=15, blank=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    # Approval chain
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teacher_applications'
    )
    hod = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='hod_applications'
    )
    principal = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='principal_applications'
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    teacher_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hod_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    principal_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='teacher')

    # Remarks
    teacher_remark = models.TextField(blank=True)
    hod_remark = models.TextField(blank=True)
    principal_remark = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return f"{self.student_name} — {self.get_type_display()} — {self.status.upper()}"

    def get_status_badge_class(self):
        badge_map = {
            'pending': 'badge-warning',
            'approved': 'badge-success',
            'rejected': 'badge-danger',
            'forwarded': 'badge-info',
        }
        return badge_map.get(self.status, 'badge-secondary')
