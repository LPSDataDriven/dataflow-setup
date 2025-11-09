# Explicação Detalhada do docker-compose.yml

## Relação entre Dockerfile e docker-compose.yml

### Diferença Fundamental

- **Dockerfile**: Define **COMO construir** uma imagem Docker (receita da imagem)
  - Instala dependências (UV, pacotes do `pyproject.toml`)
  - Configura ambiente base
  - **Resultado**: Uma **imagem Docker** (template imutável)

- **docker-compose.yml**: Define **COMO usar** a imagem e orquestrar containers
  - Define quais containers rodar
  - Configura comandos, volumes, variáveis de ambiente
  - **Resultado**: **Containers rodando** (instâncias da imagem)

### Como Se Relacionam

O `docker-compose.yml` **usa** o Dockerfile para construir a imagem:

```yaml
airflow-init:
  build:
    context: .
    dockerfile: airflow/Dockerfile  # ← Referencia o Dockerfile
  image: dataflow-airflow:latest    # ← Imagem resultante
```

**Fluxo**:
1. `docker-compose build` → Lê `docker-compose.yml` → Encontra `Dockerfile` → Constrói imagem
2. `docker-compose up` → Usa imagem construída + configurações do compose → Cria containers

**Divisão de Responsabilidades**:
- **Dockerfile**: Instala o que vai na imagem (dependências, código)
- **docker-compose.yml**: Configura como usar a imagem (comandos diferentes, volumes, ambiente)

**Exemplo**: A mesma imagem `dataflow-airflow:latest` é usada por:
- `airflow-scheduler` → roda `command: ["airflow", "scheduler"]`
- `airflow-webserver` → roda `command: ["airflow", "webserver"]`

Ambos usam a **mesma imagem**, mas executam **comandos diferentes**.

---

## O que é Docker Compose?

**Docker Compose** é uma ferramenta para definir e executar aplicações Docker multi-container. Um arquivo `docker-compose.yml` descreve:

- **Serviços** (containers): quais containers rodar
- **Volumes**: onde persistir dados
- **Networks**: como os containers se comunicam
- **Dependências**: ordem de inicialização

## Quando é Executado?

O docker-compose é executado **manualmente** no seu ambiente local:

```bash
# Iniciar todos os serviços
docker-compose up -d

# Parar todos os serviços
docker-compose down

# Ver logs
docker-compose logs -f airflow-scheduler

# Rebuild se mudar Dockerfile
docker-compose build
```

**Em produção** (AWS ECS/EKS), você **NÃO usa docker-compose**. Usa:
- **ECS**: Task definitions
- **EKS**: Kubernetes manifests
- As imagens do ECR são usadas diretamente

## Estrutura do Arquivo

### 1. Serviço: `postgres`

```yaml
postgres:
  image: postgres:16-alpine
```

**O que faz**: Banco de dados PostgreSQL para o Airflow armazenar seus metadados (DAGs, histórico de execuções, usuários, etc.)

**Detalhes**:
- **`image`**: Usa imagem oficial do PostgreSQL versão 16 (alpine = menor tamanho)
- **`environment`**: Configura usuário, senha e database
- **`ports`**: Expõe porta 5432 do container para a porta 5432 do host (você pode acessar via `localhost:5432`)
- **`volumes`**: `airflow-postgres-data:/var/lib/postgresql/data`
  - Este é um **volume nomeado** (não um bind mount)
  - `airflow-postgres-data` é criado pelo Docker e persiste mesmo se você remover o container
  - `/var/lib/postgresql/data` é onde o PostgreSQL armazena os dados **dentro do container**
  - **Por que isso é importante**: Se você rodar `docker-compose down`, os dados do banco **NÃO são perdidos** porque estão em um volume Docker
- **`healthcheck`**: Verifica se o PostgreSQL está pronto antes de outros serviços iniciarem

**Padrão?** ✅ Sim, essa estrutura é padrão para PostgreSQL em Docker

---

### 2. Serviço: `airflow-init`

```yaml
airflow-init:
  build:
    context: .
    dockerfile: airflow/Dockerfile
```

**O que faz**: Inicializa o banco de dados do Airflow (cria tabelas, usuário admin). **Roda apenas uma vez** e depois termina.

