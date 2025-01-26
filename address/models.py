from django.db import models
from Authentication.models import CustomUser


class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    pincode = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=15, blank=False, null=False, default='0000000000')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    address = models.TextField()
    area = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    is_saved = models.BooleanField(default=True)
    address_type = models.CharField(max_length=50, choices=[('Home', 'Home'), ('Office', 'Office')])

    def __str__(self):
        return f"{self.full_name} - {self.address_type}"
