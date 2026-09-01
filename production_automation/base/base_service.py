from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseService(ABC):
    """
    Abstract base class for all service classes.

    Acts as the middleman between the router and the repository.
    Contains business logic and coordinates data flow.
    Every service in the project must inherit from this class.

    Attributes:
        repository: The repository instance this service uses
                    to access the database.
    """

    def __init__(self, repository):
        self.repository = repository

    @abstractmethod
    async def get_daily_production(
        self,
        year: int,
        month: int,
        day: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve production records for a single day."""
        pass

    @abstractmethod
    async def get_monthly_production(
        self,
        year: int,
        month: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieve production records for a full month."""
        pass