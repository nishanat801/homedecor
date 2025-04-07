from django.shortcuts import  redirect
from products.models import Product,ProductAttribute
from random import sample
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .forms import ReviewForm
from .models import Review
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
@login_required
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
@login_required
def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    
    # Calculate average rating and total review count
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 1)  # Ensure one decimal place
    total_reviews = reviews.count()

    # Handle review submission
    if request.method == "POST":
        if request.user.is_authenticated:
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.user = request.user
                review.product = product
                review.save()
                messages.success(request, "Your review has been submitted successfully!")
                return redirect('product_details', product_id=product.id)
            else:
                messages.error(request, "There was an error with your submission. Please check your input.")
        else:
            messages.error(request, "You need to log in to submit a review.")
            return redirect('login')

    else:
        form = ReviewForm()

    return render(request, 'user/single_product.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'average_rating': average_rating,
        'total_reviews': total_reviews,  # Add total reviews to context
        'form': form
    })

@login_required
def my_reviews(request):
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')  # Fetch user reviews

    return render(request, 'user/my_reviews.html', {'reviews': reviews})


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)  # Ensure user owns the review

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully!")
            return redirect('my_reviews')  # Redirect to review management page
    else:
        form = ReviewForm(instance=review)

    return render(request, 'user/edit_review.html', {'form': form, 'review': review})

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)  # Ensure user owns the review
    review.delete()
    messages.success(request, "Review deleted successfully!")
    return redirect('my_reviews')



def user_login_view(request):
    return render(request,'user/login.html')
def admin_home_view(request):
    return render(request,'admin/admin_home.html')
def admin_login_view(request):
    return render(request,'admin/admin_login.html')







