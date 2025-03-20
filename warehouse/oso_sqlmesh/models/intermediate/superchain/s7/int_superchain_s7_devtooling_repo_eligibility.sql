MODEL (
  name oso.int_superchain_s7_devtooling_repo_eligibility,
  description 'Temp table - will delete after S7 migration',
  dialect trino,
  kind full,
);

SELECT *
FROM oso.int_superchain_s7_devtooling_repositories
