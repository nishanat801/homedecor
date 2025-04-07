from django.shortcuts import render, redirect, get_object_or_404
from .models import Category
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

# List Categories
@login_required
def category_list(request):
    # Fetch only active categories
    categories = Category.objects.all()

     # Handle search functionality
    search_query = request.GET.get('search', '')  # Get the search query from the request
    categories = Category.objects.filter(name__icontains=search_query)  # Filter categories by name

    # Set up pagination
    paginator = Paginator(categories, 10)  # Show 10 categories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/category_list.html', {'categories': categories,'page_obj': page_obj, 'search_query': search_query})


# Add Category
@login_required
def add_category(request):
    if request.method == 'POST':
        # Retrieve form data
        category_name = request.POST.get('category')
        description = request.POST.get('description')
        category_image = request.FILES.get('image')  # Get the uploaded image

        # Validate category name
        if not category_name:
            return render(request, 'admin/add_category.html', {
                'error_message': 'Category name is required.'
            })
        
        # Check for duplicate category name
        if Category.objects.filter(name__iexact=category_name).exists():
            return render(request, 'admin/add_category.html', {
                'error_message': 'A category with this name already exists.'
            })

        # Validate image (optional, depending on your requirement)
        if category_image:
            # Check if the uploaded file is an image
            if not category_image.content_type.startswith('image/'):
                return render(request, 'admin/add_category.html', {
                    'error_message': 'Please upload a valid image file.'
                })

        # Save the new category if validation passes
        Category.objects.create(
            name=category_name,
            description=description,
            image=category_image,
            is_active=True
        )
        print(f"Category '{category_name}' added with description: {description}")
        return redirect('category_list')  # Adjust the redirect URL as needed

    return render(request, 'admin/add_category.html')

# Edit Category
@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)  # Retrieve the category object by primary key

    if request.method == 'POST':
        # Retrieve form data
        category_name = request.POST.get('name')
        category_description = request.POST.get('description')
        category_image = request.FILES.get('image')  # Get the uploaded image

        # Validate category name
        if not category_name:
            return render(request, 'admin/edit_category.html', {
                'category': category,
                'error_message': 'Category name is required.'
            })

        # Check for duplicate category name (excluding current category)
        if Category.objects.filter(name__iexact=category_name).exclude(pk=category.pk).exists():
            return render(request, 'admin/edit_category.html', {
                'category': category,
                'error_message': 'A category with this name already exists.'
            })

        # Handle image upload and validation
        if category_image:
            # Validate the image type (optional)
            if not category_image.content_type.startswith('image/'):
                return render(request, 'admin/edit_category.html', {
                    'category': category,
                    'error_message': 'Please upload a valid image file.'
                })

            # If new image is provided, save it
            category.image = category_image

        # Update category fields and save
        category.name = category_name
        category.description = category_description
        category.save()

        return redirect('category_list')  # Redirect to the category list page after successful edit

    return render(request, 'admin/edit_category.html', {'category': category})
# Soft Delete Category
@login_required
def unlist_category(request, category_id):
    category = Category.objects.get(id=category_id)
    category.is_active = False  # Unlist the category
    category.save()
    return redirect('category_list')  # Redirect to category list page

def list_category(request, category_id):
    category = Category.objects.get(id=category_id)
    category.is_active = True  # List the category
    category.save()
    return redirect('category_list')  # Redirect to category list page
