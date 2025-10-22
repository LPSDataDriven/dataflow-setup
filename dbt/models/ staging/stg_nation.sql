with source as (
    select * from {{ source('financeiro', 'NATION') }}
)

-- select N_NAME, N_NATIONKEY, N_REGIONKEY

-- from source

select * from source