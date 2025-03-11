from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order,OrderItem
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from cart.models import Cart
from address.models import Address
from coupons.models import Coupon, UserProfile
from datetime import datetime
from coupons.models import Coupon,CouponUsage
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from payments.models import Wallet



def checkout_page(request):
    selected_address_id = request.session.get("selected_address_id")
    selected_address = get_object_or_404(Address, id=selected_address_id) if selected_address_id else None

    cart_items = Cart.objects.filter(user=request.user)
    subtotal = sum(item.total_amount for item in cart_items)

    # ✅ Get available coupons for the user (excluding used ones)
    available_coupons = Coupon.objects.filter(
        is_active=True,
        expiry_date__gte=timezone.now().date(),
        # min_amount__lte=subtotal
    ).exclude(id__in=CouponUsage.objects.filter(user=request.user).values_list("coupon_id", flat=True))

    print("Available Coupons:", available_coupons)

    discount_amount = 0
    final_total = subtotal
    applied_coupon = None

    # ✅ Check if a coupon is already applied in session
    applied_coupon_code = request.session.get("applied_coupon_code")
    if applied_coupon_code:
        applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()

        if applied_coupon and subtotal >= applied_coupon.min_amount:
            discount_amount = min((subtotal * applied_coupon.discount_percentage) / 100, applied_coupon.max_discount)
            final_total = subtotal - discount_amount
        else:
            # ✅ If coupon is no longer valid, remove it from session
            request.session.pop("applied_coupon_code", None)

    return render(request, "user/checkout.html", {
        "selected_address": selected_address,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "available_coupons": available_coupons,
        "applied_coupon": applied_coupon,
        "discount_amount": discount_amount,
        "total": final_total,
    })

def generate_tracking_number():
    return str(uuid.uuid4().hex[:10]).upper()


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "user/order_success.html", {"order": order})

ORDER_LIMIT = 5  # Maximum number of items per order

def place_order(request):
    if request.method == "POST":
        user = request.user
        selected_address_id = request.session.get("selected_address_id")

        if not selected_address_id:
            messages.error(request, "No address selected. Please select an address.")
            return redirect("orders:checkout_page")

        selected_address = get_object_or_404(Address, id=selected_address_id)

        # Fetch cart items
        cart_items = Cart.objects.filter(user=user)
        total_items = sum(item.quantity for item in cart_items)

        if total_items == 0:
            messages.error(request, "Your cart is empty.")
            return redirect("cart")

        if total_items > ORDER_LIMIT:
            messages.error(request, f"You can only order up to {ORDER_LIMIT} items.")
            return redirect("orders:checkout_page")
         # Check if a coupon is applied
        coupon = Coupon.objects.filter(is_active=True,expiry_date__gte=timezone.now().date()).exclude(couponusage__user=user).first()
        # coupon = Coupon.objects.filter(is_active=True, is_used=False).first()
        discount_percentage = coupon.discount_percentage if coupon else 0

        # Initialize a flag to check stock availability
        out_of_stock = False

        # Check stock availability for each cart item
        for item in cart_items:
            product = item.product
            if product.stock < item.quantity:
                messages.error(request, f"Not enough stock for {product.name}. Available stock is {product.stock}.")
                out_of_stock = True
                break
        
        # If any item is out of stock, redirect to cart
        if out_of_stock:
            return redirect("cart")


        # Create order
        order = Order.objects.create(
            user=user,
            address=selected_address,
            full_name=selected_address.full_name,
            coupon=coupon if coupon else None,
        )

        # Create OrderItems for each cart item
        for item in cart_items:
            original_price = item.product.price
            total_price = original_price * item.quantity
            discount_amount = (total_price * discount_percentage) / 100 if coupon else 0
            final_amount = total_price - discount_amount

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=original_price,  # Save the price at the time of order
                discount_amount=discount_amount,
                final_amount=final_amount,
            )

            # Reduce the stock of the product
            item.product.stock -= item.quantity
            item.product.save()

        # Mark coupon as used if applied
        if coupon:
            coupon.is_used = True
            coupon.save()

        # Clear cart after order is placed
        cart_items.delete()
        del request.session["selected_address_id"]  # Remove selected address from session

        messages.success(request, "Order placed successfully!")
        return redirect("orders:order_success", order_id=order.id)

    return redirect("orders:checkout_page")



