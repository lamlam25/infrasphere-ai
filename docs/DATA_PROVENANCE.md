# InfraSphere AI — Data Provenance & Ethics Disclosure

## 1. Ethical Transparency & Synthetic Data Mandate

In compliance with hackathon ethical guidelines and enterprise safety standards, **all incident reports, river telemetry observations, and operational guidelines used in this initial demonstration are clearly labeled as synthetic**.

InfraSphere AI strictly forbids claiming that synthetic or simulated data represents live Bangladesh government operations.

Every record in the relational store contains an explicit boolean flag:
```json
{
  "is_synthetic": true
}
```

The user interface surfaces a permanent indicator: **"Synthetic Telemetry Active (FFWC / OSM Demo Sandbox)"**.

---

## 2. Ingested Datasets Breakdown

### 2.1 Incidents Dataset (40 Records)
- **Source:** Synthetically generated scenarios based on historical Bangladesh monsoon infrastructure vulnerability profiles (Sylhet, Sunamganj, Netrokona, Chittagong, Cox's Bazar, Kurigram).
- **Categories:**
  - Flooding / Inundation
  - Bridge & Culvert Structural Scour
  - Road Washout & Embankment Erosion
  - Drainage Chokepoints
- **Language Distribution:** 85% English, 15% Bengali (বাংলা) to benchmark bilingual comprehension.

### 2.2 Flood Forecasting & Warning Centre (FFWC) River Stations (10 Records)
- **Source:** Simulated station profiles calibrated to realistic river basins in Bangladesh (Surma, Kushiyara, Meghna, Brahmaputra, Karnaphuli).
- **Flagship Demonstration Station:**
  - Code: `STN-SUN-01`
  - Name: `Surma River - Sunamganj Station`
  - Current Water Level: `7.35m`
  - Danger Level: `6.50m` (Exceeded by +0.85m)

### 2.3 Critical Infrastructure Assets (50 Records)
- **Source:** Synthetic infrastructure register representing national highway bridges, regional culverts, rural bypasses, and flood shelter access roads in the Sylhet and Sunamganj divisions.
- **Coordinates:** Grounded in accurate bounding boxes for Bangladesh administrative upazilas.

### 2.4 Regional Response Teams (6 Records)
- **Source:** Synthetic organizational rosters modeling regional engineering and disaster management task forces:
  - `TEAM-SUN-01`: Sunamganj Emergency Road Maintenance Unit
  - `TEAM-SYL-01`: Sylhet Division Rapid Flood Response Taskforce
  - `TEAM-CTG-01`: Chittagong Coastal Infrastructure Crew
  - `TEAM-DHK-01`: Dhaka Central Technical Engineering Reserve
  - `TEAM-NET-01`: Netrokona Drainage Clearance Team
  - `TEAM-KHI-01`: Khulna Embankment Repair Squad

### 2.5 Operational Documents & SOP Guidelines (3 Documents)
- **`DOC-FLD-01`:** *Bangladesh Flood Response Infrastructure Guidelines* (Synthetic document outlining water depth closure thresholds and evacuation priority rules).
- **`DOC-MNT-01`:** *Road & Bridge Maintenance Standard Operating Procedures* (Synthetic SOP specifying response timelines and scour inspection criteria).
- **`DOC-HST-01`:** *Historical Flood Incident Lessons Learned — Sylhet Division* (Synthetic case review analyzing 2022 monsoon flood choke points).

---

## 3. Data Licensing & Open-Source Attribution
- **Map Cartography:** &copy; [CARTO](https://carto.com/) and &copy; [OpenStreetMap](https://www.openstreetmap.org/) contributors under ODbL license.
- **Font & Iconography:** Lucide Icons (ISC License) and Inter typography (SIL Open Font License).
