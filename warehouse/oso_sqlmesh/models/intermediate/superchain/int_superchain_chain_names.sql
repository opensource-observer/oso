MODEL(
  name oso.int_superchain_chain_names,
  description 'Relevant Superchain chains',
  kind full
);

@DEF(chains, [
  'automata',
  'base',
  'bob',
  'cyber',
  'frax',
  'ham',
  'ink',
  'kroma',
  'lisk',
  'lyra',
  'metal',
  'mint',
  'mode',
  'optimism',
  'orderly',
  'polynomial',
  'race',
  'redstone',
  'shape',
  'soneium',
  'swan',
  'swell',
  'unichain',
  'worldchain',
  'xterio',
  'zora'
]);

WITH chains_struct AS (
  SELECT UPPER(t.chain) as chain
  FROM UNNEST(@chains) AS t(chain)
)

SELECT chain
FROM chains_struct
