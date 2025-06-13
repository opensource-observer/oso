MODEL (
  name oso.int_chainlist,
  description 'Current mapping of chain_id to chain_name',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  cl.chain_id,
  cl.name AS chainlist_name,
  UPPER(cid_to_name.chain_name) AS oso_chain_name,
  cid_to_name.display_name AS display_name
FROM oso.stg_chainlist__chains AS cl
JOIN oso.seed_chain_id_to_chain_name AS cid_to_name
  ON cl.chain_id = cid_to_name.chain_id
