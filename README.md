# 🚨 Incident Experience AI

## Memory-First Incident Response Agent

Incident Experience AI is an AI-powered production incident response agent that learns from previous incidents.

Instead of treating every production incident as a completely new problem, the agent retrieves relevant historical incident experience, reasons over it, recommends an investigation path, and stores the final resolution back into long-term memory.

The memory layer is powered by Hindsight.

---

## 🎯 Problem

Production incidents are expensive and stressful.

When a similar incident happens again, engineers often spend valuable time searching through:

- Previous incident reports
- Post-mortems
- Slack conversations
- Runbooks
- Tickets
- Personal notes

Important operational knowledge is easily lost.

The goal of Incident Experience AI is to turn previous incident resolution experience into reusable organizational memory.

---

## 💡 Solution

The agent follows a continuous learning loop:

NEW INCIDENT
↓
RECALL HISTORICAL INCIDENT EXPERIENCE
↓
AI REASONING
↓
INVESTIGATION RECOMMENDATION
↓
RESOLUTION
↓
CAPTURE OUTCOME
↓
HINDSIGHT MEMORY
↓
NEXT INCIDENT
↓
BETTER RESPONSE

---

## 🧠 Why Hindsight?

Hindsight provides persistent memory for the agent.

The application uses Hindsight to:

1. Retain incident information.
2. Extract structured memories from incident reports.
3. Recall relevant historical incidents.
4. Retrieve previous root causes and successful remediation.
5. Store new incident outcomes for future use.

This allows the agent to improve through accumulated incident experience.

---

## 🚨 Example

### Previous Incident

Production Orders API experienced high latency.

Root cause:

Missing database index.

Resolution:

Added the missing index.

Resolution time:

18 minutes.

The incident and its lessons are stored in Hindsight.

### Future Similar Incident

The agent receives another Orders API latency incident.

Instead of starting from zero, it recalls the previous experience and can recommend checking database query performance and indexes early.

---

## ✨ Features

### Persistent Incident Memory

Stores incident symptoms, root causes, investigation paths, remediation actions, outcomes and lessons learned.

### Similar Incident Recall

Searches historical incident experience before recommending actions.

### AI Root-Cause Reasoning

Uses retrieved historical evidence together with an LLM to analyze the current incident.

### Investigation Recommendations

Provides concrete investigation steps for incident responders.

### Evidence-Based Recommendations

The agent distinguishes historical evidence from inference and reports confidence.

### Outcome Learning

Resolved incidents are written back into Hindsight so future incidents can benefit from them.

### Incident Experience Dashboard

Provides a view of accumulated incident experience.

### Demo Mode

Demonstrates the memory-driven incident response loop.

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │   New Incident      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Hindsight Recall    │
                    │ Historical Memory   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Groq LLM          │
                    │ Incident Reasoning  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Investigation Path  │
                    │ Root Cause           │
                    │ Recommended Action   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Resolve Incident     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Hindsight Retain    │
                    │ New Experience      │
                    └─────────────────────┘