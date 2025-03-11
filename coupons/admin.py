from django.contrib import admin
from .models import Coupon
from django.utils.timezone import now
from django.utils import timezone


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "coupon_type", "discount_percentage", "min_amount", "max_discount", "expiry_date", "is_active")
    search_fields = ("name", "code")
    list_filter = ("coupon_type", "is_active", "expiry_date")

    def status(self, obj):
        return "Active" if obj.expiry_date >= timezone.now().date() else "Expired"
    
    status.short_description = "Status"
    status.admin_order_field = 'expiry_date'
