import sys
import logging
from pathlib import Path
from fastapi import APIRouter

workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from firebase_database.setup_firebase import db

from drilling.router.npt_router       import router as npt_router
from drilling.router.dashboard_router import router as dashboard_router
from drilling.router.lookup_router    import create_lookup_router

from drilling.repository.lookup_repositories import (
    PhaseRepository,
    CategoryRepository,
    ResponsiblePartyRepository,
    WellRepository,
)
from drilling.service.generic_service import GenericService

logger = logging.getLogger(__name__)


class DrillingModule:
   

    def __init__(self):
        self.router = APIRouter(prefix="/drilling")

        self.router.include_router(npt_router)

        self.router.include_router(dashboard_router)

        self.router.include_router(
            create_lookup_router(
                prefix="/phases",
                tag="Phases",
                service_factory=lambda: GenericService(PhaseRepository(db)),
            )
        )

        self.router.include_router(
            create_lookup_router(
                prefix="/categories",
                tag="Categories",
                service_factory=lambda: GenericService(CategoryRepository(db)),
            )
        )

        self.router.include_router(
            create_lookup_router(
                prefix="/responsible-parties",
                tag="Responsible Parties",
                service_factory=lambda: GenericService(ResponsiblePartyRepository(db)),
            )
        )

        self.router.include_router(
            create_lookup_router(
                prefix="/wells",
                tag="Wells",
                service_factory=lambda: GenericService(WellRepository(db)),
            )
        )

        logger.info("DrillingModule initialized")


drilling_module = DrillingModule()