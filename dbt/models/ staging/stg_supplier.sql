with source as (
    select * from {{ source('financeiro', 'SUPPLIER') }}
)
-- rename as (NAME as C_NAME, CUSTKEY as C_CUSTKEY, TOTALPRICE as O_TOTALPRICE)

-- select S_NAME, S_SUPPKEY from source
select * from source