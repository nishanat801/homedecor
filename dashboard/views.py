from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Sum
from datetime import datetime
from orders.models import Order, OrderItem
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def sales_dashboard(request):
    today = timezone.now().date()
    date_range = request.GET.get('date_range')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # ✅ Handle Date Filtering
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            start_date, end_date = today, today
    else:
        if date_range == 'today':
            start_date, end_date = today, today
        elif date_range == 'this_week':
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = start_date + timedelta(days=6)  # Sunday
        elif date_range == 'this_month':
            start_date = today.replace(day=1)
            end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        elif date_range == 'this_year':
            start_date, end_date = today.replace(month=1, day=1), today.replace(month=12, day=31)
        else:
            start_date, end_date = today, today

    # ✅ Filter Orders by Date Range
    orders = Order.objects.filter(created_at__date__range=[start_date, end_date])

    # ✅ Apply Search Filter for Order ID and Customer Name
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(status__icontains=search_query)  # Now allows searching by order status
        )

    # ✅ Apply Pagination (20 orders per page)
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)

    # ✅ Sales Metrics
    overall_sales_count = orders.count()
    overall_order_amount = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    overall_discount = orders.aggregate(Sum('total_discount'))['total_discount__sum'] or 0
    overall_net_sales = overall_order_amount - overall_discount

    # ✅ Best-Selling Items
    best_selling_products = (
        OrderItem.objects.filter(order__created_at__date__range=[start_date, end_date])
        .values('product__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:10]
    )

    best_selling_categories = (
        OrderItem.objects.filter(order__created_at__date__range=[start_date, end_date])
        .values('product__category__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:10]
    )

    best_selling_brands = (
        OrderItem.objects.filter(order__created_at__date__range=[start_date, end_date])
        .values('product__brand')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:10]
    )

    # ✅ Pass the Correct Context
    context = {
        'orders': orders_page,  # <-- Use paginated orders
        'search_query': search_query,
        'paginator': paginator,
        'overall_sales_count': overall_sales_count,
        'overall_order_amount': overall_order_amount,
        'overall_discount': overall_discount,
        'overall_net_sales': overall_net_sales,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': date_range,
        'best_selling_products': best_selling_products,
        'best_selling_categories': best_selling_categories,
        'best_selling_brands': best_selling_brands,
    }

    return render(request, 'admin/dashboard.html', context)

@login_required
def export_sales_report_pdf(request):
    today = timezone.now().date()

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        start_date, end_date = today, today

    orders = Order.objects.filter(created_at__date__range=[start_date, end_date])

    context = {
        'orders': orders,
        'start_date': start_date,
        'end_date': end_date,
        'overall_sales_count': orders.count(),
        'overall_order_amount': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'overall_discount': orders.aggregate(Sum('total_discount'))['total_discount__sum'] or 0,
        'overall_net_sales': (orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0) -
                             (orders.aggregate(Sum('total_discount'))['total_discount__sum'] or 0)
    }

    html_string = render_to_string('admin/pdf_sales_report.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    return response




# Create your views here.
