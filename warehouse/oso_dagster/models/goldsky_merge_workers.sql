{% for worker in workers %}
SELECT *
FROM {{ source(worker.deduped_table).fqdn }}
{% if not loop.last %}
UNION ALL
{% endif %}
{% endfor %}