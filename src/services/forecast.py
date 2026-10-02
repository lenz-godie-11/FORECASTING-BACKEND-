from django.db import transaction

from business_logic.config.settings import (
    FORECAST_HORIZON,
    MODEL_NAME,
    MODEL_PERIOD,
)
from business_logic.services.forecast import forecast_to_records, run_forecast

from src.models.forecast import ForecastPoint, ForecastRun
from src.services.history import observations_to_frame


class ForecastError(Exception):
    """Raised when a forecast cannot be produced or retrieved."""


def trigger_forecast() -> dict:
    """Run the full flow: DB history -> pipeline -> Theta -> persisted records."""
    history = observations_to_frame()

    if history.empty:
        raise ForecastError(
            "No patient observations found. Ingest observations first."
        )

    try:
        forecast = run_forecast(history)
    except ValueError as exc:
        raise ForecastError(str(exc)) from exc

    points = forecast_to_records(forecast)

    with transaction.atomic():
        run = ForecastRun.objects.create(
            model=MODEL_NAME,
            period=MODEL_PERIOD,
            horizon=FORECAST_HORIZON,
            history_start=history["date"].min(),
            history_end=history["date"].max(),
        )

        ForecastPoint.objects.bulk_create(
            ForecastPoint(
                forecast_run=run,
                date=point["date"],
                predicted_patients=point["patients"],
            )
            for point in points
        )

    return {
        "success": True,
        "model": MODEL_NAME,
        "period": MODEL_PERIOD,
        "horizon": FORECAST_HORIZON,
        "run_id": run.id,
        "history_start": str(run.history_start),
        "history_end": str(run.history_end),
        "forecast": points,
    }


def get_forecast(run_id: int | None = None) -> dict:
    """Retrieve a stored forecast run with all of its points."""
    if run_id is None:
        run = ForecastRun.objects.first()
    else:
        run = ForecastRun.objects.filter(id=run_id).first()

    if run is None:
        raise ForecastError("Forecast not found.")

    points = list(
        run.points.order_by("date").values_list("date", "predicted_patients")
    )

    return {
        "success": True,
        "run": {
            "id": run.id,
            "model": run.model,
            "period": run.period,
            "horizon": run.horizon,
            "history_start": str(run.history_start),
            "history_end": str(run.history_end),
            "created_at": run.created_at.isoformat(),
        },
        "points": [
            {"date": str(item[0]), "predicted_patients": float(item[1])}
            for item in points
        ],
    }
