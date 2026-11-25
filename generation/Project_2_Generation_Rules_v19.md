# Project 2 — Generation Rules

**Version:** 2.1 — Claims schema locked  
**Role:** Authoritative human-readable specification  
**Companion:** `Project_2_Generation_Rules.json`  
**Report date:** 2026-09-15  
**Service period:** 2025-09-01 through 2026-08-31  
**Claims:** 3,000  
**Seed:** 20260915

This file intentionally contains **both the original rules that remain valid and the revised/new rules identified during sanity checking**. The JSON companion mirrors the same specification for programmatic generation.

## Change labels
- **UNCHANGED** — original generation rule retained.
- **REVISED** — original rule changed after sanity checking.
- **NEW** — new table, field, or validation rule required after sanity checking.

## 1. Global generation principles
- Generate hierarchically: Service Date -> Location -> Procedure Group -> CPT -> Duration -> Provider -> Payer -> Financials -> Workflow Requirements -> Workflow Defects -> Submission -> Adjudication -> Possible Denial -> Resolution/Recovery.
- Provider and location identity do not directly influence denial probability.
- Do not change the generator merely to manufacture preferred findings.
- Every preventable denial must be traceable to an actual underlying claim/workflow defect.
- Every payer-error denial must be traceable to an otherwise valid claim plus an explicit modeled payer-processing error.
- Target initial denial rate: **9–12%**, preferably **10–11%**, but never force the result.

## 2. Tables and schema

**Schema lock status:** `Claims` = **LOCKED**. Remaining tables are still being finalized.

The revised model uses six core tables:

| Table | Grain | Purpose | Status |
|---|---|---|---|
| `Claims.csv` | One row per claim | Claim-level operational and financial summary | **LOCKED** |
| `Claim_Lines.csv` | One row per CPT/service line | Submitted/correct line coding, modifiers, units, and line financials | Draft |
| `Denial_Events.csv` | One row per denial event | Denial reason, root cause, recovery, sequencing | Draft |
| `Claim_Submissions.csv` | One row per payer transmission | Original, corrected, and duplicate submission history | Draft |
| `Authorizations.csv` | One row per authorization record | Authorization requirements and authorization-denial evidence | Draft |
| `Coverage_COB.csv` | One row per claim coverage/COB record | Eligibility, coverage, and payer-order evidence | Draft |

### Claims — **LOCKED**

**Grain:** one row per claim.  
**Purpose:** claim-level operational and financial summary.

#### Existing fields retained

- Claim ID
- Account
- Service Date
- Submit Date
- Initial Adjudication Date
- Provider Code
- Provider Name
- Provider Type
- Modifier
- Location Code
- Location Name
- Setting
- County
- Medicare Locality
- Procedure Group
- Primary CPT
- Anesthesia Minutes
- CMS Base Units
- Internal Anesthesia Units
- Payer Code
- Payer Name
- AR Type
- Payer Archetype
- Reimbursement Basis
- Modeled Filing Limit Days
- Gross Billed Amount
- Expected Allowed Amount
- Initial Claim Status
- Initial Paid Amount
- Initial Denied Amount
- Unique Revenue at Risk
- Final Paid Amount
- Final Balance
- Final Claim Status
- Denial Event Count
- Has Denial
- Claim Preventable
- Report Date

#### New claim-level fields

- Primary Diagnosis Code
- Diagnosis Category
- Documentation Required
- Documentation Status
- Referring Provider Required
- Referring Provider ID
- Referring Provider ID Valid
- Medical Necessity Review Required
- Prior Similar Service Count
- Authorization Required
- Authorization ID

#### Field interpretation rules

- `Modifier` represents the **correct/final primary anesthesia modifier**. The originally submitted modifier belongs in `Claim_Lines.csv`.
- `Primary CPT` represents the correct/intended primary CPT.
- `CMS Base Units` and `Internal Anesthesia Units` represent correct/reference values used for reimbursement and defect comparison.
- `Denial Event Count`, `Has Denial`, and `Claim Preventable` are derived from denial-event logic rather than independently randomized.
- If `Initial Adjudication Date > Report Date`, expose `Initial Adjudication Date` as blank/null and keep the claim `Pending`.
- Pending claims must have Initial Paid Amount = 0, Initial Denied Amount = 0, Denial Event Count = 0, and Has Denial = No.

#### Fields intentionally moved out of Claims

**To `Claim_Lines.csv`:**
- Submitted Modifier
- Correct Modifier
- Submitted Base Units
- Correct Base Units
- Submitted Time Units
- Correct Time Units

**To `Coverage_COB.csv`:**
- Coverage Effective Date
- Coverage Termination Date
- Eligibility Check Date
- Eligibility Check Result
- Member Information Match
- Eligibility Defect Type
- Primary Payer
- Secondary Payer
- Expected Responsible Payer
- Billed Payer
- COB Sequence
- Other Active Coverage

**To `Claim_Submissions.csv`:** submission number, submission type, and resubmission/corrected-claim history.

#### QA-only fields removed from production `Claims.csv`

These can remain in the QA workbook but are not part of the final source schema:

- DOS to Drop
- Days from Submit to Adjudication Date
- Billed vs Allowed
- Denied vs Expected/Allowed
- Column1

### Claim_Lines — draft
- One row per CPT/service line.
- Detailed schema will be locked next.

### Denial_Events — draft
- One row per denial event.
- Detailed schema will be locked after Claim_Lines.

### Claim_Submissions — draft
- One row per payer transmission.
- Detailed schema will be locked after Denial_Events.

### Authorizations — draft
- One row per authorization record.
- Supports authorization-denial evidence.

### Coverage_COB — draft
- One row per claim coverage/COB record.
- Supports eligibility, coverage, and payer-order evidence.


## 3. Facility / county / setting map — UNCHANGED
- **Pacific Crest Medical Center — Inpatient** — Los Angeles County; Hospital - Inpatient
- **Pacific Crest Medical Center — Outpatient** — Los Angeles County; Hospital - Outpatient
- **Pacific Crest Medical Center — ER** — Los Angeles County; Hospital - ER
- **Silver Ridge Regional Hospital — Inpatient** — Riverside County; Hospital - Inpatient
- **Silver Ridge Regional Hospital — Outpatient** — Riverside County; Hospital - Outpatient
- **Silver Ridge Regional Hospital — ER** — Riverside County; Hospital - ER
- **Redwood Haven Community Hospital — Inpatient** — Ventura County; Hospital - Inpatient
- **Redwood Haven Community Hospital — Outpatient** — Ventura County; Hospital - Outpatient
- **Redwood Haven Community Hospital — ER** — Ventura County; Hospital - ER
- **Canyon Crest Orthopedic Surgery Center** — Orange County; Ambulatory Surgery Center
- **Sequoia Specialty Surgery Center** — Los Angeles County; Ambulatory Surgery Center
- **Clearview Ambulatory Center** — Orange County; Ambulatory Surgery Center
- **Cypress Grove Surgery Center** — Riverside County; Ambulatory Surgery Center
- **Golden Valley Surgical Center** — San Bernardino County; Ambulatory Surgery Center
- **Pacific Coast Outpatient Center** — Ventura County; Outpatient Center

## 4. Provider roster and modifier logic — UNCHANGED
**Anesthesiologists:** Adrian Mercer, MD; Maya Chen, MD; Daniel Navarro, MD; Rebecca Lawson, MD; Marcus Bennett, MD; Elena Vasquez, MD; Nathan Kim, MD; Olivia Hart, MD; Samuel Reed, MD; Priya Shah, MD; Christopher Hale, MD

**CRNAs:** Jordan Ellis, CRNA; Morgan Price, CRNA; Taylor Brooks, CRNA; Cameron Foster, CRNA; Avery Collins, CRNA

- MD → AA
- CRNA → QZ
- QX/QY/QK medical-direction relationships remain out of scope.
- Provider identity does not directly alter denial probability.

