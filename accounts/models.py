from django.db import models
from django.contrib.auth.models import User


class GuestProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guest_profile')
	phone_number = models.CharField(max_length=30)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.user.get_full_name() or self.user.email or self.user.username

