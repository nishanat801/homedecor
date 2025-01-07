from django.shortcuts import render
from django.shortcuts import render, redirect


def home_view(request):
    return render(request, 'user/home.html')
def user_login_view(request):
    return render(request,'user/login.html')
def admin_home_view(request):
    return render(request,'admin/admin_home.html')
def admin_login_view(request):
    return render(request,'admin/admin_login.html')




