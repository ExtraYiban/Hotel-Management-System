import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from .services import _gemini_error_detail, call_gemini, extract_booking_ref, food_cards, parse_food_items


class ChatbotServiceTest(TestCase):
    def test_parse_food_items(self):
        self.assertEqual(
            parse_food_items('Nasi Goreng 1, Mie Goreng 3'),
            {'Nasi Goreng': 1, 'Mie Goreng': 3},
        )
        self.assertEqual(parse_food_items('Nasi Goreng'), {'Nasi Goreng': 1})

    def test_extract_booking_ref(self):
        self.assertEqual(extract_booking_ref('GH-2024-4091'), 4091)
        self.assertEqual(extract_booking_ref('NH-0001'), 1)
        self.assertIsNone(extract_booking_ref('belum tahu'))

    def test_food_cards_have_images(self):
        cards = food_cards()
        self.assertEqual(len(cards), 3)
        for card in cards:
            self.assertTrue(card['image'].endswith('.jpg'))
            self.assertTrue(card['image'].startswith('/'))

    def test_availability_context_reflects_real_rooms(self):
        from datetime import timedelta

        from django.contrib.auth.models import User
        from rooms.models import Room
        from reservations.models import Booking
        from .services import get_hotel_context, hotel_today

        user = User.objects.create_user('tamu', password='p')
        room = Room.objects.order_by('room_number').first()
        today = hotel_today()
        Booking.objects.create(
            user=user, room=room,
            tanggal_check_in=today, tanggal_check_out=today + timedelta(days=1),
            jumlah_tamu=1, status_pesanan='CONFIRMED',
        )
        context = get_hotel_context()
        self.assertIn(f'Tanggal hari ini: {today:%d %b %Y}', context)
        self.assertIn(f'- {room.room_number} (', context)
        self.assertIn('TERPESAN hari ini', context)
        self.assertIn('TERSEDIA', context)
        self.assertIn('Check-in 14:00', context)

    def test_gemini_404_suggests_check_command(self):
        import requests

        fake = requests.Response()
        fake.status_code = 404
        fake._content = json.dumps(
            {'error': {'message': 'models/gemini-2.0-flash is not found for API version v1beta'}}
        ).encode()
        error = requests.HTTPError('404 Client Error', response=fake)
        with mock.patch('chatbot.services.requests.post', side_effect=error):
            with self.settings(GEMINI_API_KEY='AIza-test', GEMINI_MODEL='gemini-2.0-flash'):
                reply = call_gemini('halo')
        self.assertIn('check_gemini', reply)
        self.assertIn('gemini-2.0-flash', reply)

    def test_gemini_error_detail_prefers_api_message(self):
        import requests

        fake = requests.Response()
        fake.status_code = 400
        fake._content = json.dumps({'error': {'message': 'API key not valid.'}}).encode()
        error = requests.HTTPError('400 Client Error', response=fake)
        self.assertEqual(_gemini_error_detail(error), '400 API key not valid.')

    def test_gemini_overloaded_says_try_again(self):
        import requests

        fake = requests.Response()
        fake.status_code = 503
        fake._content = json.dumps(
            {'error': {'message': 'This model is currently experiencing high demand.'}}
        ).encode()
        error = requests.HTTPError('503 Server Error', response=fake)
        with mock.patch('chatbot.services.requests.post', side_effect=error):
            with self.settings(GEMINI_API_KEY='AIza-test'):
                reply = call_gemini('halo')
        self.assertIn('padat', reply)

    def test_gemini_retries_once_on_timeout_then_answers(self):
        import requests

        ok = requests.Response()
        ok.status_code = 200
        ok._content = json.dumps({'candidates': [
            {'content': {'parts': [{'text': 'Kamar tersedia!'}]}}
        ]}).encode()
        with mock.patch(
            'chatbot.services.requests.post',
            side_effect=[requests.ReadTimeout('timed out'), ok],
        ) as post:
            with self.settings(GEMINI_API_KEY='AIza-test'):
                reply = call_gemini('halo')
        self.assertEqual(reply, 'Kamar tersedia!')
        self.assertEqual(post.call_count, 2)

    def test_gemini_timeout_twice_says_slow(self):
        import requests

        with mock.patch(
            'chatbot.services.requests.post',
            side_effect=requests.ReadTimeout('timed out'),
        ) as post:
            with self.settings(GEMINI_API_KEY='AIza-test'):
                reply = call_gemini('halo')
        self.assertIn('tidak merespons tepat waktu', reply)
        self.assertEqual(post.call_count, 2)

    def test_check_gemini_reports_working_model(self):
        import io

        import requests
        from django.core.management import call_command

        def fake_response(status, payload):
            fake = requests.Response()
            fake.status_code = status
            fake._content = json.dumps(payload).encode()
            return fake

        list_payload = {'models': [
            {'name': 'models/gemini-3.8-flash', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/gemini-3.5-flash', 'supportedGenerationMethods': ['generateContent']},
        ]}

        def fake_post(url, **kwargs):
            if 'gemini-3.5-flash' in url:
                return fake_response(200, {'candidates': []})
            return fake_response(503, {'error': {'message': 'high demand'}})

        out = io.StringIO()
        with mock.patch(
            'chatbot.management.commands.check_gemini.requests.get',
            return_value=fake_response(200, list_payload),
        ), mock.patch(
            'chatbot.management.commands.check_gemini.requests.post',
            side_effect=fake_post,
        ), mock.patch('chatbot.management.commands.check_gemini.time.sleep'):
            with self.settings(GEMINI_API_KEY='AIza-test', GEMINI_MODEL='gemini-3.8-flash'):
                call_command('check_gemini', stdout=out)
        output = out.getvalue()
        self.assertIn('gemini-3.5-flash: OK', output)
        self.assertIn('gemini-3.5-flash', output.split('these do:')[-1])


class ChatbotMenuImageTest(TestCase):
    def test_food_menu_reply_includes_cards(self):
        User.objects.create_user('tamu', password='p')
        self.client.force_login(User.objects.get(username='tamu'))
        resp = self.client.post(
            '/room-service/api/chat/',
            data=json.dumps({'message': 'Pesan Makanan & Minuman', 'history': []}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn('cards', payload)
        self.assertEqual(
            [c['label'] for c in payload['cards']],
            ['Nasi Goreng', 'Mie Goreng', 'Ayam Bakar'],
        )


class ChatbotBookingStatusTest(TestCase):
    def _chat(self, message):
        return self.client.post(
            '/room-service/api/chat/',
            data=json.dumps({'message': message, 'history': []}),
            content_type='application/json',
        ).json()

    def setUp(self):
        from datetime import date

        from rooms.models import Room
        from reservations.models import Booking

        self.user = User.objects.create_user('tamu', password='p')
        self.client.force_login(self.user)
        room = Room.objects.order_by('room_number').first()
        self.booking = Booking.objects.create(
            user=self.user, room=room,
            tanggal_check_in=date(2026, 10, 9), tanggal_check_out=date(2026, 10, 10),
            jumlah_tamu=1,
        )

    def test_found_reply_shows_status(self):
        self._chat('Pesan Makanan & Minuman')
        self._chat('Nasi Goreng 1')
        payload = self._chat(f'NH-{self.booking.pk:04d}')
        self.assertIn('Status: Pending Payment', payload['reply'])

    def test_cancelled_booking_is_refused(self):
        self.booking.status_pesanan = 'CANCELLED'
        self.booking.save()
        self._chat('Pesan Makanan & Minuman')
        self._chat('Nasi Goreng 1')
        payload = self._chat(f'NH-{self.booking.pk:04d}')
        self.assertIn('dibatalkan', payload['reply'])
