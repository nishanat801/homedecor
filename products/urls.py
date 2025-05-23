from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'products' 

urlpatterns = [
    path('products-list/', views.product_list, name='product_list'),  # Correct name
    path('add-products/', views.add_product, name='add_product'),
    path('edit-products/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('products/user/', views.category_with_products, name='products_user'),
    path('<int:category_id>/', views.category_with_products, name='category_products'),

    path("search_products/", views.search_products, name="search_products"),
    path('unlist/<int:product_id>/', views.unlist_product, name='unlist_product'),
    path('list/<int:product_id>/', views.list_product, name='list_product'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

