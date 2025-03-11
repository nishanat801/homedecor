from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import OrderItem
from payments.models import Wallet

@receiver(post_save, sender=OrderItem)
def credit_wallet_on_return(sender, instance, **kwargs):
    if instance.status == "Returned":  # Check if the order is marked as Returned
        wallet, created = Wallet.objects.get_or_create(user=instance.order.user)
        wallet.credit(instance.price)  # Credit the wallet with the returned item's price