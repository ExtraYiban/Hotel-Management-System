from django.views.generic import TemplateView

from .models import Room


class RoomListView(TemplateView):
	template_name = 'rooms/room_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		room_defaults = [
			{
				'name': 'Kamar Deluxe King', 'label': 'SAYAP BARAT', 'price': '1.800.000',
				'total': '5.400.000', 'size': '38 m2', 'bed': '1 Kasur King', 'capacity': 'Maks 2 Tamu',
				'view': 'Pemandangan Halaman Dalam', 'badge': 'Tersedia - Sisa 3 Kamar',
				'image': 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=85',
				'features': ['Wi-Fi Kecepatan Tinggi', 'Termasuk Sarapan', 'Bathtub Rendam', 'Mesin Kopi Nespresso'],
			},
			{
				'name': 'Kamar Deluxe Twin', 'label': 'TOWER TIMUR', 'price': '1.700.000',
				'total': '5.100.000', 'size': '38 m2', 'bed': '2 Kasur Twin', 'capacity': 'Maks 2 Tamu',
				'view': 'Pemandangan Kota', 'badge': 'Tersedia - Sisa 2 Kamar',
				'image': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=85',
				'features': ['Wi-Fi Cepat', 'Shower Air Hangat', 'Meja Kerja Eksekutif', 'AC Pengatur Ganda'],
			},
			{
				'name': 'Suite Eksekutif Horizon', 'label': 'LANTAI ATAS', 'price': '3.200.000',
				'total': '9.600.000', 'size': '65 m2', 'bed': 'Kasur King + Sofa Bed', 'capacity': 'Maks 3 Tamu',
				'view': 'Pemandangan Laut Luas', 'badge': 'Pilihan Populer',
				'image': 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=85',
				'features': ['Akses Executive Lounge', 'Layanan Butler Khusus', 'Wine Sore Gratis', 'Minibar Kurasi'],
			},
			{
				'name': 'Villa Taman Kerajaan', 'label': 'AREA SANCTUARY KHUSUS', 'price': '4.800.000',
				'total': '14.400.000', 'size': '95 m2', 'bed': '2 Kasur King', 'capacity': 'Maks 4 Tamu',
				'view': 'Taman Halaman Privat', 'badge': 'Hanya Tersisa 1 Unit!',
				'image': 'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=85',
				'features': ['Jacuzzi Taman Privat', 'Layanan Makan di Villa 24 Jam', 'Antar-Jemput Bandara', 'Teras Kayu Jati'],
			},
		]
		database_rooms = list(Room.objects.select_related('room_type').all()[:4])
		for index, room in enumerate(database_rooms):
			room_defaults[index]['name'] = f'Kamar {room.room_number}'
			room_defaults[index]['price'] = f'{room.room_type.price_per_night:,.0f}'.replace(',', '.')
			room_defaults[index]['total'] = room_defaults[index]['price']
		context['rooms'] = room_defaults
		context['room_count'] = Room.objects.count() or len(room_defaults)
		return context


class RoomDetailView(TemplateView):
	template_name = 'rooms/room_detail.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		catalog = RoomListView().get_context_data()
		position = self.kwargs['room_id'] - 1
		rooms = catalog['rooms']
		context['room'] = rooms[position] if 0 <= position < len(rooms) else rooms[0]
		return context
