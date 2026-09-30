from django.contrib import admin
from .models import Room, RoomType, RoomAvailability


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_night', 'capacity', 'size_m2')
    search_fields = ('name',)


class RoomAvailabilityInline(admin.TabularInline):
    model = RoomAvailability
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'room_type', 'floor', 'status', 'is_active')
    list_filter = ('room_type', 'status', 'is_active', 'floor')
    list_editable = ('status', 'is_active')
    search_fields = ('number',)
    inlines = [RoomAvailabilityInline]


@admin.register(RoomAvailability)
class RoomAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('room', 'date', 'is_available', 'note')
    list_filter = ('is_available', 'date', 'room__room_type')
    date_hierarchy = 'date'
