# Survey Facts — Configuração de Taxas de Custo de Tokens no GitPR Config

## Contexto da Tarefa
O usuário relatou que em `gitpr metrics dashboard`, a seção de custos exibia:
`As taxas vêm de GITPR_METRICS_PRICE_<MODEL>_INPUT / _OUTPUT em ~/.gitpr/.env.`
pois os modelos padrão do Gemini (`gemini-pro-latest` e `gemini-flash-lite-latest`) não constavam em `DEFAULT_MODEL_PRICES` em `src/config.py` e suas variáveis de custo não estavam disponíveis no painel TUI `gitpr config`.
A tarefa consiste em adicionar as variáveis de taxa de token por modelo ao painel de configuração do `gitpr config`, condicionadas ao provider selecionado, bem como a moeda das métricas.

## Decisões da Rodada de Entrevista (Grilling)

1. **Escopo dos Modelos e Variáveis por Provider**:
   - **Gemini**:
     - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_INPUT`: taxa de input por 1M tokens para `gemini-pro-latest` (default: 1.25).
     - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_OUTPUT`: taxa de output por 1M tokens para `gemini-pro-latest` (default: 10.00).
     - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_INPUT`: taxa de input por 1M tokens para `gemini-flash-lite-latest` (default: 0.10).
     - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_OUTPUT`: taxa de output por 1M tokens para `gemini-flash-lite-latest` (default: 0.40).
   - **DeepSeek**:
     - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT`: taxa de input por 1M tokens para `deepseek-v4-pro` (default: 0.435).
     - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT`: taxa de output por 1M tokens para `deepseek-v4-pro` (default: 0.87).
     - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_INPUT`: taxa de input por 1M tokens para `deepseek-v4-flash` (default: 0.14).
     - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_OUTPUT`: taxa de output por 1M tokens para `deepseek-v4-flash` (default: 0.28).
   - **Ollama**:
     - Provedor local (`LOCAL_PROVIDERS = ("ollama", "local")`), cujo custo é 0.0 por definição. Não expõe campos de preço.
   - Visibilidade filtrada via `show_if=(("DEFAULT_AI_PROVIDER", ("<provider>",)),)`.

2. **Preços Padrão (Defaults) e Fallback no Dashboard**:
   - Valores padrão conhecidos são configurados no schema (`seeded=True`) e os aliases `gemini-pro-latest` e `gemini-flash-lite-latest` são adicionados ao dicionário `DEFAULT_MODEL_PRICES` em `src/config.py`.
   - Isso garante que tanto instalações novas quanto existentes sem configuração manual calculem o custo imediatamente sem gerar aviso de falta de taxa.

3. **Moeda de Métricas (`GITPR_METRICS_CURRENCY`)**:
   - Adicionada na categoria `ai` no `gitpr config` como `KIND_STR` com default `"USD"` e `seeded=True`.

4. **Tipo de Dado (`KIND_FLOAT`) e Validação no Schema**:
   - Introdução do tipo `KIND_FLOAT = "float"` em `src/config_schema.py` e registro em `KINDS`.
   - Validação em `validate_field_value`: aceita float $\ge 0.0$.
   - Tratamento na TUI (`FieldRow._build_control` em `src/ui/config_app.py`) como `Input`.

5. **Organização Visual no TUI**:
   - Os campos de taxa de token são posicionados logo abaixo do respectivo modelo na categoria `ai`.
   - Labels e descrições claras, com menção explícita de "per 1M tokens".

## Fatos Levantados no Código
- `src/config.py`:
  - `metrics_price_env_key(model, kind)` constrói a chave no formato `GITPR_METRICS_PRICE_<MODEL>_<KIND>`.
  - `get_model_price(model)` consulta o ambiente e depois `DEFAULT_MODEL_PRICES`.
  - `DEFAULT_MODEL_PRICES` continha apenas `deepseek-v4-flash`, `deepseek-v4-pro`, `gemini-2.5-pro` e `gemini-2.5-flash-lite`.
- `src/config_schema.py`:
  - `FIELDS`: tupla imutável com todas as declarações de campos.
  - `DEFAULT_CONFIG`: dicionário gerado a partir de `field.seeded == True`.
  - `KINDS`: tupla de tipos válidos para os campos de configuração.
- `langs/`:
  - Requer tradução das novas strings (`__("...")`) para `pt_br.json`, `pt_pt.json`, `es_es.json`, `es.json`, `fr_fr.json`, `fr.json`.
- `tests/`:
  - `tests/test_config_schema.py` valida consistência de `DEFAULT_CONFIG`, `KINDS`, `show_if`, `seeded`, labels e descrições.
  - `tests/test_i18n.py` valida que todas as chaves estáticas de `__` estão presentes nos arquivos de idiomas.
