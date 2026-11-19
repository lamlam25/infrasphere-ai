"""
WorkforceOS: Intelligent Assignment Engine.
Computes explainable multi-factor match scores:
Score(a, t) = 0.40*S + 0.25*Z + 0.20*A + 0.15*L
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CandidateScore(BaseModel):
    team_id: str
    team_name: str
    total_score: float
    skill_score: float      # S (0.0 - 1.0)
    zone_score: float       # Z (0.0 - 1.0)
    availability_score: float # A (0.0 - 1.0)
    workload_score: float   # L (0.0 - 1.0)
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str


class AssignmentEngine:
    """
    Ranks human response teams or AI agents for a given task using a transparent,
    explainable weighted scoring algorithm.
    """

    WEIGHT_SKILL = 0.40
    WEIGHT_ZONE = 0.25
    WEIGHT_AVAILABILITY = 0.20
    WEIGHT_WORKLOAD = 0.15

    # Division mapping for Bangladesh districts
    DISTRICT_DIVISIONS = {
        "Sunamganj": "Sylhet",
        "Sylhet": "Sylhet",
        "Moulvibazar": "Sylhet",
        "Habiganj": "Sylhet",
        "Dhaka": "Dhaka",
        "Gazipur": "Dhaka",
        "Narayanganj": "Dhaka",
        "Chattogram": "Chattogram",
        "Cox's Bazar": "Chattogram",
        "Feni": "Chattogram",
        "Kurigram": "Rangpur",
        "Rangpur": "Rangpur",
    }

    def score_team_for_task(
        self,
        team: Dict[str, Any],
        required_skills: List[str],
        incident_district: Optional[str] = None,
        active_task_count: int = 0,
    ) -> CandidateScore:
        """
        Computes the multi-factor candidate match score.
        """
        # 1. Skill Score (S)
        team_skills = {
            s.get("skill", "").lower(): float(s.get("proficiency", 0.8))
            for s in team.get("skills", [])
        }
        matched = []
        missing = []
        skill_score = 0.0

        if not required_skills:
            skill_score = 1.0
        else:
            total_prof = 0.0
            for r in required_skills:
                r_low = r.lower()
                if r_low in team_skills:
                    matched.append(r)
                    total_prof += team_skills[r_low]
                else:
                    # check substring match
                    found = False
                    for ts, prof in team_skills.items():
                        if r_low in ts or ts in r_low:
                            matched.append(r)
                            total_prof += prof * 0.8
                            found = True
                            break
                    if not found:
                        missing.append(r)
            skill_score = min(1.0, total_prof / len(required_skills))

        # 2. Zone Score (Z)
        zone_score = 0.1
        team_zone = team.get("zone", "")
        if incident_district and team_zone:
            if team_zone.lower() == incident_district.lower():
                zone_score = 1.0
            else:
                team_div = self.DISTRICT_DIVISIONS.get(team_zone, "")
                inc_div = self.DISTRICT_DIVISIONS.get(incident_district, "")
                if team_div and inc_div and team_div.lower() == inc_div.lower():
                    zone_score = 0.6
                else:
                    zone_score = 0.2

        # 3. Availability Score (A)
        status = team.get("status", "available").lower()
        if status == "available":
            avail_score = 1.0
        elif status == "busy":
            avail_score = 0.3
        else:
            avail_score = 0.0

        # 4. Workload Score (L)
        # Normalized based on maximum 5 concurrent tasks per team
        workload_score = max(0.0, 1.0 - (active_task_count / 5.0))

        # Composite score
        total = (
            self.WEIGHT_SKILL * skill_score +
            self.WEIGHT_ZONE * zone_score +
            self.WEIGHT_AVAILABILITY * avail_score +
            self.WEIGHT_WORKLOAD * workload_score
        )
        total = round(min(1.0, max(0.0, total)), 3)

        explanation = (
            f"Skills: {len(matched)}/{len(required_skills)} matched (S={skill_score:.2f}); "
            f"Zone: {team_zone} vs {incident_district} (Z={zone_score:.2f}); "
            f"Status: {status} (A={avail_score:.2f}); "
            f"Active tasks: {active_task_count} (L={workload_score:.2f})"
        )

        return CandidateScore(
            team_id=team.get("id", ""),
            team_name=team.get("name", "Unknown Team"),
            total_score=total,
            skill_score=round(skill_score, 2),
            zone_score=round(zone_score, 2),
            availability_score=round(avail_score, 2),
            workload_score=round(workload_score, 2),
            matched_skills=matched,
            missing_skills=missing,
            explanation=explanation,
        )

    def rank_teams(
        self,
        teams: List[Dict[str, Any]],
        required_skills: List[str],
        incident_district: Optional[str] = None,
        active_counts: Optional[Dict[str, int]] = None,
    ) -> List[CandidateScore]:
        """
        Ranks all teams for a given task and returns sorted list in descending order of score.
        """
        active_counts = active_counts or {}
        scored = [
            self.score_team_for_task(
                team,
                required_skills,
                incident_district,
                active_counts.get(team.get("id", ""), 0),
            )
            for team in teams
        ]
        scored.sort(key=lambda x: x.total_score, reverse=True)
        return scored
