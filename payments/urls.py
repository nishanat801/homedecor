from . import views
from django.urls import path
from .views import pay_view,checkout_razorpay, payment_success



app_name = 'payments'

urlpatterns = [
    path("checkout/razorpay/", checkout_razorpay, name="checkout_razorpay"),
    path("payment-success/", payment_success, name="payment_success"),
     path("pay/",pay_view, name="pay"),
]