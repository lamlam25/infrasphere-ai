"""Tests for WorkforceOS task decomposition and intelligent scoring."""
from app.workforce.assignment_engine import AssignmentEngine
from app.workforce.task_decomposer import TaskDecomposer


def test_task_decomposition_flooding():
    decomposer = TaskDecomposer()
    incident = {
        "category": "flooding",
        "severity": "high",
        "district": "Sunamganj",
    }
    tasks = decomposer.decompose(incident)
    assert len(tasks) >= 4
    # Check that dependencies exist
    has_deps = any(len(t.dependencies) > 0 for t in tasks)
    assert has_deps is True


def test_assignment_scoring_explainability():
    engine = AssignmentEngine()
    team_sunamganj = {
        "id": "TEAM-01",
        "name": "Sunamganj Rapid Response",
        "zone": "Sunamganj",
        "status": "available",
        "skills": [{"skill": "field_inspection", "proficiency": 0.9}],
    }
    team_dhaka = {
        "id": "TEAM-02",
        "name": "Dhaka General Corps",
        "zone": "Dhaka",
        "status": "available",
        "skills": [{"skill": "structural_engineering", "proficiency": 0.8}],
    }

    score_local = engine.score_team_for_task(
        team_sunamganj,
        required_skills=["field_inspection"],
        incident_district="Sunamganj",
    )
    score_remote = engine.score_team_for_task(
        team_dhaka,
        required_skills=["field_inspection"],
        incident_district="Sunamganj",
    )

    # Local team with matching skills must score higher than distant team with missing skills
    assert score_local.total_score > score_remote.total_score
    assert score_local.zone_score == 1.0
    assert "matched" in score_local.explanation.lower()
