import logging
from typing import Any, Dict, List, Optional

from drilling.base.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GenericRepository(BaseRepository):
   

    def __init__(self, db, collection_name: str):
        super().__init__(db, collection_name)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        
        try:
            doc_ref = self.collection.document()
            doc_ref.set(data)
            data["id"] = doc_ref.id
            logger.info("Created document in %s | id=%s",
                        self.collection_name, doc_ref.id)
            return data
        except Exception as e:
            logger.error("Error creating document in %s: %s",
                         self.collection_name, e)
            raise

    async def fetch_all(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        
        try:
            query = self.collection
            docs  = query.stream()
            data  = []
            for doc in docs:
                doc_data       = doc.to_dict()
                doc_data["id"] = doc.id
                data.append(doc_data)
            return data
        except Exception as e:
            logger.error("Error fetching documents from %s: %s",
                         self.collection_name, e)
            raise

    async def fetch_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        
        try:
            doc = self.collection.document(doc_id).get()
            if doc.exists:
                data       = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error("Error fetching document %s from %s: %s",
                         doc_id, self.collection_name, e)
            raise

    async def update(
        self, doc_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        
        try:
            doc_ref = self.collection.document(doc_id)
            doc     = doc_ref.get()
            if not doc.exists:
                return None
            # Remove None values before updating
            clean_data = {k: v for k, v in data.items() if v is not None}
            doc_ref.update(clean_data)
            updated       = doc_ref.get().to_dict()
            updated["id"] = doc_id
            logger.info("Updated document %s in %s", doc_id, self.collection_name)
            return updated
        except Exception as e:
            logger.error("Error updating document %s in %s: %s",
                         doc_id, self.collection_name, e)
            raise

    async def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            doc_ref = self.collection.document(doc_id)
            doc     = doc_ref.get()
            if not doc.exists:
                return False
            doc_ref.delete()
            logger.info("Deleted document %s from %s", doc_id, self.collection_name)
            return True
        except Exception as e:
            logger.error("Error deleting document %s from %s: %s",
                         doc_id, self.collection_name, e)
            raise