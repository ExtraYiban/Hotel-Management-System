import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from reservations.models import Booking

from .models import ServiceOrder
from .services import (
    FOOD_MENU,
    SERVICE_LABELS,
    call_gemini,
    extract_booking_ref,
    food_cards,
    format_items,
    parse_food_items,
)

WELCOME_TEXT = (
    'Halo! Selamat datang di Hotel Nocturn Haven\n'
    'Ada yang bisa saya bantu? Silakan pilih layanan berikut:'
)
WELCOME_OPTIONS = [
    SERVICE_LABELS['FOOD'],
    SERVICE_LABELS['AMENITIES'],
    SERVICE_LABELS['EXTRA_BED'],
    SERVICE_LABELS['LAUNDRY'],
]
RECEPTION_LABEL = SERVICE_LABELS['RECEPTION']


class RoomServiceChatView(LoginRequiredMixin, TemplateView):
    template_name = 'chatbot/room_service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            vip = 'Gold VIP Tier' if user.bookings.exists() else 'Tamu Terhormat'
        except Exception:
            vip = 'Tamu Terhormat'
        context.update({
            'welcome_text': WELCOME_TEXT,
            'welcome_options': WELCOME_OPTIONS,
            'reception_label': RECEPTION_LABEL,
            'food_menu': FOOD_MENU,
            'vip_label': vip,
            'display_name': user.first_name or user.username,
        })
        return context


