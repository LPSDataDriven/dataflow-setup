with source as (
    select * from {{ source('financeiro', 'ORDERS') }}
)

select O_ORDERKEY, O_CUSTKEY, O_TOTALPRICE from source