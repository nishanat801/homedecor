from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Product
from category.models import Category
from random import sample
from .models import ProductAttribute
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

@login_required
def search_products(request):
    query = request.GET.get('query', '').strip()

    products = []
    if query:
        # Filter products based on the query (case-insensitive search)
        products = Product.objects.filter(name__icontains=query)
    
    # Prepare product data to return
    product_data = [
        {"id": p.id, "name": p.name, "price": p.price, "image": p.image1.url}
        for p in products
    ]
    
    return JsonResponse({"products": product_data})

@login_required
def crop_resize_image(image, size=(300, 300)):
    """Resize and crop the image to the given size."""
    img = Image.open(image)
    img = img.convert("RGB")  # Convert to RGB to avoid issues with PNG
    img = img.resize(size, Image.LANCZOS)  # Use LANCZOS instead of ANTIALIAS

    # Save image to memory
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=90)  # Save as JPEG with quality 90
    return ContentFile(img_io.getvalue(), name=image.name)

# @user_passes_test(lambda user: user.is_superuser)
@login_required
def product_list(request):
    query = request.GET.get('q', '')  
    category_filter = request.GET.get('category', '')  
    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    if category_filter:
        products = products.filter(category__id=category_filter)  # Assuming category is a ForeignKey

    # Fetch all categories to display in dropdown
    categories = Category.objects.all()  

   # Apply Pagination (Make sure this is applied AFTER filtering)
    paginator = Paginator(products, 5)  # Show 5 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': products,
        'page_obj': page_obj,
        'categories': categories,
        'search_query': query,
        'selected_category': category_filter
    }

    return render(request, 'admin/product_list.html', context)

# add product
@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        category_id = request.POST['category']
        price = request.POST['price']
        stock = request.POST['stock']
        description = request.POST['description']

        # Ensure stock is a positive number
        if int(stock) <= 0:
            messages.error(request, "Stock must be a positive number.")
            return redirect('products:add_product')  # Redirect back to the form

        # Case-insensitive check for existing product name
        if Product.objects.filter(name__iexact=name).exists():
            messages.error(request, "A product with this name already exists.")
            return redirect('products:add_product')  # Redirect back to the form

        category = get_object_or_404(Category, id=int(category_id))

        # Create the product object but don't save it yet
        product = Product(
            name=name,
            category=category,
            price=price,
            stock=stock,
            description=description
        )

        # Handle uploaded images and crop them
        for i in range(1, 4):
            image = request.FILES.get(f'image{i}')
            if image:
                processed_image = crop_resize_image(image)  # Crop & resize
                if i == 1:
                    product.image1.save(image.name, processed_image, save=False)
                elif i == 2:
                    product.image2.save(image.name, processed_image, save=False)
                elif i == 3:
                    product.image3.save(image.name, processed_image, save=False)

        # Save the product after assigning images
        product.save()

        # Save product attributes for colors, materials, and sizes
        colors = request.POST.get('colors', '').split(',')
        materials = request.POST.get('materials', '').split(',')
        sizes = request.POST.get('sizes', '').split(',')

        for color in colors:
            if color.strip():
                ProductAttribute.objects.create(product=product, attribute_type='color', value=color.strip())
        for material in materials:
            if material.strip():
                ProductAttribute.objects.create(product=product, attribute_type='material', value=material.strip())
        for size in sizes:
            if size.strip():
                ProductAttribute.objects.create(product=product, attribute_type='size', value=size.strip())

        return redirect('products:product_list')

    categories = Category.objects.filter(is_active=True)
    return render(request, 'admin/add_product.html', {'categories': categories})





