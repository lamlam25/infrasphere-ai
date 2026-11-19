"""
RiskAgent: Calculates infrastructure risk score using weighted indicator model.
R = 100 * (0.30W + 0.20F + 0.15P + 0.15E + 0.10H + 0.10S)
With transparent weight renormalization when indicators (such as live rainfall) are missing.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.agents.base import AgentInput, AgentOutput, BaseAgent

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    agent_type = "risk"

    BASE_WEIGHTS = {
        "water_level": 0.30,
        "forecast_trend": 0.20,
        "precipitation": 0.15,
        "asset_exposure": 0.15,
        "historical_frequency": 0.10,
        "incident_severity": 0.10,
    }

    SEVERITY_SCORES = {
        "low": 0.25,
        "medium": 0.50,
        "high": 0.75,
        "critical": 1.00,
    }

    async def execute(self, agent_input: AgentInput, db=None) -> AgentOutput:
        start_time = time.perf_counter()
        self._step_count += 1
        self._check_limits()

        incident = agent_input.context.get("incident", {})
        district = incident.get("district", "Sunamganj")
        severity_str = str(incident.get("severity", "medium")).lower()

        # 1. Fetch hydrologic observation for the district
        station_obs = await self._get_station_obs(district, db)
        self._record_tool_call(
            "fetch_station_observations",
            {"district": district},
            f"Observed level: {station_obs.get('level')}m, Danger: {station_obs.get('danger_level')}m"
        )

        # 2. Compute components
        # W: Water level indicator
        water_level_val = station_obs.get("level", 6.8)
        danger_level = station_obs.get("danger_level", 6.5)
        # Normalized: 0.5 at normal, 1.0 at 1.5m above danger
        diff = water_level_val - danger_level
        w_score = min(1.0, max(0.0, 0.5 + (diff / 2.0)))

        # F: Forecast trend
        forecast_trend = station_obs.get("trend", "rising")
        f_map = {"rising": 0.85, "steady": 0.50, "falling": 0.20}
        f_score = f_map.get(forecast_trend, 0.50)

        # P: Precipitation - check if live rainfall is available
        live_rainfall = incident.get("live_rainfall")
        has_rainfall = live_rainfall is not None
        p_score = min(1.0, float(live_rainfall) / 100.0) if has_rainfall else None

        # E: Asset exposure - high for flood near road/bridge
        cat = incident.get("category", "flooding")
        e_map = {"flooding": 0.80, "bridge_damage": 0.85, "road_damage": 0.70, "drainage": 0.65}
        e_score = e_map.get(cat, 0.50)

        # H: Historical incident frequency
        historical_count = await self._get_historical_count(district, db)
        h_score = min(1.0, historical_count / 10.0)

        # S: Incident severity
        s_score = self.SEVERITY_SCORES.get(severity_str, 0.50)

        # 3. Calculate weighted sum with renormalization
        active_factors = {
            "water_level": (w_score, self.BASE_WEIGHTS["water_level"]),
            "forecast_trend": (f_score, self.BASE_WEIGHTS["forecast_trend"]),
            "asset_exposure": (e_score, self.BASE_WEIGHTS["asset_exposure"]),
            "historical_frequency": (h_score, self.BASE_WEIGHTS["historical_frequency"]),
            "incident_severity": (s_score, self.BASE_WEIGHTS["incident_severity"]),
        }

        missing_indicators = []
        if has_rainfall:
            active_factors["precipitation"] = (p_score, self.BASE_WEIGHTS["precipitation"])
        else:
            missing_indicators.append("live_rainfall")

        total_weight = sum(w for _, w in active_factors.values())
        raw_score = sum(val * (weight / total_weight) for val, weight in active_factors.values())
        risk_score = round(raw_score * 100, 1)

        # 4. Determine risk level
        if risk_score >= 75:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "moderate"
        else:
            risk_level = "low"

        limitations = [
            "Prototype risk prioritization model, not an official certified flood forecast.",
            "Water-level indicator is estimated from nearest FFWC river monitoring gauge.",
        ]
        if missing_indicators:
            limitations.append(f"Missing live indicators: {', '.join(missing_indicators)}; weights renormalized.")

        result = {
            "incident_id": agent_input.incident_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "method": "weighted_indicator_model_v1",
            "effective_weights": {k: round(w / total_weight, 3) for k, (_, w) in active_factors.items()},
            "factors": {k: round(val, 3) for k, (val, _) in active_factors.items()},
            "missing_indicators": missing_indicators,
            "station_data": {
                "station_id": station_obs.get("station_id", "STN-001"),
                "name": station_obs.get("name", f"{district} River Gauge"),
                "level_m": water_level_val,
                "danger_level_m": danger_level,
                "trend": forecast_trend,
                "is_synthetic": True,
            },
            "limitations": limitations,
        }

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return AgentOutput(
            agent_type=self.agent_type,
            success=True,
            result=result,
            evidence=[f"Station {station_obs.get('station_id', 'STN-001')} recorded water level {water_level_val}m (danger level: {danger_level}m)"],
            limitations=limitations,
            execution_time_ms=elapsed_ms,
        )

    async def _get_station_obs(self, district: str, db=None) -> Dict[str, Any]:
        if db:
            try:
                from app.models.event import StationObservation
                stmt = select(StationObservation).where(
                    StationObservation.district.ilike(f"%{district}%")
                ).order_by(StationObservation.recorded_at.desc()).limit(1)
                res = await db.execute(stmt)
                obs = res.scalar_one_or_none()
                if obs:
                    return {
                        "station_id": obs.station_id,
                        "name": obs.station_name,
                        "level": obs.level,
                        "danger_level": obs.danger_level,
                        "trend": "rising" if obs.level > obs.danger_level else "steady",
                    }
            except Exception as e:
                logger.warning(f"Failed to query DB for station obs: {e}")

        # Deterministic fallback based on district
        if "sunamganj" in district.lower():
            return {"station_id": "STN-SUN-01", "name": "Surma River - Sunamganj", "level": 7.35, "danger_level": 6.50, "trend": "rising"}
        elif "sylhet" in district.lower():
            return {"station_id": "STN-SYL-01", "name": "Surma River - Sylhet", "level": 6.80, "danger_level": 6.20, "trend": "steady"}
        elif "chattogram" in district.lower():
            return {"station_id": "STN-CTG-01", "name": "Karnaphuli River", "level": 4.10, "danger_level": 5.00, "trend": "steady"}
        else:
            return {"station_id": "STN-GEN-01", "name": f"{district} Hydrology Station", "level": 5.50, "danger_level": 5.80, "trend": "steady"}

    async def _get_historical_count(self, district: str, db=None) -> int:
        if db:
            try:
                from app.models.incident import Incident
                stmt = select(Incident).where(Incident.district.ilike(f"%{district}%"))
                res = await db.execute(stmt)
                return len(res.scalars().all())
            except Exception:
                pass
        return 5
