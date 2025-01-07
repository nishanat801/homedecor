from django.urls import path
from . import views

app_name = 'products' 

urlpatterns = [
    path('products-list/', views.product_list, name='product_list'),
    path('add-products/', views.add_product, name='add_product'),
    path('edit-products/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('products/user/', views.category_with_products, name='category_list'),  # Show all categories
    path('<int:category_id>/', views.category_with_products, name='category_products'),
]

