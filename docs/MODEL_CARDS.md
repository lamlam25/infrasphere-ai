# InfraSphere AI — Model Cards

This document follows the standardized Model Card format to provide full transparency into the machine learning models and deterministic scoring algorithms deployed in InfraSphere AI.

---

## 1. Incident Triage Classifier

### 1.1 Model Details
- **Architecture:** Term Frequency-Inverse Document Frequency (TF-IDF) feature extractor paired with a Linear Support Vector Classifier (`LinearSVC`).
- **Target Classes:** 4 infrastructure incident categories: `flooding`, `bridge_damage`, `road_washout`, `drainage_block`.
- **Language Support:** Bilingual (English and Bengali / বাংলা).
- **Implementation File:** `backend/app/agents/triage.py`

### 1.2 Intended Use
- **Primary Use:** Rapid triage and categorization of incoming field reports and citizen text submissions.
- **Out-of-Scope Use:** Final assessment of structural collapse without field engineering verification.

### 1.3 Training Data
- Synthetic curated corpus of 55 infrastructure incident reports reflecting realistic Bangladesh disaster reporting vocabulary in both English and Bengali (e.g. কালভার্ট, বাঁধ, প্লাবিত, জলমগ্ন, embankment, culvert, scour).

### 1.4 Performance & Evaluation
- **Benchmark Sample Size:** 55 labeled samples.
- **Accuracy:** 52.9% (Baseline LinearSVC on diverse multilingual dataset).
- **Macro-F1 Score:** 0.485.
- **Latency:** < 15ms on standard CPU.

---

## 2. SecureAI Execution Anomaly Detector

### 2.1 Model Details
- **Architecture:** Unsupervised `IsolationForest` ensemble algorithm.
- **Features Extracted:**
  1. `step_count`: Total iterations in agent execution.
  2. `duration_ms`: Total execution latency in milliseconds.
  3. `tool_calls_count`: Number of external tool invocations.
  4. `unique_tools_ratio`: Ratio of unique tools to total tool calls.
  5. `retry_count`: Number of agent retry attempts.
- **Implementation File:** `backend/app/secureai/anomaly_detector.py`

### 2.2 Intended Use
- Detect runaway loops, anomalous latency spikes, and repetitive query thrashing before resource exhaustion occurs.

### 2.3 Evaluation & Baselines
- Pre-fitted on expected nominal workflow profiles:
  - Step range: 1 - 4 steps.
  - Duration range: 50ms - 2,500ms.
- Anomalous input triggers an anomaly flag if the Isolation Forest contamination threshold is exceeded or if hard bounds (> 10 steps, > 60s) are breached.

---

## 3. Weighted Infrastructure Risk Prioritization Model

### 3.1 Model Formulation
To prevent opaque "black-box" risk predictions, InfraSphere AI uses a transparent, linear multi-factor indicator model:

$$R = 100 \cdot \sum_{i=1}^{n} w_i \cdot x_i$$

### 3.2 Standard Indicators & Baseline Weights
| Indicator ($x_i$) | Weight ($w_i$) | Description & Data Source |
|---|---|---|
| **$W$ (Water Level)** | 0.30 | Ratio of nearest FFWC river gauge level relative to critical danger level: $\min(1.0, \frac{\text{level}}{\text{danger\_level} \times 1.2})$. |
| **$F$ (Forecast Trend)** | 0.20 | 24-48 hour rising trend derived from upstream catchment basin indicators. |
| **$P$ (Precipitation)** | 0.15 | Live 24-hour rainfall accumulation. |
| **$E$ (Asset Exposure)**| 0.15 | Vulnerable bridges, culverts, and hospitals within a 5km radius. |
| **$H$ (Historical)** | 0.10 | Frequency of past monsoon flooding events in the target Upazila. |
| **$S$ (Severity)** | 0.10 | Initial reported severity weight (`critical` = 1.0, `high` = 0.75, `medium` = 0.50, `low` = 0.25). |

### 3.3 Dynamic Weight Renormalization (Missing Data Handling)
When live telemetry (such as rainfall data $P$) is unavailable in remote areas, the model **does not hallucinate** values. Instead, it explicitly marks the indicator as missing and renormalizes the remaining weights:

$$w_j' = \frac{w_j}{\sum_{k \in \text{available}} w_k}$$

The assessment output lists all `missing_factors` and includes an explicit `limitations` disclosure.

### 3.4 Risk Classification Tiers
- **Critical (Score $\ge 80$):** Immediate emergency response and human sign-off required.
- **High (Score $60 - 79$):** Priority field inspection within 4 hours.
- **Medium (Score $40 - 59$):** Scheduled maintenance review.
- **Low (Score $< 40$):** Routine monitoring.
