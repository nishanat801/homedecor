from django.urls import path
from . import views

app_name = 'address'

urlpatterns = [
    path('addresses/', views.address_list, name='address_list'),

    # path('', views.address_list, name='address_list'),  # Your existing address listing view
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:address_id>/', views. delete_address, name='delete_address'),
    path('select-address/', views.select_address, name='select_address'),

    path('set-default/', views.set_default_address, name='set_default'),
    path('addresses/myaccount/', views.address_management, name='address_management'),
    path('address/edit/myaccount/<int:address_id>/', views.edit_address_management, name='edit_address_management'),
    path('address/delete/myaccount/<int:address_id>/', views.delete_address_management, name='delete_address_management'),
    
     

    
]