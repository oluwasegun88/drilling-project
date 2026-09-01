from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseRepository(ABC):
    """
    Abstract base class for all repository classes.

    Provides a common interface and shared Firestore collection
    access for all child repositories. Every repository in the
    project must inherit from this class and implement the
    abstract methods.

    Attributes:
        db:              Firestore database client instance.
        collection_name: Name of the Firestore collection this
                         repository manages.
    """

    def __init__(self, db, collection_name: str):
        self.db              = db
        self.collection_name = collection_name

    @property
    def collection(self):
        """Returns the Firestore collection reference."""
        return self.db.collection(self.collection_name)

    @abstractmethod
    async def find_by_month(
        self,
        year: int,
        month: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch all records for a given month.
        Must be implemented by every child repository.
        """
        pass

    @abstractmethod
    async def find_by_day(
        self,
        year: int,
        month: int,
        day: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch all records for a given day.
        Must be implemented by every child repository.
        """
        pass