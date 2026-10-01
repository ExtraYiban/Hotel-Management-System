from django.contrib import admin
from .models import Room, RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
	list_display = ('name', 'capacity', 'price_per_night')
	search_fields = ('name',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
	list_display = ('room_number', 'room_type', 'status')
	list_filter = ('status', 'room_type')
	search_fields = ('room_number', 'room_type__name')
