from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import RoomType


class RoomTypeFeatureTests(TestCase):
	def test_admin_can_create_valid_room_type_data(self):
		room_type = RoomType.objects.create(
			name='Deluxe King',
			description='Kamar dengan tempat tidur king.',
			capacity=2,
			price_per_night=Decimal('1800000.00'),
		)

		self.assertEqual(str(room_type), 'Deluxe King')
		self.assertEqual(room_type.capacity, 2)

	def test_room_type_rejects_non_positive_capacity(self):
		room_type = RoomType(name='Invalid Capacity', capacity=0, price_per_night=Decimal('100000.00'))

		with self.assertRaises(ValidationError):
			room_type.full_clean()

	def test_room_type_rejects_non_positive_price(self):
		room_type = RoomType(name='Invalid Price', capacity=2, price_per_night=Decimal('0.00'))

		with self.assertRaises(ValidationError):
			room_type.full_clean()
