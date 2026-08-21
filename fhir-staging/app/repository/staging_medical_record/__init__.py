from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["StagingMedicalRecordRepository"]


@trace_methods
class StagingMedicalRecordRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All staging-medical-record DB I/O.

    Observations have no repository of their own: they are not addressable,
    so every write goes through create()/patch() on the whole nested payload
    (see full.py). session_factory and the generic paginated-list execution
    are inherited from BaseRepository.

    @trace_methods walks the MRO, so methods on either mixin are covered
    without any logging code of their own — see app.core.logging.
    """
