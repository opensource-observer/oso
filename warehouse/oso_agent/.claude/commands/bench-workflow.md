---
description: Compare workflow performance and display benchmark analysis
allowed-tools: Read, Bash(date*), Bash(echo*)
---

# Workflow Performance Benchmark Comparison

Analyze workflow performance against baseline and display comprehensive comparison as markdown.

**Usage**: `/bench-workflow TARGET_WORKFLOW BASELINE_WORKFLOW`

**Arguments**:

- `$1` (TARGET_WORKFLOW): Target workflow to analyze (e.g., "v27_08_25/i1")
- `$2` (BASELINE_WORKFLOW): Baseline for comparison (e.g., "v18_08_25/i0")

## Execution Steps

### 1. Validate Arguments and Paths

Extract workflow components from arguments:

- Target directory: Extract directory from `$1` (everything before last '/')
- Target iteration: Extract iteration from `$1` (everything after last '/')
- Target results: `oso_agent/workflows/text2sql/semantic_iters/$1_results.json`
- Baseline results: `oso_agent/workflows/text2sql/semantic_iters/$2_results.json`

Verify all required files exist before proceeding.

### 2. Discover Available Evaluation Metrics

First, dynamically discover available evaluation metrics by reading `oso_agent/eval/text2sql/evals.py`:

- Parse the file to find all async functions that return `EvaluationResult`
- Extract function names and their docstrings for metric descriptions
- Use the `label` field from each function's `EvaluationResult` return to identify metric keys

### 3. Load Performance Data

Read both JSON result files and extract `annotationSummaries` arrays containing the discovered evaluation metrics.

For each discovered metric, extract the `meanScore` value from both target and baseline.

### 4. Calculate Performance Metrics

For each evaluation metric, compute:

- **Absolute Difference**: `target_score - baseline_score`
- **Percentage Change**: `((target_score - baseline_score) / baseline_score) * 100`
- **Change Status**:
  - "IMPROVED" if difference > +0.005
  - "REGRESSED" if difference < -0.005
  - "STABLE" if within ±0.005 range

### 5. Generate Performance Analysis

#### Create Summary Table

```
| Metric | Baseline | Target | Δ | % Change | Status |
|--------|----------|--------|---|----------|---------|
| Syntax Validation | 0.XXX | 0.XXX | ±0.XXX | ±XX.X% | STATUS |
| Execution Success | 0.XXX | 0.XXX | ±0.XXX | ±XX.X% | STATUS |
| Command Types | 0.XXX | 0.XXX | ±0.XXX | ±XX.X% | STATUS |
| Table Matching | 0.XXX | 0.XXX | ±0.XXX | ±XX.X% | STATUS |
| Exact Results | 0.XXX | 0.XXX | ±0.XXX | ±XX.X% | STATUS |
| Fuzzy Results | 0.XXX | 0.XXX | ±0.XXX | ±XX.X% | STATUS |
```

#### Determine Overall Assessment

Apply weighted scoring system:

- **High Priority** (weight 3): `results_exact_match`, `results_similarity_score`
- **Medium Priority** (weight 2): `sql_execution_success`, `oso_tables_match`
- **Low Priority** (weight 1): `sql_syntax_validation`, `sql_command_types_match`

Calculate weighted improvement score:

- Sum: (weight × percentage_change) for each metric
- Overall status: "BETTER" (>0), "WORSE" (<0), or "MIXED" (≈0)

### 6. Generate Analysis Content

#### Key Findings Analysis

**Strengths**: List metrics with >10% improvement and explain significance
**Weaknesses**: List metrics with >10% regression and explain impact
**Technical Assessment**:

- **Execution Quality**: Analyze syntax validation + execution success trends
- **Query Accuracy**: Analyze command types + table matching performance
- **Result Quality**: Analyze exact match + similarity score changes

#### Contextual Insights

For each significant change (>10%), provide context:

- What the metric measures (reference oso_agent/eval/text2sql/evals.py)
- Why the change matters for workflow performance
- Potential causes based on metric behavior patterns

### 7. Generate Markdown Output

Print the complete benchmark analysis to console as formatted markdown:

```markdown
## Benchmark Analysis

### Performance vs Baseline ($2)

[Insert Performance Summary Table]

### Key Findings

**Strengths:**
[List improved metrics with context - only include if >10% improvement]

**Weaknesses:**  
[List regressed metrics with context - only include if >10% regression]

**Overall Assessment:** [BETTER/WORSE/MIXED] - [Brief technical explanation]

### Technical Analysis

**Execution Quality:** [Analysis of syntax + execution metrics]
**Query Accuracy:** [Analysis of command types + table matching]
**Result Quality:** [Analysis of exact + fuzzy matching]

### Performance Summary

- **Best Performing Area**: [Highest scoring metric category]
- **Primary Challenge**: [Lowest scoring metric category]
- **Key Improvement**: [Largest positive change]
- **Main Regression**: [Largest negative change]

_Analysis generated on [TIMESTAMP] comparing $1 vs $2_
```

## Formatting Requirements

- Use 3 decimal places for scores (0.XXX)
- Use 1 decimal place for percentages (XX.X%)
- Format positive changes as "+X.XX" and negative as "-X.XX"
- Keep analysis concise but technically precise
- Focus on actionable insights for workflow developers
- Include timestamp with format: `$(date '+%Y-%m-%d %H:%M')`

## Error Handling

- Validate that both argument workflows exist in semantic_iters directory
- Check JSON files are valid and contain required annotationSummaries
- Handle missing metrics by noting them in analysis
- Provide clear error messages for any validation failures

**Execute comprehensive benchmark analysis and print results for workflows $1 and $2.**
