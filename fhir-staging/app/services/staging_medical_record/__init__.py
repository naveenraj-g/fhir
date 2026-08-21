from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["StagingMedicalRecordService"]


@trace_methods
class StagingMedicalRecordService(_CoreMixin):
    """All staging-medical-record business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
