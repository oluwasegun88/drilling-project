import logging
from typing import Any, Dict, List, Optional

from drilling.base.base_service import BaseService

logger = logging.getLogger(__name__)


class GenericService(BaseService):
   

    def __init__(self, repository):
        super().__init__(repository)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.repository.create(data)

    async def fetch_all(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return await self.repository.fetch_all(filters)

    async def fetch_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return await self.repository.fetch_by_id(doc_id)

    async def update(
        self, doc_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        return await self.repository.update(doc_id, data)

    async def delete(self, doc_id: str) -> bool:
        return await self.repository.delete(doc_id)