### Provider-facility affiliations — UNCHANGED
- **Canyon Crest Orthopedic Surgery Center:** Cameron Foster, CRNA; Christopher Hale, MD; Morgan Price, CRNA; Rebecca Lawson, MD; Samuel Reed, MD
- **Clearview Ambulatory Center:** Avery Collins, CRNA; Cameron Foster, CRNA; Jordan Ellis, CRNA; Maya Chen, MD; Priya Shah, MD; Rebecca Lawson, MD; Samuel Reed, MD
- **Cypress Grove Surgery Center:** Maya Chen, MD; Morgan Price, CRNA; Nathan Kim, MD
- **Golden Valley Surgical Center:** Cameron Foster, CRNA; Christopher Hale, MD; Olivia Hart, MD; Samuel Reed, MD; Taylor Brooks, CRNA
- **Pacific Coast Outpatient Center:** Avery Collins, CRNA; Daniel Navarro, MD; Elena Vasquez, MD; Olivia Hart, MD; Taylor Brooks, CRNA
- **Pacific Crest Medical Center — ER:** Adrian Mercer, MD; Marcus Bennett, MD
- **Pacific Crest Medical Center — Inpatient:** Adrian Mercer, MD; Elena Vasquez, MD; Jordan Ellis, CRNA; Marcus Bennett, MD; Priya Shah, MD
- **Pacific Crest Medical Center — Outpatient:** Adrian Mercer, MD; Avery Collins, CRNA; Elena Vasquez, MD; Jordan Ellis, CRNA; Marcus Bennett, MD; Priya Shah, MD; Rebecca Lawson, MD
- **Redwood Haven Community Hospital — ER:** Daniel Navarro, MD; Olivia Hart, MD
- **Redwood Haven Community Hospital — Inpatient:** Daniel Navarro, MD; Olivia Hart, MD; Taylor Brooks, CRNA
- **Redwood Haven Community Hospital — Outpatient:** Daniel Navarro, MD; Olivia Hart, MD; Taylor Brooks, CRNA
- **Sequoia Specialty Surgery Center:** Adrian Mercer, MD; Avery Collins, CRNA; Elena Vasquez, MD; Jordan Ellis, CRNA; Priya Shah, MD; Rebecca Lawson, MD
- **Silver Ridge Regional Hospital — ER:** Christopher Hale, MD; Nathan Kim, MD
- **Silver Ridge Regional Hospital — Inpatient:** Christopher Hale, MD; Marcus Bennett, MD; Maya Chen, MD; Morgan Price, CRNA; Nathan Kim, MD
- **Silver Ridge Regional Hospital — Outpatient:** Cameron Foster, CRNA; Christopher Hale, MD; Maya Chen, MD; Morgan Price, CRNA; Nathan Kim, MD; Samuel Reed, MD

## 5. Procedure generation — UNCHANGED unless marked
### Procedure mix targets
- **Hospital - Inpatient:** Hospital/General 25%, Orthopedic 18%, Spine 14%, Urology 12%, GI 8%, ENT 7%, Plastic 4%, Hand 4%, Foot 4%, Ophthalmology 4%
- **Hospital - Outpatient:** GI 25%, Orthopedic 20%, Ophthalmology 12%, Urology 10%, ENT 10%, Hand 7%, Foot 6%, Plastic 5%, Hospital/General 3%, Spine 2%
- **Hospital - ER:** Hospital/General 30%, Orthopedic 22%, Urology 14%, ENT 10%, Hand 8%, Foot 7%, Spine 5%, Plastic 4%
- **Canyon Crest Orthopedic Surgery Center:** Orthopedic 70%, Hand 12%, Foot 10%, Spine 5%, Pain 3%
- **Sequoia Specialty Surgery Center:** GI 25%, ENT 18%, Urology 17%, Ophthalmology 15%, Plastic 10%, Orthopedic 8%, Hand 4%, Pain 3%
- **Clearview Ambulatory Center:** GI 30%, Orthopedic 20%, Ophthalmology 15%, ENT 10%, Urology 10%, Hand 5%, Foot 5%, Plastic 3%, Pain 2%
- **Cypress Grove Surgery Center:** Orthopedic 28%, GI 22%, Urology 12%, Hand 10%, Foot 10%, ENT 7%, Ophthalmology 5%, Spine 4%, Pain 2%
- **Golden Valley Surgical Center:** Orthopedic 35%, Hand 15%, Foot 15%, Spine 10%, Urology 8%, GI 6%, ENT 5%, Pain 4%, Plastic 2%
- **Pacific Coast Outpatient Center:** GI 32%, Ophthalmology 18%, ENT 12%, Urology 10%, Orthopedic 10%, Plastic 7%, Hand 5%, Foot 3%, Pain 3%

### CPT family weights
- **Hospital/General:** 00100 30%, 00520 35%, 00532 35%
- **Ophthalmology:** 00142 65%, 00145 35%
- **ENT:** 00160 60%, 00170 40%
- **Plastic:** 00300 45%, 00400 55%
- **Spine:** 00630 60%, 00670 40%
- **GI:** 00731 25%, 00732 10%, 00811 25%, 00812 25%, 00813 15%
- **Urology:** 00910 25%, 00912 25%, 00914 20%, 00918 30%
- **Orthopedic:** 01210 8%, 01214 18%, 01380 10%, 01400 16%, 01402 20%, 01610 8%, 01620 8%, 01630 12%
- **Foot:** 01464 30%, 01470 35%, 01480 35%
- **Hand:** 01710 25%, 01810 35%, 01820 25%, 01830 15%
- **Pain:** 01991 55%, 01992 45%

### Duration profiles
| CPT | Median | Min | Max |
|---|---:|---:|---:|
| 00100 | 75 | 30 | 180 |
| 00142 | 45 | 20 | 90 |
| 00145 | 90 | 45 | 180 |
| 00160 | 75 | 30 | 150 |
| 00170 | 60 | 25 | 120 |
| 00300 | 90 | 35 | 240 |
| 00400 | 100 | 40 | 240 |
| 00520 | 75 | 30 | 180 |
| 00532 | 45 | 20 | 90 |
| 00630 | 120 | 60 | 240 |
| 00670 | 240 | 120 | 480 |
| 00731 | 35 | 15 | 75 |
| 00732 | 75 | 30 | 180 |
| 00811 | 40 | 20 | 90 |
| 00812 | 35 | 20 | 75 |
| 00813 | 55 | 25 | 120 |
| 00910 | 45 | 20 | 90 |
| 00912 | 70 | 30 | 150 |
| 00914 | 120 | 60 | 240 |
| 00918 | 75 | 30 | 150 |
| 01210 | 90 | 45 | 180 |
| 01214 | 150 | 90 | 300 |
| 01380 | 90 | 45 | 180 |
| 01400 | 90 | 45 | 180 |
| 01402 | 150 | 90 | 300 |
| 01464 | 75 | 35 | 150 |
| 01470 | 90 | 40 | 180 |
| 01480 | 110 | 50 | 240 |
| 01610 | 75 | 35 | 150 |
| 01620 | 90 | 40 | 180 |
| 01630 | 110 | 50 | 240 |
| 01710 | 75 | 30 | 150 |
| 01810 | 60 | 25 | 120 |
| 01820 | 75 | 30 | 150 |
| 01830 | 100 | 45 | 210 |
| 01991 | 45 | 20 | 90 |
| 01992 | 60 | 30 | 120 |

Durations remain whole-minute, right-skewed, bounded, and independent of provider/payer.

## 6. Financial generation — UNCHANGED
- Practice gross charge is payer-independent.
- Primary gross formula: `ROUND((Base Units + Minutes/15) * 140, 0)`.
- Secondary gross 64415: $900
- Secondary gross 64447: $950
- Secondary gross 64450: $650
- Secondary gross 64483: $1,100
- Secondary gross 62321: $1,000
- Secondary gross 76942: $300
- Allowed <= Billed.
- Initial Denied Amount uses expected allowed dollars affected, not gross charges.
- Recovered Amount <= remaining recoverable allowed amount.
- Unique Revenue at Risk de-duplicates repeat denials.

## 7. Reimbursement
### Medicare FFS — UNCHANGED
`(Base Units + actual minutes/15) × locality anesthesia CF`

| Year | Area 18 | Area 17 | Area 62 |
|---|---:|---:|---:|
| 2025 | $21.22 | $20.88 | $20.71 |
| 2026 | $21.26 | $20.99 | $20.88 |

### Medi-Cal FFS — UNCHANGED after manual validation
- Physician: `(Base Units + Medi-Cal Time Units) × $14.01`.
- CRNA: `((Base Units - 1) + Medi-Cal Time Units) × $11.02`.
- Full 15-minute units; add one unit when remainder ≥ 5 minutes; preserve applicable under-five-minute rule.
- Sanity-check example CLM200966 correctly calculated to **$132.24**.

## Reimbursement rules — Medicare FFS and Medi-Cal FFS — LOCKED

### Medicare FFS

Formula:

`(CMS Base Units + Anesthesia Minutes / 15) × locality anesthesia conversion factor`

Rules:

- Use actual anesthesia minutes divided by 15.
- Do **not** use the Medi-Cal whole-unit rounding rule.
- Use the conversion factor matching the claim's Service Date year and Medicare locality.
- Round the final expected allowed amount to cents.

