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


@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'email', 'phone_number', 'role', 'status', 'created_at')
	list_filter = ('role', 'status')
	list_editable = ('role', 'status')
	search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')

	@admin.display(description='Email')
	def email(self, obj):
		return obj.user.email

	def save_model(self, request, obj, form, change):
		obj.user.is_active = obj.status == 'ACTIVE'
		obj.user.save(update_fields=['is_active'])
		super().save_model(request, obj, form, change)
