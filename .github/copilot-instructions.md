# GitHub Copilot Instructions for OSO Data Contributions

## Mission Statement
When contributing data sources to the Open Source Observer (OSO) repository, you are expected to create production-ready, reproducible data pipelines using Dagster assets. Focus on Database replication, GraphQL API crawling, and REST API crawling following OSO's established patterns.

## Project Context & Architecture

### Technology Stack
- **Pipeline Framework**: Dagster with DLT (Data Load Tool)
- **Language**: Python 3.11+
- **Data Processing**: Polars (preferred), Pandas for compatibility
- **Storage**: Local development, cloud-ready (S3/GCS)
- **Testing**: pytest with data validation
- **CI/CD**: GitHub Actions with pre-commit hooks

### Repository Structure
```
/data/
  raw/<source>/<YYYY-MM-DD>/     # Raw ingested data
  processed/<dataset>/<version>/  # Transformed, validated data
  samples/<dataset>.csv           # Small representative samples
  metadata/<dataset>.yml          # Dataset metadata schema
/warehouse/oso_dagster/assets/   # Dagster asset definitions
/scripts/                        # Standalone data processing scripts
/tests/data/                     # Data validation tests
```

## Data Asset Creation Patterns

### 1. REST API Assets
Use the existing `create_rest_factory_asset` pattern:

```python
from warehouse.oso_dagster.factories import create_rest_factory_asset
from dlt.sources.rest_api.typing import RESTAPIConfig

# Configuration-driven REST API asset
@create_rest_factory_asset(
    config=RESTAPIConfig({
        "client": {
            "base_url": "https://api.example.com/v1",
            "headers": {"Authorization": "Bearer ${API_TOKEN}"},
            "paginator": "auto"  # or custom paginator config
        },
        "resources": [
            {
                "name": "organizations",
                "endpoint": "/orgs",
                "data_selector": "data",
                "write_disposition": "replace"
            }
        ]
    }),
    key_prefix=["external", "source_name"],
    name="organizations"
)
def source_name_organizations_asset(context: AssetExecutionContext):
    """
    Loads organization data from Source Name API.
    
    Updates: Daily via schedule
    Schema: id (int), name (str), created_at (datetime)
    """
    pass
```

### 2. GraphQL API Assets
Create GraphQL-specific factories following REST patterns:

```python
from warehouse.oso_dagster.factories import create_graphql_factory_asset

@create_graphql_factory_asset(
    endpoint="https://api.example.com/graphql",
    query="""
        query($first: Int!, $after: String) {
            repositories(first: $first, after: $after) {
                nodes { id name createdAt }
                pageInfo { hasNextPage endCursor }
            }
        }
    """,
    variables={"first": 100},
    key_prefix=["external", "source_name"],
    name="repositories"
)
def source_name_repositories_asset(context: AssetExecutionContext):
    """GraphQL-sourced repository data with cursor-based pagination."""
    pass
```

### 3. Database Replication Assets
For database replication using connection strings:

```python
from warehouse.oso_dagster.factories import create_database_factory_asset

@create_database_factory_asset(
    connection_string="${DATABASE_URL}",
    tables=["users", "projects", "contributions"],
    key_prefix=["replicated", "source_db"],
    incremental_column="updated_at"
)
def source_db_replication_asset(context: AssetExecutionContext):
    """Incremental replication from source database."""
    pass
```

## Mandatory Requirements

### File Structure for New Data Source
When adding a data source named `example_source`:

1. **Asset Definition**: `/warehouse/oso_dagster/assets/external_sources/example_source.py`
2. **Metadata File**: `/data/metadata/example_source.yml`
3. **Sample Data**: `/data/samples/example_source.csv`
4. **Tests**: `/tests/data/test_example_source.py`
5. **Documentation**: `/docs/data_sources/example_source.md`

### Metadata Schema (YAML)
```yaml
name: example_source
version: "1.0.0"
source:
  url: "https://api.example.com"
  documentation: "https://docs.example.com/api"
  license: "MIT"
  attribution: "Data provided by Example Corp"
schema:
  columns:
    - name: id
      type: int64
      nullable: false
      description: "Unique identifier"
    - name: created_at
      type: datetime
      nullable: false
      description: "Creation timestamp in UTC"
validation:
  row_count_min: 1000
  size_bytes_max: 1073741824  # 1GB
  checksum_algorithm: "sha256"
privacy:
  pii: false
  retention_days: 365
owner: "data-team@example.org"
created_at: "2024-08-21T00:00:00Z"
```

### Asset Implementation Guidelines

#### Error Handling & Resilience
```python
from dagster import AssetExecutionContext, AssetMaterialization, MetadataValue
import polars as pl
from typing import Iterator

def robust_data_asset(context: AssetExecutionContext) -> Iterator[AssetMaterialization]:
    """Template for resilient data asset implementation."""
    try:
        # Rate limiting and retry logic
        with context.log.timed_op("data_extraction"):
            data = extract_with_retries(context)
            
        # Schema validation
        validated_data = validate_schema(data, context)
        
        # Data quality checks
        quality_metrics = run_quality_checks(validated_data, context)
        
        # Materialization with metadata
        yield AssetMaterialization(
            metadata={
                "row_count": MetadataValue.int(len(validated_data)),
                "columns": MetadataValue.int(len(validated_data.columns)),
                "data_quality_score": MetadataValue.float(quality_metrics.score),
                "extraction_time": MetadataValue.text(context.op_execution_context.start_time)
            }
        )
        
    except Exception as e:
        context.log.error(f"Asset materialization failed: {str(e)}")
        # Log structured error for monitoring
        context.log_event(AssetObservation(
            metadata={"error": MetadataValue.text(str(e))}
        ))
        raise
```

