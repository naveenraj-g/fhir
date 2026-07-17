"""
GraphQL types for the Organization resource, derived from the existing
Pydantic schemas in app/schemas/organization/{response,input}.py via
`strawberry.experimental.pydantic`.

Every type/field below carries an explicit `description=`. Strawberry does
NOT promote a class's Python docstring into the GraphQL schema automatically
(only `strawberry.experimental.pydantic` field-level `Field(description=...)`
values flow through on their own) — so `description=` here is what actually
shows up in GraphiQL's introspection-based "Docs" panel, the GraphQL
equivalent of REST's Swagger UI. The docstrings are kept alongside as the
Python-facing complement, for readers who never leave the source file.

Naming convention used throughout this GraphQL layer (kept mechanical so it
replicates cleanly to the remaining resources):
  - `<X>Response` (Pydantic)          -> `<X>Type` (GraphQL object type)
  - `<X>Schema` (Pydantic)             -> `<X>Input` (GraphQL input type)
  - `<X>Input` (Pydantic, already      -> kept as-is; the Pydantic class is
     ends with "Input")                  imported under an `...Schema` alias
                                          to avoid a name collision with the
                                          GraphQL class of the same name.

Declaration order matters: `strawberry.experimental.pydantic` resolves a
wrapped model's nested-model fields by looking up the nested Pydantic class
in its own registry, which only has entries for classes wrapped *before* the
parent is declared. Leaf sub-resource types are therefore declared first,
the top-level `OrgType` / `PaginatedOrgType` last.
"""

import strawberry

# Registers AddressType/AddressUse/etc. as GraphQL enums (side-effect import) —
# required before wrapping any input schema whose fields use these enums.
import app.gql.types.enums  # noqa: F401
from app.schemas.organization.input import (
    OrgAddressInput as OrgAddressInputSchema,
    OrgAliasInput as OrgAliasInputSchema,
    OrgContactInput as OrgContactInputSchema,
    OrgContactTelecomInput as OrgContactTelecomInputSchema,
    OrgEndpointInput as OrgEndpointInputSchema,
    OrgIdentifierInput as OrgIdentifierInputSchema,
    OrgTelecomInput as OrgTelecomInputSchema,
    OrgTypeInput as OrgTypeInputSchema,
    PatchOrgSchema,
    RegisterOrgSchema,
)
from app.schemas.organization.response import (
    OrgAddressResponse,
    OrgAliasResponse,
    OrgContactResponse,
    OrgContactTelecomResponse,
    OrgEndpointResponse,
    OrgIdentifierResponse,
    OrgResponse,
    OrgTelecomResponse,
    OrgTypeResponse,
    PaginatedOrgResponse,
)

# ── Response (output) types — leaf sub-resources first ───────────────────────


@strawberry.experimental.pydantic.type(
    model=OrgIdentifierResponse,
    all_fields=True,
    description="A single Organization.identifier entry.",
)
class OrgIdentifierType:
    """A single Organization.identifier entry."""


@strawberry.experimental.pydantic.type(
    model=OrgTypeResponse,
    all_fields=True,
    description="A single Organization.type CodeableConcept entry categorising the organization (e.g. prov = Healthcare Provider, dept = Hospital Department).",
)
class OrgTypeType:
    """A single Organization.type CodeableConcept entry (e.g. prov, dept)."""


@strawberry.experimental.pydantic.type(
    model=OrgAliasResponse,
    all_fields=True,
    description="A single Organization.alias entry — an alternative name the organization is or was known by.",
)
class OrgAliasType:
    """A single Organization.alias entry."""


@strawberry.experimental.pydantic.type(
    model=OrgTelecomResponse,
    all_fields=True,
    description="A single Organization.telecom (ContactPoint) entry — phone, email, fax, etc.",
)
class OrgTelecomType:
    """A single Organization.telecom (ContactPoint) entry."""


@strawberry.experimental.pydantic.type(
    model=OrgAddressResponse,
    all_fields=True,
    description="A single Organization.address entry.",
)
class OrgAddressType:
    """A single Organization.address entry."""


@strawberry.experimental.pydantic.type(
    model=OrgContactTelecomResponse,
    all_fields=True,
    description="A single telecom entry nested inside an Organization.contact person.",
)
class OrgContactTelecomType:
    """A single telecom entry nested inside an Organization.contact person."""


@strawberry.experimental.pydantic.type(
    model=OrgContactResponse,
    all_fields=True,
    description="A single Organization.contact person — someone contactable about the organization in a specific capacity (admin, billing, clinical, etc.), with nested telecom entries.",
)
class OrgContactType:
    """A single Organization.contact person (references OrgContactTelecomType)."""


@strawberry.experimental.pydantic.type(
    model=OrgEndpointResponse,
    all_fields=True,
    description="A single Organization.endpoint reference to a technical endpoint (e.g. SMART on FHIR, Direct Messaging) associated with the organization.",
)
class OrgEndpointType:
    """A single Organization.endpoint reference."""


