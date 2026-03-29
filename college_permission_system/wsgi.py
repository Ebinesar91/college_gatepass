import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from pathlib import Path

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_permission_system.settings')

# Build the WSGI application
application = get_wsgi_application()

# Vercel needs 'app'
app = application
