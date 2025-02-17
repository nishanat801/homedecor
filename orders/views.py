from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order,OrderItem
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from cart.models import Cart
from address.models import Address



def checkout_page(request):
    selected_address_id = request.session.get("selected_address_id")
    selected_address = None

    if selected_address_id:
        selected_address = get_object_or_404(Address, id=selected_address_id)


    cart_items = Cart.objects.filter(user=request.user) 

    subtotal = sum(item.total_amount for item in cart_items)
    

    return render(request, "user/checkout.html", {
        "selected_address": selected_address,
        "cart_items": cart_items,
        "subtotal": subtotal
    })

def generate_tracking_number():
    return str(uuid.uuid4().hex[:10]).upper()


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "user/order_success.html", {"order": order})

ORDER_LIMIT = 5  # Maximum number of items per order

def place_order(request):
    if request.method == "POST":
        user = request.user
        selected_address_id = request.session.get("selected_address_id")

        if not selected_address_id:
            messages.error(request, "No address selected. Please select an address.")
            return redirect("orders:checkout_page")

        selected_address = get_object_or_404(Address, id=selected_address_id)

        # Fetch cart items
        cart_items = Cart.objects.filter(user=user)
        total_items = sum(item.quantity for item in cart_items)

        if total_items == 0:
            messages.error(request, "Your cart is empty.")
            return redirect("cart")

        if total_items > ORDER_LIMIT:
            messages.error(request, f"You can only order up to {ORDER_LIMIT} items.")
            return redirect("orders:checkout_page")

        # Create order
        order = Order.objects.create(
            user=user,
            address=selected_address,
            full_name=selected_address.full_name,
        )

        # Create OrderItems for each cart item
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,  # Save the price at the time of order
            )

        # Clear cart after order is placed
        cart_items.delete()
        del request.session["selected_address_id"]  # Remove selected address from session

        messages.success(request, "Order placed successfully!")
        return redirect("orders:order_success", order_id=order.id)
    

    return redirect("orders:checkout_page")



def user_order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')

    context = {
        'orders': [
            {
                'id': order.id,
                'order_number': order.tracking_number,
                'order_date': order.created_at.strftime("%Y-%m-%d"),
                'status': order.status,
                'total_price': sum(item.price * item.quantity for item in order.items.all()),  # Calculate total price dynamically
                'estimated_delivery': "5-7 business days",
                'address': {
                    'full_name': order.full_name,
                    'address_line_1': order.address.address if order.address else 'N/A',
                    'city': order.address.city if order.address else 'N/A',
                },
                'items': [
                    {
                        'product_name': item.product.name,
                        'product_images': [
                            item.product.image1.url if item.product.image1 else '',
                            item.product.image2.url if item.product.image2 else '',
                            item.product.image3.url if item.product.image3 else ''
                        ],
                        'price': item.price,
                        'quantity': item.quantity,
                        'date_of_delivery': "TBD",
                    } for item in order.items.all()
                ]
            } for order in orders
        ]
    }

    return render(request, 'user/orders_list.html', context)


def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)  # Fetch single order
    print("ok")
    if order.status == "pending":
        order.status = "cancelled"
        order.save()
        
        messages.success(request, "Your order has been cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled.")

    return redirect("orders:user_order_list")



def admin_orders(request):
    orders = Order.objects.select_related("user", "address").prefetch_related("items__product").all()

    orders_data = []
    for order in orders:
        total_price = sum(item.price * item.quantity for item in order.items.all())
        address = f"{order.address.address}, {order.address.city}" if order.address else "N/A"

        orders_data.append({
            'id': order.id,
            'tracking_number': order.tracking_number,
            'user': order.user.username,
            'total_price': total_price,
            'created_at': order.created_at,
            'status': order.status,
            'shipping_address': address,
        })

    context = {
        'orders': orders_data,
    }
    return render(request, 'admin/admin_order.html', context)


def admin_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Calculate total price for the order
    total_price = sum(item.price * item.quantity for item in order_items)

    # Shipping address (ensure you access it correctly based on your model)
    shipping_address = f"{order.address.city}" if order.address else "N/A"

    # Handle form submission for changing status
    if request.method == "POST":
        item_id = request.POST.get('item_id')  # This would be the OrderItem's ID
        new_status = request.POST.get('new_status')

        if new_status:
            # Update the status for the order item, if the item_id is provided
            if item_id:
                try:
                    order_item = OrderItem.objects.get(id=item_id)
                    order_item.status = new_status
                    order_item.save()
                    messages.success(request, f"Order item status updated to {new_status}")
                except OrderItem.DoesNotExist:
                    messages.error(request, "Order item not found")
            # If the status is meant for the whole order, update the Order status
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                messages.success(request, f"Order status updated to {new_status}")

            return redirect(request.path)  # Re-render the same page

    context = {
        'order': order,
        'order_items': order_items,
        'total_price': total_price,
        'shipping_address': shipping_address,
    }
    return render(request, 'admin/order_details.html', context)

  


