import io
import logging
import calendar
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from production_automation.base.base_exporter import BaseExporter

logger = logging.getLogger(__name__)

# ── PDF styling constants ─────────────────────────────────────────────────────
DARK_BLUE  = "#1a3c5e"
LIGHT_BLUE = "#e8f0fe"
LIGHT_GREY = "#f5f7fa"


class PDFExporter(BaseExporter):
    """
    Exports production records as formatted PDF reports.

    Inherits from BaseExporter and implements export_daily
    and export_monthly methods for PDF format using reportlab.

    Each PDF includes:
        - A title block with date and asset information
        - A summary statistics box at the top
        - A detailed data table with alternating row colours
        - A grand total row at the bottom

    Requires: pip install reportlab
    """

    def _check_reportlab(self):
        """Verify reportlab is installed before attempting PDF generation."""
        try:
            import reportlab
        except ImportError:
            raise RuntimeError(
                "reportlab is required for PDF export. "
                "Install it with: pip install reportlab"
            )

    def _get_reportlab_imports(self):
        """Import and return all reportlab components."""
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        return (landscape, A4, colors, getSampleStyleSheet,
                ParagraphStyle, cm, SimpleDocTemplate,
                Paragraph, Spacer, Table, TableStyle)

    def _build_stats_table(self, stats, Table, TableStyle, colors, cm):
        """Build the summary statistics box at the top of the report."""
        col_w = 5 * cm
        data  = [
            [s["label"] for s in stats],
            [s["value"] for s in stats],
        ]
        table = Table(data, colWidths=[col_w] * len(stats))
        table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(DARK_BLUE)),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor(LIGHT_BLUE)),
            ("FONTNAME",      (0, 1), (-1, 1),  "Helvetica-Bold"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWHEIGHT",     (0, 0), (-1, -1), 20),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def _build_data_table(self, headers, rows, col_widths,
                          Table, TableStyle, colors):
        """Build the main data table with alternating row colours."""
        table_data  = [headers] + rows
        last_row    = len(table_data) - 1
        main_table  = Table(table_data, colWidths=col_widths, repeatRows=1)
        main_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),              colors.HexColor(DARK_BLUE)),
            ("TEXTCOLOR",     (0, 0), (-1, 0),              colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),              "Helvetica-Bold"),
            ("ALIGN",         (0, 0), (-1, -1),             "CENTER"),
            ("FONTSIZE",      (0, 0), (-1, -1),             8),
            ("ROWHEIGHT",     (0, 0), (-1, -1),             16),
            ("TOPPADDING",    (0, 0), (-1, -1),             4),
            ("BOTTOMPADDING", (0, 0), (-1, -1),             4),
            ("ROWBACKGROUNDS",(0, 1), (-1, last_row - 1),
             [colors.white, colors.HexColor(LIGHT_GREY)]),
            ("BACKGROUND",    (0, last_row), (-1, last_row),
             colors.HexColor(DARK_BLUE)),
            ("TEXTCOLOR",     (0, last_row), (-1, last_row), colors.white),
            ("FONTNAME",      (0, last_row), (-1, last_row), "Helvetica-Bold"),
            ("GRID",          (0, 0), (-1, -1),
             0.4, colors.HexColor("#cccccc")),
        ]))
        return main_table

    def _aggregate_by_day(
        self, flat_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate flat rows into daily totals per asset."""
        totals: Dict = defaultdict(
            lambda: {"gross": 0.0, "oil": 0.0, "gas": 0.0, "water": 0.0}
        )
        for row in flat_rows:
            key = (row.get("date", ""), row.get("asset", ""))
            for field in self.NUMERIC_FIELDS:
                val = row.get(field)
                if isinstance(val, (int, float)):
                    totals[key][field] += val

        return [
            {
                "date":  date,
                "asset": asset,
                "gross": round(v["gross"], 4),
                "oil":   round(v["oil"],   4),
                "gas":   round(v["gas"],   4),
                "water": round(v["water"], 4),
            }
            for (date, asset), v in sorted(totals.items())
        ]

    # ── Public methods ────────────────────────────────────────────────────────

    def export_daily(
        self,
        records: List[Dict[str, Any]],
        year: int,
        month: int,
        day: int,
        asset: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Export one day's production records as a formatted PDF.
        One row per productionString entry.
        """
        self._check_reportlab()
        (landscape, A4, colors, getSampleStyleSheet, ParagraphStyle,
         cm, SimpleDocTemplate, Paragraph, Spacer,
         Table, TableStyle) = self._get_reportlab_imports()

        if not records:
            raise ValueError(
                f"No records for {year}-{month:02d}-{day:02d}.")

        flat_rows   = self.flatten_records(records)
        totals      = self.calculate_totals(flat_rows)
        date_label  = f"{year}-{month:02d}-{day:02d}"
        asset_label = asset or "All Assets"

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(
            buffer, pagesize=landscape(A4),
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=1.5*cm,  bottomMargin=1.5*cm,
        )
        styles = getSampleStyleSheet()
        story  = []

        # Title
        story.append(Paragraph(
            "Daily Production Report",
            ParagraphStyle("T", parent=styles["Title"],
                           fontSize=16, spaceAfter=4)))
        story.append(Paragraph(
            f"{date_label}  |  Asset: {asset_label}",
            ParagraphStyle("S", parent=styles["Normal"],
                           fontSize=10, spaceAfter=16,
                           textColor=colors.grey)))

        # Summary stats
        story.append(self._build_stats_table([
            {"label": "Total Strings",      "value": str(len(flat_rows))},
            {"label": "Gross (bbl)",        "value": f"{totals['gross']:,.2f}"},
            {"label": "Oil (bbl)",          "value": f"{totals['oil']:,.2f}"},
            {"label": "Gas (Mscf)",         "value": f"{totals['gas']:,.2f}"},
            {"label": "Water (bbl)",        "value": f"{totals['water']:,.2f}"},
        ], Table, TableStyle, colors, cm))
        story.append(Spacer(1, 20))

        # Detail table
        story.append(Paragraph(
            "Production String Breakdown", styles["Heading2"]))
        story.append(Spacer(1, 8))

        headers = ["Asset", "Production String",
                   "Gross (bbl)", "Oil (bbl)", "Gas (Mscf)",
                   "Water (bbl)", "Remark"]

        rows = [[
            r.get("asset", ""),
            r.get("productionString", ""),
            f"{r['gross']:,.2f}"  if isinstance(r.get("gross"),  (int, float)) else "",
            f"{r['oil']:,.2f}"    if isinstance(r.get("oil"),    (int, float)) else "",
            f"{r['gas']:,.2f}"    if isinstance(r.get("gas"),    (int, float)) else "",
            f"{r['water']:,.2f}"  if isinstance(r.get("water"),  (int, float)) else "",
            r.get("remark", "") or "",
        ] for r in flat_rows]

        # Totals row
        rows.append(["TOTAL", "",
                      f"{totals['gross']:,.2f}", f"{totals['oil']:,.2f}",
                      f"{totals['gas']:,.2f}",   f"{totals['water']:,.2f}", ""])

        story.append(self._build_data_table(
            headers, rows,
            [3.5*cm, 5.5*cm, 4*cm, 4*cm, 4*cm, 4*cm, 4*cm],
            Table, TableStyle, colors
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        filename  = self.build_filename(
            "daily_production", "pdf", year, month, day, asset)

        logger.info("PDFExporter.export_daily | %d-%02d-%02d rows=%d",
                    year, month, day, len(flat_rows))

        return pdf_bytes, filename

    def export_monthly(
        self,
        records: List[Dict[str, Any]],
        year: int,
        month: int,
        asset: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Export a full month's production as a formatted PDF.
        One row per (date, asset) combination with daily totals.
        """
        self._check_reportlab()
        (landscape, A4, colors, getSampleStyleSheet, ParagraphStyle,
         cm, SimpleDocTemplate, Paragraph, Spacer,
         Table, TableStyle) = self._get_reportlab_imports()

        if not records:
            raise ValueError(f"No records for {year}-{month:02d}.")

        flat_rows    = self.flatten_records(records)
        summary_rows = self._aggregate_by_day(flat_rows)
        totals       = self.calculate_totals(flat_rows)
        month_label  = f"{calendar.month_name[month]} {year}"
        asset_label  = asset or "All Assets"

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(
            buffer, pagesize=landscape(A4),
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=1.5*cm,  bottomMargin=1.5*cm,
        )
        styles = getSampleStyleSheet()
        story  = []

        # Title
        story.append(Paragraph(
            "Monthly Production Report",
            ParagraphStyle("T", parent=styles["Title"],
                           fontSize=16, spaceAfter=4)))
        story.append(Paragraph(
            f"{month_label}  |  Asset: {asset_label}",
            ParagraphStyle("S", parent=styles["Normal"],
                           fontSize=10, spaceAfter=16,
                           textColor=colors.grey)))

        # Summary stats
        story.append(self._build_stats_table([
            {"label": "Days in Month",  "value": str(calendar.monthrange(year, month)[1])},
            {"label": "Gross (bbl)",    "value": f"{totals['gross']:,.2f}"},
            {"label": "Oil (bbl)",      "value": f"{totals['oil']:,.2f}"},
            {"label": "Gas (Mscf)",     "value": f"{totals['gas']:,.2f}"},
            {"label": "Water (bbl)",    "value": f"{totals['water']:,.2f}"},
        ], Table, TableStyle, colors, cm))
        story.append(Spacer(1, 20))

        # Daily breakdown table
        story.append(Paragraph(
            "Daily Production Breakdown", styles["Heading2"]))
        story.append(Spacer(1, 8))

        headers = ["Date", "Asset", "Gross (bbl)",
                   "Oil (bbl)", "Gas (Mscf)", "Water (bbl)"]

        rows = [[
            r.get("date",  ""),
            r.get("asset", ""),
            f"{r.get('gross', 0):,.2f}",
            f"{r.get('oil',   0):,.2f}",
            f"{r.get('gas',   0):,.2f}",
            f"{r.get('water', 0):,.2f}",
        ] for r in summary_rows]

        rows.append(["TOTAL", "",
                     f"{totals['gross']:,.2f}", f"{totals['oil']:,.2f}",
                     f"{totals['gas']:,.2f}",   f"{totals['water']:,.2f}"])

        story.append(self._build_data_table(
            headers, rows,
            [3.5*cm, 5*cm, 5*cm, 5*cm, 5*cm, 5*cm],
            Table, TableStyle, colors
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        filename  = self.build_filename(
            "monthly_production", "pdf", year, month, asset=asset)

        logger.info("PDFExporter.export_monthly | %d-%02d rows=%d",
                    year, month, len(summary_rows))

        return pdf_bytes, filename