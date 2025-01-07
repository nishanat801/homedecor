from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('login/', views.user_login_view, name='login'),
    path('admin-home/', views.admin_home_view, name='admin_home'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    
   
]