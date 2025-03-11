from django.db import models
from django.contrib.auth.models import User
from address.models import Address
from products.models import Product
from coupons.models import Coupon
from Authentication.models import CustomUser
import uuid


class Order(models.Model):
    STATUS_CHOICES = [
       ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    tracking_number = models.CharField(max_length=20, unique=True, default="PENDING")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")  # Payment Status
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon,on_delete=models.CASCADE,blank=True,null=True)

    def save(self, *args, **kwargs):
        if not self.tracking_number or self.tracking_number == "PENDING":
            self.tracking_number = str(uuid.uuid4().hex[:10]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - {self.status}"

class OrderItem(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Number of items ordered
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)  # Price per item at purchase time
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Discount per item
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Final price after discount
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"