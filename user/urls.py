from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('profile/', views.user_profile_list, name='user_profile_list'),  # List all users
    path('block/<int:user_id>/', views.block_user, name='block_user'),   # Block user
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),  # Unblock user
    path('my_account/',views.my_account,name='my_account'),
    
    
    
]