from django.contrib import admin
from .models import Booking, Payment, PromoVoucher, Review, TemporaryRoom

admin.site.register(TemporaryRoom)
admin.site.register(PromoVoucher)
admin.site.register(Booking)
admin.site.register(Payment)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('booking', 'guest', 'rating', 'created_at')
	list_filter = ('rating',)
	search_fields = ('guest__email', 'booking__id')