from django.contrib.auth.models import AbstractUser
from django.db import models
from  Authentication.models import CustomUser
from  products.models import Product
from django.utils.timezone import now
from datetime import  timedelta


# class UserDetails(models.Model):
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
#     phone = models.CharField(max_length=15)
#     email = models.EmailField()
#     full_name = models.CharField(max_length=255)
#     pincode = models.CharField(max_length=6)
#     city = models.CharField(max_length=100, null=True)
#     state = models.CharField(max_length=100,null=True)
#     address_line_1 = models.CharField(max_length=255,null=True)
#     address_line_2 = models.CharField(max_length=255, blank=True, null=True)
#     landmark = models.CharField(max_length=255, blank=True, null=True)
#     date_of_order = models.DateField(default=now)
#     estimated_delivery = models.DateField(default=now() + timedelta(days=7))
#     address_type = models.CharField(
#     max_length=50,
#     choices=[('Home', 'Home'), ('Office', 'Office'), ('Others', 'Others')],
#     default='Home',
# )

# from django.contrib.auth import get_user_model

# User = get_user_model()


# class Order(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     full_name = models.CharField(max_length=255, default="Unknown User")  # Storing user name
#     tracking_number = models.CharField(max_length=20, unique=True, default="PENDING")
#     status = models.CharField(max_length=20, choices=[
#         ('pending', 'Pending'),
#         ('shipped', 'Shipped'),
#         ('delivered', 'Delivered')
#     ], default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order {self.id} - {self.user.username}"
# class OrderItem(models.Model):
#     STATUS_CHOICES = [
#         ('Order Pending', 'Order Pending'),
#         ('Order Confirmed', 'Order Confirmed'),
#         ('Shipped', 'Shipped'),
#         ('Delivered', 'Delivered'),
#         ('Requested Return', 'Requested Return'),
#         ('Returned', 'Returned'),
#         ('Cancelled', 'Cancelled'),
#     ]

#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Order Pending')
    
    
#     def __str__(self):
#         return f"{self.quantity} x {self.product.name} - {self.status}"