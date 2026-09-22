# Secret scanning no linter — implementação

## Contexto

A pergunta foi "o que foi implementado do Secret Scanning?" — e a resposta verificada é **nada**. Existem apenas os cinco documentos da sessão de grill (spec, survey, plano, glossary, ADR-007), todos ainda não rastreados pelo git. Não há `src/security_ruleset.py`, não há `tests/test_security_ruleset.py`, nenhuma ocorrência de `GITPR_LINTER_SECURITY` em `src/` ou `langs/`, nenhuma regra `sec-*`, nenhum merge em `load_linter_rules()`, nenhum commit, nenhum stash, nenhum branch. `src/linter_engine.py:16` ainda é `if file_extension not in rule.get("extensions", []): return False`. Isso é coerente com a decisão Q1 daquela sessão — o grill produz documentos, a implementação é uma sessão separada. É esta.

O desenho já está fechado e aprovado em `docs/plans/20260921_skill_gitpr_secret_scanning_plan.md`, que continua sendo a fonte de verdade. Este arquivo é o plano de execução dele, com as correções que a verificação de hoje encontrou.

**Decisões desta sessão:** eu redijo as traduções nos 4 idiomas (você revisa depois); `GITPR_LINTER_SECURITY=false` fixado no `conftest`; escopo completo, incluindo docs e nota de release.

## Correções ao plano, verificadas hoje

1. **`get_config()` não existe em lugar nenhum do repositório.** O snippet do plano (linhas 61 e 64) produziria `NameError` na primeira execução do linter. Os helpers reais são `_env_bool_default_true()` (`src/config.py:700-709`) e `load_dotenv(ENV_FILE)` + `os.getenv(nome, "")` para a lista.
2. **`python tests/sync_i18n.py` é uma armadilha documentada.** `.claude/memory/i18n-sync-canonicos-roundtrip.md` registra o estrago duas vezes (2026-09-05 e 2026-09-13): 23 chaves completas viraram fragmentos com valor EN, porque o extrator é regex e reconstrói os seis arquivos. A própria mensagem de falha do `test_i18n.py` que manda rodá-lo é citada como armadilha no fim daquela memória. O passo 5 do plano prescreve exatamente isso — **não será seguido**. Caminho seguro na etapa 5 abaixo.
3. **Três arquivos de teste quebram sem o pin, não um.** `tests/test_plugins.py` (8 testes, não só as contagens: dois `assertEqual(rules, [])`), `tests/badge/test_badge_data.py:92-96` e `tests/badge/test_badge_optout.py:120-128`. Todos chamam o `load_linter_rules()` real.
4. **As fixtures de teste seriam pegas pelo próprio hook deste repositório.** `src/main.py:2804` roda o linter no pre-commit, e o `gitpr -l` sai com código 1. Um fixture com `"AKIAIOSFODNN7EXAMPLE"` literal é um diff que se autobloqueia. Toda fixture de segredo será montada com fragmentos concatenados.
5. **`(?i)` só é legal no índice 0 do padrão.** Dentro de uma alternação ou depois de um grupo levanta `re.error: global flags not at the start of the expression`. A forma à prova de futuro é o grupo com escopo, `(?i:password|senha|...)`.
6. **A semântica do helper é fail-*open*, e é a correta aqui.** `_env_bool_default_true` só desliga com `false/0/no/off/n`; `""` ou `maybe` mantêm ligado. O `== "true"` do plano seria fail-*closed* — um opt-*out* que se desliga sozinho com texto inesperado. O ADR-007 §3 pede opt-out, e o precedente é `badge_enabled()` (`src/config.py:336-349`), com o mesmo raciocínio já escrito em `tests/badge/test_badge_optout.py:44-46`.

## Mudanças

### 1. As duas chaves de configuração

`DEFAULT_CONFIG` (`src/config.py:17-80`), junto de `OUTPUT_FILE_NAME_LINTER` (linha 44): `"GITPR_LINTER_SECURITY": "true"` e `"GITPR_LINTER_SECURITY_DISABLED_RULES": ""`.

