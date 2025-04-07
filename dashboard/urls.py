from django.urls import path
from . import views

urlpatterns = [
    path('sales_dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('export-sales-report-pdf/', views.export_sales_report_pdf, name='export_sales_report_pdf'),
]