

import sys
import os

# تنظیم مسیر پروژه
sys.path.insert(0, '/home/mykamani/voice_app/passenger_wsgi.py')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