| Year | Area 18 LA/Orange | Area 17 Ventura | Area 62 Riverside/San Bernardino |
|---|---:|---:|---:|
| 2025 | $21.22 | $20.88 | $20.71 |
| 2026 | $21.26 | $20.99 | $20.88 |

### Medi-Cal FFS

**Physician**

`(Base Units + Medi-Cal Time Units) × $14.01`

**CRNA**

`((Base Units - 1) + Medi-Cal Time Units) × $11.02`

Time-unit rule:

- count full 15-minute units;
- add one additional unit when the remaining minutes are **5 minutes or more**;
- preserve applicable under-five-minute handling;
- round the final expected allowed amount to cents.

Primary modifier mapping remains:

- Physician → `AA`
- CRNA → `QZ`

Validated example:

`CLM200966` — CRNA, CPT 00400, 147 minutes, 3 base units:

- 147 minutes → 10 Medi-Cal time units
- `(3 - 1) + 10 = 12 units`
- `12 × $11.02 = $132.24`

### Global reimbursement constraints

- `Expected Allowed Amount <= Gross Billed Amount`.
- Use the correct payer-specific time-unit methodology before calculating expected allowance.
- Correct/canonical base units determine the expected allowance. Erroneous submitted units may support a denial, but they do not redefine the correct reimbursement benchmark.
- For the same DOS, payer basis, locality, provider type, CPT, and anesthesia minutes, the reimbursement calculation must be deterministic.


### California Workers’ Compensation — REVISED
- Formula: `(Base Units + WC Time Units) × DWC locality CF`.
- WC Time Units = `round(actual minutes/15, 1)`.
- Do **not** use Medi-Cal whole-unit rounding.

| Year | Area 18 | Area 17 | Area 62 |
|---|---:|---:|---:|
| 2025 | $31.27 | $30.77 | $30.51 |
| 2026 | $32.09 | $31.68 | $31.52 |

- 2025 table applies through 2026-02-28; 2026 table applies beginning 2026-03-01 within this dataset.
- Recalculate WC allowed, paid, denied, balance, and recovery-related amounts.

### Commercial / managed care — UNCHANGED synthetic profiles
- Commercial PPO/POS/OAP: 58-72 CF
- HMO/EPO: 48-62 CF
- Exchange: 46-58 CF
- Medicare Advantage: 105-120% Medicare FFS
- Medi-Cal Managed: 105-125% Medi-Cal FFS
- Network/Other Commercial: 45-58 CF
- Out-of-Area Medicaid: 90-110% Medi-Cal FFS
- Use one fixed seeded profile per payer, not a new random rate per claim.

## 8. Payer administrative profiles — UNCHANGED synthetic assumptions
| Archetype | Auth | Filing days | Eligibility mult | Bundling mult | COB mult | Documentation mult |
|---|---:|---:|---:|---:|---:|---:|
| Commercial PPO/POS | 25% | 180 | 1.00 | 1.00 | 1.00 | 1.00 |
| HMO/EPO | 45% | 120 | 1.15 | 1.10 | 1.05 | 1.05 |
| Exchange | 35% | 120 | 1.25 | 1.00 | 1.15 | 1.00 |
| Medicare FFS | 5% | 365 | 0.80 | 1.20 | 1.30 | 1.15 |
| Medicare Advantage | 35% | 120 | 1.00 | 1.20 | 1.15 | 1.15 |
| Medi-Cal FFS | 20% | 180 | 1.25 | 1.00 | 1.10 | 1.10 |
| Medi-Cal Managed | 45% | 120 | 1.35 | 1.05 | 1.20 | 1.15 |
| Workers Compensation | 60% | 365 | 1.10 | 0.90 | 0.70 | 1.30 |
| Other | 25% | 180 | 1.10 | 1.00 | 1.00 | 1.00 |

## 9. Workflow defect probabilities — UNCHANGED unless evidence makes scenario ineligible
- **Eligibility:** 1.7% * payer eligibility multiplier
- **Authorization:** 6.5% of claims actually requiring auth
- **Coding/Modifier:** 1.6%; x1.30 with secondary services
- **Missing Information/Documentation:** 1.2% * documentation multiplier
- **Medical Necessity:** 0.7% * documentation multiplier; sensitive services only
- **COB/Wrong Payer:** 0.8% * COB multiplier
- **Duplicate:** 0.5%
- **Timely Filing:** 0.35%; only by actual lag beyond modeled filing limit
- **Bundling:** 7.5% of eligible secondary-service claims
- **Non-Covered:** 0.6%; x2 for pain/injection
- **Payer/External Processing:** 0.7%

Detection probabilities are also retained: Eligibility 98%, Authorization 98%, Coding 93%, Missing 92%, Medical Necessity 90%, COB 95%, Duplicate 100%, Timely Filing 100%, Bundling 95%, Non-Covered 95%, Payer Processing 100%.

## 10. Denial master and evidence requirements
**REVISED governing rule:** a denial scenario may only be generated when its supporting evidence exists in the underlying data.

| ID | Business category | CARC/RARC | Root cause | Evidence required |
|---|---|---|---|---|
| DEN01 | Eligibility / Coverage | 26 | Coverage effective after DOS | Coverage Effective Date > Service Date |
| DEN02 | Eligibility / Coverage | 27 | Coverage terminated before DOS | Coverage Termination Date < Service Date |
| DEN03 | Eligibility / Coverage | 31 | Incorrect/mismatched member information | Member Information Match = No |
| DEN04 | Payer / Processing Issue | 31 | Payer eligibility file incorrect or delayed | Internally valid claim + explicit modeled payer eligibility-file error |
| DEN05 | Authorization / Precertification | 197 | Required authorization was never obtained | Authorization required and authorization absent |
| DEN06 | Authorization / Precertification | TBD | Authorized CPT/service mismatch | Submitted CPT/service not covered by authorization record |
| DEN07 | Authorization / Precertification | 210 | Authorization outside valid timeframe | Authorization timeframe does not cover DOS |
| DEN08 | Authorization / Precertification | 16 / N54 | Claim information mismatch with authorized service | Claim and authorization attributes conflict |
| DEN09 | Coding / Modifier | 4 | Incorrect or missing anesthesia modifier | Submitted Modifier missing or differs from Correct Modifier |
| DEN10 | Coding / Modifier | 5 | Procedure/place-of-service mismatch | Submitted CPT/setting violates explicit compatibility rule |
| DEN11 | Coding / Modifier | 11 | Diagnosis inconsistent with procedure | Diagnosis present and conflicts with modeled procedure logic |
| DEN12 | Missing Information / Documentation | 16 / M76 | Missing, incomplete, or invalid diagnosis | Diagnosis missing/invalid |
| DEN13 | Missing Information / Documentation | 16 / M53 | Missing or invalid units | Submitted units missing or differ from correct units |
| DEN14 | Missing Information / Documentation | 16 / N286 | Referring provider identifier missing or invalid | Required referring provider ID absent/invalid |
| DEN15 | Missing Information / Documentation | 252 / M127 | Records required but not submitted | Documentation required and not submitted |
| DEN16 | Medical Necessity | 50 | Service not medically necessary | Diagnosis/documentation fails modeled medical-necessity rule |
| DEN17 | Medical Necessity | 151 | Frequency/number of services not supported | Prior-service/frequency history exceeds modeled rule |
| DEN18 | COB / Wrong Payer | 22 | Other insurance primary | Another active payer is primary under modeled COB order |
| DEN19 | COB / Wrong Payer | 109 | Claim submitted to wrong payer | Billed Payer != Expected Responsible Payer |
| DEN20 | Duplicate Claim | 18 | Unnecessary duplicate resubmission | Claim_Submissions proves prior + unnecessary duplicate resubmission |
| DEN21 | Payer / Processing Issue | 18 | Payer incorrectly classified claim as duplicate | Submission history does not support true duplicate + modeled payer error |
| DEN22 | Timely Filing | 29 | Filing limit exceeded | Submit Date - Service Date > Modeled Filing Limit Days |
| DEN23 | Bundling / Non-Separately Payable | 97 | Correctly included in another allowance | Eligible secondary service modeled as bundled |
| DEN24 | Payer / Processing Issue | 97 | Payer incorrectly bundled separately payable service | Eligible secondary service otherwise separately payable + modeled payer error |
| DEN25 | Non-Covered Service | 96 / N130 | Non-covered service | Modeled coverage rule excludes service |
| DEN26 | Non-Covered Service | 204 | Service not covered under current benefit | Modeled benefit rule excludes service |

**DEN06 is REVISED:** replace “authorized units/services exceeded” with **authorized CPT/service mismatch**.

