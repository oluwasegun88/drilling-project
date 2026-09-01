from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseRepository(ABC):
    

    def __init__(self, db, collection_name: str):
        self.db              = db
        self.collection_name = collection_name

    @property
    def collection(self):
                return self.db.collection(self.collection_name)

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        
        pass

    @abstractmethod
    async def fetch_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        
        pass

    @abstractmethod
    async def fetch_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
       
        pass

    @abstractmethod
    async def update(self, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        
        pass

    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        
        pass