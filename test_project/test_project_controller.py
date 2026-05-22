from typing import Optional

from fastapi import APIRouter, Query

from test_project.test_project_service import TestProjectService

router = APIRouter(prefix="/test-project", tags=["Test Project"])

@router.get("/fetch-all-records")
async def fetch_all_records(
        asset: Optional[str] = Query(None, description="Asset filter"),
        page: Optional[int] = Query(None),
        limit: Optional[int] = Query(None),
):
    service = TestProjectService()
    filters = {
        "asset": asset,
        "page": page,
        "limit": limit
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    response = await service.fetch_all_records(filters)

    return response