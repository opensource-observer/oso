SELECT COUNT(*) AS total
FROM project_summary AS ps
WHERE 
  ps.status != 'UPDATED' 
  AND ps.blockchain_added == 0 
  OR ps.blockchain_removed == 0 
  OR ps.code_added == 0 
  OR ps.code_removed == 0 
  OR ps.package_added == 0 
  OR ps.package_removed == 0 