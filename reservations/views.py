from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from .models import Booking, Payment
from .forms import BookingForm, PaymentForm

# Mewarisi CreateView dari Django untuk OOP yang lebih rapi
class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'reservations/booking_form.html' # Mutia bakal bikin ui di sini
    
    def form_valid(self, form):
        # Otomatis ngisi user yang sedang login
        form.instance.user = self.request.user
        response = super().form_valid(form)
        # Menghitung total harga otomatis (enkapsulasi)
        self.object.hitung_total_biaya()
        return response

    def get_success_url(self):
        return reverse_lazy('booking_detail', kwargs={'pk': self.object.pk})

class BookingDetailView(DetailView):
    model = Booking
    template_name = 'reservations/booking_detail.html' # Mutia bakal bikin UI-nya di sini

class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'reservations/payment_form.html'

    def form_valid(self, form):
        booking = Booking.objects.get(pk=self.kwargs['booking_id'])
        form.instance.booking = booking
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('booking_detail', kwargs={'pk': self.object.booking.pk})