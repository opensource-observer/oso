SELECT *
FROM project_summary AS ps
WHERE 
  ps.status = 'UPDATED' 
  OR ps.blockchain_added != 0 
  OR ps.blockchain_removed != 0 
  OR ps.url_added != 0 
  OR ps.url_removed != 0 