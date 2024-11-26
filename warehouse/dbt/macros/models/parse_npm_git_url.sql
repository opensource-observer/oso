{% macro parse_npm_git_url(key, source) %}

  with parsed_data as (
    select
      *,

      case
        when regexp_contains({{ key }}, r'#') then 
          regexp_replace({{ key }}, r'#.*$', '')
        when regexp_contains({{ key }}, r'^git\+ssh://') then 
          regexp_replace({{ key }}, r'^git\+ssh://([^@]+)@', 'https://')
        when regexp_contains({{ key }}, r'^git@') then 
          regexp_replace({{ key }}, r'^git@(.*?):', 'https://\\1/')
        when regexp_contains({{ key }}, r'^git\+https://') then 
          regexp_replace({{ key }}, r'^git\+', '')
        when regexp_contains({{ key }}, r'^https?://') then 
          {{ key }}
        when regexp_contains({{ key }}, r'^[^:/]+\.[^:/]+/') then 
          concat('https://', {{ key }})
        else null
      end as remote_url,

      regexp_extract(
        case
          when regexp_contains({{ key }}, r'#') then 
            regexp_replace({{ key }}, r'#.*$', '')
          when regexp_contains({{ key }}, r'\.git$') then 
            regexp_replace({{ key }}, r'\.git$', '')
          else {{ key }}
        end,
        r'/([^/]+)(?:\.git)?$'
      ) as remote_name,

      regexp_extract(
        case
          when regexp_contains({{ key }}, r'#') then 
            regexp_replace({{ key }}, r'#.*$', '')
          when regexp_contains({{ key }}, r'^git@') then 
            regexp_replace({{ key }}, r'^git@(.*?):', 'https://\\1/')
          when regexp_contains({{ key }}, r'^git\+ssh://') then 
            regexp_replace({{ key }}, r'^git\+ssh://', 'https://')
          else {{ key }}
        end,
        r'https?:\/\/[^\/]+\/([^\/]+)\/[^\/]+'
      ) as remote_namespace,

      case
        when regexp_contains({{ key }}, r'github\.com') then 'GITHUB'
        when regexp_contains({{ key }}, r'gitlab\.com') then 'GITLAB'
        when regexp_contains({{ key }}, r'bitbucket\.org') then 'BITBUCKET'
        else 'OTHER'
      end as remote_source_id

    from {{ source }}
  ),

  final_data as (
    select
      * except(remote_url),
      case
        when regexp_contains(remote_url, r'\.git$') then remote_url
        else concat(remote_url, '.git')
      end as remote_url
    from parsed_data
  )

  select * from final_data

{% endmacro %}
