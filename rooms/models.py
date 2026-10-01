from django.db import models


class RoomType(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	capacity = models.PositiveIntegerField()
	price_per_night = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		db_table = 'room_types'
		ordering = ['price_per_night', 'name']

	def __str__(self):
		return self.name


class Room(models.Model):
	STATUS_CHOICES = [
		('CLEAN', 'Clean'),
		('DIRTY', 'Dirty'),
		('MAINTENANCE', 'Maintenance'),
	]

	room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='rooms')
	room_number = models.CharField(max_length=20, unique=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CLEAN')

	class Meta:
		db_table = 'rooms'
		ordering = ['room_number']

	def __str__(self):
		return f'{self.room_type.name} - {self.room_number}'
