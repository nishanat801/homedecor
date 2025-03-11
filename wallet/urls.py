from django.urls import path
from .views import wallet_payment

urlpatterns = [
    path("wallet-payment/", wallet_payment, name="wallet_payment"),
]