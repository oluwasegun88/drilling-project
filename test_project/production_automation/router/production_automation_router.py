import sys
import io
import logging
import calendar
from datetime  import datetime
from pathlib   import Path
from typing    import Optional

from fastapi           import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))

from firebase_database.setup_firebase import db as firestore_db
from production_automation.repository.production_automation_repository import ProductionAutomationRepository
from production_automation.service.production_automation_service       import ProductionAutomationService
from production_automation.exporters.csv_exporter                      import CSVExporter
from production_automation.exporters.pdf_exporter                      import PDFExporter
from email_config  import EmailConfig
from email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/production", tags=["Production Automation"])

# ── Shared instances ──────────────────────────────────────────────────────────
csv_exporter  = CSVExporter()
pdf_exporter  = PDFExporter()
email_config  = EmailConfig.from_env()
email_service = EmailService(email_config)

ASSETS = ["OML 152", "OML 24", "OML 147"]


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_repository() -> ProductionAutomationRepository:
    return ProductionAutomationRepository(firestore_db)

def get_service(
    repo: ProductionAutomationRepository = Depends(get_repository)
) -> ProductionAutomationService:
    return ProductionAutomationService(repo)


# ── Shared helper ─────────────────────────────────────────────────────────────

def stream_file(
    file_bytes: bytes, filename: str, media_type: str
) -> StreamingResponse:
    """Return a StreamingResponse that triggers a file download."""
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length":      str(len(file_bytes)),
        },
    )


# ── CRON job functions (called by the scheduler in main.py) ──────────────────

async def run_daily_report_job():
    """
    CRON Job — runs every day at 10:00 PM.
    Fetches today's production records and sends
    a separate email for each asset with CSV and PDF attached.
    """
    now   = datetime.now()
    year  = now.year
    month = now.month
    day   = now.day

    logger.info("=== Daily CRON started | %d-%02d-%02d ===", year, month, day)

    repo    = get_repository()
    service = ProductionAutomationService(repo)

    for asset in ASSETS:
        try:
            filters        = {"asset": asset}
            records, total = await service.get_daily_production(
                year, month, day, filters
            )

            if not records:
                logger.warning("No daily records for %s on %d-%02d-%02d",
                               asset, year, month, day)
                continue

            # Generate CSV and PDF
            csv_bytes, csv_filename = csv_exporter.export_daily(
                records, year, month, day, asset
            )
            pdf_bytes, pdf_filename = pdf_exporter.export_daily(
                records, year, month, day, asset
            )

            date_str = f"{year}-{month:02d}-{day:02d}"

            # Send email
            email_service.send_daily_report(
                csv_bytes=csv_bytes,     csv_filename=csv_filename,
                pdf_bytes=pdf_bytes,     pdf_filename=pdf_filename,
                date_str=date_str,
                asset=asset,
                total_records=total,
            )

            logger.info("✅ Daily report sent | asset=%s records=%d",
                        asset, total)

        except Exception as e:
            logger.error("❌ Daily report failed | asset=%s error=%s", asset, e)

    logger.info("=== Daily CRON completed ===")


async def run_monthly_report_job():
    """
    CRON Job — runs every day at 10:00 PM.
    Checks if today is the last day of the month.
    If yes, sends the monthly summary for each asset.
    """
    now      = datetime.now()
    year     = now.year
    month    = now.month
    day      = now.day
    last_day = calendar.monthrange(year, month)[1]

    # Only run on the last day of the month
    if day != last_day:
        logger.info("Monthly CRON skipped — today (%d) is not last day (%d)",
                    day, last_day)
        return

    logger.info("=== Monthly CRON started | %d-%02d ===", year, month)

    repo    = get_repository()
    service = ProductionAutomationService(repo)

    for asset in ASSETS:
        try:
            filters        = {"asset": asset}
            records, total = await service.get_monthly_production(
                year, month, filters
            )

            if not records:
                logger.warning("No monthly records for %s %d-%02d",
                               asset, year, month)
                continue

            # Generate CSV and PDF
            csv_bytes, csv_filename = csv_exporter.export_monthly(
                records, year, month, asset
            )
            pdf_bytes, pdf_filename = pdf_exporter.export_monthly(
                records, year, month, asset
            )

            # Send email
            email_service.send_monthly_report(
                csv_bytes=csv_bytes,     csv_filename=csv_filename,
                pdf_bytes=pdf_bytes,     pdf_filename=pdf_filename,
                year=year,               month=month,
                asset=asset,
                total_records=total,
            )

            logger.info("✅ Monthly report sent | asset=%s records=%d",
                        asset, total)

        except Exception as e:
            logger.error("❌ Monthly report failed | asset=%s error=%s", asset, e)

    logger.info("=== Monthly CRON completed ===")


