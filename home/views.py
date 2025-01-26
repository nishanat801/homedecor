from django.shortcuts import render
from products.models import Product,ProductAttribute
from random import sample
from django.shortcuts import render, get_object_or_404

def home_view(request):
    material_value = request.GET.get('material')  # Get selected material
    color_value = request.GET.get('color')  # Get selected color
    category_id = request.GET.get('category')  # Get selected category
    sort_by = request.GET.get('sort_by')  # Get sorting option

    # Get all active products initially
    products = Product.objects.filter(is_active=True)

    # Apply category filter if provided
    if category_id:
        products = products.filter(category_id=category_id)

    # Apply material filter if provided
    if material_value:
        products = products.filter(attributes__attribute_type='material', attributes__value=material_value)
        available_colors = ProductAttribute.objects.filter(
            product__in=products, attribute_type='color'
        ).values_list('value', flat=True).distinct()
    else:
        available_colors = ProductAttribute.objects.filter(attribute_type='color').values_list('value', flat=True).distinct()

    # Apply color filter if provided
    if color_value:
        products = products.filter(attributes__attribute_type='color', attributes__value=color_value)

    # Sorting logic
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'name-asc':
        products = products.order_by('name')
    elif sort_by == 'name-desc':
        products = products.order_by('-name')

    # Sample 6 products if no filters or sorting applied
    if not (material_value or color_value or category_id or sort_by):
        products = sample(list(products), min(len(products), 6))

    # Get unique materials and colors for filter dropdowns
    materials = ProductAttribute.objects.filter(attribute_type='material').values_list('value', flat=True).distinct()

    return render(request, 'user/home.html', {
        'products': products,
        'materials': materials,
        'colors': available_colors,  # Update colors based on selected material
        'sort_by': sort_by,  # Pass sort option to template
    })

def product_details(request, product_id):
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







