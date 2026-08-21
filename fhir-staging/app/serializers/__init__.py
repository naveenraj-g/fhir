"""Model -> plain snake_case dict.

This package is fhir-staging's equivalent of fhir-server's
`app/fhir/mappers/<resource>/`, minus the FHIR half. There is no `fhir.py` and
no `to_fhir_*`: the FHIR R4 standard governs the *table shape* in this service,
not the wire format, so nothing here ever emits camelCase or a resourceType.
"""

from app.serializers.staging_observation import to_plain_staging_observation
from app.serializers.staging_medical_record import to_plain_staging_medical_record

__all__ = ["to_plain_staging_observation", "to_plain_staging_medical_record"]
