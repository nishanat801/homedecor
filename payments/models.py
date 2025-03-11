from django.db import models
from Authentication.models import CustomUser

class Payment(models.Model):
    name = models.CharField(max_length=100,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def credit(self, amount):
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(wallet=self, transaction_type="credit", amount=amount, description="Product Return")

    def debit(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            WalletTransaction.objects.create(wallet=self, transaction_type="debit", amount=amount, description="Order Payment")
            return True
        return False  # Insufficient balance

    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - {self.amount}"