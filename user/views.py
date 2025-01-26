from django.shortcuts import render, get_object_or_404, redirect
from Authentication.models import CustomUser
from cart.models import Cart
from products.models import Product
from .models import UserDetails,OrderItem,Order
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import  timedelta
from django.db import IntegrityError
from django.http import JsonResponse
import logging
from django.db import transaction
import time
from django.contrib.auth import get_user_model
from .forms import OrderForm
from django.contrib.auth.models import User
import uuid
from django.core.paginator import Paginator
from django.db.models import Q
from address.models import Address
from decimal import Decimal
from django.db import transaction




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

@login_required
def user_details(request):
    try:
        user_details = UserDetails.objects.get(user=request.user)
    except UserDetails.DoesNotExist:
        user_details = None

    if request.method == 'POST':
        # Get phone and email from POST data
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        # Check if phone and email are provided
        if not phone or not email:
            messages.error(request, "Both phone and email are required.")
            return render(request, 'user/user_details.html', {'user_details': user_details})

        if user_details:
            # Update existing user details
            user_details.phone = phone
            user_details.email = email
        else:
            # Create new user details
            user_details = UserDetails(user=request.user, phone=phone, email=email)

        user_details.save()  # Save the object to the database
        messages.success(request, "Details saved successfully!")
        
        return render(request, 'user/address.html')
    
    # Fetch cart items for the logged-in user
    cart_items = Cart.objects.filter(user=request.user)

    # Calculate order summary
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    savings = sum(item.product.discount * item.quantity for item in cart_items if item.product.discount)
    tax = round(0.18 * subtotal, 2)  # Assuming 18% tax
    estimated_total = subtotal - savings + tax
    
    print("Subtotal:", subtotal)
    print("Savings:", savings)
    print("Tax:", tax)
    print("Estimated Total:", estimated_total)

    #Pass all values to the template
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'savings': savings,
        'tax': tax,
        'estimated_total': estimated_total,
        'user_details': user_details,
    }

    return render(request, 'user/user_details.html', context)

@login_required
def save_address(request):
    if request.method == 'POST':
        # Collect data from the form
        full_name = request.POST.get('full-name')
        pincode = request.POST.get('pincode')
        city = request.POST.get('city')
        state = request.POST.get('state')
        address = request.POST.get('address')
        area = request.POST.get('area', '')  # Default to an empty string if not provided
        landmark = request.POST.get('landmark', '')
        address_type = request.POST.get('address-type', 'Home')

        # Collect phone and email from the form or fallback to user's email
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', request.user.email)

        # Calculate estimated delivery
        estimated_delivery = now().date() + timedelta(days=7)

        try:
            # Check if the UserDetails entry exists
            user_details, created = UserDetails.objects.update_or_create(
                user=request.user,
                defaults={
                    "full_name": full_name,
                    "phone": phone,
                    "email": email,
                    "pincode": pincode,
                    "city": city,
                    "state": state,
                    "address_line_1": address,
                    "address_line_2": area,
                    "landmark": landmark,
                    "address_type": address_type,
                    "date_of_order": now().date(),
                    "estimated_delivery": estimated_delivery,
                    
                },
            )
            if created:
                messages.success(request, "Address saved successfully!")
            else:
                messages.success(request, "Address updated successfully!")

        except IntegrityError as e:
            messages.error(request, "There was an issue saving your address. Please try again.")
            return render(request, 'user/address.html')

        return redirect('user:checkout')  # Redirect to the payment page

    # Render the address form page for GET requests
    return render(request, 'user/address.html')


# @login_required
# def payment(request):
#     try:
#         # Fetch the user's address details
#         user_details = UserDetails.objects.get(user=request.user)
#     except UserDetails.DoesNotExist:
#         messages.error(request, "Please save your address before proceeding to payment.")
#         return redirect('user:user_address')

#     # Fetch cart items for the logged-in user
#     cart_items = Cart.objects.filter(user=request.user)

#     # Calculate order summary
#     subtotal = sum(item.product.price * item.quantity for item in cart_items)
#     savings = -211
#     tax = 73
#     estimated_total = subtotal - savings + tax

