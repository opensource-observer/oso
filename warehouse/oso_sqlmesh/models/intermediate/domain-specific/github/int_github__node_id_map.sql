MODEL (
  name oso.int_github__node_id_map,
  description 'Pre-computed mapping of GitHub GraphQL Node IDs to decoded integer IDs. Decodes each unique Node ID once for efficient lookups by downstream models.',
  dialect trino,
  kind FULL,
  grain (node_id),
  tags (
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    not_null(columns := (node_id, decoded_id))
  )
);

WITH unique_node_ids AS (
  SELECT DISTINCT primary_github_user_id AS node_id
  FROM oso.stg_opendevdata__canonical_developers
  WHERE primary_github_user_id IS NOT NULL
    AND primary_github_user_id != ''

  UNION

  SELECT DISTINCT github_graphql_id AS node_id
  FROM oso.stg_opendevdata__repos
  WHERE github_graphql_id IS NOT NULL
    AND github_graphql_id != ''
)

SELECT
  node_id,
  @decode_github_node_id(node_id) AS decoded_id
FROM unique_node_ids
