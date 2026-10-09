from django.urls import path
from . import views

urlpatterns = [
    path("api/voice/", views.voice_api, name="voice_api"),
]