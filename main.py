from pathlib import Path
import warnings
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.staticfiles import StaticFiles
# import pandas as pd
# from openai import OpenAI
from core.config import settings
from global_cache_service import global_cache

from well_modelling.vlp.vlp_module import vlp_module
from well_modelling.ipr.ipr_module import ipr_module
from pvt.pvt_module import pvt_module
from well_modelling.nodal_analysis.nodal_analysis_module import nodal_analysis_module
from well_modelling.well_operating_envelope.woe_module import woe_module
from aquifer.aquifer_module import aquifer_module
from mbe.mbe_module import mbe_module
from fractional_flow.fractional_flow_module import fractional_flow_module
from ips_forecast.ips_forecast_module import ips_forecast_module
from setup.setup_module import setup_module
# from dynamic_dashboard.dynamic_dashbaord_service import DynamicDashboardService
# from dynamic_dashboard.dynamic_dashbaord_module import dynamic_dashbaord_module
from test_project.test_project_module import test_project_module
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# user_id = "fSD2oLxBocdnzpUmLnZzUeWViHB3"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start cache cleanup task
    await global_cache.start_cleanup()
    logger.info("Cache cleanup task started")
    
    yield
    
    # Shutdown: Clean up resources if needed
    await global_cache.stop_cleanup()
    logger.info("Cache cleanup task stopped")


app = FastAPI(
    title="RADA API",
    description="RADA API for Newcross Exploration and Production",
    version="1.0.0",
    docs_url="/docs",   
    redoc_url="/redoc", 
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# def load_data():
#     df = pd.read_excel("Production_Report (41).xlsx")
#     df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True)
#     client = OpenAI(api_key=settings.OPENAI_API_KEY)
#     app.state.dynamic_dashboard_service = DynamicDashboardService(df, client)

static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

app.include_router(vlp_module.router)

app.include_router(ipr_module.router)

app.include_router(pvt_module.router)

app.include_router(nodal_analysis_module.router)

app.include_router(woe_module.router)

app.include_router(aquifer_module.router)

app.include_router(mbe_module.router)

app.include_router(fractional_flow_module.router)

app.include_router(ips_forecast_module.router)

app.include_router(setup_module.router)

app.include_router(test_project_module.router)

# app.include_router(dynamic_dashbaord_module.router)

app.mount("/viewer", StaticFiles(directory="static", html=True), name="viewer")


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Hello RADA API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)