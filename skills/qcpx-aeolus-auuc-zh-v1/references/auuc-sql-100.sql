WITH expanded AS (
  SELECT arrayJoin([20,25,30,35,40]) AS treatment,
    extra_int{'coupon_discount_rate'} AS actual_discount,
    label{'head_68'} AS y,
    multiIf(
      treatment=20,predict{'head_9'}-predict{'head_8'},
      treatment=25,predict{'head_10'}-predict{'head_8'},
      treatment=30,predict{'head_11'}-predict{'head_8'},
      treatment=35,predict{'head_12'}-predict{'head_8'},
      predict{'head_13'}-predict{'head_8'}
    ) AS score,
    uid
  FROM reckon.deep_insight2_sail
  WHERE toDate(server_time) BETWEEN toDate('2026-09-01') AND toDate('2026-09-10')
    AND server_time <= 1789047442
    AND model_name='shop_qcpx_t3_sipw_0813_streaming_r6641741_0'
    AND toDate(req_time) BETWEEN toDate('2026-09-01') AND toDate('2026-09-10')
    AND predict{'head_5'}=1
    AND extra_int{'coupon_discount_rate'} IN (15,20,25,30,35,40)
    AND isNotNull(label{'head_68'}) AND sample_rate{'head_68'}>0
), paired AS (
  SELECT * FROM expanded WHERE actual_discount=15 OR actual_discount=treatment
), ranked AS (
  SELECT treatment,actual_discount,y,score,
    row_number() OVER (PARTITION BY treatment ORDER BY score DESC,uid ASC) AS rn,
    count() OVER (PARTITION BY treatment) AS total_n
  FROM paired
), bucketed AS (
  SELECT treatment,least(100,intDiv((rn-1)*100,total_n)+1) AS bucket_100,actual_discount,y,score
  FROM ranked
)
SELECT treatment,bucket_100,count() AS n,
  countIf(actual_discount=treatment) AS treatment_n,
  countIf(actual_discount=15) AS control_n,
  sumIf(y,actual_discount=treatment) AS treatment_positive,
  sumIf(y,actual_discount=15) AS control_positive,
  avg(score) AS avg_score,min(score) AS min_score,max(score) AS max_score
FROM bucketed
GROUP BY treatment,bucket_100
ORDER BY treatment,bucket_100