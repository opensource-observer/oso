# Simplified Artifacts Lineage

This document provides guidance on implementing the simplified lineage structure for the `artifacts_by_project_v1` model and related models.

## Overview

The current lineage structure for `artifacts_by_project_v1` has grown complex over time, with:

- 18 models across 7 dependency levels
- Circular dependencies between models
- Separate models for different artifact types and sources
- Complex deployment chains

The simplified approach reduces this complexity by:

- Consolidating models by function
- Creating clear interfaces between layers
- Unifying artifact types
- Flattening dependency chains

## Key Files

- [artifacts_by_project_lineage.md](artifacts_by_project_lineage.md) - Current lineage structure
- [simplified_artifacts_by_project_lineage.md](simplified_artifacts_by_project_lineage.md) - Proposed simplified structure
- [lineage_comparison.md](lineage_comparison.md) - Comparison between current and simplified structures
- Sample implementations:
  - [sample_int_raw_artifacts.sql](sample_int_raw_artifacts.sql) - Consolidated artifacts from all sources
  - [sample_int_ossd_interface.sql](sample_int_ossd_interface.sql) - Interface for OSS Directory data
  - [sample_int_typed_artifacts.sql](sample_int_typed_artifacts.sql) - Unified model for all artifact types

## Core Principles

### 1. Source Abstraction

Create clear interfaces between staging and intermediate layers:

```
staging models → source interfaces → consolidated models
```

Benefits:

- Isolates source-specific logic
- Makes it easier to handle changes in source data
- Provides a clear contract between layers

### 2. Type Consolidation

Instead of separate models for each artifact type, use a single model with a type column:

```
int_typed_artifacts (with artifact_type column)
```

Benefits:

- Common processing logic for all types
- Easier to add new types
- Reduced circular dependencies

### 3. Domain Modularization

Group related models into clear domains:

```
/contracts/
/social/
/identifiers/
```

Benefits:

- Better organization
- Clearer responsibilities
- Easier to understand and maintain

## Implementation Strategy

### Phase 1: Create Interface Models

1. Implement source-specific interfaces without changing existing models
2. Validate that interfaces produce the same output as current models

Example:

```sql
-- Create new interface model
CREATE MODEL oso.int_ossd_interface AS
SELECT ... FROM oso.stg_ossd__current_projects;

-- Validate against existing model
SELECT COUNT(*) FROM oso.int_ossd_interface;
SELECT COUNT(*) FROM oso.int_artifacts_by_project_in_ossd;
```

### Phase 2: Implement Consolidated Models

1. Create `int_raw_artifacts` and `int_typed_artifacts`
2. Run in parallel with existing models to validate output

Example:

```sql
-- Create consolidated model
CREATE MODEL oso.int_raw_artifacts AS
SELECT ... FROM oso.int_ossd_interface
UNION ALL
SELECT ... FROM oso.int_op_atlas_interface;

-- Validate against existing model
SELECT COUNT(*) FROM oso.int_raw_artifacts;
SELECT COUNT(*) FROM oso.int_artifacts_by_project_all_sources;
```

### Phase 3: Implement Domain-Specific Modules

1. Create `int_contract_deployments` and other domain modules
2. Validate against existing deployment chain

Example:

```sql
-- Create consolidated deployment model
CREATE MODEL oso.int_contract_deployments AS
SELECT ... FROM oso.stg_superchain__factories;

-- Validate against existing models
SELECT COUNT(*) FROM oso.int_contract_deployments;
SELECT COUNT(*) FROM oso.int_derived_contracts;
```

### Phase 4: Update Final Models

1. Modify `int_all_artifacts` and `int_artifacts_by_project` to use new models
2. Validate final output matches current output

Example:

```sql
-- Update final model
CREATE MODEL oso.int_all_artifacts_new AS
SELECT ... FROM oso.int_raw_artifacts
UNION ALL
SELECT ... FROM oso.int_typed_artifacts;

-- Validate against existing model
SELECT COUNT(*) FROM oso.int_all_artifacts_new;
SELECT COUNT(*) FROM oso.int_all_artifacts;
```

### Phase 5: Deprecate Legacy Models

1. Once all validations pass, deprecate and remove old models
2. Update documentation and lineage diagrams

## Benefits

1. **Reduced Model Count**: 50% fewer models to maintain
2. **Clearer Data Flow**: 43% fewer dependency levels
3. **Modular Design**: Organized by domain and function
4. **Easier Extensibility**: Adding new sources or types is simpler
5. **Reduced Circular Dependencies**: Cleaner architecture

## Considerations

1. **Backward Compatibility**: Ensure existing downstream consumers aren't affected
2. **Performance**: Test query performance with the new structure
3. **Documentation**: Update documentation to reflect the new structure
4. **Testing**: Comprehensive testing to ensure data integrity

## Next Steps

1. Review the proposed structure and sample implementations
2. Develop a detailed migration plan
3. Implement Phase 1 (interface models)
4. Validate and iterate
5. Continue with subsequent phases
