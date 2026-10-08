from django.test import TestCase


class HealthCheckTest(TestCase):
    def test_health_returns_ok(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'status': 'ok'})
