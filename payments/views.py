import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from orders.models import Order,OrderItem  # Assuming you have an Order model
import json

@login_required
def checkout_razorpay(request):
    user = request.user
    order = Order.objects.filter(user=user, status="Pending").order_by('-created_at').first()  # Fetch the latest pending order

    if not order:
        return render(request, "user/cart.html")  # Redirect if no order exists

    order_items = OrderItem.objects.filter(order=order)
    subtotal = sum(item.product.price * item.quantity for item in order_items)
    shipping = 40  # Fixed shipping cost (adjust as needed)
    total_amount = subtotal + shipping

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
    
    # Create a Razorpay order
    razorpay_order = client.order.create({
        "amount": int(total_amount * 100),  # Convert to paise
        "currency": "INR",
        "payment_capture": 1  # Auto-capture payment
    })

    context = {
        "order_items": order_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total_amount": total_amount,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }

    print("Context Data:", context)
    return render(request, "user/pay.html", context)


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        try:
            # ✅ Read JSON data from request body
            data = json.loads(request.body)
            print("Received Data:", data)  # ✅ Debugging step

            razorpay_order_id = data.get("order_id")  
            razorpay_payment_id = data.get("payment_id")
            razorpay_signature = data.get("signature")

            if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
                return JsonResponse({"status": "failed", "message": "Missing payment details"}, status=400)

            # ✅ Fetch order from DB
            order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)
            print("Order found:", order)  # ✅ Debugging step

            # ✅ Verify Razorpay Signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
            
            client.utility.verify_payment_signature(params_dict)
            print("Signature verification passed!")  # ✅ Debugging step

            # ✅ Update order as "Paid"
            order.status = "Paid"  
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()
            print("Order updated successfully!")  # ✅ Debugging step

            return JsonResponse({"status": "success", "message": "Payment successful!"})

        except razorpay.errors.SignatureVerificationError:
            print("Signature verification failed!")  # ✅ Debugging step
            return JsonResponse({"status": "failed", "message": "Signature verification failed!"}, status=400)
        except json.JSONDecodeError:
            print("Invalid JSON format!")  # ✅ Debugging step
            return JsonResponse({"status": "failed", "message": "Invalid JSON format!"}, status=400)
        except Exception as e:
            print("Error:", str(e))  # ✅ Debugging step
            return JsonResponse({"status": "failed", "message": str(e)}, status=400)

    return JsonResponse({"status": "failed", "message": "Invalid request!"}, status=400)


def pay_view(request):
    return render(request, "user/pay.html")
