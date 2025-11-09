## Base de setup para projeto de dados com dbt, Snowflake, Airflow e AWS

Este repositório é um template de partida para criar um projeto do zero contemplando:

- dbt Core (modelagem, testes, documentação)
- Snowflake (warehouse, Snowpark, `snowflake-connector-python`)
- Airflow (orquestração local com Docker)
- AWS (S3 para artefatos/logs, Secrets Manager, IAM)

O objetivo é fornecer um guia de setup inicial robusto e reaproveitável, além de uma estrutura base para evolução do projeto.

### Sumário

- Visão geral e pré‑requisitos
- Setup de ambiente com `uv` e `direnv`
- Explicação do `pyproject.toml`
- Estrutura sugerida do repositório
- Configuração do dbt + Snowflake (`profiles.yml`, chave RSA, conexão)
- Qualidade de código: `pre-commit` e `sqlfluff`
- Integração com Airflow e AWS
- Comandos úteis
- Troubleshooting

## Visão geral e pré‑requisitos

Pré‑requisitos recomendados:

- Python 3.12+
- Git
- [uv](https://docs.astral.sh/uv/) para gerenciar virtualenv e dependências
- [direnv](https://direnv.net/) para carregar `.env` e ativar o venv automaticamente
- Acesso a uma conta Snowflake com role para criação/leitura de objetos
- Conta AWS (opcional nesta fase) com acesso a S3 e Secrets Manager

## Setup de ambiente (uv + direnv)

1) Crie/clonar o repositório
```bash
git clone git@github.com:<accountName>/<repoName>.git
cd <repoName>
```

2) Instale o `uv` (se necessário)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Outras opções: consulte [instalação do uv](https://docs.astral.sh/uv/getting-started/installation/).

3) Crie o ambiente virtual
```bash
uv venv --python=3.12
```
Isso criará a pasta `.venv` na raiz do projeto.

4) Ative o ambiente virtual (manual, se não usar direnv)
```bash
source .venv/bin/activate
```

5) Variáveis de ambiente e `direnv`
- Crie um arquivo `.env` na raiz (baseado em `.env.example` se existir) com as variáveis sensíveis (Snowflake, AWS, etc.).
- Crie um `.envrc` com o conteúdo abaixo:
```bash
dotenv
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi
unset PS1
```
Instale o `direnv` e habilite no shell:
```bash
# Ubuntu/Debian
sudo apt-get install direnv

# bash
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
# zsh
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

direnv allow
```
Observação: o aviso "PS1 cannot be exported" pode aparecer e é esperado; não impacta o funcionamento.

## `pyproject.toml`: dependências e tooling

Este arquivo centraliza dependências e ferramentas do projeto.

### Estrutura das dependências

**`[project].dependencies`** - Dependências de produção (sempre instaladas):
  - `dbt-core`, `dbt-snowflake`: base do dbt e adaptador Snowflake
  - `pre-commit`, `sqlfluff`: qualidade e lint de SQL
  - `recce`: ferramenta de QA para dados
  - `pandas`: utilidades de manipulação de dados
  - `snowflake-snowpark-python`, `snowflake-connector-python[pandas]`: integração com Snowflake
  - `cryptography`: suporte a chaves RSA

**`[tool.uv].dev-dependencies`** - Dependências de desenvolvimento (apenas para desenvolvimento local):
  - `pytest`, `pytest-mock`, `pytest-cov`, `moto`: testes
  - `black`, `isort`, `flake8`: formatadores e linters
  - `apache-airflow>=2.8.0`: Airflow para desenvolvimento local
  - `awscli`, `aws-sam-cli`: ferramentas AWS para desenvolvimento

### Instalação das dependências

**Para desenvolvimento local** (recomendado):
```bash
uv pip install -e ".[dev]"
```
Instala **todas** as dependências: produção + desenvolvimento (pytest, black, isort, etc.)

**Para produção** (apenas dependências essenciais):
```bash
uv pip install -e .
```
Instala **apenas** as dependências de produção (sem black, isort, pytest, etc.)

### Configurações de formatação

- `[tool.black]`: configuração do Black (formatação automática)
- `[tool.isort]`: configuração do isort (ordenação de imports)

## Estrutura sugerida do repositório

Exemplo mínimo (ajuste conforme a necessidade):
```
.
├── .dbt/
│   └── profiles.yml               # perfis do dbt (NÃO commitar credenciais reais)
├── dbt/                           # projeto dbt
│   ├── dbt_project.yml
│   ├── models/                    # modelos dbt (staging, marts, etc.)
│   ├── snapshots/
│   ├── seeds/
│   ├── analyses/
│   ├── macros/
│   └── tests/
├── dataflow/                      # utilitários Python para Snowflake/Snowpark
├── airflow/                       # configuração do Airflow (Docker, ECR)
│   ├── Dockerfile                 # Imagem Docker usando UV
│   ├── build-ecr.sh              # Script para build/push ECR
│   ├── setup-ecr.sh              # Script para criar repositório ECR
│   └── dags/                      # DAGs do Airflow (ex.: execução de dbt)
├── .sqlfluff
├── .pre-commit-config.yaml
├── .envrc
├── .gitignore
├── pyproject.toml
└── README.md
```

## Configuração dbt + Snowflake

1) Inicialize um projeto dbt (se ainda não existir)
```bash
dbt init my_dbt_project
```

