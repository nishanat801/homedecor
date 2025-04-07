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
from django.contrib import messages
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from decimal import Decimal
from django.utils import timezone
from decimal import Decimal



@login_required
def pay_view(request):
    razorpay_order = Order.objects.filter(user=request.user, payment_status="Pending").order_by('-created_at').first()

    if not razorpay_order:
        print("No pending order found, redirecting to checkout")
        return redirect("orders:checkout_page")  

    print("Found order:", razorpay_order)  # Debugging print

    applied_coupon_code = request.session.get("applied_coupon_code")
    discount_amount = Decimal(0)  # Use Decimal for consistency

    if applied_coupon_code:
        print("Applied Coupon Code from session:", applied_coupon_code)

        coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True, expiry_date__gte=timezone.now().date()).first()
        
        if coupon:
            discount_percentage = float(coupon.discount_percentage) 

            discount_amount = min(Decimal(discount_percentage / 100) * Decimal(razorpay_order.subtotal), Decimal(coupon.max_discount))
            print("Discount Calculated:", discount_amount)

    total_amount = razorpay_order.subtotal - discount_amount

    return render(request, "user/pay.html", {
        "razorpay_order_id": razorpay_order.razorpay_order_id,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "total_amount": round(total_amount, 2),  
        "subtotal": razorpay_order.subtotal,
        "discount": round(discount_amount, 2),  
        "retry_payment": razorpay_order.payment_status == "Failed", 
        "shipping": 0,
        "order_items": OrderItem.objects.filter(order=razorpay_order),
    })



