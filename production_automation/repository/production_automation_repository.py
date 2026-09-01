import sys
import logging
import calendar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from utils.data_clean_up import DataCleanUp
from production_automation.base.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ProductionAutomationRepository(BaseRepository):
    """
    Repository for the actualProduction Firestore collection.

    Inherits from BaseRepository and implements all abstract
    methods for fetching production records by day or month.

    Responsibilities:
        - Talk directly to the Firestore database
        - Apply filters (asset, date range, pagination)
        - Sanitize and return clean data dictionaries

    This is the ONLY class in the project that should
    communicate with the database directly.
    """

    def __init__(self, db):
        super().__init__(db, collection_name="actualProduction")
        self.data_clean_up = DataCleanUp()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _apply_asset_filter(self, query, filters: Dict[str, Any]):
        """Apply optional asset filter to a Firestore query."""
        if filters.get("asset"):
            query = query.where("asset", "==", filters["asset"])
        return query

    def _apply_pagination(self, query, filters: Dict[str, Any]):
        """Apply limit and offset pagination to a Firestore query."""
        limit  = filters.get("limit", 100)
        offset = filters.get("offset", 0)
        if offset > 0:
            docs = list(query.stream())
            if len(docs) > offset:
                query = query.start_after(docs[offset - 1])
        return query.limit(limit)

    def _stream_to_list(self, query) -> List[Dict[str, Any]]:
        """Execute a Firestore query and return a list of clean dicts."""
        data = []
        for doc in query.stream():
            doc_data       = self.data_clean_up.sanitize_firestore_data(doc.to_dict())
            doc_data["id"] = doc.id
            data.append(doc_data)
        return data

    # ── Public methods ────────────────────────────────────────────────────────

    async def find_by_day(
        self,
        year: int,
        month: int,
        day: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch all production records for a single day.

        Args:
            year:    The calendar year  (e.g. 2025).
            month:   The calendar month (1-12).
            day:     The calendar day   (1-31).
            filters: Optional dict with keys: asset, limit, offset.

        Returns:
            Tuple of (records list, total count before pagination).
        """
        try:
            filters  = filters or {}
            date_str = f"{year}-{month:02d}-{day:02d}"

            query = self.collection
            query = self._apply_asset_filter(query, filters)
            query = query.where("date", "==", date_str)

            total = len(list(query.stream()))

            print(f"DEBUG daily | date={date_str} "
                  f"asset={filters.get('asset', '*')} total={total}")

            query = self._apply_pagination(query, filters)
            data  = self._stream_to_list(query)

            logger.info("find_by_day | %s asset=%s returned=%d total=%d",
                        date_str, filters.get("asset", "*"), len(data), total)

            return data, total

        except Exception as e:
            logger.error("Error fetching records for %d-%02d-%02d: %s",
                         year, month, day, e)
            raise

    async def find_by_month(
        self,
        year: int,
        month: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch all production records for an entire month.

        Args:
            year:    The calendar year  (e.g. 2025).
            month:   The calendar month (1-12).
            filters: Optional dict with keys: asset, limit, offset.

        Returns:
            Tuple of (records list, total count before pagination).

        Raises:
            ValueError: If month is not between 1 and 12.
        """
        if not 1 <= month <= 12:
            raise ValueError(f"month must be between 1 and 12, got {month}")

        try:
            filters        = filters or {}
            first_day      = datetime(year, month, 1)
            last_day       = datetime(year, month,
                                      calendar.monthrange(year, month)[1])
            start_date_str = first_day.strftime("%Y-%m-%d")
            end_date_str   = last_day.strftime("%Y-%m-%d")

            query = self.collection
            query = self._apply_asset_filter(query, filters)
            query = query.where("date", ">=", start_date_str)
            query = query.where("date", "<=", end_date_str)

            total = len(list(query.stream()))

            print(f"DEBUG monthly | start={start_date_str} end={end_date_str} "
                  f"asset={filters.get('asset', '*')} total={total}")

            query = self._apply_pagination(query, filters)
            data  = self._stream_to_list(query)

            logger.info("find_by_month | %d-%02d asset=%s returned=%d total=%d",
                        year, month, filters.get("asset", "*"), len(data), total)

            return data, total

        except ValueError:
            raise
        except Exception as e:
            logger.error("Error fetching records for %d-%02d: %s",
                         year, month, e)
            raise