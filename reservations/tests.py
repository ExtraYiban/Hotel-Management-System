from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from rooms.models import Room
from reservations.forms import BookingForm, ReviewForm
from reservations.models import Booking, Payment, PromoVoucher, Review


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

    def test_available_rooms_excludes_overlap_and_non_clean_room(self):
        from datetime import timedelta

        user = User.objects.create_user('booked-guest', password='p')
        rooms = list(Room.objects.order_by('room_number')[:3])
        rooms[1].status = 'MAINTENANCE'
        rooms[1].save()
        start = date(2026, 10, 9)
        end = start + timedelta(days=2)
        Booking.objects.create(
            user=user,
            room=rooms[0],
            tanggal_check_in=start,
            tanggal_check_out=end,
            jumlah_tamu=1,
            status_pesanan='CONFIRMED',
        )

        available = set(Booking.available_rooms(start, end).values_list('pk', flat=True))

        self.assertNotIn(rooms[0].pk, available)
        self.assertNotIn(rooms[1].pk, available)
        self.assertIn(rooms[2].pk, available)

    def test_booking_form_rejects_invalid_dates(self):
        room = Room.objects.order_by('room_number').first()
        form = BookingForm(data={
            'room': room.pk,
            'tanggal_check_in': '2026-10-12',
            'tanggal_check_out': '2026-10-11',
            'jumlah_tamu': 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Tanggal check-out harus setelah check-in.', form.non_field_errors())

    def test_booking_form_rejects_capacity_overflow(self):
        room = Room.objects.order_by('room_number').first()
        form = BookingForm(data={
            'room': room.pk,
            'tanggal_check_in': '2026-10-12',
            'tanggal_check_out': '2026-10-13',
            'jumlah_tamu': room.room_type.capacity + 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Kapasitas kamar maksimal', form.non_field_errors()[0])

    def test_booking_form_rejects_overlapping_room(self):
        user = User.objects.create_user('overlap-guest', password='p')
        room = Room.objects.order_by('room_number').first()
        Booking.objects.create(
            user=user,
            room=room,
            tanggal_check_in=date(2026, 10, 12),
            tanggal_check_out=date(2026, 10, 14),
            jumlah_tamu=1,
            status_pesanan='CONFIRMED',
        )
        form = BookingForm(data={
            'room': room.pk,
            'tanggal_check_in': '2026-10-13',
            'tanggal_check_out': '2026-10-15',
            'jumlah_tamu': 1,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('Kamar tidak tersedia pada periode tersebut.', form.non_field_errors())


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

    def test_second_payment_submission_is_rejected(self):
        Payment.objects.create(
            booking=self.booking, amount=self.booking.total_biaya_akhir,
            metode_pembayaran='Transfer Bank', status_pembayaran='PENDING_VERIFICATION',
        )

        response = self.client.post(
            f'/reservations/{self.booking.pk}/bayar/',
            {'metode_pembayaran': 'Transfer Bank'},
        )

        self.assertRedirects(response, f'/reservations/{self.booking.pk}/')
        self.assertEqual(Payment.objects.filter(booking=self.booking).count(), 1)

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


class BookingCheckInTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('checkin-guest', password='p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=room,
            tanggal_check_in=date(2026, 12, 15), tanggal_check_out=date(2026, 12, 16),
            jumlah_tamu=1, status_pesanan='CONFIRMED',
        )

    def test_confirmed_booking_can_check_in(self):
        self.assertTrue(self.booking.check_in())

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status_pesanan, 'CHECKED_IN')
        self.assertIsNotNone(self.booking.checked_in_at)

    def test_unconfirmed_booking_cannot_check_in(self):
        self.booking.status_pesanan = 'PENDING_PAYMENT'
        self.booking.save()

        self.assertFalse(self.booking.check_in())
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status_pesanan, 'PENDING_PAYMENT')


class BookingCheckOutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('checkout-guest', password='p')
        self.room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=self.room,
            tanggal_check_in=date(2026, 12, 20), tanggal_check_out=date(2026, 12, 21),
            jumlah_tamu=1, status_pesanan='CHECKED_IN',
        )

    def test_checked_in_booking_can_check_out_and_dirties_room(self):
        self.assertTrue(self.booking.check_out())

        self.booking.refresh_from_db()
        self.room.refresh_from_db()
        self.assertEqual(self.booking.status_pesanan, 'CHECKED_OUT')
        self.assertIsNotNone(self.booking.checked_out_at)
        self.assertEqual(self.room.status, 'DIRTY')

    def test_booking_not_checked_in_cannot_check_out(self):
        self.booking.status_pesanan = 'CONFIRMED'
        self.booking.save()

        self.assertFalse(self.booking.check_out())
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status_pesanan, 'CONFIRMED')


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

    def test_list_hides_other_guests_bookings(self):
        other_user = User.objects.create_user('other-history-guest', password='p')
        other_room = Room.objects.order_by('room_number').last()
        other_booking = Booking.objects.create(
            user=other_user,
            room=other_room,
            tanggal_check_in=date(2026, 12, 1),
            tanggal_check_out=date(2026, 12, 2),
            jumlah_tamu=1,
        )
        self.client.force_login(self.user)

        response = self.client.get('/reservations/riwayat/')

        self.assertContains(response, f'NH-{self.booking.pk:04d}')
        self.assertNotContains(response, f'NH-{other_booking.pk:04d}')

    def test_latest_redirects_to_detail(self):
        self.client.force_login(self.user)
        resp = self.client.get('/reservations/terakhir/')
        self.assertRedirects(resp, f'/reservations/{self.booking.pk}/')

    def test_latest_without_booking_goes_to_list(self):
        Booking.objects.all().delete()
        self.client.force_login(self.user)
        resp = self.client.get('/reservations/terakhir/')
        self.assertRedirects(resp, '/reservations/riwayat/')


class BookingDetailAccessTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='p')
        self.other_guest = User.objects.create_user('other', password='p')
        self.admin = User.objects.create_superuser('detail-admin', 'admin@test.com', 'p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.owner,
            room=room,
            tanggal_check_in=date(2026, 11, 1),
            tanggal_check_out=date(2026, 11, 2),
            jumlah_tamu=1,
        )

    def test_guest_cannot_view_another_guests_booking(self):
        self.client.force_login(self.other_guest)

        response = self.client.get(f'/reservations/{self.booking.pk}/')

        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_any_booking_detail(self):
        self.client.force_login(self.admin)

        response = self.client.get(f'/reservations/{self.booking.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'NH-{self.booking.pk:04d}')


class BookingCancellationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('cancel-guest', password='p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=room,
            tanggal_check_in=date(2026, 12, 10), tanggal_check_out=date(2026, 12, 11),
            jumlah_tamu=1,
        )
        self.client.force_login(self.user)

    def test_guest_can_cancel_pending_booking(self):
        response = self.client.post(f'/reservations/{self.booking.pk}/batal/')

        self.assertRedirects(response, f'/reservations/{self.booking.pk}/')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status_pesanan, 'CANCELLED')

    def test_checked_in_booking_cannot_be_cancelled(self):
        self.booking.status_pesanan = 'CHECKED_IN'
        self.booking.save()

        self.client.post(f'/reservations/{self.booking.pk}/batal/')

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status_pesanan, 'CHECKED_IN')


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


class ReviewFeatureTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('review-guest', password='p')
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=room,
            tanggal_check_in=date(2026, 12, 25), tanggal_check_out=date(2026, 12, 26),
            jumlah_tamu=1, status_pesanan='CHECKED_OUT',
        )
        self.client.force_login(self.user)

    def test_guest_can_submit_review_after_checkout(self):
        response = self.client.post(
            f'/reservations/{self.booking.pk}/review/',
            {'rating': 5, 'comment': 'Sangat nyaman.'},
        )

        self.assertRedirects(response, f'/reservations/{self.booking.pk}/')
        review = Review.objects.get(booking=self.booking)
        self.assertEqual(review.guest, self.user)
        self.assertEqual(review.rating, 5)

    def test_review_before_checkout_is_rejected(self):
        self.booking.status_pesanan = 'CONFIRMED'
        self.booking.save()

        response = self.client.get(f'/reservations/{self.booking.pk}/review/')

        self.assertRedirects(response, f'/reservations/{self.booking.pk}/')
        self.assertFalse(Review.objects.filter(booking=self.booking).exists())

    def test_duplicate_review_is_rejected(self):
        Review.objects.create(booking=self.booking, guest=self.user, rating=4, comment='Baik.')

        response = self.client.get(f'/reservations/{self.booking.pk}/review/')

        self.assertRedirects(response, f'/reservations/{self.booking.pk}/')

    def test_rating_must_be_between_one_and_five(self):
        form = ReviewForm(data={'rating': 6, 'comment': 'Invalid'})

        self.assertFalse(form.is_valid())
