# Walkthrough — Contrato de Exit Code do Baseline

Mapeamento, documentação completa e testes automatizados do blast radius de um baseline inutilizável no exit code da CLI GitPR.

## Mudanças Realizadas

### 1. Documentação (5 Idiomas)
- **`docs/baseline-suppressions.md`** (+ `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`):
  - Adicionada subseção canônica com tabela detalhada dos códigos de saída por fluxo quando o baseline não pode ser aplicado (exit 1 para `-l`, `-r`, `-f`, `-i`, `risk`, `review-pr`, exit 2 para `check`, e neutro para fluxos não-bloqueantes).
  - Corrigida a afirmação enganosa de que `-r`/`-f`/`-i` nunca mudam exit code: esclarecido que não mudam por achados, mas saem com 1 diante de um baseline inutilizável.
  - Documentada explicitamente a nota de decisão adiada sobre unificação para exit 2.
- **`docs/check-ci.md`** (+ `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`):
  - Inserida nota de referência cruzada na linha do Exit Code 2 apontando para o contrato em `baseline-suppressions`.

### 2. Glossário do Domínio
- **`CONTEXT.md`**:
  - Adicionado o termo oficial **Unusable baseline** com regras de nomenclatura e termos a evitar.

### 3. Testes Automatizados
- **`tests/integration/test_baseline_exit_code_contract.py`**:
  - Suíte completa de integração validando os 8 cenários contra um baseline adulterado/incompatível:
    - `-l`, `-r`, `-f`, `-i`, `risk`, `review-pr` → exit 1 com mensagem no stderr.
    - `check` → exit 2.
    - `-c` (commit) → sem efeito / exit 0.

### 4. Correção em `run_check.py`
- Corrigido acesso de atributo em `FileRisk` para `f.file_path` (em vez de `f.path`), garantindo que o `check` calcule o mapa de riscos preliminares e alcance a checagem de baseline sem levantar exceções não tratadas.

---

## Verificação e Resultados

### Testes Executados
```bash
# Teste de contrato dos exit codes
python -m pytest tests/integration/test_baseline_exit_code_contract.py -v
# Resultado: 8 passed in 20.31s

# Suítes de regressão de baseline, check e internacionalização
python -m pytest tests/test_baseline_cli.py tests/test_check_cli.py tests/test_i18n.py -q
# Resultado: 80 passed in 258.64s
```
Nenhum teste quebrou e todas as asserções de contrato foram satisfeitas.
