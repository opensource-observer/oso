SELECT 
  s.url_value,
  s.url_type
FROM url_status as s
WHERE s.status = 'ADDED' AND
    s.url_type = 'DEFILLAMA'