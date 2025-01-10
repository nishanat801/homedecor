from django.shortcuts import render
from products.models import Product
from random import sample
from django.shortcuts import render, get_object_or_404

def home_view(request):
    all_products = Product.objects.filter(is_active=True)
    products = sample(list(all_products), min(len(all_products), 6))  # Display up to 6 random products

    return render(request, 'user/home.html', {
        'products': products
    })
def product_details(request, product_id):
    # product = get_object_or_404(Product, id=product_id)
    # return render(request, 'user/single_product.html', {'product': product})
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]  # Limit to 4 related products
    return render(request, 'user/single_product.html', {
        'product': product,
        'related_products': related_products
    })


def user_login_view(request):
    return render(request,'user/login.html')
def admin_home_view(request):
    return render(request,'admin/admin_home.html')
def admin_login_view(request):
    return render(request,'admin/admin_login.html')