`src/config_schema.py`, categoria `linter`, depois de `GITPR_LINTER_TIMEOUT` (linha 579-586): `KIND_BOOL` com `default="true"` e `KIND_STR` com `default=""`. O gate `tests/test_config_schema.py:43` exige que toda chave de `DEFAULT_CONFIG` esteja no schema, e `:57` exige **defaults idênticos** entre os dois arquivos. Usar `KIND_STR`, não `KIND_WORDS` — o único `KIND_WORDS` do schema é `read_only` e renderiza como lista quebrada; o precedente citado pelo plano, `GITPR_FIX_SAFE_EXCLUDED_PATHS`, é `KIND_STR`.

### 2. `src/security_ruleset.py` (novo)

As sete regras da tabela §1.1 do plano, no schema que o motor lê (`name`, `level`, `regex`, `message`, `extensions`), todas com `extensions: ["*"]` e regexes em raw string. `error` para as cinco que são prova por si (AWS, GitHub, Slack, Google, bloco de chave privada), `warning` para as duas que aparecem legitimamente em exemplo e documentação (connection string, atribuição genérica).

Mensagens via `__()` com chave literal em inglês contendo `{file_name}` e `{line_number}` — as duas únicas que o motor substitui (`.replace()`, não `.format()`). **Nenhuma mensagem interpola o valor casado**, e nenhuma chave `__()` pode aparecer em docstring do módulo (o regex do sync a captura, o AST não — vira chave fantasma).

### 3. `src/linter_engine.py` — `"*"` em `extensions`

Em `_is_rule_applicable` (linhas 13-17):

```python
    # Check extension ("*" means every file, including the ones with no suffix)
    extensions = rule.get("extensions", [])
    if "*" not in extensions and file_extension not in extensions:
        return False
```

`file_extension` vem de `current_file.split(".")[-1] if "." in current_file else ""` (linhas 242 e 285), então `id_rsa` → `""` e `.env` → `"env"` — os dois casos que hoje seriam pulados. Regra sem `extensions` continua nunca aplicando, como hoje.

### 4. `src/config.py` — merge no fim de `load_linter_rules()`

Substituindo o `return rules` da linha 612:

```python
    # 3. Security ruleset (embedded; opt-out via config)
    if _env_bool_default_true("GITPR_LINTER_SECURITY"):
        load_dotenv(ENV_FILE)
        disabled = {
            name.strip()
            for name in os.getenv("GITPR_LINTER_SECURITY_DISABLED_RULES", "").split(";")
            if name.strip()
        }
        from src.security_ruleset import SECURITY_RULES

        rules.extend(rule for rule in SECURITY_RULES if rule["name"] not in disabled)

    return rules
```

Import tardio mantido por higiene (não há ciclo real: `src/security_ruleset.py` só importa `src.i18n` — a cadeia é `security_ruleset → i18n → net`, e `net.py` é terminal por contrato). Sem `try/except ImportError`: erro de digitação no import tem de ser barulhento, não virar "sem regras".

### 5. i18n — 7 chaves nos 6 arquivos, por script cirúrgico

**Não rodar `tests/sync_i18n.py`.** O procedimento seguro, com precedente no repositório (`scripts_dev/add_i18n_keys.py` e os `tests/_stage*_i18n_insert.py` citados na memória):

1. Diagnóstico por arquivo: `json.loads` → `json.dumps(indent=2, ensure_ascii=False)` na ordem original → comparar bytes com CRLF. Os seis passam; isso prova que o dumper é fiel e que o merge é sem perda.
2. Inserir as 7 chaves em cada arquivo (es → `es.json` + `es_es.json`, fr → `fr.json` + `fr_fr.json`), gravando com `write_bytes` e CRLF — os arquivos são CRLF e um `open(..., "w")` em modo texto os converteria inteiros para LF.
3. Verificar por arquivo: +7 chaves, re-parse, idempotência (reaplicar é no-op), chaves pré-existentes com valor intacto.
4. Eu redijo as 28 frases (pt_br, pt_pt, es, fr) seguindo as âncoras de voz do repositório: pt_pt usa "ficheiro", fr usa o espaço tipográfico antes de dois-pontos, es/es_es usam o tratamento formal. Você revisa no working tree.

