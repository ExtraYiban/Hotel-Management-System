from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Room, RoomType, RoomAvailability


def room_list(request):
    room_types = RoomType.objects.all()
    rooms = Room.objects.filter(is_active=True).select_related('room_type')

    selected_type = request.GET.get('type')
    if selected_type:
        rooms = rooms.filter(room_type_id=selected_type)

    selected_status = request.GET.get('status')
    if selected_status:
        rooms = rooms.filter(status=selected_status)

    guests = request.GET.get('guests', '')
    if guests.isdigit():
        rooms = rooms.filter(room_type__capacity__gte=int(guests))

    check_in_raw = request.GET.get('check_in', '')
    check_out_raw = request.GET.get('check_out', '')
    check_in = parse_date(check_in_raw) if check_in_raw else None
    check_out = parse_date(check_out_raw) if check_out_raw else None

    if check_in and check_out and check_out > check_in:
        blocked_ids = RoomAvailability.objects.filter(
            date__gte=check_in, date__lt=check_out, is_available=False
        ).values_list('room_id', flat=True)
        rooms = rooms.exclude(id__in=blocked_ids).exclude(status='maintenance')

    context = {
        'rooms': rooms,
        'room_types': room_types,
        'selected_type': selected_type,
        'selected_status': selected_status,
        'check_in': check_in_raw,
        'check_out': check_out_raw,
        'guests': guests,
    }
    return render(request, 'rooms/room_list.html', context)


def room_detail(request, pk):
    room = get_object_or_404(
        Room.objects.select_related('room_type'), pk=pk, is_active=True
    )

    today = timezone.localdate()
    end = today + timedelta(days=14)
    blocked = {
        a.date: a
        for a in room.availabilities.filter(
            date__gte=today, date__lt=end, is_available=False
        )
    }
    calendar = []
    for i in range(14):
        d = today + timedelta(days=i)
        entry = blocked.get(d)
        calendar.append({
            'date': d,
            'available': entry is None,
            'note': entry.note if entry else '',
        })

    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'calendar': calendar,
    })