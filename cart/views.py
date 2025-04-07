from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart,Wishlist
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def cart_view(request):
    # Fetch cart items for the logged-in user
    cart_items = Cart.objects.filter(user=request.user)  # Assuming Cart has a 'user' field
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        # 'savings': savings,
        # 'tax': tax,
        # 'estimated_total': estimated_total,
        'cart_item_count': cart_items.count(),
    }

    return render(request, 'user/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ✅ Check if the product is in stock
    if product.stock == 0:
        messages.error(request, "This product is out of stock!")
        return redirect('product_details', product_id=product.id)
    
    cart_item, created = Cart.objects.get_or_create(product=product, user=request.user)  # Assuming user is a field
    if not created:
        cart_item.quantity += 1
    cart_item.save()

    return redirect('cart')  # Redirect to the cart view

@login_required
def update_quantity(request, product_id, action):
    cart_item = get_object_or_404(Cart, product_id=product_id, user=request.user)
    product = get_object_or_404(Product, id=product_id)

    if action == "increment":
        if cart_item.quantity >= 4:  # ✅ Limit to a maximum of 4 items
            return JsonResponse({
                "error": "You can't purchase more than 4 items of this product!",
                "quantity": cart_item.quantity
            })
        elif cart_item.quantity < product.stock:  # ✅ Check stock availability
            cart_item.quantity += 1
            cart_item.save()
        else:
            return JsonResponse({
                "error": "Not enough stock available!",
                "quantity": cart_item.quantity
            })

    elif action == "decrement":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            return JsonResponse({"quantity": 0})  # ✅ Remove item if quantity reaches 0

    # ✅ Calculate the total price for this product
    total_price = cart_item.product.price * cart_item.quantity

    return JsonResponse({
        "quantity": cart_item.quantity,
        "total_price": total_price
    })

@login_required
def remove_from_cart(request, product_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            cart_item = get_object_or_404(Cart, product__id=product_id, user=request.user)
            cart_item.delete()
            return redirect('cart')  # Redirect to the cart page after removal
        except Cart.DoesNotExist:
            return redirect('cart')  # Redirect even if the item doesn't exist
    return redirect('cart')  # Redirect for invalid requests





@login_required
def wishlist_view(request):
    # Fetch wishlist items for the logged-in user
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {'wishlist_items': wishlist_items}
    return render(request, 'user/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist')  # Redirect to the wishlist page

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('wishlist')  # Redirect to the wishlist page

