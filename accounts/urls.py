from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('top-up/', views.top_up_balance, name='top_up_balance'),
    path('author/<int:user_id>/', views.author_detail, name='author_detail'),
    path('become-author/', views.become_author, name='become_author'),
]