#     shipping_address = f"{user_details.address_line_1}, {user_details.address_line_2}, {user_details.city}, {user_details.state}, {user_details.pincode}"

#     context = {
#         'user_details': user_details,
#         'cart_items': cart_items,
#         'subtotal': subtotal,
#         'savings': savings,
#         'tax': tax,
#         'estimated_total': estimated_total,
#         'shipping_address': shipping_address,
#         'estimated_delivery_date': user_details.estimated_delivery,
#     }
#     return render(request, 'user/payment.html', context)


@login_required
def place_order(request):
    estimated_delivery = now().date() + timedelta(days=7)
    product = Product.objects.first()  # Replace with the actual product logic
    return render(request, 'user/placeorder.html', {
        'estimated_delivery': estimated_delivery,
        'product': product,
    })

@login_required
def my_account(request):
    return render(request,'user/myaccount.html')

def generate_tracking_number():
    return str(uuid.uuid4().hex[:10]).upper()



def select_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        
        if address_id:
            request.session['selected_address_id'] = address_id
            print("Selected address ID:", request.session.get('selected_address_id'))
            messages.success(request, "Address selected successfully!")
            return redirect('user:checkout')

        messages.error(request, "Please select a valid address.")
        return redirect('user:personal_info')

    return redirect('user:personal_info')


@login_required
@login_required
def checkout(request):
    selected_address = None
    address_id = request.session.get('selected_address_id')

    if address_id:
        selected_address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = form.save(commit=False)
                order.user = request.user
                order.shipping_address = selected_address.address if selected_address else "No address provided"
                order.total_price = Decimal(request.POST.get('total_price', 0))  # Ensure total price is saved
                order.tracking_number = generate_tracking_number()
                order.save()

                cart_items = Cart.objects.filter(user=request.user)

                # Save order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )

                # Clear the cart
                cart_items.delete()

                messages.success(request, "Your order has been placed successfully!")
                return redirect('user:order_success')

            except Exception as e:
                messages.error(request, f"Error placing order: {e}")
                return redirect('user:checkout')
        else:
            print("Form errors:", form.errors)

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('user:cart')

    subtotal = sum(Decimal(item.product.price) * Decimal(item.quantity) for item in cart_items)
    savings = Decimal('110')
    tax = round(subtotal * Decimal('0.18'), 2)
    estimated_total = subtotal - savings + tax

    initial_data = {
        'shipping_address': selected_address.address if selected_address else '',
        'total_price': estimated_total
    }
    form = OrderForm(initial=initial_data)

    context = {
        'form': form,
        'selected_address': selected_address,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'savings': savings,
        'tax': tax,
        'estimated_total': estimated_total,
    }
    return render(request, 'user/checkout.html', context)



@login_required
def order_success(request):
    return render(request, 'user/order_success.html')


def admin_orders(request):
  
    orders = Order.objects.all()  # Fetching orders from the database
    print(orders)
    context = {
        'orders': orders,  # Sending orders to the template
    }
    return render(request, 'admin/admin_order.html', context)

def admin_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    print(f"Order {order.id} - {order.user.username}")
    print(f"Order Items: {order_items}")  # Should show items if they exist

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'admin/order_details.html', context)


@login_required
def user_order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')

    context = {
        'orders': [
            {
                'order_number': order.tracking_number,
                'order_date': order.created_at.strftime("%Y-%m-%d"),
                'status': order.status,
                'total_price': order.total_price,
                'estimated_delivery': "5-7 business days",
                'address': {
                    'full_name': order.user.get_full_name(),
                    'address_line_1': order.shipping_address,
                    'city': 'City Placeholder',
                },
                'items': [
                    {
                        'product_name': item.product.name,
                        'product_images': [
                            item.product.image1.url if item.product.image1 else '',
                            item.product.image2.url if item.product.image2 else '',
                            item.product.image3.url if item.product.image3 else ''
                        ],
                        'price': item.price,
                        'quantity': item.quantity,
                        'date_of_delivery': "TBD"
                    } for item in order.items.all()
                ]
            } for order in orders
        ]
    }
    return render(request, 'user/orders_list.html', context)





















   