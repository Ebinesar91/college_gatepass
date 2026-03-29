from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.core.cache import cache
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.db.models import Q
from django.core.management import call_command
from django.http import HttpResponse

from .models import CustomUser, Application
from .forms import (
    StudentRegisterForm, LoginForm, ApplicationForm,
    ForgotPasswordForm, ResetPasswordForm,
)
from .decorators import role_required


# ─────────────────────────────────────────────
#  Helper: Role-based redirect
# ─────────────────────────────────────────────
def _redirect_by_role(user):
    role_map = {
        'student': '/dashboard/',
        'teacher': '/teacher/',
        'hod': '/hod/',
        'principal': '/principal/',
        'admin': '/admin/',
    }
    return redirect(role_map.get(user.role, '/admin/' if user.is_staff else '/login/'))


# ─────────────────────────────────────────────
#  Root redirect
# ─────────────────────────────────────────────
def root_redirect(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    return redirect('/login/')


# ─────────────────────────────────────────────
#  Database Initialization
# ─────────────────────────────────────────────
def run_migrations(request):
    try:
        # 1. Run Migrations
        print("⚙️ Running migrations...")
        call_command('migrate', interactive=False)
        
        # 2. Create Admin if not exists
        admin_email = 'admin@gmail.com'
        if not CustomUser.objects.filter(email=admin_email).exists():
            CustomUser.objects.create_superuser(
                email=admin_email,
                password='Admin123!',
                student_name='System Admin'
            )
            return HttpResponse("✅ SUCCESS: Database Migrated & Admin (admin@gmail.com / Admin123!) Created!")
        
        return HttpResponse("✅ SUCCESS: Database is already up to date.")
    except Exception as e:
        return HttpResponse(f"❌ ERROR: {e}")


# ─────────────────────────────────────────────
#  Register
# ─────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = StudentRegisterForm()
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.student_name}! Your account has been created successfully.')
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'auth/register.html', {'form': form})


# ─────────────────────────────────────────────
#  Login  (with rate limiting)
# ─────────────────────────────────────────────
MAX_ATTEMPTS = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
LOCKOUT_MINUTES = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15)


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']

            # Rate-limit check
            cache_key = f'login_attempts_{email}'
            attempts = cache.get(cache_key, 0)

            if attempts >= MAX_ATTEMPTS:
                messages.error(
                    request,
                    f'Too many failed attempts. Account temporarily locked for {LOCKOUT_MINUTES} minutes.'
                )
                return render(request, 'auth/login.html', {'form': form, 'locked': True})

            user = authenticate(request, email=email, password=password)
            if user is not None:
                cache.delete(cache_key)  # Clear attempts on success
                login(request, user)
                messages.success(request, f'Welcome back, {user.student_name}!')
                return _redirect_by_role(user)
            else:
                # Increment failed attempts
                cache.set(cache_key, attempts + 1, timeout=LOCKOUT_MINUTES * 60)
                remaining = MAX_ATTEMPTS - (attempts + 1)
                if remaining > 0:
                    messages.error(request, f'Invalid email or password. {remaining} attempt(s) remaining.')
                else:
                    messages.error(request, f'Account locked for {LOCKOUT_MINUTES} minutes due to too many failed attempts.')

    return render(request, 'auth/login.html', {'form': form})


# ─────────────────────────────────────────────
#  Logout
# ─────────────────────────────────────────────
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('/login/')