### Scenario weights — retain unless later evidence-based tuning is needed
- **Eligibility / Coverage:** DEN01 25%, DEN02 35%, DEN03 40%
- **Authorization / Precertification:** DEN05 45%, DEN06 20%, DEN07 15%, DEN08 20%
- **Coding / Modifier:** DEN09 50%, DEN10 25%, DEN11 25%
- **Missing Information / Documentation:** DEN12 30%, DEN13 35%, DEN14 20%, DEN15 15%
- **Medical Necessity:** DEN16 70%, DEN17 30%
- **COB / Wrong Payer:** DEN18 65%, DEN19 35%
- **Duplicate Claim:** DEN20 100%
- **Timely Filing:** DEN22 100%
- **Bundling / Non-Separately Payable:** DEN23 100%
- **Non-Covered Service:** DEN25 60%, DEN26 40%
- **Payer / Processing Issue:** DEN04 35%, DEN21 30%, DEN24 35%

## 11. Recovery assumptions — UNCHANGED
| Scenario | Recovery probability | Typical days |
|---|---:|---:|
| DEN01 | 55% | 30 |
| DEN02 | 45% | 35 |
| DEN03 | 90% | 18 |
| DEN04 | 90% | 28 |
| DEN05 | 55% | 35 |
| DEN06 | 65% | 28 |
| DEN07 | 45% | 40 |
| DEN08 | 85% | 20 |
| DEN09 | 93% | 14 |
| DEN10 | 85% | 18 |
| DEN11 | 75% | 24 |
| DEN12 | 90% | 18 |
| DEN13 | 92% | 16 |
| DEN14 | 88% | 18 |
| DEN15 | 82% | 25 |
| DEN16 | 55% | 42 |
| DEN17 | 45% | 45 |
| DEN18 | 80% | 35 |
| DEN19 | 88% | 30 |
| DEN20 | 0% | 7 |
| DEN21 | 90% | 22 |
| DEN22 | 20% | 60 |
| DEN23 | 0% | 10 |
| DEN24 | 65% | 35 |
| DEN25 | 35% | 40 |
| DEN26 | 10% | 20 |

Hard rules: Recovered <= Denied; open/unresolved = $0; DEN20 and DEN23 = $0 recovery; repeat events cannot inflate unique revenue at risk.

## 12. Bundling — REVISED
- Bundling denials generally target eligible secondary lines, not primary anesthesia CPT
- If 64415/64447/64450 denied for bundling and 76942 present, 76942 has moderate-to-high probability of also denying
- Do not automatically deny 76942 every time
- DEN24 must target a secondary service that is otherwise separately payable

## 13. Snapshot and chronology — REVISED
- If Initial Adjudication Date > Report Date, expose it as null and keep claim Pending
- Pending claims: Initial Paid=0, Initial Denied=0, Denial Event Count=0, Has Denial=No
- No Denial/Follow-Up/Appeal/Resolution date after Report Date may be visible
- Do not move future activity earlier to fit snapshot
- Resolution Date >= Denial Date
- Resolution Date >= Follow-Up Date if populated
- Resolution Date >= Appeal Date when appealed
- Cross-event chronology must be valid at claim level
- A subsequent denial must follow the corrective/resubmission action that could produce a new adjudication

## 14. Seasonality — REVISED
- Mild operational seasonality
- December elective/surgery-center dip must actually appear
- No direct seasonal denial-rate multiplier

## 15. QA constraints
### Structural
- Claims=3000
- Claim IDs unique
- Denial Event IDs unique
- 01991/01992 standalone
- 76942 only with eligible block CPTs
- correct/final MD modifier AA; CRNA QZ

### Financial
- Billed >= Allowed
- Denied <= Expected Allowed
- Recovered <= Denied
- Open/Unresolved recovered=0
- DEN20 and DEN23 recovered=0
- Unique Revenue at Risk de-duplicated

### Snapshot
- No visible future Initial Adjudication, Denial, Follow-Up, Appeal, or Resolution dates

### Denial Evidence
- Every preventable denial has auditable underlying evidence
- Every payer-error denial has an otherwise valid claim plus modeled payer-error evidence

### Distributions
- Initial denial rate generally 9-12% but not forced
- No implausibly dominant denial category
- Provider/location rates plausible without direct multipliers
- Payer variation emerges from archetype/workflow exposure

## 16. Rules that passed and should be preserved
- Facility volume distribution
- Procedure mix by facility/setting
- Anesthesia duration bounds
- Provider/facility affiliations
- Core claim-line structure
- Billed/allowed financial relationships
- Recovery constraints
- Provider denial-rate plausibility
- Location denial-rate plausibility
- Payer denial-rate plausibility
- Core denial-category distribution

## 17. Post-regeneration validation
Run a **targeted re-validation**, not the entire original 18-step sanity check.
1. Workers Compensation reimbursement
2. Medi-Cal calculations
3. snapshot/date censoring
4. authorization evidence
5. submission history/duplicate logic
6. bundling + 76942
7. primary and secondary modifiers
8. eligibility evidence
9. coding/POS evidence
10. units defects
11. diagnosis/documentation support
12. medical necessity
13. COB support
14. repeat-denial chronology
15. recovery amounts
16. overall initial denial rate
17. financial reconciliation

The corrected generator should generally remain within the intended 9–12% initial denial-rate range, but the result must emerge from the rules rather than be forced.

### 2. Claim_Lines — LOCKED

**Grain:** one row per CPT/service line.

#### Locked schema

1. Claim Line ID  
2. Claim ID  
3. Line Number  
4. Service Date  
5. Provider Code  
6. Provider Name  
7. Location Code  
8. Location Name  
9. Payer Code  
10. Payer Name  
11. Payer Archetype  
12. Procedure Group  
13. Line Type  
14. Submitted CPT  
15. Correct CPT  
16. Submitted Modifier  
17. Correct Modifier  
18. Submitted Setting  
19. Correct Setting  
20. Anesthesia Minutes  
21. Submitted Base Units  
22. Correct Base Units  
23. Submitted Time Units  
24. Correct Time Units  
25. Submitted Total Units  
26. Correct Total Units  
27. Coding Defect Type  
28. Bundling Eligible  
29. Bundling Relationship ID  
30. Gross Billed Amount  
31. Expected Allowed Amount  
32. Initial Paid Amount  
33. Initial Denied Amount  
34. Unique Line Revenue at Risk  
35. Final Paid Amount  
36. Final Line Status  

#### Coding and unit rules

- `Submitted CPT` is the CPT actually transmitted to the payer.
- `Correct CPT` is the CPT that should have been submitted.
- `Submitted Modifier` is the modifier actually transmitted.
- `Correct Modifier` is the correct expected modifier.
- `Submitted Setting` is the submitted setting/POS.
- `Correct Setting` is the correct modeled setting/POS.
- Submitted and correct base, time, and total units are stored separately so unit-related denials are auditable.
- `Coding Defect Type` uses: None / Wrong CPT / Missing Modifier / Wrong Modifier / Wrong Base Units / Wrong Time Units / POS Mismatch.

#### Correct modifier rules

- Primary MD anesthesia line → `AA`
- Primary CRNA anesthesia line → `QZ`
- `76942` → `26`
- `64415`, `64447`, `64450`, `64483` → `XU`

A coding-denial scenario may intentionally make the submitted value differ from the correct value, but the erroneous submitted value must remain visible in the data.

#### Line structure

- One primary anesthesia line per claim.
- Eligible claims may contain one injection/block line plus optional 76942.
- 01991 and 01992 remain standalone anesthesia codes.
- 76942 may only be generated with 64415, 64447, or 64450.
- 62321 remains reference-only with zero generation probability under the current service universe.
- Secondary-line modifiers must be populated.

#### POS and denial support

- DEN09 requires an actual submitted-modifier defect.
- DEN10 requires an actual submitted CPT/setting mismatch against explicit modeled correct logic.
- DEN13 requires an actual submitted-unit defect.
- Do not assign these denial labels unless the supporting defect exists in the line data.

#### Bundling support

- `Bundling Eligible` identifies whether a line can participate in modeled bundling logic.
- `Bundling Relationship ID` links related services such as primary anesthesia + block + 76942.
- Bundling denials should generally hit eligible secondary lines rather than the primary anesthesia CPT.
- If 64415, 64447, or 64450 is denied for bundling and 76942 is present, 76942 may also deny in the same adjudication event with a defined moderate-to-high probability.
- 76942 must not automatically deny every time.
- DEN24 payer-processing bundling errors must target an otherwise separately payable secondary line.

#### Financial rules

