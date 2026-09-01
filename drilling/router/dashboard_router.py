import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from drilling.repository.npt_repository import NPTRepository
from drilling.service.dashboard_service  import DashboardService
from firebase_database.setup_firebase    import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["NPT Dashboard"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_dashboard_service(
    total_rig_hours: float = 2415.0
) -> DashboardService:
    return DashboardService(NPTRepository(db), total_rig_hours)


# ── Main dashboard metrics ────────────────────────────────────────────────────

@router.get("/metrics")
async def get_dashboard_metrics(
    well:            Optional[str]   = Query(None,   description="Well name e.g. Awoba NW 5"),
    start_date:      Optional[str]   = Query(None,   description="Start date YYYY-MM-DD"),
    end_date:        Optional[str]   = Query(None,   description="End date YYYY-MM-DD"),
    total_rig_hours: Optional[float] = Query(2415.0, description="Total rig hours"),
):
    """
    Get all dashboard metrics for a well.
    Returns all KPIs, costs and breakdowns by category, phase,
    responsible party and month.
    """
    try:
        service = get_dashboard_service(total_rig_hours or 2415.0)
        metrics = await service.get_dashboard_metrics(
            well=well,
            start_date=start_date,
            end_date=end_date,
            total_rig_hours=total_rig_hours,
        )
        return {"status": "success", "data": metrics}
    except Exception as e:
        logger.error("Dashboard metrics error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── Individual breakdown endpoints ────────────────────────────────────────────

@router.get("/by-category")
async def get_npt_by_category(
    well: Optional[str] = Query(None, description="Filter by well name"),
):
    """Get NPT hours and cost grouped by category."""
    try:
        service = get_dashboard_service()
        result  = await service.get_npt_summary_by_category(well=well)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/by-phase")
async def get_npt_by_phase(
    well: Optional[str] = Query(None, description="Filter by well name"),
):
    """Get NPT hours and cost grouped by drilling phase."""
    try:
        service = get_dashboard_service()
        result  = await service.get_npt_summary_by_phase(well=well)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/by-responsible-party")
async def get_npt_by_responsible_party(
    well: Optional[str] = Query(None, description="Filter by well name"),
):
    """Get NPT hours and cost grouped by responsible party."""
    try:
        service = get_dashboard_service()
        result  = await service.get_npt_summary_by_responsible_party(well=well)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@router.get("/by-month")
async def get_npt_by_month(
    well: Optional[str] = Query(None, description="Filter by well name"),
):
    """Get NPT hours and cost grouped by month."""
    try:
        service = get_dashboard_service()
        result  = await service.get_npt_summary_by_month(well=well)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))