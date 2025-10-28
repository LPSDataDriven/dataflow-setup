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
# macOS
brew install direnv
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

- Dependências principais (`[project].dependencies`):
  - `dbt-core`, `dbt-snowflake`: base do dbt e adaptador Snowflake
  - `pre-commit`, `sqlfluff`: qualidade e lint de SQL
  - `recce`: ferramenta de QA para dados
  - `pandas`: utilidades de manipulação de dados
  - `snowflake-snowpark-python`, `snowflake-connector-python[pandas]`: integração com Snowflake
  - `cryptography`: suporte a chaves RSA
- Dev dependencies (`[tool.uv].dev-dependencies`): `pytest`, `black`, `isort`, `flake8`, etc.
- Formatadores: configurações de `black` e `isort`.

Após alterações no `pyproject.toml`, rode:
```bash
uv pip install -e .
```

## Estrutura sugerida do repositório

Exemplo mínimo (ajuste conforme a necessidade):
```
.
├── .dbt/
│   └── profiles.yml               # perfis do dbt (NÃO commitar credenciais reais)
├── models/                        # modelos dbt (staging, marts, etc.)
├── snapshots/
├── seeds/
├── analyses/
├── macros/
├── snowflake_utils/               # utilitários Python para Snowflake/Snowpark
├── dags/                          # DAGs do Airflow (ex.: execução de dbt)
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

2) Crie/configure `~/.dbt/profiles.yml` OU use uma pasta `.dbt/` no repositório com `profiles.yml` (como neste template). Exemplo de autenticação via chave RSA:
```yaml
my_dbt_project:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: ${SNOWFLAKE_ACCOUNT}
      user: ${SNOWFLAKE_USER}
      role: ${SNOWFLAKE_ROLE}
      database: ${SNOWFLAKE_DATABASE}
      warehouse: ${SNOWFLAKE_WAREHOUSE}
      schema: ${SNOWFLAKE_SCHEMA}
      authenticator: rsa_key_pair
      private_key_path: ${SNOWFLAKE_PRIVATE_KEY_PATH}
      client_session_keep_alive: true
```

3) Chave RSA no Snowflake
- Gere um par de chaves RSA localmente e configure a chave pública no usuário Snowflake.
- Armazene o caminho da chave privada em `${SNOWFLAKE_PRIVATE_KEY_PATH}` no `.env`.

4) Verifique a instalação e a conexão
```bash
dbt --version
dbt debug
dbt build
```

## Qualidade de código: pre-commit e sqlfluff

1) Garanta que os arquivos `.pre-commit-config.yaml` e `.sqlfluff` existam e reflitam suas regras.

2) Instale e habilite os hooks
```bash
pre-commit --version
pre-commit install
```
Após isso, os hooks rodam automaticamente nos commits.

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
uv venv --python=3.12
uv pip install -e .
uv pip install -e ".[dev]"
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
