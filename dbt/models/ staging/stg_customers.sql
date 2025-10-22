-- este arquivo vai gerar uma tabela chamada stg_customers no DW (Data Warehouse)
with source as (
    select * from {{ source('financeiro', 'CUSTOMER') }} -- source (fonte de dados, tabela)
) -- Pega todas as colunas da tabela customers 

-- select C_NAME, C_CUSTKEY, O_TOTALPRICE -- seleciona as colunas que desejamos

--from source -- from (de onde vem os dados)

select * from source -- select * from (tabela)