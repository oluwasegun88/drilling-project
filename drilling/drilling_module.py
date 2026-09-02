import logging
from fastapi import APIRouter

from drilling.router.excel_data_router import router as excel_router

logger = logging.getLogger(__name__)


class DrillingModule:
    """
    Drilling module — currently serving data from Excel file
    while Firebase connection is being resolved.
    
    Once Firebase is fixed, uncomment the Firebase routers below.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/drilling")

        # ── Excel data router (temporary) ─────────────────────────────────────
        self.router.include_router(excel_router)

        # ── Firebase routers (uncomment when Firebase is fixed) ───────────────
        # from firebase_database.setup_firebase import db
        # from drilling.router.npt_router import router as npt_router
        # from drilling.router.dashboard_router import router as dashboard_router
        # from drilling.router.lookup_router import create_lookup_router
        # from drilling.repository.lookup_repositories import (
        #     PhaseRepository, CategoryRepository,
        #     ResponsiblePartyRepository, WellRepository,
        # )
        # from drilling.service.generic_service import GenericService
        # self.router.include_router(npt_router)
        # self.router.include_router(dashboard_router)
        # self.router.include_router(
        #     create_lookup_router("/phases", "Phases",
        #         lambda: GenericService(PhaseRepository(db))))
        # self.router.include_router(
        #     create_lookup_router("/categories", "Categories",
        #         lambda: GenericService(CategoryRepository(db))))
        # self.router.include_router(
        #     create_lookup_router("/responsible-parties", "Responsible Parties",
        #         lambda: GenericService(ResponsiblePartyRepository(db))))
        # self.router.include_router(
        #     create_lookup_router("/wells", "Wells",
        #         lambda: GenericService(WellRepository(db))))

        logger.info("DrillingModule initialized with Excel data router")


drilling_module = DrillingModule()