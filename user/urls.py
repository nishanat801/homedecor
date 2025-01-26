from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('profile/', views.user_profile_list, name='user_profile_list'),  # List all users
    path('block/<int:user_id>/', views.block_user, name='block_user'),   # Block user
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),  # Unblock user

    path('user/details/',views.user_details,name='user_details'),
    path('user/address/',views.save_address,name='user_address'),
    path('checkout/', views.checkout, name='checkout'), 
    path('select-address/', views.select_address, name='select_address'),
    path('placeorder/', views.place_order, name='place_order'),

    path('my_account/',views.my_account,name='my_account'),
   path('orders/user/', views.user_order_list, name='user_orders'),
    


    path('order-success/', views.order_success, name='order_success'),
    path('orders/list/', views.admin_orders, name='admin_orders'),
    path('orders/item<int:order_id>/', views.admin_order_details, name='order_details')
]