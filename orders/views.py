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
from payments.models import Wallet,Payment
from django.db import transaction
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import FileResponse
import os
from django.conf import settings
from decimal import Decimal
from django.core.paginator import Paginator


# @login_required(login_url='/login_user/')
@login_required
def checkout_page(request):
    selected_address_id = request.session.get("selected_address_id")
    selected_address = get_object_or_404(Address, id=selected_address_id) if selected_address_id else None

    cart_items = Cart.objects.filter(user=request.user)

     # ✅ Check if all items are in stock
    for item in cart_items:
        if item.product.stock < item.quantity:
            messages.error(request, f"Not enough stock for {item.product.name}. Please adjust your cart.")
            return redirect('cart:view_cart')

    subtotal = sum(item.total_amount for item in cart_items)

    # ✅ Get available coupons (excluding used ones)
    available_coupons = Coupon.objects.filter(
        is_active=True,
        expiry_date__gte=timezone.now().date(),
        min_amount__lte=subtotal  # Ensure subtotal meets minimum requirement
    ).exclude(id__in=CouponUsage.objects.filter(user=request.user).values_list("coupon_id", flat=True))
    # print("Available Coupons:", available_coupons)

    discount_amount = 0
    applied_coupon = None
    final_total = subtotal
    item_discounts = {}  # Store discount per item

    # ✅ Check if a coupon is already applied in session
    applied_coupon_code = request.session.get("applied_coupon_code")
    if applied_coupon_code:
        applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()

        if applied_coupon and subtotal >= applied_coupon.min_amount:
            total_discount = min((subtotal * applied_coupon.discount_percentage) / 100, applied_coupon.max_discount)

            # ✅ Distribute discount proportionally across cart items
            for item in cart_items:
                proportion = item.total_amount / subtotal
                item_discount = round(proportion * total_discount, 2)
                item_discounts[item.id] = item_discount  # Store discount per item

            discount_amount = total_discount
            final_total = subtotal - discount_amount
        else:
            # ✅ Remove invalid coupon from session
            request.session.pop("applied_coupon_code", None)

    return render(request, "user/checkout.html", {
        "selected_address": selected_address,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "available_coupons": available_coupons,
        "applied_coupon": applied_coupon,
        "discount_amount": discount_amount,
        "item_discounts": item_discounts,  # Send item-wise discounts
        "total": final_total,
    })
@login_required
def generate_tracking_number():
    return str(uuid.uuid4().hex[:10]).upper()

@login_required
def order_success(request, order_id):
    # Fetch the order and its related items
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    request.session.pop("latest_order_id", None)
    
    # Render the order success page with product details
    context = {
        'order': order,
        'order_items': order_items
    }

    # Ensure you return a valid HttpResponse by rendering a template
    return render(request, 'user/order_success.html', context)

ORDER_LIMIT = 5  # Maximum number of items per order

