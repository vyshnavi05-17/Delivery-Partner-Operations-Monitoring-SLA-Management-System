# OpsPulse — Delivery Partner Operations Monitoring & SLA Management System

OpsPulse is a simulated operations monitoring and SLA management system designed to demonstrate how delivery-partner support cases can be tracked, monitored, and managed in a structured operations environment.

The application provides a centralized dashboard for monitoring case status, SLA adherence, productivity, quality, SOP compliance, escalations, stakeholder responses, repeated issues, and operational exceptions.

> **Important:** This project uses completely synthetic/simulated data. It is an independent portfolio project and is not connected to Amazon, Amazon Flex, or any real delivery-partner operations system.

---

## 📌 Project Overview

In a fast-paced operations environment, associates need to:

- Follow defined SOPs
- Resolve cases within SLA
- Monitor priority cases
- Maintain accurate operational records
- Identify cases requiring escalation
- Track productivity and quality
- Respond to stakeholders within expected timelines
- Identify repeated operational issues
- Support continuous process improvement

OpsPulse simulates this workflow through an interactive operations dashboard.

---

## 🎯 Project Objectives

The main objectives of this project are to:

1. Monitor operational cases from creation to resolution.
2. Track SLA adherence based on case priority.
3. Identify cases that are approaching or exceeding their SLA.
4. Detect cases requiring escalation.
5. Monitor associate productivity and workload.
6. Track quality and SOP compliance.
7. Identify repeated issues within a defined time window.
8. Maintain structured operational records.
9. Provide actionable exception queues.
10. Present operational insights through interactive dashboards.

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────────┐
                    │   Synthetic Case Data   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Python Data Layer     │
                    │ Pandas + NumPy + Logic  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     SQLite Database     │
                    │     SQL Data Layer      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Business Services    │
                    │                         │
                    │ SLA Monitoring          │
                    │ Escalation Rules        │
                    │ Case Management         │
                    │ Productivity            │
                    │ Quality Monitoring      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Streamlit Dashboard  │
                    │      + Plotly Charts    │
                    └─────────────────────────┘
