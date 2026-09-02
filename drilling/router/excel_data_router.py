"""
Temporary Excel Data Router
============================
Serves NPT data directly from the Excel file while Firebase
connection is being resolved. Drop this file into your
drilling/router/ folder and register it in drilling_module.py.

This router provides the same endpoints as the real dashboard
and NPT router but reads from the Excel file instead of Firestore.
"""

import logging
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/excel", tags=["Excel Data (Temporary)"])

# ── Excel file path ───────────────────────────────────────────────────────────
EXCEL_FILE = Path(__file__).parent.parent.parent / "Awoba NW 5 NPT_Drilling_Performance_Dashboard.xlsx"
WELL_NAME  = "Awoba NW 5"
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


def calculate_metrics(records, total_rig_hours=TOTAL_RIG_HOURS):
    """Calculate all dashboard metrics from records."""
    total_npt_hours = round(sum(r["hours"] for r in records), 4)
    total_npt_cost  = round(sum(r["npt_cost"] for r in records), 2)
    productive_hours = round(total_rig_hours - total_npt_hours, 4)
    npt_percent      = round((total_npt_hours / total_rig_hours * 100) if total_rig_hours > 0 else 0, 4)
    productive_pct   = round((productive_hours / total_rig_hours * 100) if total_rig_hours > 0 else 0, 4)

    def group_by(key):
        result = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
        for r in records:
            k = r.get(key) or "Unknown"
            result[k]["hours"] += r["hours"]
            result[k]["cost"]  += r["npt_cost"]
        return {k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
                for k, v in sorted(result.items())}

    def group_by_month():
        result = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
        for r in records:
            try:
                month = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%b-%Y")
            except Exception:
                month = "Unknown"
            result[month]["hours"] += r["hours"]
            result[month]["cost"]  += r["npt_cost"]
        return {k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
                for k, v in result.items()}

    return {
        "well":                     WELL_NAME,
        "total_rig_hours":          total_rig_hours,
        "total_rig_days":           round(total_rig_hours / 24, 4),
        "total_npt_hours":          total_npt_hours,
        "total_npt_days":           round(total_npt_hours / 24, 4),
        "overall_npt_percent":      npt_percent,
        "total_npt_cost":           total_npt_cost,
        "productive_hours":         productive_hours,
        "productive_days":          round(productive_hours / 24, 4),
        "productive_time_percent":  productive_pct,
        "total_records":            len(records),
        "npt_by_category":          group_by("category"),
        "npt_by_responsible_party": group_by("responsible_party"),
        "npt_by_phase":             group_by("phase"),
        "npt_by_month":             group_by_month(),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/npt")
async def get_all_npt_records(
    phase:             Optional[str] = Query(None),
    category:          Optional[str] = Query(None),
    responsible_party: Optional[str] = Query(None),
    start_date:        Optional[str] = Query(None),
    end_date:          Optional[str] = Query(None),
):
    """Get all NPT records from the Excel file."""
    try:
        records = load_npt_records()

        if phase:
            records = [r for r in records if r["phase"] == phase]
        if category:
            records = [r for r in records if r["category"] == category]
        if responsible_party:
            records = [r for r in records if r["responsible_party"] == responsible_party]
        if start_date:
            records = [r for r in records if r["date"] >= start_date]
        if end_date:
            records = [r for r in records if r["date"] <= end_date]

        return {"status": "success", "total": len(records), "data": records}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/metrics")
async def get_dashboard_metrics(
    total_rig_hours: Optional[float] = Query(2415.0),
):
    """Get all dashboard KPI metrics from the Excel file."""
    try:
        records = load_npt_records()
        metrics = calculate_metrics(records, total_rig_hours or TOTAL_RIG_HOURS)
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-category")
async def get_by_category():
    """Get NPT breakdown by category from Excel."""
    try:
        records = load_npt_records()
        result  = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
        for r in records:
            k = r["category"] or "Unknown"
            result[k]["hours"] += r["hours"]
            result[k]["cost"]  += r["npt_cost"]
        return {"status": "success", "data": {
            k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
            for k, v in sorted(result.items())
        }}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-phase")
async def get_by_phase():
    """Get NPT breakdown by phase from Excel."""
    try:
        records = load_npt_records()
        result  = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
        for r in records:
            k = r["phase"] or "Unknown"
            result[k]["hours"] += r["hours"]
            result[k]["cost"]  += r["npt_cost"]
        return {"status": "success", "data": {
            k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
            for k, v in sorted(result.items())
        }}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-responsible-party")
async def get_by_responsible_party():
    """Get NPT breakdown by responsible party from Excel."""
    try:
        records = load_npt_records()
        result  = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
        for r in records:
            k = r["responsible_party"] or "Unknown"
            result[k]["hours"] += r["hours"]
            result[k]["cost"]  += r["npt_cost"]
        return {"status": "success", "data": {
            k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
            for k, v in sorted(result.items())
        }}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/dashboard/by-month")
async def get_by_month():
    """Get NPT breakdown by month from Excel."""
    try:
        records = load_npt_records()
        result  = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
        for r in records:
            try:
                month = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%b-%Y")
            except Exception:
                month = "Unknown"
            result[month]["hours"] += r["hours"]
            result[month]["cost"]  += r["npt_cost"]
        return {"status": "success", "data": {
            k: {"hours": round(v["hours"], 4), "cost": round(v["cost"], 2)}
            for k, v in result.items()
        }}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/phases")
async def get_phases():
    """Get all phases."""
    return {"status": "success", "data": [{"id": str(i), "name": p} for i, p in enumerate(PHASES)]}


@router.get("/categories")
async def get_categories():
    """Get all categories."""
    return {"status": "success", "data": [{"id": str(i), "name": c} for i, c in enumerate(CATEGORIES)]}


@router.get("/responsible-parties")
async def get_responsible_parties():
    """Get all responsible parties."""
    return {"status": "success", "data": [{"id": str(i), "name": p} for i, p in enumerate(RESPONSIBLE_PARTIES)]}


@router.get("/wells")
async def get_wells():
    """Get all wells."""
    return {"status": "success", "data": [{"id": "1", "name": WELL_NAME}]}