@login_required
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

        # ✅ Check if a coupon is applied
        applied_coupon_code = request.session.get("applied_coupon_code")
        applied_coupon = None
        if applied_coupon_code:
            applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()

        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        discount_per_item = {}

        # Calculate discount distribution
        total_discount = 0
        if applied_coupon and subtotal >= applied_coupon.min_amount:
            total_discount = min((subtotal * applied_coupon.discount_percentage) / 100, applied_coupon.max_discount)

            for item in cart_items:
                proportion = (item.product.price * item.quantity) / subtotal
                item_discount = round(proportion * total_discount, 2)
                discount_per_item[item.id] = item_discount

        # Check stock availability
        out_of_stock = False
        for item in cart_items:
            if item.product.stock < item.quantity:
                messages.error(request, f"Not enough stock for {item.product.name}. Available stock is {item.product.stock}.")
                out_of_stock = True
                break

        if out_of_stock:
            return redirect("cart")
        
        total_amount=subtotal - total_discount
         # ✅ Restrict COD for orders above 1000
        if total_amount > 1000:
            messages.error(request, "Cash on Delivery is not available for orders above ₹1000.")
            return redirect("orders:checkout_page")


        # ✅ Use transaction.atomic() to ensure the order is placed successfully
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                address=selected_address,
                full_name=selected_address.full_name,
                tracking_number=f"TRK{timezone.now().timestamp()}",
                subtotal=subtotal,  
                total_amount=subtotal - total_discount,  
                total_discount=total_discount,  
            )

            for item in cart_items:
                discount_amount = discount_per_item.get(item.id, 0)
                final_price = (item.product.price * item.quantity) - discount_amount

            

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                    subtotal=item.product.price * item.quantity,
                    discount_amount=discount_amount,
                    final_amount=final_price,
                    coupon=applied_coupon,
                )

                # Reduce stock of the product
                item.product.stock -= item.quantity
                item.product.save()

            # ✅ Save the CouponUsage after the order is placed
            if applied_coupon:
                CouponUsage.objects.create(
                    user=user,
                    coupon=applied_coupon,
                    final_total=order.total_amount,
                    discount_amount=total_discount
                )

            # ✅ Clear the applied coupon from the session after the order
            request.session.pop("applied_coupon_code", None)
            request.session.pop("latest_order_id", None)

            # ✅ Clear the cart
            cart_items.delete()
            del request.session["selected_address_id"]

        messages.success(request, "Order placed successfully!")
        return redirect("orders:order_success", order_id=order.id)

    return redirect("orders:checkout_page")




@login_required
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
            # print(f"Item ID: {item.id}, Name: {item.product.name}, Status: {item.status}")  # Debugging print

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
            # Fetch the order item
            order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
            order = order_item.order  # Get the associated order

            # Get the payment method
            payment_method = order.payment_method
            is_payment_completed = order.payment_status == "Completed"
            
            # # Order status should be 'Pending' or 'Shipped'
            # if order_item.status not in ["Pending", "Shipped"]:
            #     return JsonResponse({
            #         "success": False,
            #         "message": "Order cannot be cancelled at this stage.",
            #     })

            with transaction.atomic():
                if payment_method == "Cash on Delivery":
                    # Cash on Delivery logic: Cancel the item as usual
                    order_item.status = "Cancelled"
                    order_item.save()

                    # Increment the stock of the product
                    order_item.product.stock += order_item.quantity
                    order_item.product.save()

                    return JsonResponse({
                        "success": True,
                        "message": "Order item has been cancelled successfully.",
                        "item_id": order_item.id
                    })

                elif payment_method in ["Wallet", "Razorpay"]:
                    if is_payment_completed:
                        # Change status to "Requested for Refund"
                        order_item.status = "Requested for Refund"
                        order_item.save()

                        return JsonResponse({
                            "success": True,
                            "message": "Refund request has been sent. Admin will review it.",
                            "item_id": order_item.id
                        })
                    else:
                        return JsonResponse({
                            "success": False,
                            "message": "Payment not completed. Cannot request a refund.",
                            "item_id": order_item.id
                        })
                else:
                    return JsonResponse({
                        "success": False,
                        "message": "Unsupported payment method for cancellation.",
                        "item_id": order_item.id
                    })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)
@login_required
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
@login_required
def return_product(request, item_id):
    try:
        # Find the order item by its ID
        item = get_object_or_404(OrderItem, id=item_id)

        # Check if the item is eligible for return (status = "Delivered")
        if item.status != "Delivered":
            return JsonResponse({"success": False, "message": "Only delivered items can be returned."}, status=400)

        with transaction.atomic():
            # Change status to "Requested for Return"
            item.status = "Requested for Return"
            item.save()

            return JsonResponse({"success": True, "message": "Return request submitted. Admin approval pending."})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)




@login_required
def admin_orders(request):
    search_query = request.GET.get('q', '')  # Get search query for username
    date_filter = request.GET.get('date', '')  # Get search query for date

    # Fetch orders with related user, address, and items for optimization
    orders = Order.objects.select_related("user", "address").prefetch_related("items__product").order_by("-created_at")

    # Apply search filters
    if search_query:
        orders = orders.filter(user__username__icontains=search_query)

    if date_filter:
        orders = orders.filter(created_at__date=date_filter)

   # Pagination (Set 10 orders per page)
    paginator = Paginator(orders, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare order data
    orders_data = []  # ✅ Define only once
    for order in page_obj:  # ✅ Use paginated orders, not all orders
        total_price = sum(item.price * item.quantity for item in order.items.all())
        address = f"{order.address.address}, {order.address.city}, {order.address.state}" if order.address else "N/A"



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
        'page_obj': page_obj,
        'search_query': search_query,
        'date_filter': date_filter,
    }
    return render(request, 'admin/admin_order.html', context)

