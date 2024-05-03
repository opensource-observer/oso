{# 
  Onchain address segementation using the RFM model.
  
  RFM stands for Recency, Frequency, and Monetary Value.
  In this version, we adapt the M to represent the 
  number of projects a user has interacted with.
  
  We will consider the following metrics:
  - Recency: Days since last activity
  - Frequency: Total activity
  - Monetary Value: Project count
  
  We will then assign a segment to each user based on these
  metrics.
#}

with user_history as (
  select
    from_id,
    network,
    project_id,
    count_events as total_activity,
    DATE_DIFF(CURRENT_TIMESTAMP(), date_last_txn, day)
      as days_since_last_activity
  from {{ ref('int_addresses') }}
),

user_stats as (
  select
    from_id,
    network,
    project_id,
    total_activity,
    days_since_last_activity,
    COUNT(distinct project_id) as project_count
  from user_history
  group by 1, 2, 3, 4, 5
),

rfm_components as (
  select
    from_id,
    network,
    project_id,
    case
      when days_since_last_activity < 7 then 5
      when days_since_last_activity < 30 then 4
      when days_since_last_activity < 90 then 3
      when days_since_last_activity < 180 then 2
      else 1
    end as rfm_recency,
    case
      when total_activity = 1 then 1
      when total_activity < 10 then 2
      when total_activity < 100 then 3
      when total_activity < 1000 then 4
      else 5
    end as rfm_frequency,
    case
      when project_count = 1 then 1
      when project_count <= 3 then 2
      when project_count <= 10 then 3
      when project_count <= 30 then 4
      else 5
    end as rfm_ecosystem
  from user_stats
)

select
  *,
  case
    when rfm_frequency = 5
      then
        case
          when rfm_recency = 5 then 'Power'
          when rfm_recency = 4 then 'Loyal'
          when rfm_recency = 3 then 'At risk'
          else 'Churned'
        end
    when rfm_frequency = 4
      then
        case
          when rfm_recency >= 4 then 'Loyal'
          when rfm_recency = 3 then 'At risk'
          else 'Churned'
        end
    when rfm_frequency = 3
      then
        case
          when rfm_recency >= 4 then 'Promising'
          when rfm_recency = 3 then 'Needs attention'
          else 'Tourist'
        end
    when rfm_frequency = 2
      then
        case
          when rfm_recency >= 4 then 'Noob'
          else 'Tourist'
        end
    when rfm_frequency = 1 then
      case
        when rfm_recency >= 3 then 'Noob'
        else 'One and done'
      end
  end as user_segment
from rfm_components
