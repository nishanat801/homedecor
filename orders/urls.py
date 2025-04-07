from django.urls import path
from .views import place_order
from . import views

app_name = "orders"

urlpatterns = [
    path("place/order", place_order, name="place_order"),
    path("order-success/<int:order_id>/", views.order_success, name="order_success"),
    path('checkout-page/', views.checkout_page, name='checkout_page'),

    path('orders/', views.user_order_list, name='user_order_list'),
    path('cancel-order/<int:item_id>/', views.cancel_order, name='cancel_order'),
    path("reorder/<int:item_id>/", views.reorder_item, name="reorder_item"),
    path('return-product/<int:item_id>/', views.return_product, name='return_product'),

    path("orders/admin", views.admin_orders, name="admin_orders"),
    path("orders/admin/<int:order_id>/", views.admin_order_details, name="admin_order_details"),

    path('order/<int:order_id>/download-invoice/', views.download_invoice, name='download_invoice'),
]