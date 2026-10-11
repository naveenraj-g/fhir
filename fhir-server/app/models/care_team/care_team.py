from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Sequence, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.care_team.enums import CareTeamParticipantMemberType, CareTeamReasonReferenceType, CareTeamStatus
from app.models.enums import EncounterReferenceType, OrganizationReferenceType, SubjectReferenceType

care_team_id_seq = Sequence("care_team_pub_seq", start=420000, increment=1, metadata=Base.metadata)

_ALL = "all, delete-orphan"


def _org_ref_enum():
    """Shared organization_reference_type (never created/dropped by this resource)."""
    return Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False)


class CareTeamModel(Base):
    """FHIR R4 CareTeam — the people and organizations planned to participate in coordinating a patient's care."""

    __tablename__ = "care_team"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    care_team_id = Column(
        Integer, care_team_id_seq, server_default=care_team_id_seq.next_value(), unique=True, index=True, nullable=False
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # status (0..1 code)
    status = Column(Enum(CareTeamStatus, name="care_team_status"), nullable=True, index=True)

    # name (0..1 string)
    name = Column(String, nullable=True, index=True)

    # subject (0..1 Reference(Patient | Group)) — shared subject_reference_type
    subject_type = Column(Enum(SubjectReferenceType, name="subject_reference_type", create_type=False), nullable=True)
    subject_id = Column(Integer, nullable=True, index=True)  # public id — no FK to other resources
    subject_display = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter)) — shared encounter_reference_type
    encounter_type = Column(Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False), nullable=True)
    encounter_id = Column(Integer, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    identifiers = relationship("CareTeamIdentifier", back_populates="care_team", cascade=_ALL)
    categories = relationship("CareTeamCategory", back_populates="care_team", cascade=_ALL)
    participants = relationship("CareTeamParticipant", back_populates="care_team", cascade=_ALL, order_by="CareTeamParticipant.id")
    reason_codes = relationship("CareTeamReasonCode", back_populates="care_team", cascade=_ALL)
    reason_references = relationship("CareTeamReasonReference", back_populates="care_team", cascade=_ALL)
    managing_organizations = relationship("CareTeamManagingOrganization", back_populates="care_team", cascade=_ALL)
    telecoms = relationship("CareTeamTelecom", back_populates="care_team", cascade=_ALL)
    notes = relationship("CareTeamNote", back_populates="care_team", cascade=_ALL)


def _fk():
    """care_team_id FK — a child table pointing at its own parent resource (the only kind of FK we use)."""
    return Column(Integer, ForeignKey("care_team.id"), nullable=False, index=True)


class CareTeamIdentifier(Base):
    """identifier[] — business identifiers."""

    __tablename__ = "care_team_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="identifiers")


class CareTeamCategory(Base):
    """category[] — CodeableConcept (type of team)."""

    __tablename__ = "care_team_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="categories")


class CareTeamParticipant(Base):
    """participant[] BackboneElement — role[] + member + onBehalfOf + period."""

    __tablename__ = "care_team_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    # member (0..1 Reference — Practitioner|PractitionerRole|RelatedPerson|Patient|Organization|CareTeam)
    member_type = Column(Enum(CareTeamParticipantMemberType, name="care_team_member_type"), nullable=True)
    member_id = Column(Integer, nullable=True, index=True)
    member_display = Column(String, nullable=True)

    # onBehalfOf (0..1 Reference(Organization)) — only when member is a Practitioner (ctm-1)
    on_behalf_of_type = Column(_org_ref_enum(), nullable=True)
    on_behalf_of_id = Column(Integer, nullable=True, index=True)
    on_behalf_of_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    care_team = relationship("CareTeamModel", back_populates="participants")
    roles = relationship("CareTeamParticipantRole", back_populates="participant", cascade=_ALL)


class CareTeamParticipantRole(Base):
    """participant.role[] — CodeableConcept (type of involvement)."""

    __tablename__ = "care_team_participant_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(Integer, ForeignKey("care_team_participant.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    participant = relationship("CareTeamParticipant", back_populates="roles")


class CareTeamReasonCode(Base):
    """reasonCode[] — CodeableConcept (why the care team exists)."""

    __tablename__ = "care_team_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="reason_codes")


class CareTeamReasonReference(Base):
    """reasonReference[] — Reference(Condition)."""

    __tablename__ = "care_team_reason_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    reference_type = Column(Enum(CareTeamReasonReferenceType, name="care_team_reason_reference_type"), nullable=True)
    reference_id = Column(Integer, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="reason_references")


class CareTeamManagingOrganization(Base):
    """managingOrganization[] — Reference(Organization)."""

    __tablename__ = "care_team_managing_organization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    reference_type = Column(_org_ref_enum(), nullable=True)
    reference_id = Column(Integer, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="managing_organizations")


class CareTeamTelecom(Base):
    """telecom[] — ContactPoint (central contact detail applying to all members)."""

    __tablename__ = "care_team_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    care_team = relationship("CareTeamModel", back_populates="telecoms")


class CareTeamNote(Base):
    """note[] — Annotation (text + optional time + author[x] string | Reference)."""

    __tablename__ = "care_team_note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_team_id = _fk()
    org_id = Column(String, nullable=True)

    text = Column(Text, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    # authorReference — Practitioner|Patient|RelatedPerson|Organization (open string type, public id)
    author_reference_type = Column(String, nullable=True)
    author_reference_id = Column(Integer, nullable=True)
    author_reference_display = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="notes")
