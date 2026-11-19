"""
Seed demo data for InfraSphere AI.
Populates SQLite with realistic synthetic Bangladesh infrastructure datasets:
- 3 users (Admin, Manager, Analyst)
- 6 human response teams with skills
- 6 registered AI agents
- 40 synthetic infrastructure incidents (including flagship INC-0041 in Sunamganj)
- 50 synthetic infrastructure assets (roads, bridges, culverts, embankments)
- 10 FFWC river monitoring stations and observations
- 3 seeded operational documents with chunks
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.agent import Agent, AgentStatus, AgentType
from app.models.asset import Asset, AssetType
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentVisibility
from app.models.event import StationObservation
from app.models.incident import Incident, IncidentCategory, IncidentSeverity, IncidentStatus
from app.models.team import Team, TeamSkill, TeamStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def seed_all_data(db: AsyncSession) -> None:
    # Check if already seeded
    res = await db.execute(select(User).limit(1))
    if res.scalar_one_or_none():
        logger.info("Demo data already seeded, skipping.")
        return

    logger.info("Seeding realistic synthetic Bangladesh demo data...")
    org_id = "ORG-BD-INFRA-01"

    # 1. Users
    users_data = [
        ("admin@infrasphere.bd", "System Administrator", UserRole.admin),
        ("manager@infrasphere.bd", "Operations Manager", UserRole.manager),
        ("analyst@infrasphere.bd", "Infrastructure Analyst", UserRole.analyst),
    ]
    for email, name, role in users_data:
        u = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=hash_password("Demo1234!"),
            full_name=name,
            role=role,
            is_active=True,
            organization_id=org_id,
        )
        db.add(u)

    # 2. Registered AI Agents
    agents_data = [
        ("security_guardian", "SecureAI Guardian", AgentType.security_guardian, "Monitors inputs for prompt injections, jailbreaks, and enforces tool permissions", ["inspect_input", "log_security_event", "check_permissions"]),
        ("triage", "Incident Triage Agent", AgentType.triage, "Classifies infrastructure incidents using TF-IDF + LinearSVC and extracts entities", ["read_incident", "classify_incident", "extract_entities", "update_incident_status"]),
        ("knowledge", "Knowledge Analyst Agent", AgentType.knowledge, "Retrieves operational guidelines and past incident history from Knowledge Grid", ["search_documents", "retrieve_chunks", "query_graph", "read_incident"]),
        ("risk", "Infrastructure Risk Agent", AgentType.risk, "Calculates multi-factor risk score from FFWC river observations and exposure", ["read_incident", "read_stations", "read_assets", "read_history"]),
        ("workforce", "Workforce Coordination Agent", AgentType.workforce, "Decomposes incident into tasks and ranks teams using explainable multi-factor scoring", ["read_teams", "read_agents", "read_tasks", "create_tasks", "recommend_assignments"]),
        ("response", "Response Recommendation Agent", AgentType.response, "Synthesizes multi-agent evidence into human approval dossiers", ["read_all_results", "generate_recommendation", "create_approval_request"]),
    ]
    for a_id, a_name, a_type, desc, perms in agents_data:
        agent = Agent(
            id=a_id,
            name=a_name,
            agent_type=a_type,
            description=desc,
            status=AgentStatus.active,
            permissions_json=perms,
            capabilities_json=["multilingual_nlp", "risk_calculation", "task_planning"],
        )
        db.add(agent)

    # 3. Human Response Teams
    teams_data = [
        ("TEAM-SUN-01", "Sunamganj Haor Rapid Response Team", "Sunamganj", TeamStatus.available, [
            ("field_inspection", 0.95), ("bridge_inspection", 0.90), ("structural_engineering", 0.85), ("traffic_management", 0.80)
        ]),
        ("TEAM-SYL-01", "Sylhet Division Heavy Civil Engineering Unit", "Sylhet", TeamStatus.available, [
            ("gis_mapping", 0.90), ("field_inspection", 0.95), ("dewatering", 0.85), ("emergency_response", 0.90)
        ]),
        ("TEAM-CTG-01", "Chattogram Highway & Embankment Division", "Chattogram", TeamStatus.available, [
            ("road_maintenance", 0.95), ("heavy_machinery", 0.90), ("asphalt_laying", 0.85), ("field_inspection", 0.80)
        ]),
        ("TEAM-DHK-01", "Central Technical Services - Dhaka", "Dhaka", TeamStatus.available, [
            ("structural_engineering", 0.95), ("data_analysis", 0.90), ("civil_engineering", 0.95), ("operations_management", 0.90)
        ]),
        ("TEAM-KUR-01", "Kurigram Riverbank Protection Taskforce", "Kurigram", TeamStatus.available, [
            ("riverbank_protection", 0.95), ("flood_response", 0.90), ("field_inspection", 0.85), ("heavy_machinery", 0.80)
        ]),
        ("TEAM-CXB-01", "Cox's Bazar Coastal Infrastructure Patrol", "Cox's Bazar", TeamStatus.available, [
            ("coastal_engineering", 0.90), ("emergency_response", 0.85), ("field_inspection", 0.85), ("traffic_management", 0.75)
        ]),
    ]
    for tid, tname, tzone, tstatus, skills in teams_data:
        t = Team(
            id=tid,
            organization_id=org_id,
            name=tname,
            zone=tzone,
            status=tstatus,
        )
        db.add(t)
        for s_name, prof in skills:
            ts = TeamSkill(
                team_id=tid,
                skill=s_name,
                proficiency=prof,
            )
            db.add(ts)

    # 4. FFWC River Monitoring Stations
    stations = [
        ("STN-SUN-01", "Surma River - Sunamganj Gauge", "Sunamganj", 7.35, 6.50),
        ("STN-SYL-01", "Surma River - Sylhet Station", "Sylhet", 6.85, 6.20),
        ("STN-KUS-01", "Kushiyara River - Sheola Station", "Sylhet", 13.40, 13.00),
        ("STN-MEG-01", "Meghna River - Bhairab Bazar", "Kishoreganj", 5.20, 5.80),
        ("STN-BRA-01", "Brahmaputra River - Chilmari Gauge", "Kurigram", 23.80, 23.50),
        ("STN-JAM-01", "Jamuna River - Sirajganj Station", "Sirajganj", 12.90, 13.35),
        ("STN-TEE-01", "Teesta River - Dalia Barrage", "Nilphamari", 52.10, 52.40),
        ("STN-CTG-01", "Karnaphuli River - Chittagong Port", "Chattogram", 4.10, 5.00),
        ("STN-DHK-01", "Buriganga River - Mill Barrack Gauge", "Dhaka", 4.80, 6.00),
        ("STN-TUR-01", "Turag River - Mirpur Station", "Dhaka", 5.10, 5.94),
    ]
    for sid, sname, sdist, level, danger in stations:
        so = StationObservation(
            station_id=sid,
            station_name=sname,
            district=sdist,
            level=level,
            unit="m",
            danger_level=danger,
            recorded_at=datetime.now(timezone.utc),
            source="FFWC_SYNTHETIC_FEED",
            is_synthetic=True,
        )
        db.add(so)

    # 5. Flagship INC-0041 Incident & 39 Other Realistic Synthetic Incidents
    incidents_catalog = [
        # Flagship scenario
        ("INC-0041", "Reported flood-related road disruption", "Water accumulation reported near a road section in Sunamganj Sadar. Pavement is submerged by approximately 0.45m of floodwater from the Surma River overflow. Vehicle passage is halted.", IncidentCategory.flooding, IncidentSeverity.high, 25.065, 91.395, "Sunamganj"),
        # Other Sunamganj incidents
        ("INC-0001", "Surma River crossing approach road erosion", "Riverbank scour has eroded 2 meters of the road shoulder near the Surma river crossing.", IncidentCategory.road_damage, IncidentSeverity.critical, 25.071, 91.402, "Sunamganj"),
        ("INC-0002", "Tahirpur road culvert blockage", "Severe silt and vegetation debris clogging double-vent box culvert.", IncidentCategory.drainage, IncidentSeverity.medium, 25.102, 91.178, "Sunamganj"),
        ("INC-0003", "Chhatak bridge approach settlement", "Cracks observed in the western approach slab of the Chhatak regional bridge.", IncidentCategory.bridge_damage, IncidentSeverity.high, 25.038, 91.671, "Sunamganj"),
        ("INC-0004", "Derai-Sunamganj highway shoulder collapse", "Heavy water current washed away embankment toe protection.", IncidentCategory.road_damage, IncidentSeverity.high, 24.789, 91.354, "Sunamganj"),
        ("INC-0005", "Jamalganj haor road submergence", "Overtopping of 500m of sub-mergible road during flash flood surge.", IncidentCategory.flooding, IncidentSeverity.high, 24.998, 91.229, "Sunamganj"),
        # Sylhet incidents
        ("INC-0010", "Sylhet-Zakiganj highway water logging", "Flash flood inundation across 1.2km stretch near Kanaighat.", IncidentCategory.flooding, IncidentSeverity.critical, 25.012, 92.261, "Sylhet"),
        ("INC-0011", "Keane Bridge pedestrian walkway crack", "Superficial masonry expansion joint displacement observed.", IncidentCategory.bridge_damage, IncidentSeverity.low, 24.891, 91.871, "Sylhet"),
        ("INC-0012", "Shahjalal Upashahar storm drainage overflow", "Backflow from Surma River into municipal collector canal.", IncidentCategory.drainage, IncidentSeverity.medium, 24.887, 91.884, "Sylhet"),
        ("INC-0013", "Osmani Nagar culvert structural fracture", "Central pier exhibiting hairline shear cracks.", IncidentCategory.bridge_damage, IncidentSeverity.high, 24.712, 91.782, "Sylhet"),
        # Chattogram incidents
        ("INC-0020", "Agrabad commercial area tidal water logging", "High tide coinciding with torrential rain causes 0.6m flooding.", IncidentCategory.flooding, IncidentSeverity.high, 22.327, 91.812, "Chattogram"),
        ("INC-0021", "Chaktai canal siltation and barrier failure", "Canal sluice gate jammed by urban debris.", IncidentCategory.drainage, IncidentSeverity.high, 22.339, 91.848, "Chattogram"),
        ("INC-0022", "Mirsharai highway asphalt rutting", "Heavy industrial freight vehicle rutting following continuous rain.", IncidentCategory.road_damage, IncidentSeverity.medium, 22.771, 91.575, "Chattogram"),
        ("INC-0023", "Karnaphuli bridge expansion joint vibration", "Abnormal noise reported at span 4 roller bearing.", IncidentCategory.bridge_damage, IncidentSeverity.medium, 22.324, 91.854, "Chattogram"),
        # Dhaka incidents
        ("INC-0030", "Mirpur Rokeya Sarani drainage overflow", "Kallyanpur retention basin overflow submerging street lanes.", IncidentCategory.drainage, IncidentSeverity.high, 23.799, 90.371, "Dhaka"),
        ("INC-0031", "Kuril flyover ramp water accumulation", "Clogged drainage scuppers causing vehicular hazard.", IncidentCategory.drainage, IncidentSeverity.medium, 23.818, 90.419, "Dhaka"),
        ("INC-0032", "Babubazar bridge approach pavement pothole cluster", "Deep pothole cluster damaging light passenger transit.", IncidentCategory.road_damage, IncidentSeverity.medium, 23.711, 90.402, "Dhaka"),
        ("INC-0033", "Demra-Staff Quarter road water pipe rupture", "Municipal distribution main burst undermining road base.", IncidentCategory.water_supply, IncidentSeverity.high, 23.719, 90.498, "Dhaka"),
        # Kurigram & Northern Division incidents
        ("INC-0035", "Rajarhat Teesta flood embankment breach", "40m breach in agricultural flood defense dyke.", IncidentCategory.flooding, IncidentSeverity.critical, 25.801, 89.551, "Kurigram"),
        ("INC-0036", "Ulipur wooden footbridge washed out", "Flood velocity washed out 3 timber support trestles.", IncidentCategory.bridge_damage, IncidentSeverity.medium, 25.662, 89.629, "Kurigram"),
    ]

    # Generate up to 40 records programmatically with slight variations
    districts_cycle = ["Sunamganj", "Sylhet", "Chattogram", "Dhaka", "Kurigram"]
    for i in range(len(incidents_catalog), 40):
        d = districts_cycle[i % len(districts_cycle)]
        inc_id = f"INC-{1000 + i}"
        incidents_catalog.append((
            inc_id,
            f"Routine infrastructure report #{i+1} in {d}",
            f"Automated monitoring alert: observed maintenance requirement along the primary connectivity axis in {d}.",
            IncidentCategory.road_damage if i % 2 == 0 else IncidentCategory.flooding,
            IncidentSeverity.medium if i % 3 != 0 else IncidentSeverity.high,
            24.5 + (i * 0.03),
            90.5 + (i * 0.04),
            d,
        ))

    for inc_tuple in incidents_catalog:
        iid, title, desc, cat, sev, lat, lng, dist = inc_tuple
        inc = Incident(
            id=iid,
            organization_id=org_id,
            title=title,
            description=desc,
            category=cat,
            severity=sev,
            status=IncidentStatus.received,
            latitude=lat,
            longitude=lng,
            district=dist,
            language="en",
            source="demo_dataset",
            is_synthetic=True,
        )
        db.add(inc)

    # 6. Infrastructure Assets (50 synthetic assets)
    assets_catalog = [
        ("ASSET-001", "Surma River Main Road Bridge", AssetType.bridge, "Sunamganj", 25.070, 91.400, "Two-lane prestressed concrete girder bridge spanning the Surma River."),
        ("ASSET-002", "Sunamganj-Sylhet Regional Highway (R280)", AssetType.road, "Sunamganj", 25.050, 91.420, "Primary arterial transport corridor connecting Sunamganj to Sylhet."),
        ("ASSET-003", "Tahirpur Haor Flood Protection Embankment", AssetType.other, "Sunamganj", 25.110, 91.170, "Earthen flood bund protecting boro rice paddies."),
        ("ASSET-004", "Chhatak Railway & Road Bridge", AssetType.bridge, "Sunamganj", 25.040, 91.670, "Combined transport bridge across Surma tributary."),
        ("ASSET-005", "Keane Bridge Historic Crossing", AssetType.bridge, "Sylhet", 24.890, 91.870, "Iconic steel arch bridge across Surma River."),
        ("ASSET-006", "Shahjalal International Airport Drainage Canal", AssetType.drainage, "Dhaka", 23.850, 90.400, "Main storm runoff discharge channel."),
        ("ASSET-007", "Karnaphuli River Heavy Freight Crossing", AssetType.bridge, "Chattogram", 22.320, 91.850, "Multi-span steel truss bridge."),
        ("ASSET-008", "Teesta Barrage Gate Structure #14", AssetType.other, "Nilphamari", 52.100, 52.400, "Hydraulic flood regulation weir."),
    ]
    # Expand to 50 assets
    for i in range(len(assets_catalog), 50):
        d = districts_cycle[i % len(districts_cycle)]
        aid = f"ASSET-{100 + i}"
        assets_catalog.append((
            aid,
            f"{d} Regional Infrastructure Asset #{i+1}",
            AssetType.road if i % 2 == 0 else AssetType.bridge,
            d,
            24.0 + (i * 0.04),
            91.0 + (i * 0.03),
            f"Synthetic critical infrastructure monitoring node located in {d}.",
        ))

    for aid, aname, atype, adist, alat, alng, adesc in assets_catalog:
        asset = Asset(
            id=aid,
            organization_id=org_id,
            name=aname,
            asset_type=atype,
            district=adist,
            latitude=alat,
            longitude=alng,
            description=adesc,
            source="DEMO_GIS_SYNTHETIC",
            is_synthetic=True,
        )
        db.add(asset)

    # 7. Seed Operational Documents into Knowledge Grid
    docs = [
        (
            "DOC-FLD-01",
            "Bangladesh Flood Response Infrastructure Guidelines",
            """# Bangladesh Flood Response Infrastructure Guidelines
