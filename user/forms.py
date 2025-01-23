from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address']

    # Additional fields (not in the model) can be added manually
    payment_method = forms.ChoiceField(choices=[
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery')
    ], required=True)

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['shipping_address'].widget.attrs.update({
            'placeholder': 'Enter your shipping address',
            'class': 'form-control'
        })