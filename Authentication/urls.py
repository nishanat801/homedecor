from django.urls import path
from . import views



app_name = 'Authentication'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_user'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password-otp-verify/', views.forgot_password_otp_verify, name='forgot_password_otp_verify'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('product-list/', views.product_list, name='product_list'),
    
]

