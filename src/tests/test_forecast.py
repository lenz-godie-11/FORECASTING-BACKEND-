from datetime import date, timedelta

from django.test import TestCase

from src.models.forecast import ForecastPoint, ForecastRun
from src.models.obs import PatientObservation
from src.services.forecast import ForecastError, get_forecast, trigger_forecast

FORECAST_URL = "/api/v1/forecast/"


def seed_observations(days: int = 90, gap: int = 0):
    end = date.today() - timedelta(days=gap)
    for i in range(days):
        PatientObservation.objects.create(
            date=end - timedelta(days=days - 1 - i),
            patients=100 + 10 * (i % 7),
        )


class ForecastServiceTests(TestCase):
    def test_trigger_without_history_raises(self):
        with self.assertRaises(ForecastError):
            trigger_forecast()

    def test_forecast_run_persisted_with_metadata(self):
        seed_observations()
        result = trigger_forecast()

        run = ForecastRun.objects.get()
        self.assertEqual(run.model, "ThetaModel")
        self.assertEqual(run.period, 7)
        self.assertEqual(run.horizon, 90)
        self.assertEqual(run.id, result["run_id"])
        self.assertEqual(run.history_end, date.today())
        self.assertEqual(run.history_start, date.today() - timedelta(days=89))
        self.assertEqual(result["history_start"], str(run.history_start))
        self.assertEqual(result["history_end"], str(run.history_end))

    def test_ninety_points_linked_to_run_with_valid_dates(self):
        seed_observations()
        trigger_forecast()

        run = ForecastRun.objects.get()
        points = list(run.points.all())
        self.assertEqual(len(points), 90)
        self.assertTrue(all(point.forecast_run_id == run.id for point in points))
        self.assertTrue(all(point.predicted_patients >= 0 for point in points))
        dates = [point.date for point in points]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(dates[0], date.today() + timedelta(days=1))
        self.assertEqual(dates[-1], date.today() + timedelta(days=90))

    def test_get_forecast_latest_and_by_id(self):
        seed_observations()
        result = trigger_forecast()
        run_id = result["run_id"]

        latest = get_forecast()
        self.assertEqual(latest["run"]["id"], run_id)
        self.assertEqual(len(latest["points"]), 90)

        fetched = get_forecast(run_id)
        self.assertEqual(fetched["run"]["id"], run_id)

        with self.assertRaises(ForecastError):
            get_forecast(99999)

    def test_forecast_points_are_unique_per_run(self):
        seed_observations()
        trigger_forecast()

        self.assertEqual(
            len({point.date for point in ForecastPoint.objects.all()}), 90
        )


class ForecastApiTests(TestCase):
    def test_post_triggers_forecast(self):
        seed_observations()
        response = self.client.post(
            FORECAST_URL, data="{}", content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["model"], "ThetaModel")
        self.assertEqual(data["period"], 7)
        self.assertEqual(data["horizon"], 90)
        self.assertEqual(len(data["forecast"]), 90)
        self.assertEqual(ForecastRun.objects.count(), 1)
        self.assertEqual(ForecastPoint.objects.count(), 90)

    def test_post_without_history_returns_400(self):
        response = self.client.post(
            FORECAST_URL, data="{}", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_get_latest_returns_stored_forecast(self):
        seed_observations()
        self.client.post(FORECAST_URL, data="{}", content_type="application/json")

        response = self.client.get(FORECAST_URL)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["run"]["model"], "ThetaModel")
        self.assertEqual(len(data["points"]), 90)
        self.assertGreaterEqual(data["points"][0]["predicted_patients"], 0)

    def test_get_specific_run(self):
        seed_observations()
        trigger_result = self.client.post(
            FORECAST_URL, data="{}", content_type="application/json"
        )
        run_id = trigger_result.json()["run_id"]

        response = self.client.get(f"{FORECAST_URL}{run_id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run"]["id"], run_id)

    def test_get_unknown_run_returns_404(self):
        response = self.client.get(f"{FORECAST_URL}99999/")

        self.assertEqual(response.status_code, 404)
