from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseExporter(ABC):
    """
    Abstract base class for all exporter classes.

    Defines a common interface for converting raw Firestore
    records into downloadable file formats (CSV, PDF, etc.).
    Every exporter must inherit from this class and implement
    the abstract methods.

    Subclasses:
        CSVExporter  — exports data as a CSV spreadsheet
        PDFExporter  — exports data as a formatted PDF report
    """

    # ── Column definitions (shared by all exporters) ─────────────────────────

    COLUMN_HEADERS: Dict[str, str] = {
        "id":               "Record ID",
        "asset":            "Asset",
        "date":             "Date",
        "productionString": "Production String",
        "gross":            "Gross Production (bbl)",
        "oil":              "Oil Volume (bbl)",
        "gas":              "Gas Volume (Mscf)",
        "water":            "Water Volume (bbl)",
        "remark":           "Remark",
    }

    NUMERIC_FIELDS = ["gross", "oil", "gas", "water"]

    # ── Abstract methods ──────────────────────────────────────────────────────

    @abstractmethod
    def export_daily(
        self,
        records: List[Dict[str, Any]],
        year: int,
        month: int,
        day: int,
        asset: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Export a single day's records.
        Returns (file_bytes, filename).
        """
        pass

    @abstractmethod
    def export_monthly(
        self,
        records: List[Dict[str, Any]],
        year: int,
        month: int,
        asset: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """
        Export a full month's records.
        Returns (file_bytes, filename).
        """
        pass

    # ── Shared helper methods (available to all child exporters) ─────────────

    def flatten_records(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Flatten nested productionData array into individual rows.
        Each productionString becomes its own row with parent
        fields (id, asset, date) repeated on every row.
        """
        rows = []
        for record in records:
            parent_id    = record.get("id",    "")
            parent_asset = record.get("asset", "")
            parent_date  = record.get("date",  "")

            for item in record.get("productionData", []):
                rows.append({
                    "id":               parent_id,
                    "asset":            parent_asset,
                    "date":             parent_date,
                    "productionString": item.get("productionString", ""),
                    "gross":            item.get("gross"),
                    "oil":              item.get("oil"),
                    "gas":              item.get("gas"),
                    "water":            item.get("water"),
                    "remark":           item.get("remark", ""),
                })

        return rows

    def calculate_totals(
        self, rows: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate grand totals for all numeric fields."""
        totals = {f: 0.0 for f in self.NUMERIC_FIELDS}
        for row in rows:
            for field in self.NUMERIC_FIELDS:
                val = row.get(field)
                if isinstance(val, (int, float)):
                    totals[field] += val
        return {k: round(v, 4) for k, v in totals.items()}

    def build_filename(
        self,
        report_type: str,
        extension: str,
        year: int,
        month: int,
        day: Optional[int] = None,
        asset: Optional[str] = None,
    ) -> str:
        """Build a consistent filename for any report."""
        asset_part = f"_{asset}" if asset else ""
        date_part  = (f"{year}-{month:02d}-{day:02d}"
                      if day else f"{year}-{month:02d}")
        return f"{report_type}{asset_part}_{date_part}.{extension}"