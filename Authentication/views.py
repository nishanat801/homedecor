import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .models import OTPVerification, CustomUser
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings
from django.urls import reverse
from django.views.decorators.cache import never_cache
import datetime
import re
from django.http import JsonResponse
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.views import product_list
import random
from django.utils import timezone
logger = logging.getLogger(__name__)



User = get_user_model()
# Generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))
#send mail
def send_otp_email(to_email, otp):
    subject = 'Your OTP for Registration'
    message = f'Your OTP is {otp}. It will expire in 5 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL
    logger.info(f"Sending OTP email to {to_email} with OTP: {otp}")

    try:
        send_mail(subject, message, from_email, [to_email])
        logger.info(f"OTP email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        return False

def is_valid(self):
    return self.expires_at > timezone.now()

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('Authentication:login_user')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid():
            try:
                # Generate OTP
                otp = generate_otp()
                print(otp)
                # Create user
                user = form.save(commit=False)
                user.is_active = True 
                user.otp = otp
                user.otp_expiry = now() + datetime.timedelta(minutes=5)
                user.save()

                return redirect('Authentication:otp_verify')
                
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again later.')
        
                return redirect('Authentication:signup_user')

        else:
            # Form validation errors
            return render(request, 'user/signup.html', {'form': form})


    form = CustomUserCreationForm() 
    return render(request, 'user/signup.html', {'form': form})



# OTP Verification View
def otp_verify_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # Retrieve email from form
        otp = request.POST.get('otp')      # Retrieve entered OTP

        print(f"Submitted email: {email}")

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            messages.error(request, 'User not found. Please check the email.')
            return redirect('Authentication:otp_verify')

        print(f"Stored OTP: {user.otp}, Entered OTP: {otp}")
        print(f"OTP Expiry: {user.otp_expiry}, Current Time: {timezone.now()}")

        if user.otp == otp and user.otp_expiry > timezone.now():
            user.is_active = True
            user.otp = None  # Clear OTP after successful verification
            user.save()
            messages.success(request, 'Account verified successfully.')
            return redirect('Authentication:login_user')
        else:
            messages.error(request, 'Invalid or expired OTP.')
            return redirect('Authentication:otp_verify')

    return render(request, 'user/otp_verify.html')


@never_cache
def login_user(request):
    if request.user.is_authenticated:
        return redirect('Authentication:home_user')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validation
        errors = {}

        if not username:
            errors['username'] = 'Username is required.'
        else:
            username = username.strip()

        if not password:
            errors['password'] = 'Password is required.'
        else:
            password = password.strip()

        if errors:
            for field, error_message in errors.items():
                messages.error(request, error_message)
            return render(request, 'user/login.html')

        # Validate username format (optional)
        username_pattern = r"^[a-zA-Z0-9_]+$"  # Alphanumeric and underscores only
        if not re.match(username_pattern, username):
            messages.error(request, 'Invalid username format.')
            return render(request, 'user/login.html')

        # Validate password length
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'user/login.html')

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('products:product_list')
            else:
                messages.error(request, 'Your account is inactive. Please contact support.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'user/login.html')


# logout_view
@never_cache
def logout_user(request):
    request.session.flush()
    logout(request)
    return redirect('Authentication:login_user')

# Forgot Password View
def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('Authentication:home_user')

    if request.method == 'POST':
        email = request.POST.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email does not exist.'}, status=400)

        otp = generate_otp()
        otp_expiry = now() + datetime.timedelta(minutes=5)

        OTPVerification.objects.create(email=email, otp=otp, expires_at=otp_expiry)

        if send_otp_email(email, otp):
            request.session['email'] = email
            return JsonResponse({'status': 'success', 'redirect_url': reverse('Authentication:verify_otp')})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to send OTP. Please try again.'}, status=500)

    return render(request, 'user/forgot_password.html')


# Reset Password View
def reset_password(request):
    if request.method == 'POST':
        email = request.session.get('email')
        new_password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if new_password != confirm_password:
            return JsonResponse({'status': 'error', 'message': 'Passwords do not match.'}, status=400)

        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Clean up session
        request.session.flush()
        return JsonResponse({'status': 'success', 'redirect_url': reverse('Authentication:login_user')})

    return render(request, 'user/reset_password.html')

#username:admin
#email:admin@gmail.com
#password:homedecoradmin

# admin login
@never_cache
def admin_login(request):
    if request.user.is_authenticated:
        return redirect('products:product_list')
    
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            admin = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            admin = None
        
        if admin is not None:
            admin = authenticate(request, username=admin.username, password=password)

            if admin is not None and admin.is_superuser:
                login(request, admin)
                
                return redirect('products:product_list')
        
        error_message = "Invalid credentials or not a superuser."
        
        return render(request, 'admin/admin_login.html', {'error_message': error_message})

    return render(request, 'admin/admin_login.html')
from products.models import Product
@never_cache
def admin_logout(request):
    request.session.flush()
    logout(request)
    return redirect('Authentication:admin/admin_login')

