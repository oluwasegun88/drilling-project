from fastapi import APIRouter
from production_automation.router.production_automation_router import router as production_automation_router


class ProductionAutomationModule:

    def __init__(self):
        self.router = APIRouter()
        self.router.include_router(production_automation_router)


production_automation_module = ProductionAutomationModule()