@strawberry.experimental.pydantic.type(
    model=OrgResponse,
    all_fields=True,
    description="A full Organization resource, including all nested sub-resource arrays (identifiers, types, aliases, telecoms, addresses, contacts, endpoints).",
)
class OrgType:
    """A full Organization resource, including all nested sub-resource arrays."""


@strawberry.experimental.pydantic.type(
    model=PaginatedOrgResponse,
    all_fields=True,
    description="Paginated envelope returned by the `organizations` query — `data` for the current page, plus `total`/`limit`/`offset` for pagination.",
)
class PaginatedOrgType:
    """Paginated envelope returned by the `organizations` list query."""


# ── Input types — leaf sub-resources first ───────────────────────────────────


@strawberry.experimental.pydantic.input(
    model=OrgIdentifierInputSchema,
    all_fields=True,
    description="Input for one Organization.identifier entry.",
)
class OrgIdentifierInput:
    """Input for one Organization.identifier entry."""


@strawberry.experimental.pydantic.input(
    model=OrgTypeInputSchema,
    all_fields=True,
    description="Input for one Organization.type CodeableConcept entry — common codes: prov, dept, team, govt, ins, pay, edu, reli, crs, cg, bus, other.",
)
class OrgTypeInput:
    """Input for one Organization.type CodeableConcept entry."""


@strawberry.experimental.pydantic.input(
    model=OrgAliasInputSchema,
    all_fields=True,
    description="Input for one Organization.alias entry.",
)
class OrgAliasInput:
    """Input for one Organization.alias entry."""


@strawberry.experimental.pydantic.input(
    model=OrgTelecomInputSchema,
    all_fields=True,
    description="Input for one Organization.telecom entry. `system` and `value` are required.",
)
class OrgTelecomInput:
    """Input for one Organization.telecom entry."""


@strawberry.experimental.pydantic.input(
    model=OrgAddressInputSchema,
    all_fields=True,
    description="Input for one Organization.address entry.",
)
class OrgAddressInput:
    """Input for one Organization.address entry."""


@strawberry.experimental.pydantic.input(
    model=OrgContactTelecomInputSchema,
    all_fields=True,
    description="Input for one telecom entry nested inside an Organization.contact person.",
)
class OrgContactTelecomInput:
    """Input for one telecom entry nested inside an Organization.contact person."""


@strawberry.experimental.pydantic.input(
    model=OrgContactInputSchema,
    all_fields=True,
    description="Input for one Organization.contact person, with a nested telecom array.",
)
class OrgContactInput:
    """Input for one Organization.contact person (references OrgContactTelecomInput)."""


@strawberry.experimental.pydantic.input(
    model=OrgEndpointInputSchema,
    all_fields=True,
    description="Input for one Organization.endpoint reference.",
)
class OrgEndpointInput:
    """Input for one Organization.endpoint reference."""


@strawberry.experimental.pydantic.input(
    model=RegisterOrgSchema,
    all_fields=True,
    description=(
        "Input for `registerOrganization`. Enforces `name` and `type` even though FHIR itself "
        "leaves them optional. Deduplicates by name — a case-insensitive match against an "
        "existing organization raises a GraphQL error with `extensions.code == 409`. "
        "`createdBy` is stamped automatically from the caller's JWT — do not supply it."
    ),
)
class RegisterOrgInput:
    """Input for `registerOrganization` — mirrors RegisterOrgSchema exactly, including its `name`/`type` requirement."""


@strawberry.experimental.pydantic.input(
    model=PatchOrgSchema,
    all_fields=True,
    description=(
        "Input for `updateOrganization`. Only `active`, `name`, and `partofDisplay` are "
        "patchable — child arrays (identifier, type, alias, telecom, address, contact, "
        "endpoint) are not; delete and re-create them instead. At least one field must be set."
    ),
)
class PatchOrgInput:
    """Input for `updateOrganization` — every field optional, at least one must be set (enforced in OrganizationsService)."""


# `ListOrgsSchema` / `MeOrgsSchema` are query-parameter schemas, not mutation
# payloads — GraphQL convention is to expose filters as plain field arguments
# rather than a wrapped input type, so these two are intentionally NOT wrapped
# here. See app/gql/resolvers/organization.py, which builds these Pydantic
# objects directly from the query field's scalar arguments.
__all__ = [
    "OrgIdentifierType",
    "OrgTypeType",
    "OrgAliasType",
    "OrgTelecomType",
    "OrgAddressType",
    "OrgContactTelecomType",
    "OrgContactType",
    "OrgEndpointType",
    "OrgType",
    "PaginatedOrgType",
    "OrgIdentifierInput",
    "OrgTypeInput",
    "OrgAliasInput",
    "OrgTelecomInput",
    "OrgAddressInput",
    "OrgContactTelecomInput",
    "OrgContactInput",
    "OrgEndpointInput",
    "RegisterOrgInput",
    "PatchOrgInput",
]
