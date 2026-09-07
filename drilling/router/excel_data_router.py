import logging
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/excel", tags=["Excel Data (Temporary)"])

# ── Excel file path ───────────────────────────────────────────────────────────
EXCEL_FILE      = Path(__file__).parent.parent.parent / "Awoba NW 5 NPT_Drilling_Performance_Dashboard.xlsx"
WELL_NAME       = "Awoba NW 5"
TOTAL_RIG_HOURS = 2415.0

# ── Lookup data ───────────────────────────────────────────────────────────────
PHASES = [
    "Conductor Piling/Cleanout",
    "17-1/2 x 23 Hole Section",
    "16 Hole Section",
    "12 1/4 Hole Section",
    "Perforation and Wellbore Cleanout",
    "Completions",
]

CATEGORIES = [
    "Mechanical", "Electrical", "Wellbore", "BHA / Tools",
    "Mud / Solids", "Cementing", "Logistics", "Weather",
    "HSE", "Waiting on Service", "Human Error",
    "Equipment Failure", "Wellhead", "Other",
]

RESPONSIBLE_PARTIES = [
    "SMS Joy", "Newcross EP", "OMASUP", "MultiChase",
    "Clinton", "Marine/Logistics", "TBD", "Fredrikov",
    "Mega Field", "Lagrange", "Ulla", "Geowell",
]


# ── Helper functions ──────────────────────────────────────────────────────────

