---
title: OSO Data Challenge 02
sidebar_position: 7
---

# Audit of RF4 Impact Metric Calculations

## Objective

Conduct a code and data audit of the 16 impact metrics implemented by Open Source Observer for Optimism Retro Funding 4.

The intended business logic of impact metrics will not change. The purpose of this audit is to identify any bugs/issues within the code. If any critical issues are found, then a fix will be pushed to the query logic before voting closes. _Changes made in this way will not impact voting ballots, as badgeholders are voting on impact metrics not individual projects._

## Context

A full write-up on the process OSO employed is available [here](https://mirror.xyz/cerv1.eth/0s05D8YqJwezhJpOn9PEx_jLihvTqtFxw0R4_6nFl5I) and in a more distilled format [here](/blog/2024-06-29-impact-metrics-rf4-deep-dive/index). All SQL models are available in interactive format [here](https://models.opensource.observer/#!/overview) and from our [GitHub](https://github.com/opensource-observer/oso/tree/main/warehouse/dbt/models).

The downstream models most relevant to this audit are available in interactive format [here](https://models.opensource.observer/#!/model/model.opensource_observer.rf4_impact_metrics_by_project) and in our GitHub [here](https://github.com/opensource-observer/oso/tree/main/warehouse/dbt/models/marts/superchain.)

## Auditor requirements

The auditor will need a strong command of SQL and blockchain concepts. Experience with dbt and working in a BigQuery environment will be helpful.

_Important: If you are interested in participating in the bounty, please join our [Discord](https://opensource.observer/discord) and provide a short introduction, including a link to your GitHub profile. We will review your profile and let you know if you are eligible to participate._

## Scope of audit

The auditor is expected to audit the following components of the impact metrics model:

1. Unified events model

   1. Audit the primary event models (eg, [Events Daily to Project](https://models.opensource.observer/#!/model/model.opensource_observer.rf4_events_daily_to_project), [4337 Events](https://models.opensource.observer/#!/model/model.opensource_observer.rf4_4337_events)), upstream source data (eg, [Base Transactions](https://models.opensource.observer/#!/model/model.opensource_observer.int_base_transactions), [Base Traces](https://models.opensource.observer/#!/model/model.opensource_observer.int_base_traces)), and the dbt macros used for intermediate processing (eg, [contract_invocation_events](https://github.com/opensource-observer/oso/blob/main/warehouse/dbt/macros/models/contract_invocation_events_with_l1.sql), [filtered_blockchain_events](https://github.com/opensource-observer/oso/blob/main/warehouse/dbt/macros/models/filtered_blockchain_events.sql)).
   2. Comment on the following aspects:

      1. Completeness and accuracy of underlying transaction and trace data for the six relevant chains
      2. Correct and consistent implementation of the RF4 transaction window (2023-10-01 to 2024-06-01)
      3. Correct and consistent implementation of the relevant RF4 onchain event types (eg, gas fees, contract interactions, etc.)
      4. Implementation of "special cases" for 4337 interactions (see [here](https://github.com/opensource-observer/oso/blob/main/warehouse/dbt/models/marts/superchain/rf4_4337_events.sql)) and EOA bridges (see [here](https://github.com/opensource-observer/oso/blob/main/warehouse/dbt/macros/models/contract_invocation_events_with_l1.sql#L5))

2. Contract discovery and attribution model

   1. Audit the contract discovery logic (eg, [Derived Contracts](https://models.opensource.observer/#!/model/model.opensource_observer.int_derived_contracts), [Contracts by Project](https://models.opensource.observer/#!/model/model.opensource_observer.int_contracts_by_project)) and upstream logic for identifying factories, deployers, and deterministic deployments
   2. Comment on the following aspects:

      1. Completeness and accuracy of the [Contract by Project](https://github.com/opensource-observer/insights/blob/main/analysis/optimism/retrofunding4/data/op_rf4_contracts_by_project.parquet) database, including efforts to de-dupe contracts deployed by creator factories such as Zora's and pool factories such as Aerodrome's
      2. Correct attribution of all contract artifacts included in approved project's applications (see [here](https://github.com/opensource-observer/insights/blob/main/analysis/optimism/retrofunding4/data/op_rf4_contracts_by_application.csv))

3. Trusted user model

   1. Audit the trusted user model logic (see [here](https://models.opensource.observer/#!/model/model.opensource_observer.rf4_trusted_users)) and upstream source data (from Farcaster and reputation data providers)
   2. Comment on the following aspects:

      1. Completeness and accuracy of underlying source data
      2. Correct implementation of the trusted user model heuristics

4. Impact metric implementation

   1. Audit the logic of the [Impact Metrics by Project](https://models.opensource.observer/#!/model/model.opensource_observer.rf4_impact_metrics_by_project) model and the 13 upstream models that power individual metrics
   2. Comment on the following aspects:

      1. Correct and consistent implementation of all 13 underlying metrics models and 3 log-transformed metrics models
      2. Correct and consistent implementation of the summary model that aggregates all 16 metrics and links them with project applications

5. Open Source labeling

   1. Audit that project labels (see [here](https://docs.google.com/spreadsheets/d/1f6zQCCR2OmaM7bsjVU22YcVP4J_JmLaEKLc-YIDjCkw/edit?gid=88938804#gid=88938804)) have been applied correctly based on the stated logic. Note that these checks are not implemented in SQL. You can replicate the API calls used for these checks [here](https://docs.google.com/document/d/187487ksRqjD2hNVtxCFwomP58gvAN0Gz_sXyO5NsJA0/edit?usp=sharing).
   2. Comment on the following aspects:

      1. Repo age checked correctly
      2. Repo license discovered correctly

## Deliverable

The deliverable is a Google or Markdown doc that includes the following:

1. Brief introduction of the auditor and their relevant experience
2. Audit methodology and the environment used to test or replicate the data
3. Audit findings, itemized by severity (critical, minor, OK):
   1. **Critical** means an issue that will almost certainly have a material effect on the metrics and should be addressed. Any critical issues should be accompanied by a CSV or a copy of the query logic needed to replicate the issue.
   2. **Minor** means an issue that is unlikely to have a material effect on the metrics but should be addressed in subsequent iterations or for peace of mind.
   3. **OK** means the auditor has reviewed but did not find any issue.
4. [OPTIONAL] Recommendations for improving models for future funding rounds.

The final deliverable should be sent by email to carl[at]karibalabs[dot]co

## Deadline

If you are interested in participating, you must let us know (via [Discord](https://opensource.observer/discord)) by 2024-07-03 23:59 UTC.

The submission deadline for audit reports is 2024-07-08 23:59 UTC.

## Amount

Up to $1000 per audit, with up to three winning submissions. Partial payment may be awarded for strong submissions that only address a subset of the five components. Auditors will be required to KYC in order to receive payment.
