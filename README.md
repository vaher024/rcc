# Prerequisites

- Python 3.7 or higher

- Required Python packages: requests, pandas, numpy, matplotlib

# Installation

1. Clone or download this repository

2. Install required packages:

```bash
    'pip install requests pandas numpy matplotlib'
```

# Task 1 assessment (Run 'python main.py' for analysis):

On 22.09.2025, the total imbalance volume was 442 MWh, while activated aFRR was only 15 MWh. The correlation between aFRR activation and absolute imbalance was slightly negative (-0.19), meaning activations did not consistently follow imbalance size.

aFRR is meant to stabilize frequency by correcting short-term imbalances, but the low ratio suggests most imbalances were handled by other reserves (mFRR, FCR) or remained as residuals. This indicates that aFRR played only a minor role in balancing on this day.

# Task 2 assessment (Run 'python main2.py' for analysis):

## 1. Total Production Capacity of Generators

The total production capacity is 1500 MW, calculated from the three synchronous machines:

- NL-G1: 1000 MW

- NL-G2: 250 MW

- NL-G3: 250 MW

## 2. Nominal Voltages of Transformer NL_TR2_2 Windings

- Winding 1 (endNumber=1): 220 kV

- Winding 2 (endNumber=2): 15.75 kV

## 3. Current Limits for NL-Line_5

- Permanently Allowed (PATL): 1876 A

- Temporarily Allowed (TATL): 500 A

Difference: PATL is the continuous thermal rating, while TATL is a short-term emergency rating (10 minutes duration in this model) allowing higher loading temporarily.

## 4. Slack Generator Identification

No generator is explicitly designated as slack in this model. While NL-G1 has voltage regulation capability, no specific "slack" role is assigned.

Why models need slack nodes: Power flow calculations require a slack/reference bus to:

- Balance active power mismatches

- Provide a phase angle reference (0°)

- Handle system losses

## 5. Identified Model Errors

Critical Errors:

- Duplicate PowerTransformerEnd IDs: Three winding ends all use the same ID _0dbed103-fc51-4df4-a6fa-0dee4c57f3a3 for NL_TR2_2

- Incomplete OperationalLimitType: TATL limit type has incorrect ID _bf2a4896-2e92-465b-b5f9-b033993a318 (truncated)

- XML Syntax Errors: Unclosed <md:FullModel> tag and incorrect <cim:IdentifiedObject.lname> element

- Missing BaseVoltage References: Several equipment references undefined base voltages (e.g., _abb2348a-aa10-446f-9f5d-49f93f211534)

Power System Issues:

- Inconsistent Transformer Configurations: Mixed phase and ratio tap changers without clear coordination

- Missing Connectivity: Several EquivalentInjections and line terminals reference undefined connectivity nodes

- Voltage Regulation Conflicts: Multiple regulating controls without defined priority

Data Quality Issues:

- Zero Impedance EquivalentInjections: Multiple equivalent injections with R=X=0, which are unrealistic

- Incomplete Load Characteristics: Most loads missing detailed response characteristics

- Inconsistent Naming: Some equipment has duplicate or unclear naming conventions
