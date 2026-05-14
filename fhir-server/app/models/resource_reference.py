from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import FHIRBase as Base


class ResourceReference(Base):
    """
    Generic polymorphic reference table.

    Use this ONLY where a field can point to multiple resource types.
    For known, fixed relationships (e.g. Encounter → Patient) use a
    direct typed FK instead.

    Example row:
        source_type="Encounter", source_id=5,
        target_type="Condition",  target_id=12
    """

    __tablename__ = "resource_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_type = Column(String, nullable=False)
    source_id = Column(Integer, nullable=False)

    target_type = Column(String, nullable=False)
    target_id = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_resource_ref_source", "source_type", "source_id"),
        Index("ix_resource_ref_target", "target_type", "target_id"),
    )
