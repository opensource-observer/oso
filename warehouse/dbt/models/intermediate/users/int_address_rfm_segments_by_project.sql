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
    artifact_id,
    project_id,
    transaction_count,
    DATE_DIFF(CURRENT_TIMESTAMP(), last_transaction_time, day)
      as days_since_last_activity
  from {{ ref('int_addresses_to_project') }}
),

user_stats as (
  select
    artifact_id,
    project_id,
    transaction_count,
    days_since_last_activity,
    COUNT(distinct project_id) as project_count
  from user_history
  group by
    artifact_id,
    project_id,
    transaction_count,
    days_since_last_activity
),

rfm_components as (
  select
    artifact_id,
    project_id,
    case
      when days_since_last_activity < 7 then 5
      when days_since_last_activity < 30 then 4
      when days_since_last_activity < 90 then 3
      when days_since_last_activity < 180 then 2
      else 1
    end as rfm_recency,
    case
      when transaction_count = 1 then 1
      when transaction_count < 10 then 2
      when transaction_count < 100 then 3
      when transaction_count < 1000 then 4
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
  artifact_id,
  project_id,
  rfm_recency,
  rfm_frequency,
  rfm_ecosystem,
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
