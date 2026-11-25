Healthcare Revenue Cycle Simulation & Analytics \| Study 01: Synthetic
Anesthesia Claims & Denial Analysis \| Case Study

Study 01: Synthetic Anesthesia Claims & Denial Analysis

# Project Overview

This project analyzes a synthetic healthcare revenue cycle dataset to
identify denial trends, financial exposure, recovery performance, and
operational opportunities within a fictional anesthesia practice.

The goal was not simply to report denial counts, but to understand:

- Which denial categories create the greatest financial and operational
  burden

- How much denial exposure is preventable

- Which payer segments create the greatest risk

- How successful the organization is at recovering denied revenue

- Whether provider, facility, repeat-denial, or time-based patterns
  suggest deeper operational issues

- Where management should focus process-improvement efforts

The analysis ultimately tells the story of a generally stable revenue
cycle operation with opportunities to strengthen existing controls
rather than a practice experiencing a broad systemic failure.

# Tools Used

- Tableau

- Microsoft Excel

- Python

- CSV-based relational data model

- Healthcare revenue cycle and denial-management concepts

- CARC/RARC denial classification

- Synthetic healthcare claims data

# Dataset

The project uses a synthetic, PHI-free dataset representing anesthesia
claims with dates of service from September 2025 through August 2026.
The dataset was generated specifically for this portfolio project using
deterministic rules, a fixed random seed, modeled reimbursement logic,
and evidence-linked denial scenarios.

The dataset contains six related production tables:

- Claims.csv

- Claim_Lines.csv

- Denial_Events.csv

- Claim_Submissions.csv

- Authorizations.csv

- Coverage_COB.csv

The Tableau data model uses Claims.csv as the central table, with the
remaining tables connected through relationships using Claim ID. This
preserves each table's native grain and avoids row multiplication from
physically joining one-to-many tables.

## How the Dataset Was Generated

A substantial part of this project was the design and generation of the
dataset itself. Claims were generated hierarchically so that service
date, facility, procedure, CPT, duration, provider, payer,
reimbursement, workflow requirements, defects, submissions,
adjudication, denials, and recovery followed a coherent sequence rather
than being independently randomized.

Preventable denials were generated only when a supporting operational
defect existed in the underlying data, while payer-processing denials
required an otherwise valid claim plus an explicit modeled payer error.
Repeat denials, corrected submissions, authorizations, coverage/COB
evidence, and point-in-time snapshot rules were also modeled so that
each denial could be audited back to its supporting records.

The detailed generation methodology is documented separately in
Project_2_Dataset_Generation_README.

# Dataset Summary

| **Metric**                         | **Value**    |
|------------------------------------|--------------|
| Claims                             | 3,000        |
| Claim Lines                        | 3,263        |
| Denied Claims                      | 303          |
| Denial Events                      | 333          |
| Pending Claims                     | 133          |
| Initial Denial Rate                | 10.6%        |
| Unique Recoverable Revenue at Risk | \$120,826.76 |
| Recovered Amount                   | \$75,787.11  |
| Open Revenue at Risk               | \$30,708.43  |
| Preventable Revenue at Risk        | \$93,403.62  |

# Key Findings

## 1. Primary Denial Drivers

The largest denial categories by volume were:

- Eligibility / Coverage

- Coding / Modifier

- Missing Information / Documentation

- Authorization / Precertification

- COB / Wrong Payer

- Payer / Processing Issue

The largest categories by unique recoverable revenue at risk were:

| **Denial Category**                 | **Unique Recoverable Revenue at Risk** |
|-------------------------------------|----------------------------------------|
| Eligibility / Coverage              | \$30,580.46                            |
| Coding / Modifier                   | \$21,278.43                            |
| Missing Information / Documentation | \$16,986.76                            |
| COB / Wrong Payer                   | \$14,296.29                            |
| Non-Covered Service                 | \$13,290.80                            |
| Authorization / Precertification    | \$11,265.25                            |

The analysis shows that denial volume and financial impact should both
be considered when prioritizing improvement efforts.

## 2. Preventability

Preventable denials represented:

- 77.5% of denial events

- Approximately 77.3% of recoverable revenue at risk

A total of \$93,403.62 in recoverable revenue at risk was associated
with preventable denial causes.

The four largest preventable workflow areas were:

- Eligibility / Coverage

- Coding / Modifier

- Missing Information / Documentation

- COB / Wrong Payer

