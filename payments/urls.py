from . import views
from django.urls import path
from .views import checkout_razorpay, payment_success,pay_view,payment_success_page



app_name = 'payments'

urlpatterns = [
    path("checkout/razorpay/", checkout_razorpay, name="checkout_razorpay"),
    path("payment-success/", payment_success, name="payment_success"),
    path("payment_success_page/", payment_success_page, name="payment_success_page"),

     path("pay/", pay_view, name="pay"),
     path("wallet/",views.wallet_view, name="wallet"),
    
]