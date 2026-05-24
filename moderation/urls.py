from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('queue/', views.moderation_queue, name='queue'),
    path('moderate/<int:work_id>/', views.moderate_work, name='moderate_work'),
]