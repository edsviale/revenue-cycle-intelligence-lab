# Healthcare Revenue Cycle Simulation & Analytics 
Study 01: Synthetic Anesthesia Claims & Denial Analysis \
Dataset Generation Methodology

# Purpose

This document explains how the synthetic dataset for Study 01 of Revenue
Cycle Intelligence Lab was designed, generated, and validated. The
data-generation work was a major part of the project: the goal was not
simply to create rows that looked realistic, but to build an auditable
relational dataset in which reimbursement, workflow defects,
submissions, denials, recovery, and chronology were internally
consistent.

# Design Goals

- Create a realistic but fully synthetic anesthesia revenue cycle
  dataset with no PHI.

- Preserve relational structure rather than flattening all information
  into one table.

- Generate denials from underlying evidence instead of assigning generic
  denial labels at random.

- Model reimbursement differently for Medicare FFS, Medi-Cal FFS,
  California Workers' Compensation, and commercial/managed-care payers.

- Represent corrected submissions, repeat denials, authorizations,
  eligibility/COB evidence, recovery, and unresolved claims.

- Create a point-in-time snapshot in which future activity is not
  visible.

- Make the dataset reproducible through a fixed random seed and a
  deterministic generation script.

# Reproducibility and Snapshot

| **Parameter**          | **Value**                           |
|------------------------|-------------------------------------|
| Generation seed        | 20260915                            |
| Service date range     | September 1, 2025 - August 31, 2026 |
| Report / snapshot date | September 15, 2026                  |
| Target claim count     | 3,000                               |

The generator uses a fixed seed so the same rules reproduce the same six
CSV files. The report date acts as a censoring boundary: adjudications,
denials, follow-up, appeals, resolutions, and submissions that would
occur after September 15, 2026 are not exposed in the snapshot.

# Relational Architecture

The final production model contains six tables, each with a defined
grain:

| **Table**             | **Grain**                           | **Purpose**                                                         |
|-----------------------|-------------------------------------|---------------------------------------------------------------------|
| Claims.csv            | 1 row per claim                     | Claim-level operational and financial summary                       |
| Claim_Lines.csv       | 1 row per CPT/service line          | Submitted/correct coding, modifiers, units, and line financials     |
| Denial_Events.csv     | 1 row per denial event              | Denial reason, evidence, root cause, sequence, recovery, and status |
| Claim_Submissions.csv | 1 row per payer transmission        | Original, corrected, duplicate, and resubmission history            |
| Authorizations.csv    | 1 row per authorization record      | Authorization status and evidence supporting authorization denials  |
| Coverage_COB.csv      | 1 row per claim coverage/COB record | Eligibility, coverage dates, payer order, and COB evidence          |

Claims.csv functions as the central claim-level entity, but the
one-to-many detail remains in separate tables so claim lines,
submissions, and denial events can be analyzed without multiplying
claim-level dollars.

# Generation Order

Claims were generated hierarchically in the following order:

1.  Service Date

2.  Location / setting

3.  Procedure group

4.  Primary CPT

5.  Anesthesia duration

6.  Provider

7.  Payer

8.  Expected reimbursement and billed amounts

9.  Workflow requirements such as authorization, documentation,
    eligibility, and COB

10. Underlying workflow defects or modeled payer-processing errors

11. Original claim submission

12. Initial adjudication

13. Supported denial event, when applicable

14. Corrected submission / appeal / follow-up

15. Resolution, recovery, or unresolved status

This ordering matters because later events depend on earlier facts. A
denial is therefore an outcome of a modeled defect or payer error, not
an independent random label.

# Clinical and Operational Population

The dataset models a fictional California anesthesia practice across
multiple facilities, settings, counties, providers, procedure groups,
CPT families, payer types, and service dates. Provider and facility
identity were intentionally prevented from directly driving denial
probability so that apparent provider/facility patterns would emerge
from the generated case mix and workflow rather than from hard-coded
poor performers.

Service volume varies modestly by month, including a modest December
elective-volume dip. No direct seasonal denial-rate multiplier was used.