# ─────────────────────────────────────────────
#  Forgot Password
# ─────────────────────────────────────────────
def forgot_password_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = ForgotPasswordForm()
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            # Always show success message regardless of email existence (security best practice)
            try:
                user = CustomUser.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = request.build_absolute_uri(
                    f'/reset-password/{uid}/{token}/'
                )
                send_mail(
                    subject='Password Reset — Smart CPMS',
                    message=(
                        f'Hello {user.student_name},\n\n'
                        f'You requested a password reset for your Smart CPMS account.\n\n'
                        f'Click the link below to reset your password (expires in 1 hour):\n'
                        f'{reset_link}\n\n'
                        f'If you did not request this, please ignore this email.\n\n'
                        f'— Smart CPMS Team'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except CustomUser.DoesNotExist:
                pass  # Don't reveal if email exists
            messages.success(
                request,
                'If an account exists with that email, a password reset link has been sent. '
                'Check your inbox (and spam folder).'
            )
            return redirect('/forgot-password/')

    return render(request, 'auth/forgot_password.html', {'form': form})


# ─────────────────────────────────────────────
#  Reset Password
# ─────────────────────────────────────────────
def reset_password_view(request, uidb64, token):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    # Validate token
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    token_valid = user is not None and default_token_generator.check_token(user, token)

    if not token_valid:
        messages.error(request, 'This password reset link is invalid or has expired.')
        return render(request, 'auth/reset_password_invalid.html')

    form = ResetPasswordForm()
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, 'Your password has been reset successfully. Please log in.')
            return redirect('/login/')

    return render(request, 'auth/reset_password.html', {'form': form, 'uidb64': uidb64, 'token': token})


# ─────────────────────────────────────────────
#  Student Dashboard
# ─────────────────────────────────────────────
@login_required
@role_required('student')
def student_dashboard(request):
    applications = Application.objects.filter(student=request.user)

    total = applications.count()
    approved = applications.filter(status='approved').count()
    pending = applications.filter(status='pending').count()
    rejected = applications.filter(status='rejected').count()

    context = {
        'applications': applications,
        'total': total,
        'approved': approved,
        'pending': pending,
        'rejected': rejected,
    }
    return render(request, 'student/dashboard.html', context)


# ─────────────────────────────────────────────
#  Apply for Permission
# ─────────────────────────────────────────────
@login_required
@role_required('student')
def apply_view(request):
    form = ApplicationForm(initial={'department': request.user.department})
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.student = request.user
            app.student_name = request.user.student_name
            app.register_number = request.user.register_number
            app.department = request.user.department
            app.status = 'pending'
            app.current_stage = 'teacher'
            app.teacher_status = 'pending'
            app.hod_status = 'pending'
            app.principal_status = 'pending'
            app.save()
            messages.success(request, '✅ Your application has been submitted successfully!')
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Please fix the errors in the form.')

    return render(request, 'student/apply.html', {'form': form})


# ─────────────────────────────────────────────
#  Teacher Dashboard
# ─────────────────────────────────────────────
@login_required
@role_required('teacher')
def teacher_dashboard(request):
    all_apps = Application.objects.filter(teacher=request.user)
    pending_apps = all_apps.filter(current_stage='teacher', teacher_status='pending')
    processed_apps = all_apps.exclude(teacher_status='pending')

    approved_count = all_apps.filter(teacher_status='approved').count()
    rejected_count = all_apps.filter(teacher_status='rejected').count()

    context = {
        'pending_apps': pending_apps,
        'processed_apps': processed_apps,
        'pending_count': pending_apps.count(),
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': all_apps.count(),
    }
    return render(request, 'teacher/dashboard.html', context)


@login_required
@role_required('teacher')
def teacher_review(request, app_id):
    app = get_object_or_404(Application, id=app_id, teacher=request.user)

    if app.current_stage != 'teacher' or app.teacher_status != 'pending':
        messages.warning(request, 'This application is no longer awaiting your review.')
        return redirect('/teacher/')

    if request.method == 'POST':
        action = request.POST.get('action')
        remark = request.POST.get('remark', '')
        hod_id = request.POST.get('hod_id')
        app.teacher_remark = remark

        if action == 'approve':
            if not hod_id:
                messages.error(request, 'Please select the HOD for authorization.')
                return render(request, 'teacher/review.html', {
                'app': app, 
                'hods': CustomUser.objects.filter(role='hod', department=app.department)
            })
                
            app.teacher_status = 'approved'
            app.current_stage = 'hod'
            app.hod = get_object_or_404(CustomUser, id=hod_id, role='hod')
            app.status = 'pending'
            messages.success(request, 'Application approved and forwarded to HOD.')
        elif action == 'reject':
            app.teacher_status = 'rejected'
            app.status = 'rejected'
            app.current_stage = 'rejected'
            messages.warning(request, 'Application has been rejected.')

        app.save()
        return redirect('/teacher/')

    hods = CustomUser.objects.filter(role='hod', department=app.department)
    return render(request, 'teacher/review.html', {'app': app, 'hods': hods})


# ─────────────────────────────────────────────
#  HOD Dashboard
# ─────────────────────────────────────────────
@login_required
@role_required('hod')
def hod_dashboard(request):
    all_apps = Application.objects.filter(teacher_status='approved')
    pending_apps = all_apps.filter(current_stage='hod', hod_status='pending')
    processed_apps = all_apps.filter(hod_status__in=['approved', 'rejected'])

    approved_count = all_apps.filter(hod_status='approved').count()
    rejected_count = all_apps.filter(hod_status='rejected').count()

    context = {
        'pending_apps': pending_apps,
        'processed_apps': processed_apps,
        'pending_count': pending_apps.count(),
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': all_apps.count(),
    }
    return render(request, 'hod/dashboard.html', context)


@login_required
@role_required('hod')
def hod_review(request, app_id):
    app = get_object_or_404(Application, id=app_id)

    if app.current_stage != 'hod' or app.hod_status != 'pending':
        messages.warning(request, 'This application is not awaiting HOD review.')
        return redirect('/hod/')

    if request.method == 'POST':
        action = request.POST.get('action')
        remark = request.POST.get('remark', '')
        principal_id = request.POST.get('principal_id')
        app.hod_remark = remark

        if action == 'approve':
            app.hod_status = 'approved'
            if app.type == 'gatepass':
                if not principal_id:
                    messages.error(request, 'Please select the Principal for final authorization.')
                    return render(request, 'hod/review.html', {'app': app, 'principals': CustomUser.objects.filter(role='principal')})
                
                app.current_stage = 'principal'
                app.principal = get_object_or_404(CustomUser, id=principal_id, role='principal')
                app.status = 'pending'
                messages.success(request, 'Gate Pass approved and forwarded to Principal.')
            else:
                app.current_stage = 'approved'
                app.status = 'approved'
                messages.success(request, 'Application fully approved!')
        elif action == 'reject':
            app.hod_status = 'rejected'
            app.status = 'rejected'
            app.current_stage = 'rejected'
            messages.warning(request, 'Application has been rejected.')

        app.save()
        return redirect('/hod/')

    principals = CustomUser.objects.filter(role='principal')
    return render(request, 'hod/review.html', {'app': app, 'principals': principals})


# ─────────────────────────────────────────────
#  Principal Dashboard
# ─────────────────────────────────────────────
@login_required
@role_required('principal')
def principal_dashboard(request):
    all_apps = Application.objects.filter(type='gatepass', hod_status='approved')
    pending_apps = all_apps.filter(current_stage='principal', principal_status='pending')
    processed_apps = all_apps.filter(principal_status__in=['approved', 'rejected'])

    approved_count = all_apps.filter(principal_status='approved').count()
    rejected_count = all_apps.filter(principal_status='rejected').count()

    context = {
        'pending_apps': pending_apps,
        'processed_apps': processed_apps,
        'pending_count': pending_apps.count(),
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': all_apps.count(),
    }
    return render(request, 'principal/dashboard.html', context)


@login_required
@role_required('principal')
def principal_review(request, app_id):
    app = get_object_or_404(Application, id=app_id)

    if app.current_stage != 'principal' or app.type != 'gatepass':
        messages.warning(request, 'This application is not awaiting Principal review.')
        return redirect('/principal/')

    if request.method == 'POST':
        action = request.POST.get('action')
        remark = request.POST.get('remark', '')
        app.principal = request.user
        app.principal_remark = remark

        if action == 'approve':
            app.principal_status = 'approved'
            app.current_stage = 'approved'
            app.status = 'approved'
            messages.success(request, 'Gate Pass fully approved!')
        elif action == 'reject':
            app.principal_status = 'rejected'
            app.status = 'rejected'
            app.current_stage = 'rejected'
            messages.warning(request, 'Gate Pass has been rejected.')

        app.save()
        return redirect('/principal/')

    return render(request, 'principal/review.html', {'app': app})


# ─────────────────────────────────────────────
#  Application Detail
# ─────────────────────────────────────────────
@login_required
def application_detail(request, app_id):
    user = request.user
    if user.role == 'student':
        app = get_object_or_404(Application, id=app_id, student=user)
    elif user.role == 'teacher':
        app = get_object_or_404(Application, id=app_id, teacher=user)
    else:
        app = get_object_or_404(Application, id=app_id)

    return render(request, 'shared/application_detail.html', {'app': app})
