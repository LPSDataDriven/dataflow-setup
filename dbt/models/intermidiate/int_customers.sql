with customers as (

    select * from {{ ref('stg_customers') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

final as (

    select
        customers.c_custkey,
        customers.c_name,
        orders.o_orderkey,
        orders.o_totalprice
    from customers
    inner join orders
        on customers.c_custkey = orders.o_custkey
    limit 100

)

select * from final
