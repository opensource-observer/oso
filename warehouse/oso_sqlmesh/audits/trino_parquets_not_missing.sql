-- This is an audit to ensure we catch issues with parquet files missing 
-- in trino
AUDIT (
  name trino_parquets_not_missing
);
SELECT count(*) FROM @this_model