from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin-panal/', admin.site.urls),  # Admin panel URL
    path('hostel/', include('hostel.urls')),  # Include URLs from the hostel app
    path('', lambda request: redirect('login')),  # Redirect to login page if the root URL is accessed
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)