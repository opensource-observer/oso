{% macro parse_npm_git_url(repository_url_column, source_table) %}
with cleaned_urls as (
  select
    `name`,
    artifact_url,
    {{ repository_url_column }} as original_url,
    case
      when regexp_contains({{ repository_url_column }}, r'#') then 
        regexp_replace({{ repository_url_column }}, r'#.*$', '')
      else {{ repository_url_column }}
    end as cleaned_url
  from {{ source_table }}
),

normalized_urls as (
  select
    `name`,
    artifact_url,
    original_url,
    cleaned_url,
    case
      when regexp_contains(cleaned_url, r'^git\+ssh://') then 
        regexp_replace(cleaned_url, r'^git\+ssh://([^@]+)@', 'https://')
      when regexp_contains(cleaned_url, r'^git@') then 
        regexp_replace(cleaned_url, r'^git@(.*?):', 'https://\\1/')
      when regexp_contains(cleaned_url, r'^git\+https://') then 
        regexp_replace(cleaned_url, r'^git\+', '')
      when regexp_contains(cleaned_url, r'^[^:/]+\.[^:/]+/') then 
        concat('https://', cleaned_url)
      when regexp_contains(cleaned_url, r'^https?://') then 
        cleaned_url
      else null
    end as normalized_url
  from cleaned_urls
),

parsed_data as (
  select
    `name`,
    artifact_url,
    original_url,
    normalized_url,
    regexp_extract(normalized_url, r'https?://([^/]+)/') as remote_host,
    regexp_extract(
      normalized_url, 
      r'https?://[^/]+/([^/]+)/'
    ) as remote_namespace,
    regexp_extract(
      normalized_url, 
      r'https?://[^/]+/[^/]+/([^/.]+)'
    ) as remote_name
  from normalized_urls
),

final_data as (
  select
    `name`,
    artifact_url,
    original_url,
    normalized_url as remote_url,
    remote_host,
    remote_namespace,
    remote_name,
    case
      when lower(remote_host) like 'github.com%' then 'GITHUB'
      when lower(remote_host) like 'gitlab.com%' then 'GITLAB'
      when lower(remote_host) like 'bitbucket.org%' then 'BITBUCKET'
      else 'OTHER'
    end as remote_source_id
  from parsed_data
)

select * from final_data
{% endmacro %}
