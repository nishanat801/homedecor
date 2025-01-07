from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import CustomUser

# View to display a user's profile
@login_required
def user_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'user_profile.html', {'user': user})

# View to block a user
@login_required
def block_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False  # Block the user
    user.save()
    return redirect('user_profile', user_id=user.id)

# View to unblock a user
@login_required
def unblock_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True  # Unblock the user
    user.save()
    return redirect('user_profile', user_id=user.id)
