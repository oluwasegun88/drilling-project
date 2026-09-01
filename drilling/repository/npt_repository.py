import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from drilling.base.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class NPTRepository(BaseRepository):
    

    def __init__(self, db):
        super().__init__(db, collection_name="nptRecords")

   
    def _doc_to_dict(self, doc) -> Dict[str, Any]:
        
        data       = doc.to_dict()
        data["id"] = doc.id
        return data

    def _apply_well_filter(self, query, well: Optional[str]):
        
        if well:
            query = query.where("well", "==", well)
        return query

   
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        
        try:
            # Calculate days from hours automatically
            if data.get("hours"):
                data["days"] = round(data["hours"] / 24, 6)

            doc_ref = self.collection.document()
            doc_ref.set(data)
            data["id"] = doc_ref.id
            logger.info("Created NPT record | id=%s well=%s",
                        doc_ref.id, data.get("well"))
            return data
        except Exception as e:
            logger.error("Error creating NPT record: %s", e)
            raise

    async def fetch_all(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        
        try:
            filters = filters or {}
            query   = self.collection

            if filters.get("well"):
                query = query.where("well", "==", filters["well"])
            if filters.get("phase"):
                query = query.where("phase", "==", filters["phase"])
            if filters.get("category"):
                query = query.where("category", "==", filters["category"])
            if filters.get("responsible_party"):
                query = query.where("responsible_party", "==",
                                    filters["responsible_party"])
            if filters.get("start_date"):
                query = query.where("date", ">=", filters["start_date"])
            if filters.get("end_date"):
                query = query.where("date", "<=", filters["end_date"])

            return [self._doc_to_dict(doc) for doc in query.stream()]

        except Exception as e:
            logger.error("Error fetching NPT records: %s", e)
            raise

    async def fetch_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        
        try:
            doc = self.collection.document(doc_id).get()
            if doc.exists:
                return self._doc_to_dict(doc)
            return None
        except Exception as e:
            logger.error("Error fetching NPT record %s: %s", doc_id, e)
            raise

    async def update(
        self, doc_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        
        try:
            doc_ref = self.collection.document(doc_id)
            if not doc_ref.get().exists:
                return None

            # Recalculate days if hours is being updated
            if data.get("hours"):
                data["days"] = round(data["hours"] / 24, 6)

            clean_data = {k: v for k, v in data.items() if v is not None}
            doc_ref.update(clean_data)
            updated       = doc_ref.get().to_dict()
            updated["id"] = doc_id
            logger.info("Updated NPT record | id=%s", doc_id)
            return updated
        except Exception as e:
            logger.error("Error updating NPT record %s: %s", doc_id, e)
            raise

    async def delete(self, doc_id: str) -> bool:
        
        try:
            doc_ref = self.collection.document(doc_id)
            if not doc_ref.get().exists:
                return False
            doc_ref.delete()
            logger.info("Deleted NPT record | id=%s", doc_id)
            return True
        except Exception as e:
            logger.error("Error deleting NPT record %s: %s", doc_id, e)
            raise

    

    async def fetch_for_dashboard(
        self, well: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date:   Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        
        try:
            query = self.collection
            query = self._apply_well_filter(query, well)

            if start_date:
                query = query.where("date", ">=", start_date)
            if end_date:
                query = query.where("date", "<=", end_date)

            return [self._doc_to_dict(doc) for doc in query.stream()]
        except Exception as e:
            logger.error("Error fetching dashboard data: %s", e)
            raise