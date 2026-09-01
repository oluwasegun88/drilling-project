import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


DEFAULT_TOTAL_RIG_HOURS = 2415.0


class DashboardService:
    

    def __init__(self, npt_repository, total_rig_hours: float = DEFAULT_TOTAL_RIG_HOURS):
        self.npt_repository   = npt_repository
        self.total_rig_hours  = total_rig_hours

    

    def _safe_float(self, value) -> float:
        
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _get_month_label(self, date_str: str) -> str:
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%b-%Y")
        except Exception:
            return "Unknown"

    def _sum_by_key(
        self,
        records: List[Dict[str, Any]],
        group_key: str,
    ) -> Dict[str, Dict[str, float]]:
        
        result = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})

        for record in records:
            key   = record.get(group_key) or "Unknown"
            hours = self._safe_float(record.get("hours"))
            cost  = self._safe_float(record.get("npt_cost"))
            result[key]["hours"] += hours
            result[key]["cost"]  += cost

        return {
            k: {
                "hours": round(v["hours"], 4),
                "cost":  round(v["cost"],  2),
            }
            for k, v in sorted(result.items())
        }

    def _sum_by_month(
        self, records: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        
        result = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})

        for record in records:
            date_str = record.get("date", "")
            month    = self._get_month_label(date_str)
            hours    = self._safe_float(record.get("hours"))
            cost     = self._safe_float(record.get("npt_cost"))
            result[month]["hours"] += hours
            result[month]["cost"]  += cost

        return {
            k: {
                "hours": round(v["hours"], 4),
                "cost":  round(v["cost"],  2),
            }
            for k, v in result.items()
        }

    

    async def get_dashboard_metrics(
        self,
        well:            Optional[str] = None,
        start_date:      Optional[str] = None,
        end_date:        Optional[str] = None,
        total_rig_hours: Optional[float] = None,
    ) -> Dict[str, Any]:
       
        records = await self.npt_repository.fetch_for_dashboard(
            well=well, start_date=start_date, end_date=end_date
        )

        logger.info("DashboardService | well=%s records=%d",
                    well or "all", len(records))

        
        rig_hours = total_rig_hours or self.total_rig_hours

        total_npt_hours = round(
            sum(self._safe_float(r.get("hours")) for r in records), 4
        )
        total_npt_cost = round(
            sum(self._safe_float(r.get("npt_cost")) for r in records), 2
        )
        productive_hours        = round(rig_hours - total_npt_hours, 4)
        overall_npt_percent     = round(
            (total_npt_hours / rig_hours * 100) if rig_hours > 0 else 0.0, 4
        )
        productive_time_percent = round(
            (productive_hours / rig_hours * 100) if rig_hours > 0 else 0.0, 4
        )
        
        npt_by_category         = self._sum_by_key(records, "category")
        npt_by_responsible_party = self._sum_by_key(records, "responsible_party")
        npt_by_phase            = self._sum_by_key(records, "phase")
        npt_by_month            = self._sum_by_month(records)

        return {
            "well":                     well or "All Wells",
            "total_rig_hours":          rig_hours,
            "total_rig_days":           round(rig_hours / 24, 4),
            "total_npt_hours":          total_npt_hours,
            "total_npt_days":           round(total_npt_hours / 24, 4),
            "overall_npt_percent":      overall_npt_percent,
            "total_npt_cost":           total_npt_cost,
            "productive_hours":         productive_hours,
            "productive_days":          round(productive_hours / 24, 4),
            "productive_time_percent":  productive_time_percent,
            "total_records":            len(records),
            "npt_by_category":          npt_by_category,
            "npt_by_responsible_party": npt_by_responsible_party,
            "npt_by_phase":             npt_by_phase,
            "npt_by_month":             npt_by_month,
        }

    async def get_npt_summary_by_category(
        self, well: Optional[str] = None
    ) -> Dict[str, Any]:
        records = await self.npt_repository.fetch_for_dashboard(well=well)
        return self._sum_by_key(records, "category")

    async def get_npt_summary_by_phase(
        self, well: Optional[str] = None
    ) -> Dict[str, Any]:
        records = await self.npt_repository.fetch_for_dashboard(well=well)
        return self._sum_by_key(records, "phase")

    async def get_npt_summary_by_responsible_party(
        self, well: Optional[str] = None
    ) -> Dict[str, Any]:
        records = await self.npt_repository.fetch_for_dashboard(well=well)
        return self._sum_by_key(records, "responsible_party")

    async def get_npt_summary_by_month(
        self, well: Optional[str] = None
    ) -> Dict[str, Any]:
        records = await self.npt_repository.fetch_for_dashboard(well=well)
        return self._sum_by_month(records)