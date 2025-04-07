from django.urls import path
from . import views

urlpatterns = [
path('cart/', views.cart_view, name='cart'),  # View cart items
path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Add to cart
 path('cart/update/<int:product_id>/<str:action>/', views.update_quantity, name='update_quantity'),
path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

path('wishlist/', views.wishlist_view, name='wishlist'),
path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

]