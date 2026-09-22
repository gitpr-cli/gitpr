# Plano — Secret scanning no linter regex do GitPR

> Substitui a [spec](20260921_skill_gitpr_secret_scanning_spec.md) como fonte de verdade para implementação. Decisões em [survey 20260921](../survey/20260921_gitpr_secret_scanning_surveyfacts.md) §3, vocabulário em [glossary-gitpr-secret-scanning.md](glossary-gitpr-secret-scanning.md), desvios aprovados no [ADR-007](ADR-007-secret-ruleset-location-and-severity.md).
> Cada etapa é um commit isolado, como pede a spec §7.

## 0. O que mudou em relação à spec

| Spec | Plano |
|---|---|
| Três níveis (`blocker`/`critical`/`warning`) | Dois: `error`/`warning` (ADR-007 §1) |
| `presets/linter/security.yml` | `src/security_ruleset.py` (ADR-007 §2) |
| `gitpr --linter security` | Chave de config; `-l` continua flag booleana |
| `exclude_values` | Lookahead negativo no próprio regex |
| Registro em `core.py` | Merge em `load_linter_rules()` |
| `id` / `category` / `severity` | `name` / — / `level` (schema real do motor) |
| Override e supressão inline "já existentes" | Não existem: entram como chaves de config; supressão inline vira follow-up |

## 1. Desenho final

### 1.1 As sete regras do v1

| `name` | `level` | `regex` |
|---|---|---|
| `sec-aws-access-key` | `error` | `AKIA[0-9A-Z]{16}` |
| `sec-github-token` | `error` | `gh[pousr]_[A-Za-z0-9]{36,}` |
| `sec-slack-token` | `error` | `xox[baprs]-[A-Za-z0-9-]{10,}` |
| `sec-google-api-key` | `error` | `AIza[0-9A-Za-z\-_]{35}` |
| `sec-private-key-block` | `error` | `-----BEGIN [A-Z ]*PRIVATE KEY-----` |
| `sec-db-connection-string` | `warning` | `(mysql\|postgres\|postgresql\|mongodb(\+srv)?)://[^:\s]+:[^@\s]+@` |
| `sec-generic-credential-assignment` | `warning` | `(?i)(password\|senha\|secret\|api[_-]?key\|token)\s*[:=]\s*['"](?!(?:changeme\|xxx+\|your[_-]?(?:key\|password\|secret\|token)[_-]?here\|placeholder\|examples?\|dummy\|sample\|sua[_-]?senha)['"])[^'"]{6,}['"]` |

Todas com `extensions: ["*"]`. Padrões escritos como **raw strings** (`r"..."`) no módulo — `"\+"` e `"[A-Za-z0-9\-_]"` disparam `SyntaxWarning` em Python 3.12+.

Mensagens específicas por categoria (exigência da spec §6.8), no estilo das regras existentes — `Found in {file_name} (Line {line_number}).` — e via `__()` com chave literal em inglês, porque o ruleset é Python (o YAML de regra nunca teve i18n). Chave em inglês, traduções nos seis arquivos de `langs/`.

A regra de bloco de chave privada casa **apenas a linha de cabeçalho**, que já é sinal definitivo por si só. O corpo base64 não é lido — o motor casa linha a linha, sem exceção.

### 1.2 Ativação e escape

| Chave (`~/.gitpr/.env`) | Default | Efeito |
|---|---|---|
| `GITPR_LINTER_SECURITY` | `true` | Liga o ruleset inteiro |
| `GITPR_LINTER_SECURITY_DISABLED_RULES` | `""` | Nomes de regra separados por `;` a desligar |

Escape genérico que já existe e continua valendo: `git commit --no-verify`, `GITPR_SKIP_LINT`.

### 1.3 Mudanças no motor — duas, ambas pequenas