(Synthetic Operational Document - For Demonstration Purposes Only)

## 1. Alert Levels & Trigger Thresholds
- Warning Stage: Water level reaches 0.50m above official danger level.
- Critical Stage: Water level exceeds 1.00m above danger level. Immediate deployment of regional patrol units required.

## 2. Road Submergence Standard Operating Procedure
- When water accumulation on road pavement reaches 0.30m, all light vehicular traffic must be suspended.
- Heavy vehicles are restricted at 0.45m depth due to risk of hidden road shoulder collapse.
- Deploy detour signs and alert local police divisions within 60 minutes of submergence confirmation.

## 3. High-Risk Zones in Sunamganj and Sylhet
Sunamganj Sadar, Tahirpur, and Derai upazilas are particularly vulnerable to sudden flash floods from Meghalaya upstream basins.
Inspect all box culverts for debris clogging immediately following heavy downpours.""",
            "pdf",
        ),
        (
            "DOC-MNT-01",
            "Road & Bridge Maintenance Standard Operating Procedures",
            """# Road & Bridge Maintenance Standard Operating Procedures
(Synthetic Operational Document - For Demonstration Purposes Only)

## Section 4: Culvert and Drainage Debris Removal
All culverts in haor basins must be inspected twice annually: once pre-monsoon (April) and post-monsoon (October).
Use mechanical excavator or high-pressure water jetting when siltation exceeds 40% of culvert opening.

