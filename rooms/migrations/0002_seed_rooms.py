"""Seed room types + rooms so the booking form dropdowns are usable.

Runs only on an empty database; safe to keep in history.
"""
from decimal import Decimal

from django.db import migrations


ROOM_TYPES = [
    {
        'name': 'Kamar Deluxe King',
        'description': 'Kamar hangat dengan tempat tidur king dan ruang kerja yang tenang.',
        'capacity': 2,
        'price_per_night': Decimal('1800000'),
    },
    {
        'name': 'Kamar Deluxe Twin',
        'description': 'Dua kasur twin dengan pemandangan kota, cocok untuk rekan perjalanan.',
        'capacity': 2,
        'price_per_night': Decimal('1700000'),
    },
    {
        'name': 'Suite Eksekutif Horizon',
        'description': 'Suite luas dengan ruang duduk dan pemandangan kota dari ketinggian.',
        'capacity': 3,
        'price_per_night': Decimal('3200000'),
    },
]

ROOMS = [
    ('401', 'Kamar Deluxe King'),
    ('402', 'Kamar Deluxe King'),
    ('301', 'Kamar Deluxe Twin'),
    ('302', 'Kamar Deluxe Twin'),
    ('501', 'Suite Eksekutif Horizon'),
]


def seed_rooms(apps, schema_editor):
    RoomType = apps.get_model('rooms', 'RoomType')
    Room = apps.get_model('rooms', 'Room')
    if RoomType.objects.exists() or Room.objects.exists():
        return
    types = {}
    for spec in ROOM_TYPES:
        types[spec['name']] = RoomType.objects.create(**spec)
    for number, type_name in ROOMS:
        Room.objects.create(room_number=number, room_type=types[type_name], status='CLEAN')


def unseed_rooms(apps, schema_editor):
    Room = apps.get_model('rooms', 'Room')
    RoomType = apps.get_model('rooms', 'RoomType')
    Room.objects.filter(room_number__in=[n for n, _ in ROOMS]).delete()
    RoomType.objects.filter(name__in=[t['name'] for t in ROOM_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_rooms, unseed_rooms),
    ]
