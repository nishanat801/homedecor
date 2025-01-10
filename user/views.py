from django.shortcuts import render, get_object_or_404, redirect
from Authentication.models import CustomUser

def user_profile_list(request):
    users = CustomUser.objects.all()  # Retrieve all users
    return render(request, 'admin/user_management.html', {'users': users})


def block_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False  # Block the user
    user.save()
    return redirect('user:user_profile_list')

def unblock_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True  # Unblock the user
    user.save()
    return redirect('user:user_profile_list')

