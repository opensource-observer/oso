MODEL (
  name oso.int_artifacts_by_project_in_op_atlas_updates,
  dialect trino,
  kind FULL,
  enabled False,
  audits (
    has_at_least_n_rows(threshold := 0) -- Allow it to be empty initially
  )
);

-- Define manual artifact rules for OP Atlas projects.
-- Columns:
--   op_atlas_project_id (VARCHAR): The raw project ID from OP Atlas.
--   artifact_identifier (VARCHAR): The primary unique identifier for the artifact (e.g., slug, URL, address).
--   artifact_type (VARCHAR): The specific type of the artifact (e.g., 'DEFILLAMA_PROTOCOL', 'WEBSITE', 'CONTRACT').
--   rule_action (VARCHAR): 'INCLUDE' or 'EXCLUDE'.
--   blockchain_network (VARCHAR, nullable): For 'CONTRACT' or 'DEPLOYER' types, the network (e.g., 'optimism').

-- Example entries:
-- ('project_id_1', 'artifact_slug_or_url_1', 'ARTIFACT_TYPE_1', 'INCLUDE', NULL),
-- ('project_id_2', 'artifact_slug_or_url_2', 'ARTIFACT_TYPE_2', 'EXCLUDE', 'optimism')

/*

('0x808b31862cec6dccf3894bb0e76ce4ca298e4c2820e2ccbf4816da740463b220', 'fractal-visions'),
      ('0xed3d54e5394dc3ed01f15a67fa6a70e203df31c928dad79f70e25cb84f6e2cf9', 'host-it'),
      ('0x15b210abdc6acfd99e60255792b2b78714f4e8c92c4c5e91b898d48d046212a4', 'defieye')

*/      


SELECT
  op_atlas_project_id,
  artifact_identifier,
  artifact_type,
  rule_action,
  blockchain_network
FROM (
  VALUES
    ('0xd4f0252e6ac2408099cd40d213fb6f42e8fa129b446d6e8da55e673598ef14c0', 'moonwell-lending', 'DEFILLAMA_PROTOCOL', 'INCLUDE', NULL),
    ('0xd4f0252e6ac2408099cd40d213fb6f42e8fa129b446d6e8da55e673598ef14c0', 'moonwell-vaults', 'DEFILLAMA_PROTOCOL', 'INCLUDE', NULL),
    ('0xfd9f98de666c5b0a5ce96d4a4b8d4ceee9f8c2156734d57bf6c23d0cff183e90', 'kim-exchange', 'DEFILLAMA_PROTOCOL', 'INCLUDE', NULL),
    ('0x96767e87a27cdb9798f40c3a6fd78e70da611afe53a5e45cbaafc50cae4ad0e7', 'sonus', 'DEFILLAMA_PROTOCOL', 'INCLUDE', NULL), -- legacy parent protocol name
    ('0x7262ed9c020b3b41ac7ba405aab4ff37575f8b6f975ebed2e65554a08419f8f4', 'sablier-finance', 'DEFILLAMA_PROTOCOL', 'INCLUDE', NULL), -- legacy parent protocol name
    ('0x9c691ba3012549259099205cc1a7ca4d09d9b7a24a1b7b821b52c7bf1c9b89f4', 'origin-defi', 'DEFILLAMA_PROTOCOL', 'INCLUDE', NULL), -- legacy parent protocol name
    -- Manual GitHub repository mappings from original stg_op_atlas_project_repository.sql
    ('0xc377ed1b705bcc856a628f961f1e7c8ca943e6f3727b7c179c657e227e8e852c', 'https://github.com/miguelmota/merkletreejs', 'GITHUB_REPOSITORY', 'INCLUDE', NULL),
    ('0x48220ef1d103189cd918e9290db4c4b99b463ae2817fb5ef0cc54556a7961b6f', 'https://github.com/miguelmota/keccak256', 'GITHUB_REPOSITORY', 'INCLUDE', NULL),
    ('0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8', 'https://github.com/ethereum/solc-js', 'GITHUB_REPOSITORY', 'INCLUDE', NULL)
    -- Add more rules here as needed, for example:
    -- ,('some_project_id', 'https://example.com/badsite', 'WEBSITE', 'EXCLUDE', NULL)
    -- ,('another_project_id', '0x123abc...', 'CONTRACT', 'INCLUDE', 'optimism')
) AS x (op_atlas_project_id, artifact_identifier, artifact_type, rule_action, blockchain_network)
WHERE op_atlas_project_id IS NOT NULL; -- Basic validation to ensure rows are meaningful
