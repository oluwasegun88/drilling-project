from typing import Any, Dict, Optional

from test_project.test_project_repository import TestProjectRepository
from firebase_database.setup_firebase import db


class TestProjectService:

    def __init__(self):

        self.repo = TestProjectRepository(db)


    async def fetch_all_records(
            self,
            filters: Optional[Dict[str, Any]] = None
    ):
        filters = filters or {}
            
        # Extract pagination parameters
        page = filters.get("page", 1)
        limit = filters.get("limit", 100)
        offset = (page - 1) * limit
        
        # Prepare repository filters
        repo_filters = {
            "asset": filters.get("asset"),
            "limit": limit,
            "offset": offset
        }
        
        # Remove None values
        # repo_filters = {k: v for k, v in repo_filters.items() if v is not None}
        
        # Get data from repository
        data, total = await self.repo.find_all(repo_filters)
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        
        return {
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