**a) `extensions: ["*"]`** em `_is_rule_applicable` ([src/linter_engine.py:13-37](../src/linter_engine.py#L13-L37)):

```python
extensions = rule.get("extensions", [])
if "*" not in extensions and file_extension not in extensions:
    return False
```

**b) Merge do ruleset** no fim de `load_linter_rules()` ([src/config.py:562-612](../src/config.py#L562-L612)) — leitura de config no módulo que já é dono dela, import tardio da dados para não criar ciclo:

```python
    # 3. Security ruleset (embedded; opt-out via config)
    if str(get_config("GITPR_LINTER_SECURITY")).lower() == "true":
        disabled = {
            n.strip()
            for n in (get_config("GITPR_LINTER_SECURITY_DISABLED_RULES") or "").split(";")
            if n.strip()
        }
        from src.security_ruleset import SECURITY_RULES

        rules.extend(r for r in SECURITY_RULES if r["name"] not in disabled)
```

## 2. Árvore de arquivos

```
src/security_ruleset.py            NOVO  — SECURITY_RULES: lista de dicts no schema do motor
tests/test_security_ruleset.py     NOVO  — detecção por categoria, filtro, não-eco, compilação

src/config.py                      ALT   — 2 chaves em DEFAULT_CONFIG + merge em load_linter_rules()
src/config_schema.py               ALT   — 2 ConfigField na categoria "linter"
src/linter_engine.py               ALT   — "*" em extensions
langs/{pt_br,pt_pt,es_es,es,fr_fr,fr}.json  ALT — chaves novas das mensagens (paridade obrigatória)

docs/linter-regras-customizadas.md (+.pt_br)  ALT — documentar `level` e o ruleset
docs/git-hooks-locais.md (+.pt_br)            ALT — a promessa de "passwords" passa a ser verdade
CLAUDE.md                                     ALT — seção de linter
```

## 3. Etapas

| # | Etapa | Verificação |
|---|---|---|
| 1 | Duas chaves em `DEFAULT_CONFIG` ([src/config.py:17-80](../src/config.py#L17-L80)) e dois `ConfigField` em `config_schema.py` na categoria `linter`, junto de `OUTPUT_FILE_NAME_LINTER` | `python -m pytest tests/test_config_schema.py -q` verde; `gitpr config` mostra os dois campos |
| 2 | `src/security_ruleset.py` com as sete regras da §1.1 | `tests/test_security_ruleset.py`: toda regex compila com `re.compile` (guarda contra o bloqueio universal de typo); positiva e negativa por categoria; placeholder filtrado e não-placeholder detectado |
| 3 | `"*"` em `extensions` no motor | Teste novo com regra `extensions: ["*"]` sobre `id_rsa` (sem extensão) e sobre `app.py`; `tests/test_linter_metrics.py`, `tests/test_external_linters.py` e `tests/test_plugins.py` seguem verdes |
| 4 | Merge em `load_linter_rules()` | Teste com `GITPR_LINTER_SECURITY=false` → nenhuma regra `sec-*`; com `..._DISABLED_RULES="sec-db-connection-string"` → só ela ausente; regras do projeto e plugins intactas |
| 5 | Chaves `__()` nos seis arquivos de idioma, traduzidas | `python tests/sync_i18n.py` e então `python -m pytest tests/test_i18n.py -q` verde (paridade + tradução + sem órfãs) |
| 6 | Integração real: `parse_diff_and_lint` sobre diff sintético com uma linha de cada categoria | Erros caem em `alerts["errors"]`, avisos em `alerts["warnings"]`; nenhum alerta contém o valor casado (invariante de não-eco) |
| 7 | E2E manual em repo de rascunho | Ver §4 |
| 8 | Documentação da §2 | Leitura + convenção do repo; `.pt_br` espelhado |
| 9 | Suíte completa | `python -m pytest tests/ -q` verde |

Cada etapa é um commit; a ordem 2 → 3 → 4 mantém a árvore sempre funcional (a etapa 2 não muda comportamento até a 4 ligar o merge).

**Armadilha de idioma nos testes novos:** as mensagens passam por `__()`, então o texto renderizado depende do locale da máquina. Medido nesta sessão: 22 testes do próprio repositório falham em locale pt-BR só porque asseveram o literal em inglês (`tests/test_suggest_reviewers.py:232-257`, por exemplo). `tests/test_security_ruleset.py` deve asseverar **identidade estrutural** — `name` da regra, `level`, presença do alerta em `alerts["errors"]` vs `alerts["warnings"]` — e não o texto traduzido; onde o texto for inevitável, fixar `GITPR_LANG=en_us` no teste.

## 4. Verificação end-to-end

Num repositório de rascunho, com o GitPR em modo dev (`pipenv run python run.py`):

```bash
# 1. Baseline: nada muda num diff limpo
gitpr -l                      # espera: "Nothing to validate" ou sucesso, exit 0

# 2. Detecção e bloqueio
printf 'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"\n' >> app.py
git add app.py && gitpr -l    # espera: TUI de erro (ou texto em --quiet) e exit 1
                              #         relatório .md em .gitpr/reports/linter/
git commit -m "teste"         # espera: hook aborta com "COMMIT BLOCKED!"

# 3. Escape
GITPR_LINTER_SECURITY=false gitpr -l    # espera: exit 0
git commit --no-verify -m "teste"       # espera: passa

# 4. Sem rede e sem IA
#    (a suíte e o fluxo acima não fazem chamada de rede nem de IA por causa do ruleset)
```

O relatório gerado deve nomear a categoria ("Possible AWS Access Key ID hardcoded") **sem** repetir o valor da chave.

## 5. Critério de pronto (spec §6, ajustado)

| Teste da spec | Onde vive no plano |
|---|---|
| 1. Detecção positiva por categoria | §3 etapa 2 |
| 2. Não-detecção de string parecida | §3 etapa 2 |
| 3. Filtro de placeholder | §3 etapa 2 — **viável** por lookahead negativo; o fallback da spec (rebaixar por falta de filtro) não é necessário |
| 4. Carregamento pelo motor real | §3 etapa 6 |
| 5. Coexistência com outros presets | §3 etapa 4 — regras do projeto e plugins intactas |
| 6. Bloqueio de fluxo | §4 passo 2 |
| 7. Sem rede nem IA | §4 passo 4 |
| 8. Mensagens específicas por categoria | §3 etapa 2 |
| — | **Novo:** toda regex compila (risco de bloqueio universal) e nenhum alerta ecoa o valor casado |

## 6. Fora de escopo (follow-ups registrados)

- Supressão inline por linha/arquivo — capacidade transversal ao linter, não específica de segurança.
- Regra com janela de proximidade entre linhas (par `AKIA…` + Secret Access Key).
- Detecção por entropia e bridge SAST (Gitleaks, Semgrep, Bandit) — evolução de tier pago.
- Varredura retroativa do histórico.
- Objeto de finding estruturado (arquivo, linha, regra, nível) — hoje os alertas são strings renderizadas, o que impede refiltro e redação a posteriori.

## 7. Nota de release

Ativar o ruleset por padrão muda comportamento de quem já usa a ferramenta: commits que passavam podem passar a ser bloqueados. A nota da versão precisa dizer isso, nomear as cinco categorias que bloqueiam e apontar as duas chaves de escape.