@login_required
def checkout_razorpay(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            address_id = data.get('address_id')
            coupon_code = data.get("coupon_code")

            if not address_id:
                return JsonResponse({"status": "error", "message": "Address not selected"}, status=400)

            # Fetch cart items
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return JsonResponse({"status": "error", "message": "Cart is empty"}, status=400)

            # Fetch selected address (Ensuring user owns it)
            selected_address = get_object_or_404(Address, id=address_id, user=request.user)

            # Calculate subtotal
            subtotal = sum(item.total_amount for item in cart_items)

            # Default values
            shipping = 0  # Fixed shipping cost
            discount = 0
            applied_coupon = None
            total_amount = subtotal

            # ✅ Check if a new coupon is provided, otherwise use session coupon
            if coupon_code:
                applied_coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
                request.session["applied_coupon_code"] = coupon_code  # Store new coupon in session
            else:
                applied_coupon_code = request.session.get("applied_coupon_code")
                if applied_coupon_code:
                    applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()

            # ✅ Apply coupon if valid
            # Calculate total discount
            total_discount = 0
            discount_per_item = {}

            if applied_coupon and subtotal >= applied_coupon.min_amount:
                total_discount = min((subtotal * applied_coupon.discount_percentage) / 100, applied_coupon.max_discount)

                # Distribute discount among cart items
                for item in cart_items:
                    proportion = (item.product.price * item.quantity) / subtotal
                    item_discount = round(proportion * total_discount, 2)
                    discount_per_item[item.id] = item_discount

            # Calculate final total amount after applying the discount
            total_amount = subtotal - total_discount

            # Create the order in database first (with pending status)
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    address=selected_address,
                    full_name=selected_address.full_name,
                    status="Pending Payment",
                    payment_status="Pending",
                    payment_method="Razorpay",
                    subtotal=subtotal,
                    total_discount=discount,
                    total_amount=total_amount,
                )

                for item in cart_items:
                    discount_amount = discount_per_item.get(item.id, 0)
                    final_price = (item.product.price * item.quantity) - discount_amount
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,  # Save original price per unit
                        subtotal=item.product.price * item.quantity,  # Total before discount
                        discount_amount=discount_amount,  # Discount for this item
                        final_amount=final_price,  # Final amount after discount
                        coupon=applied_coupon,  # Store coupon if applied
                    )
  
            
            # Create Razorpay Order
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            razorpay_order = client.order.create({
                "amount": int(total_amount * 100),  # Convert to paise
                "currency": "INR",
                "payment_capture": 1,
            })

           # Update our order with Razorpay order ID
            order.razorpay_order_id = razorpay_order["id"]
            print(order.razorpay_order_id)
            order.save()

            return JsonResponse({
                "status": "success",
                "razorpay_order_id": razorpay_order["id"],
                "total_amount": total_amount,
                "order_id": order.id,  # Return our DB order ID for reference
            })

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        data = json.loads(request.body)  # Handle JSON data

        razorpay_order_id = data.get("order_id")
        razorpay_payment_id = data.get("payment_id")
        razorpay_signature = data.get("signature")

         # Get the order from database
        order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id, user=request.user)
            
        if order.payment_status == "Completed":
            return JsonResponse({"status": "success", "message": "Payment already processed"})


        # # Retrieve order details from session
        # session_order_data = request.session.get("razorpay_order")
        # if not session_order_data or session_order_data["order_id"] != razorpay_order_id:
        #     return JsonResponse({"status": "failed", "message": "Order session mismatch"}, status=400)
        
          
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
            # selected_address = get_object_or_404(Address, id=session_order_data["selected_address_id"])

            # Fetch cart items
            cart_items = Cart.objects.filter(user=user)
            subtotal = sum(item.product.price * item.quantity for item in cart_items)

            # ✅ Fetch applied coupon from CouponUsage instead of session
            applied_coupon_code = request.session.get("applied_coupon_code")
            applied_coupon = None
            if applied_coupon_code:
                applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()

            # Calculate total discount
            total_discount = 0
            discount_per_item = {}

            if applied_coupon and subtotal >= applied_coupon.min_amount:
                total_discount = min((subtotal * applied_coupon.discount_percentage) / 100, applied_coupon.max_discount)

                # Distribute discount among cart items
                for item in cart_items:
                    proportion = (item.product.price * item.quantity) / subtotal
                    item_discount = round(proportion * total_discount, 2)
                    discount_per_item[item.id] = item_discount

            # Calculate final total amount after applying the discount
            total_amount = subtotal - total_discount

            

             # Update order status
            with transaction.atomic():
                order.payment_status = "Completed"
                order.status = "Paid"  # Or your next status
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.save()

                # ✅ Create CouponUsage record after order is placed
                if applied_coupon:
                    CouponUsage.objects.create(
                        user=user,
                        coupon=applied_coupon,
                        final_total=order.total_amount,
                        discount_amount=total_discount,
                    )

                # ✅ Clear the applied coupon from the session after the order
                request.session.pop("applied_coupon_code", None)

                # Clear cart after order is placed
                cart_items.delete()

                # Remove session data related to Razorpay order
                request.session.pop("razorpay_order", None)

            return JsonResponse({"status": "success", "message": "Payment successful!", "order_id": order.id})

        except razorpay.errors.SignatureVerificationError:
            order.payment_status = "Failed"
            order.status = "Payment Failed"
            order.save()

            return JsonResponse({"status": "failed", "message": "Signature verification failed!"}, status=400)

    return JsonResponse({"status": "failed", "message": "Invalid request!"}, status=400)



@login_required
def payment_success_page(request):
    razorpay_order_id = request.session.get('razorpay_order_id')  # Or fetch from request

    orders = Order.objects.filter(razorpay_order_id=razorpay_order_id)
    if not orders.exists():
        return JsonResponse({"status": "failed", "message": "Order not found"}, status=404)

    order = orders.latest('created_at')  
    order_items = OrderItem.objects.filter(order=order)

    coupon_usage = CouponUsage.objects.filter(user=request.user).order_by('-used_at').first()
    discount_amount = coupon_usage.discount_amount if coupon_usage else 0
    print(discount_amount)

    payment_id = order.razorpay_payment_id if order.razorpay_payment_id else "N/A"
    print(payment_id)

    context = {
        'order_id': order.id,
        'payment_id': payment_id,
        'total_amount': sum(item.final_amount for item in order_items),  
        'discount_amount': discount_amount,  
        'order_items': order_items,
        'order': order
    }
    return render(request, "user/payment_success.html", context)




