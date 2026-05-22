from google.cloud import firestore
from typing import Optional, Dict, Any, List, Tuple
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)


class TestProjectRepository:

    def __init__(self, db):
        self.db = db
        self.collection_name = "actualProduction"


    @property
    def collection(self):
        return self.db.collection(self.collection_name)
    
    def sanitize_firestore_data(self, data):
        """
        Recursively sanitize Firestore data for JSON serialization.
        Converts NaN/Infinity to None.
        """

        if isinstance(data, dict):
            return {
                key: self.sanitize_firestore_data(value)
                for key, value in data.items()
            }

        elif isinstance(data, list):
            return [self.sanitize_firestore_data(item) for item in data]

        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None
            return data

        elif isinstance(data, datetime):
            return data.isoformat()

        return data
    

    async def find_all(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
       
        try:
            filters = filters or {}
            query = self.collection
            
            # Apply filters
            if filters.get("asset"):
                query = query.where("asset", "==", filters["asset"])

            
            # Get total count (without pagination)
            total_snapshot = query.get()
            total = len(total_snapshot)
            
            # Apply pagination
            limit = filters.get("limit", 100)
            offset = filters.get("offset", 0)
            
            # Apply offset using start after
            if offset > 0:
                last_doc = await self.get_last_document(offset)
                if last_doc:
                    query = query.start_after(last_doc)
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            snapshot = query.get()
            
            # Convert to list of dictionaries
            data = []
            for doc in snapshot:
                # doc_data = doc.to_dict()
                doc_data = self.sanitize_firestore_data(doc.to_dict())
                doc_data["id"] = doc.id
                data.append(doc_data)
            
            return data, total
            
        except Exception as e:
            logger.error(f"Error finding records: {e}")
            raise