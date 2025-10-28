with source as (

    select * from {{ source('financeiro', 'orders') }}

),

final as (
    select
        o_orderkey,
        o_custkey,
        o_totalprice
    from source

)

select * from final
