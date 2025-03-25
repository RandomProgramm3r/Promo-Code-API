import django.contrib.admin
import django.urls

urlpatterns = [
    django.urls.path('api/business/', django.urls.include('business.urls')),
    django.urls.path('api/user/', django.urls.include('user.urls')),
    django.urls.path('api/ping/', django.urls.include('core.urls')),
    django.urls.path('admin/', django.contrib.admin.site.urls),
]
