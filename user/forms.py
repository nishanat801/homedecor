# from django import forms
# from .models import Order

# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = ['total_price', 'shipping_address']
        
#     def clean(self):
#         cleaned_data = super().clean()
#         total_price = cleaned_data.get('total_price')
#         shipping_address = cleaned_data.get('shipping_address')
        
#         if not total_price or total_price <= 0:
#             raise forms.ValidationError("Invalid total price")
        
#         if not shipping_address:
#             raise forms.ValidationError("Shipping address is required")
        
#         return cleaned_data