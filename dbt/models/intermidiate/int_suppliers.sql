with supplier as (
    select * from {{ ref('stg_supplier') }}
),
nation as (
    select * from {{ ref('stg_nation') }}
)

select
    s.S_SUPPKEY,
    n.N_NAME,
    s.S_NATIONKEY
from supplier as s
join nation as n
    on s.S_NATIONKEY = n.N_NATIONKEY
limit 100