from django.urls import path
from . import views
# from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/user/', views.home_view, name='products_user'),
    path('login/', views.user_login_view, name='login'),
    path('admin-home/', views.admin_home_view, name='admin_home'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    #  path('products/', views.product_list, name='product_list'),  # URL for listing all products
    path('product/<int:product_id>/', views.product_details, name='product_details'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('edit-review/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    
]