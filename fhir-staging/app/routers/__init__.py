"""Router discovery.

Every router module is imported here unconditionally (cheap, no side effects)
and `discover_routers()` introspects the package namespace for any submodule
exposing a module-level `router: APIRouter`. Each router carries its own
`prefix=`/`tags=`, set where it is constructed, so there is no separate
prefix/tag table to keep in sync.

Only *mounting* is conditional — see app/main.py's mount_routers(), which
mounts the names listed in configs/config.yaml's `routes.enabled`.
"""

import inspect
import sys

from fastapi import APIRouter

from . import staging_medical_record as staging_medical_record

__all__ = ["discover_routers", "staging_medical_record"]


def discover_routers() -> dict[str, APIRouter]:
    """{module name: router} for every submodule exposing a module-level
    `router`."""
    module = sys.modules[__name__]
    found: dict[str, APIRouter] = {}
    for name, submodule in inspect.getmembers(module, inspect.ismodule):
        router = getattr(submodule, "router", None)
        if isinstance(router, APIRouter):
            found[name] = router
    return found
