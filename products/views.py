from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Product
from category.models import Category
from random import sample
from django.contrib.auth.decorators import user_passes_test

# @user_passes_test(lambda user: user.is_superuser)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'admin/product_list.html', {'products': products})

# add product
def add_product(request):
    if request.method == 'POST':
        # Retrieve and validate form inputs
        name = request.POST['name']
        category_id = request.POST['category']
        price = request.POST['price']
        stock = request.POST['stock']
        description = request.POST['description']
        brand = request.POST.get('brand', '')
        colors = request.POST.getlist('colors')

        try:
            # Validate and fetch the category
            category = get_object_or_404(Category, id=int(category_id))
        except ValueError:
            return JsonResponse({'error': 'Invalid category ID'}, status=400)

        # Create the product
        product = Product.objects.create(
            name=name,
            category=category,
            price=price,
            stock=stock,
            description=description,
            brand=brand,
            available_colors=colors
        )

        # Handle uploaded images
        for i in range(1, 4):
            image = request.FILES.get(f'image{i}')
            if image:
                setattr(product, f'image{i}', image)

        product.save()
         
        print("Product added, redirecting to product list...")

        return redirect('product_list')

    # Render the add product page
    categories = Category.objects.filter(is_active=True)
    return render(request, 'admin/add_product.html', {'categories': categories})


# edit product
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST['name']
        category_id = request.POST['category']
        product.category = get_object_or_404(Category, id=category_id)
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        product.description = request.POST['description']
        product.brand = request.POST.get('brand', '')
        product.available_colors = request.POST.getlist('colors')

        for i in range(1, 4):
            image = request.FILES.get(f'image{i}')
            if image:
                setattr(product, f'image{i}', image)

        product.save()
        return redirect('products:product_list')

    return render(request, 'admin/edit_product.html', {'product': product, 'categories': Category.objects.filter(is_active=True)})

#delete product 
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False  # Soft delete
    product.save()
    return redirect('products:product_list')


# user side product list and category list

def category_with_products(request, category_id=None):
    categories = Category.objects.filter(is_active=True)  # Fetch active categories
    selected_category = None
    products = []

    if category_id:  # If a specific category is clicked
        selected_category = get_object_or_404(Category, id=category_id, is_active=True)
        products = selected_category.products.filter(is_active=True)
    else:  # Load random products on the first page
        all_products = Product.objects.filter(is_active=True)
        products = sample(list(all_products), min(len(all_products), 6))  # Display up to 6 random products

    return render(request, 'user/home_product.html', {
        'categories': categories,
        'selected_category': selected_category,
        'products': products
    })

