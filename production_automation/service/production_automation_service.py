import logging
from typing import Any, Dict, List, Optional, Tuple

from production_automation.base.base_service import BaseService

logger = logging.getLogger(__name__)


class ProductionAutomationService(BaseService):
    """
    Service class for production automation business logic.

    Inherits from BaseService and implements all abstract methods.
    Acts as the middleman between the router and the repository.

    Responsibilities:
        - Receive requests from the router
        - Apply any business rules or validations
        - Call the repository to fetch data
        - Return the data back to the router

    This class should NEVER talk to the database directly —
    it always goes through the repository.
    """

    def __init__(self, repository):
        super().__init__(repository)

    async def get_daily_production(
        self,
        year: int,
        month: int,
        day: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all production records for a single day.

        Args:
            year:    The calendar year  (e.g. 2025).
            month:   The calendar month (1-12).
            day:     The calendar day   (1-31).
            filters: Optional filters (asset, limit, offset).

        Returns:
            Tuple of (records list, total count).
        """
        logger.info("Service: get_daily_production | %d-%02d-%02d asset=%s",
                    year, month, day, (filters or {}).get("asset", "*"))

        return await self.repository.find_by_day(
            year=year, month=month, day=day, filters=filters
        )

    async def get_monthly_production(
        self,
        year: int,
        month: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all production records for an entire month.

        Args:
            year:    The calendar year  (e.g. 2025).
            month:   The calendar month (1-12).
            filters: Optional filters (asset, limit, offset).

        Returns:
            Tuple of (records list, total count).
        """
        logger.info("Service: get_monthly_production | %d-%02d asset=%s",
                    year, month, (filters or {}).get("asset", "*"))

        return await self.repository.find_by_month(
            year=year, month=month, filters=filters
        )