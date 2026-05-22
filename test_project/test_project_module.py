from fastapi import APIRouter
from test_project.test_project_controller import router as test_project_router


class TestProjectModule:

    def __init__(self):
        self.router = APIRouter()
        self.router.include_router(test_project_router)


test_project_module = TestProjectModule()