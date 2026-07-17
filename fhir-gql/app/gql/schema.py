"""
Composes the GraphQL schema from per-domain Query/Mutation resolver mixins
and exposes it as a FastAPI-mountable router.

Adding a new resource to the GraphQL API means: write its
`app/gql/types/<resource>.py` + `app/gql/resolvers/<resource>.py`, then add
its Query/Mutation mixin below — this mirrors how `app/routers/__init__.py`
aggregates REST routers into one `api_router`.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.config import settings
from app.gql.context import get_context
from app.gql.resolvers.organization import OrganizationMutation, OrganizationQuery
from app.gql.resolvers.patient import PatientMutation, PatientQuery
from app.gql.resolvers.patient_everything_example import PatientEverythingQuery
from app.gql.resolvers.patient_lazy_example import PatientLazyQuery


@strawberry.type
class Query(PatientQuery, OrganizationQuery, PatientLazyQuery, PatientEverythingQuery):
    """
    Root GraphQL query type — merges every domain's query fields via mixin
    inheritance. `PatientLazyQuery` adds the `patientLazy`/`patientsLazy`
    EXAMPLE fields (see app/gql/resolvers/patient_lazy_example.py)
    demonstrating field-level lazy/parallel/dependent resolvers alongside
    the pilot's `patient` field. `PatientEverythingQuery` adds the
    `patientEverything` EXAMPLE field (see
    app/gql/resolvers/patient_everything_example.py) demonstrating the same
    independent/parallel shape fanned out across resource types instead of
    one resource's own fields. Remove either mixin if you don't want that
    example exposed in the schema.
    """


@strawberry.type
class Mutation(PatientMutation, OrganizationMutation):
    """Root GraphQL mutation type — merges every domain's mutation fields via mixin inheritance."""


schema = strawberry.Schema(query=Query, mutation=Mutation)

# GraphiQL (the in-browser IDE served on GET /graphql) is convenient for
# local/dev testing but disabled in production to avoid exposing schema
# introspection and a live query console publicly.
#
# allow_queries_via_get=False is required for auth correctness, not just
# style: with it left at Strawberry's default (True), a client could send a
# full GraphQL operation as `GET /graphql?query=...`. Auth is enforced inside
# get_context() (see app/gql/context.py) rather than as a router-level
# FastAPI dependency, specifically so the bare GraphiQL HTML/JS shell can
# still load without an Authorization header — a browser navigating to
# GET /graphql cannot attach one. If GET could also execute operations,
# that path would bypass auth entirely.
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide="graphiql" if settings.ENVIRONMENT != "production" else None,
    allow_queries_via_get=False,
)
