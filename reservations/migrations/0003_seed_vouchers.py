"""Seed demo promo vouchers so the booking form voucher dropdown is usable.

Runs only when no voucher exists yet.
"""
import datetime

from django.db import migrations


VOUCHERS = [
    {
        'kode_voucher': 'HEMAT10',
        'persen_diskon': 10.0,
        'potongan_nominal': 0.0,
        'minimal_transaksi': 0.0,
        'kuota_penggunaan': 100,
    },
    {
        'kode_voucher': 'STAY20',
        'persen_diskon': 20.0,
        'potongan_nominal': 0.0,
        'minimal_transaksi': 2000000.0,
        'kuota_penggunaan': 50,
    },
]

EXPIRY = datetime.datetime(2027, 12, 31, tzinfo=datetime.timezone.utc)


def seed_vouchers(apps, schema_editor):
    PromoVoucher = apps.get_model('reservations', 'PromoVoucher')
    if PromoVoucher.objects.exists():
        return
    for spec in VOUCHERS:
        PromoVoucher.objects.create(tanggal_kedaluwarsa=EXPIRY, **spec)


def unseed_vouchers(apps, schema_editor):
    PromoVoucher = apps.get_model('reservations', 'PromoVoucher')
    PromoVoucher.objects.filter(
        kode_voucher__in=[v['kode_voucher'] for v in VOUCHERS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0002_review_payment_amount_payment_verified_at_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_vouchers, unseed_vouchers),
    ]
