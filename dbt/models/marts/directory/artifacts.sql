{# for now this just copies all of the artifacts data #}
SELECT * 
FROM {{ ref('int_artifacts') }}