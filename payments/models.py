from django.db import models

class Payment(models.Model):
    name = models.CharField(max_length=100,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.BooleanField(default=False)

    def __str__(self):
        return self.name