@csrf_exempt
@login_required
def payment_failed(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_order_id = data.get("razorpay_order_id")
            error_code = data.get("error_code")
            error_description = data.get("error_description")

            print(f"Received payment failure data: {data}")  # Log the incoming data

            if not razorpay_order_id:
                return JsonResponse({"status": "failed", "message": "Invalid data received"}, status=400)

            # Fetch the order by Razorpay order ID
            order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)
            order.payment_status = "Failed"
            order.status = "Payment Failed"
            order.save()

            request.session.pop("applied_coupon_code", None)
            request.session.pop("applied_coupon_code", None)

            print(f"Updated order with Razorpay order ID {razorpay_order_id}")  # Log the update

            return JsonResponse({"status": "success", "message": "Payment failure recorded"})
        except Exception as e:
            print(f"Error processing payment failure: {e}")  # Log errors
            return JsonResponse({"status": "failed", "message": str(e)}, status=500)

    return JsonResponse({"status": "failed", "message": "Invalid request!"}, status=400)



def payment_failed_page(request):
    razorpay_order_id = request.GET.get("order_id")  # Razorpay order ID received
    print("Received Razorpay Order ID:", razorpay_order_id)

    order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)  # Get Order model ID
    order_id = order.id  # Store the correct Order model ID

    print("Mapped Order ID:", order_id)
    return render(request, "user/payment_failed.html", {"order_id": order_id})
    



def retry_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == "Paid":
        return JsonResponse({"status": "error", "message": "Order is already paid!"})

    # Re-create Razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
    razorpay_order = client.order.create({
        "amount": int(order.total_amount * 100),  # Convert to paise
        "currency": "INR",
        "payment_capture": 1,
        "notes": {"order_id": str(order.id)}
    })

    # Update order with new Razorpay order ID
    order.razorpay_order_id = razorpay_order["id"]
    order.save()
    return redirect("payments:pay_retry", order_id=order.id)



def pay_retry(request,order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    razorpay_order = Order.objects.filter(user=request.user, payment_status="Pending").order_by('-created_at').first()

    if not razorpay_order:
        print("No pending order found, redirecting to checkout")
        return redirect("orders:checkout_page")  

    print("Found order:", razorpay_order)  # Debugging print

    return render(request, "user/pay.html", {
        "razorpay_order_id": razorpay_order.razorpay_order_id,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "total_amount": razorpay_order.total_amount,
        "subtotal": razorpay_order.subtotal,
        "discount": razorpay_order.total_discount,
        "retry_payment": razorpay_order.payment_status == "Failed", 
        "shipping": 0,
        "order_items": OrderItem.objects.filter(order=razorpay_order),
    })

@login_required
def wallet_view(request):
    # Get or create the wallet for the logged-in user
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    
    # Get all transactions related to this wallet
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-date')

    print(f"Wallet Balance: {wallet.balance}")
    print(f"Transactions: {transactions}")

    return render(request, "user/wallet.html", {"wallet": wallet, "transactions": transactions})

@login_required
def wallet_payment(request):
    # ✅ Ensure cart is not empty
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("orders:checkout_page")

    # ✅ Retrieve selected address
    selected_address_id = request.session.get("selected_address_id")
    if not selected_address_id:
        messages.error(request, "Please select a shipping address.")
        return redirect("orders:checkout_page")

    selected_address = get_object_or_404(Address, id=selected_address_id, user=request.user)

    # ✅ Calculate total amount
    subtotal = sum(item.total_amount for item in cart_items)
    discount_amount = 0
    final_total = subtotal

    # ✅ Check if coupon is applied
    applied_coupon_code = request.session.get("applied_coupon_code")
    applied_coupon = None
    if applied_coupon_code:
        applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()
        if applied_coupon and subtotal >= applied_coupon.min_amount:
            discount_amount = min((subtotal * applied_coupon.discount_percentage) / 100, applied_coupon.max_discount)
            final_total -= discount_amount

    # ✅ Fetch or create wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    context = {
        "cart_items": cart_items,
        "selected_address": selected_address,
        "wallet_balance": wallet.balance,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "applied_coupon": applied_coupon,
    }

    return render(request, "user/wallet_payment.html", context)