### 6. `tests/test_security_ruleset.py` (novo)

Pytest com classes simples e docstrings, no estilo de `tests/badge/test_badge_data.py` e `tests/test_i18n.py`. Fixtures: as regras por nome, o dict `{"errors": [], "warnings": []}`, e — obrigatório — `monkeypatch.setattr` em `src.config.resolve_skill_path` e `src.config.get_linter_plugins`, senão o `.gitpr.linter.yml` e os plugins da máquina de quem roda entram em toda asserção; mais `log_local_metric` silenciado (`parse_diff_and_lint` escreve métrica no `~/.gitpr` real; precedente em `tests/badge/conftest.py:82-90`).

O que cada bloco prova:

| Bloco               | Prova                                                                                                                                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Forma               | toda regra tem `name`/`regex`/`message` não vazios, `level` em `{error, warning}`, `extensions == ["*"]`; 7 nomes, prefixo `sec-`, sem repetição                              |
| Placeholders        | `{file_name}` e `{line_number}` presentes em toda mensagem — tradução que perca um deles perde a localização em silêncio                                                      |
| Compilação          | `re.compile` nas 7. É a proteção real: um regex com erro de digitação não derruba o linter, ele **multiplica** — medido, 50 linhas de diff → 50 alertas bloqueantes idênticos |
| Positivos/negativos | uma linha realista e um quase-acerto por categoria (`AKIA`+15, `ghp_`+35, `AIza`+34, `-----BEGIN CERTIFICATE-----`, `postgresql://localhost:5432/db` sem credencial)          |
| Placeholder         | `changeme`, `your_password_here`, `xxxxxx`, `placeholder`, `dummy`, `sample`, `example`, `sua_senha` → não casam; `hunter2xyz` → casa                                         |
| Roteamento de nível | por regra, um `_apply_rule` e a comparação contra a **própria** mensagem da regra — nunca contra uma frase escrita à mão, que é o que mantém o teste à prova de locale        |
| `["*"]`             | `_is_rule_applicable(rule, "id_rsa", "")` e `(rule, ".env", "env")` verdadeiros; uma regra sem `"*"` continua recusada nos dois                                               |
| Merge               | com `false` → nenhuma `sec-*`; com `true` → as 7; com `DISABLED_RULES="sec-db-connection-string"` → só ela ausente; regras do projeto e de plugin intactas                    |
| Default             | com `ENV_FILE` redirecionado para um arquivo temporário e a variável removida do ambiente → as 7 carregam                                                                     |
| Não-eco             | nenhum alerta dos dois baldes contém o valor casado                                                                                                                           |
| Integração          | o diff sintético com uma linha por categoria (montado por fragmentos) dá exatamente 5 erros e 2 avisos pelo `parse_diff_and_lint` real                                        |

### 7. `tests/conftest.py` — o pin

Uma linha `os.environ["GITPR_LINTER_SECURITY"] = "false"` antes de qualquer import de projeto, com um parágrafo de docstring no mesmo tom dos três que já estão lá. Vale por três razões independentes: mantém os três arquivos de teste intactos, torna a suíte independente do `~/.gitpr/.env` de quem roda, e impede que o `setup_environment()` (`src/config.py:435-438`, alcançado pelo fluxo principal em `src/main.py:1260`) grave as duas chaves novas no perfil real durante o pytest — o que reintroduziria a escrita no `~/.gitpr` que a suíte acabou de eliminar. Como todo `load_dotenv` do projeto roda com `override=False`, os testes que precisam do ruleset ligado o ligam com `monkeypatch.setenv`, que vence o pin.

### 8. Documentação e nota de release

`docs/linter-regras-customizadas.md` (+ `.pt_br`) para documentar `level` e o ruleset; `docs/git-hooks-locais.md` (+ `.pt_br`), cuja promessa de "passwords" passa a ser verdade; a seção de linter no `CLAUDE.md` (regras + as duas chaves novas na lista de variáveis de ambiente).

