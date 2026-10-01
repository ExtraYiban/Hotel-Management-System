from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import GuestProfile


class GuestProfileInline(admin.StackedInline):
	model = GuestProfile
	extra = 0


class ManagedUserAdmin(UserAdmin):
	inlines = [GuestProfileInline]
	list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
	list_filter = ('is_staff', 'is_active')


admin.site.unregister(User)
admin.site.register(User, ManagedUserAdmin)
