# Documentação Técnica: Geração de Testes com IA (`gitpr tests generate`)

`gitpr tests generate` transforma um conjunto de mudanças em um arquivo de teste completo. Ele detecta o framework de testes do projeto, calcula o caminho de destino convencional, pede à IA uma suíte executável, valida a sintaxe com o toolchain local quando disponível e — somente com `--apply` — grava o arquivo em disco.

O comando nunca executa os testes gerados e nunca faz stage ou commit de nada.

---

## 1. Visão geral

```bash
# Gera testes para o diff completo da árvore de trabalho (dry run)
gitpr tests generate

# Gera testes para um arquivo
gitpr tests generate --file src/auth/limiter.py

# Aponta para um achado da última revisão de código
gitpr tests generate --finding FIX-001

# Força o framework em vez de detectá-lo automaticamente
gitpr tests generate --framework vitest

# Grava o arquivo gerado em disco (pede confirmação)
gitpr tests generate --file src/auth/limiter.py --apply

# Ajuda contextual com o link da documentação
gitpr tests generate -h
```

---

## 2. Referência de comandos

```text
gitpr tests generate [--file PATH] [--finding ID] [--framework NAME] [--apply] [--provider NAME]
```

| Opção | Padrão | Descrição |
|---|---|---|
| `--file PATH` | — | Gera testes para este arquivo em vez do diff completo. |
| `--finding ID` | — | Gera testes para um achado específico da última revisão de código (por exemplo `FIX-001`). |
| `--framework NAME` | Detectado automaticamente | Força o framework: `pest`, `phpunit`, `jest`, `vitest`, `pytest`. |
| `--apply` | `false` | Grava o arquivo gerado em disco após o dry run e as confirmações. |
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Força o provedor de IA nesta execução (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Ajuda do Click mais o link para esta página. |

`--file` e `--finding` são mutuamente exclusivos na prática: `--finding` tem precedência, e `--file` é então sobrescrito com o caminho do arquivo do achado.

---

## 3. Resolução do alvo

O comando decide o que enviar ao modelo antes de gerar qualquer coisa:

| Invocação | Conteúdo do alvo |
|---|---|
| *(sem flags de alvo)* | Diff da árvore de trabalho: `git diff HEAD` com as smart excludes. |
| `--file PATH` | `git diff HEAD -- PATH`. Se esse diff estiver vazio e o arquivo existir, o **conteúdo completo do arquivo** é usado em seu lugar. |
| `--finding ID` | A última revisão é carregada (`resolve_review` → `collect_candidates` → `find_candidate`), e o prompt recebe os metadados do achado, seu `suggested_test` e seu patch `diff_unified`. O scaffold usa o `file_path` do achado. |

Se o conteúdo resolvido estiver vazio, o comando imprime `❌ No changes or target content found to generate tests.` e sai com código `1`.

Para `--finding`, a revisão precisa existir e ser legível. Se a resolução da candidatura falhar, o comando imprime um aviso e recua para um contexto mínimo contendo apenas `Finding ID: <id>`; nesse caso o teste gerado tem muito pouco com que trabalhar.

---

## 4. Detecção de framework

A detecção roda apenas na **raiz do repositório**. A primeira correspondência vence, nesta ordem:

| Ordem | Framework | Indicadores |
|---|---|---|
| 1 | `pest` | `pest.php`, `tests/Pest.php` ou `pestphp/pest` no `composer.json` (`require` / `require-dev`). |
| 2 | `phpunit` | `phpunit.xml`, `phpunit.dist.xml`, `phpunit.xml.dist` ou `phpunit/phpunit` no `composer.json`. |
| 3 | `vitest` | `vitest.config.{ts,js,mjs,mts}`, `vite.config.{ts,js}` ou `vitest` nas dependências ou scripts do `package.json`. |
| 4 | `jest` | `jest.config.{js,ts,mjs,cjs,json}` ou `jest` nas dependências ou scripts do `package.json`. |
| 5 | `pytest` | `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, um `pyproject.toml` mencionando pytest, ou `tests/test_*.py` / `tests/*_test.py`. |
| — | `unknown` | Nenhum indicador encontrado. Um aviso orienta a usar `--framework`. |

`--framework` é aplicado primeiro. O valor é comparado sem diferenciar maiúsculas de minúsculas com os cinco nomes conhecidos; um valor desconhecido gera um aviso e recua para a detecção automática em vez de falhar.

---

## 5. Convenções de caminho do scaffold

O caminho de destino é calculado antes de chamar a IA, e o prompt o recebe como alvo obrigatório.

### Pest / PHPUnit

- `app/` é removido do início do caminho.
- A suíte é **Feature** quando o primeiro segmento restante é `Http`, `Controllers`, `Livewire` ou `Filament`; caso contrário, é **Unit**.
- O nome do arquivo recebe o sufixo `Test.php`, a menos que o stem já termine com `Test`.

| Origem | Destino |
|---|---|
| `app/Http/Controllers/Api/UserController.php` | `tests/Feature/Http/Controllers/Api/UserControllerTest.php` |
| `app/Services/UserService.php` | `tests/Unit/Services/UserServiceTest.php` |
| *(sem arquivo de origem, Pest)* | `tests/Feature/GeneratedTest.php` |
| *(sem arquivo de origem, PHPUnit)* | `tests/Unit/GeneratedTest.php` |

### Jest / Vitest

- `src/` é removido do início do caminho.
- `.ts` / `.tsx` → `.test.ts`; `.vue` → `.spec.js`; qualquer outro → `.test.js`.

| Origem | Destino |
|---|---|
| `src/components/Button.vue` | `tests/components/Button.spec.js` |
| `src/utils/date.ts` | `tests/utils/date.test.ts` |
| `src/lib/api.js` | `tests/lib/api.test.js` |
| *(sem arquivo de origem, Vitest)* | `tests/generated.test.ts` |
| *(sem arquivo de origem, Jest)* | `tests/generated.test.js` |

### pytest

- `src/` ou `app/` é removido do início do caminho.
- `test_` é prefixado, a menos que o stem já comece com ele.

| Origem | Destino |
|---|---|
| `src/core.py` | `tests/test_core.py` |
| `app/services/auth.py` | `tests/services/test_auth.py` |
| *(sem arquivo de origem)* | `tests/test_generated.py` |

### Desconhecido

| Origem | Destino |
|---|---|
| `src/model.py` | `tests/test_model.py` |
| *(sem arquivo de origem)* | `tests/test_generated.txt` |

O scaffold também registra `already_exists`, que controla a confirmação de sobrescrita em `--apply`.

---

## 6. Pipeline de geração

1. **Detecção de framework** — override ou indicadores do repositório (seção 4).
2. **Scaffold** — caminho de destino convencional (seção 5).
3. **Provedor e chave** — `--provider` ou `DEFAULT_AI_PROVIDER`. Sem chave, o comando adiciona um aviso (`No API key configured for <provider>...`), retorna conteúdo vazio e sai com código `1`. `ollama` não precisa de chave.
4. **Modelo** — usa-se o modelo avançado/primário (`task_complexity="advanced"`).
5. **Skill** — `get_skill_context("tests", quiet=True)` lê `.gitpr/skill/.gitpr.tests.md`; sem ele, usa-se uma instrução embutida equivalente ao template em inglês. A skill define a persona de QA e o envelope JSON.
6. **Prompt** — framework, caminho de destino, tipo de alvo, metadados de arquivo/achado e o diff completo.
7. **Chamada de IA** — `call_ai_model(..., action="tests")`, temperatura `0.0`, até **3** tentativas com intervalo de **2 s**.
8. **Parsing** — o provedor retorna um **dict** já parseado; uma string JSON também é aceita. Uma string que não é JSON é tratada como bloco de código: as cercas são removidas e o texto inteiro vira o arquivo de teste, com o cenário `Generated from raw model output`.
9. **Validação de sintaxe** — o toolchain local verifica o código gerado quando disponível (seção 7).
10. **Gravação opcional** — somente quando `--apply` é passado (seção 8).

Não há cache de prompt nem registro no ledger de métricas: cada execução chama o modelo.

---

## 7. Validação de sintaxe

A validação é de melhor esforço e nunca bloqueia a geração:

| Framework | Ferramenta | Comando | Observações |
|---|---|---|---|
| Pest / PHPUnit | `php` | `php -l <temp>.php` | Pulada quando o PHP não está no `PATH`. |
| Jest / Vitest | `node` | `node --check <temp>.js` | O arquivo temporário sempre usa sufixo `.js`, inclusive para fontes TypeScript. Pega erros grosseiros de sintaxe, não erros de tipo. |
| pytest | `python` / `python3` | `python -m py_compile <temp>.py` | Pulada quando nenhum dos binários está no `PATH`. |
| desconhecido | — | — | Sem validação. |

Uma validação que falha adiciona um aviso (`Syntax validation failed ... Marked as EXPERIMENTAL / low confidence.`), mas o conteúdo gerado continua sendo retornado e ainda pode ser gravado com `--apply`. Conteúdo gerado vazio é reportado como inválido.

---

## 8. Gravação com `--apply`

O comando **sempre** imprime o dry run primeiro: framework, caminho de destino, cenários cobertos e o código gerado completo. A gravação só acontece depois disso e somente quando `--apply` está presente.

| Etapa | Condição | Resposta padrão |
|---|---|---|
| Confirmação de sobrescrita | O caminho de destino já existe (`already_exists`) | **Não** |
| Confirmação de gravação | Sempre | **Sim** |

Se qualquer confirmação for recusada, o comando imprime uma mensagem de cancelamento e retorna sem gravar. Quando aceita, cria os diretórios pais e grava o arquivo em UTF-8 com `errors='replace'`, relativo ao **diretório de trabalho atual**.

Ele **não** executa `git add`, não faz commit e não roda os testes gerados.

---

## 9. Exemplo de saída

```text
$ gitpr tests generate --file src/auth/limiter.py

🧪 Analyzing diff and generating test file...

📋 Target Framework: PYTEST
📂 Target Test Path: tests/test_limiter.py

🧪 Covered Scenarios:
  • Happy path: request under the limit is allowed
  • Boundary: request exactly at the limit
  • Regression: counter expiration resets the window

--- Generated Test Code ---
def test_request_under_limit_is_allowed():
    ...
---

ℹ️ Dry-run mode. Run with --apply to write to disk.
```

Com `--apply`, o mesmo relatório é seguido pelas confirmações e por `✅ Test file successfully created at '<path>'!`.

---

## 10. Erros e códigos de saída

| Situação | Comportamento | Código de saída |
|---|---|---|
| Testes gerados (dry run ou aplicados) | Relatório e, com `--apply`, o arquivo | `0` |
| Sem diff / sem conteúdo de arquivo | `❌ No changes or target content found to generate tests.` | `1` |
| Sem chave de API | Aviso mais `❌ Test generation failed.` (conteúdo vazio) | `1` |
| Modelo não retornou nada útil | Aviso mais `❌ Test generation failed.` | `1` |
| Validação de sintaxe falhou | Apenas aviso; o conteúdo continua sendo exibido/aplicado | `0` |
| Usuário recusa uma confirmação | Mensagem de cancelamento | `0` |
| Uso inválido da CLI | Erro de uso do Click | `2` |

---

## 11. Limitações

- **Detecção apenas na raiz.** Os indicadores de framework são procurados na raiz do repositório. Monorepos com configurações por pacote não são suportados; use `--framework`.
- **A primeira correspondência vence.** Um repositório com indicadores PHP e JS é detectado como PHP, porque o PHP é verificado primeiro.
- **O teste gerado não é executado.** Apenas a sintaxe é verificada, e somente quando o binário correspondente está instalado. Um teste sintaticamente válido ainda pode falhar em tempo de execução.
- **A validação de TypeScript é superficial.** `node --check` analisa o arquivo como JavaScript; erros de tipo e muitas construções específicas de TS não são validados.
- **Framework desconhecido produz um arquivo `.txt`.** Sem framework não há convenção, nem checagem de sintaxe, e o destino é `tests/test_generated.txt` (ou `tests/test_<stem><ext>`).
- **`--file` sem diff envia o arquivo inteiro.** Para um arquivo grande e inalterado, isso pode consumir uma parte significativa da janela de contexto; o comando não faz chunking.
- **`--finding` depende da última revisão.** Ele lê o artefato de revisão produzido por `gitpr -r` / `gitpr -f` por meio da maquinaria de `fix`. Sem revisão, o contexto degrada para o ID do achado.
- **Os caminhos são relativos ao diretório atual.** Executar a partir de um subdiretório grava o teste relativo a esse subdiretório, não à raiz do repositório.
- **Sem cache, sem ledger.** Execuções repetidas chamam o modelo de novo, e a execução não é registrada em `gitpr metrics`.
- **Sem integração com o git.** O novo arquivo fica não rastreado; `git add` e commit são responsabilidade sua.
- **O comando `/tests` do chat é separado.** Ele não delega a este motor; use `gitpr tests generate` para geração estruturada.
- **O texto gerado segue o idioma da skill**, não o idioma de interface de `--lang`.

---

## 12. Documentação relacionada

- [Revisão de Código com IA](code-review-ia.pt_br.md) — de onde vêm os achados consumidos por `--finding`.
- [Comando Fix](fix-command.pt_br.md) — os achados de revisão e a maquinaria de patch compartilhada com `--finding`.
- [Templates de Skill](skill-template.pt_br.md) — como `.gitpr.tests.md` é resolvido, baixado e sobrescrito.
- [Provedores de IA](providers-ia.pt_br.md) — provedores, modelos, tentativas e configuração de chaves.
- [Guia do Revisor](explain-pr.pt_br.md) — o outro comando de geração com IA.
- [Verificação Unificada de CI](check-ci.pt_br.md) — quais validações rodam na CI em vez disso.
