#buat di styling ui nya sama mutia

from django import forms
from .models import Booking, Payment

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'tanggal_check_in', 'tanggal_check_out', 'jumlah_tamu', 'voucher']
        widgets = {
            'tanggal_check_in': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'tanggal_check_out': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['metode_pembayaran', 'bukti_transfer_url']