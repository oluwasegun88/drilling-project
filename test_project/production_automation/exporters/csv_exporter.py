import csv
import io
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from production_automation.base.base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """
    Exports production records as CSV files.

    Inherits from BaseExporter and implements export_daily
    and export_monthly methods for CSV format.

    The CSV uses UTF-8 with BOM encoding so it opens correctly
    in Microsoft Excel without garbled characters.
    """

    # ── Private helpers ───────────────────────────────────────────────────────

    def _write_csv(
        self,
        fields: List[str],
        rows: List[Dict[str, Any]],
        include_totals: bool = True,
        label_field: str = "id",
    ) -> bytes:
        """Write rows to a CSV buffer and return encoded bytes."""
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\r\n",
        )

        # Human-readable header row
        writer.writerow(
            {f: self.COLUMN_HEADERS.get(f, f.replace("_", " ").title())
             for f in fields}
        )

        # Data rows
        writer.writerows(rows)

        # Totals row
        if include_totals and rows:
            totals  = self.calculate_totals(rows)
            summary = {f: "" for f in fields}
            summary[label_field] = "TOTAL"
            summary.update({k: v for k, v in totals.items() if k in fields})
            writer.writerow(summary)

        return buffer.getvalue().encode("utf-8-sig")

    def _aggregate_by_day(
        self, flat_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate flat rows into daily totals per asset.
        Returns one summary row per (date, asset) combination.
        """
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
                "asset": asset,
                "date":  date,
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
        include_totals: bool = True,
    ) -> Tuple[bytes, str]:
        """
        Export one day's production records as a flat CSV.
        One row per productionString entry.
        """
        if not records:
            raise ValueError(
                f"No records for {year}-{month:02d}-{day:02d}.")

        fields    = list(self.COLUMN_HEADERS.keys())
        flat_rows = self.flatten_records(records)
        csv_bytes = self._write_csv(fields, flat_rows, include_totals)
        filename  = self.build_filename(
            "daily_production", "csv", year, month, day, asset)

        logger.info("CSVExporter.export_daily | %d-%02d-%02d rows=%d",
                    year, month, day, len(flat_rows))

        return csv_bytes, filename

    def export_monthly(
        self,
        records: List[Dict[str, Any]],
        year: int,
        month: int,
        asset: Optional[str] = None,
        include_totals: bool = True,
    ) -> Tuple[bytes, str]:
        """
        Export a full month's production as a summarised CSV.
        One row per (date, asset) combination with daily totals.
        """
        if not records:
            raise ValueError(f"No records for {year}-{month:02d}.")

        fields        = ["asset", "date", "gross", "oil", "gas", "water"]
        flat_rows     = self.flatten_records(records)
        summary_rows  = self._aggregate_by_day(flat_rows)
        csv_bytes     = self._write_csv(
            fields, summary_rows, include_totals, label_field="asset")
        filename      = self.build_filename(
            "monthly_production", "csv", year, month, asset=asset)

        logger.info("CSVExporter.export_monthly | %d-%02d rows=%d",
                    year, month, len(summary_rows))

        return csv_bytes, filename