- Gross Billed Amount >= Expected Allowed Amount.
- Initial Denied Amount <= Expected Allowed Amount.
- `Unique Line Revenue at Risk` must not be duplicated across repeat denial events.
- Final Paid Amount must reconcile to Final Line Status.

The generic `Modifier` and ambiguous `Anesthesia Units` fields are not used in the final Claim_Lines schema because submitted and correct values are stored separately.


### 3. Denial_Events — LOCKED

**Grain:** one row per denial event.

#### Locked schema

1. Denial Event ID  
2. Claim ID  
3. Claim Line ID  
4. Sequence  
5. Prior Denial Event ID  
6. Trigger Submission ID  
7. Denial Date  
8. Group Code  
9. CARC  
10. RARC  
11. Business Denial Category  
12. Scenario ID  
13. Root Cause  
14. Root Cause Owner  
15. Preventable  
16. Evidence Type  
17. Evidence Record ID  
18. Defect Field  
19. Submitted Value  
20. Expected Value  
21. Denied Amount  
22. Revenue Opportunity  
23. Recoverable Revenue at Risk  
24. Unique Revenue at Risk Flag  
25. Resolution Method  
26. Follow-Up Date  
27. Appeal Submitted  
28. Appeal Date  
29. Appeal Outcome  
30. Resolution Submission ID  
31. Resolution Date  
32. Recovered Amount  
33. Final Denial Status  
34. Days to Resolution  

#### Evidence linkage

- Every denial identifies an `Evidence Type`.
- `Evidence Record ID` links to the supporting record when applicable.
- `Defect Field`, `Submitted Value`, and `Expected Value` preserve the underlying defect in auditable form.
- `Trigger Submission ID` identifies the submission that produced the denial.
- `Resolution Submission ID` identifies the corrective/resubmitted claim that resolved or advanced the denial when applicable.

#### Chronology rules

- Denial Date <= Report Date.
- Follow-Up Date >= Denial Date when populated.
- Appeal Date >= Follow-Up Date when applicable.
- Resolution Date >= all relevant prior activity dates.
- No future denial activity may be exposed beyond the Report Date.
- Sequence 2 and Sequence 3 must follow the corrective/resubmission activity from the preceding event.
- `Prior Denial Event ID` is blank for Sequence 1 and points to the immediately preceding denial for later sequences.

#### Dollar logic

- Recovered Amount <= Denied Amount.
- Only newly exposed dollars contribute to unique revenue-at-risk totals.
- Repeat denial events may retain their operational denied amount, but `Unique Revenue at Risk Flag = No` unless the event introduces newly at-risk dollars.

#### Controlled Final Denial Status values

- Open / Unresolved
- Resolved - Recovered
- Resolved - Not Recovered
- Corrected / Subsequent Denial
- Closed - No Revenue Opportunity

`Date Sequence Check` and `Recovered vs Denied` remain QA-only fields and are not included in the production CSV.


### 4. Claim_Submissions — LOCKED

**Grain:** one row per claim transmission to a payer.

#### Locked schema

1. Submission ID  
2. Claim ID  
3. Submission Number  
4. Submission Date  
5. Submission Type  
6. Submission Reason  
7. Trigger Denial Event ID  
8. Resulting Denial Event ID  
9. Submission Outcome  
10. Payer Code  
11. Payer Name  
12. Claim Frequency Type  
13. Was Duplicate Submission  
14. Duplicate Of Submission ID  
15. Corrected Fields  
16. Days Since Prior Submission  
17. Report Date  

#### Controlled Submission Type values

- Original
- Corrected
- Resubmission
- Appeal-Related

#### Chronology rules

- Submission 1 is the earliest submission and uses `Original`.
- Submission numbers increase sequentially by Claim ID.
- Each later Submission Date must occur after the prior submission date.
- `Trigger Denial Event ID`, if present, must reference a denial that occurred before the submission.
- `Resulting Denial Event ID`, if present, must reference a denial that occurred after the submission.
- No Submission Date may occur after the Report Date in the point-in-time snapshot.
- A second or later submission requires a modeled reason.
- `Days Since Prior Submission` is derived from submission chronology.

#### Duplicate logic

**DEN20 — true duplicate**

- Requires a prior legitimate submission.
- The later transmission has `Was Duplicate Submission = Yes`.
- `Duplicate Of Submission ID` points to the prior submission.
- That later transmission may produce DEN20.

**DEN21 — payer incorrectly classified duplicate**

- `Was Duplicate Submission = No`.
- Submission history does not support a true duplicate.
- The payer may nevertheless return the duplicate denial as an external processing error.

#### Corrected-claim logic

- Corrected/resubmitted claims may reference the denial event that triggered the new transmission.
- `Corrected Fields` stores a coded delimiter-separated list such as `Modifier|Diagnosis`.
- Supported corrected-field values may include Modifier, Base Units, Diagnosis, Referring Provider, Authorization Number, Payer, or Documentation.
- A corrected submission may resolve the prior denial or produce a subsequent denial event.

#### Claim frequency type

Keep Original / Replacement / Void available where modeled, but do not expand this project into a full EDI transaction implementation.



### 5. Authorizations — LOCKED

**Grain:** one row per authorization record tied to a claim or planned service.

#### Locked schema

1. Authorization ID  
2. Claim ID  
3. Payer Code  
4. Payer Name  
5. Authorization Required  
6. Authorization Obtained  
7. Authorization Number  
8. Authorization Start Date  
9. Authorization End Date  
10. Authorized Provider Code  
11. Authorized Location Code  
12. Authorized CPT  
13. Submitted CPT  
14. Authorization Match Status  
15. Mismatch Type  
16. Authorization Status  
17. Retro Authorization Requested  
18. Retro Authorization Outcome  
19. Report Date  

#### Controlled values

- **Authorization Match Status:** Match / No Match / Missing
- **Mismatch Type:** CPT / Provider / Location / DOS / Missing Authorization / None
- **Authorization Status:** Valid / Expired / Missing / Mismatched / Not Required
- **Retro Authorization Outcome:** Approved / Denied / Pending / N/A

#### Denial support rules

- **DEN05:** Authorization Required = Yes and Authorization Obtained = No.
- **DEN06:** authorization exists and Authorized CPT != Submitted CPT. This replaces the original authorized-units/services-exceeded scenario.
- **DEN07:** authorization exists and Service Date falls outside the authorization start/end dates.
- **DEN08:** authorization exists but provider, location, CPT, DOS, or another modeled authorization attribute conflicts with the submitted claim.

#### Design rules

- Routine anesthesia-time authorization-unit limits are not modeled as a default denial scenario.
- Authorization denials must be backed by actual authorization data.
- Retro authorization fields support realistic recovery behavior.
- Authorization activity after the Report Date must not appear in the point-in-time snapshot.



### 6. Coverage_COB — LOCKED

**Grain:** one row per claim-level coverage/COB record.

#### Locked schema

1. Coverage COB ID  
2. Claim ID  
3. Service Date  
4. Billed Payer Code  
5. Billed Payer Name  
6. Primary Payer Code  
7. Primary Payer Name  
8. Secondary Payer Code  
9. Secondary Payer Name  
10. Expected Responsible Payer Code  
11. Expected Responsible Payer Name  
12. Other Active Coverage  
13. COB Sequence  
14. Coverage Effective Date  
15. Coverage Termination Date  
16. Eligibility Check Date  
17. Eligibility Check Result  
18. Member Information Match  
19. Eligibility Defect Type  
20. Payer Eligibility File Error  
21. Report Date  

#### Controlled values

**Eligibility Check Result**
- Active
- Inactive
- Not Found
- Mismatch
- Payer Error

**Eligibility Defect Type**
- None
- Coverage Not Yet Effective
- Coverage Terminated
- Member ID Mismatch
- Demographic Mismatch
- Other Insurance Primary
- Wrong Payer
- Payer Eligibility File Error

**COB Sequence**
- Primary
- Secondary
- Tertiary

#### Denial support rules

- **DEN01:** Coverage Effective Date > Service Date.
- **DEN02:** Coverage Termination Date < Service Date.
- **DEN03:** Member Information Match = No, supported by member ID or demographic mismatch.
- **DEN04:** claim otherwise valid and Payer Eligibility File Error = Yes.
- **DEN18:** Other Active Coverage = Yes and the billed payer is not the actual primary payer.
- **DEN19:** Billed Payer Code != Expected Responsible Payer Code.

#### Design rules

