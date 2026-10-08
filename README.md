# Hotel Management System

Hotel Management System berbasis Django.

## Tech Stack

- Python
- Django
- Django Templates
- Bootstrap
- SQLite (development)
- PostgreSQL (production)

## Setup

1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Run migration
5. Run development server

## Room Service Chatbot (Gemini)

- Page: `/room-service/` (requires login), API: `/room-service/api/chat/`
- Set your key before running (never commit it):
  - PowerShell: `$env:GEMINI_API_KEY="..."; $env:GEMINI_MODEL="gemini-3.8-flash"`
  - Optional: `GEMINI_MODEL` defaults to `gemini-2.0-flash`
- Get a key: https://aistudio.google.com/apikey
- Structured orders (food → reservation code → confirm) run server-side
  against your `bookings` table; Gemini is only the fallback for open Q&A.
- Troubleshoot the key/model without opening the browser:
  `python manage.py check_gemini` — verifies the key, lists usable models,
  and sends a test prompt. If the chat says the model was "not found",
  set `$env:GEMINI_MODEL` to one of the listed names.

## Verifikasi Pembayaran (untuk staf)

1. Buat akun admin (sekali saja): `python manage.py createsuperuser`
2. Buka `http://localhost:8000/admin/` dan login sebagai admin.
3. Alur tamu: buat reservasi → "Lanjutkan Pembayaran" → upload bukti
   transfer (status pembayaran menjadi `Menunggu Verifikasi`).
4. Alur staf: Admin → Payments → centang pembayaran → pilih aksi
   "Setujui pembayaran (booking → Confirmed)" → Go. Booking terkait
   otomatis menjadi `Confirmed`; aksi "Tolak pembayaran" menolaknya.