# Reimbursement Modeling

## Medicare FFS

Expected allowance is based on CMS anesthesia base units plus actual
anesthesia minutes divided by 15, multiplied by the modeled
locality/year anesthesia conversion factor. The conversion factor is
selected from the claim's service-date year and California Medicare
locality.

Worked example (2026 Medicare FFS, Area 17): CPT 00160, 5 CMS base
units, 96 anesthesia minutes, and a \$20.99 conversion factor. Expected
allowed = (5 + 96 ÷ 15) × \$20.99 = (5 + 6.4) × \$20.99 = \$239.29.
Medicare time units use actual minutes ÷ 15, without rounding to whole
units before the calculation.

## Medi-Cal FFS

Physician reimbursement is modeled as (Base Units + Medi-Cal Time Units)
x \$14.01. CRNA reimbursement is modeled as ((Base Units - 1) + Medi-Cal
Time Units) x \$11.02. Medi-Cal time units use the project's validated
whole-unit timing rule rather than Medicare's continuous minutes/15
calculation.

**Worked example (Medi-Cal FFS, CRNA):** Claim CLM200121, CPT 00400, 3
base units, 103 anesthesia minutes, and a \$11.02 CRNA conversion
factor. The 103 minutes produce 6 complete 15-minute intervals plus 1
whole time unit for the remaining 13 minutes, giving 7 Medi-Cal time
units. Expected allowed = ((3 - 1) + 7) × \$11.02 = 9 × \$11.02 =
\$99.18. Under this model, a remainder of at least 5 minutes counts as
an additional time unit.

## California Workers' Compensation

Expected allowance is modeled as (CMS Base Units + Workers' Compensation
Time Units) x the applicable DWC anesthesia conversion factor. Time
units are minutes/15 rounded to one decimal place, with the 2025 or 2026
DWC table selected according to the service date and locality.

Worked example (2026 California Workers’ Compensation, Area 18): CPT
00170, 5 CMS base units, 58 anesthesia minutes, and a \$32.09 DWC
conversion factor. Workers’ Compensation time units = round(58 ÷ 15, 1)
= 3.9. Expected allowed = (5 + 3.9) × \$32.09 = \$285.60. The applicable
DWC conversion factor depends on service date and locality.

## Commercial and Managed Care

Commercial and managed-care reimbursement uses synthetic payer-specific
profiles. Each payer receives one fixed seeded profile rather than a new
random rate for every claim. Modeled ranges include Commercial
PPO/POS/OAP conversion factors of 58-72 and HMO/EPO conversion factors
of 48-62, with separate modeled approaches for Exchange, Medicare
Advantage, Medi-Cal Managed, network/other commercial, and out-of-area
Medicaid payers.

These rates are synthetic modeling assumptions and are not presented as
real contracted rates for any actual payer.

**Worked example (illustrative Commercial PPO/POS):** Assume a synthetic
\$64.00 per-unit conversion factor, 5 base units, and 90 anesthesia
minutes (6 time units). Expected allowed = (5 + 90 ÷ 15) × \$64.00 = 11
× \$64.00 = \$704.00. The \$64.00 factor is illustrative within the
modeled PPO/POS range (\$58–\$72); it is not an actual payer contract
rate or the observed rate of a specific dataset row. Other managed-care
segments use different rules: Medicare Advantage uses a payer-specific
multiplier of modeled Medicare reimbursement; Medi-Cal Managed uses a
payer-specific multiplier of modeled Medi-Cal reimbursement. Expected
allowed is capped at gross billed charges.

# Denial Generation: Evidence First

The governing denial rule is evidence first: create the underlying
defect or payer-processing condition, then generate only the denial
scenario supported by that evidence. This prevents impossible
combinations such as an authorization denial without authorization data
or a modifier denial when the submitted modifier is actually correct.

The final denial master contains 26 modeled scenarios (DEN01-DEN26)
spanning:

- Eligibility / Coverage

