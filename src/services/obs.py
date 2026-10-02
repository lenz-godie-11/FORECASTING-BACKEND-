from django.db import IntegrityError

from src.models.obs import PatientObservation


class ObservationConflict(Exception):
    """Raised when an existing observation conflicts with the incoming one."""


def create_observation(data: dict) -> tuple[PatientObservation, bool]:
    """Create an observation, or return the existing one when identical.

    Raises ObservationConflict when the same date exists with a
    different patient count, so data is never silently overwritten.
    """
    observation_date = data["date"]
    patients = data["patients"]
    source = data.get("source", "hospital_system")

    existing = PatientObservation.objects.filter(
        date=observation_date
    ).first()

    if existing:
        if existing.patients == patients:
            return existing, False

        raise ObservationConflict(
            "An observation for this date already exists "
            "with a different patient count."
        )

    try:
        observation = PatientObservation.objects.create(
            date=observation_date,
            patients=patients,
            source=source,
        )
    except IntegrityError:
        # Concurrent insert between the check above and the create.
        existing = PatientObservation.objects.get(date=observation_date)

        if existing.patients == patients:
            return existing, False

        raise ObservationConflict(
            "An observation for this date already exists "
            "with a different patient count."
        ) from None

    return observation, True
