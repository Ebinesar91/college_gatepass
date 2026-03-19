from django.shortcuts import redirect
from django.contrib import messages


# ── Public URLs that don't require authentication ──
PUBLIC_URLS = [
    '/login/',
    '/register/',
    '/forgot-password/',
    '/reset-password/',
    '/admin/',
]

# ── Role to allowed URL prefix mapping ──
ROLE_URL_MAP = {
    'student': ['/dashboard/', '/apply/', '/application/', '/logout/'],
    'teacher': ['/teacher/', '/application/', '/logout/'],
    'hod': ['/hod/', '/application/', '/logout/'],
    'principal': ['/principal/', '/application/', '/logout/'],
    'admin': ['/admin/', '/logout/'],
}


class RoleBasedAccessMiddleware:
    """
    Custom middleware for role-based access control.
    Prevents unauthorized URL access between Students, Teachers, HODs, and Principal.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Always allow public paths
        for pub in PUBLIC_URLS:
            if path.startswith(pub):
                return self.get_response(request)

        # Allow media and static files
        if path.startswith('/media/') or path.startswith('/static/'):
            return self.get_response(request)

        # Handle root redirect separately or let view handles it
        if path == '/':
            return self.get_response(request)

        # ── User must be authenticated ──
        if not request.user.is_authenticated:
            # Prevent redirect loop if already on login (redundant with PUBLIC_URLS but safe)
            if not any(path.startswith(p) for p in PUBLIC_URLS):
                return redirect('/login/')
            return self.get_response(request)

        user = request.user
        role = getattr(user, 'role', 'student')

        # ── Superuser / Admin bypass ──
        if user.is_superuser or role == 'admin':
            return self.get_response(request)

        # ── Role Validation ──
        allowed_prefixes = ROLE_URL_MAP.get(role, [])
        allowed = any(path.startswith(prefix) for prefix in allowed_prefixes)

        if not allowed:
            # Log unauthorized access attempt if needed
            messages.error(request, 'You do not have permission to access that section.')
            
            # Redirect to their own dashboard
            role_home = {
                'student': '/dashboard/',
                'teacher': '/teacher/',
                'hod': '/hod/',
                'principal': '/principal/',
            }
            return redirect(role_home.get(role, '/login/'))

        return self.get_response(request)
