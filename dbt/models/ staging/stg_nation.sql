with source as (

    select * from {{ source('financeiro', 'nation') }}

),

final as (

    select
        n_nationkey,
        n_name,
        n_regionkey,
        n_comment
    from source

)

select * from final
