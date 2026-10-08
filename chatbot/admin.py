from django.contrib import admin

from .models import ServiceOrder


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service_type', 'booking', 'status', 'created_at')
    list_filter = ('service_type', 'status')
    search_fields = ('user__username', 'detail')
