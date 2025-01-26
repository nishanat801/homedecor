from django.shortcuts import render, redirect, get_object_or_404
from .models import Address
from .forms import AddressForm

def address_list(request):
    """Display the list of saved addresses and add new addresses."""
    if not request.user.is_authenticated:
        return redirect('login')

    addresses = Address.objects.filter(user=request.user)  # Assuming addresses are linked to a user
    form = AddressForm()

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user  # Assign the logged-in user
            address.save()
            return redirect('address:address_list')  # Redirect after saving
        else:
            print(form.errors)  # Print form errors for debugging

    return render(request, 'user/personal_info.html', {'addresses': addresses, 'form': form})