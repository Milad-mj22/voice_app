<<<<<<< HEAD


import sys
import os

# تنظیم مسیر پروژه
sys.path.insert(0, '/home/mykamani/voice_app/passenger_wsgi.py')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

=======


import sys
import os

# تنظیم مسیر پروژه
sys.path.insert(0, '/home/mykamani/voice_app/passenger_wsgi.py')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

>>>>>>> a2c94b69e0e42a901a6a9f97218defd2a293ec7d