@login_required
def confirm_wallet_payment(request):
    if request.method == "POST":
        user = request.user

        # Fetch user's wallet
        wallet, _ = Wallet.objects.get_or_create(user=user)

        # Fetch cart items
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty!")
            return redirect("orders:checkout_page")

        # Retrieve selected address
        selected_address = get_object_or_404(Address, user=user, is_default=True)

        # Calculate subtotal
        subtotal = sum(Decimal(item.product.price) * item.quantity for item in cart_items)

        # ✅ Fetch applied coupon from session
        applied_coupon_code = request.session.get("applied_coupon_code")
        applied_coupon = None
        if applied_coupon_code:
            applied_coupon = Coupon.objects.filter(code=applied_coupon_code, is_active=True).first()

        # ✅ Calculate total discount
        total_discount = Decimal("0.00")
        discount_per_item = {}

        if applied_coupon and subtotal >= applied_coupon.min_amount:
            max_discount = Decimal(applied_coupon.max_discount)
            calculated_discount = (subtotal * Decimal(applied_coupon.discount_percentage)) / Decimal("100")
            total_discount = min(calculated_discount, max_discount)

            # ✅ Distribute discount among cart items
            for item in cart_items:
                proportion = (Decimal(item.product.price) * item.quantity) / subtotal
                item_discount = round(proportion * total_discount, 2)
                discount_per_item[item.id] = item_discount

        # ✅ Calculate final total amount after applying the discount
        final_total = subtotal - total_discount

        # ✅ Check wallet balance
        if wallet.balance < final_total:
            messages.error(request, "Insufficient wallet balance!")
            return redirect("orders:checkout_page")

        # ✅ Process payment
        with transaction.atomic():
            # Deduct wallet balance
            wallet.balance -= final_total
            wallet.save()

            # Record wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="debit",
                amount=final_total,
                description="Order payment using wallet",
            )

            # Create Order
            order = Order.objects.create(
                user=user,
                address=selected_address,
                full_name=selected_address.full_name,
                tracking_number=f"TRK{now().timestamp()}",
                subtotal=subtotal,
                total_discount=total_discount,
                total_amount=final_total,
                status="Pending",
                payment_status="Completed",
                payment_method="Wallet",
            )

            # ✅ Create OrderItems with distributed discount
            for item in cart_items:
                discount_amount = discount_per_item.get(item.id, Decimal("0.00"))
                final_price = (Decimal(item.product.price) * item.quantity) - discount_amount

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=Decimal(item.product.price),
                    subtotal=Decimal(item.product.price) * item.quantity,
                    discount_amount=discount_amount,
                    final_amount=final_price,
                    coupon=applied_coupon,
                )

            # ✅ Save CouponUsage after order placement
            if applied_coupon:
                CouponUsage.objects.create(
                    user=user,
                    coupon=applied_coupon,
                    final_total=order.total_amount,
                    discount_amount=total_discount
                )

            # ✅ Clear the applied coupon from the session after the order
            request.session.pop("applied_coupon_code", None)

            # Clear cart
            cart_items.delete()

        messages.success(request, "Payment successful!")
        return redirect("payments:wallet_payment_success", order_id=order.id)

    return redirect("orders:checkout_page")  # Redirect if GET request
@login_required
def wallet_payment_success(request, order_id):
    try:
        # Fetch the order and wallet details
        order = Order.objects.get(id=order_id, user=request.user)
        wallet = Wallet.objects.get(user=request.user)

        context = {
            "order": order,
            "subtotal": order.subtotal,
            "discount": order.total_discount,
            "total_amount": order.total_amount,
            "wallet_balance": wallet.balance,
        }

        return render(request, "user/wallet_payment_success.html", context)

    except Order.DoesNotExist:
        return redirect("home")  # Redirect to home if order is not found