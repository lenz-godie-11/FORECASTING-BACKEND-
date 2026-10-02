import pandas as pd

from django.test import SimpleTestCase

from pipeline.services.pipeline import run_pipeline


class PipelineIntegrationTests(SimpleTestCase):
    def test_same_day_rows_are_summed(self):
        raw = pd.DataFrame(
            {
                "date": [
                    "2026-01-01",
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-03",
                    "2026-01-04",
                    "2026-01-05",
                    "2026-01-06",
                    "2026-01-07",
                ],
                "patients": [10, 5, 15, 15, 15, 15, 15, 15],
            }
        )

        prepared = run_pipeline(raw).reset_index()
        dates = pd.to_datetime(prepared["date"])

        self.assertEqual(len(prepared), 7)
        self.assertAlmostEqual(
            prepared.loc[dates == "2026-01-01", "patients"].iloc[0], 15.0
        )

    def test_missing_days_are_filled_by_interpolation(self):
        raw = pd.DataFrame(
            {
                "date": ["2026-01-01", "2026-01-03"],
                "patients": [10, 30],
            }
        )

        prepared = run_pipeline(raw).reset_index()
        dates = pd.to_datetime(prepared["date"])

        self.assertEqual(
            dates.tolist(),
            pd.date_range("2026-01-01", periods=3).tolist(),
        )
        self.assertTrue(prepared["patients"].notna().all())
        self.assertAlmostEqual(
            prepared.loc[dates == "2026-01-02", "patients"].iloc[0], 20.0
        )

    def test_outlier_is_clipped_to_iqr_bounds(self):
        dates = pd.date_range("2026-01-01", periods=11, freq="D")
        patients = [10] * 10 + [100]

        raw = pd.DataFrame({"date": dates, "patients": patients})

        prepared = run_pipeline(raw).reset_index()

        self.assertEqual(prepared["patients"].max(), 10.0)
        self.assertEqual(prepared["patients"].min(), 10.0)

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            run_pipeline(pd.DataFrame(columns=["date", "patients"]))
