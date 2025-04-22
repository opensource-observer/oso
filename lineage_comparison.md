# Comparison: Current vs. Simplified Lineage

This document compares the current lineage structure with the proposed simplified structure for the `artifacts_by_project_v1` model.

## Model Count Comparison

| Metric                  | Current Structure | Simplified Structure | Reduction |
| ----------------------- | ----------------- | -------------------- | --------- |
| Total Models            | 18                | 9                    | 50%       |
| Dependency Levels       | 7                 | 4                    | 43%       |
| Source-specific Models  | 2                 | 3 (interfaces)       | N/A       |
| Artifact Type Models    | 3                 | 1                    | 67%       |
| Deployment Chain Models | 4                 | 1                    | 75%       |

## Structural Improvements

### 1. Consolidated Source Layer

**Current Structure:**

- Separate models for each source (`int_artifacts_by_project_in_ossd`, `int_artifacts_by_project_in_op_atlas`)
- Different schemas and processing logic for each source
- Complex joins to combine sources

**Simplified Structure:**

- Single `int_raw_artifacts` model with standardized schema
- Source-specific interfaces that handle the transformation to the standard schema
- Cleaner separation between source-specific logic and common processing

### 2. Unified Artifact Types

**Current Structure:**

- Separate models for each artifact type (`int_deployers_by_project`, `int_contracts_by_project`, `int_bridges_by_project`)
- Duplicated logic across artifact type models
- Complex circular dependencies

**Simplified Structure:**

- Single `int_typed_artifacts` model with a type column
- Common processing logic for all artifact types
- Simpler extension for new artifact types

### 3. Flattened Deployment Chain

**Current Structure:**

- Long chain of models: `int_contracts_deployment` → `int_contracts_root_deployers` → `int_derived_contracts`
- Complex dependencies between deployment-related models
- Difficult to understand the full deployment logic

**Simplified Structure:**

- Single `int_contract_deployments` model
- Consolidated deployment logic in one place
- Clearer understanding of contract deployment process

## Visual Comparison

### Current Structure

```
7 levels deep, 18 models, complex circular dependencies
```

### Simplified Structure

```
4 levels deep, 9 models, clear unidirectional flow
```

## Migration Strategy

To migrate from the current structure to the simplified structure:

1. **Phase 1: Create Interface Models**

   - Implement source-specific interfaces without changing existing models
   - Validate that interfaces produce the same output as current models

2. **Phase 2: Implement Consolidated Models**

   - Create `int_raw_artifacts` and `int_typed_artifacts`
   - Run in parallel with existing models to validate output

3. **Phase 3: Implement Domain-Specific Modules**

   - Create `int_contract_deployments` and other domain modules
   - Validate against existing deployment chain

4. **Phase 4: Update Final Models**

   - Modify `int_all_artifacts` and `int_artifacts_by_project` to use new models
   - Validate final output matches current output

5. **Phase 5: Deprecate Legacy Models**
   - Once all validations pass, deprecate and remove old models

## Conclusion

The simplified structure offers significant advantages in terms of maintainability, clarity, and extensibility. By reducing the model count by 50% and flattening the dependency hierarchy, the lineage becomes much easier to understand and maintain.
