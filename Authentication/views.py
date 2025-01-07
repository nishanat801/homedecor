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
                user.is_active = False 
                user.otp = otp
                user.otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
                user.save()

                return redirect('Authentication:otp_verify')
                # Save OTP in the database
                #OTPVerification.objects.create(email=form.cleaned_data['email'], otp=otp, expires_at=otp_expiry)

                # Send OTP email
                # if send_otp_email(form.cleaned_data['email'], otp):
                #     request.session['email'] = form.cleaned_data['email']
                #     request.session['username'] = form.cleaned_data['username']
                #     request.session['password'] = form.cleaned_data['password1']

                #     messages.success(request, 'Account created successfully. Please check your email for the OTP.')
                #     print(otp)
                #     return redirect('otp_verify')

                # else:
                #     user.delete()  
                #     messages.error(request, 'Failed to send OTP. Please try again later.')
                #     return redirect('Authentication:signup_user') 

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
    if request.user.is_authenticated:
        return redirect('Authentication:login_user') 

    context = {}

    if request.method == 'POST':
        email = request.session.get('email')
        entered_otp = request.POST.get('otp')

        if not email:
            context['error'] = 'Session expired. Please try signing up again.'
            return render(request, 'user/otp_verify.html', context)

        try:
            # Validate OTP
            otp_entry = OTPVerification.objects.filter(email=email, otp=entered_otp).first()
            if not otp_entry:
                context['error'] = 'Invalid OTP.'
                return render(request, 'user/otp_verify.html', context)

            if not otp_entry.is_valid():
                context['error'] = 'OTP has expired.'
                return render(request, 'user/otp_verify.html', context)

            # Create user and log in
            user = CustomUser.objects.create_user(
                username=request.session['username'],
                email=email,
                password=request.session['password']
            )
            login(request, user)

            # Clean up session and OTP record
            request.session.flush()
            otp_entry.delete()

            # Redirect to the login page after successful OTP verification
            return redirect('login_user')  # Adjust the URL name if needed

        except Exception as e:
            context['error'] = f'An error occurred: {e}'
            return render(request, 'user/otp_verify.html', context)

    return render(request, 'user/otp_verify.html', context)


#login_view
@never_cache
def login_user(request):
    if request.user.is_authenticated:
        return redirect('Authentication:home_user')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        errors = {}

        if not email:
            errors['email'] = 'Email is required.'
        else:
            email = email.strip()

        if not password:
            errors['password'] = 'Password is required.'
        else:
            password = password.strip()

        if errors:
            for field, error_message in errors.items():
                messages.error(request, error_message)
            return render(request, 'user/login.html')

        # Validate email format using a regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            messages.error(request, 'Invalid email format.')
            return render(request, 'user/login.html')

        # Validate password length
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'user/login.html')

        try:
            # Check if the user exists
            user = CustomUser.objects.get(email=email)

            # Check if the account is active
            if not user.is_active:
                messages.error(request, 'Your account is blocked.')
                return render(request, 'user/login.html')

            authenticated_user = authenticate(request, username=user.username, password=password)

            if authenticated_user is not None:
                login(request, authenticated_user)

                return redirect('Authentication:home_user')

            else:
                messages.error(request, 'Invalid password')
                return render(request, 'user/login.html')

        except CustomUser.DoesNotExist:
            messages.error(request, 'User does not exist')
            return render(request, 'user/login.html')

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

