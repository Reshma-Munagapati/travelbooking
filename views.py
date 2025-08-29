from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm

from .forms import UserRegisterForm, UserUpdateForm, BookingForm
from .models import TravelOption, Booking

# ---- Home: Register + Login on same page ----
def home(request):
    if request.method == 'POST':
        # Register submitted?
        if 'register' in request.POST:
            r_form = UserRegisterForm(request.POST)
            l_form = AuthenticationForm()
            if r_form.is_valid():
                r_form.save()
                messages.success(request, "Account created! Please log in below.")
                return redirect('home')
        # Login submitted?
        elif 'login' in request.POST:
            r_form = UserRegisterForm()
            l_form = AuthenticationForm(request, data=request.POST)
            if l_form.is_valid():
                user = l_form.get_user()
                login(request, user)
                return redirect('travel_list')
            else:
                messages.error(request, "Invalid username/password.")
    else:
        r_form = UserRegisterForm()
        l_form = AuthenticationForm()

    return render(request, 'accounts/home.html', {'r_form': r_form, 'l_form': l_form})

# ---- Logout ----
@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# ---- Profile ----
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})

# ---- Travel list ----
@login_required
def travel_list_view(request):
    qs = TravelOption.objects.all().order_by('date_time')
    t = request.GET.get('type')
    src = request.GET.get('source')
    dst = request.GET.get('destination')
    if t:
        qs = qs.filter(type=t)
    if src:
        qs = qs.filter(source__icontains=src)
    if dst:
        qs = qs.filter(destination__icontains=dst)
    return render(request, 'accounts/travel_list.html', {'travels': qs})

# ---- Create booking ----
@login_required
@transaction.atomic
def booking_create_view(request, travel_id):
    travel = get_object_or_404(TravelOption, pk=travel_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            seats = form.cleaned_data['number_of_seats']
            travel_locked = TravelOption.objects.select_for_update().get(pk=travel.pk)
            if seats > travel_locked.available_seats:
                messages.error(request, f"Only {travel_locked.available_seats} seats available.")
                return redirect('booking_create', travel_id=travel.pk)

            booking = Booking(
                user=request.user,
                travel_option=travel_locked,
                number_of_seats=seats,
                booking_date=timezone.now(),
                status='Confirmed',
            )
            booking.recalc_total()
            booking.save()

            travel_locked.available_seats -= seats
            travel_locked.save(update_fields=['available_seats'])

            messages.success(request, f"Booking confirmed! #{booking.booking_id}")
            return redirect('my_bookings')
    else:
        form = BookingForm()

    return render(request, 'accounts/booking_create.html', {'travel': travel, 'form': form})

# ---- My bookings ----
@login_required
def my_bookings_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'accounts/bookings_list.html', {'bookings': bookings})

# ---- Cancel booking ----
@login_required
@transaction.atomic
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status == 'Cancelled':
        messages.info(request, "This booking is already cancelled.")
        return redirect('my_bookings')

    if request.method == 'POST':
        travel_locked = TravelOption.objects.select_for_update().get(pk=booking.travel_option.pk)
        travel_locked.available_seats += booking.number_of_seats
        travel_locked.save(update_fields=['available_seats'])

        booking.status = 'Cancelled'
        booking.save(update_fields=['status'])
        messages.success(request, f"Booking #{booking.booking_id} cancelled.")
        return redirect('my_bookings')

    return render(request, 'accounts/booking_cancel_confirm.html', {'booking': booking})
