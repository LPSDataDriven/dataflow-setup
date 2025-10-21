with customers as (
    select *
    from {{ ref('stg_customers') }}
),
orders as (
    select *
    from {{ ref('stg_orders') }}
)

select
    c.C_CUSTKEY,
    c.C_NAME,
    o.O_ORDERKEY,
    o.O_TOTALPRICE
from customers as c
join orders as o
    on c.C_CUSTKEY = o.O_CUSTKEY
limit 100