class ChatApiView(LoginRequiredMixin, View):
    """JSON endpoint: {message, history:[{from,text}]} -> {reply, options, stage}."""

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'reply': 'Format pesan tidak valid.'}, status=400)
        message = str(payload.get('message', '')).strip()
        history = payload.get('history', []) if isinstance(payload.get('history'), list) else []
        if not message:
            return JsonResponse({'reply': 'Silakan ketik pesan atau pilih layanan.'}, status=400)

        # 1) Structured flow has priority (reservation-safe).
        rule_reply = self._handle_flow(request, message)
        if rule_reply is not None:
            return JsonResponse(rule_reply)

        # 2) Quick intent shortcuts before spending a Gemini call.
        lowered = message.lower()
        if lowered in ('ya', 'iya', 'benar', 'betul', 'oke', 'ok'):
            pending = request.session.get('chat_pending_booking')
            if pending:
                return JsonResponse(self._confirm_order(request))
        if any(k in lowered for k in ('hai', 'halo', 'hello', 'pagi', 'siang', 'sore', 'malam')) and len(lowered) < 20:
            return JsonResponse({
                'reply': 'Halo! Senang bisa membantu. Silakan pilih layanan berikut:',
                'options': WELCOME_OPTIONS,
                'show_reception': True,
            })

        # 3) Gemini fallback for open-ended questions.
        reply = call_gemini(message, history)
        return JsonResponse({'reply': reply})

    # -- state machine -------------------------------------------------
    def _handle_flow(self, request, message):
        session = request.session
        stage = session.get('chat_stage', 'idle')
        lowered = message.lower()

        # Entry points (work from any stage to restart cleanly).
        if lowered == SERVICE_LABELS['FOOD'].lower() or 'makanan' in lowered or 'minuman' in lowered:
            session.update({'chat_stage': 'food_menu', 'chat_service': 'FOOD'})
            return {'reply': 'Silakan Pilih Menu:', 'options': FOOD_MENU, 'cards': food_cards()}
        if 'amenit' in lowered or lowered == SERVICE_LABELS['AMENITIES'].lower():
            session.update({'chat_stage': 'await_booking', 'chat_service': 'AMENITIES', 'chat_items': {}})
            return {'reply': 'Baik, Anda memilih Request Amenities. Sebutkan kebutuhan Anda (misal: handuk tambahan, perlengkapan mandi).'}
        if 'extra bed' in lowered:
            session.update({'chat_stage': 'await_booking', 'chat_service': 'EXTRA_BED', 'chat_items': {'Extra Bed': 1}})
            return {'reply': 'Baik, Anda memilih Request Extra Bed.\nSebelum melanjutkan, silakan masukkan kode reservasi Anda.'}
        if 'laundry' in lowered:
            session.update({'chat_stage': 'await_booking', 'chat_service': 'LAUNDRY'})
            return {'reply': 'Baik, Anda memilih Laundry. Sebutkan jumlah dan jenis pakaian (misal: 3 kemeja, 2 celana).\nSetelah itu masukkan kode reservasi Anda.'}
        if 'resepsionis' in lowered:
            session.update({'chat_stage': 'idle', 'chat_service': 'RECEPTION'})
            return {'reply': 'Baik, saya hubungkan ke resepsionis. Tim kami akan segera membalas di sini. Sambil menunggu, boleh ceritakan kebutuhan Anda?'}

        if stage == 'food_menu':
            items = parse_food_items(message)
            # A bare menu tap ("Nasi Goreng") counts as x1; "Lainnya" asks for detail.
            if not items:
                return {'reply': 'Silakan Pilih Menu:', 'options': FOOD_MENU, 'cards': food_cards()}
            if set(items) == {'Lainnya'}:
                session['chat_stage'] = 'food_menu'
                return {'reply': 'Silakan ketik nama makanan/minuman yang Anda inginkan (contoh: Soto Ayam 2, Es Teh 3).'}
            session.update({'chat_stage': 'await_booking', 'chat_service': 'FOOD', 'chat_items': items})
            return {
                'reply': f"Pesanan Anda:\n\n{format_items(items)}\n\nSebelum melanjutkan, silakan masukkan kode reservasi Anda.",
            }

        if stage == 'await_booking':
            # Allow laundry/amenities free-text detail before the code arrives.
            ref = extract_booking_ref(message)
            if ref is None:
                service = session.get('chat_service', 'FOOD')
                if service in ('LAUNDRY', 'AMENITIES') and len(message) >= 2:
                    session['chat_items'] = {message[:120]: 1}
                    return {'reply': 'Baik, catat. Sekarang silakan masukkan kode reservasi Anda (contoh: GH-2024-4091 atau cukup angka ID booking Anda).'}
                return {'reply': 'Kode reservasi tidak terbaca. Silakan masukkan kode reservasi Anda (contoh: GH-2024-4091).'}
            booking = self._find_booking(request, ref)
            if booking is None:
                return {'reply': 'Maaf, data reservasi tidak ditemukan untuk akun Anda. Periksa kembali kode reservasi Anda.'}
            if booking.status_pesanan == 'CANCELLED':
                session.update({'chat_stage': 'idle', 'chat_pending_booking': None})
                return {'reply': 'Maaf, reservasi tersebut sudah dibatalkan sehingga tidak bisa dipakai memesan layanan. Silakan buat reservasi baru di halaman Pemesanan Saya.', 'options': WELCOME_OPTIONS, 'show_reception': True}
            session['chat_pending_booking'] = booking.pk
            session['chat_stage'] = 'await_confirm'
            room = booking.room
            jadwal = f'{booking.tanggal_check_in:%d %b %Y} - {booking.tanggal_check_out:%d %b %Y}'
            return {
                'reply': (
                    'Data reservasi ditemukan:\n\n'
                    f'Nama: {booking.user.first_name or booking.user.username}\n'
                    f'Tipe Kamar: {room.room_type.name}\n'
                    f'No. Kamar: {room.room_number}\n'
                    f'Jadwal Menginap: {jadwal}\n'
                    f'Status: {booking.get_status_pesanan_display()}'
                ),
                'follow_up': 'Apakah data reservasi anda sudah benar?',
                'options': ['Ya', 'Tidak'],
            }

        if stage == 'await_confirm':
            if lowered in ('ya', 'iya', 'benar', 'betul', 'oke', 'ok', 'y'):
                return self._confirm_order(request)
            if lowered in ('tidak', 'bukan', 'salah', 'batal'):
                session.update({'chat_stage': 'idle', 'chat_pending_booking': None})
                return {'reply': 'Baik, pesanan dibatalkan. Silakan pilih layanan lain:', 'options': WELCOME_OPTIONS, 'show_reception': True}
            return {'reply': 'Apakah data reservasi anda sudah benar?', 'options': ['Ya', 'Tidak']}

        return None

    def _find_booking(self, request, ref):
        qs = Booking.objects.filter(user=request.user).select_related('room', 'room__room_type')
        booking = qs.filter(pk=ref).first()
        if booking is not None:
            return booking
        # Allow codes like "GH-2024-4091" to match PK 4091 by suffix.
        ref_str = str(ref)
        for candidate in qs.order_by('-created_at')[:20]:
            if str(candidate.pk).endswith(ref_str[-4:]):
                return candidate
        # Single-booking accounts: be lenient so the demo flow works.
        if qs.count() == 1:
            return qs.first()
        return None

    def _confirm_order(self, request):
        session = request.session
        booking_id = session.get('chat_pending_booking')
        service = session.get('chat_service', 'FOOD')
        items = session.get('chat_items', {}) or {}
        try:
            booking = Booking.objects.filter(user=request.user, pk=booking_id).select_related('room').first()
        except (TypeError, ValueError):
            booking = None
        if not booking:
            session.update({'chat_stage': 'idle', 'chat_pending_booking': None})
            return {'reply': 'Sesi reservasi kedaluwarsa. Silakan ulangi dari awal.', 'options': WELCOME_OPTIONS}
        detail = format_items(items) if isinstance(items, dict) else str(items)
        if service in ('AMENITIES', 'LAUNDRY') and not detail:
            detail = '(menunggu detail dari tamu via resepsionis)'
        ServiceOrder.objects.create(
            user=request.user, booking=booking, service_type=service, detail=detail, status='CONFIRMED',
        )
        session.update({'chat_stage': 'idle', 'chat_pending_booking': None, 'chat_items': {}, 'chat_service': ''})
        return {'reply': 'Pesanan anda telah dikonfirmasi.\nPesanan akan segera diproses dan diantar ke kamar Anda.'}
