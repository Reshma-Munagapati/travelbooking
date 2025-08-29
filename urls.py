from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                     # Register + Login single page
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('travel/', views.travel_list_view, name='travel_list'),
    path('book/<int:travel_id>/', views.booking_create_view, name='booking_create'),
    path('bookings/', views.my_bookings_view, name='my_bookings'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking_view, name='booking_cancel'),
]
