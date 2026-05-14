from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import FHIRBase as Base


class CodeableConcept(Base):
    __tablename__ = "codeable_concept"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=True)

    codings = relationship(
        "Coding", back_populates="codeable_concept", cascade="all, delete-orphan"
    )


class Coding(Base):
    __tablename__ = "coding"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codeable_concept_id = Column(
        Integer, ForeignKey("codeable_concept.id"), nullable=False, index=True
    )

    system = Column(String, nullable=True)
    version = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display = Column(String, nullable=True)
    user_selected = Column(Boolean, nullable=True)

    codeable_concept = relationship("CodeableConcept", back_populates="codings")
