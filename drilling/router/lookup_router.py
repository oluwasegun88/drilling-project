import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LookupCreateDTO(BaseModel):
    name:        str
    description: str = ""


class LookupUpdateDTO(BaseModel):
    name:        str = None
    description: str = None


def create_lookup_router(
    prefix: str,
    tag: str,
    service_factory,
) -> APIRouter:
   
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.post("/", status_code=201)
    async def create(payload: LookupCreateDTO):
        
        try:
            service = service_factory()
            result  = await service.create(payload.model_dump())
            return {"status": "success", "data": result}
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    @router.get("/")
    async def fetch_all():
        
        try:
            service = service_factory()
            records = await service.fetch_all()
            return {"status": "success", "total": len(records), "data": records}
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    @router.get("/{item_id}")
    async def fetch_by_id(item_id: str):
        
        try:
            service = service_factory()
            record  = await service.fetch_by_id(item_id)
            if not record:
                raise HTTPException(404, detail=f"{tag} {item_id} not found")
            return {"status": "success", "data": record}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    @router.put("/{item_id}")
    async def update(item_id: str, payload: LookupUpdateDTO):
        
        try:
            service = service_factory()
            result  = await service.update(
                item_id,
                {k: v for k, v in payload.model_dump().items() if v is not None}
            )
            if not result:
                raise HTTPException(404, detail=f"{tag} {item_id} not found")
            return {"status": "success", "data": result}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    @router.delete("/{item_id}")
    async def delete(item_id: str):
        
        try:
            service = service_factory()
            deleted = await service.delete(item_id)
            if not deleted:
                raise HTTPException(404, detail=f"{tag} {item_id} not found")
            return {"status": "success", "message": f"{tag} {item_id} deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    return router