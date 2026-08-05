from dependency_injector import containers, providers

from app.repository.practitioner_role_repository import PractitionerRoleRepository
from app.repository.schedule_repository import ScheduleRepository
from app.repository.slot_repository import SlotRepository
from app.services.slot_service import SlotService


class SlotContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    slot_repository = providers.Factory(
        SlotRepository,
        session_factory=core.database.provided.session,
    )

    schedule_repository = providers.Factory(
        ScheduleRepository,
        session_factory=core.database.provided.session,
    )

    practitioner_role_repository = providers.Factory(
        PractitionerRoleRepository,
        session_factory=core.database.provided.session,
    )

    slot_service = providers.Factory(
        SlotService,
        repository=slot_repository,
        schedule_repository=schedule_repository,
        practitioner_role_repository=practitioner_role_repository,
    )
