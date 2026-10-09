from django.urls import path
from . import views

urlpatterns = [
    path("api/voice/", views.voice_api, name="voice_api"),
    path("api/voice/text/", views.voice_text_api, name="voice_text_api"),
]