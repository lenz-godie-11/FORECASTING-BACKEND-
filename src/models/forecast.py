from django.db import models


class ForecastRun(models.Model):
    """One Theta forecast run over a window of observed history."""

    model = models.CharField(max_length=100)
    period = models.PositiveIntegerField()
    horizon = models.PositiveIntegerField()
    history_start = models.DateField()
    history_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "forecast_runs"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.model} run {self.id}"


class ForecastPoint(models.Model):
    """One predicted daily patient count belonging to a ForecastRun."""

    forecast_run = models.ForeignKey(
        ForecastRun,
        on_delete=models.CASCADE,
        related_name="points",
    )
    date = models.DateField()
    predicted_patients = models.FloatField()

    class Meta:
        db_table = "forecast_points"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["forecast_run", "date"],
                name="unique_forecast_point_per_run",
            )
        ]

    def __str__(self):
        return f"{self.forecast_run_id} {self.date}: {self.predicted_patients}"