**Detalhes**:
- **`build`**:
  - `context: .` = pasta raiz do projeto (onde está o `pyproject.toml`)
  - `dockerfile: airflow/Dockerfile` = caminho para o Dockerfile
  - Isso constrói a imagem `dataflow-airflow:latest`
- **`depends_on`**:
  - Espera o PostgreSQL estar **saudável** (`service_healthy`) antes de iniciar
  - Garante que o banco está pronto antes de criar tabelas
- **`command`**:
  - `airflow db init` = cria todas as tabelas no banco
  - `airflow users create` = cria usuário admin
  - `|| true` = não falha se o usuário já existe (útil para reruns)
- **`volumes`**:
  - **Bind mounts** (mapeamento direto): `./airflow/dags:/opt/airflow/dags`
  - `./airflow/dags` = pasta no seu **computador local**
  - `/opt/airflow/dags` = pasta **dentro do container**
  - **O que isso significa**: Quando você edita um DAG em `./airflow/dags/main.py` no seu computador, a mudança é **instantânea** no container (sem rebuild)

**Volumes explicados em detalhes**:

```yaml
volumes:
  - ./airflow/dags:/opt/airflow/dags           # Bind mount: DAGs locais → container
  - ./dbt:/opt/airflow/dbt                     # Bind mount: Projeto dbt → container
  - ./.dbt:/opt/airflow/.dbt                   # Bind mount: Profiles dbt → container
  - ./logs:/opt/airflow/logs                   # Bind mount: Logs do Airflow → pasta local
  - ./plugins:/opt/airflow/plugins             # Bind mount: Plugins customizados
  - ./dataflow:/opt/airflow/dataflow           # Bind mount: Módulo Python (dbt_utils)
  - ./.env:/opt/airflow/.env:ro                # Bind mount: Variáveis de ambiente (read-only)
```

**Tipos de volumes**:

1. **Bind mounts** (`./pasta:/caminho/container`):
   - Mapeia diretamente uma pasta do seu computador para o container
   - Mudanças são instantâneas (útil para desenvolvimento)
   - Exemplo: `./airflow/dags:/opt/airflow/dags`

2. **Named volumes** (`nome-volume:/caminho/container`):
   - Gerenciados pelo Docker
   - Persistem mesmo após `docker-compose down`
   - Exemplo: `airflow-postgres-data:/var/lib/postgresql/data`

**Padrão?** ✅ Sim, `airflow-init` é uma prática padrão no Airflow 2.x

---

### 3. Serviço: `airflow-scheduler`

```yaml
airflow-scheduler:
  image: dataflow-airflow:latest
  command: ["airflow", "scheduler"]
```

**O que faz**: **Motor do Airflow**. Fica monitorando os DAGs, agendando tarefas e orquestrando execuções.

**Detalhes**:
- **`image`**: Usa a mesma imagem que foi construída (reutiliza, não rebuild)
- **`depends_on`**:
  - Espera `airflow-init` **terminar com sucesso** (`service_completed_successfully`)
  - Espera PostgreSQL estar saudável
- **`restart: unless-stopped`**: Reinicia automaticamente se o container parar (exceto se você parar manualmente)
- **`command`**: Roda o scheduler do Airflow
- **`volumes`**: Mesmos volumes do `airflow-init` (compartilha DAGs, dbt, etc.)

**Por que precisa dos mesmos volumes?**
- Precisa ler os DAGs de `./airflow/dags`
- Precisa acessar o projeto dbt em `./dbt`
- Precisa acessar `dataflow/` (módulo Python com `dbt_utils`)
- Precisa ler `.env` para variáveis de ambiente

**Padrão?** ✅ Sim, esse é o padrão de deployment do Airflow

---

### 4. Serviço: `airflow-webserver`

```yaml
airflow-webserver:
  image: dataflow-airflow:latest
  command: ["airflow", "webserver"]
  ports:
    - "8080:8080"
```

**O que faz**: Interface web do Airflow. Você acessa em `http://localhost:8080`.

**Detalhes**:
- **`ports`**: `"8080:8080"` = porta do host:porta do container
  - `localhost:8080` no seu computador → porta 8080 no container
- **`restart: unless-stopped`**: Reinicia automaticamente
- **`depends_on`**: Mesmas dependências do scheduler

