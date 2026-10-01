from django.views.generic import TemplateView

from reservations.models import Booking, TemporaryRoom


class DashboardView(TemplateView):
	template_name = 'dashboard/home.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		rooms = list(TemporaryRoom.objects.all()[:3])
		bookings = Booking.objects.select_related('room').order_by('-created_at')

		showcase_rooms = [
			{
				'name': 'Kamar Deluxe King',
				'eyebrow': 'Pilihan populer',
				'price': '1.800.000',
				'capacity': '2 tamu',
				'size': '38 m2',
				'view': 'Pemandangan kota',
				'image': 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1000&q=85',
				'description': 'Kamar hangat dengan jendela tinggi, tempat tidur king, dan ruang kerja yang tenang.',
			},
			{
				'name': 'Suite Eksekutif Horizon',
				'eyebrow': 'Suite unggulan',
				'price': '3.200.000',
				'capacity': '4 tamu',
				'size': '65 m2',
				'view': 'Kota dan matahari terbenam',
				'image': 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1000&q=85',
				'description': 'Suite luas dengan ruang duduk, bathtub, dan pemandangan kota dari ketinggian.',
			},
			{
				'name': 'Grand Suite Presidensial',
				'eyebrow': 'Eksklusif apex',
				'price': '5.500.000',
				'capacity': '4 tamu',
				'size': '110 m2',
				'view': 'Teras privat',
				'image': 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1000&q=85',
				'description': 'Ruang privat berkelas dengan teras luas, lounge, dan layanan personal sepanjang hari.',
			},
		]

		for index, room in enumerate(rooms):
			showcase_rooms[index]['database_room'] = room
			showcase_rooms[index]['price'] = f'{room.harga_per_malam:,.0f}'.replace(',', '.')

		context.update({
			'rooms': showcase_rooms,
			'recent_bookings': bookings[:4],
			'room_count': TemporaryRoom.objects.count(),
			'booking_count': Booking.objects.count(),
			'paid_booking_count': Booking.objects.filter(status_pesanan='PAID').count(),
		})
		return context
