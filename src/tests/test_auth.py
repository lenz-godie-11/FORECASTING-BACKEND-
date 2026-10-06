from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase

from src.auth.roles import ADMIN, MANAGER
from src.models.obs import PatientObservation

LOGIN_URL = "/api/v1/auth/login/"
FORECAST_URL = "/api/v1/forecast/"
OBS_URL = "/api/v1/obs/"

STAFF_PASSWORD = "staff-password-123"


def make_user(username: str, role: str | None = None, active: bool = True) -> User:
    user = User.objects.create_user(
        username=username,
        password=STAFF_PASSWORD,
        is_active=active,
    )

    if role:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

    return user


def login(client, username: str):
    return client.post(
        LOGIN_URL,
        {"username": username, "password": STAFF_PASSWORD},
        content_type="application/json",
    )


def staff_headers(client, role: str = MANAGER, username: str = "staff") -> dict:
    user = make_user(username, role=role)
    response = login(client, user.username)
    assert response.status_code == 200, response.content

    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


def seed_observations(days: int = 90):
    end = date.today()
    for i in range(days):
        PatientObservation.objects.create(
            date=end - timedelta(days=days - 1 - i),
            patients=100 + 10 * (i % 7),
        )


class LoginTests(TestCase):
    def test_manager_login_returns_tokens(self):
        user = make_user("manager", role=MANAGER)

        response = login(self.client, user.username)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["username"], "manager")
        self.assertEqual(data["role"], MANAGER)
        self.assertIn("access", data)
        self.assertIn("refresh", data)

    def test_admin_login_returns_admin_role(self):
        user = make_user("admin", role=ADMIN)

        response = login(self.client, user.username)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], ADMIN)

    def test_admin_role_preferred_when_both_roles_present(self):
        user = make_user("dual", role=MANAGER)
        admin_group, _ = Group.objects.get_or_create(name=ADMIN)
        user.groups.add(admin_group)

        response = login(self.client, user.username)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], ADMIN)

    def test_invalid_credentials_return_401(self):
        make_user("manager", role=MANAGER)

        response = self.client.post(
            LOGIN_URL,
            {"username": "manager", "password": "wrong-password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_unknown_user_returns_401(self):
        response = self.client.post(
            LOGIN_URL,
            {"username": "ghost", "password": "any-password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_missing_fields_return_400(self):
        response = self.client.post(
            LOGIN_URL, data="{}", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    def test_non_staff_user_rejected(self):
        make_user("plain", role=None)

        response = login(self.client, "plain")

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_inactive_user_rejected(self):
        make_user("dormant", role=MANAGER, active=False)

        response = login(self.client, "dormant")

        self.assertEqual(response.status_code, 401)


class ForecastRetrievalAuthTests(TestCase):
    def test_unauthenticated_latest_forecast_returns_401(self):
        response = self.client.get(FORECAST_URL)

        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_run_forecast_returns_401(self):
        seed_observations()
        self.client.post(FORECAST_URL, data="{}", content_type="application/json")

        response = self.client.get(f"{FORECAST_URL}1/")

        self.assertEqual(response.status_code, 401)

    def test_malformed_token_returns_401(self):
        response = self.client.get(
            FORECAST_URL,
            **{"HTTP_AUTHORIZATION": "Bearer not-a-jwt"},
        )

        self.assertEqual(response.status_code, 401)

    def test_authenticated_latest_forecast_returns_200(self):
        seed_observations()
        self.client.post(FORECAST_URL, data="{}", content_type="application/json")

        response = self.client.get(FORECAST_URL, **staff_headers(self.client))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["run"]["model"], "ThetaModel")
        self.assertEqual(len(data["points"]), 90)

    def test_authenticated_specific_run_returns_200(self):
        seed_observations()
        trigger_result = self.client.post(
            FORECAST_URL, data="{}", content_type="application/json"
        )
        run_id = trigger_result.json()["run_id"]

        response = self.client.get(
            f"{FORECAST_URL}{run_id}/", **staff_headers(self.client)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run"]["id"], run_id)

    def test_authenticated_unknown_run_returns_404(self):
        response = self.client.get(
            f"{FORECAST_URL}99999/", **staff_headers(self.client)
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_can_retrieve_forecast(self):
        seed_observations()
        self.client.post(FORECAST_URL, data="{}", content_type="application/json")

        response = self.client.get(
            FORECAST_URL, **staff_headers(self.client, role=ADMIN, username="boss")
        )

        self.assertEqual(response.status_code, 200)


class OpenEndpointsUnchangedTests(TestCase):
    def test_obs_post_stays_open_without_auth(self):
        response = self.client.post(
            OBS_URL,
            {"date": date.today().isoformat(), "patients": 5},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

    def test_forecast_post_stays_open_without_auth(self):
        seed_observations()

        response = self.client.post(
            FORECAST_URL, data="{}", content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
