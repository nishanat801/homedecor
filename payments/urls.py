from . import views
from django.urls import path
from .views import checkout_razorpay, payment_success,pay_view,payment_success_page



app_name = 'payments'

urlpatterns = [
    path("checkout/razorpay/", checkout_razorpay, name="checkout_razorpay"),
    path("payment-success/", payment_success, name="payment_success"),
    path("payment_success_page/", payment_success_page, name="payment_success_page"),
    path("payment-failed/",views.payment_failed, name="payment_failed"),
    path("payment-failed-page/",views.payment_failed_page, name="payment_failed_page"),
    path("retry-payment/<str:order_id>/", views.retry_payment, name="retry_payment"),
    path("pay/", pay_view, name="pay"),
    path("pay-retry/<int:order_id>/", views.pay_retry, name="pay_retry"),
    path("wallet/",views.wallet_view, name="wallet"),
    path("wallet-payment/", views.wallet_payment, name="wallet_payment"),
    path("confirm-wallet-payment/", views.confirm_wallet_payment, name="confirm_wallet_payment"),
    path('wallet-success/<int:order_id>/', views.wallet_payment_success, name='wallet_payment_success')

    
]