import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from drilling.models.drilling_dto import NPTRecordCreateDTO, NPTRecordUpdateDTO
from drilling.repository.npt_repository import NPTRepository
from drilling.service.npt_service import NPTService
from firebase_database.setup_firebase import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/npt", tags=["NPT Records"])


# ── Dependency ────────────────────────────────────────────────────────────────

def get_npt_service() -> NPTService:
    return NPTService(NPTRepository(db))


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
async def create_npt_record(
    payload: NPTRecordCreateDTO,
    service: NPTService = Depends(get_npt_service),
):
    """Create a new NPT record."""
    try:
        data   = payload.model_dump()
        result = await service.create(data)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error("Create NPT error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── READ ALL ──────────────────────────────────────────────────────────────────

@router.get("/")
async def fetch_all_npt_records(
    well:              Optional[str] = Query(None, description="Filter by well name"),
    phase:             Optional[str] = Query(None, description="Filter by phase"),
    category:          Optional[str] = Query(None, description="Filter by category"),
    responsible_party: Optional[str] = Query(None, description="Filter by responsible party"),
    start_date:        Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date:          Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    service: NPTService = Depends(get_npt_service),
):
    """Fetch all NPT records with optional filters."""
    try:
        filters = {
            "well":               well,
            "phase":              phase,
            "category":           category,
            "responsible_party":  responsible_party,
            "start_date":         start_date,
            "end_date":           end_date,
        }
        filters = {k: v for k, v in filters.items() if v is not None}
        records = await service.fetch_all(filters)
        return {"status": "success", "total": len(records), "data": records}
    except Exception as e:
        logger.error("Fetch NPT error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── READ ONE ──────────────────────────────────────────────────────────────────

@router.get("/{record_id}")
async def fetch_npt_record(
    record_id: str,
    service: NPTService = Depends(get_npt_service),
):
    """Fetch a single NPT record by ID."""
    try:
        record = await service.fetch_by_id(record_id)
        if not record:
            raise HTTPException(404, detail=f"NPT record {record_id} not found")
        return {"status": "success", "data": record}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Fetch NPT by ID error: %s", e)
        raise HTTPException(500, detail=str(e))


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.put("/{record_id}")
async def update_npt_record(
    record_id: str,
    payload:   NPTRecordUpdateDTO,
    service: NPTService = Depends(get_npt_service),
):
    """Update an existing NPT record."""
    try:
        data   = payload.model_dump()
        result = await service.update(record_id, data)
        if not result:
            raise HTTPException(404, detail=f"NPT record {record_id} not found")
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update NPT error: %s", e)
        raise HTTPException(500, detail=str(e))


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete("/{record_id}")
async def delete_npt_record(
    record_id: str,
    service: NPTService = Depends(get_npt_service),
):
    """Delete an NPT record by ID."""
    try:
        deleted = await service.delete(record_id)
        if not deleted:
            raise HTTPException(404, detail=f"NPT record {record_id} not found")
        return {"status": "success", "message": f"NPT record {record_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete NPT error: %s", e)
        raise HTTPException(500, detail=str(e))