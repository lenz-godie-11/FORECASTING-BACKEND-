import pandas as pd

from src.models.obs import PatientObservation


def observations_to_frame() -> pd.DataFrame:
    """Read all stored observations into a DataFrame with 'date' and 'patients'."""
    rows = list(PatientObservation.objects.all().values("date", "patients"))

    return pd.DataFrame(rows, columns=["date", "patients"])
