"""Diagnose Gemini API key / model problems.

Usage:
    python manage.py check_gemini

Reads GEMINI_API_KEY and GEMINI_MODEL from settings (i.e. from your
environment), lists the models your key can use, then probes the
chat-suitable text models with a tiny test prompt and reports which
ones actually answer.
"""
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

# Text-chat candidates, most stable first.
PREFERRED_TEXT_MODELS = [
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-3.5-flash-lite',
]

SKIP_KEYWORDS = (
    'tts', 'image', 'transcribe', 'lyria', 'robotics',
    'computer-use', 'deep-research', 'nano-banana', 'omni',
    'gemma', 'antigravity',
)


class Command(BaseCommand):
    help = 'Check Gemini API key validity and probe which text models answer.'

    def handle(self, *args, **options):
        key = getattr(settings, 'GEMINI_API_KEY', '')
        model = getattr(settings, 'GEMINI_MODEL', 'gemini-3.8-flash')
        self.stdout.write(f'GEMINI_MODEL = {model}')
        if not key:
            self.stderr.write('GEMINI_API_KEY is empty. Set it first.')
            return
        self.stdout.write(f'GEMINI_API_KEY = {key[:4]}...{key[-4:]} ({len(key)} chars)')
        if not key.startswith('AIza'):
            self.stdout.write(
                'Note: key has an uncommon prefix (classic AI Studio keys start '
                'with "AIza"; newer key types differ). Continuing...'
            )

        try:
            resp = requests.get(
                'https://generativelanguage.googleapis.com/v1beta/models',
                params={'key': key, 'pageSize': 100},
                timeout=20,
            )
        except requests.RequestException as exc:
            self.stderr.write(f'Network error reaching Google: {exc}')
            return
        if resp.status_code != 200:
            self.stderr.write(f'Key rejected ({resp.status_code}): {self._api_message(resp)}')
            self.stderr.write('Get a fresh key at https://aistudio.google.com/apikey')
            return

        usable = [
            m['name'].replace('models/', '')
            for m in resp.json().get('models', [])
            if 'generateContent' in m.get('supportedGenerationMethods', [])
        ]
        self.stdout.write(f'Key OK. {len(usable)} usable model(s) listed.')

        candidates = []
        for name in [model] + PREFERRED_TEXT_MODELS:
            if name in usable and name not in candidates:
                candidates.append(name)
        for name in usable:
            if ('flash' in name and name not in candidates
                    and not any(k in name for k in SKIP_KEYWORDS)):
                candidates.append(name)

        working = []
        for name in candidates:
            status, detail = self._probe(key, name)
            marker = '  <-- configured' if name == model else ''
            if status == 'ok':
                self.stdout.write(self.style.SUCCESS(f'  - {name}: OK{marker}'))
                working.append(name)
            else:
                self.stdout.write(f'  - {name}: {detail}{marker}')

        if model in working:
            self.stdout.write(self.style.SUCCESS('Configured model answers — chatbot AI will work.'))
        elif working:
            self.stdout.write(self.style.WARNING(
                f'Configured model "{model}" does not answer, but these do: '
                + ', '.join(working)
            ))
            self.stdout.write(
                f'Set $env:GEMINI_MODEL="{working[0]}", restart the server, done.'
            )
        else:
            self.stderr.write(
                'No text model answered (all overloaded or blocked). '
                'Wait a few minutes and re-run this check.'
            )

    def _probe(self, key, model):
        """Send a tiny test prompt; retry once on capacity errors."""
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        for attempt in (1, 2):
            try:
                resp = requests.post(
                    url,
                    params={'key': key},
                    json={'contents': [{'role': 'user', 'parts': [{'text': 'Balas hanya dengan: OK'}]}]},
                    timeout=20,
                )
            except requests.RequestException as exc:
                return ('error', f'network error: {exc}')
            if resp.status_code == 200:
                return ('ok', '')
            if resp.status_code in (429, 503) and attempt == 1:
                time.sleep(3)
                continue
            return ('fail', f'{resp.status_code}: {self._api_message(resp)}')
        return ('fail', 'no response')

    @staticmethod
    def _api_message(resp):
        try:
            return resp.json().get('error', {}).get('message', resp.text[:200])
        except ValueError:
            return resp.text[:200]
