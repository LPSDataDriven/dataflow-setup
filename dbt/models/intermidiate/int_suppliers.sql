with supplier as (

    select * from {{ ref('stg_supplier') }}

),

nation as (

    select * from {{ ref('stg_nation') }}

),

final as (

    select
        supplier.s_suppkey,
        supplier.s_nationkey,
        nation.n_name
    from supplier
    inner join nation
        on supplier.s_nationkey = nation.n_nationkey
    limit 100

)

select * from final
