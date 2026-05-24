from django.urls import path
from . import views

app_name = 'works'

urlpatterns = [
    path('', views.work_list, name='work_list'),
    path('<int:work_id>/', views.work_detail, name='work_detail'),
    path('create/', views.work_create, name='work_create'),
    path('my-works/', views.my_works, name='my_works'),
    path('<int:work_id>/download/', views.download_work, name='download_work'),
    path('<int:work_id>/purchase/', views.purchase_work, name='purchase_work'),
    path('<int:work_id>/edit/', views.work_edit, name='work_edit'),
]