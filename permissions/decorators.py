from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """
    Decorator to restrict access to views based on user roles.
    Usage: @role_required('student') or @role_required('teacher', 'hod')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                role_home = {
                    'student': '/dashboard/',
                    'teacher': '/teacher/',
                    'hod': '/hod/',
                    'principal': '/principal/',
                }
                return redirect(role_home.get(request.user.role, '/login/'))

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
