from django.db import models
from django.contrib.auth.models import User

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
        return self.kuota_penggunaan > 0 and total_transaksi >= self.minimal_transaksi

    def __str__(self):
        return self.kode_voucher

#kelas booking enkapsulasi dan abstraksi
class Booking(BaseTransaction):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Lunas'),
        ('CANCELLED', 'Dibatalkan'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(TemporaryRoom, on_delete=models.CASCADE)
    voucher = models.ForeignKey(PromoVoucher, on_delete=models.SET_NULL, null=True, blank=True)
    
    tanggal_check_in = models.DateTimeField()
    tanggal_check_out = models.DateTimeField()
    jumlah_tamu = models.IntegerField(default=1)
    
    #Enkapsulasi
    total_harga_dasar = models.FloatField(default=0.0)
    pajak_dan_layanan = models.FloatField(default=0.0)
    total_biaya_akhir = models.FloatField(default=0.0)
    status_pesanan = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')

    def hitung_total_biaya(self):
        """Abstraksi kalkulasi biaya"""
        durasi = (self.tanggal_check_out - self.tanggal_check_in).days
        if durasi <= 0: durasi = 1
        
        self.total_harga_dasar = self.room.harga_per_malam * durasi
        diskon = 0.0

        if self.voucher and self.voucher.is_valid(self.total_harga_dasar):
            diskon = (self.total_harga_dasar * (self.voucher.persen_diskon / 100)) if self.voucher.persen_diskon > 0 else self.voucher.potongan_nominal

        subtotal = max(0.0, self.total_harga_dasar - diskon)
        self.pajak_dan_layanan = subtotal * 0.11
        self.total_biaya_akhir = subtotal + self.pajak_dan_layanan
        self.save()

    def batalkan_pesanan(self):
        if self.status_pesanan != 'PAID':
            self.status_pesanan = 'CANCELLED'
            self.save()
            return True
        return False

#payment
class Payment(BaseTransaction):
    STATUS_PAYMENT = [
        ('WAITING', 'Menunggu Verifikasi'),
        ('VERIFIED', 'Terverifikasi'),
        ('REJECTED', 'Ditolak'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    metode_pembayaran = models.CharField(max_length=50)
    bukti_transfer_url = models.ImageField(upload_to='bukti_transfer/', null=True, blank=True)
    status_pembayaran = models.CharField(max_length=50, choices=STATUS_PAYMENT, default='WAITING')

    def verifikasi_pembayaran(self, is_approved: bool):
        if is_approved:
            self.status_pembayaran = 'VERIFIED'
            self.booking.status_pesanan = 'PAID'
        else:
            self.status_pembayaran = 'REJECTED'
        self.save()
        self.booking.save()