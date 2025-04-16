from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Coupon,CouponUsage
from .forms import CouponForm
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from cart.models import Cart
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from orders.models import Order
from cart.models import Cart


@csrf_exempt
@login_required
def apply_coupon(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            coupon_code = data.get("code", "").strip()
            total_amount = float(data.get("total_amount", 0))

            # ✅ Check if coupon exists
            coupon = Coupon.objects.filter(code=coupon_code, is_active=True, expiry_date__gte=timezone.now().date()).first()
            # print("📢 Coupon Object:", coupon)

            if not coupon:
                return JsonResponse({"success": False, "error": "Coupon not found or expired."}, status=400)

            # ✅ Check if the user has already used this coupon
            if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                return JsonResponse({"success": False, "error": "You have already used this coupon."}, status=400)

            print("✅ Coupon Found:", coupon.code, "Discount:", coupon.discount_percentage)

            # ✅ Apply discount with max limit
            discount_amount = min((coupon.discount_percentage / 100) * total_amount, coupon.max_discount)
            # print("📢 Discount Amount:", discount_amount)
            
            final_total = total_amount - float(discount_amount)
            # print("📢 Final Total After Discount:", final_total)

            # ✅ Save the coupon usage for this user
            # CouponUsage.objects.create(user=request.user, coupon=coupon,final_total=final_total,discount_amount=discount_amount).save()

            # ✅ Store applied coupon in session
            request.session["applied_coupon_code"] = coupon.code

            return JsonResponse({
                "success": True,
                "discount_amount": round(discount_amount, 2),
                "final_total": round(final_total, 2)
            })

        except Exception as e:
            # print("❌ Internal Server Error:", e)
            return JsonResponse({"success": False, "error": str(e)}, status=500)
       

@login_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    today = now().date()
    return render(request, 'admin/coupon_list.html', {'coupons': coupons, 'today': today})

@login_required
def add_coupon(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')  # Redirect to list after saving
    else:
        form = CouponForm()
    return render(request, 'admin/coupon_add.html', {'form': form})


@login_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm(instance=coupon)

    today = now().date() 

    return render(request, 'admin/edit_coupon.html', {'form': form, 'coupon': coupon, 'today': today})
   
@login_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == "POST":
        coupon.delete()
        return redirect('coupon_list')
    else:
        return HttpResponseForbidden("Invalid request method. Please use POST.")