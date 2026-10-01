#buat di styling ui nya sama mutia

from django import forms
from .models import Booking, Payment

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'tanggal_check_in', 'tanggal_check_out', 'jumlah_tamu', 'voucher']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_check_in': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'tanggal_check_out': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'jumlah_tamu': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'voucher': forms.Select(attrs={'class': 'form-select'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['metode_pembayaran', 'bukti_transfer_url']
        widgets = {
            'metode_pembayaran': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Transfer Bank'}),
            'bukti_transfer_url': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }