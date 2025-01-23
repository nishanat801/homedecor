from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import datetime


class CustomUser(AbstractUser):
    # address = models.TextField(blank=True, null=True)
    # phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)  # Field for storing OTP
    otp_expiry = models.DateTimeField(null=True, blank=True)  # Field for storing OTP

    # Add related_name to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Custom related name for groups
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',  # Custom related name for user_permissions
        blank=True
    )

    def __str__(self):
        return self.username
    
class OTPVerification(models.Model):
    email = models.EmailField(unique=True)  # Email to which the OTP is sent
    otp = models.IntegerField()  # The OTP itself
    created_at = models.DateTimeField(auto_now_add=True)  # To track when OTP was created
    expires_at = models.DateTimeField()
    
    

    def is_valid(self):
        return self.expires_at > datetime.datetime.now(datetime.timezone.utc)

    def __str__(self):
        return f"OTP for {self.email} - {self.otp}"
    

class ForgotPasswordOTPVerification(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at