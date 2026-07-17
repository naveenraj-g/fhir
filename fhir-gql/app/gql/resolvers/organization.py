"""
GraphQL resolvers for the Organization resource.

Every resolver follows the exact same shape the REST router
(app/routers/organization.py) follows: check RBAC -> call
OrganizationsService -> shape the result. `OrganizationsService` itself is
untouched — this module is purely a GraphQL-shaped adapter on top of it.

GraphQL has no equivalent of REST's `Accept` header content negotiation
(see app/core/content_negotiation.py), so every service call below omits
`accept` — the service then defaults to plain JSON, which is exactly the
shape `OrgResponse`/`PaginatedOrgResponse` (and therefore `OrgType`/
`PaginatedOrgType`) expect. FHIR R4 Bundle format remains REST-only.

Every field below carries an explicit `description=`, mirroring the
`summary`/`description` text on the equivalent REST route in
app/routers/organization.py (Strawberry does not auto-promote a resolver's
Python docstring into the GraphQL schema) — this is what shows up in
GraphiQL's Docs panel.
"""

from typing import Optional

import strawberry

from app.gql.context import get_container
from app.gql.errors import translate_errors
from app.gql.permissions import require_gql_permission
from app.gql.types.organization import OrgType, PaginatedOrgType, PatchOrgInput, RegisterOrgInput
from app.schemas.organization.input import ListOrgsSchema, MeOrgsSchema, PatchOrgSchema
from app.schemas.organization.response import OrgResponse, PaginatedOrgResponse


@strawberry.type(description="Query fields for the Organization resource.")
class OrganizationQuery:
    """
    Query fields for the Organization resource. Mixed into the root `Query`
    type in app/gql/schema.py.

    Decorated with @strawberry.type (rather than left a plain class) so its
    fields carry proper dataclass field metadata for the composed `Query`
    class to inherit via multiple inheritance — this class is never used as
    a standalone schema root itself.
    """

    @strawberry.field(description="Fetch a single Organization by its integer ID. Requires the `org:read` permission.")
    @translate_errors
    async def organization(self, info: strawberry.types.Info, organization_id: int) -> OrgType:
        """Fetch a single Organization by its integer ID."""
        actor = require_gql_permission(info, "org", "read")
        service = get_container(info).organization.organization_service()
        data = await service.get_by_id(organization_id, actor)
        # model_validate re-parses the raw fhir-server dict against the same
        # Pydantic response schema REST uses, then from_pydantic() converts
        # that validated instance into the GraphQL type.
        return OrgType.from_pydantic(OrgResponse.model_validate(data))

    @strawberry.field(
        description=(
            "List Organizations, optionally filtered by `name` (case-insensitive substring), "
            "`active` status, `userId`, or `orgId`, with `limit`/`offset` pagination "
            "(default limit 50, max 200). Requires the `org:read` permission."
        )
    )
    @translate_errors
    async def organizations(
        self,
        info: strawberry.types.Info,
        name: Optional[str] = None,
        active: Optional[bool] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedOrgType:
        """List Organizations with optional filters — mirrors GET /organizations/."""
        actor = require_gql_permission(info, "org", "read")
        service = get_container(info).organization.organization_service()
        # Filters are exposed as plain field arguments (GraphQL convention for
        # query filters) then assembled into the same ListOrgsSchema REST uses.
        filters = ListOrgsSchema(name=name, active=active, user_id=user_id, org_id=org_id, limit=limit, offset=offset)
        data = await service.list(filters, actor)
        return PaginatedOrgType.from_pydantic(PaginatedOrgResponse.model_validate(data))

    @strawberry.field(
        description=(
            "List Organizations scoped to the caller's own JWT identity — `userId`/`orgId` "
            "are resolved from the token and cannot be overridden by the caller. Requires the "
            "`org:read` permission."
        )
    )
    @translate_errors
    async def my_organizations(
        self,
        info: strawberry.types.Info,
        active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedOrgType:
        """List Organizations scoped to the caller's own JWT identity — mirrors GET /organizations/me."""
        actor = require_gql_permission(info, "org", "read")
        service = get_container(info).organization.organization_service()
        filters = MeOrgsSchema(active=active, limit=limit, offset=offset)
        data = await service.get_me(filters, actor)
        return PaginatedOrgType.from_pydantic(PaginatedOrgResponse.model_validate(data))


@strawberry.type(description="Mutation fields for the Organization resource.")
class OrganizationMutation:
    """Mutation fields for the Organization resource. Mixed into the root `Mutation` type in app/gql/schema.py (see OrganizationQuery docstring for why this is decorated)."""

    @strawberry.mutation(
        description=(
            "Create a new Organization. Enforces that `name` and `type` are provided (FHIR "
            "leaves both optional). Deduplicates by name — a case-insensitive match against an "
            "existing organization raises a GraphQL error with `extensions.code == 409`. "
            "`createdBy` is stamped automatically from the caller's JWT. Requires the "
            "`org:create` permission."
        )
    )
    @translate_errors
    async def register_organization(self, info: strawberry.types.Info, input: RegisterOrgInput) -> OrgType:
        """Create a new Organization — mirrors POST /organizations/, including the duplicate-name 409 check in OrganizationsService."""
        actor = require_gql_permission(info, "org", "create")
        service = get_container(info).organization.organization_service()
        # to_pydantic() re-runs the exact validation RegisterOrgSchema performs for REST.
        dto = input.to_pydantic()
        data = await service.register(dto, actor)
        return OrgType.from_pydantic(OrgResponse.model_validate(data))

    @strawberry.mutation(
        description=(
            "Partially update an Organization's `active`, `name`, or `partofDisplay` fields — "
            "at least one must be set. Child arrays are not patchable here (see "
            "`PatchOrgInput`). `updatedBy` is stamped automatically from the caller's JWT. "
            "Requires the `org:update` permission."
        )
    )
    @translate_errors
    async def update_organization(self, info: strawberry.types.Info, organization_id: int, input: PatchOrgInput) -> OrgType:
        """Partially update an Organization — mirrors PATCH /organizations/{id}."""
        actor = require_gql_permission(info, "org", "update")
        service = get_container(info).organization.organization_service()
        dto: PatchOrgSchema = input.to_pydantic()
        data = await service.update(organization_id, dto, actor)
        return OrgType.from_pydantic(OrgResponse.model_validate(data))

    @strawberry.mutation(
        description=(
            "Permanently delete an Organization and all its associated child records. "
            "Irreversible. Requires the `org:delete` permission. Returns true on success."
        )
    )
    @translate_errors
    async def delete_organization(self, info: strawberry.types.Info, organization_id: int) -> bool:
        """Delete an Organization and its child records — mirrors DELETE /organizations/{id}. Returns true on success."""
        actor = require_gql_permission(info, "org", "delete")
        service = get_container(info).organization.organization_service()
        await service.delete(organization_id, actor)
        return True
