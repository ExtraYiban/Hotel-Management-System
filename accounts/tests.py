from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import GuestProfile


class AccountFeatureTests(TestCase):
	def register_data(self, email='guest@example.com'):
		return {
			'full_name': 'Guest Example',
			'email': email,
			'phone_number': '08123456789',
			'password1': 'StrongPassword123!',
			'password2': 'StrongPassword123!',
		}

	def test_guest_can_register_with_profile(self):
		response = self.client.post(reverse('register'), self.register_data())

		self.assertRedirects(response, reverse('home'))
		user = User.objects.get(email='guest@example.com')
		self.assertEqual(user.guest_profile.role, 'GUEST')
		self.assertEqual(user.guest_profile.status, 'ACTIVE')

	def test_duplicate_email_is_rejected(self):
		self.client.post(reverse('register'), self.register_data())
		response = self.client.post(reverse('register'), self.register_data())

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Email tersebut sudah terdaftar.')
		self.assertEqual(User.objects.filter(email='guest@example.com').count(), 1)

	def test_inactive_guest_cannot_login(self):
		user = User.objects.create_user(username='guest@example.com', email='guest@example.com', password='StrongPassword123!')
		GuestProfile.objects.create(user=user, phone_number='08123456789', status='INACTIVE')

		response = self.client.post(reverse('login'), {
			'username': 'guest@example.com',
			'password': 'StrongPassword123!',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Akun Anda sedang dinonaktifkan.')

	def test_guest_login_and_logout(self):
		user = User.objects.create_user(username='guest@example.com', email='guest@example.com', password='StrongPassword123!')
		GuestProfile.objects.create(user=user, phone_number='08123456789')

		login_response = self.client.post(reverse('login'), {
			'username': 'guest@example.com',
			'password': 'StrongPassword123!',
		})
		logout_response = self.client.post(reverse('logout'))

		self.assertRedirects(login_response, reverse('home'))
		self.assertRedirects(logout_response, reverse('home'))

	def test_admin_login_redirects_to_admin(self):
		admin = User.objects.create_user(username='admin@example.com', email='admin@example.com', password='StrongPassword123!', is_staff=True, is_superuser=True)

		response = self.client.post(reverse('login'), {
			'username': admin.email,
			'password': 'StrongPassword123!',
		})

		self.assertRedirects(response, reverse('admin:index'))
