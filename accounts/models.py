from django.db import models
from django.contrib.auth.models import User


class GuestProfile(models.Model):
	ROLE_CHOICES = [('GUEST', 'Guest'), ('ADMIN', 'Admin')]
	STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guest_profile')
	phone_number = models.CharField(max_length=30)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='GUEST')
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.user.get_full_name() or self.user.email or self.user.username

