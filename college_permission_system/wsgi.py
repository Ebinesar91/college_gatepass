"""
WSGI config for college_permission_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_permission_system.settings')

# 🚀 Running auto-migrations on startup (fixes 500 error for new databases)
try:
    import django
    django.setup()
    from django.core.management import call_command
    print("⚙️ Running migrations...")
    call_command('migrate', interactive=False)
    print("✅ Migrations completed!")
except Exception as e:
    print(f"⚠️ Migration failed: {e}")

application = get_wsgi_application()

# Vercel requires the WSGI callable to be named 'app'
app = application