#### Data Validation Patterns
```python
import great_expectations as gx
from warehouse.oso_dagster.utils.validation import validate_asset_data

def validate_asset_data(df: pl.DataFrame, context: AssetExecutionContext) -> pl.DataFrame:
    """Standard validation pipeline for all assets."""
    expectations = [
        gx.expect_table_row_count_to_be_between(min_value=1),
        gx.expect_column_to_exist("id"),
        gx.expect_column_values_to_be_unique("id"),
        gx.expect_column_values_to_not_be_null("created_at")
    ]
    
    # Run expectations and log results
    for expectation in expectations:
        result = expectation.validate(df)
        if not result.success:
            context.log.warning(f"Validation failed: {expectation}")
    
    return df
```

### Testing Requirements

#### Data Asset Tests
```python
import pytest
from unittest.mock import patch
from warehouse.oso_dagster.assets.external_sources.example_source import example_asset

def test_example_asset_schema():
    """Test that asset produces expected schema."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = SAMPLE_API_RESPONSE
        
        # Test asset execution
        result = example_asset.execute_in_process()
        assert result.success
        
        # Validate schema
        df = result.output_for_node("example_asset")
        assert "id" in df.columns
        assert len(df) > 0

def test_example_asset_handles_api_errors():
    """Test graceful handling of API failures."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("API down")
        
        with pytest.raises(requests.RequestException):
            example_asset.execute_in_process()
```

## Security & Privacy Guidelines

### Environment Variables
- Never hardcode API keys or secrets
- Use `${VARIABLE_NAME}` syntax in configurations
- Document required environment variables in `.env.example`

### PII Handling
- Set `pii: true` in metadata if data contains personal information
- Implement anonymization before writing to `/data/processed/`
- Add data retention policies and cleanup jobs

### Rate Limiting
```python
from time import sleep
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_resilient_session(max_retries: int = 3) -> requests.Session:
    """Create HTTP session with retry strategy and rate limiting."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

## Git & PR Workflow

### Branch Naming
- Feature: `feat/data-{source_name}-v{version}`
- Bug fix: `fix/data-{source_name}-{issue_description}`
- Enhancement: `enhance/data-{source_name}-{feature}`

### Commit Messages
Follow conventional commits:
```
feat(data): add GitHub GraphQL API crawler v1.0

- Implements repository and issue data extraction
- Includes rate limiting and error handling
- Adds comprehensive test coverage
- Updates documentation with API schema
```

### PR Requirements Checklist
- [ ] Asset definition follows factory patterns
- [ ] Metadata YAML is complete and valid
- [ ] Sample data file included (< 1MB)
- [ ] Tests cover success and failure scenarios
- [ ] Documentation includes schema and examples
- [ ] Environment variables documented
- [ ] Pre-commit hooks pass
- [ ] CI pipeline succeeds

## Common Patterns & Anti-Patterns

### ✅ Do This
```python
# Use configuration-driven factories
@create_rest_factory_asset(config=CONFIG)
def clean_asset_name(context: AssetExecutionContext):
    """Clear, concise docstring explaining purpose."""
    pass

# Leverage Polars for performance
df = pl.read_json(response.text).with_columns([
    pl.col("created_at").str.to_datetime(),
    pl.col("id").cast(pl.Int64)
])
```

### ❌ Don't Do This
```python
# Avoid hardcoding configurations
def bad_asset():
    url = "https://api.example.com"  # Bad: hardcoded
    headers = {"Authorization": "Bearer abc123"}  # Bad: secret exposed
    
# Don't ignore error handling
def fragile_asset():
    response = requests.get(url)  # Bad: no error handling
    data = response.json()  # Bad: might fail
```

## Performance Optimization

### Memory Management
- Stream large datasets instead of loading entirely into memory
- Use chunked processing for datasets > 100MB
- Prefer columnar formats (Parquet) over CSV for processed data

### Caching Strategy
```python
from dagster import asset, CachingConfig

@asset(
    caching_config=CachingConfig(
        cache_key_fn=lambda context: f"api_data_{context.partition_key}"
    )
)
def cached_api_asset(context: AssetExecutionContext):
    """Asset with intelligent caching based on partition key."""
    pass
```

## Monitoring & Observability

### Logging Standards
```python
def asset_with_proper_logging(context: AssetExecutionContext):
    context.log.info(f"Starting data extraction from {source_name}")
    
    try:
        with context.log.timed_op("api_request"):
            data = fetch_data()
            
        context.log.info(f"Successfully extracted {len(data)} records")
        
    except Exception as e:
        context.log.error(f"Extraction failed: {str(e)}", extra={"source": source_name})
        raise
```

### Metrics Collection
Include these metadata fields in all assets:
- `row_count`: Number of records processed
- `processing_time_seconds`: Execution duration
- `data_freshness`: Age of source data
- `quality_score`: Data quality metrics (0-1)

---

## Final Checklist

Before submitting any data contribution:

1. **Code Quality**
   - [ ] Follows existing factory patterns
   - [ ] Includes comprehensive error handling
   - [ ] Uses environment variables for secrets
   - [ ] Implements proper logging

2. **Documentation**
   - [ ] Complete metadata YAML
   - [ ] Asset docstrings explain purpose and schema
   - [ ] Sample data file provided
   - [ ] API documentation referenced

3. **Testing**
   - [ ] Unit tests for asset logic
   - [ ] Integration tests with mocked APIs
   - [ ] Data validation tests
   - [ ] Error scenario coverage

4. **Security**
   - [ ] No hardcoded secrets or URLs
   - [ ] PII handling if applicable
   - [ ] Rate limiting implemented
   - [ ] Input validation present

Remember: Write code that OSO maintainers will be impressed to merge. Focus on clarity, robustness, and following established patterns rather than reinventing solutions.
