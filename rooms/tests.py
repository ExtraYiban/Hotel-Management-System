from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from .models import Room, RoomType


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

	def test_room_type_can_be_updated(self):
		room_type = RoomType.objects.create(name='Standard', capacity=2, price_per_night=Decimal('900000.00'))
		room_type.name = 'Standard Plus'
		room_type.capacity = 3
		room_type.save()

		room_type.refresh_from_db()
		self.assertEqual(room_type.name, 'Standard Plus')
		self.assertEqual(room_type.capacity, 3)

	def test_room_type_in_use_cannot_be_deleted(self):
		room_type = RoomType.objects.create(name='Used Type', capacity=2, price_per_night=Decimal('900000.00'))
		Room.objects.create(room_type=room_type, room_number='901')

		with self.assertRaises(ProtectedError):
			room_type.delete()
