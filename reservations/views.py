from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView, RedirectView
from django.urls import reverse, reverse_lazy
from .models import Booking, Payment
from .forms import BookingForm, PaymentForm

# Mewarisi CreateView dari Django untuk OOP yang lebih rapi
class BookingCreateView(LoginRequiredMixin, CreateView):
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

class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'reservations/booking_detail.html' # Mutia bakal bikin UI-nya di sini

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('room', 'payment')

class BookingListView(LoginRequiredMixin, ListView):
    """Riwayat pemesanan milik tamu yang sedang login ("Pemesanan Saya")."""
    model = Booking
    template_name = 'reservations/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related(
            'room', 'room__room_type', 'payment'
        ).order_by('-created_at')

class BookingLatestView(LoginRequiredMixin, RedirectView):
    """Lompat ke rincian reservasi terbaru ("Rincian Pemesanan")."""
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        latest = Booking.objects.filter(user=self.request.user).order_by('-created_at').first()
        if latest is None:
            return reverse('booking_list')
        return reverse('booking_detail', kwargs={'pk': latest.pk})

class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'reservations/payment_form.html'

    def form_valid(self, form):
        booking = Booking.objects.get(pk=self.kwargs['booking_id'], user=self.request.user)
        form.instance.booking = booking
        form.instance.amount = booking.total_biaya_akhir
        # Bukti diunggah → tandai menunggu verifikasi manual oleh staf.
        form.instance.status_pembayaran = 'PENDING_VERIFICATION'
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('booking_detail', kwargs={'pk': self.object.booking.pk})