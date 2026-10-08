from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from rooms.models import Room
from reservations.forms import BookingForm
from reservations.models import Booking, Payment, PromoVoucher


class BookingFormSeedTest(TestCase):
    def test_room_and_voucher_dropdowns_have_options(self):
        self.assertGreater(Room.objects.count(), 0)
        self.assertGreater(PromoVoucher.objects.count(), 0)
        form = BookingForm()
        room_values = [str(choice[0]) for choice in form.fields['room'].choices if choice[0]]
        self.assertTrue(room_values)
        voucher_labels = [choice[1] for choice in form.fields['voucher'].choices]
        self.assertIn('— Tanpa voucher —', voucher_labels)
        self.assertFalse(form.fields['voucher'].required)

    def test_booking_page_renders_options(self):
        User.objects.create_user('tamu', password='p')
        self.client.force_login(User.objects.get(username='tamu'))
        resp = self.client.get('/reservations/buat/')
        first_room = Room.objects.order_by('room_number').first()
        self.assertContains(resp, first_room.room_number)
        self.assertContains(resp, PromoVoucher.objects.order_by('kode_voucher').first().kode_voucher)


class PaymentVerificationFlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tamu', password='p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=room,
            tanggal_check_in=date(2026, 10, 9), tanggal_check_out=date(2026, 10, 10),
            jumlah_tamu=1,
        )
        self.booking.hitung_total_biaya()
        self.client.force_login(self.user)

    def test_pay_button_visible_while_pending(self):
        resp = self.client.get(f'/reservations/{self.booking.pk}/')
        self.assertContains(resp, 'Lanjutkan Pembayaran')

    def test_upload_sets_pending_verification(self):
        resp = self.client.post(
            f'/reservations/{self.booking.pk}/bayar/',
            {'metode_pembayaran': 'Transfer Bank'},
        )
        self.assertEqual(resp.status_code, 302)
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.status_pembayaran, 'PENDING_VERIFICATION')
        self.assertEqual(payment.amount, self.booking.total_biaya_akhir)

    def test_approve_confirms_booking(self):
        payment = Payment.objects.create(
            booking=self.booking, amount=self.booking.total_biaya_akhir,
            metode_pembayaran='Transfer Bank', status_pembayaran='PENDING_VERIFICATION',
        )
        payment.verifikasi_pembayaran(True)
        self.booking.refresh_from_db()
        self.assertEqual(payment.status_pembayaran, 'VERIFIED')
        self.assertEqual(self.booking.status_pesanan, 'CONFIRMED')

    def test_reject_keeps_booking_pending(self):
        payment = Payment.objects.create(
            booking=self.booking, amount=self.booking.total_biaya_akhir,
            metode_pembayaran='Transfer Bank', status_pembayaran='PENDING_VERIFICATION',
        )
        payment.verifikasi_pembayaran(False)
        self.booking.refresh_from_db()
        self.assertEqual(payment.status_pembayaran, 'REJECTED')
        self.assertEqual(self.booking.status_pesanan, 'PENDING_PAYMENT')


class BookingHistoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tamu', password='p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=room,
            tanggal_check_in=date(2026, 10, 9), tanggal_check_out=date(2026, 10, 10),
            jumlah_tamu=1,
        )
        self.booking.hitung_total_biaya()

    def test_list_requires_login(self):
        self.client.logout()
        resp = self.client.get('/reservations/riwayat/')
        self.assertEqual(resp.status_code, 302)

    def test_list_shows_own_bookings(self):
        self.client.force_login(self.user)
        resp = self.client.get('/reservations/riwayat/')
        self.assertContains(resp, f'NH-{self.booking.pk:04d}')
        self.assertContains(resp, self.booking.room.room_number)

    def test_latest_redirects_to_detail(self):
        self.client.force_login(self.user)
        resp = self.client.get('/reservations/terakhir/')
        self.assertRedirects(resp, f'/reservations/{self.booking.pk}/')

    def test_latest_without_booking_goes_to_list(self):
        Booking.objects.all().delete()
        self.client.force_login(self.user)
        resp = self.client.get('/reservations/terakhir/')
        self.assertRedirects(resp, '/reservations/riwayat/')


class BookingAdminPropagationTest(TestCase):
    def test_confirm_in_admin_verifies_payment(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        from reservations.admin import BookingAdmin

        staff = User.objects.create_superuser('staf', 'staf@test.com', 'p')
        user = User.objects.create_user('tamu', password='p')
        room = Room.objects.order_by('room_number').first()
        booking = Booking.objects.create(
            user=user, room=room,
            tanggal_check_in=date(2026, 10, 9), tanggal_check_out=date(2026, 10, 10),
            jumlah_tamu=1,
        )
        payment = Payment.objects.create(
            booking=booking, amount=100000, metode_pembayaran='Transfer Bank',
            status_pembayaran='PENDING_VERIFICATION',
        )
        booking.status_pesanan = 'CONFIRMED'
        request = RequestFactory().post('/admin/')
        request.user = staff
        from django.contrib.messages.storage.cookie import CookieStorage
        request._messages = CookieStorage(request)
        BookingAdmin(Booking, AdminSite()).save_model(request, booking, form=None, change=True)
        payment.refresh_from_db()
        self.assertEqual(payment.status_pembayaran, 'VERIFIED')
        self.assertEqual(payment.verified_by, staff)
        self.assertIsNotNone(payment.verified_at)
