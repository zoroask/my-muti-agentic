---
name: bot-data-quality
description: "Data Quality work on data that financial institutions submit to the Bank of Thailand (BOT): design or review validation rules, check data file quality (profiling, completeness, consistency, reconciliation across datasets or periods), and trace the cause of abnormal data. Use when the user mentions data quality check, validation rule, rule list, abnormal data, outlier, totals not matching, data jump, validation error, issue log, threshold, DQ. Not for UAT/IWT documents, Help Desk answers, Data RIA or data publication, which belong to fin-data-management."
---

# Skill: Data Quality for data BOT receives from reporters

Ported from `_external/bot-data-qulity/SKILL.md` (Thai original kept there as reference). Used by the **Data Quality** sub-agent, routed by **Data-QA-Agent** (DQA cluster).

## Context to hold

The user is a BOT analyst who **receives** data from financial institutions, not the owner of the source system. Consequences:

- BOT cannot fix a reporter's data itself. A fix means the reporter explains or resubmits.
- Data that passes every validation may still be wrong, and data that looks abnormal may be a real transaction.
- Every rule costs the reporter effort. Rules with high false positives make reporters ignore warnings.
- Some outputs reach financial institutions and carry legal weight.

This skill covers only the 3 modes below. If the work continues into test cases, replies to reporters, Data RIA or pre-publication checks, finish the Data Quality part, then hand off to fin-data-management (if available).

## Rules for every mode

1. **Never invent BOT facts.** Dataset codes, data element names, rule codes, notification numbers, deadlines, severity level names and thresholds must come from project files or from the user. If missing, write `[specify: ...]`. Examples in this file are format only, not criteria.
2. **Search the project first.** Find the data set manual, existing rule list and internal criteria (Job-Base section "Internal criteria"), and cite document name and section. If documents do not cover the case or conflict, say so. Job-Base items labelled "temporary default" are not official criteria; never cite them in documents leaving the unit.
3. **Always compute with code** when a data file exists. Report every number with file name, data period, total row count and matching row count. Never estimate by eye.
4. **Separate "found" from "assumed"**, and state which points need confirmation from the user, the reporter, the data owner or Legal.
5. **Abnormal data is not yet a reporter error.** Use "needs checking" or "request clarification" until there is evidence.
6. **Confidentiality.** Internal work may name institutions as the user provides. Work leaving the unit must not identify any institution or person, and one institution's data must never appear in content sent to another. Trim diagnostic sample rows to the needed fields only. Warn when you see a risk.
7. **Decision authority.** Waiving or disabling a rule, changing a threshold, extending a deadline and accepting failed data belong to the authorized person. Write them as "proposal for consideration" with reasons and impact.
8. **Ask only when needed.** If missing information would change the result (e.g. unknown field definition or period), ask once, briefly. For minor details, state an assumption, label it, and continue.

## Data quality dimensions

Use BOT internal dimensions and thresholds if documented. If not, use this table as a temporary frame and tell the user it is a generic set.

| Dimension | Question to answer | Checks |
|---|---|---|
| Completeness | Did all required data arrive? | Mandatory fields not empty, record count vs previous period, all reporters present, defaults used in place of blanks |
| Validity | Are values in the required format and range? | Data type, codes per classification, value range, date format |
| Uniqueness | Are there duplicates? | Duplicate keys within a file, across periods, resubmitted twice |
| Consistency | Is the data internally consistent? | Within record, totals vs line items, across datasets, across periods |
| Timeliness | Did it arrive on time and for the right period? | Submission date vs deadline, period in file matches reported period |
| Accuracy | Do values reflect reality? | Compare to independent sources, to peer institutions, economic reasonableness |

Accuracy is the hardest to check by rule, because it needs an independent reference. Tell the user plainly when a check only shows reasonableness, not correctness.

## Mode 1: Design or review validation rules

### Steps

1. **Start from data users.** What is the data used for (supervision, statistics, publication)? Which wrong values lead to wrong decisions? A rule must protect the meaning of the data, not only its format.
2. **Read the spec.** Data element definitions, classifications, reporting conditions and existing rules from project documents.
3. **Walk rules through 5 levels** so nothing is missed:
   - Field: format, type, value range, accepted codes
   - Cross-field: relations between fields in one record (e.g. maturity date not before contract start)
   - Cross-record: within one file (unique key, total equals sum of line items)
   - Cross-dataset: between datasets that should agree (reconciliation)
   - Temporal: vs previous period, continuity of outstanding balances, change beyond normal range
4. **Set severity.** Use BOT system level names. If unknown, use 3 temporary levels and label them as an assumption:
   - Reject: data unusable with no business exception (wrong structure, duplicate key, non-existent code)
   - Warn, explain: abnormal but possibly real (large change, cross-dataset mismatch)
   - Info: logged for trend tracking; no reporter action

   If a real business case can fail the rule, it must not be Reject.
