from django.urls import path
from . import views

urlpatterns = [
    # ── Initialization ──
    path('migrate/', views.run_migrations, name='migrate'),

    # ── Root ──
    path('', views.root_redirect, name='name'),

    # ── Authentication ──
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ── Password Reset ──
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_view, name='reset_password'),

    # ── Student ──
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('apply/', views.apply_view, name='apply'),

    # ── Teacher ──
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/review/<int:app_id>/', views.teacher_review, name='teacher_review'),

    # ── HOD ──
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/review/<int:app_id>/', views.hod_review, name='hod_review'),

    # ── Principal ──
    path('principal/', views.principal_dashboard, name='principal_dashboard'),
    path('principal/review/<int:app_id>/', views.principal_review, name='principal_review'),

    # ── Shared ──
    path('application/<int:app_id>/', views.application_detail, name='application_detail'),
]
