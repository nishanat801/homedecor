from django.urls import path
from . import views

app_name = 'address'

urlpatterns = [
    path('addresses/', views.address_list, name='address_list'),
]