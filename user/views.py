from django.shortcuts import render, get_object_or_404, redirect
from Authentication.models import CustomUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib.auth import get_user_model
# from .forms import OrderForm
from django.contrib.auth.models import User





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
def my_account(request):
    return render(request,'user/myaccount.html')


# @login_required
# def user_details(request):
#     try:
#         user_details = UserDetails.objects.get(user=request.user)
#     except UserDetails.DoesNotExist:
#         user_details = None

#     if request.method == 'POST':
#         # Get phone and email from POST data
#         phone = request.POST.get('phone')
#         email = request.POST.get('email')

#         # Check if phone and email are provided
#         if not phone or not email:
#             messages.error(request, "Both phone and email are required.")
#             return render(request, 'user/user_details.html', {'user_details': user_details})

#         if user_details:
#             # Update existing user details
#             user_details.phone = phone
#             user_details.email = email
#         else:
#             # Create new user details
#             user_details = UserDetails(user=request.user, phone=phone, email=email)

#         user_details.save()  # Save the object to the database
#         messages.success(request, "Details saved successfully!")
        
#         return render(request, 'user/address.html')
    
#     # Fetch cart items for the logged-in user
#     cart_items = Cart.objects.filter(user=request.user)

#     # Calculate order summary
#     subtotal = sum(item.product.price * item.quantity for item in cart_items)
#     savings = sum(item.product.discount * item.quantity for item in cart_items if item.product.discount)
#     tax = round(0.18 * subtotal, 2)  # Assuming 18% tax
#     estimated_total = subtotal - savings + tax
    
#     print("Subtotal:", subtotal)
#     print("Savings:", savings)
#     print("Tax:", tax)
#     print("Estimated Total:", estimated_total)

#     #Pass all values to the template
#     context = {
#         'cart_items': cart_items,
#         'subtotal': subtotal,
#         'savings': savings,
#         'tax': tax,
#         'estimated_total': estimated_total,
#         'user_details': user_details,
#     }

#     return render(request, 'user/user_details.html', context)

# @login_required
# def save_address(request):
#     if request.method == 'POST':
#         # Collect data from the form
#         full_name = request.POST.get('full-name')
#         pincode = request.POST.get('pincode')
#         city = request.POST.get('city')
#         state = request.POST.get('state')
#         address = request.POST.get('address')
#         area = request.POST.get('area', '')  # Default to an empty string if not provided
#         landmark = request.POST.get('landmark', '')
#         address_type = request.POST.get('address-type', 'Home')

#         # Collect phone and email from the form or fallback to user's email
#         phone = request.POST.get('phone', '')
#         email = request.POST.get('email', request.user.email)

#         # Calculate estimated delivery
#         estimated_delivery = now().date() + timedelta(days=7)

#         try:
#             # Check if the UserDetails entry exists
#             user_details, created = UserDetails.objects.update_or_create(
#                 user=request.user,
#                 defaults={
#                     "full_name": full_name,
#                     "phone": phone,
#                     "email": email,
#                     "pincode": pincode,
#                     "city": city,
#                     "state": state,
#                     "address_line_1": address,
#                     "address_line_2": area,
#                     "landmark": landmark,
#                     "address_type": address_type,
#                     "date_of_order": now().date(),
#                     "estimated_delivery": estimated_delivery,
                    
#                 },
#             )
#             if created:
#                 messages.success(request, "Address saved successfully!")
#             else:
#                 messages.success(request, "Address updated successfully!")

#         except IntegrityError as e:
#             messages.error(request, "There was an issue saving your address. Please try again.")
#             return render(request, 'user/address.html')

#         return redirect('user:checkout')  # Redirect to the payment page

#     # Render the address form page for GET requests
#     return render(request, 'user/address.html')


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


# @login_required
# def place_order(request):
#     estimated_delivery = now().date() + timedelta(days=7)
#     product = Product.objects.first()  # Replace with the actual product logic
#     return render(request, 'user/placeorder.html', {
#         'estimated_delivery': estimated_delivery,
#         'product': product,
#     })





#





# @login_required
# def save_order(request):
#     if request.method == 'POST':
#         address_id = request.POST.get('address_id')
#         print(address_id)

#         # Ensure address is selected
#         if not address_id:
#             messages.error(request, "Please select a shipping address.")
#             return redirect('checkout')

#         # Get user's selected address
#         address = get_object_or_404(Address, id=address_id, user=request.user)

#         # Fetch cart items for the user
#         cart_items = Cart.objects.filter(cart__user=request.user)
#         if not cart_items.exists():
#             messages.error(request, "Your cart is empty.")
#             return redirect('cart')

#         # Calculate total price
#         total_price = sum(item.product.price * item.quantity for item in cart_items)

#         # Create order instance
#         order = Order.objects.create(
#             user=request.user,
#             total_price=total_price,
#             shipping_address=f"{address.full_name}, {address.address}, {address.city}, {address.state}, {address.pincode}, {address.phone_number}",
#             tracking_number=generate_tracking_number(),
#             status='pending'
#         )

#         # Create order items
#         for item in cart_items:
#             OrderItem.objects.create(
#                 order=order,
#                 product=item.product,
#                 quantity=item.quantity,
#                 price=item.product.price
#             )
#             # Reduce product stock
#             item.product.stock -= item.quantity
#             item.product.save()

#         # Clear user's cart after order is placed
#         cart_items.delete()

#         messages.success(request, "Your order has been placed successfully!")
#         return redirect('order_success')

#     # Handle if accessed via GET request
#     addresses = Address.objects.filter(user=request.user)
#     cart_items = Cart.objects.filter(cart__user=request.user)
#     return render(request, 'checkout.html', {'addresses': addresses, 'cart_items': cart_items})



















   