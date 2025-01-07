from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),
]