# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from Authentication.models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
