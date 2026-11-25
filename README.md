# Revenue Cycle Intelligence Lab

**Healthcare Revenue Cycle Simulation & Analytics**

## Study 01: Synthetic Anesthesia Claims & Denial Analysis

A healthcare revenue cycle simulation and analytics portfolio study focused on **building, validating, and analyzing a reproducible, synthetic anesthesia claims dataset**. The study explores denial causes, recoverable financial exposure, recovery performance, payer differences, and operational improvement opportunities using Tableau.

### Study at a glance

| Metric | Result |
|---|---:|
| Synthetic claims | 3,000 |
| Claim lines | 3,263 |
| Initially denied claims | 303 |
| Denial events | 333 |
| Initial denial rate (excluding pending) | 10.6% |
| Unique recoverable revenue at risk | $120,826.76 |
| Recovered amount across denial events | $75,787.11 |
| Open claim-level revenue at risk | $30,708.43 |
| Preventable recoverable revenue at risk | $93,403.62 |

### What this study demonstrates

- **Synthetic data engineering:** Six related tables created using a deterministic generator, healthcare-specific reimbursement logic, evidence-backed denial scenarios, and timeline constraints.
- **Data modeling:** Tableau relationships preserve distinct claim, line, submission, authorization, coverage/COB, and denial-event grains.
- **Revenue cycle analytics:** Exploratory analysis across denial category, preventability, payer segment, facility, provider, recovery, repeat denials, and time.
- **Operational decision-making:** Recommendations focused on improving existing eligibility/COB, coding, documentation, and payer-monitoring processes.

### Tableau dashboards

| Dashboard | Purpose |
|---|---|
| **Study 01 — Executive Overview** | High-level KPIs, denial drivers, preventability |
| **Study 01 — Payer & Recovery Analysis** | Payer exposure, denial rates, recovery performance |
| **Study 01 — Operational Analysis** | Trends, facility exposure, repeat-denial activity |

*Dashboard screenshots and a Tableau Public link can be added after export/publication.*

### Documentation

- [Study 01 — Case Study](docs/Study_01_Case_Study.md)
- [Study 01 — Dataset Generation Methodology](docs/Study_01_Dataset_Generation_Methodology.md)

### Dataset and code

The frozen dataset contains: `Claims.csv`, `Claim_Lines.csv`, `Denial_Events.csv`, `Claim_Submissions.csv`, `Authorizations.csv`, and `Coverage_COB.csv`.

Generation is governed by the v19 rules and a deterministic Python script using seed `20260915`. The simulated dates of service are September 1, 2025 to August 31, 2026, with reporting snapshot September 15, 2026.

The dataset contains **synthetic information only**, not real patient records or protected health information (PHI). Real-world operational expertise and high-level metrics may inform generation rules, but source patient records are not supplied to the dataset.

### Interpretation

The study's main conclusion is **refinement rather than rescue**: the simulated practice displays broadly stable performance, with opportunities to strengthen existing upstream controls. This is a synthetic modeling and analytical exercise, not a performance assessment of a real organization.
