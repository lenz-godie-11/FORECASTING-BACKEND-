from datetime import date, timedelta

from django.test import TestCase

from src.models.obs import PatientObservation

OBS_URL = "/api/v1/obs/"


def payload(day_offset: int, patients: int = 42) -> dict:
    return {
        "date": (date.today() + timedelta(days=day_offset)).isoformat(),
        "patients": patients,
    }


class ObservationIngestionTests(TestCase):
    def test_ingest_creates_observation(self):
        response = self.client.post(OBS_URL, payload(-1), content_type="application/json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["created"])
        self.assertEqual(PatientObservation.objects.count(), 1)
        self.assertEqual(PatientObservation.objects.get().patients, 42)

    def test_duplicate_same_date_same_value_is_idempotent(self):
        self.client.post(OBS_URL, payload(-1), content_type="application/json")
        response = self.client.post(OBS_URL, payload(-1), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["created"])
        self.assertEqual(PatientObservation.objects.count(), 1)

    def test_conflicting_value_returns_409(self):
        self.client.post(OBS_URL, payload(-1, 42), content_type="application/json")
        response = self.client.post(OBS_URL, payload(-1, 99), content_type="application/json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(PatientObservation.objects.get().patients, 42)

    def test_future_date_rejected(self):
        response = self.client.post(OBS_URL, payload(1), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PatientObservation.objects.count(), 0)

    def test_negative_patients_rejected(self):
        response = self.client.post(OBS_URL, payload(-1, -5), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PatientObservation.objects.count(), 0)

    def test_invalid_date_rejected(self):
        body = {"date": "not-a-date", "patients": 1}
        response = self.client.post(OBS_URL, body, content_type="application/json")

        self.assertEqual(response.status_code, 400)