@login_required
def admin_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Fetch order values
    total_price = order.subtotal  
    total_discount = order.total_discount  
    final_total = order.total_amount  
    shipping_address = f"{order.address.address}, {order.address.city}" if order.address else "N/A"

    if request.method == "POST":
        item_id = request.POST.get('item_id')  
        new_status = request.POST.get('new_status')

        if item_id and new_status:
            try:
                order_item = get_object_or_404(OrderItem, id=item_id, order=order)

                with transaction.atomic():
                    if new_status == "Refunded" and order_item.status == "Requested for Refund":
                        order_item.product.stock += Decimal(str(order_item.quantity))
                        # print(type(order_item.quantity), type(order_item.product.stock))
                        # Process refund to wallet
                        wallet, created = Wallet.objects.get_or_create(user=order.user)
                        wallet.credit(order_item.final_amount)
                        order_item.status = "Refunded"
                        messages.success(request, f"Order item #{order_item.id} has been refunded.")

                    elif new_status == "Returned & Refunded" and order_item.status == "Requested for Return":
                        # Process return & refund
                        order_item.product.stock += Decimal(str(order_item.quantity))
                        order_item.product.save()
                        wallet, created = Wallet.objects.get_or_create(user=order.user)
                        wallet.credit(order_item.final_amount)
                        order_item.status = "Returned & Refunded"
                        messages.success(request, f"Order item #{order_item.id} has been returned and refunded.")

                    else:
                        order_item.status = new_status
                        messages.success(request, f"Order item #{order_item.id} status updated to {new_status}")

                    order_item.save()

                update_order_status(order)

            except OrderItem.DoesNotExist:
                messages.error(request, "Order item not found")

        return redirect(request.path)

    context = {
        'order': order,
        'order_items': order_items,
        'total_price': total_price,
        'total_discount': total_discount,
        'final_total': final_total,
        'shipping_address': shipping_address,
    }
    return render(request, 'admin/order_details.html', context)


def update_order_status(order):
    """Updates the order status based on the status of its items."""
    order_items = OrderItem.objects.filter(order=order)

    if all(item.status == "Delivered" for item in order_items):
        order.status = "Delivered"
    elif any(item.status == "Shipped" for item in order_items):
        order.status = "Shipped"
    elif all(item.status in ["Cancelled", "Returned & Refunded", "Refunded"] for item in order_items):
        order.status = "Cancelled"
    else:
        order.status = "Pending"

    order.save()
@login_required
def generate_invoice(order):
    order_items = order.items.all()

    shipping_address = (
        f"{order.address.full_name}, {order.address.address}, "
        f"{order.address.area if order.address.area else ''}, "
        f"{order.address.landmark if order.address.landmark else ''}, "
        f"{order.address.city}, {order.address.state} - {order.address.pincode}, "
        f"Phone: {order.address.phone_number}"
        if order.address else "N/A"
    )

    html_content = render_to_string('user/invoice_template.html', {
        'order': order,
        'order_items': order_items,
        'shipping_address': shipping_address,
        'total_discount': order.total_discount,
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
    })

    invoices_dir = os.path.join(settings.MEDIA_ROOT, "invoices")
    os.makedirs(invoices_dir, exist_ok=True)

    pdf_file_path = os.path.join(invoices_dir, f"{order.id}_invoice.pdf")

    pdf = HTML(string=html_content).write_pdf()

    with open(pdf_file_path, 'wb') as f:
        f.write(pdf)

    return pdf_file_path
@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)  # Fetch the Order object
    invoice_path = generate_invoice(order)  # Pass the Order object

    return FileResponse(open(invoice_path, 'rb'), content_type='application/pdf')



  


