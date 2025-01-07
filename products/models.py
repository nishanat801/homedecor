from django.db import models
from category.models import Category

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    available_colors = models.JSONField(default=list)  # Store colors as a list of strings
    brand = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)  # For soft delete
    image1 = models.ImageField(upload_to="products/", blank=True, null=True)
    image2 = models.ImageField(upload_to="products/", blank=True, null=True)
    image3 = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name
