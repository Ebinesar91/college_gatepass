"""
WSGI config for college_permission_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_permission_system.settings')

# 🚀 Running auto-migrations on startup (fixes 500 error for new databases)
try:
    import django
    django.setup()
    from django.core.management import call_command
    print("⚙️ Running migrations...")
    call_command('migrate', interactive=False)
    print("✅ Migrations completed!")

    # 🔑 Auto-create admin if it doesn't exist
    from permissions.models import CustomUser
    admin_email = 'admin@gmail.com'
    if not CustomUser.objects.filter(email=admin_email).exists():
        CustomUser.objects.create_superuser(
            email=admin_email,
            password='Admin123!',
            student_name='System Admin'
        )
        print(f"🔑 Admin user created: {admin_email} / Admin123!")
except Exception as e:
    print(f"⚠️ Migration failed: {e}")

application = get_wsgi_application()

# 🚀 The "Master Fix" for Vercel Static Files
# We wrap the application in WhiteNoise directly at the WSGI level.
# This ensures that /static/ requests are handled immediately.
application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'static'))
application.add_files(os.path.join(BASE_DIR, 'static'), prefix='static/')

# Vercel requires the WSGI callable to be named 'app'
app = application