- `Claims.csv` continues to show the payer actually billed.
- `Coverage_COB.csv` stores the actual and expected payer order required to audit eligibility and COB denials.
- Eligibility Check Date may not be after the Report Date.
- Do not expose future eligibility/COB discoveries in the point-in-time snapshot.
- Later payer corrections must be represented through `Claim_Submissions.csv` rather than retroactively rewriting the original claim.



## Locked schema architecture

Project 2 uses **six production tables**:

1. `Claims.csv`
2. `Claim_Lines.csv`
3. `Denial_Events.csv`
4. `Claim_Submissions.csv`
5. `Authorizations.csv`
6. `Coverage_COB.csv`

This six-table architecture is **LOCKED**.

### Documentation and medical necessity

Do **not** create a separate Documentation or Medical Necessity table for Project 2.

The following supporting fields remain in `Claims.csv`:

- Primary Diagnosis Code
- Diagnosis Category
- Documentation Required
- Documentation Status
- Referring Provider Required
- Referring Provider ID
- Referring Provider ID Valid
- Medical Necessity Review Required
- Prior Similar Service Count

These fields provide the supporting evidence needed for:

- DEN11 — Diagnosis inconsistent with procedure
- DEN12 — Missing/incomplete/invalid diagnosis
- DEN14 — Referring provider identifier missing/invalid
- DEN15 — Records required but not submitted
- DEN16 — Service not medically necessary
- DEN17 — Frequency/number of services not supported

A separate supporting table would only be warranted if the project later expands to multiple document requests/submissions, multiple diagnosis relationships, repeated utilization reviews, or other many-to-one clinical-documentation history. That is intentionally out of scope for the current portfolio project.



## Revised denial logic — DEN01 through DEN08 — LOCKED

### Eligibility / Coverage

- **DEN01 — Coverage effective after date of service**
  - Category: Eligibility / Coverage
  - CARC: 26
  - Evidence: `Coverage Effective Date > Service Date`
  - Owner: Patient Access / Eligibility
  - Preventable: Yes

- **DEN02 — Coverage terminated before date of service**
  - Category: Eligibility / Coverage
  - CARC: 27
  - Evidence: `Coverage Termination Date < Service Date`
  - Owner: Patient Access / Eligibility
  - Preventable: Yes

- **DEN03 — Incorrect or mismatched member information**
  - Category: Eligibility / Coverage
  - CARC: 31
  - Evidence: `Member Information Match = No` plus Member ID or demographic mismatch
  - Owner: Patient Access / Eligibility
  - Preventable: Yes

- **DEN04 — Payer eligibility file incorrect or delayed**
  - Category: Payer / Processing Issue
  - CARC: 31
  - Evidence: claim/member data otherwise valid and `Payer Eligibility File Error = Yes`
  - Owner: Payer
  - Preventable: No

### Authorization / Precertification

- **DEN05 — Required authorization was never obtained**
  - CARC: 197
  - Evidence: `Authorization Required = Yes` and `Authorization Obtained = No`
  - Owner: Authorization
  - Preventable: Yes

- **DEN06 — Authorized CPT/service mismatch**
  - Replaces the prior “authorized units/services exceeded” scenario.
  - Evidence: authorization exists and `Authorized CPT != Submitted CPT`
  - Owner: Authorization
  - Preventable: Yes

- **DEN07 — Authorization outside valid timeframe**
  - CARC: 210
  - Evidence: Service Date falls before Authorization Start Date or after Authorization End Date
  - Owner: Authorization
  - Preventable: Yes

- **DEN08 — Authorized provider/location mismatch**
  - CARC: 16
  - RARC: N54
  - Evidence: Authorized Provider Code or Authorized Location Code does not match the submitted claim
  - Owner: Authorization
  - Preventable: Yes
  - CPT mismatch is handled by DEN06 to avoid scenario overlap.



## Revised denial logic — DEN09 through DEN11 — LOCKED

### Coding / Modifier

- **DEN09 — Incorrect or missing anesthesia modifier**
  - CARC: 4
  - Evidence: `Submitted Modifier` is blank or differs from `Correct Modifier`
  - Owner: Coding / Billing
  - Preventable: Yes
  - Examples include MD submitted with QZ instead of AA, CRNA submitted with AA instead of QZ, 76942 without modifier 26, or modeled block/injection CPTs without XU.

- **DEN10 — Procedure / place-of-service mismatch**
  - CARC: 5
  - Evidence: `Submitted Setting != Correct Setting` or the submitted CPT/setting combination violates an explicit compatibility rule
  - Owner: Coding / Billing
  - Preventable: Yes
  - The underlying clinical service may still be valid; the defect is in what was submitted.

- **DEN11 — Diagnosis inconsistent with procedure**
  - CARC: 11
  - Evidence: diagnosis data is present and fails a defined modeled diagnosis-to-procedure compatibility rule
  - Owner: Coding
  - Preventable: Yes
  - Use a limited synthetic compatibility ruleset sufficient to support the denial; do not build a full medical-policy engine.

### Coding denial generation rule

The generator must:

`Create actual coding defect -> identify the supported denial scenario -> generate denial`

It must not:

`Choose generic coding denial -> attach random scenario`



## Revised denial logic — DEN12 through DEN15 — LOCKED

### Missing Information / Documentation

- **DEN12 — Missing, incomplete, or invalid diagnosis**
  - CARC: 16
  - RARC: M76
  - Evidence: `Primary Diagnosis Code` is blank, invalid, or fails a defined basic format/allowed-value rule
  - Owner: Coding / Billing
  - Preventable: Yes
  - Distinction: DEN11 means the diagnosis exists but is inconsistent with the procedure; DEN12 means the diagnosis itself is missing, incomplete, or invalid.

- **DEN13 — Missing or invalid units**
  - CARC: 16
  - RARC: M53
  - Evidence: submitted units are blank/invalid, or submitted base/time/total units differ from the correct values
  - Owner: Coding / Billing
  - Preventable: Yes

- **DEN14 — Referring provider identifier missing or invalid**
  - CARC: 16
  - RARC: N286
  - Evidence: `Referring Provider Required = Yes` and the ID is blank or invalid
  - Owner: Billing / Claims
  - Preventable: Yes
  - If a referring provider is not required, DEN14 cannot be generated.

- **DEN15 — Records required but not submitted**
  - CARC: 252
  - RARC: M127
  - Evidence: `Documentation Required = Yes` and `Documentation Status` is Missing or Not Submitted
  - Owner: Documentation / Billing
  - Preventable: Context-dependent
  - Controlled Documentation Status values: Not Required / Complete / Incomplete / Missing / Submitted / Pending

### Missing-information generation rule

Create the actual missing/invalid data or documentation defect first, then generate the denial scenario supported by that defect.



## Revised denial logic — DEN16 through DEN17 — LOCKED

### Medical Necessity

- **DEN16 — Service not medically necessary**
  - CARC: 50
  - Evidence: `Medical Necessity Review Required = Yes` and the diagnosis/procedure context fails a defined modeled medical-necessity rule, with no documentation override supporting the service
  - Owner: Clinical Documentation / Coding
  - Preventable: Context-dependent
  - Use a limited, documented synthetic ruleset. Do not attempt to reproduce full payer LCD/NCD policy logic.

- **DEN17 — Frequency / number of services not supported**
  - CARC: 151
  - Evidence: `Medical Necessity Review Required = Yes` and `Prior Similar Service Count` exceeds a defined modeled threshold for the relevant service/lookback window
  - Owner: Clinical Documentation / Utilization Review
  - Preventable: Context-dependent
  - Use a limited, documented synthetic frequency ruleset.

### Medical-necessity generation rule

Create the underlying medical-necessity or frequency condition first, then generate the supported denial scenario.

Do not assign a medical-necessity denial solely because a CPT belongs to a sensitive service family.



## Revised denial logic — DEN18 through DEN19 — LOCKED

### COB / Wrong Payer

- **DEN18 — Other insurance primary**
  - CARC: 22
  - Evidence: `Other Active Coverage = Yes` and `Billed Payer Code != Primary Payer Code`
  - Owner: Patient Access / Eligibility / COB
  - Preventable: Yes
  - Use when the defect is specifically coordination-of-benefits / payer-order sequencing.

- **DEN19 — Claim submitted to wrong payer**
  - CARC: 109
  - Evidence: `Billed Payer Code != Expected Responsible Payer Code`
  - Owner: Billing / Claims
  - Preventable: Yes
  - Use only when the error is wrong-payer routing outside of COB sequencing.

### COB / wrong-payer overlap rule

DEN18 and DEN19 must not be assigned to the same underlying payer-routing defect.

- Use **DEN18** when another insurer is actually primary under COB rules.
- Use **DEN19** when the claim was routed to the wrong payer and COB sequencing is not the cause.

