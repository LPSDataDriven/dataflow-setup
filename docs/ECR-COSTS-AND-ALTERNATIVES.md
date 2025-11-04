# Custos ECR e Alternativas Gratuitas para Projeto de Treinamento

## Custos do AWS ECR

### Preços ECR (2024)

#### 1. **Storage** (armazenamento de imagens)
- **Primeiros 500MB por mês**: **GRATUITO** ✅
- **Depois disso**: ~**$0.10 por GB/mês**
- **Deduplicação**: ECR deduplica camadas, economizando espaço

#### 2. **Data Transfer**
- **Inbound** (push para ECR): **GRATUITO** ✅
- **Outbound** (pull do ECR):
  - **Primeiro 1GB/mês**: **GRATUITO** ✅
  - **Depois disso**: ~$0.09 por GB

#### 3. **API Requests**
- Put, Get, BatchGet: **GRATUITO** ✅

### Estimativa para Projeto de Treinamento

**Cenário típico**:
- Imagem Docker: ~500MB-1GB (Airflow + dependências)
- Push inicial: 1 imagem = ~500MB
- Pulls: 2-3 pulls por mês para testes

**Custo mensal estimado**:
- Storage: **$0.00** (dentro do free tier de 500MB) ✅
- Data transfer: **$0.00** (dentro do free tier de 1GB) ✅
- **Total: $0.00/mês** ✅

**Cenário se passar do free tier**:
- Storage: 1GB = $0.10/mês
- Data transfer: 2GB = ~$0.09 (primeiro GB grátis) = **$0.09/mês**
- **Total: ~$0.19/mês** 💰

### Conclusão sobre ECR

✅ **ECR é praticamente GRATUITO para projetos de treinamento**!

- Free tier cobre projetos pequenos/médios
- Mesmo passando, custo é muito baixo (~$0.20/mês)
- Integração nativa com AWS (ECS, EKS, Lambda)

---

## Alternativas Gratuitas

### 1. GitHub Container Registry (ghcr.io) ⭐ RECOMENDADO

**Custos**: **100% GRATUITO** (ilimitado para repositórios públicos)

**Vantagens**:
- ✅ Totalmente gratuito
- ✅ Integrado com GitHub (mesmo login)
- ✅ Público ou privado
- ✅ Funciona com docker-compose
- ✅ Funciona com ECS/EKS também

**Desvantagens**:
- ⚠️ Não é AWS nativo (mas funciona bem)

**Uso**:
```bash
# Build e push
docker build -f airflow/Dockerfile -t ghcr.io/seu-usuario/dataflow-airflow:latest .
echo $GITHUB_TOKEN | docker login ghcr.io -u seu-usuario --password-stdin
docker push ghcr.io/seu-usuario/dataflow-airflow:latest

# Pull
docker pull ghcr.io/seu-usuario/dataflow-airflow:latest
```

**Para projeto de treinamento**: ⭐ **Excelente opção!**

---

### 2. Docker Hub

**Custos**:
- **Público**: Gratuito (ilimitado)
- **Privado**: Gratuito até 1 imagem, depois $5/mês

**Vantagens**:
- ✅ Gratuito para imagens públicas
- ✅ Mais popular/conhecido
- ✅ Fácil de usar

**Desvantagens**:
- ⚠️ Rate limiting (100 pulls/6h para contas gratuitas)
- ⚠️ Privado tem limites

**Uso**:
```bash
docker build -t seu-usuario/dataflow-airflow:latest .
docker login
docker push seu-usuario/dataflow-airflow:latest
```

**Para projeto de treinamento**: ✅ Boa opção se imagens forem públicas

---

### 3. Apenas Local (docker-compose)

**Custos**: **$0.00** ✅

**Para que serve**:
- Desenvolvimento local
- Treinamento de pipeline end-to-end localmente
- Não precisa de registry se tudo roda localmente

**Limitações**:
- ❌ Não simula produção real
- ❌ Não aprende ECR/registry

**Para projeto de treinamento**: ✅ Ok para aprender Docker/Airflow, mas não aprende registry

---

## Recomendação para Projeto de Treinamento

### Opção 1: GitHub Container Registry (ghcr.io) ⭐ **MELHOR PARA TREINAMENTO**

**Por quê**:
1. ✅ **100% gratuito** (ilimitado)
2. ✅ Ensina conceitos de registry/container registry
3. ✅ Similar ao ECR (conceitos transferem)
4. ✅ Integrado com GitHub (que você já usa)
5. ✅ Pode usar depois em ECS/EKS também

**Quando usar**: Se quiser aprender registry sem custo

---

### Opção 2: AWS ECR 💰 **PRÁTICAMENTE GRATUITO**

**Por quê**:
1. ✅ **Praticamente grátis** (free tier cobre)
2. ✅ **AWS nativo** (aprende stack AWS completa)
3. ✅ Real production-ready
4. ✅ Mesmo se passar do free tier, ~$0.20/mês

**Quando usar**: Se quiser aprender stack AWS completa

**Risco**: Se exceder free tier, custo mínimo de ~$0.20/mês

---

### Opção 3: Híbrido (Recomendado)

**Estratégia**:
1. **Desenvolvimento**: docker-compose local ($0)
2. **Demonstração**: GitHub Container Registry ($0)
3. **Produção (se necessário)**: ECR (~$0.20/mês se passar free tier)

**Vantagens**:
- ✅ Aprende múltiplas ferramentas
- ✅ Custo zero na maioria dos casos
- ✅ Flexibilidade

---

## Comparação Rápida

| Opção | Custo Mensal | Integração AWS | Aprende Registry | Realismo Produção |
|-------|--------------|----------------|------------------|-------------------|
| **ECR** | ~$0.00-$0.20 | ✅ Nativo | ✅ Sim | ✅ Sim |
| **ghcr.io** | $0.00 | ⚠️ Manual | ✅ Sim | ✅ Sim |
| **Docker Hub** | $0.00 | ⚠️ Manual | ✅ Sim | ⚠️ Parcial |
| **Apenas Local** | $0.00 | ❌ Não | ❌ Não | ❌ Não |

---

## Recomendação Final

Para um **projeto de treinamento end-to-end** com objetivo de aprender pipeline completo:

### **Use GitHub Container Registry (ghcr.io)** ⭐

**Razões**:
1. ✅ **100% gratuito** garantido
2. ✅ Ensina conceitos de container registry
3. ✅ Conceitos são transferíveis para ECR
4. ✅ Não há risco de custos inesperados
5. ✅ Funciona perfeitamente para treinamento

**Depois**, quando quiser praticar AWS específico:
- Use ECR (que praticamente também é grátis no free tier)
- Conceitos aprendidos no ghcr.io aplicam ao ECR

---

## Próximos Passos

Se escolher **ghcr.io**, posso:
1. Atualizar scripts `build-ecr.sh` → `build-ghcr.sh`
2. Criar script `setup-ghcr.sh` (não precisa, só criar PAT no GitHub)
3. Atualizar documentação

Se escolher **ECR**:
- Manter scripts atuais
- Adicionar avisos sobre free tier
- Documentar como monitorar custos

**Qual prefere?**
