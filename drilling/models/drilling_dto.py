from pydantic import BaseModel
from typing import Optional


class WellDTO(BaseModel):
    """Represents a well (e.g. Awoba NW 5, Awoba NW 6)."""
    id:       Optional[str] = None
    name:     str
    location: Optional[str] = None
    field:    Optional[str] = None


class PhaseDTO(BaseModel):
    """Represents a drilling phase (e.g. 16 Hole Section, Conductor Piling)."""
    id:          Optional[str] = None
    name:        str
    description: Optional[str] = None


class CategoryDTO(BaseModel):
    """Represents an NPT category (e.g. Mechanical, Equipment Failure)."""
    id:          Optional[str] = None
    name:        str
    description: Optional[str] = None


class ResponsiblePartyDTO(BaseModel):
    """Represents a responsible party (e.g. SMS Joy, Clinton, Geowell)."""
    id:          Optional[str] = None
    name:        str
    description: Optional[str] = None


class NPTRecordDTO(BaseModel):
    """
    Represents a single NPT (Non-Productive Time) record.
    Maps directly to a row in the NPT Tracking Register.
    """
    id:               Optional[str]   = None
    well:             Optional[str]   = None
    date:             Optional[str]   = None
    phase:            Optional[str]   = None
    hours:            Optional[float] = None
    days:             Optional[float] = None
    npt_cost:         Optional[float] = None
    description:      Optional[str]   = None
    category:         Optional[str]   = None
    responsible_party: Optional[str]  = None


class NPTRecordCreateDTO(BaseModel):
    """DTO for creating a new NPT record — all required fields."""
    well:              str
    date:              str
    phase:             str
    hours:             float
    npt_cost:          float
    description:       str
    category:          str
    responsible_party: str


class NPTRecordUpdateDTO(BaseModel):
    
    well:              Optional[str]   = None
    date:              Optional[str]   = None
    phase:             Optional[str]   = None
    hours:             Optional[float] = None
    npt_cost:          Optional[float] = None
    description:       Optional[str]   = None
    category:          Optional[str]   = None
    responsible_party: Optional[str]  = None


class DashboardMetricsDTO(BaseModel):
    

    well:                    str
    total_rig_hours:         float
    total_npt_hours:         float
    overall_npt_percent:     float
    total_npt_cost:          float
    productive_hours:        float
    productive_time_percent: float
    npt_by_category:         dict
    npt_by_responsible_party: dict
    npt_by_phase:            dict
    npt_by_month:            dict