Together, the preventable portions of these four areas represented
approximately 87.5% of preventable recoverable revenue at risk.

## 3. Operational Intervention Opportunities

### Eligibility, Coverage, and COB

The organization should review its insurance-verification process for:

- Active coverage

- Payer order

- Member information

- Other active insurance

- Eligibility documentation

Any additional controls should be balanced against claim-submission
speed to avoid introducing timely-filing or cash-flow problems.

### Coding and Modifiers

Coders should independently review the coding received from facilities
and surgeon offices for accuracy rather than treating outside coding as
automatically correct. This may add some work before submission, but the
tradeoff should be evaluated against the time and cost of correcting
coding-related denials after the claim has already been submitted.

Potential improvements include:

- Independent review of facility- and surgeon-supplied coding before
  claim submission

- Focused staff education and coding refreshers based on recurring
  denial patterns

- Periodic coding audits to identify recurring errors and training needs

- Review of payer-specific coding and modifier requirements

### Documentation and Claim Completeness

The organization should identify payer- and service-specific
documentation requirements earlier in the billing process and ensure
that required information is complete before claim submission. This
includes documentation, identifiers, diagnosis information, units, and
other required claim elements.

### Authorization

Authorization denials are especially difficult in anesthesia because
anesthesia is not always expressly identified in the authorization for
the underlying procedure. Reviewing CPT/service, provider, location, and
date-range matching remains important, but the workflow also needs a
reliable way for billers to know which cases have an authorization so
potential authorization-related issues can be anticipated before
billing.

Authorization information is also not always included in the
documentation received from hospitals or surgery centers. Because the
anesthesia practice often does not control the authorization process
itself, improvement may require closer coordination with facilities and
surgeon offices so the billing team is notified when an authorization
exists or when anesthesia-specific authorization requirements may apply.
This makes authorization a preventable category in the model, but
operationally one of the more difficult areas for the anesthesia
practice to control directly.

## 4. Payer Risk

Three payer segments created the greatest combination of denial volume
and financial exposure. Exposure is not simply a function of how many
claims were denied; the modeled reimbursement per anesthesia unit also
affects how much revenue is at risk when a denial occurs.

| **Payer Segment**     | **Initially Denied Claims** | **Unique Revenue at Risk** | **Denial Rate** | **Avg. Expected Allowed per Anesthesia Unit\*** |
|-----------------------|-----------------------------|----------------------------|-----------------|-------------------------------------------------|
| Commercial PPO/POS    | 90                          | \$52,859.99                | 10.3%           | \$63.45                                         |
| HMO/EPO               | 62                          | \$31,453.02                | 11.9%           | \$55.07                                         |
| Workers' Compensation | 45                          | \$13,340.57                | 13.8%           | \$31.29                                         |

\*Weighted average for initially denied primary-anesthesia claim lines:
total Expected Allowed Amount divided by total Correct Total Units.
These are synthetic modeled rates within this dataset, not real-world
contracted payer rates.

Commercial PPO/POS has the greatest overall exposure because it combines
the largest number of initially denied claims with the highest modeled
reimbursement per anesthesia unit among these three segments. HMO/EPO
shows a similar pattern at a lower level: it has the second-highest
denied-claim count and the second-highest modeled per-unit reimbursement
of the three. Workers' Compensation has a substantially lower modeled
per-unit reimbursement, but it remains important because it has
meaningful denied-claim volume and the highest denial rate of the three
segments.

Medicare FFS produced meaningful denial volume but substantially lower
financial exposure.

## 5. Provider and Facility Patterns

No major physician-level denial problem was identified. Provider
differences were relatively small and appeared more consistent with
normal variation than with a clear provider-specific operational issue.

At the facility level, Pacific Crest Medical Center Inpatient and
Outpatient accounted for relatively large shares of both denied claims
and unique revenue at risk. However, their actual denial rates were not
unusually high compared with other facilities. This suggests that the
concentration is more likely related to business volume than evidence of
poor facility-specific denial performance.

## 6. Recovery Performance

Total unique recoverable revenue at risk was \$120,826.76. Total
recovered revenue was \$75,787.11.

Recovery performance varied considerably by denial category.

| **Denial Category**                 | **Recovery Rate** |
|-------------------------------------|-------------------|
| Payer / Processing Issue            | 83.8%             |
| Coding / Modifier                   | 78.5%             |
| Missing Information / Documentation | 77.1%             |
| Timely Filing                       | 72.5%             |
| Eligibility / Coverage              | 60.1%             |
| COB / Wrong Payer                   | 60.1%             |
| Medical Necessity                   | 34.0%             |
| Non-Covered Service                 | 20.7%             |

