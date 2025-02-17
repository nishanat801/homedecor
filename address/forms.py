from django import forms
from .models import Address
import re

class AddressForm(forms.ModelForm):
    is_default = forms.BooleanField(required=False, label="Make Default Address") 

    class Meta:
        model = Address
        fields = ['full_name', 'phone_number', 'pincode', 'address', 'city', 'state', 'address_type','is_default']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'required': 'required'
            })
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not re.match(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError("Invalid phone number")
        return phone
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not re.match(r'^\d{6}$', pincode):
            raise forms.ValidationError("Invalid pincode")
        return pincode