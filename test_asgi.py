import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from config.asgi import application
from apps.voice.routing import websocket_urlpatterns

print("✅ ASGI loaded")
print("✅ WebSocket routes:", websocket_urlpatterns)

for r in websocket_urlpatterns:
    print("   -", r.pattern)