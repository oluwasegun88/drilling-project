from pathlib import Path
import warnings
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.staticfiles import StaticFiles
from test_project.test_project_module import test_project_module
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


app = FastAPI(
    title="RADA ANALYSIS API",
    description="RADA ANALYSIS API for Newcross Exploration and Production",
    version="1.0.0",
    docs_url="/docs",   
    redoc_url="/redoc", 
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_project_module.router)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Hello RADA ANALYSIS API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8007, reload=True)