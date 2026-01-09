MODEL (
  name oso.int_optimism__op_token_activity,
  kind INCREMENTAL_BY_TIME_RANGE(
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
    on_destructive_change warn
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("block_timestamp"),
  grain(
    block_timestamp,
    transaction_hash,
    log_index
  ),
  audits(
    has_at_least_n_rows(threshold := 0)
  ),
  ignored_rules(
    "incrementalmustdefinenogapsaudit"
  ),
  tags(
    "superchain",
    "incremental",
    "optimism"
  )
);

-- OP Token Transfer activity with method-based categorization
-- Replicates Optimism's token activity analysis model

WITH op_transfers AS (
  SELECT
    block_timestamp,
    transaction_hash,
    log_index,
    from_address AS tx_from_address,
    to_address AS called_contract,
    function_selector,
    -- Extract op_from_address from indexed_args_list[1] (last 40 hex chars = 20 bytes)
    CASE
      WHEN CARDINALITY(indexed_args_list) >= 1 
        AND indexed_args_list[1].element IS NOT NULL 
      THEN LOWER(CONCAT('0x', SUBSTRING(indexed_args_list[1].element, 27)))
    END AS op_from_address,
    -- Extract op_to_address from indexed_args_list[2]
    CASE
      WHEN CARDINALITY(indexed_args_list) >= 2 
        AND indexed_args_list[2].element IS NOT NULL 
      THEN LOWER(CONCAT('0x', SUBSTRING(indexed_args_list[2].element, 27)))
    END AS op_to_address,
    -- Parse value from data_hex and normalize to OP units (18 decimals)
    CASE
      WHEN data_hex IS NOT NULL 
        AND data_hex != '0x' 
        AND LENGTH(data_hex) >= 3
      THEN CAST(
        TRY(@safe_hex_to_int(SUBSTRING(data_hex, 3))) / CAST(1e18 AS DOUBLE) 
        AS DOUBLE
      )
      ELSE 0.0
    END AS value_op
  FROM oso.stg_optimism__enriched_logs
  WHERE
    block_timestamp BETWEEN @start_dt AND @end_dt
    -- Filter for ERC20 Transfer event signature
    AND topic0 = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    AND CARDINALITY(indexed_args_list) >= 2
),

categorized AS (
  SELECT
    block_timestamp,
    transaction_hash,
    log_index,
    tx_from_address,
    called_contract,
    function_selector,
    op_from_address,
    op_to_address,
    value_op,
    
    -- Map function_selector to human-readable function name
    CASE function_selector
      -- ERC20 core
      WHEN '0xa9059cbb' THEN 'transfer(address,uint256)'
      WHEN '0x23b872dd' THEN 'transferFrom(address,address,uint256)'
      WHEN '0x095ea7b3' THEN 'approve(address,uint256)'
      WHEN '0xd505accf' THEN 'permit(address,address,uint256,uint256,uint8,bytes32,bytes32)'
      -- Uniswap V2 swaps
      WHEN '0x38ed1739' THEN 'swapExactTokensForTokens'
      WHEN '0x8803dbee' THEN 'swapTokensForExactTokens'
      WHEN '0x7ff36ab5' THEN 'swapExactETHForTokens'
      WHEN '0x4a25d94a' THEN 'swapTokensForExactETH'
      WHEN '0x18cbafe5' THEN 'swapExactTokensForETH'
      WHEN '0xfb3bdb41' THEN 'swapETHForExactTokens'
      -- Liquidity
      WHEN '0xe8e33700' THEN 'addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)'
      WHEN '0xf305d719' THEN 'addLiquidityETH(address,uint256,uint256,uint256,address,uint256)'
      WHEN '0xbaa2abde' THEN 'removeLiquidity(address,address,uint256,uint256,uint256,address,uint256)'
      WHEN '0x02751cec' THEN 'removeLiquidityETH(address,uint256,uint256,address,uint256)'
      -- Uniswap V3 swaps
      WHEN '0x5d76b977' THEN 'exactInputSingle(tuple)'
      WHEN '0x89cf0f4a' THEN 'exactInput(bytes)'
      WHEN '0x5bd7800f' THEN 'exactOutputSingle(tuple)'
      WHEN '0xc0bcfe67' THEN 'exactOutput(bytes)'
      -- Bridge
      WHEN '0xb1a1a882' THEN 'depositETH(uint32,bytes)'
      WHEN '0x9a2ac6d5' THEN 'depositETHTo(address,uint32,bytes)'
      WHEN '0x58a997f6' THEN 'depositERC20(address,address,uint256,uint32,bytes)'
      WHEN '0x838b2520' THEN 'depositERC20To(address,address,address,uint256,uint32,bytes)'
      WHEN '0x32b7006d' THEN 'withdraw(address,uint256,uint32,bytes)'
      WHEN '0xa3a79548' THEN 'withdrawTo(address,address,uint256,uint32,bytes)'
      WHEN '0x3dbb202b' THEN 'sendMessage(address,bytes,uint32)'
      -- Staking
      WHEN '0xa694fc3a' THEN 'stake(uint256)'
      WHEN '0x2e1a7d4d' THEN 'withdraw(uint256)'
      WHEN '0x3d18b912' THEN 'getReward()'
      WHEN '0x4e71d92d' THEN 'claim()'
      -- Meta/multicall
      WHEN '0xac9650d8' THEN 'multicall(bytes[])'
      WHEN '0xb61d27f6' THEN 'execute(address,uint256,bytes)'
      WHEN '0x1cff79cd' THEN 'execute(address,bytes)'
      -- Governance
      WHEN '0x5c19a95c' THEN 'delegate(address)'
      ELSE 'other'
    END AS func_name,
    
    -- Map function_selector to category bucket
    CASE
      WHEN function_selector IN ('0xa9059cbb', '0x23b872dd') THEN 'transfer'
      WHEN function_selector IN ('0x095ea7b3', '0xd505accf') THEN 'approval'
      WHEN function_selector IN (
        '0x38ed1739', '0x8803dbee', '0x7ff36ab5', '0x4a25d94a', '0x18cbafe5', '0xfb3bdb41',
        '0x5d76b977', '0x89cf0f4a', '0x5bd7800f', '0xc0bcfe67'
      ) THEN 'swap'
      WHEN function_selector IN ('0xe8e33700', '0xf305d719', '0xbaa2abde', '0x02751cec') THEN 'liquidity'
      WHEN function_selector IN (
        '0xb1a1a882', '0x9a2ac6d5', '0x58a997f6', '0x838b2520', 
        '0x32b7006d', '0xa3a79548', '0x3dbb202b'
      ) THEN 'bridge'
      WHEN function_selector IN ('0xa694fc3a', '0x2e1a7d4d', '0x3d18b912', '0x4e71d92d') THEN 'staking'
      WHEN function_selector IN ('0xac9650d8', '0xb61d27f6', '0x1cff79cd') THEN 'meta_exec'
      WHEN function_selector IN ('0x5c19a95c') THEN 'governance'
      ELSE 'other'
    END AS func_bucket
  FROM op_transfers
)

SELECT
  block_timestamp,
  transaction_hash,
  log_index,
  tx_from_address,
  called_contract,
  function_selector,
  op_from_address,
  op_to_address,
  value_op,
  func_name,
  func_bucket
FROM categorized