Create the actual payer-responsibility or payer-sequence mismatch first, then generate the supported denial. Do not generate either scenario without supporting `Coverage_COB.csv` data.



## Revised denial logic — DEN20 through DEN21 — LOCKED

### Duplicate Claim vs Payer Duplicate Error

- **DEN20 — Unnecessary duplicate resubmission**
  - CARC: 18
  - Category: Duplicate Claim
  - Evidence: `Claim_Submissions.csv` shows a prior valid submission plus a later unnecessary duplicate submission; `Was Duplicate Submission = Yes`; `Duplicate Of Submission ID` points to the earlier submission
  - Owner: Billing / Claims
  - Preventable: Yes
  - Recovery: $0

- **DEN21 — Payer incorrectly classified claim as duplicate**
  - CARC: 18
  - Category: Payer / Processing Issue
  - Evidence: `Was Duplicate Submission = No` and submission history demonstrates there was no true duplicate, yet the payer returns a duplicate denial
  - Owner: Payer
  - Preventable: No

### Duplicate-denial generation rule

DEN20 and DEN21 are mutually exclusive for the same denial event.

- **DEN20:** create an unnecessary duplicate submission first, then generate the duplicate denial.
- **DEN21:** create legitimate submission history first, then inject a payer-processing duplicate error.

No duplicate denial may be generated without supporting `Claim_Submissions.csv` evidence.



## Revised denial logic — DEN22 through DEN24 — LOCKED

### Timely Filing

- **DEN22 — Filing limit exceeded**
  - CARC: 29
  - Evidence: `Submit Date - Service Date > Modeled Filing Limit Days`
  - Owner: Billing / Claims
  - Preventable: Yes
  - The filing limit must come from the payer profile already assigned to the claim.
  - Do not generate DEN22 unless the actual filing-limit violation exists.

### Bundling

- **DEN23 — Correctly included in another allowance**
  - CARC: 97
  - Category: Bundling / Non-Separately Payable
  - Evidence: an eligible secondary service is present and modeled as correctly bundled
  - Owner: Contractual Payment Logic
  - Preventable: No
  - Recovery: $0
  - The primary anesthesia CPT should generally not be the bundled denied line.

- **DEN24 — Payer incorrectly bundled separately payable service**
  - CARC: 97
  - Category: Payer / Processing Issue
  - Evidence: an eligible secondary service is present and modeled as separately payable, but the payer incorrectly bundles it
  - Owner: Payer
  - Preventable: No

### 76942 companion-bundling rule

When `64415`, `64447`, or `64450` is denied for bundling and `76942` is present:

- 76942 may also deny in the same adjudication event;
- use a defined moderate-to-high probability;
- do not automatically deny 76942 every time the related block is denied.

`Bundling Eligible`, `Bundling Relationship ID`, and line-level payment logic are the source of truth for these scenarios.



## Revised denial logic — DEN25 through DEN26 — LOCKED

### Non-Covered Service

- **DEN25 — Service/category broadly non-covered under modeled benefit**
  - CARC: 96
  - RARC: N130
  - Evidence: the modeled payer/benefit rule excludes the billed service or service category, while coding, authorization, eligibility, and COB logic otherwise pass
  - Owner: Coverage / Benefit Design
  - Preventable: Usually No
  - Recovery: limited; only when a modeled exception, correction, or benefit clarification applies

- **DEN26 — Service not covered under the patient's current modeled benefit configuration**
  - CARC: 204
  - Evidence: the claim/member-specific modeled benefit configuration excludes the service, and no coding, authorization, eligibility, or COB defect better explains the denial
  - Owner: Coverage / Benefit Design
  - Preventable: Usually No
  - Recovery: very low; only when a modeled exception, correction, or benefit clarification applies

### Non-covered overlap and sequencing rule

DEN25 and DEN26 are mutually exclusive for the same underlying coverage defect.

- **DEN25** = broad/general modeled benefit exclusion.
- **DEN26** = claim/member-specific current-benefit exclusion.

Non-covered-service scenarios may only be generated after coding, authorization, eligibility, and COB logic have passed. Do not use non-covered service as a catch-all denial category.



## California Workers’ Compensation reimbursement — LOCKED

Formula:

`Expected Allowed Amount = (CMS Base Units + WC Time Units) × DWC Conversion Factor`

### WC time units

`WC Time Units = ROUND(Anesthesia Minutes / 15, 1)`

Examples:

- 30 minutes → 2.0 units
- 38 minutes → 2.5 units
- 44 minutes → 2.9 units
- 46 minutes → 3.1 units

Do **not** use the Medi-Cal remainder ≥5-minute whole-unit methodology for Workers’ Compensation.

### Official DWC conversion factors

| Period | Area 18 LA/Orange | Area 17 Ventura | Area 62 Riverside/San Bernardino |
|---|---:|---:|---:|
| 2025 | $31.27 | $30.77 | $30.51 |
| 2026 | $32.09 | $31.68 | $31.52 |

### Effective-date rule

- DOS 2025-09-01 through 2026-02-28 → 2025 Table A
- DOS 2026-03-01 through 2026-08-31 → 2026 Table A

### County/locality mapping

- Los Angeles → Area 18
- Orange → Area 18
- Ventura → Area 17
- Riverside → Area 62
- San Bernardino → Area 62

### Hard rules

- Use correct/canonical CMS base units for the expected reimbursement benchmark.
- Erroneous submitted units may generate a denial but do not redefine the correct allowance.
- Round final expected allowed amount to cents.
- `Expected Allowed Amount <= Gross Billed Amount`.
- After regeneration, recalculate all affected WC financial fields:
  - Expected Allowed Amount
  - Initial Paid Amount
  - Initial Denied Amount
  - Final Paid Amount
  - Final Balance
  - recovery-related amounts



## Commercial / managed care reimbursement — LOCKED

Commercial and managed-care reimbursement remains **synthetic** and payer-specific.

### Locked reimbursement profiles

| Payer archetype | Synthetic reimbursement method |
|---|---|
| Commercial PPO / POS / OAP | Anesthesia CF approximately **$58–$72** |
| HMO / EPO | Anesthesia CF approximately **$48–$62** |
| Exchange | Anesthesia CF approximately **$46–$58** |
| Medicare Advantage | **105–120% of Medicare FFS** |
| Medi-Cal Managed | **105–125% of Medi-Cal FFS** |
| Network / Other Commercial | Anesthesia CF approximately **$45–$58** |
| Out-of-Area Medicaid | **90–110% of Medi-Cal FFS** |

### Assignment rule

Each payer receives **one fixed seeded synthetic contract profile**.

The rate or multiplier does **not** change randomly from claim to claim.

For a given payer and reimbursement basis, all claims use that same synthetic contract profile unless a future project version explicitly models a contract-period change.

### Calculation rules

- Commercial CF-based plans use the same anesthesia-unit framework as the modeled contract profile.
- Medicare Advantage is calculated from the corresponding Medicare FFS benchmark.
- Medi-Cal Managed and Out-of-Area Medicaid are calculated from the corresponding Medi-Cal FFS benchmark.
- Use correct/canonical units for the reimbursement benchmark.
- `Expected Allowed Amount <= Gross Billed Amount`.
- Round final expected allowed amount to cents.

### Denial-risk separation

Synthetic reimbursement generosity must **not** directly create an arbitrary payer denial penalty.

Payer denial-rate differences must emerge from the previously locked administrative-profile and workflow-exposure rules, not from the contract rate itself.

### Documentation requirement

These reimbursement profiles are **synthetic portfolio assumptions** and must not be described as actual payer contract terms.



## Snapshot and date sequencing rules — LOCKED

**Report Date:** 2026-09-15

### Snapshot rules

No future operational activity may appear in the point-in-time snapshot.

- Service Date <= 2026-08-31
- Submit Date <= Report Date
- Initial Adjudication Date <= Report Date if populated
- Denial Date <= Report Date
- Follow-Up Date <= Report Date if populated
- Appeal Date <= Report Date if populated
- Resolution Date <= Report Date if populated
- `Claim_Submissions.csv` Submission Date <= Report Date
- Eligibility and authorization activity after Report Date must not appear

Future activity must **not** be moved earlier simply to fit the snapshot. It must remain blank/not yet present.

### Pending claims

If the true adjudication would occur after the Report Date:

- `Initial Claim Status = Pending`
- `Initial Adjudication Date = blank`
- `Initial Paid Amount = 0`
- `Initial Denied Amount = 0`
- `Denial Event Count = 0`
- `Has Denial = No`

### Within-event chronology

For each denial event:

