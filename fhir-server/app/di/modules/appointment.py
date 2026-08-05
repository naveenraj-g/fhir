from dependency_injector import containers, providers
from app.repository.appointment_repository import AppointmentRepository
from app.repository.slot_repository import SlotRepository
from app.services.appointment_service import AppointmentService


class AppointmentContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    appointment_repository = providers.Factory(
        AppointmentRepository,
        session_factory=core.database.provided.session,
    )

    slot_repository = providers.Factory(
        SlotRepository,
        session_factory=core.database.provided.session,
    )

    appointment_service = providers.Factory(
        AppointmentService,
        repository=appointment_repository,
        slot_repository=slot_repository,
    )
