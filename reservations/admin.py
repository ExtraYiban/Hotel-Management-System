from django.contrib import admin
from django.utils import timezone

from .models import Booking, Payment, PromoVoucher, Review, TemporaryRoom

admin.site.register(TemporaryRoom)
admin.site.register(PromoVoucher)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'room', 'tanggal_check_in', 'tanggal_check_out', 'total_biaya_akhir', 'status_pesanan')
	list_filter = ('status_pesanan',)
	search_fields = ('user__username', 'room__room_number')
	ordering = ('-created_at',)
	actions = ('check_in_bookings',)

	@admin.action(description='Check-in booking terkonfirmasi')
	def check_in_bookings(self, request, queryset):
		checked_in = 0
		for booking in queryset:
			if booking.check_in():
				checked_in += 1
		self.message_user(request, f'{checked_in} booking berhasil check-in.')

	def save_model(self, request, obj, form, change):
		"""Mengubah status booking menjadi Confirmed juga memverifikasi
		pembayaran terkait yang masih menunggu, supaya kedua sisi
		(status tamu + status pembayaran) selalu konsisten."""
		old_status = None
		if change:
			old_status = Booking.objects.filter(pk=obj.pk).values_list('status_pesanan', flat=True).first()
		super().save_model(request, obj, form, change)
		if old_status != 'CONFIRMED' and obj.status_pesanan == 'CONFIRMED':
			try:
				payment = obj.payment
			except Payment.DoesNotExist:
				payment = None
			if payment is not None and payment.status_pembayaran in ('UNPAID', 'PENDING_VERIFICATION'):
				payment.status_pembayaran = 'VERIFIED'
				payment.verified_by = request.user
				payment.verified_at = timezone.now()
				payment.save()
				self.message_user(request, f'Pembayaran #{payment.pk} ikut terverifikasi otomatis.')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	"""Staf memverifikasi bukti transfer di sini.

	Centang pembayaran → pilih aksi "Setujui" / "Tolak" → Go.
	Menyetujui otomatis mengubah booking terkait menjadi Confirmed
	melalui Payment.verifikasi_pembayaran().
	"""
	list_display = ('id', 'booking', 'amount', 'metode_pembayaran', 'status_pembayaran', 'verified_by', 'verified_at')
	list_filter = ('status_pembayaran',)
	search_fields = ('booking__id', 'booking__user__username')
	readonly_fields = ('verified_by', 'verified_at')
	actions = ('setujui_pembayaran', 'tolak_pembayaran')

	def _verifikasi(self, request, queryset, disetujui):
		for payment in queryset.select_related('booking'):
			payment.verifikasi_pembayaran(disetujui)
			payment.verified_by = request.user
			payment.verified_at = timezone.now()
			payment.save(update_fields=['verified_by', 'verified_at'])
		hasil = 'disetujui' if disetujui else 'ditolak'
		self.message_user(request, f'{queryset.count()} pembayaran {hasil}.')

	@admin.action(description='Setujui pembayaran (booking → Confirmed)')
	def setujui_pembayaran(self, request, queryset):
		self._verifikasi(request, queryset, True)

	@admin.action(description='Tolak pembayaran')
	def tolak_pembayaran(self, request, queryset):
		self._verifikasi(request, queryset, False)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('booking', 'guest', 'rating', 'created_at')
	list_filter = ('rating',)
	search_fields = ('guest__email', 'booking__id')
