from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import OrderItem

@receiver(post_save, sender=OrderItem)
def update_wallet_on_return(sender, instance, **kwargs):
    if instance.status == "Returned":
        # Logic to credit the wallet when an item is returned
        print("Wallet credited for returned item!")