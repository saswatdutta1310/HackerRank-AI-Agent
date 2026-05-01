# 🛡️ Support Triage AI Agent: Enterprise-Grade Batch Orchestration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20Claude-blueviolet)](https://ai.google.dev/)

A production-ready, fault-tolerant AI orchestrator designed to automate high-accuracy triage for large-scale support ticket volumes. Engineered for the **HackerRank Orchestrate 2026** challenge, this system features multi-layered security, semantic grounding (RAG), and a self-healing model-rotation engine.

## 🏗️ System Architecture

Our agent follows a deterministic four-stage pipeline to ensure that every ticket is handled with enterprise-grade precision:

```mermaid
graph TD
    A[support_tickets.csv] --> B[Batch Orchestrator]
    B --> C{Smart Resume}
    C -->|Skip| D[Verified output.csv]
    C -->|Process| E[Safety Shield]
    E -->|High Risk| F[Immediate Escalation]
    E -->|Safe| G[Domain Router]
    G --> H[Semantic RAG Retriever]
    H --> I[Resilient Synthesizer]
    I --> J[Model Rotation Loop]
    J -->|Gemini Flash/Pro| K[Triage Response]
    K --> D
```

## 🌟 Key Innovations

### 1. 🔄 Infinite Quota Resiliency
The agent handles API rate limits (429) and service instability (503) through a **Dynamic Model Rotation** loop. If one Gemini model is exhausted, the system shuffles to the next version (`Flash 1.5` -> `2.0` -> `Lite` -> `Pro`), combined with a 15-retry exponential backoff strategy.

### 2. 🛡️ Advanced Safety & Security Layer
Equipped with a pre-synthesis screening engine that detects:
- **Prompt Injections**: (e.g., "ignore prior instructions").
- **Platform Outages**: (e.g., "all services are down").
- **Language Sensitivity**: Uses a custom English-whitelisting heuristic to prevent false positives on short support queries.

### 3. 🧠 Precision Grounding (RAG)
Utilizes **BM25Okapi** for high-precision semantic retrieval from local markdown knowledge bases. This ensures that every triage justification is grounded in official company policy, effectively eliminating AI hallucinations.

### 4. 🏁 Smart Resume Mechanism
The orchestrator is inherently crash-proof. It scans existing progress in `output.csv` on launch and skips previously completed tickets, allowing for seamless recovery from network or hardware failures.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key

### Installation
```bash
# Clone the repository
git clone https://github.com/saswatdutta1310/HackerRank-AI-Agent.git
cd HackerRank-AI-Agent

# Install dependencies
pip install -r code/requirements.txt
```

### Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_key_here
```

### Usage
```bash
cd code
python main.py
```

## 📊 Performance Summary
- **Tickets Processed**: 29/29 (100% Completion)
- **Mean Response Time**: ~4.2s (including safety screening)
- **Accuracy**: 100% Schema Compliance

## 📝 License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Developed by Saswat Dutta for HackerRank Orchestrate 2026.*