## Section 7: Sunamganj Sadar Bridge Inspection Records
Sunamganj Sadar Bridge inspection completed on 10 October 2024. All foundation scour parameters recorded within safe limits.
Recommended follow-up: underwater acoustic sonar survey in dry season.""",
            "markdown",
        ),
        (
            "DOC-HST-01",
            "Sunamganj Historical Flood Incident Log (2022-2024)",
            """# Sunamganj Historical Flood Incident Log
(Synthetic Historical Summary - For Demonstration Purposes Only)

## June 2022 Flash Flood Event
Unprecedented 100-year flood event submerged 85% of Sunamganj district.
Primary damage concentrated on R280 regional highway where 14 sections were washed out.

## October 2024 Inspection Discrepancy Record
Contradiction Notice: Field log B-14 claims Sunamganj Sadar Bridge inspection pending as of 15 October 2024 due to delayed survey equipment arrival.
This creates a status conflict with Maintenance Document DOC-MNT-01 which reported completion on 10 October 2024.""",
            "markdown",
        ),
    ]

    for did, dtitle, dcontent, dtype in docs:
        d = Document(
            id=did,
            organization_id=org_id,
            title=dtitle,
            file_path=f"seed/{did}.md",
            file_hash=uuid.uuid4().hex,
            file_type=dtype,
            version=1,
            status=DocumentStatus.indexed,
            visibility=DocumentVisibility.public,
            is_synthetic=True,
        )
        db.add(d)

        # Split into paragraph chunks
        paras = [p.strip() for p in dcontent.split("\n\n") if len(p.strip()) > 20]
        for idx, p in enumerate(paras):
            chk = DocumentChunk(
                id=f"CHK-{uuid.uuid4().hex[:8].upper()}",
                document_id=did,
                chunk_index=idx,
                page_number=1 + (idx // 2),
                content=p,
                metadata_json={"title": dtitle, "document_id": did},
            )
            db.add(chk)


    await db.commit()
    logger.info("Demo data seeding completed successfully.")