A nota vai numa seção `## [<próxima versão>] - <data>` no topo do `CHANGELOG.md`, abaixo do `# Changelog` — não existe convenção de "Unreleased" ativa (o único `## [Unreleased]` está na linha 174, resto morto do lote de SCM). Precisa dizer que commits que passavam podem passar a ser bloqueados, nomear as cinco categorias que bloqueiam e as duas chaves de escape, registrar que as duas chaves passam a ser semeadas no `~/.gitpr/.env` na próxima execução, e que o `--input` agora varre também `.md` e lockfiles (o ruleset é `["*"]`).

## Verificação

| #   | Verificação                                                                          | Critério                                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `python -m pytest tests/test_config_schema.py tests/test_plugins.py tests/badge/ -q` | verde — o pin segurou os três                                                                                                                                                 |
| 2   | `python -m pytest tests/test_security_ruleset.py -q`                                 | verde                                                                                                                                                                         |
| 3   | `python -m pytest tests/test_i18n.py -q`                                             | verde: paridade entre os 6, sem órfãs, sem chave com `{` devolvendo a si mesma                                                                                                |
| 4   | `git diff --stat langs/`                                                             | exatamente +7 chaves por arquivo, nenhum valor existente alterado                                                                                                             |
| 5   | `python -m pytest tests/ -q`                                                         | suíte completa verde; mtimes de `~/.gitpr/.env` e `~/.gitpr/langs/*.json` **inalterados** antes/depois                                                                        |
| 6   | E2E em repo de rascunho (§4 do plano)                                                | `gitpr -l` limpo → exit 0; com `aws_access_key_id = "AKIA…"` → TUI de erro, exit 1 e relatório `.md`; `git commit` abortado pelo hook; `GITPR_LINTER_SECURITY=false` → exit 0 |
| 7   | O relatório do passo 6                                                               | nomeia a categoria e **não** repete o valor da chave                                                                                                                          |
| 8   | Primeira execução real do produto                                                    | as duas chaves aparecem no `~/.gitpr/.env`                                                                                                                                    |

Cada etapa é um commit isolado, na ordem 1 → 8 (a etapa 2 não muda comportamento até a 4 ligar o merge, então a árvore fica funcional o tempo todo). Como o CLAUDE.md me proíbe de commitar, entrego tudo no working tree e você commita — o relatório de conclusão em `docs/claude-code/reports/develop_natan/2026-09-21_secret_scanning.md` segue a mesma regra.

## Riscos e lacunas honestas

- **Lacunas de cobertura do v1**, a registrar na nota de release em vez de esconder: atribuição sem aspas (`API_KEY=abc123` — o formato de `.env`, que é justamente onde segredo vaza, e a regra genérica exige aspas); prefixos ausentes (`ASIA…` de credencial temporária AWS, `github_pat_…`, `xoxc-`/`xoxd-`); e nenhuma fronteira à esquerda do nome da chave, então `mytoken = "abcdefgh"` casa.
- **`src/branding/badge_data.py:43`** (`if not load_linter_rules(): return None`) deixa de ser o caso comum e passa a ser o caso do opt-out. O invariante do módulo sobrevive — lista vazia de alertas continua significando "verificou e não achou" —, mas quem nunca rodou `--skill` passa a receber uma medição em vez de nenhum badge. Uma linha na nota de release.
- **Blast radius do `["*"]`**: no modo `--input` (arquivo inteiro) o ruleset passa a varrer `.md`, `.txt` e lockfiles. Não bloqueia (`src/review/render.py` só imprime e grava; o `sys.exit(1)` existe apenas no caminho do `-l`), mas contradiz a frase de "ponto cego aceito" do ADR-007 — corrigir a frase, não o código.
- **Suíte sem cobertura do default de produção.** Com o pin em `false`, nenhum teste exercita o ruleset ligado pela via ambiente; o merge é coberto explicitamente pela etapa 6. Mesmo recorte que o `GITPR_LANG=en_us` já impôs.
