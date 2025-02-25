import django.contrib.admin
import django.urls

urlpatterns = [
    django.urls.path('api/ping/', django.urls.include('core.urls')),
    django.urls.path('admin/', django.contrib.admin.site.urls),
]
