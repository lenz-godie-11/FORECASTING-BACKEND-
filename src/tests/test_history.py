from datetime import date, timedelta

from django.test import TestCase

from src.models.obs import PatientObservation
from src.services.history import observations_to_frame


class HistoryToFrameTests(TestCase):
    def test_empty_database_returns_empty_frame_with_columns(self):
        frame = observations_to_frame()

        self.assertTrue(frame.empty)
        self.assertEqual(list(frame.columns), ["date", "patients"])

    def test_rows_converted_and_sorted_by_date(self):
        today = date.today()
        PatientObservation.objects.create(
            date=today - timedelta(days=2), patients=5
        )
        PatientObservation.objects.create(
            date=today - timedelta(days=3), patients=7
        )
        PatientObservation.objects.create(
            date=today - timedelta(days=1), patients=9
        )

        frame = observations_to_frame()

        self.assertEqual(len(frame), 3)
        self.assertEqual(
            frame["date"].tolist(),
            [
                today - timedelta(days=3),
                today - timedelta(days=2),
                today - timedelta(days=1),
            ],
        )
        self.assertEqual(frame["patients"].tolist(), [7, 5, 9])
