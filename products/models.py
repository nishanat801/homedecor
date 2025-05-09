from django.db import models
from category.models import Category
from Authentication.models import CustomUser

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    available_colors = models.JSONField(default=list, blank=True, null=True)
    image1 = models.ImageField(upload_to='products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute_type = models.CharField(max_length=50, choices=[('color', 'Color'), ('material', 'Material'), ('size', 'Size')])
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.product.name} - {self.attribute_type}: {self.value}"
    

