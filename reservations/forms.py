#buat di styling ui nya sama mutia

from django import forms
from django.core.exceptions import ValidationError
from rooms.models import Room
from .models import Booking, Payment, PromoVoucher

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'tanggal_check_in', 'tanggal_check_out', 'jumlah_tamu', 'voucher']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tanggal_check_out': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'jumlah_tamu': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'voucher': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.select_related('room_type').order_by('room_number')
        self.fields['room'].empty_label = '— Pilih kamar —'
        self.fields['voucher'].queryset = PromoVoucher.objects.order_by('kode_voucher')
        self.fields['voucher'].required = False
        self.fields['voucher'].empty_label = '— Tanpa voucher —'

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        check_in = cleaned_data.get('tanggal_check_in')
        check_out = cleaned_data.get('tanggal_check_out')
        guest_count = cleaned_data.get('jumlah_tamu')

        if not room or not check_in or not check_out or not guest_count:
            return cleaned_data
        if check_out <= check_in:
            raise ValidationError('Tanggal check-out harus setelah check-in.')
        if guest_count > room.room_type.capacity:
            raise ValidationError(f'Kapasitas kamar maksimal {room.room_type.capacity} tamu.')
        if room.status != 'CLEAN':
            raise ValidationError('Kamar yang dipilih belum siap untuk dipesan.')
        if not Booking.available_rooms(check_in, check_out).filter(pk=room.pk).exists():
            raise ValidationError('Kamar tidak tersedia pada periode tersebut.')
        return cleaned_data

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['metode_pembayaran', 'bukti_transfer_url']
        widgets = {
            'metode_pembayaran': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Transfer Bank'}),
            'bukti_transfer_url': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }