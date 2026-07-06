from pydantic import BaseModel
from typing import Optional


class ProductionRecord(BaseModel):
    
    id:               Optional[str]   = None
    asset:            Optional[str]   = None
    date:             Optional[str]   = None
    gas:              Optional[float] = None
    gross:            Optional[float] = None
    oil:              Optional[float] = None
    productionString: Optional[str]   = None
    remark:           Optional[str]   = None
    water:            Optional[float] = None