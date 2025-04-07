from django.db import models
from products.models import Product
from Authentication.models import CustomUser

class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  #
    rating = models.PositiveIntegerField()  # Rating from 1 to 5
    review_text = models.TextField()  # Review content
    created_at = models.DateTimeField(auto_now_add=True)  # Date the review was created

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

# Create your models here.
