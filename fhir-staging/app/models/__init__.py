"""Every model package, imported here so SQLAlchemy's registry is complete.

Both `migrations/env.py` and `tests/conftest.py` import this module and nothing
else — a relationship declared with a string target ("StagingObservationModel") only
resolves once the module defining it has been imported, so a partial import set
fails at mapper-configuration time rather than at the import itself, with an
error that points at the wrong place.
"""

from app.models.enums import EncounterReferenceType, StagingReviewStatus, StagingStatus
from app.models.staging_observation import *  # noqa: F401,F403
from app.models.staging_medical_record import *  # noqa: F401,F403

from app.models.staging_observation import __all__ as _staging_observation_all
from app.models.staging_medical_record import __all__ as _staging_medical_record_all

__all__ = [
    "EncounterReferenceType",
    "StagingReviewStatus",
    "StagingStatus",
    *_staging_observation_all,
    *_staging_medical_record_all,
]
