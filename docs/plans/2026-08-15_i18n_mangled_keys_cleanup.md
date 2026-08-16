# Plano: Limpeza de Chaves i18n Mangificadas

## Contexto

Descoberta documentada no relatório `docs/claude-code/reports/develop_natan/2026-08-15_staging_i18n_deadcode_mcp_docs.md` (Próximos Passos): uma família de chaves i18n cujo texto capturou fragmentos do call site Python (ex.: `📋 Auto-staging {count} file(s)...", count=len(unstaged)), fg="cyan`). São **51 chaves mangificadas idênticas nos 6 arquivos** de `langs/` (306 entradas mortas), todas com `value == key` (inglês).

Como `__()` é um dict lookup puro (`TRANSLATIONS.get(key, key)` em [src/i18n.py:98](src/i18n.py#L98)), essas chaves nunca casam — as mensagens sempre caem no inglês, mesmo com o idioma instalado.

**Causa raiz:** o regex de extração em [tests/sync_i18n.py:6](tests/sync_i18n.py#L6) (`__\([\'"](.*?)[\'"]\)`). Para chamadas como `click.secho(__("...", count=len(x)), fg="cyan")`, o `.*?` não-greedy passa da aspa real do literal (seguida de `,`, não `)`) e para na primeira aspa seguida de `)` — que é o `fg="cyan")`. O script de sync gravou essas capturas como chaves JSON.

## Decisões de escopo (aprovadas pelo usuário)

1. **Traduzir tudo** — remover as 51 mangificadas e adicionar as chaves corretas com tradução completa nos 6 arquivos.
2. **Corrigir causa raiz + teste de regressão** — novo regex no sync + `tests/test_i18n.py`.
3. **Incluir adjacentes** — chave truncada, paridade es/fr, poda de 2 órfãs.
4. **Bump `__lang_version__`** v0.0.15 → v0.0.16 em [src/updater.py:13](src/updater.py#L13).

## Estado verificado (fatia de trabalho)

- Árvore **limpa** em `develop_natan` (`c67ab6a`) — o trabalho empilha direto; confirmar com `git status --short` antes de começar.
- Regra de detecção sem falsos positivos: `k == v and re.search(r'",\s*\w+=', k)` — a chave legítima `You are a Software Architect...` (prompt LLM, contém `", ` no texto) **não** casa. Não tocar nela.
- Derivação da chave limpa: `mangled.split('", ', 1)[0]` → **50 chaves distintas** (não 49: os dois call sites de `🚨 Linter found {count} error(s):` são chaves runtime diferentes — [main.py:1687](src/main.py#L1687) tem `\n` inicial, [pr_publish_app.py:528](src/ui/pr_publish_app.py#L528) não). Nenhuma das 50 existe em nenhum arquivo (verificado).
- **Chave truncada** `Generate a Conventional Commits message (e.g., 'feat: add user auth`: o call site [mcp_server.py:1142-1147](src/mcp_server.py#L1142-L1147) é um `__()` com literal adjacente em 2 linhas — a chave runtime é a concatenação completa. Conserto exige **refatorar o call site para literal única**; sem isso o sync nunca extrai a chave completa e um sync futuro derrubaria a chave manual.
- `❌ Failed to stage files: {error}` presente e traduzida em pt_br/pt_pt/es_es/fr_fr, **ausente em es.json e fr.json** (a diferença 531 vs 532). Espelhar es_es/fr_fr.
- Órfãs confirmadas sem uso em `src/`: `No files selected for staging.` e `❌ Failed to stage files` (só a variante `{error}` é chamada: main.py:1573, 1593, 1621).
- **Fonte de traduções:** dicts `FR` (~linha 20) e `ES` (~linha 539) de `scripts/sync_all_langs.py` cobrem 41 das 50 chaves; 9 autoradas fresh (lista abaixo); chave MCP completa: FR ~linha 390, ES ~linha 909.
- **Contagem final: 529 chaves** nos 6 arquivos (532 − 51 + 50 − 2 = 529; es/fr: 531 − 51 + 50 − 2 + 1 = 529).
- `tests/sync_i18n.py` é script top-level sem funções nem guard `__main__` — **precisa de refactor** para o teste importá-lo sem disparar o scan/rewrite.

## Passos de implementação

### 1. Script de reparo único (commitado): `scripts/fix_mangled_i18n_keys.py`

Repositório `scripts/` já abriga one-offs similares — commitar para rastreabilidade do mapeamento mangificada→limpa→tradução.

- Detecta mangificadas pela regra acima; **assert** de 51 por arquivo e conjuntos idênticos entre os 6.
- Deriva limpas (`split('", ', 1)[0]`); **assert** de 50 distintas e de nenhuma pré-existente.
- Aplica tabela de traduções por idioma:
  - **FR/ES**: minerar dicts de `scripts/sync_all_langs.py` via `ast.parse` + `ast.literal_eval` (NÃO importar o módulo — código top-level escreve arquivos). 41/50 prontas; autorar as 9 restantes fresh.
  - **pt_br/pt_pt**: autorar fresh (50 + chave MCP), seguindo a voz das traduções existentes no próprio arquivo (âncoras: `✅ Git Hooks instalados com sucesso!`, `❌ Falha ao adicionar arquivos ao stage: {error}`; pt_pt usa variantes regionais, ex. `ficheiros`).
  - **es.json = es_es**, **fr.json = fr_fr** (convenção de pares idênticos).
  - **Chave MCP completa**: FR/ES mineradas; pt_br/pt_pt completar o valor truncado (pt_br: `Gera uma mensagem no padrão Conventional Commits (ex.: 'feat: add user auth') a partir das alterações atuais não commitadas.`).
  - **Chave de erro de stage para es/fr**: espelhar es_es/fr_fr.
- Transforma cada arquivo **in-place preservando a ordem das chaves** (diff mínimo — não reordenar).
- Também: chave truncada → chave completa + valor completo; 2 órfãs → delete; es/fr → inserir chave de erro de stage na posição relativa de es_es/fr_fr.
- Grava com `json.dump(indent=2, ensure_ascii=False)` e `encoding='utf-8'` em **todos** os `open()` (console Windows cp1252 corromperia emojis/acentos; usar `sys.stdout.reconfigure(encoding='utf-8')` ou `PYTHONIOENCODING=utf-8`).
- **Asserts finais** (exit ≠ 0 em falha): zero mangificadas restantes; paridade de chaves entre os 6 = 529; as 50 limpas com `value != key`; as 50 aparecem como substring literal em `src/`+`main.py`+`run.py`; órfãs e chave truncada ausentes.

### 2. Refatorar o call site `src/mcp_server.py:1142-1147`

De literal adjacente para literal única (comportamento idêntico, extraível pelo sync):

```python
description=__(
    "Generate a Conventional Commits message (e.g., 'feat: add user auth') from the current uncommitted changes."
),
```

Não tocar na descrição dict em `src/mcp_server.py:1550` (não é chamada `__()`).

### 3. Bump `src/updater.py:13`

`__lang_version__ = "v0.0.15"` → `"v0.0.16"`.

### 4. Commit 1 (JSONs + script + call site + bump juntos)

`fix(i18n): repair 51 mangled translation keys, prune dead keys, bump lang version to v0.0.16` — arquivos: `langs/*.json` (6), `scripts/fix_mangled_i18n_keys.py`, `src/mcp_server.py`, `src/updater.py`. Rodar pytest + linter antes. Rodapé `Co-Authored-By: Claude <noreply@anthropic.com>`.

**Invariante OTA:** `get_translations()` só puxa do `main` quando `LANG_VERSION` difere de `__lang_version__` — JSONs corrigidos e bump devem chegar ao `main` no mesmo PR.

### 5. Corrigir `tests/sync_i18n.py` (causa raiz)

Novo regex — captura só o literal, sem exigir `)` após a aspa (foi essa exigência que causou a mangificação):

```python
# Captures only the string literal of __("...") calls. Deliberately does NOT
# require a trailing ")": that requirement ran the match past kwargs
# (e.g. __("...", count=len(x)), fg="red") and mangled keys.
# Known limitations (accepted): adjacent literals __("a" "b") yield only "a";
# multi-line literals are captured up to the first line's closing quote.
PATTERN = re.compile(r'__\(\s*(["\'])(?:\\.|(?!\1).)*\1')
```

Verificado contra o corpus real: extrai as 50 limpas, call sites aninhados ([core.py:1317](src/core.py#L1317) `__("   Current: {current} (from .env)", current=env_version or __("none"))`) e multi-linha.

Refactor em módulo importável: funções `scan_file(filepath, keys)` / `scan_dir(directory, keys)` / `scan(keys)`, constantes `SRC_DIRS`, `LANG_FILES`, `PATTERN`, guard `if __name__ == "__main__":`. Loop de rebuild inalterado (sorted keys, mantém traduções existentes, default inglês, `indent=2, ensure_ascii=False`).

**Não** re-rodar o sync como fonte da verdade — usá-lo apenas como verificação (Step 7). Commit 2: `fix(i18n): make sync script extraction capture only the string literal`

### 6. Criar `tests/test_i18n.py` (regressão)

Importa `PATTERN`/helpers de `tests.sync_i18n`. Testes puro-JSON (sem rede, sem `~/.gitpr`; evitar import de `src.i18n` em escopo de módulo — o init lê `.env` e pode baixar). ~10 testes:

1. JSON válido nos 6 arquivos; valores são `str`.
2. Nenhuma chave casa padrão mangificado: `r'",\s*\w+=|\),\s*(?:fg|severity|classes)\s*=|,\s*\w+=len\('`.
3. Paridade de conjuntos de chaves entre os 6 e `len == 529`.
4. As 50 limpas presentes nos 6 com `value != key`.
5. Chave truncada ausente; chave MCP completa presente e traduzida nos 6.
6. `❌ Failed to stage files: {error}` presente e traduzida nos 6.
7. Órfãs ausentes nos 6.
8. Allowlist de chaves-identidade com `{`: exatamente 1 (a `You are a Software Architect...`).
9. Unit do `PATTERN`: amostra antes-mangificada → literal limpo; `__('He said "hi"', x=1)` → `He said "hi"`; `__("Don\'t stop", y=2)` → `Don't stop`; caso aninhado do core.py → ambas as chaves; `__("a" "b")` → `a` (documenta limitação).
10. Smoke de formatação: carregar `langs/pt_br.json` num monkeypatched `i18n.TRANSLATIONS` e verificar que `__("📋 Auto-staging {count} file(s)...", count=3)` retorna o texto pt_br com `3`.

Commit 3: `test(i18n): guard against mangled keys and enforce language parity`

### 7. Dry-run do sync (verificação, não fonte da verdade)

`python tests/sync_i18n.py` → `git diff --stat langs/` deve ser **vazio** (prova que o regex novo extrai exatamente o conjunto reparado). Se houver chaves traduzidas derrubadas → `git checkout -- langs/` e ajustar. Se houver só adições seguras → revisar uma a uma, manter ou reverter com julgamento, registrar no relatório. (Verificado: nenhum outro literal adjacente além do refatorado.)

### 8. Verificação final (comandos)

```powershell
pipenv run pytest tests/ -q          # baseline 227; esperado ~237
pipenv run python run.py -l          # linter local
python -X utf8 -m json.tool langs/pt_br.json   # validade (repetir p/ os 6)

# Paridade + contagem 529
python -X utf8 -c "import json;d=[json.load(open(f,encoding='utf-8')) for f in ['langs/pt_br.json','langs/pt_pt.json','langs/es_es.json','langs/es.json','langs/fr_fr.json','langs/fr.json']];print(len(d[0]), all(set(x)==set(d[0]) for x in d))"

# Nenhum artefato mangificado restante (esperado: sem saída)
grep -rn --include="*.json" -E '", [a-z_]+=' langs/
grep -rn --include="*.json" -E '\), (fg|severity|classes)="' langs/

# Smoke: chave antes-mangificada agora traduz (pt_br)
pipenv run python -X utf8 -c "import json;from src import i18n;i18n.CURRENT_LANG='pt_br';i18n.TRANSLATIONS=json.load(open('langs/pt_br.json',encoding='utf-8'));print(i18n.__('📋 Auto-staging {count} file(s)...', count=3))"
# esperado: texto pt_br contendo "3" e NÃO "Auto-staging"

# Smoke: chave MCP completa (fr)
pipenv run python -X utf8 -c "import json;from src import i18n;i18n.CURRENT_LANG='fr_fr';i18n.TRANSLATIONS=json.load(open('langs/fr_fr.json',encoding='utf-8'));print(i18n.__(\"Generate a Conventional Commits message (e.g., 'feat: add user auth') from the current uncommitted changes.\"))"

# Import check pós-refactor do mcp_server
pipenv run python -c "from src.mcp_server import mcp; print('ok')"
```

Nota: `GITPR_LANG=pt_br python run.py --help` NÃO serve de smoke pré-merge (faria download OTA dos arquivos ainda não corrigidos do `main`).

### 9. Relatório obrigatório (CLAUDE.md)

`docs/claude-code/reports/develop_natan/2026-08-15_i18n_mangled_keys_cleanup.md` no formato padrão, registrando: 51 → 50 chaves traduzidas nos 6 idiomas; fix do regex; chave MCP completa (com refactor do call site); paridade restaurada em 529; 2 órfãs podadas; bump v0.0.16; e em Próximos Passos: chave aninhada `none` de core.py:1317 segue sem tradução; `ORIGIN`/`REFACTORING` de blame_engine.py:242 são inglês por design; scripts legacy de `scripts/` ainda contêm mangificadas inertes (candidatos a exclusão futura). Commit 4: `docs: add completion report for i18n mangled keys cleanup`

### 10. Higiene do PR

Commits 1-4 num único PR para `main` — langs corrigidos e bump do `__lang_version__` juntos (invariante OTA).

## As 9 chaves sem tradução pronta (autorar FR/ES fresh)

`\n⚠️ Linter generated {count} warning(s):` · `\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}` · `\n❌ Unexpected error reading local linter rules: {error}` · `\n🚨 Linter found {count} error(s):` · `⚠️ Warning: Could not load linter plugin {file} ({error})` · `❌ Commit failed: {output}` · `❌ GitHub API Error ({code}): {msg}` · `📋 Auto-staging {count} file(s)...` · `🚨 Linter found {count} error(s):` (sem `\n`)

## As 50 chaves limpas (referência para autoração de traduções; derivação programática no script)

Família A (39, `fg="..."` capturado): `\n⚠️ Linter generated {count} warning(s):` · `\n❌ Error saving review: {error}` · `\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}` · `\n❌ Unexpected error reading local linter rules: {error}` · `\n🚨 Linter found {count} error(s):` · `⚠️ Attention! Found {count} alerts in the Linter rules.` · `⚠️ Failed to install {hook_name}: HTTP {code}` · `⚠️ Failed to install {hook_name}: {error}` · `⚠️ File {local_name} already exists in this directory. It will not be overwritten.` · `⚠️ Warning: Could not get Git Log: {error}` · `⚠️ Warning: Could not load linter plugin {file} ({error})` · `⚠️ Warning: Could not move {filename} to .gitpr/skill/ ({error})` · `⚠️ Warning: Failed to read file {file_name} ({error})` · `✅ Found {count} commit(s) on the surface. Starting time travel...\n` · `✅ Metrics purged ({count} files removed).` · `❌ Commit failed: {output}` · `❌ Error calculating diff: {error}` · `❌ Error injecting into hook: {error}` · `❌ Error reading file: {error}` · `❌ Error running Git: {error}` · `❌ Error saving file: {error}` · `❌ Error saving report: {error}` · `❌ Error: API Key for provider '{provider}' not found.` · `❌ Error: API Key not configured for provider '{provider}' in the CI/CD environment.` · `❌ Error: Could not determine model for provider '{provider}'.` · `❌ Failed to apply update: {error}` · `❌ Failed to process {local_name}: {error}` · `❌ Model configuration not found for provider {provider}.` · `❌ Network error while downloading {local_name}: {error}` · `❌ The file '{file_path}' was not found.` · `❌ Unknown AI provider: {provider}` · `📄 File Mode: Analyzing full content of '{input}'...` · `📋 Auto-staging {count} file(s)...` · `📥 Downloading {hook_name}...` · `📦 Updating scripts to {version}...` · `🔄 Compiling history of repository '{repo_name}', branch '{branch}' against '{base_branch}'...` · `🔑 API Key for {provider} not found.` · `🤖 GitPR is analyzing your code using {provider} ({model})...\n` · `🧠 File {file_name} (Skill) found and loaded!`

Família B (6, `json_format='...'`): `Generate ONLY a JSON object in the format {json_format} for the commit message, unifying these technical summaries:\n` · `Generate ONLY a JSON object in the format {json_format} for this diff:\n` (2 mangificadas gêmeas) · `Generate ONLY a JSON object in the format {json_format} pointing out errors and improvements for this diff:\n` · `Generate ONLY a JSON object in the format {json_format} with a code review focused on improvements, using these summaries:\n` · `Generate ONLY a JSON object in the format {json_format} with the analysis and improvements for the entire code of this file:\n` · `Unify these technical summaries and generate ONLY a JSON object in the format {json_format} describing the Pull Request:\n`

Família C (5, truncadas no meio da expressão): `❌ No code blocks found in message #{n}.` · `🚨 Linter found {count} error(s):` (sem `\n`) · `   Current: {current} (from .env)` (3 espaços iniciais, intencionais) · `Rule '{rule_name}' contains invalid Regex: {error}` · `❌ GitHub API Error ({code}): {msg}`

Chaves especiais: **MCP completa** `Generate a Conventional Commits message (e.g., 'feat: add user auth') from the current uncommitted changes.` · **erro de stage** `❌ Failed to stage files: {error}` (adicionar a es/fr) · **órfãs removidas** `No files selected for staging.`, `❌ Failed to stage files`.

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Qualidade de ~120 traduções autoradas (pt_br/pt_pt/9 FR/9 ES) | Minerar 82 de `sync_all_langs.py`; espelhar pares es/es_es e fr/fr_fr; âncoras de estilo nos arquivos; revisão manual do `git diff langs/` lendo cada tradução |
| Erro na derivação limpa | Script asserta que as 50 aparecem como literal em `src/`; dry-run do sync vazio; unit do PATTERN |
| Sync derrubando chaves traduzidas | Nenhum literal adjacente além do refatorado; escape hatch `git checkout -- langs/` |
| Discrepância 49 vs 50 | Plano usa 50 (main.py:1687 vs pr_publish_app.py:528); teste asserta 529; documentar no relatório |
| Encoding Windows | Todo `open()` com `encoding='utf-8'`; console com `-X utf8`/`PYTHONIOENCODING=utf-8`; conferir emojis no `git diff` |
| Efeitos OTA em smoke local | Usar `__()` direto contra os arquivos do repo, não `run.py` (que baixaria o `main` velho) |
| Poda de chave ainda usada | Verificado por grep (só a variante `{error}` é chamada); teste 7 guarda para sempre |
| Scripts legacy defasados | Fora de escopo por decisão; `sync_all_langs.py` nunca ADICIONA chaves próprias — entradas velhas são inertes; anotar em Próximos Passos |

## Arquivos críticos

- `langs/pt_br.json` (+ pt_pt, es_es, es, fr_fr, fr) — alvos do reparo
- `scripts/fix_mangled_i18n_keys.py` — novo script de reparo (mapeamento + traduções)
- `tests/sync_i18n.py` — regex raiz + refactor em módulo importável
- `tests/test_i18n.py` — nova suíte de regressão
- `src/mcp_server.py` — refactor do literal (linhas 1142-1147)
- `src/updater.py` — bump `__lang_version__` (linha 13)
- `docs/claude-code/reports/develop_natan/2026-08-15_i18n_mangled_keys_cleanup.md` — relatório obrigatório
