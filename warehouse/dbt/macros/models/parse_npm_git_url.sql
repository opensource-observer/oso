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
    cleaned_url,
    case
      when regexp_contains(cleaned_url, r'^git\+ssh://') then 
        regexp_replace(cleaned_url, r'^git\+ssh://([^@]+)@', 'https://')
      when regexp_contains(cleaned_url, r'^git@') then 
        regexp_replace(cleaned_url, r'^git@(.*?):', 'https://\\1/')
      when regexp_contains(cleaned_url, r'^git\+https://') then 
        regexp_replace(cleaned_url, r'^git\+', '')
      when regexp_contains(cleaned_url, r'^git://') then 
        regexp_replace(cleaned_url, r'^git://', 'https://')
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
    lower(`name`) as artifact_name,
    lower(regexp_extract(`name`, r'@?([^/]+)')) as artifact_namespace,
    lower(artifact_url) as artifact_url,
    lower(normalized_url) as normalized_url,
    lower(regexp_extract(normalized_url, r'https?://([^/]+)/'))
      as remote_artifact_host,
    lower(regexp_extract(normalized_url, r'https?://[^/]+/([^/]+)/'))
      as remote_artifact_namespace,
    lower(regexp_extract(normalized_url, r'https?://[^/]+/[^/]+/([^/.]+)')) 
      as remote_artifact_name
  from normalized_urls
),

final_data as (
  select
    'NPM' as artifact_source,
    artifact_name,
    artifact_namespace,
    artifact_url,
    concat(
      'https://', remote_artifact_host, '/', remote_artifact_namespace,
      '/', remote_artifact_name, '.git'
    ) as remote_artifact_url,
    remote_artifact_host,
    remote_artifact_namespace,
    remote_artifact_name,
    case
      when remote_artifact_host like 'github.com%' then 'GITHUB'
      when remote_artifact_host like 'gitlab.com%' then 'GITLAB'
      when remote_artifact_host like 'bitbucket.org%' then 'BITBUCKET'
      else 'OTHER'
    end as remote_artifact_source
  from parsed_data
)

select * from final_data
{% endmacro %}