# edit product
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Retrieve existing attributes for the product
    existing_colors = ProductAttribute.objects.filter(product=product, attribute_type='color').values_list('value', flat=True)
    existing_materials = ProductAttribute.objects.filter(product=product, attribute_type='material').values_list('value', flat=True)
    existing_sizes = ProductAttribute.objects.filter(product=product, attribute_type='size').values_list('value', flat=True)

    if request.method == 'POST':
        # Retrieve values from the POST request
        name = request.POST['name']
        category_id = request.POST['category']
        price = request.POST['price']
        stock = request.POST['stock']
        description = request.POST['description']

        # Validate price (must be greater than 0)
        try:
            price = float(price)
            stock = int(stock)
            if price <= 0:
                messages.error(request, "Price must be greater than 0.")
                return redirect('products:edit_product', product_id=product_id)
        except ValueError:
            messages.error(request, "Invalid input! Price must be a number.")
            return redirect('products:edit_product', product_id=product_id)

        # Ensure product name is unique (excluding the current product)
        if Product.objects.filter(name__iexact=name).exclude(id=product_id).exists():
            messages.error(request, "A product with this name already exists.")
            return redirect('products:edit_product', product_id=product_id)

        # Update the product fields
        product.name = name
        product.category = get_object_or_404(Category, id=category_id)
        product.price = price
        product.stock = stock  # Allow zero stock
        product.description = description

        # Handle image uploads
        for i in range(1, 4):
            image = request.FILES.get(f'image{i}')
            if image:
                # Check if the same image filename already exists
                if Product.objects.filter(
                    Q(image1__icontains=image.name) |
                    Q(image2__icontains=image.name) |
                    Q(image3__icontains=image.name)
                ).exclude(id=product_id).exists():
                    messages.error(request, "An image with the same name already exists. Please rename the file and try again.")
                    return redirect('products:edit_product', product_id=product_id)

                processed_image = crop_resize_image(image)  # Crop & resize image
                if i == 1:
                    product.image1.save(image.name, processed_image, save=False)
                elif i == 2:
                    product.image2.save(image.name, processed_image, save=False)
                elif i == 3:
                    product.image3.save(image.name, processed_image, save=False)

        product.save()  # Save after all changes

        # Handle attribute updates (colors, materials, sizes)
        colors = request.POST.get('colors', '').split(',')
        materials = request.POST.get('materials', '').split(',')
        sizes = request.POST.get('sizes', '').split(',')

        # Clear existing attributes (optional)
        ProductAttribute.objects.filter(product=product, attribute_type='color').delete()
        ProductAttribute.objects.filter(product=product, attribute_type='material').delete()
        ProductAttribute.objects.filter(product=product, attribute_type='size').delete()

        # Save new attributes
        for color in colors:
            if color.strip():
                ProductAttribute.objects.create(product=product, attribute_type='color', value=color.strip())
        for material in materials:
            if material.strip():
                ProductAttribute.objects.create(product=product, attribute_type='material', value=material.strip())
        for size in sizes:
            if size.strip():
                ProductAttribute.objects.create(product=product, attribute_type='size', value=size.strip())

        messages.success(request, "Product updated successfully!")
        return redirect('products:product_list')

    # Pass existing attributes to the template
    return render(request, 'admin/edit_product.html', {
        'product': product,
        'categories': Category.objects.filter(is_active=True),
        'existing_colors': ', '.join(existing_colors),  # Prepopulate colors
        'existing_materials': ', '.join(existing_materials),  # Prepopulate materials
        'existing_sizes': ', '.join(existing_sizes),  # Prepopulate sizes
    })


#delete product 
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False  # Soft delete
    product.save()
    return redirect('products:product_list')


def unlist_product(request, product_id):
    product = Product.objects.get(id=product_id)
    product.is_active = False  # Unlist the product (soft delete)
    product.save()
    return redirect('products:product_list')

def list_product(request, product_id):
    product = Product.objects.get(id=product_id)
    product.is_active = True  # List the product
    product.save()
    return redirect('products:product_list')


# user side product list and category list

@login_required
def category_with_products(request, category_id=None):
    categories = Category.objects.filter(is_active=True)  # Fetch active categories
    selected_category = None
    products = []

    if category_id:  # If a specific category is clicked
        selected_category = get_object_or_404(Category, id=category_id, is_active=True)
        products = selected_category.products.filter(is_active=True)
    else:  # Load random products on the first page
        all_products = Product.objects.filter(is_active=True)
        products = sample(list(all_products), min(len(all_products), 15))  # Display up to 6 random products

    return render(request, 'user/home_product.html', {
        'categories': categories,
        'selected_category': selected_category,
        'products': products
    })