def load_npt_records():
    """Load all NPT records from the Excel file."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(EXCEL_FILE), read_only=True, data_only=True)
        ws = wb["NPT"]
        records = []
        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if i <= 3 or not row[1]:
                continue
            try:
                date_val = row[1]
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)
                records.append({
                    "id":               f"excel_{i}",
                    "well":             WELL_NAME,
                    "date":             date_str,
                    "phase":            str(row[2]).strip() if row[2] else "",
                    "hours":            round(float(row[3]), 4) if row[3] else 0.0,
                    "days":             round(float(row[4]), 6) if row[4] else 0.0,
                    "npt_cost":         round(float(row[5]), 2) if row[5] else 0.0,
                    "description":      str(row[6]).strip() if row[6] else "",
                    "category":         str(row[7]).strip() if row[7] else "",
                    "responsible_party": str(row[8]).strip() if row[8] else "",
                })
            except Exception:
                continue
        wb.close()
        return records
    except Exception as e:
        logger.error("Error loading Excel file: %s", e)
        return []


def apply_filters(
    records,
    phase:              Optional[str]       = None,
    category:           Optional[str]       = None,
    responsible_party:  Optional[List[str]] = None,
    start_date:         Optional[str]       = None,
    end_date:           Optional[str]       = None,
):
    """
    Apply all optional filters to a list of records.
    responsible_party accepts a LIST — multiple parties can be selected at once.
    All their hours and costs will be combined in the response.
    """
    if phase:
        records = [r for r in records if r["phase"] == phase]
    if category:
        records = [r for r in records if r["category"] == category]
    if responsible_party:
        # Support multiple responsible parties — match any in the list
        records = [r for r in records if r["responsible_party"] in responsible_party]
    if start_date:
        records = [r for r in records if r["date"] >= start_date]
    if end_date:
        records = [r for r in records if r["date"] <= end_date]
    return records


def group_by_key(records, key):
    """Group records by a key and sum hours and cost."""
    result = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
    for r in records:
        k = r.get(key) or "Unknown"
        result[k]["hours"] += r["hours"]
        result[k]["cost"]  += r["npt_cost"]
    return {
        k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
        for k, v in sorted(result.items())
    }


def group_by_month(records):
    """Group records by month and sum hours and cost."""
    result = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
    for r in records:
        try:
            month = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%b-%Y")
        except Exception:
            month = "Unknown"
        result[month]["hours"] += r["hours"]
        result[month]["cost"]  += r["npt_cost"]
    return {
        k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
        for k, v in result.items()
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/npt")
async def get_all_npt_records(
    phase:             Optional[str]        = Query(None, description="Filter by phase"),
    category:          Optional[str]        = Query(None, description="Filter by category"),
    responsible_party: Optional[List[str]]  = Query(None, description="Filter by one or more responsible parties e.g. ?responsible_party=SMS Joy&responsible_party=Geowell"),
    start_date:        Optional[str]        = Query(None, description="Start date YYYY-MM-DD"),
    end_date:          Optional[str]        = Query(None, description="End date YYYY-MM-DD"),
):
    """Get all NPT records with optional filters. responsible_party accepts multiple values."""
    try:
        records = load_npt_records()
        records = apply_filters(records, phase, category, responsible_party, start_date, end_date)
        return {"status": "success", "total": len(records), "data": records}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/metrics")
async def get_dashboard_metrics(
    phase:             Optional[str]       = Query(None,   description="Filter by phase"),
    category:          Optional[str]       = Query(None,   description="Filter by category"),
    responsible_party: Optional[List[str]] = Query(None,   description="Filter by one or more responsible parties"),
    start_date:        Optional[str]       = Query(None,   description="Start date YYYY-MM-DD"),
    end_date:          Optional[str]       = Query(None,   description="End date YYYY-MM-DD"),
    total_rig_hours:   Optional[float]     = Query(2415.0, description="Total rig hours"),
):
    """Get all dashboard KPI metrics with optional filters."""
    try:
        records  = load_npt_records()
        records  = apply_filters(records, phase, category, responsible_party, start_date, end_date)
        rig_hrs  = total_rig_hours or TOTAL_RIG_HOURS

        total_npt_hours  = round(sum(r["hours"]    for r in records), 4)
        total_npt_cost   = round(sum(r["npt_cost"] for r in records), 2)
        productive_hours = round(rig_hrs - total_npt_hours, 4)
        npt_pct          = round((total_npt_hours / rig_hrs * 100) if rig_hrs > 0 else 0, 4)
        prod_pct         = round((productive_hours / rig_hrs * 100) if rig_hrs > 0 else 0, 4)

        return {"status": "success", "data": {
            "well":                     WELL_NAME,
            "total_rig_hours":          rig_hrs,
            "total_rig_days":           round(rig_hrs / 24, 4),
            "total_npt_hours":          total_npt_hours,
            "total_npt_days":           round(total_npt_hours / 24, 4),
            "overall_npt_percent":      npt_pct,
            "total_npt_cost":           total_npt_cost,
            "productive_hours":         productive_hours,
            "productive_days":          round(productive_hours / 24, 4),
            "productive_time_percent":  prod_pct,
            "total_records":            len(records),
            "npt_by_category":          group_by_key(records, "category"),
            "npt_by_responsible_party": group_by_key(records, "responsible_party"),
            "npt_by_phase":             group_by_key(records, "phase"),
            "npt_by_month":             group_by_month(records),
        }}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-category")
async def get_by_category(
    responsible_party: Optional[List[str]] = Query(None, description="Filter by one or more responsible parties"),
    phase:             Optional[str]       = Query(None, description="Filter by phase"),
    start_date:        Optional[str]       = Query(None, description="Start date YYYY-MM-DD"),
    end_date:          Optional[str]       = Query(None, description="End date YYYY-MM-DD"),
):
    """Get NPT breakdown by category with optional filters."""
    try:
        records = load_npt_records()
        records = apply_filters(records, phase, None, responsible_party, start_date, end_date)
        return {"status": "success", "data": group_by_key(records, "category")}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-phase")
async def get_by_phase(
    responsible_party: Optional[List[str]] = Query(None, description="Filter by one or more responsible parties"),
    category:          Optional[str]       = Query(None, description="Filter by category"),
    start_date:        Optional[str]       = Query(None, description="Start date YYYY-MM-DD"),
    end_date:          Optional[str]       = Query(None, description="End date YYYY-MM-DD"),
):
    """Get NPT breakdown by phase with optional filters."""
    try:
        records = load_npt_records()
        records = apply_filters(records, None, category, responsible_party, start_date, end_date)
        return {"status": "success", "data": group_by_key(records, "phase")}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-responsible-party")
async def get_by_responsible_party(
    phase:      Optional[str] = Query(None, description="Filter by phase"),
    category:   Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date:   Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """Get NPT breakdown by responsible party with optional filters."""
    try:
        records = load_npt_records()
        records = apply_filters(records, phase, category, None, start_date, end_date)
        return {"status": "success", "data": group_by_key(records, "responsible_party")}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-month")
async def get_by_month(
    responsible_party: Optional[List[str]] = Query(None, description="Filter by one or more responsible parties"),
    phase:             Optional[str]       = Query(None, description="Filter by phase"),
    category:          Optional[str]       = Query(None, description="Filter by category"),
    start_date:        Optional[str]       = Query(None, description="Start date YYYY-MM-DD"),
    end_date:          Optional[str]       = Query(None, description="End date YYYY-MM-DD"),
):
    """Get NPT breakdown by month with optional filters."""
    try:
        records = load_npt_records()
        records = apply_filters(records, phase, category, responsible_party, start_date, end_date)
        return {"status": "success", "data": group_by_month(records)}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/phases")
async def get_phases():
    """Get all phases for dropdown menus."""
    return {"status": "success", "data": [{"id": str(i), "name": p} for i, p in enumerate(PHASES)]}


@router.get("/categories")
async def get_categories():
    """Get all categories for dropdown menus."""
    return {"status": "success", "data": [{"id": str(i), "name": c} for i, c in enumerate(CATEGORIES)]}


@router.get("/responsible-parties")
async def get_responsible_parties():
    """Get all responsible parties for dropdown menus."""
    return {"status": "success", "data": [{"id": str(i), "name": p} for i, p in enumerate(RESPONSIBLE_PARTIES)]}


@router.get("/wells")
async def get_wells():
    """Get all wells for dropdown menus."""
    return {"status": "success", "data": [{"id": "1", "name": WELL_NAME}]}