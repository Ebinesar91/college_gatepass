from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from permissions.views import run_migrations

urlpatterns = [
    path('migrate/', run_migrations, name='system_migrate'),
    path('admin/', admin.site.urls),
    path('', include('permissions.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
