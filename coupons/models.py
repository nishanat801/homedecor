from django.db import models
from Authentication.models import CustomUser
from datetime import date

class Coupon(models.Model):
    COUPON_TYPES = [
        ("welcome", "Welcome Coupon"),
        ("conditional", "Conditional Coupon"),
    ]
    # users = models.ManyToManyField(CustomUser,related_name="available_coupons", blank=True)
    name = models.CharField(max_length=255, default="firstbuy")
    code = models.CharField(max_length=50, unique=True)  # Make unique to prevent duplicate codes
    expiry_date = models.DateField()
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPES)  # Only one coupon_type field
    discount_percentage = models.IntegerField(null=True, blank=True,default=0.00)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Threshold for conditional coupons
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
   

    def is_valid(self, user, total_amount):
        """Checks if the coupon is valid for the user and cart total."""
        if self.expiry_date < date.today():
            return False, "Coupon has expired."
        
        if self.coupon_type == "welcome":
            if not user.userprofile.first_purchase:
                return False, "Welcome coupon is only for first-time buyers."
        
        if self.coupon_type == "conditional" and total_amount < self.min_amount:
            return False, f"Minimum purchase of ₹{self.min_amount} required."

        return True, "Coupon is valid."
    
    def apply_discount(self, total_amount):
        discount_amount = (self.discount_percentage / 100) * total_amount
        return min(discount_amount, self.max_discount)  # Ensure max discount is applied

    # def use_coupon(self):
    #     """Mark the coupon as used (only for one-time use coupons)."""
    #     self.is_used = True
    #     self.is_active = False
    #     self.save()

    # def __str__(self):
    #     return f"{self.code} ({'Used' if self.is_used else 'Active'})"
    

class CouponUsage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("user", "coupon")  # Prevent duplicate usage records

    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_purchase = models.BooleanField(default=False)  # Tracks if the user made their first purchase
    first_purchase_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"