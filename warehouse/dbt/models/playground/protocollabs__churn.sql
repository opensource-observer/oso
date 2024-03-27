WITH queries AS (

  SELECT to_name,
               year,
               month,
               contributors,
               MAX(lost) AS lost,
               MAX(gained) AS gained,
               COUNT(DISTINCT(cum_contributors)) AS cum_contributors_count,
               lag_contributors,
               STRING_AGG(DISTINCT(cum_contributors), ', ') AS cum_contributors,
               lag_contributors_count,
               contributors_count
        FROM (
                SELECT to_name,
                       year,
                       contributors,
                       contributors_count,
                       lag_contributors,
                       lost,
                       gained,
                       month,
                       cum_contributors,
                       lag_contributors_count
                FROM (
                  SELECT to_name,
                               year,
                               month,
                               STRING_AGG(contributors, ', ') OVER (PARTITION BY to_name,
                                                                                 year
                                                                    ORDER BY month rows between unbounded preceding and current row) AS cum_contributors,
                               contributors,
                               COUNT(SPLIT(contributors)) AS contributors_count,
                               COALESCE(SUM(lost), 0) AS lost,
                               gained,
                               STRING_AGG(DISTINCT(lag_contributors), ', ') AS lag_contributors,
                               COUNT(lag_contributors) AS lag_contributors_count
                        FROM (
                                SELECT *,
                                      (CASE WHEN strpos(contributors, lag_contributors) > 0 THEN 0
                                        ELSE 1 END) AS lost
                                FROM (
                                        SELECT to_name,
                                               year,
                                               month,
                                               lag_contributors,
                                               contributors,
                                               gained
                                        FROM (
                                                SELECT to_name,
                                                       year,
                                                       month,
                                                       COALESCE(lag_contributors, '') AS lag_contributors,
                                                       COALESCE(SUM(gained), 0) AS gained,
                                                       STRING_AGG(contributors, ', ') AS contributors
                                                FROM (
                                                        SELECT *,
                                                                (CASE WHEN strpos(lag_contributors, contributors) > 0 THEN 0
                                                                      ELSE 1 END) AS gained
                                                        FROM (
                                                              SELECT to_name,
                                                                        year,
                                                                        month,
                                                                        contributors,
                                                                        lag_contributors
                                                                FROM (
                                                                        SELECT *,
                                                                               STRING_AGG(contributors, ', ') OVER (PARTITION BY to_name, year, month
                                                                                                                   ORDER BY month rows between unbounded preceding and current row) AS cum_contributors
                                                                                                FROM   (
                                                                                                          SELECT *,
                                                                                                               LAG(month, 1) OVER (PARTITION BY to_name ORDER BY month) lag_month,
                                                                                                               LAG(contributors, 1) OVER (PARTITION BY to_name ORDER BY month) lag_contributors
                                                                                                          FROM   (
                                                                                                                    SELECT to_name,
                                                                                                                            year,
                                                                                                                            month,
                                                                                                                            STRING_AGG(DISTINCT(from_name), ', ') AS contributors
                                                                                                                    FROM   (
                                                                                                                      SELECT *,
                                                                                                                               EXTRACT(isoyear FROM time) AS year,
                                                                                                                               EXTRACT(week FROM time) AS week,
                                                                                                                               EXTRACT(day FROM time) AS day,
                                                                                                                               EXTRACT(month FROM time) AS month
                                                                                                                      FROM {{ ref("int_events") }} AS q1) AS q2
                                                                                                                    GROUP BY to_name, year, month
                                                                                                                    ORDER BY to_name, year, month) AS q3) AS q4) AS q5
                                                                                                    CROSS JOIN UNNEST(SPLIT(contributors)) AS contributors ) AS q6 ) AS q7
                                                                                        GROUP BY to_name, year, lag_contributors, month
                                                                                        ORDER BY to_name, year, month )  AS q11
                                                                                        CROSS JOIN UNNEST(SPLIT(lag_contributors)) AS lag_contributors ) AS q12 ) AS q13
                                                                          GROUP BY to_name, year, gained, contributors, month
                                                                          ORDER BY to_name, year, month ) AS q14
                                                                          CROSS JOIN UNNEST(SPLIT(cum_contributors))) AS q15
                                                            GROUP BY to_name, year, contributors, lag_contributors, contributors_count, lag_contributors_count, month
                                                            ORDER BY to_name, year, month
 )


 SELECT to_name,
        year,
        month,
        lost,
        gained,
        cum_contributors,
        cum_contributors_count,
        lag_contributors,
        lag_contributors_count,
        contributors,
        contributors_count,
        (CAST(lost AS FLOAT64)/cum_contributors_count)*100 AS churn_prior,
        ((CAST(cum_contributors_count AS FLOAT64) - CAST(contributors_count AS FLOAT64))/CAST(cum_contributors_count AS FLOAT64))*100 AS churn_total
 FROM queries
