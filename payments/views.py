import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from orders.models import Order,OrderItem  # Assuming you have an Order model
import json
from django.db import transaction
from address.models import Address
from cart.models import Cart
from django.shortcuts import render, redirect
from coupons.models import Coupon,CouponUsage
from datetime import timezone
from payments.models import Wallet, WalletTransaction



@login_required
def pay_view(request):
    razorpay_order = request.session.get("razorpay_order", {})

    if not razorpay_order:
        return redirect("checkout")  # Redirect to checkout if no order details exist

    return render(request, "user/pay.html", {
        "razorpay_order_id": razorpay_order.get("order_id"),
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "total_amount": razorpay_order.get("total_amount"),
        "subtotal": razorpay_order.get("subtotal"),
        "discount": razorpay_order.get("discount"),
        "shipping": razorpay_order.get("shipping"),
        "order_items": razorpay_order.get("order_items", []),
    })




@login_required
def checkout_razorpay(request):
    if request.method == "POST":
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)

            address_id = data.get('address_id')  # Get address_id from the parsed JSON

            coupon_code = data.get("coupon_code")

            if not address_id:
                return JsonResponse({"status": "error", "message": "Address not selected"}, status=400)

            # Fetch selected address
            selected_address = get_object_or_404(Address, id=address_id)

            # Fetch cart items
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return JsonResponse({"status": "error", "message": "Cart is empty"}, status=400)

            # Calculate totals
            subtotal = sum(item.product.price * item.quantity for item in cart_items)
            shipping = 40  # Fixed shipping cost
            discount = 0  # Default discount
              # Check if a valid coupon is applied
            # if coupon_code:
            #     try:
            #         coupon = Coupon.objects.get(code=coupon_code, expiry_date__gte=timezone.now(), is_active=True)

            #         # Ensure minimum amount condition is met
            #         if subtotal >= coupon.minimum_amount:
            #             discount = (subtotal * coupon.discount_percentage) / 100
            #             discount = min(discount, coupon.maximum_discount)  # Ensure max discount limit
            #     except Coupon.DoesNotExist:
            #         return JsonResponse({"status": "error", "message": "Invalid or expired coupon"}, status=400)

            # Calculate total after discount
            coupon_usage = CouponUsage.objects.filter(user=request.user).last()
            print(coupon_usage.final_total)
            total_amount = coupon_usage.final_total

            
            
            # Create Razorpay Order
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            razorpay_order = client.order.create({
                "amount": int(total_amount * 100),  # Convert to paise
                "currency": "INR",
                "payment_capture": 1,
            })

            if razorpay_order["status"] == "created":
                # Store order details in session
                request.session["razorpay_order"] = {
                    "order_id": razorpay_order["id"],
                    "subtotal": str(subtotal),
                    "shipping": str(shipping),
                    "total_amount": str(total_amount),
                    "selected_address_id": address_id,
                    "discount": str(discount),
                    "applied_coupon": coupon_code if coupon_code else None,
                }

                return JsonResponse({
                    "status": "success",
                    "razorpay_order_id": razorpay_order["id"],
                    "total_amount": total_amount,
                })
            else:
                return JsonResponse({"status": "error", "message": "Failed to create Razorpay order"}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        data = json.loads(request.body)  # Handle JSON data

        razorpay_order_id = data.get("order_id")
        razorpay_payment_id = data.get("payment_id")
        razorpay_signature = data.get("signature")

        # Retrieve order details from session
        session_order_data = request.session.get("razorpay_order")
        if not session_order_data or session_order_data["order_id"] != razorpay_order_id:
            return JsonResponse({"status": "failed", "message": "Order session mismatch"}, status=400)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

        try:
            # Verify payment signature
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })

            # Fetch user and address from session data
            user = request.user
            selected_address = get_object_or_404(Address, id=session_order_data["selected_address_id"])

            # ⚡ Create a new Order after payment success
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    address=selected_address,
                    full_name=selected_address.full_name,
                    status="Pending",
                    payment_status="Completed",
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=razorpay_signature,
                )

                # Fetch cart items and create Order Items
                cart_items = Cart.objects.filter(user=user)
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,  # Save the price at order time
                    )
                


                # Clear cart after order is placed
                cart_items.delete()
                request.session.pop("razorpay_order", None)  # Remove session data
               
                # # After the order is successfully placed, update the user's profile
                # user_profile = UserProfile.objects.get(user=request.user)
                # user_profile.first_purchase = True
                # user_profile.first_purchase_date = datetime.now()
                # user_profile.save()

            return JsonResponse({"status": "success", "message": "Payment successful!", "order_id": order.id})
            

           
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"status": "failed", "message": "Signature verification failed!"}, status=400)

    return JsonResponse({"status": "failed", "message": "Invalid request!"}, status=400)



def payment_success_page(request):
    razorpay_order_id = request.session.get('razorpay_order_id')  # Or fetch from request

    # Fetch the first order with the given razorpay_order_id
    orders = Order.objects.filter(razorpay_order_id=razorpay_order_id)
    if not orders.exists():
        return JsonResponse({"status": "failed", "message": "Order not found"}, status=404)

    # If multiple orders exist, you can decide how to handle that, e.g., take the latest one
    order = orders.latest('created_at')  # assuming there's a `created_at` field to sort by

    # Fetch order items related to this order
    order_items = OrderItem.objects.filter(order=order)

    # Prepare context to pass to the template
    context = {
        'order_id': order.id,
        'payment_id': order.razorpay_payment_id,
        'total_amount': sum(item.final_amount for item in order_items),  # Total amount paid (sum of final amounts)
        'order_items': order_items,
    }

    # Render the payment success template with the context
    return render(request, "user/payment_success.html", context)



@csrf_exempt
def payment_failed(request):
    if request.method == "POST":
        data = json.loads(request.body)
        razorpay_order_id = data.get("order_id")

        if not razorpay_order_id:
            return JsonResponse({"status": "failed", "message": "Invalid data received"}, status=400)

        try:
            order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)
            order.payment_status = "Failed"
            order.save()

            return JsonResponse({"status": "failed", "message": "Payment failed! Please try again."})

        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "message": "Order not found!"}, status=404)

    return JsonResponse({"status": "failed", "message": "Invalid request!"}, status=400)


@login_required
def wallet_view(request):
    # Get or create the wallet for the logged-in user
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get all transactions related to this wallet
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-date')

    print(f"Wallet Balance: {wallet.balance}")
    print(f"Transactions: {transactions}")

    return render(request, "user/wallet.html", {"wallet": wallet, "transactions": transactions})