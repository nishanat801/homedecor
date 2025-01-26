from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'pincode','phone_number', 'city', 'state', 'address', 'area', 'landmark', 'address_type']