def user_order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')  # Latest first

    context = {
        'orders': []
    }

    for order in orders:
        total_price = sum(item.price * item.quantity for item in order.items.all())
        discount_amount = 0

        # Get applied coupon from the first item in the order (assuming one coupon per order)
        order_items = OrderItem.objects.filter(order=order)
        applied_coupon = order_items.first().coupon if order_items.exists() and hasattr(order_items.first(), 'coupon') else None

        if applied_coupon:
            discount_amount = (total_price * applied_coupon.discount_percentage) / 100
            discount_amount = min(discount_amount, applied_coupon.max_discount)  # Ensure discount doesn't exceed max limit

        final_amount = total_price - discount_amount  # ✅ Final total after discount

        order_data = {
            'id': order.id,
            'order_number': order.tracking_number,
            'order_date': order.created_at.strftime("%Y-%m-%d"),
            'status': order.status,
            'total_price': total_price,
            'discount_amount': discount_amount,  # ✅ Ensure discount is sent to template
            'final_amount': final_amount,  # ✅ Send final amount after discount
            'estimated_delivery': "5-7 business days",
            'address': {
                'full_name': order.full_name,
                'address_line_1': order.address.address if order.address else 'N/A',
                'city': order.address.city if order.address else 'N/A',
            },
            'items': []
        }

        for item in order.items.all():
            print(f"Item ID: {item.id}, Name: {item.product.name}, Status: {item.status}")  # Debugging print

            order_data['items'].append({
                'id': item.id,  # Ensure this exists
                'product_name': item.product.name,
                'product_image': item.product.image1.url if item.product.image1 else '',
                'price': item.price,
                'quantity': item.quantity,
                'status': item.status, 
                
            })

        context['orders'].append(order_data)

    return render(request, 'user/orders_list.html', context)





@login_required
def cancel_order(request, item_id):
    if request.method == "POST":
        try:
            order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
            
            if order_item.status == "Delivered":
                return JsonResponse({"success": False, "error": "Delivered items cannot be canceled."}, status=400)

            order_item.status = "Cancelled"
            order_item.save()

            # Restock the product when the order is canceled
            order_item.product.stock += order_item.quantity
            order_item.product.save()

            return JsonResponse({
                "success": True,
                "message": "Order item has been cancelled, and stock has been updated.",
                "item_id": order_item.id
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)

def reorder_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)

    # Ensure the product exists
    if not item.product:
        messages.error(request, "Product not found.")
        return redirect("orders:user_order_list")

    # Check if the user already has this product in the cart
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=item.product,
        defaults={"quantity": item.quantity}
    )

    # If the product is already in the cart, just update the quantity
    if not created:
        cart_item.quantity += item.quantity
        cart_item.save()

    messages.success(request, f"{item.product.name} added to your cart.")

    return redirect("cart") 

def return_product(request, item_id):
    try:
        # Find the order item by its ID
        item = OrderItem.objects.get(id=item_id)

        # Check if the item is eligible for return (status = "Delivered")
        if item.status != "Delivered":
            return JsonResponse({"error": "Only delivered items can be returned."}, status=400)

        # Update the status to "Requested for Return"
        item.status = "Requested for Return"
        item.save()

        item.status = "Returned"
        item.save()

        # Increase stock when the item is returned
        item.product.stock += item.quantity
        item.product.save()

        # Credit the wallet with the item's price
        wallet, created = Wallet.objects.get_or_create(user=item.order.user)
        wallet.credit(item.price)

        return JsonResponse({"success": True, "message": "Return request processed, stock updated, and amount credited to wallet."})

    except OrderItem.DoesNotExist:
        return JsonResponse({"error": "Item not found."}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




def admin_orders(request):
    orders = Order.objects.select_related("user", "address").prefetch_related("items__product").order_by("-created_at")

    orders_data = []
    for order in orders:
        total_price = sum(item.price * item.quantity for item in order.items.all())
        address = f"{order.address.address}, {order.address.city}" if order.address else "N/A"

        orders_data.append({
            'id': order.id,
            'tracking_number': order.tracking_number,
            'user': order.user.username,
            'total_price': total_price,
            'created_at': order.created_at,
            'status': order.status,
            'shipping_address': address,
        })

    context = {
        'orders': orders_data,
    }
    return render(request, 'admin/admin_order.html', context)


def admin_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Calculate total price for the order
    total_price = sum(item.price * item.quantity for item in order_items)

    # Shipping address (ensure you access it correctly based on your model)
    shipping_address = f"{order.address.city}" if order.address else "N/A"

    if request.method == "POST":
        item_id = request.POST.get('item_id')  # OrderItem ID
        new_status = request.POST.get('new_status')

        if item_id and new_status:
            try:
                order_item = OrderItem.objects.get(id=item_id, order=order)
                order_item.status = new_status
                order_item.save()
                messages.success(request, f"Order item #{order_item.id} status updated to {new_status}")
            except OrderItem.DoesNotExist:
                messages.error(request, "Order item not found")

        return redirect(request.path)  # Refresh the page after updating

    context = {
        'order': order,
        'order_items': order_items,
        'total_price': total_price,
        'shipping_address': shipping_address,
    }
    return render(request, 'admin/order_details.html', context)

  


