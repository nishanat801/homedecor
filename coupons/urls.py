from django.urls import path
from . import views  # Import views from the same app

urlpatterns = [
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),

    path('coupon/list/', views.coupon_list, name='coupon_list'),
    path('add/', views.add_coupon, name='add_coupon'),
    path('edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete/coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
]