SELECT 
  CAST(cu.date AS Timestamp) AS `time`,
  TO_BASE64(
    SHA1(
      CONCAT(
        CAST(cu.date AS STRING), 
        cu.address, 
        CASE 
          WHEN cu.user_address IS NULL THEN "" 
          ELSE cu.user_address
        END,
        CASE 
          WHEN cu.safe_address IS NULL THEN "" 
          ELSE cu.safe_address
        END
      ))
  ) as `source_id`,
  cu.address AS `to_name`,
  "ARBITRUM" AS `to_namespace`,
  "CONTRACT_ADDRESS" AS `to_type`,
  cu.address AS `to_source_id`,
  
  CASE
    WHEN cu.safe_address IS NULL THEN cu.user_address
    WHEN cu.user_address IS NULL THEN cu.safe_address
    ELSE "unknown"
  END AS `from_name`,

  "ARBITRUM" AS `from_namespace`,

  CASE
    WHEN cu.safe_address IS NULL THEN "EOA_ADDRESS"
    WHEN cu.user_address IS NULL THEN "SAFE_ADDRESS"
    ELSE "unknown"
  END AS `from_type`,

  CASE
    WHEN cu.safe_address IS NULL THEN cu.user_address
    WHEN cu.user_address IS NULL THEN cu.safe_address
    ELSE "unknown"
  END AS `from_source_id`,

  CAST(cu.l1_gas AS FLOAT64) as `l1_gas`,
  CAST(cu.l2_gas AS FLOAT64) as `l2_gas`,
  CAST(cu.tx_count AS FLOAT64) AS `tx_count`

{# FROM `oso-production.opensource_observer.contract_usage` as cu #}
FROM {{ oso_source('dune', 'arbitrum_contract_usage')}} as cu