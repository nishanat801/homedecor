from django.shortcuts import render, redirect, get_object_or_404
from .models import Address
from .forms import AddressForm
from django.contrib import messages
from django.http import JsonResponse
import json

def address_list(request):
    """Display the list of saved addresses and add new addresses."""
    if not request.user.is_authenticated:
        return redirect('login')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()  # Fetch default address
    remaining_addresses = addresses.exclude(id=default_address.id) if default_address else addresses
    form = AddressForm()

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user  # Assign the logged-in user
            address.save()
            return redirect('address:address_list')  # Redirect after saving
        
        else:
            form = AddressForm()

    return render(request, 'user/address_list.html', {
        'default_address': default_address,
        'remaining_addresses': remaining_addresses,
        'form': form
    })

def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address:address_list')  # Redirect back to address list after saving
    else:
        form = AddressForm(instance=address)

    return render(request, 'user/edit_address.html', {'form': form, 'address': address})


def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        address.delete()
        return redirect('address:address_list')  # Redirect back to address list after deletion

    return render(request, 'user/confirm_delete.html', {'address': address})

def select_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        
        if address_id:
            request.session['selected_address_id'] = address_id
            print("Selected address ID:", request.session.get('selected_address_id'))
            messages.success(request, "Address selected successfully!")
            return redirect('orders:checkout_page')

        messages.error(request, "Please select a valid address.")
        return redirect('address:address_list')

    return redirect('address:address_list')

def set_default_address(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        address_id = data.get('address_id')

        if address_id:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            Address.objects.filter(id=address_id, user=request.user).update(is_default=True)
            return JsonResponse({'message': 'Default address updated successfully'}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def address_management(request):
    """Manage addresses in My Account (Add, Edit, Delete)"""
    if not request.user.is_authenticated:
        return redirect('login')

    addresses = Address.objects.filter(user=request.user)
    form = AddressForm()

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('address_management')  # Redirect after saving

    return render(request, 'user/address_management.html', {
        'addresses': addresses,
        'form': form
    })
def edit_address_management(request, address_id):
    address = get_object_or_404(Address, id=address_id)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address:address_management')  # Redirect back to address list after saving
    else:
        form = AddressForm(instance=address)

    return render(request, 'user/myaccount_edit_address.html', {'form': form, 'address': address})


def delete_address_management(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        address.delete()
        return redirect('address:address_management')  # Redirect back to address list after deletion

    return render(request, 'user/myaccount_delete_address.html', {'address': address})