# ── Daily CSV ─────────────────────────────────────────────────────────────────

@router.get("/report/daily-csv")
async def daily_production_csv(
    year:           int           = Query(..., description="Year e.g. 2025"),
    month:          int           = Query(..., ge=1, le=12),
    day:            int           = Query(..., ge=1, le=31),
    asset:          Optional[str] = Query(None),
    include_totals: bool          = Query(True),
    service: ProductionAutomationService = Depends(get_service),
):
    """Download a single day's production records as CSV."""
    try:
        filters    = {"asset": asset} if asset else {}
        records, _ = await service.get_daily_production(
            year, month, day, filters)

        if not records:
            raise HTTPException(404,
                detail=f"No records for {year}-{month:02d}-{day:02d}"
                       + (f" (asset: {asset})" if asset else ""))

        file_bytes, filename = csv_exporter.export_daily(
            records, year, month, day, asset,
            include_totals=include_totals)

        return stream_file(file_bytes, filename, "text/csv")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("daily-csv error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── Daily PDF ─────────────────────────────────────────────────────────────────

@router.get("/report/daily-pdf")
async def daily_production_pdf(
    year:  int           = Query(..., description="Year e.g. 2025"),
    month: int           = Query(..., ge=1, le=12),
    day:   int           = Query(..., ge=1, le=31),
    asset: Optional[str] = Query(None),
    service: ProductionAutomationService = Depends(get_service),
):
    """Download a single day's production records as PDF."""
    try:
        filters    = {"asset": asset} if asset else {}
        records, _ = await service.get_daily_production(
            year, month, day, filters)

        if not records:
            raise HTTPException(404,
                detail=f"No records for {year}-{month:02d}-{day:02d}"
                       + (f" (asset: {asset})" if asset else ""))

        file_bytes, filename = pdf_exporter.export_daily(
            records, year, month, day, asset)

        return stream_file(file_bytes, filename, "application/pdf")

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(500, detail=str(e))
    except Exception as e:
        logger.error("daily-pdf error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── Monthly CSV ───────────────────────────────────────────────────────────────

@router.get("/report/monthly-csv")
async def monthly_production_csv(
    year:           int           = Query(..., description="Year e.g. 2025"),
    month:          int           = Query(..., ge=1, le=12),
    asset:          Optional[str] = Query(None),
    include_totals: bool          = Query(True),
    service: ProductionAutomationService = Depends(get_service),
):
    """Download a full month's production summary as CSV."""
    try:
        filters    = {"asset": asset} if asset else {}
        records, _ = await service.get_monthly_production(
            year, month, filters)

        if not records:
            raise HTTPException(404,
                detail=f"No records for {year}-{month:02d}"
                       + (f" (asset: {asset})" if asset else ""))

        file_bytes, filename = csv_exporter.export_monthly(
            records, year, month, asset,
            include_totals=include_totals)

        return stream_file(file_bytes, filename, "text/csv")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("monthly-csv error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── Monthly PDF ───────────────────────────────────────────────────────────────

@router.get("/report/monthly-pdf")
async def monthly_production_pdf(
    year:  int           = Query(..., description="Year e.g. 2025"),
    month: int           = Query(..., ge=1, le=12),
    asset: Optional[str] = Query(None),
    service: ProductionAutomationService = Depends(get_service),
):
    """Download a full month's production summary as PDF."""
    try:
        filters    = {"asset": asset} if asset else {}
        records, _ = await service.get_monthly_production(
            year, month, filters)

        if not records:
            raise HTTPException(404,
                detail=f"No records for {year}-{month:02d}"
                       + (f" (asset: {asset})" if asset else ""))

        file_bytes, filename = pdf_exporter.export_monthly(
            records, year, month, asset)

        return stream_file(file_bytes, filename, "application/pdf")

    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(500, detail=str(e))
    except Exception as e:
        logger.error("monthly-pdf error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── Preview ───────────────────────────────────────────────────────────────────

@router.get("/report/preview")
async def preview_production(
    year:  int           = Query(..., description="Year e.g. 2025"),
    month: int           = Query(..., ge=1, le=12),
    day:   Optional[int] = Query(None, description="Omit for monthly preview"),
    asset: Optional[str] = Query(None),
    service: ProductionAutomationService = Depends(get_service),
):
    """Preview first 5 records for a day or month before downloading."""
    try:
        filters = {"limit": 5}
        if asset:
            filters["asset"] = asset

        if day:
            records, total = await service.get_daily_production(
                year, month, day, filters)
            period = f"{year}-{month:02d}-{day:02d}"
        else:
            records, total = await service.get_monthly_production(
                year, month, filters)
            period = f"{year}-{month:02d}"

        return {
            "period":        period,
            "asset":         asset or "all",
            "total_records": total,
            "preview_count": len(records),
            "sample":        records,
        }

    except Exception as e:
        logger.error("preview error: %s", e)
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ── Manual trigger endpoints (test emails without waiting for 10PM) ───────────

@router.get("/report/trigger-daily-email")
async def trigger_daily_email(
    year:  int           = Query(None, description="Year e.g. 2025"),
    month: int           = Query(None, description="Month (1-12)"),
    day:   int           = Query(None, description="Day (1-31)"),
    asset: Optional[str] = Query(None, description="Specific asset to test"),
):
    """
    Manually trigger the daily email report.
    Pass year, month, day to test with a specific date.
    """
    try:
        from datetime import datetime
        now   = datetime.now()
        year  = year  or now.year
        month = month or now.month
        day   = day   or now.day

        assets  = [asset] if asset else ASSETS
        results = []

        repo    = get_repository()
        service = ProductionAutomationService(repo)

        for a in assets:
            filters        = {"asset": a}
            records, total = await service.get_daily_production(
                year, month, day, filters
            )

            print(f"DEBUG trigger | asset={a} date={year}-{month:02d}-{day:02d} records={total}")

            if not records:
                results.append({
                    "asset":   a,
                    "status":  "skipped",
                    "reason":  f"No records found for {year}-{month:02d}-{day:02d}",
                    "records": 0,
                })
                continue

            csv_bytes, csv_filename = csv_exporter.export_daily(records, year, month, day, a)
            pdf_bytes, pdf_filename = pdf_exporter.export_daily(records, year, month, day, a)
            date_str                = f"{year}-{month:02d}-{day:02d}"

            email_service.send_daily_report(
                csv_bytes=csv_bytes,   csv_filename=csv_filename,
                pdf_bytes=pdf_bytes,   pdf_filename=pdf_filename,
                date_str=date_str,     asset=a,
                total_records=total,
            )

            results.append({
                "asset":   a,
                "status":  "sent",
                "records": total,
                "date":    date_str,
            })

        return {"status": "success", "results": results}

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))

@router.get("/report/trigger-monthly-email")
async def trigger_monthly_email():
    """
    Manually trigger the monthly email report right now.
    Useful for testing without waiting for end of month.
    """
    try:
        await run_monthly_report_job()
        return {"status": "success", "message": "Monthly email report triggered"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ── Debug ─────────────────────────────────────────────────────────────────────

@router.get("/report/debug-fetch")
async def debug_fetch(
    repo: ProductionAutomationRepository = Depends(get_repository),
):
    """Fetch 5 raw documents for debugging — remove in production."""
    try:
        results = []
        for doc in repo.collection.limit(5).stream():
            data       = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return {"count": len(results), "documents": results}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, detail=str(e))