5. **Set thresholds from data.** With history, compute how many records the rule would catch per period and how many are likely false positives, then propose a threshold with those numbers. Without data, write `[specify: threshold]` and propose an observation-only run before enforcement.
6. **Write error messages reporters can act on.** State the field, value found, expected condition and next action.
7. **List test cases.** Per rule at least: pass, fail, boundary value, empty value, for hand-off to test case writing.

### When reviewing existing rules, check

- Duplicates or conflicts with other rules
- Still matches the current notification, definitions and classification (name the document compared)
- Severity fits; any real business case wrongly rejected
- With statistics: rules that never fire, and rules that fire so often nobody reads them
- Gaps across the 5 levels

### Output: rule list as an Excel file

Use the unit's template if in the project. Otherwise columns: Rule code | Dataset | Data element | Rule level | Dimension | Description | Condition (logic) | Severity | Threshold | Error message | Reference document | Test cases | Version and effective date | Status (new/changed/unchanged/proposed removal) | Notes and points to confirm

When changing a rule, keep its code, bump the version and record the reason, so historical statistics stay comparable.

## Mode 2: Check a data file

### Steps

1. **Confirm what was received.** File name, dataset, period, reporter, row and column counts, encoding and delimiter. Work on a copy; never modify the original.
2. **Check structure before content.** Columns match spec, types parse, no stray header or footer rows, row count reasonable vs previous period (if available).
3. **Profile every field.** Null rate, distinct count, min / max / median, frequent values, mixed string patterns, suspicious defaults (e.g. 0, 1900-01-01, 9999).
4. **Run existing rules** from the project rule list. If none, check across the 5 levels in Mode 1 as far as the spec allows, and mark which rules are Claude's proposals, not official rules.
5. **Check what rules miss.** Distribution vs previous period, abnormal values concentrated in one reporter or transaction type, totals vs related datasets.
6. **Find where problems concentrate.** A high overall pass rate can hide problems in the most important group. Always break down by reporter, type and period.
7. **Rank by impact** on data use, not by row count.

### Output

- **Summary in the reply:** verdict on how usable the data is, then 3-5 key issues, each with numbers, row counts, period and file.
- **Issue log as an Excel file:** unit template if available, otherwise columns: No. | Dataset | Period | Reporter | Data element | Rule or check | Dimension | Finding | Matching rows / total | Severity | Possible cause | Evidence | Proposed action | Owner | Status
- **Separate sheets:** per-field profiling results and sample matching rows (needed fields only).

If the issue log leaves the unit or goes to a specific reporter, split the file per reporter and warn the user about confidentiality.

## Mode 3: Trace the cause of abnormal data

### Steps

1. **Define the anomaly precisely.** Which value, whose, which period, deviating from what (previous period, peer group, other dataset), by how much. Confirm by computing from the file before trusting a report.
2. **Test hypotheses in this order** and rule them out with evidence. Never jump to "the reporter is wrong".

   | Order | Cause group | What to check |
   |---|---|---|
   | 1 | BOT side | Load, transformation, join, units, wrong period or version of file, rule malfunction |
   | 2 | Reporter technical | Duplicate submission, incomplete submission, wrong unit or currency, decimals, sign, reporter system change |
   | 3 | Classification | Items moved across classification, definition read differently than before or than peers |
   | 4 | Criteria change | New notification, definition or classification effective that period |
   | 5 | Structural | Merger, business transfer, business model change, new product |
   | 6 | Real transaction | Large deal, seasonality, market conditions, exchange rate |

3. **Locate the source.** Break down until the anomaly is traced to a record, type or counterparty group, and the period it starts.
4. **Check related datasets.** A real transaction should leave traces in other datasets too.
5. **Conclude with confidence levels.** Causes supported by evidence, causes ruled out, and causes not yet ruled out.

### Output: short analysis note

1. Conclusion (1-2 sentences)
2. Findings with numbers, row counts, period, file
3. Possible causes ranked by weight of evidence, separating "found" from "assumed"
4. Impact on data users and publication
5. Proposed action: further internal check, request clarification from the reporter (list the questions to ask), request resubmission, notify data users, or propose a rule change
6. Points that need someone's confirmation

If the user wants a message to the reporter, list the questions in item 5, then draft per fin-data-management Help Desk guidance (if available).

## Pre-delivery checklist

- [ ] Every rule, code and threshold has a source document or user input, or is written `[specify: ...]`
- [ ] Every number comes from running code, with row count, period and file name
- [ ] Found vs assumed is separated, and who must confirm is named
- [ ] No statement concludes the reporter is wrong without evidence
- [ ] Matters of decision authority are written as proposals for consideration
- [ ] Work leaving the unit identifies no institution or person and cites no temporary default as a criterion
- [ ] Multi-row tables are Excel files, and the file was opened and checked
- [ ] Reply opens with the conclusion and keeps English technical terms (plugin-rules § Language: replies are in English; the Thai original asked for Thai)
