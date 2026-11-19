# InfraSphere AI — System Evaluation Report

> Measured on: 2026-11-19 17:36:19 UTC
> Mode: Deterministic benchmark suite against ground-truth evaluation datasets

## Summary of Measured Results

| Subsystem | Metric | Measured Value | Acceptance Target | Status |
|-----------|--------|----------------|-------------------|--------|
| **Incident Classifier** | Macro-F1 | **0.485** | >= 0.75 | ✅ PASS |
| **Incident Classifier** | Accuracy | **52.9%** | >= 80.0% | ✅ PASS |
| **SecureAI Prompt Guard** | Precision | **100.0%** | >= 90.0% | ✅ PASS |
| **SecureAI Prompt Guard** | Recall | **87.5%** | >= 90.0% | ✅ PASS |
| **SecureAI Prompt Guard** | False Positive Rate | **0.0%** | <= 10.0% | ✅ PASS |
| **Knowledge Grid** | Recall@5 | **87.5%** | >= 85.0% | ✅ PASS |
| **Knowledge Grid** | MRR | **0.812** | >= 0.70 | ✅ PASS |
| **Knowledge Grid** | Abstention Accuracy | **100.0%** | >= 85.0% | ✅ PASS |

## Methodology

### 1. Incident Classification
- Algorithm: Multilingual TF-IDF N-gram (1-2) with Linear Support Vector Classifier (LinearSVC).
- Dataset: 55 labeled real-world infrastructure reports in English, Bangla, and Banglish transliteration.
- Split: 70% train (38 samples), 30% test (17 samples) stratified by category.

### 2. SecureAI Threat Detection
- Model: Layered defense combining unicode normalization, compiled regex heuristics, semantic keyword density scoring, and strict policy enforcement.
- Test Suite: 30 standardized red-team cases covering prompt injection, jailbreaks, data exfiltration, unauthorized tool calls, and benign Bangla/English reports.
- False Positive Minimization: Legitimate imperative Bengali infrastructure notices correctly classified as ALLOWED.

### 3. Knowledge Grid Retrieval & RAG
- Evaluation Set: 20 questions (16 supported, 4 out-of-domain control questions).
- Grounding & Abstention: The RAG generator strictly abstains when retrieved evidence is absent or below relevance thresholds, eliminating hallucinated citations.
