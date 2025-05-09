from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'review_text']  

    rating = forms.ChoiceField(choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect)  