2) Crie/configure `~/.dbt/profiles.yml` OU use uma pasta `.dbt/` no repositório com `profiles.yml` (como neste template). Exemplo de autenticação via chave RSA usando variáveis de ambiente:
```yaml
my_dbt_project:
  target: dev
  outputs:
    # Common Snowflake connection settings
    defaults: &snowflake_defaults
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      private_key_path: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PATH') }}"
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE_DEV') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      client_session_keep_alive: False
      threads: 10
      query_tag: "{{ env_var('SNOWFLAKE_QUERY_TAG') }}"

    dev:
      <<: *snowflake_defaults
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"

    stage:
      <<: *snowflake_defaults
      schema: stage

    # For read-only access to prod for recce
    prod-read-only:
      <<: *snowflake_defaults
      database: "{{ env_var('SNOWFLAKE_DATABASE_PROD') }}"
      schema: prod
```

3) Chave RSA no Snowflake
- Gere um par de chaves RSA localmente e configure a chave pública no usuário Snowflake.
- Armazene o caminho da chave privada em `${SNOWFLAKE_PRIVATE_KEY_PATH}` no `.env`.
- Se a chave privada estiver protegida por senha (recomendado), configure também `${SNOWFLAKE_PRIVATE_KEY_PASSPHRASE}` no `.env` com a senha da chave.

4) Verifique a instalação e a conexão
```bash
dbt --version
dbt debug
dbt build
```

## Qualidade de código: pre-commit e sqlfluff

O [pre-commit](https://pre-commit.com/) é um framework para gerenciar hooks de git que executam verificações antes de cada commit. Ele permite identificar problemas simples (como trailing whitespace, formatação incorreta, problemas de lint) antes da revisão de código, economizando tempo tanto do desenvolvedor quanto do revisor.

1) Garanta que os arquivos `.pre-commit-config.yaml` e `.sqlfluff` existam e reflitam suas regras.

2) Verifique a instalação e configure os hooks do git
```bash
# Verifique se o pre-commit está instalado (já vem com uv pip install -e .)
pre-commit --version

# Instale os hooks do git (isso configura os scripts em .git/hooks/pre-commit)
pre-commit install
```

Após isso, os hooks rodam automaticamente em cada `git commit`. O pre-commit gerencia o download e execução de qualquer hook escrito em qualquer linguagem antes de cada commit.

3) (Opcional) Execute os hooks em todos os arquivos
Quando você adiciona novos hooks, é recomendado executá-los em todos os arquivos do projeto para garantir que tudo está em conformidade:
```bash
pre-commit run --all-files
```

Isso executa todos os hooks configurados em todos os arquivos, não apenas nos arquivos alterados. Durante um commit normal, o pre-commit executa apenas nos arquivos modificados.

4) Executar hooks manualmente
Você também pode executar os hooks manualmente sem fazer commit:
```bash
# Executa apenas nos arquivos staged
pre-commit run

# Executa um hook específico
pre-commit run sqlfluff-lint --all-files
```

## Integração com Airflow e AWS

Esta base não impõe uma stack específica, mas sugere caminhos:

- Airflow local: utilize um `docker-compose` com `webserver`, `scheduler` e `postgres` e a pasta `dags/` deste repositório. Uma DAG típica chama o dbt via CLI (por exemplo, `dbt build`).
- AWS S3: armazene artefatos de execução (logs, manifest.json, run_results.json) e seeds estáticos.
- AWS Secrets Manager: gerencie credenciais (Snowflake, etc.) e injete-as via conexão/variáveis do Airflow.
- Airflow gerenciado: para produção, considere Airflow em ECS/EKS ou outras soluções gerenciadas. Ajuste a image para incluir `dbt-core`/`dbt-snowflake`.

Pontos de atenção:
- Conexão do Airflow com Snowflake deve usar a mesma modalidade de autenticação (idealmente chave RSA ou usuário/senha rotacionada via Secrets Manager).
- Garanta que as roles Snowflake e permissões IAM (S3/Secrets) estejam corretas.

## Comandos úteis

Ambiente e dependências:
```bash
# Criar ambiente virtual
uv venv --python=3.12

# Para desenvolvimento (instala tudo: produção + dev)
uv pip install -e ".[dev]"

# Para produção (apenas dependências essenciais)
uv pip install -e .
```

dbt básico:
```bash
dbt debug
dbt deps
dbt seed
dbt run
dbt test
dbt build
dbt docs generate && dbt docs serve
```

Formatadores e lint:
```bash
black .
isort .
flake8
sqlfluff lint
sqlfluff fix
```

Snowflake (Python):
```bash
python -c "from snowflake import connector; print('ok')"
```

## Troubleshooting

- dbt não conecta ao Snowflake: confira `profiles.yml`, variáveis do `.env`, role/warehouse/schema, e se a chave RSA está correta.
- `direnv` não carrega: confirme `direnv allow` e o hook no shell.
- Falha em hooks `pre-commit`: rode os linters localmente para corrigir (`black`, `isort`, `sqlfluff`).
- Incompatibilidade de versão: valide Python 3.12+, versões do `dbt-snowflake` e do conector no `pyproject.toml`.

---

Este README serve como base inicial e pode ser estendido conforme o projeto evolui (monitoramento, CI/CD, testes de dados avançados, etc.).