- Authorization / Precertification

- Coding / Modifier

- Missing Information / Documentation

- Medical Necessity

- COB / Wrong Payer

- Duplicate Claim

- Timely Filing

- Bundling

- Non-Covered Service

- Payer / Processing Issue

Each denial event records evidence linkage, defect field, submitted
value, expected value, CARC/RARC coding where applicable,
preventability, root-cause ownership, denied amount, recoverable revenue
at risk, resolution activity, and final denial status.

# Authorization Modeling

Authorization logic is stored in Authorizations.csv and linked to denial
events only when supporting authorization evidence exists. The model can
represent missing authorization, service/CPT mismatch, authorization
outside the valid date range, and provider/location mismatch. It does
not assume that every anesthesia case has a simple anesthesia-specific
authorization because real anesthesia workflows often depend on
authorizations initiated by facilities or surgeon offices.

# Eligibility and COB Modeling

Coverage_COB.csv stores coverage dates, member/coverage evidence, actual
billed payer, expected responsible payer, and other active coverage.
Eligibility and COB denials are generated from these underlying records,
while later payer corrections are represented through new submissions
rather than by rewriting the original claim history.

# Coding and Claim-Line Modeling

Claim_Lines.csv stores submitted and correct CPTs, modifiers, settings,
base units, time units, and total units separately. This allows coding
denials to preserve the actual submitted defect while maintaining a
correct reimbursement benchmark. Secondary services and bundling
relationships are also modeled at the line level.

# Submissions, Repeat Denials, and Chronology

Claim_Submissions.csv preserves the original transmission plus
corrected, resubmitted, or duplicate transmissions. Denial_Events.csv
links each denial to the submission that produced it. Later denial
sequences reference the immediately prior denial and can occur only
after an intervening corrective/resubmission action.

Repeat denial events may retain an operational denied amount, but they
do not automatically create new unique revenue at risk. This prevents
the same dollars from being counted repeatedly when a claim is denied
more than once.

# Recovery and Financial Logic

- Recovered Amount cannot exceed the relevant denied/recoverable amount.

- Open / Unresolved denials carry no recovered amount.

- True duplicate denials and correctly bundled secondary services are
  modeled as no-revenue-opportunity outcomes.

- Unique Revenue at Risk is designed to de-duplicate repeat denial
  chains.

- Final Paid Amount cannot exceed Expected Allowed Amount.

- Claim-level and line-level financials reconcile to their modeled
  reimbursement logic.

# Point-in-Time Snapshot Rules

- Pending claims have no initial adjudication, paid amount, denied
  amount, or denial event.

- No visible initial adjudication, denial, follow-up, appeal,
  resolution, or submission date can occur after the report date.

- Future activity is left blank rather than moved earlier to make the
  record look complete.

- Resolution dates cannot precede denial dates.

- Subsequent denials must occur after the corrective submission that
  could have produced the new adjudication.

# Controlled Regeneration and QA

After the generation rules were finalized, the dataset was regenerated
from the fixed seed and subjected to structural, financial,
reimbursement, chronology, evidence, and distribution checks. The
regeneration was repeated to confirm deterministic output.

| **QA Metric**           | **Final Result**                |
|-------------------------|---------------------------------|
| Claims                  | 3,000                           |
| Claim lines             | 3,263                           |
| Denial events           | 333                             |
| Claim submissions       | 3,228                           |
| Authorizations          | 992                             |
| Coverage/COB records    | 3,000                           |
| Pending claims          | 133                             |
| Initially denied claims | 303                             |
| Adjudicated claims      | 2,867                           |
| Initial denial rate     | 10.57%                          |
| Denial sequence counts  | 303 first / 29 second / 1 third |
| Hard QA failures        | 0                               |
| Warnings                | 0                               |
| Release status          | PASS                            |

Post-regeneration validation included targeted checks of Medicare FFS,
Medi-Cal FFS, Workers' Compensation reimbursement, snapshot censoring,
denial evidence, duplicate/bundling logic, and repeat-denial chronology.