**Padrão?** ✅ Sim, padrão para Airflow

---

## Variáveis de Ambiente Explicadas

### `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`
```yaml
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
```
**O que é**: String de conexão com o PostgreSQL
- `postgresql+psycopg2://` = driver de conexão
- `airflow:airflow` = usuário:senha
- `@postgres:5432` = host:porta (`postgres` é o nome do serviço no docker-compose!)
- `airflow` = nome do database

**Por que `postgres` funciona?**
Docker Compose cria uma **rede interna** onde todos os serviços podem se comunicar pelo **nome do serviço**. Então `postgres` resolve para o IP do container PostgreSQL.

### `DBT_PROFILES_DIR`
```yaml
DBT_PROFILES_DIR: /opt/airflow/.dbt
```
**O que é**: Caminho onde o dbt procura o `profiles.yml`

**Está correto?** ✅ Sim!
- No container: `/opt/airflow/.dbt`
- No seu computador: `./.dbt` (mapeado via volume)
- O dbt dentro do container procura em `/opt/airflow/.dbt/profiles.yml`

### `PYTHONPATH`
```yaml
PYTHONPATH: /opt/airflow:/opt/airflow/dataflow
```
**O que é**: Onde o Python procura módulos
- Permite que os DAGs façam `from dbt_utils.connector import ...`
- Porque `dataflow/` está em `/opt/airflow/dataflow` (via volume mount)

**Está correto?** ✅ Sim!

### `DBT_TARGET`
```yaml
DBT_TARGET: dev
```
**O que é**: Qual target do dbt usar (dev, stage, prod, etc. - definidos em `.dbt/profiles.yml`)

**Está correto?** ✅ Sim para desenvolvimento local

---

## Paths no Container

Todos os caminhos estão **corretos** porque são mapeados via volumes:

| No seu computador | No container | Para que serve |
|-------------------|--------------|----------------|
| `./airflow/dags` | `/opt/airflow/dags` | DAGs do Airflow |
| `./dbt` | `/opt/airflow/dbt` | Projeto dbt |
| `./.dbt` | `/opt/airflow/.dbt` | Profiles dbt (profiles.yml) |
| `./dataflow` | `/opt/airflow/dataflow` | Módulo Python (dbt_utils) |
| `./logs` | `/opt/airflow/logs` | Logs do Airflow |
| `./plugins` | `/opt/airflow/plugins` | Plugins customizados |
| `./.env` | `/opt/airflow/.env` | Variáveis de ambiente |

**Por que `/opt/airflow/`?**
Essa é a **pasta padrão** da imagem oficial do Airflow. Todos os caminhos padrão do Airflow usam `/opt/airflow/`.

---

## É uma Estrutura Padrão?

✅ **SIM!** Esta estrutura segue as melhores práticas do Airflow:

1. ✅ **Separação de serviços**: Postgres separado do Airflow
2. ✅ **Healthchecks**: Garantem ordem correta de inicialização
3. ✅ **Init container**: Padrão do Airflow 2.x
4. ✅ **Bind mounts para desenvolvimento**: Permite editar código sem rebuild
5. ✅ **Named volumes para dados**: Persiste dados do banco

---

## Fluxo de Execução

Quando você roda `docker-compose up -d`:

1. **PostgreSQL inicia** → Aguarda healthcheck passar
2. **Airflow-init inicia** → Cria tabelas e usuário admin → **Termina**
3. **Airflow-scheduler inicia** → Fica rodando continuamente
4. **Airflow-webserver inicia** → Fica rodando continuamente → Disponível em `localhost:8080`

---

## Quando Usar?

- ✅ **Desenvolvimento local**: Editar DAGs e testar
- ✅ **Testes**: Validar pipelines antes de produção
- ❌ **Produção**: Use ECS/EKS com imagens do ECR

---

## Comandos Úteis

```bash
# Ver status de todos os serviços
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f airflow-scheduler

# Parar tudo
docker-compose down

# Parar e remover volumes (⚠️ apaga dados do banco)
docker-compose down -v

# Rebuild se mudou Dockerfile
docker-compose build airflow-init

# Executar comando dentro de um container
docker-compose exec airflow-scheduler airflow dags list
```
