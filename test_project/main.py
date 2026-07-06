import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron      import CronTrigger

from production_automation.router.production_automation_router import (
    router as production_router,
    run_daily_report_job,
    run_monthly_report_job,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Scheduler setup ───────────────────────────────────────────────────────────
scheduler = AsyncIOScheduler(timezone="Africa/Lagos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on server startup and shutdown.
    Starts the scheduler when the API starts,
    shuts it down cleanly when the API stops.
    """
    # ── Daily report — every day at 10:00 PM ─────────────────────────────────
    scheduler.add_job(
        run_daily_report_job,
        trigger=CronTrigger(hour=22, minute=0, timezone="Africa/Lagos"),
        id="daily_production_report",
        name="Daily Production Report — 10:00 PM",
        replace_existing=True,
    )

    # ── Monthly report — last day of every month at 10:00 PM ─────────────────
    scheduler.add_job(
        run_monthly_report_job,
        trigger=CronTrigger(hour=22, minute=0, timezone="Africa/Lagos"),
        id="monthly_production_report",
        name="Monthly Production Report — Last day of month at 10:00 PM",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ Scheduler started")
    logger.info("📅 Daily report   → every day at 10:00 PM (Africa/Lagos)")
    logger.info("📅 Monthly report → last day of month at 10:00 PM (Africa/Lagos)")

    yield  # API is running

    scheduler.shutdown()
    logger.info("🛑 Scheduler stopped")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Production Automation API",
    version="2.0.0",
    description="OOP-structured production reporting system with automated email reports",
    lifespan=lifespan,
)

app.include_router(production_router)


@app.get("/")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/scheduler/status")
def scheduler_status():
    """Check what scheduled jobs are running."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id":        job.id,
            "name":      job.name,
            "next_run":  str(job.next_run_time),
        })
    return {"scheduler": "running", "jobs": jobs}