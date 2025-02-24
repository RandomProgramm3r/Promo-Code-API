import os

import django.core.asgi

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promo_code.settings')

application = django.core.asgi.get_asgi_application()
