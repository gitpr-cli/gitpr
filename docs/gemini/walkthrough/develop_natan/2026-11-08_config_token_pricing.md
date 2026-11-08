# Walkthrough — Configuração de Taxas de Custo de Token no `gitpr config`

Implementamos os campos de taxas de custo de tokens (`GITPR_METRICS_PRICE_<MODEL>_INPUT` e `GITPR_METRICS_PRICE_<MODEL>_OUTPUT`) e a moeda métrica (`GITPR_METRICS_CURRENCY`) no painel de configuração interativo do `gitpr config`, condicionados dinamicamente ao provedor de IA selecionado (`gemini` ou `deepseek`).

---

## 1. O Que Mudou

### 1.1. Suporte a Campo Numérico Flutuante (`KIND_FLOAT`)
- Definida a constante `KIND_FLOAT = "float"` em `src/config_schema.py`.
- Adicionada validação no `validate_field_value`:
  - Permite valor vazio (remove a variável de `.env` para restaurar os preços padrão embutidos).
  - Converte para `float` e valida se o valor é não-negativo ($\ge 0.0$). Valores negativos ou não-numéricos disparam erro traduzido.
- Suportado no `src/ui/config_app.py` utilizando o controle de entrada `Input`.

### 1.2. Preços Padrão de Referência para Modelos Gemini
- Em `src/config.py`:
  - `DEFAULT_MODEL_PRICES` agora inclui `gemini-pro-latest` (\$1.25 / \$10.00 por 1M tokens) e `gemini-flash-lite-latest` (\$0.10 / \$0.40 por 1M tokens), equiparando o suporte ao DeepSeek.

### 1.3. Definição do Esquema e Condicionamento Dinâmico
- Em `src/config_schema.py`:
  - Adicionado `GITPR_METRICS_CURRENCY` (`KIND_STR`, `seeded=False`, `default=""`) na categoria `ai`.
  - Adicionados 4 campos para Gemini quando `DEFAULT_AI_PROVIDER == "gemini"`:
    - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_INPUT`
    - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_OUTPUT`
    - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_INPUT`
    - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_OUTPUT`
  - Adicionados 4 campos para DeepSeek quando `DEFAULT_AI_PROVIDER == "deepseek"`:
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT`
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT`
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_INPUT`
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_OUTPUT`
  - Para `ollama`, nenhum campo de preço é exibido (provedor local/gratuito).
  - Todos os campos de preço configurados com `seeded=False` e `default=""`, permitindo que o sistema use as taxas embutidas por padrão sem forçar escrita de defaults no `.env`.

### 1.4. Internacionalização (i18n)
- Todas as 15 novas chaves (rótulos, descrições e mensagem de erro de validação) foram adicionadas e sincronizadas em todos os catálogos:
  - `langs/pt_br.json`
  - `langs/pt_pt.json`
  - `langs/es_es.json` & `langs/es.json`
  - `langs/fr_fr.json` & `langs/fr.json`
  - `en_us` direto nas strings padrão do schema.

### 1.5. Glossário de Domínio
- Termos `Token price rate` e `Metrics currency` formalizados no `CONTEXT.md`.

---

## 2. Testes e Verificação

Executados testes unitários cobrindo o schema, validação flutuante, i18n e fallback de métricas:

| Teste | Comando | Resultado |
|---|---|---|
| Validação de Schema e Floats | `pytest tests/test_config_schema.py -v` | 55 passados |
| Integridade de i18n | `pytest tests/test_i18n.py -v` | 22 passados |
| Custo de Métricas e Fallback de Taxas | `pytest tests/test_metrics.py -k TestCost -v` | 15 passados |
| Aliases de Gemini e Moeda | `pytest tests/test_metrics.py -k "gemini_aliases or another_currency" -v` | 2 passados |

---

## 3. Como Usar

1. Execute:
   ```bash
   gitpr config
   ```
2. Na categoria **Configurações de IA**:
   - Ao selecionar o provedor `gemini`, os campos de taxas para `gemini-pro-latest` e `gemini-flash-lite-latest` surgem logo abaixo de seus respectivos modelos.
   - Ao trocar para `deepseek`, os campos de taxas para `deepseek-v4-pro` e `deepseek-v4-flash` são apresentados dinamicamente.
   - O campo **Moeda para Métricas e Custos** permite definir o símbolo desejado (ex: `USD`, `R$`, `€`).
   - Para reverter para as taxas embutidas oficiais, basta deixar o campo de preço vazio.
