from google.cloud import firestore
from typing import Optional, Dict, Any, List, Tuple
import logging
import math
from datetime import datetime
from utils.data_clean_up import DataCleanUp

logger = logging.getLogger(__name__)


class TestProjectRepository:

    def __init__(self, db):
        self.db = db
        self.collection_name = "actualProduction"
        self.data_clean_up = DataCleanUp()


    @property
    def collection(self):
        return self.db.collection(self.collection_name)
    

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
                doc_data = self.data_clean_up.sanitize_firestore_data(doc.to_dict())
                doc_data["id"] = doc.id
                data.append(doc_data)
            
            return data, total
            
        except Exception as e:
            logger.error(f"Error finding records: {e}")
            raise
    

    async def find_by_date_range(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
       
        try:
            filters = filters or {}
            query = self.collection
            
            # Apply filters
            
            if filters.get("asset"):
                query = query.where("asset", "==", filters["asset"])

            if filters.get("start_date"):
                # Convert to datetime object
                start_date_obj = datetime.strptime(filters["start_date"], "%Y-%m-%d")

                # Format date as string
                start_date_str = start_date_obj.strftime("%Y-%m-%d")

                query = query.where("date", ">=", start_date_str)

            if filters.get("end_date"):
                # Convert to datetime object
                end_date_obj = datetime.strptime(filters["end_date"], "%Y-%m-%d")

                # Format date as string
                end_date_str = end_date_obj.strftime("%Y-%m-%d")

                query = query.where("date", "<=", end_date_str)

            
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
            #snapshot = query.get()

            snapshot = query.stream()
            
            # Convert to list of dictionaries
            data = []
            for doc in snapshot:
                # doc_data = doc.to_dict()
                doc_data = self.data_clean_up.sanitize_firestore_data(doc.to_dict())
                doc_data["id"] = doc.id
                data.append(doc_data)
            
            return data, total
            
        except Exception as e:
            logger.error(f"Error finding records: {e}")
            raise