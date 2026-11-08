# Plano de Execução — Configuração de Taxas de Custo de Tokens no GitPR Config

## 1. Visão Geral
Adicionar o gerenciamento e exibição das taxas de custo de tokens (`GITPR_METRICS_PRICE_<MODEL>_INPUT / _OUTPUT`) e da moeda (`GITPR_METRICS_CURRENCY`) no painel de configuração interativo (`gitpr config`), condicionados ao provedor selecionado na categoria de IA, eliminando a ausência de taxas no dashboard e permitindo ao usuário customizar valores por milhão de tokens.

## 2. Mudanças Propostas

### 2.1. `src/config.py`
- Atualizar `DEFAULT_MODEL_PRICES` para registrar oficialmente as taxas para os aliases padrão do Gemini:
  - `"gemini-pro-latest": (1.25, 10.00)`
  - `"gemini-flash-lite-latest": (0.10, 0.40)`

### 2.2. `src/config_schema.py`
- Adicionar constante `KIND_FLOAT = "float"` e registrá-la em `KINDS`.
- Atualizar `validate_field_value` para validar `KIND_FLOAT`:
  - Se preenchido, converter para `float`.
  - Rejeitar se não numérico ou se `< 0.0` com mensagem localizada `__("Use a number greater than or equal to zero.")`.
- Adicionar novos `ConfigField` em `FIELDS` na categoria `"ai"`:
  - `GITPR_METRICS_CURRENCY` (`KIND_STR`, default `"USD"`, `seeded=True`)
  - **Gemini** (`show_if=(("DEFAULT_AI_PROVIDER", ("gemini",)),)`):
    - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_INPUT` (`KIND_FLOAT`, default `"1.25"`, `seeded=True`)
    - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_OUTPUT` (`KIND_FLOAT`, default `"10.00"`, `seeded=True`)
    - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_INPUT` (`KIND_FLOAT`, default `"0.10"`, `seeded=True`)
    - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_OUTPUT` (`KIND_FLOAT`, default `"0.40"`, `seeded=True`)
  - **DeepSeek** (`show_if=(("DEFAULT_AI_PROVIDER", ("deepseek",)),)`):
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT` (`KIND_FLOAT`, default `"0.435"`, `seeded=True`)
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT` (`KIND_FLOAT`, default `"0.87"`, `seeded=True`)
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_INPUT` (`KIND_FLOAT`, default `"0.14"`, `seeded=True`)
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_OUTPUT` (`KIND_FLOAT`, default `"0.28"`, `seeded=True`)

### 2.3. `src/ui/config_app.py`
- Importar `KIND_FLOAT` de `src.config_schema`.
- Garantir que `KIND_FLOAT` seja renderizado adequadamente no controle `Input`.

### 2.4. `langs/*.json`
- Adicionar todas as novas chaves de tradução em:
  - `langs/pt_br.json`
  - `langs/pt_pt.json`
  - `langs/es_es.json`
  - `langs/es.json`
  - `langs/fr_fr.json`
  - `langs/fr.json`

### 2.5. Testes
- Atualizar `tests/test_config_schema.py` com testes para `KIND_FLOAT` e validações de float positivo/zero.
- Garantir 100% de aprovação em `tests/test_config_schema.py`, `tests/test_metrics.py` e `tests/test_i18n.py`.

## 3. Verificação
- Execução dos testes automatizados via `pytest`.
- Verificação da TUI e da correta renderização com `DEFAULT_AI_PROVIDER=gemini` e `DEFAULT_AI_PROVIDER=deepseek`.