Bundling and true duplicate claims had no recoverable revenue
opportunity and were therefore treated as N/A rather than as ordinary 0%
recovery categories. The findings support both stronger denial
prevention and targeted recovery activity.

## 7. Remaining Financial Exposure

- \$30,708.43 remained Denied / Open

- \$18,594.07 was Resolved - Partial/No Recovery

- \$71,524.26 was Paid / Recovered

A total of \$49,302.50 remained unrecovered at the claim level. Of that
amount, the \$30,708.43 still open represents the most immediately
actionable financial opportunity.

## 8. Repeat Denials

- First denial events: 303

- Second denial events: 29

- Third denial events: 1

Approximately 9% of denial events were repeat denials. Repeat activity
was concentrated primarily in Coding / Modifier, Missing Information /
Documentation, and Payer / Processing Issue. This suggests that repeat
denials are better addressed through targeted workflow review rather
than broad organizational intervention.

## 9. Time-Based Patterns

No strong seasonal denial pattern was identified. Monthly denial rates
fluctuated within a relatively stable range, and claim volume remained
reasonably consistent throughout the year.

Recent periods, particularly August 2026, contained a large number of
pending claims and therefore require additional caution when
interpreting denial rates. Overall, the data did not support a specific
seasonal intervention strategy.

# Management Recommendations

## 1. Strengthen Eligibility, Coverage, and COB Verification

Improve front-end verification of active coverage, payer order, member
information, and other insurance. The goal should be to increase
accuracy without materially delaying claim submission.

## 2. Improve Coding and Modifier Validation

Require coders to review coding received from facilities and surgeon
offices for accuracy before claims are released, rather than relying on
external coding without internal verification. This may slow the
pre-submission process somewhat, but management should balance that cost
against the downstream time and expense of correcting avoidable coding
denials after submission.

- Independent verification of external coding inputs

- Focused coding education and refreshers

- Periodic coding audits

- Review of payer-specific modifier and coding requirements

## 3. Strengthen Documentation and Claim-Completeness Controls

Identify payer- and service-specific requirements earlier and verify
required documentation and claim information before release.

## 4. Improve Authorization Visibility and Coordination

Create a more reliable way for billers to know when an authorization
exists or may be required, and strengthen communication with facilities
and surgeon offices when authorization information is not routinely
included in the records sent to the anesthesia billing team. Because
anesthesia often does not control the authorization process, the
objective is better visibility and coordination rather than assuming the
practice can directly manage every authorization.

## 5. Prioritize Payer-Specific Monitoring

Focus monitoring on Commercial PPO/POS, HMO/EPO, and Workers'
Compensation. Track denial rate, denial category mix, revenue exposure,
and reimbursement intensity so that interventions remain targeted rather
than universal.

# Tableau Dashboard

## Executive Overview

Provides a high-level view of:

- Initial Denial Rate

- Unique Recoverable Revenue at Risk

- Recovered Amount

- Open Revenue at Risk

- Preventable Revenue at Risk

- Denial drivers by financial exposure

- Denial volume

- Preventability

## Payer & Recovery Analysis

Focuses on:

- Unique Revenue at Risk by Payer Segment

- Denial Rate by Payer Segment

- Recovery Rate by Denial Category

## Operational Analysis

Focuses on:

- Monthly Denial Rate Trend

- Unique Revenue at Risk by Facility

- Repeat Denial Volume

- Facility and provider filtering

# Project Conclusion

The analysis suggests a generally stable revenue cycle operation with a
manageable denial rate, but also clear opportunities to strengthen
existing controls.

Rather than identifying one major systemic failure, the data highlights
recurring workflow opportunities in eligibility and COB verification,
coding and modifier accuracy, documentation completeness, authorization
visibility and coordination, and payer-specific monitoring.

Because the dataset does not contain every real-world operational detail
behind each claim, the findings should be used as a starting point for
deeper process investigation rather than as proof of a specific root
cause.

**The overall opportunity is one of refinement rather than rescue:
strengthening existing processes to reduce preventable denials, improve
recovery efficiency, and reduce financial exposure.**

# Data Privacy

All data used in this project is synthetic and contains no protected
health information (PHI).