# Why the Dataset Was Built This Way

The project intentionally treats synthetic-data engineering as part of
the portfolio work. A dashboard can only be as credible as the data
model behind it. Building the dataset required translating revenue-cycle
concepts into explicit schemas, relationships, reimbursement formulas,
workflow rules, denial evidence, and chronology constraints. The
resulting analysis is therefore not just an exercise in reading a
prepared dataset; it also demonstrates data modeling, business-rule
design, validation, and reproducibility.

# Limitations

- The dataset is synthetic and does not represent the performance of any
  real anesthesia practice, provider, facility, or payer.

- Commercial reimbursement profiles are modeled assumptions, not real
  contracts.

- The denial logic is intentionally bounded to 26 portfolio scenarios
  and is not a complete representation of every CARC/RARC or payer
  policy.

- Medical-policy and clinical-necessity logic is simplified for
  portfolio purposes.

- Authorization workflows are necessarily simplified; real anesthesia
  authorization responsibility can vary among payers, facilities,
  surgeon offices, and anesthesia groups.

- Observed analytical patterns should be interpreted as properties of
  this synthetic population, not generalized as industry benchmarks.

# Source Files for Reproducibility

- Project_2_Generation_Rules_v19.md - final human-readable generation
  specification

- Project_2_Generation_Rules_v19.json - machine-readable rules companion

- regenerate_project2.py - controlled generation script

- Project_2_QA_Report.txt - final automated QA summary

- Project_2_Controlled_Regeneration_Package.zip - final regeneration
  package

# Data Privacy

All records are synthetic and contain no protected health information
(PHI).

# Personal Thoughts and Final Review

The following reflections describe how I would improve the model, how I
might reuse it, and what I learned while developing it.

## What I Would Do Differently Next Time

- Review my practice’s operational metrics—including time to bill, case
  volume and seasonality, procedure mix, denial rates, and resolution
  timing—to adjust the rules and distributions used to generate a future
  synthetic dataset that better represents daily operations. The
  operational metrics would guide modeling decisions only; no real
  patient records or PHI would be entered into this dataset generator or
  used as training data.

- Use the generator to represent very different fictional practices,
  each with its own workflows, payer mix, operational constraints, and
  deliberately distinct issues to investigate and improve.

- Refine the reimbursement model at the individual-payer level,
  particularly within Commercial PPO/POS and HMO/EPO. Compare modeled
  payer-specific conversion factors and contract terms with actual
  practice experience, including relevant Medicare-linked adjustments
  and payment recoupments or clawbacks, without treating the current
  synthetic profiles as real contracts.

## Future Uses of the Dataset

Beyond refining the generation rules, I see the model as a foundation
for larger synthetic datasets—including populations well beyond 3,000
claims—that could support:

- Practice drilling from high-level dashboards into individual claim
  histories within a large, relational dataset.

- Investigations into operational and financial trends that could reveal
  opportunities for workflow improvement or revenue protection.

- Training exercises, reporting practice, and realistic hiring
  assessments for revenue-cycle or analytics roles, without exposing
  PHI. Because the records are synthetic, this approach also avoids
  using real patient information as training material.

## What I Learned

- Even with substantial revenue-cycle experience, I identified gaps in
  my understanding of the full claims process. Creating the model showed
  me where I need to keep learning.

- Developing a credible synthetic dataset is substantial work and
  depends on deep subject-matter knowledge. I could not readily build an
  equally detailed public-utility or retail dataset without first
  learning those industries.

- Working with a structured external or synthetic dataset can reveal
  reporting gaps in my own organization. For example, I would like
  better visibility into denial rates, timelines, and denial
  types—including paper denials—through a more unified tracking process.
  Better data capture would make our operational reviews more useful.

- All models have limits. This dataset is a useful starting point and
  represents many of the data relationships an anesthesia practice
  encounters, but it is cleaner and more controlled than real
  operational data. Future versions should account for more exceptions,
  incomplete inputs, inconsistent documentation, and process variation.
