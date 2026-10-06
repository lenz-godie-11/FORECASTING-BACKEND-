from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase

from src.models.obs import PatientObservation

OBS_URL = "/api/v1/obs/"

STAFF_PASSWORD = "staff-password-123"


def payload(day_offset: int, patients: int = 42) -> dict:
    return {
        "date": (date.today() + timedelta(days=day_offset)).isoformat(),
        "patients": patients,
    }


def staff_headers(client, role: str = "MANAGER") -> dict:
    user = User.objects.create_user(
        username=f"staff-{role.lower()}",
        password=STAFF_PASSWORD,
    )
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)

    response = client.post(
        "/api/v1/auth/login/",
        {"username": user.username, "password": STAFF_PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content

    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


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


class ObservationReadTests(TestCase):
    def test_get_empty_returns_empty_list(self):
        response = self.client.get(OBS_URL, **staff_headers(self.client))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"], [])

    def test_get_returns_ordered_observations(self):
        self.client.post(OBS_URL, payload(-2, 100), content_type="application/json")
        self.client.post(OBS_URL, payload(-1, 200), content_type="application/json")

        response = self.client.get(OBS_URL, **staff_headers(self.client))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["data"][0]["date"], (date.today() - timedelta(days=2)).isoformat())
        self.assertEqual(data["data"][0]["patients"], 100)
        self.assertEqual(data["data"][1]["date"], (date.today() - timedelta(days=1)).isoformat())
        self.assertEqual(data["data"][1]["patients"], 200)

    def test_get_requires_authentication(self):
        response = self.client.get(OBS_URL)

        self.assertEqual(response.status_code, 401)
