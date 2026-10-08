from django.test import TestCase

from datetime import date
from django.contrib.auth.models import User

from reservations.models import Booking, Payment
from rooms.models import Room


class HealthCheckTest(TestCase):
    def test_health_returns_ok(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'status': 'ok'})


class ReportFeatureTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('report-admin', 'report@test.com', 'p')
        self.guest = User.objects.create_user('report-guest', password='p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.guest, room=room,
            tanggal_check_in=date(2027, 1, 1), tanggal_check_out=date(2027, 1, 2),
            jumlah_tamu=1, status_pesanan='CONFIRMED',
        )
        Payment.objects.create(
            booking=self.booking, amount=100000, metode_pembayaran='Transfer Bank',
            status_pembayaran='VERIFIED',
        )

    def test_report_requires_admin(self):
        self.client.force_login(self.guest)

        response = self.client.get('/dashboard/laporan/')

        self.assertEqual(response.status_code, 403)

    def test_admin_can_see_operational_summary(self):
        self.client.force_login(self.admin)

        response = self.client.get('/dashboard/laporan/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_bookings'], 1)
        self.assertEqual(response.context['confirmed_bookings'], 1)
        self.assertEqual(response.context['verified_payments'], 1)
