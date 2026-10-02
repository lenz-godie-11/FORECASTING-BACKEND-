from django.db import models


class PatientObservation(models.Model):
    """One daily patient-count observation per calendar date."""

    date = models.DateField(unique=True)
    patients = models.PositiveIntegerField()
    source = models.CharField(max_length=100, default="hospital_system")
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patient_observations"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date}: {self.patients}"
