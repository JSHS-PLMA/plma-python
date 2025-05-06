from django.urls import path
from . import views

urlpatterns = [
    path('youtube-audio/', views.youtube_audio, name='youtube_audio'),
]