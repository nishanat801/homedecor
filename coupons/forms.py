
from django import forms
from .models import Coupon

# class CouponForm(forms.Form):
#     coupon_code = forms.CharField(label="Coupon Code", max_length=50)

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["name", "code", "expiry_date", "coupon_type", "discount_percentage", "min_amount", "max_discount", "is_active"]