# from django.urls import path
# from . import views

# urlpatterns = [
#     path('user/signup/', views.signup_view, name='signup'),
#     path('verify-otp/', views.otp_verify_view, name='verify_otp'),
#     path('user/login/', views.login_view, name='login_user'),
#     path('home/', views.home_view, name='home_user'),
#     path('user/forgot/forgot_password', views.home_view, name='home_user'),

# ]

from django.urls import path
from . import views

app_name = 'Authentication'

urlpatterns = [
    path('signup/', views.signup_view, name='signup_user'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('login/', views.login_user, name='login_user'),
    # path('logout/', views.logout_user, name='logout_user'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('product-list/', views.product_list, name='product_list'),
]

