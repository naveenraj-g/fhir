"""
Column-group factories for the FHIR datatypes that repeat throughout PlanDefinition.

Each factory returns a dict {column_name: Column} for a given prefix, so a model body can write
`locals().update(cc("type"))` to get type_system / type_code / type_display / type_text.
Everything is a plain flat column: references hold the PUBLIC id and are never foreign keys.
"""

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, Text


def cc(p: str, index_code: bool = False) -> dict:
    """CodeableConcept (0..1)."""
    return {
        f"{p}_system": Column(String, nullable=True),
        f"{p}_code": Column(String, nullable=True, index=index_code),
        f"{p}_display": Column(String, nullable=True),
        f"{p}_text": Column(String, nullable=True),
    }


def coding(p: str) -> dict:
    """Coding (0..1)."""
    return {
        f"{p}_system": Column(String, nullable=True),
        f"{p}_code": Column(String, nullable=True),
        f"{p}_display": Column(String, nullable=True),
    }


def quantity(p: str) -> dict:
    """Quantity / Duration / Age (value + comparator + unit + system + code)."""
    return {
        f"{p}_value": Column(Float, nullable=True),
        f"{p}_comparator": Column(String, nullable=True),
        f"{p}_unit": Column(String, nullable=True),
        f"{p}_system": Column(String, nullable=True),
        f"{p}_code": Column(String, nullable=True),
    }


def simple_quantity(p: str) -> dict:
    """SimpleQuantity (Range bounds): no comparator."""
    return {
        f"{p}_value": Column(Float, nullable=True),
        f"{p}_unit": Column(String, nullable=True),
        f"{p}_system": Column(String, nullable=True),
        f"{p}_code": Column(String, nullable=True),
    }


def range_(p: str) -> dict:
    """Range (low + high SimpleQuantity)."""
    return {**simple_quantity(f"{p}_low"), **simple_quantity(f"{p}_high")}


def ratio(p: str) -> dict:
    """Ratio (numerator + denominator Quantity)."""
    return {**quantity(f"{p}_numerator"), **quantity(f"{p}_denominator")}


def period(p: str) -> dict:
    """Period (start / end)."""
    return {
        f"{p}_start": Column(DateTime(timezone=True), nullable=True),
        f"{p}_end": Column(DateTime(timezone=True), nullable=True),
    }


def reference(p: str, enum_cls=None, enum_name: str = "") -> dict:
    """Reference — closed (Enum type) when enum_cls is given, open (String type) otherwise. Public id, no FK."""
    type_col = Column(Enum(enum_cls, name=enum_name), nullable=True) if enum_cls else Column(String, nullable=True)
    return {
        f"{p}_type": type_col,
        f"{p}_id": Column(Integer, nullable=True, index=True),
        f"{p}_display": Column(String, nullable=True),
    }


def expression(p: str) -> dict:
    """Expression (description, name, language, expression, reference)."""
    return {
        f"{p}_description": Column(String, nullable=True),
        f"{p}_name": Column(String, nullable=True),
        f"{p}_language": Column(String, nullable=True),
        f"{p}_expression": Column(Text, nullable=True),
        f"{p}_reference": Column(String, nullable=True),
    }


def attachment(p: str) -> dict:
    """Attachment."""
    return {
        f"{p}_content_type": Column(String, nullable=True),
        f"{p}_language": Column(String, nullable=True),
        f"{p}_data": Column(Text, nullable=True),
        f"{p}_url": Column(String, nullable=True),
        f"{p}_size": Column(Integer, nullable=True),
        f"{p}_hash": Column(String, nullable=True),
        f"{p}_title": Column(String, nullable=True),
        f"{p}_creation": Column(DateTime(timezone=True), nullable=True),
    }


def timing(p: str) -> dict:
    """
    Timing. The 0..* primitives (event, dayOfWeek, timeOfDay, when) are comma-separated Text — they are
    never filtered individually (same treatment as Address.line[] / daysOfWeek[]).
    """
    return {
        f"{p}_event": Column(Text, nullable=True),
        **cc(f"{p}_code"),
        **quantity(f"{p}_repeat_bounds_duration"),
        **range_(f"{p}_repeat_bounds_range"),
        **period(f"{p}_repeat_bounds_period"),
        f"{p}_repeat_count": Column(Integer, nullable=True),
        f"{p}_repeat_count_max": Column(Integer, nullable=True),
        f"{p}_repeat_duration": Column(Float, nullable=True),
        f"{p}_repeat_duration_max": Column(Float, nullable=True),
        f"{p}_repeat_duration_unit": Column(String, nullable=True),
        f"{p}_repeat_frequency": Column(Integer, nullable=True),
        f"{p}_repeat_frequency_max": Column(Integer, nullable=True),
        f"{p}_repeat_period": Column(Float, nullable=True),
        f"{p}_repeat_period_max": Column(Float, nullable=True),
        f"{p}_repeat_period_unit": Column(String, nullable=True),
        f"{p}_repeat_day_of_week": Column(Text, nullable=True),
        f"{p}_repeat_time_of_day": Column(Text, nullable=True),
        f"{p}_repeat_when": Column(Text, nullable=True),
        f"{p}_repeat_offset": Column(Integer, nullable=True),
    }
