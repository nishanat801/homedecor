import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from .models import OTPVerification, CustomUser,ForgotPasswordOTPVerification
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings
from django.views.decorators.cache import never_cache
import datetime
import re
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.views import product_list
from home.views import home_view
import random
from django.utils import timezone
from datetime import timedelta
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

# def signup_view(request):
#     if request.user.is_authenticated:
#         return redirect('Authentication:login_user')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('Authentication:login_user')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                otp = generate_otp()
                print("Generated OTP:", otp)

                # Create user but don't activate until OTP verification
                user = form.save(commit=False)
                user.is_active = False
                user.otp = otp
                user.otp_expiry = now() + datetime.timedelta(minutes=5)
                user.save()
                print("User saved:", user.email)

                # Store email in session
                request.session['email'] = user.email
                request.session.save()
                print("Session saved with email:", user.email)

                # Send OTP via email
                if send_otp_email(user.email, otp):
                    print("OTP sent successfully.")
                    return redirect('Authentication:otp_verify')
                else:
                    messages.error(request, "Failed to send OTP. Please try again.")
                    return redirect('Authentication:signup_user')

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return redirect('Authentication:signup_user')

        else:
            print("Form validation failed:", form.errors)
            messages.error(request, "Please correct the errors below.")
            return render(request, 'user/signup.html', {'form': form})

    form = CustomUserCreationForm()
    return render(request, 'user/signup.html', {'form': form})



# OTP Verification View
def otp_verify_view(request):
    email = request.session.get('email')  # Get email from session

    if not email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('Authentication:signup_user')

    if request.method == 'POST':
        otp = request.POST.get('otp')  # Get entered OTP

        print(f"Stored email from session: {email}")

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            messages.error(request, 'User not found. Please try again.')
            return redirect('Authentication:otp_verify')

        print(f"Stored OTP: {user.otp}, Entered OTP: {otp}")
        print(f"OTP Expiry: {user.otp_expiry}, Current Time: {timezone.now()}")

        if user.otp == otp and user.otp_expiry > timezone.now():
            user.is_active = True
            user.otp = None  # Clear OTP after verification
            user.otp_expiry = None
            user.save()

            # Clear session
            del request.session['email']

            messages.success(request, 'Account verified successfully.')
            return redirect('Authentication:login_user')
        else:
            messages.error(request, 'Invalid or expired OTP.')
            return redirect('Authentication:otp_verify')

    return render(request, 'user/otp_verify.html')

@never_cache
def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')  # Correct redirect without namespace

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
                return redirect('home')  # Correct redirect without namespace
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
        return redirect('Authentication:login_user')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not CustomUser.objects.filter(email=email).exists():
            return render(request, 'user/forgot_password.html', {
                'error': 'Email does not exist.'
            })
        
        otp = generate_otp()  # Ensure this generates a valid OTP
        otp_expiry = timezone.now() + timedelta(minutes=5)
        
        # Save OTP to the database
        otp_entry, created = ForgotPasswordOTPVerification.objects.update_or_create(
            email=email,
            defaults={
                'otp': otp,
                'expires_at': otp_expiry
            }
        )
        
        if send_otp_email(email, otp):
            request.session['email'] = email
            return redirect('Authentication:forgot_password_otp_verify')
        else:
            return render(request, 'user/forgot_password.html', {
                'error': 'Failed to send OTP. Please try again.'
            })
    
    return render(request, 'user/forgot_password.html')

# forgot-password-otp-verify
def forgot_password_otp_verify(request):
    email = request.session.get('email')
    if not email:
        return redirect('Authentication:forgot_password')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        
        try:
            otp_record = ForgotPasswordOTPVerification.objects.get(email=email)
        except ForgotPasswordOTPVerification.DoesNotExist:
            return render(request, 'user/forgot_password_otp_verify.html', 
                          {'error': 'OTP not found.'})
        
        if timezone.now() > otp_record.expires_at:
            return render(request, 'user/forgot_password_otp_verify.html', 
                          {'error': 'OTP expired.'})
        
        if str(otp_record.otp) != entered_otp:
            return render(request, 'user/forgot_password_otp_verify.html', 
                          {'error': 'Invalid OTP.'})
        
        return redirect('Authentication:reset_password')
    
    return render(request, 'user/forgot_password_otp_verify.html')



# Reset Password View
def reset_password(request):
    email = request.session.get('email')

    if not email:
        return redirect('Authentication:forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')

        if new_password != confirm_password:
            return render(request, 'user/reset_password.html', {
                'error': 'Passwords do not match.'
            })

        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Clean session and redirect
        request.session.flush()
        messages.success(request, 'Password reset successful. Please log in.')
        return redirect('Authentication:login_user')

    return render(request, 'user/reset_password.html')
#username:homedecor
#email:homedecoradmin@gmail.com
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

