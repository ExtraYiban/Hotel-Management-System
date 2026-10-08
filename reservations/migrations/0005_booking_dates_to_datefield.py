# Generated to reconcile models with migrations 0002 (DateField intent).
# History: 0002 set DateField, 0004 flipped back to DateTimeField as
# makemigrations fallout. Booking dates are day-granularity everywhere
# (date inputs, availability filters), so DateField is the correct type.
from django.db import migrations, models


def normalize_dates(apps, schema_editor):
    # Kolom masih datetime saat migrasi ini jalan; pangkas komponen jam
    # supaya nilai lama tetap terbaca sebagai DATE sesudah AlterField.
    schema_editor.execute(
        'UPDATE bookings SET check_in_date = date(check_in_date),'
        ' check_out_date = date(check_out_date)'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_alter_booking_tanggal_check_in_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_dates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='booking',
            name='tanggal_check_in',
            field=models.DateField(db_column='check_in_date'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='tanggal_check_out',
            field=models.DateField(db_column='check_out_date'),
        ),
    ]
