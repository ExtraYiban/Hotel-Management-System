from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from rooms.models import Room

#Ini sementara aja karena room blm selesai
class TemporaryRoom(models.Model):
    nomor_kamar = models.CharField(max_length=10)
    harga_per_malam = models.FloatField(default=500000.0)

    def __str__(self):
        return f"Kamar {self.nomor_kamar}"

#Inheritance
class BaseTransaction(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

#promo vocer
class PromoVoucher(BaseTransaction):
    kode_voucher = models.CharField(max_length=50, unique=True)
    persen_diskon = models.FloatField(default=0.0)
    potongan_nominal = models.FloatField(default=0.0)
    minimal_transaksi = models.FloatField(default=0.0)
    tanggal_kedaluwarsa = models.DateTimeField()
    kuota_penggunaan = models.IntegerField(default=0)

    def is_valid(self, total_transaksi):
        return self.kuota_penggunaan > 0 and Decimal(str(total_transaksi)) >= Decimal(str(self.minimal_transaksi))

    def __str__(self):
        return self.kode_voucher

#kelas booking enkapsulasi dan abstraksi
class Booking(BaseTransaction):
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked-in'),
        ('CHECKED_OUT', 'Checked-out'),
        ('CANCELLED', 'Dibatalkan'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='guest_id', related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, db_column='room_id', related_name='bookings')
    voucher = models.ForeignKey(PromoVoucher, on_delete=models.SET_NULL, null=True, blank=True)
    
    tanggal_check_in = models.DateField(db_column='check_in_date')
    tanggal_check_out = models.DateField(db_column='check_out_date')
    jumlah_tamu = models.PositiveIntegerField(default=1, db_column='guest_count')
    
    #Enkapsulasi
    total_harga_dasar = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='total_amount')
    pajak_dan_layanan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_biaya_akhir = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status_pesanan = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_PAYMENT', db_column='status')
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bookings'
        constraints = [
            models.CheckConstraint(condition=models.Q(tanggal_check_out__gt=models.F('tanggal_check_in')), name='booking_checkout_after_checkin'),
            models.CheckConstraint(condition=models.Q(jumlah_tamu__gt=0), name='booking_guest_count_positive'),
        ]

    @classmethod
    def available_rooms(cls, check_in, check_out):
        if check_out <= check_in:
            raise ValueError('Tanggal check-out harus setelah check-in.')

        blocking_statuses = ['PENDING_PAYMENT', 'CONFIRMED', 'CHECKED_IN']
        blocked_room_ids = cls.objects.filter(
            status_pesanan__in=blocking_statuses,
            tanggal_check_in__lt=check_out,
            tanggal_check_out__gt=check_in,
        ).values('room_id')
        return Room.objects.filter(status='CLEAN').exclude(pk__in=blocked_room_ids)

    def hitung_total_biaya(self):
        """Abstraksi kalkulasi biaya"""
        durasi = (self.tanggal_check_out - self.tanggal_check_in).days
        if durasi <= 0: durasi = 1
        
        self.total_harga_dasar = Decimal(str(self.room.room_type.price_per_night)) * durasi
        diskon = Decimal('0')

        if self.voucher and self.voucher.is_valid(self.total_harga_dasar):
            diskon = (self.total_harga_dasar * (Decimal(str(self.voucher.persen_diskon)) / Decimal('100'))) if self.voucher.persen_diskon > 0 else Decimal(str(self.voucher.potongan_nominal))

        subtotal = max(Decimal('0'), self.total_harga_dasar - diskon)
        self.pajak_dan_layanan = subtotal * Decimal('0.11')
        self.total_biaya_akhir = subtotal + self.pajak_dan_layanan
        self.save()

    def batalkan_pesanan(self):
        if self.status_pesanan in {'PENDING_PAYMENT', 'CONFIRMED'}:
            self.status_pesanan = 'CANCELLED'
            self.save()
            return True
        return False

    def check_in(self):
        if self.status_pesanan != 'CONFIRMED':
            return False
        self.status_pesanan = 'CHECKED_IN'
        self.checked_in_at = timezone.now()
        self.save(update_fields=['status_pesanan', 'checked_in_at', 'updated_at'])
        return True

    def check_out(self):
        if self.status_pesanan != 'CHECKED_IN':
            return False
        self.status_pesanan = 'CHECKED_OUT'
        self.checked_out_at = timezone.now()
        self.save(update_fields=['status_pesanan', 'checked_out_at', 'updated_at'])
        self.room.status = 'DIRTY'
        self.room.save(update_fields=['status'])
        return True

#payment
class Payment(BaseTransaction):
    STATUS_PAYMENT = [
        ('UNPAID', 'Belum Dibayar'),
        ('PENDING_VERIFICATION', 'Menunggu Verifikasi'),
        ('VERIFIED', 'Terverifikasi'),
        ('REJECTED', 'Ditolak'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metode_pembayaran = models.CharField(max_length=30, db_column='method')
    bukti_transfer_url = models.ImageField(upload_to='bukti_transfer/', null=True, blank=True, db_column='proof')
    status_pembayaran = models.CharField(max_length=30, choices=STATUS_PAYMENT, default='UNPAID', db_column='status')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')

    class Meta:
        db_table = 'payments'

    def verifikasi_pembayaran(self, is_approved: bool):
        if is_approved:
            self.status_pembayaran = 'VERIFIED'
            self.booking.status_pesanan = 'CONFIRMED'
        else:
            self.status_pembayaran = 'REJECTED'
        self.save()
        self.booking.save()


class Review(BaseTransaction):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)

    class Meta:
        db_table = 'reviews'
        constraints = [
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name='review_rating_1_to_5'),
        ]