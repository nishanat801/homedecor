from django.shortcuts import render, get_object_or_404, redirect
from Authentication.models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib.auth import get_user_model
# from .forms import OrderForm
from django.contrib.auth.models import User
from .models import UserInfo
from django.contrib.auth import update_session_auth_hash
from payments.models import Wallet




@login_required
def user_profile_list(request):
    users = CustomUser.objects.all()  # Retrieve all users
    return render(request, 'admin/user_management.html', {'users': users})

@login_required
def block_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False  # Block the user
    user.save()
    return redirect('user:user_profile_list')
@login_required
def unblock_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True  # Unblock the user
    user.save()
    return redirect('user:user_profile_list')

@login_required
def my_account(request):
    return render(request,'user/myaccount.html')



@login_required
def edit_profile(request):          
    user_info, created = UserInfo.objects.get_or_create(user=request.user)  # Get or create UserInfo

    # Fetch wallet balance
    wallet_balance = Wallet.objects.filter(user=request.user).first().balance if Wallet.objects.filter(user=request.user).exists() else 0.00

    if request.method == "POST":
        # Update User fields
        user = request.user
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.save()

        # Update UserInfo fields
        user_info.phone_number = request.POST.get("phone_number")
        user_info.gender = request.POST.get("gender")
        user_info.date_of_birth = request.POST.get("date_of_birth")

        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user_info.profile_picture = request.FILES["profile_picture"]

        user_info.save()

        messages.success(request, "Your profile has been updated successfully.")
        return redirect("user:edit_profile")

    return render(request, "user/personal_info.html", {
        "user_info": user_info,
        "wallet_balance": wallet_balance,
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('currentPassword')
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')

        # Validate password match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, 'user/personal_info.html')

        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'user/personal_info.html')

        # Ensure the user has a valid username before saving
        user = request.user
        if not user.username or user.username.strip() == "":
            user.username = user.email  # Use email as username if missing

        # Update the password and save the user
        user.set_password(new_password)
        user.save(update_fields=['password', 'username'])

        # Update session to keep the user logged in
        update_session_auth_hash(request, request.user)

        messages.success(request, "Your password has been changed successfully.")
        return redirect('user:edit_profile')  # Redirect to profile after update

    return render(request, "user/personal_info.html")

















   