- Follow-Up Date >= Denial Date when populated
- Appeal Date >= Denial Date
- Appeal Date >= Follow-Up Date when applicable
- Resolution Date >= the latest applicable prior action
- `Days to Resolution = Resolution Date - Denial Date`
- no negative or impossible chronology

### Repeat-denial chronology

For Sequence 2 or 3:

- later denial must occur after the prior corrective/resubmission action capable of producing a new adjudication;
- a later denial may not appear while the prior event is unresolved unless `Claim_Submissions.csv` proves a legitimate new adjudication path;
- `Prior Denial Event ID` must point to the immediately preceding event;
- `Trigger Submission ID` must identify the submission that produced the new denial.

Clean sequence:

`Denial 1 -> correction/resubmission -> Denial 2 -> correction/resubmission -> Denial 3`

### Resolution / submission linkage

If a denial is resolved through a corrected claim:

- `Resolution Submission ID` must exist;
- its Submission Date must occur after the denial;
- Resolution Date must be on/after that submission.

For appeals:

- Appeal Outcome cannot exist before Appeal Date;
- recovered dollars resulting from the appeal cannot be recognized before resolution.

### Hard QA failures

Generation fails if any of the following occur:

- visible future activity after Report Date
- Resolution Date before Denial Date
- Appeal Date before Denial Date or required follow-up
- Sequence 2/3 before the action that should have produced it
- submission chronology out of order
- denial linked to a submission occurring after the denial date
- pending claim with a visible future adjudication outcome



## Recovery and repeat-denial financial rules — LOCKED

### Recovery amount rules

- `Recovered Amount <= Denied Amount`
- `Recovered Amount <= remaining recoverable allowed amount`
- Open / Unresolved denial events → `Recovered Amount = 0`
- DEN20 true duplicate → `Recovered Amount = 0`
- DEN23 correctly bundled / non-separately payable → `Recovered Amount = 0`
- Recovery cannot be recognized before Resolution Date
- Recovery follows the scenario-specific recovery probability and typical-days logic already defined

### Unique revenue at risk

Repeat denials must not inflate exposure.

If the same dollars are denied multiple times:

- the first event placing those dollars at risk gets `Unique Revenue at Risk Flag = Yes`
- later repeat denials against the same dollars get `Unique Revenue at Risk Flag = No`
- if a later denial introduces additional newly-denied dollars, only the incremental new amount counts as new unique risk

Hard constraint:

`Claim-level Unique Revenue at Risk <= total recoverable allowed amount`

### Repeat-denial financial sequencing

- Event 1 may deny the full or partial expected allowed amount
- after correction/resubmission, later events may deny the same remaining amount again
- later events do not create new unique risk unless they affect additional previously unexposed dollars
- recovered dollars from earlier events reduce the remaining amount available for later recovery
- `Sum of Recovered Amount across claim <= Claim-level Unique Revenue at Risk`

### Final paid amount reconciliation

- `Final Paid Amount <= Expected Allowed Amount`
- generally:
  `Final Paid Amount + Final Balance = Expected Allowed Amount`
  unless an intentional contractual/non-recoverable adjustment is modeled
- for correctly non-recoverable outcomes, denied dollars may remain unpaid
- Final Balance may be 0 if the amount is contractually written off/non-recoverable, but claim/final denial status must explain the outcome

### Recovery behavior by scenario

Preserve the existing scenario-specific recovery probabilities and typical-days logic unless explicitly revised later.

Relative behavior remains:

- coding/modifier → high recovery
- missing information → high recovery
- payer-processing error → fairly high recovery
- eligibility → moderate recovery
- authorization → moderate recovery
- medical necessity → lower recovery
- timely filing → low recovery
- non-covered → low recovery
- true duplicate → zero recovery
- correct bundling → zero recovery

### Resolution status logic

Controlled values:

- Open / Unresolved
- Resolved - Recovered
- Resolved - Not Recovered
- Corrected / Subsequent Denial
- Closed - No Revenue Opportunity

Rules:

- `Resolved - Recovered` requires `Recovered Amount > 0`
- `Resolved - Not Recovered` requires `Recovered Amount = 0`
- `Open / Unresolved` requires no Resolution Date and `Recovered Amount = 0`
- `Corrected / Subsequent Denial` requires a later valid denial sequence
- `Closed - No Revenue Opportunity` is appropriate for true duplicate, correct bundling, or other no-revenue-opportunity outcomes

### Hard QA failures

Generation fails if:

- Recovered Amount > Denied Amount
- total claim recovery > claim-level Unique Revenue at Risk
- repeat denial events inflate Unique Revenue at Risk
- open denial has recovered dollars
- DEN20 true duplicate or DEN23 correct bundling recovers money
- Final Paid Amount > Expected Allowed Amount
- financial outcome contradicts Final Denial Status



## Final QA / validation rules — LOCKED

### Structural integrity

- every Claim Line → valid Claim
- every Denial Event → valid Claim and, when applicable, valid Claim Line
- every Trigger Submission ID / Resolution Submission ID → valid submission
- every Authorization ID → valid authorization record
- every Coverage COB ID → valid coverage record
- no orphan foreign keys
- no duplicate primary keys

### Financial integrity — hard failures

Generation fails if:

- `Expected Allowed Amount > Gross Billed Amount`
- `Initial Paid Amount + Initial Denied Amount > Expected Allowed Amount`
- `Recovered Amount > Denied Amount`
- `Final Paid Amount > Expected Allowed Amount`
- total claim recovery > claim-level Unique Revenue at Risk
- repeat denials double-count Unique Revenue at Risk
- line totals fail to reconcile reasonably to claim totals

### Coding / reimbursement integrity

Verify:

- CPT exists in the defined project universe
- correct CMS base units are present
- physician primary modifier = `AA`
- CRNA primary modifier = `QZ`
- `76942 = 26`
- modeled injection modifiers = `XU`
- Medicare uses Medicare time logic
- Medi-Cal uses Medi-Cal time logic
- Workers’ Compensation uses `minutes / 15`, rounded to 1 decimal
- correct locality/year reimbursement factors are applied

Any mismatch is a hard fail.

### Denial evidence integrity

Every denial must have supporting evidence.

Examples:

- authorization denial → authorization defect record
- eligibility/COB denial → Coverage_COB evidence
- coding denial → submitted vs correct coding differs
- duplicate denial → submission history proves duplicate
- timely filing → actual filing-limit violation
- missing information → required field actually missing/invalid
- payer-processing denial → underlying claim data otherwise correct

No denial may exist solely because a random denial category was selected.

### Chronology / snapshot integrity

Apply all locked Step 4 rules:

- no visible event after 2026-09-15
- no impossible date sequence
- repeat denials follow valid resubmission/adjudication activity
- pending claims contain no future adjudication data
- resolution/recovery cannot precede the actions producing them

### Distribution guardrails — diagnostic only

Review after generation:

- initial denial rate roughly 9–12%
- repeat denials remain uncommon
- provider/location/payer denial rates show no unexplained extreme outliers
- procedure/facility mix remains consistent with design
- monthly volumes show mild variation
- December elective dip is visible but modest
- recovery rates broadly reflect scenario difficulty

If a distribution falls outside expectation, investigate the cause. Do **not** manipulate the generator merely to force it back into a preferred range.

### Targeted regression checks

Re-test every previously identified issue:

- no future adjudication dates
- no overlapping/impossible denial sequences
- corrected Workers’ Compensation reimbursement
- no unsupported authorization-unit denials
- duplicate denials have submission evidence
- 76942 bundling behavior works
- correct secondary modifiers
- eligibility/COB evidence exists
- submitted vs correct coding fields support denials
- missing-unit denials represent actual defects
- documentation/referring-ID denials have supporting fields
- payer-error bundling targets eligible secondary lines
- Unique Revenue at Risk is de-duplicated

### Final release gate

Accept the regenerated dataset only if:

1. **0 hard QA failures**
2. all six production tables reconcile
3. all known prior defects pass regression testing
4. distributions remain plausible
5. no manual manipulation was needed to create a preferred analytical finding

### Generation readiness

All previously identified rulebook items are now resolved. Controlled regeneration may proceed.



## DEN06 final code mapping — LOCKED

**Scenario:** Authorized CPT/service mismatch

- **CARC:** 198
- **RARC:** N54
- **Evidence rule:** authorization exists and `Authorized CPT != Submitted CPT`
- **Root Cause Owner:** Authorization
- **Preventable:** Yes

This replaces the prior DEN06 TBD code mapping.

DEN06 remains distinct from:

- DEN05 — missing authorization
- DEN07 — authorization outside valid dates
- DEN08 — authorized provider/location mismatch

