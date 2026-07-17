"""
EXAMPLE / reference resolver — companion to
app/gql/types/patient_everything_example.py. See that module's docstring for
the full explanation of what this demonstrates (fanning out from one known
Patient ID to every OTHER FHIR resource type related to that patient, all
independent/parallel, each enforcing its own resource's RBAC permission).

Try it in GraphiQL (with an Authorization header set):

    query {
      patientEverything(patientId: 1) {
        patient {
          id
          gender
          name { family given }
        }
        appointments { id status start }
        encounters { id status }
        serviceRequests { id status }
      }
    }

Unlike `patientsLazy` in app/gql/resolvers/patient_lazy_example.py, there is
no dependency chain to resolve here: `patientId` is already known as a query
argument, so `patient`, `appointments`, `encounters`, and `serviceRequests`
are independent siblings from the start and graphql-core resolves all four
concurrently when requested together. The resolver below does no fetching
itself at all — it just seeds `patient_id` and defers everything to the four
field resolvers on `PatientEverythingType`.
"""

import strawberry

from app.gql.types.patient_everything_example import PatientEverythingType


@strawberry.type(
    description=(
        "EXAMPLE query field mirroring FHIR's Patient/$everything operation — see "
        "app/gql/types/patient_everything_example.py."
    )
)
class PatientEverythingQuery:
    """Mixed into the root Query type in app/gql/schema.py, alongside — not instead of — PatientQuery/PatientLazyQuery."""

    @strawberry.field(
        description=(
            "EXAMPLE field. Fans out from one Patient ID to every FHIR resource type "
            "clinically related to that patient (Patient itself, Appointments, "
            "Encounters, ServiceRequests), mirroring FHIR's own Patient/$everything "
            "operation. All four sub-fields are independent of each other and "
            "resolve in parallel when requested together — see "
            "app/gql/types/patient_everything_example.py for the full explanation, "
            "including why each sub-field checks its own resource's permission "
            "independently rather than one blanket check here."
        )
    )
    def patient_everything(self, patient_id: int) -> PatientEverythingType:
        """EXAMPLE resolver — no fetch here; just seeds patient_id and defers everything to PatientEverythingType's four independent field resolvers."""
        return PatientEverythingType(patient_id=patient_id)
