# Documentação Técnica: Geração de Testes com IA (`gitpr tests generate`)

`gitpr tests generate` transforma um conjunto de alterações num ficheiro de teste completo. Deteta o framework de testes do projeto, calcula o caminho de destino convencional, pede à IA um conjunto de testes executável, valida a sintaxe com o toolchain local quando disponível e — apenas com `--apply` — escreve o ficheiro no disco.

O comando nunca executa os testes gerados e nunca faz stage ou commit de nada.

---

## 1. Visão Geral

```bash
# Gera testes para o diff completo da árvore de trabalho (dry run)
gitpr tests generate

# Gera testes para um ficheiro
gitpr tests generate --file src/auth/limiter.py

# Aponta para um achado da última revisão de código
gitpr tests generate --finding FIX-001

# Força o framework em vez de o detetar automaticamente
gitpr tests generate --framework vitest

# Escreve o ficheiro gerado no disco (pede confirmação)
gitpr tests generate --file src/auth/limiter.py --apply

# Ajuda contextual com a ligação para a documentação
gitpr tests generate -h
```

---

## 2. Referência de Comandos

```text
gitpr tests generate [--file PATH] [--finding ID] [--framework NAME] [--apply] [--provider NAME]
```

| Opção | Predefinição | Descrição |
|---|---|---|
| `--file PATH` | — | Gera testes para este ficheiro em vez do diff completo. |
| `--finding ID` | — | Gera testes para um achado específico da última revisão de código (por exemplo `FIX-001`). |
| `--framework NAME` | Detetado automaticamente | Força o framework: `pest`, `phpunit`, `jest`, `vitest`, `pytest`. |
| `--apply` | `false` | Escreve o ficheiro gerado no disco após o dry run e as confirmações. |
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Força o fornecedor de IA nesta execução (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Ajuda do Click mais a ligação para esta página. |

`--file` e `--finding` são mutuamente exclusivos na prática: `--finding` tem precedência, e `--file` é então substituído pelo caminho do ficheiro do achado.

---

## 3. Resolução do Alvo

O comando decide o que enviar ao modelo antes de gerar seja o que for:

| Invocação | Conteúdo do alvo |
|---|---|
| *(sem flags de alvo)* | Diff da árvore de trabalho: `git diff HEAD` com as smart excludes. |
| `--file PATH` | `git diff HEAD -- PATH`. Se esse diff estiver vazio e o ficheiro existir, o **conteúdo completo do ficheiro** é usado em alternativa. |
| `--finding ID` | A última revisão é carregada (`resolve_review` → `collect_candidates` → `find_candidate`), e o prompt recebe os metadados do achado, o seu `suggested_test` e o seu patch `diff_unified`. O scaffold usa o `file_path` do achado. |

Se o conteúdo resolvido estiver vazio, o comando imprime `❌ No changes or target content found to generate tests.` e termina com código `1`.

Para `--finding`, a revisão tem de existir e ser legível. Se a resolução da candidatura falhar, o comando imprime um aviso e recua para um contexto mínimo contendo apenas `Finding ID: <id>`; nesse caso o teste gerado tem muito pouco com que trabalhar.

---

## 4. Deteção de Framework

A deteção corre apenas na **raiz do repositório**. A primeira correspondência ganha, nesta ordem:

| Ordem | Framework | Indicadores |
|---|---|---|
| 1 | `pest` | `pest.php`, `tests/Pest.php` ou `pestphp/pest` no `composer.json` (`require` / `require-dev`). |
| 2 | `phpunit` | `phpunit.xml`, `phpunit.dist.xml`, `phpunit.xml.dist` ou `phpunit/phpunit` no `composer.json`. |
| 3 | `vitest` | `vitest.config.{ts,js,mjs,mts}`, `vite.config.{ts,js}` ou `vitest` nas dependências ou scripts do `package.json`. |
| 4 | `jest` | `jest.config.{js,ts,mjs,cjs,json}` ou `jest` nas dependências ou scripts do `package.json`. |
| 5 | `pytest` | `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, um `pyproject.toml` que mencione pytest, ou `tests/test_*.py` / `tests/*_test.py`. |
| — | `unknown` | Nenhum indicador encontrado. Um aviso indica para usar `--framework`. |

`--framework` é aplicado primeiro. O valor é comparado sem distinguir maiúsculas de minúsculas com os cinco nomes conhecidos; um valor desconhecido gera um aviso e recua para a deteção automática em vez de falhar.

---

## 5. Convenções de Caminho do Scaffold

O caminho de destino é calculado antes de chamar a IA, e o prompt recebe-o como alvo obrigatório.

### Pest / PHPUnit

- `app/` é removido do início do caminho.
- A suite é **Feature** quando o primeiro segmento restante é `Http`, `Controllers`, `Livewire` ou `Filament`; caso contrário, é **Unit**.
- O nome do ficheiro recebe o sufixo `Test.php`, a menos que o stem já termine com `Test`.

| Origem | Destino |
|---|---|
| `app/Http/Controllers/Api/UserController.php` | `tests/Feature/Http/Controllers/Api/UserControllerTest.php` |
| `app/Services/UserService.php` | `tests/Unit/Services/UserServiceTest.php` |
| *(sem ficheiro de origem, Pest)* | `tests/Feature/GeneratedTest.php` |
| *(sem ficheiro de origem, PHPUnit)* | `tests/Unit/GeneratedTest.php` |

### Jest / Vitest

- `src/` é removido do início do caminho.
- `.ts` / `.tsx` → `.test.ts`; `.vue` → `.spec.js`; qualquer outro → `.test.js`.

| Origem | Destino |
|---|---|
| `src/components/Button.vue` | `tests/components/Button.spec.js` |
| `src/utils/date.ts` | `tests/utils/date.test.ts` |
| `src/lib/api.js` | `tests/lib/api.test.js` |
| *(sem ficheiro de origem, Vitest)* | `tests/generated.test.ts` |
| *(sem ficheiro de origem, Jest)* | `tests/generated.test.js` |

### pytest

- `src/` ou `app/` é removido do início do caminho.
- `test_` é prefixado, a menos que o stem já comece por ele.

| Origem | Destino |
|---|---|
| `src/core.py` | `tests/test_core.py` |
| `app/services/auth.py` | `tests/services/test_auth.py` |
| *(sem ficheiro de origem)* | `tests/test_generated.py` |

### Desconhecido

| Origem | Destino |
|---|---|
| `src/model.py` | `tests/test_model.py` |
| *(sem ficheiro de origem)* | `tests/test_generated.txt` |

O scaffold também registra `already_exists`, que controla a confirmação de substituição em `--apply`.

---

## 6. Pipeline de Geração

1. **Deteção de framework** — override ou indicadores do repositório (secção 4).
2. **Scaffold** — caminho de destino convencional (secção 5).
3. **Fornecedor e chave** — `--provider` ou `DEFAULT_AI_PROVIDER`. Sem chave, o comando acrescenta um aviso (`No API key configured for <provider>...`), devolve conteúdo vazio e termina com código `1`. O `ollama` não precisa de chave.
4. **Modelo** — é usado o modelo avançado/primário (`task_complexity="advanced"`).
5. **Skill** — `get_skill_context("tests", quiet=True)` lê `.gitpr/skill/.gitpr.tests.md`; sem ele, é usada uma instrução incorporada equivalente ao template em inglês. A skill define a persona de QA e o envelope JSON.
6. **Prompt** — framework, caminho de destino, tipo de alvo, metadados de ficheiro/achado e o diff completo.
7. **Chamada de IA** — `call_ai_model(..., action="tests")`, temperatura `0.0`, até **3** tentativas com intervalo de **2 s**.
8. **Parsing** — o fornecedor devolve um **dict** já parseado; uma string JSON também é aceite. Uma string que não seja JSON é tratada como bloco de código: as cercas são removidas e o texto completo passa a ser o ficheiro de teste, com o cenário `Generated from raw model output`.
9. **Validação de sintaxe** — o toolchain local verifica o código gerado quando disponível (secção 7).
10. **Escrita opcional** — apenas quando `--apply` é passado (secção 8).

Não há cache de prompt nem registo no ledger de métricas: cada execução chama o fornecedor.

---

## 7. Validação de Sintaxe

A validação é de melhor esforço e nunca bloqueia a geração:

| Framework | Ferramenta | Comando | Observações |
|---|---|---|---|
| Pest / PHPUnit | `php` | `php -l <temp>.php` | Ignorada quando o PHP não está no `PATH`. |
| Jest / Vitest | `node` | `node --check <temp>.js` | O ficheiro temporário usa sempre o sufixo `.js`, incluindo para fontes TypeScript. Apanha erros grosseiros de sintaxe, não erros de tipo. |
| pytest | `python` / `python3` | `python -m py_compile <temp>.py` | Ignorada quando nenhum dos binários está no `PATH`. |
| desconhecido | — | — | Sem validação. |

Uma validação que falha acrescenta um aviso (`Syntax validation failed ... Marked as EXPERIMENTAL / low confidence.`), mas o conteúdo gerado continua a ser devolvido e ainda pode ser escrito com `--apply`. Conteúdo gerado vazio é reportado como inválido.

---

## 8. Escrita com `--apply`

O comando **imprime sempre** o dry run primeiro: framework, caminho de destino, cenários cobertos e o código gerado completo. A escrita só acontece depois disso e apenas quando `--apply` está presente.

| Etapa | Condição | Resposta predefinida |
|---|---|---|
| Confirmação de substituição | O caminho de destino já existe (`already_exists`) | **Não** |
| Confirmação de escrita | Sempre | **Sim** |

Se qualquer confirmação for recusada, o comando imprime uma mensagem de cancelamento e regressa sem escrever. Quando aceite, cria os diretórios pais e escreve o ficheiro em UTF-8 com `errors='replace'`, relativo ao **diretório de trabalho atual**.

Não executa `git add`, não faz commit e não corre os testes gerados.

---

## 9. Exemplo de Saída

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

## 10. Erros e Códigos de Saída

| Situação | Comportamento | Código de saída |
|---|---|---|
| Testes gerados (dry run ou aplicados) | Relatório e, com `--apply`, o ficheiro | `0` |
| Sem diff / sem conteúdo de ficheiro | `❌ No changes or target content found to generate tests.` | `1` |
| Sem chave de API | Aviso mais `❌ Test generation failed.` (conteúdo vazio) | `1` |
| O modelo não devolveu nada útil | Aviso mais `❌ Test generation failed.` | `1` |
| A validação de sintaxe falhou | Apenas aviso; o conteúdo continua a ser mostrado/aplicado | `0` |
| O utilizador recusa uma confirmação | Mensagem de cancelamento | `0` |
| Utilização inválida da CLI | Erro de utilização do Click | `2` |

---

## 11. Limitações

- **Deteção apenas na raiz.** Os indicadores de framework são procurados na raiz do repositório. Monorepos com configurações por pacote não são suportados; use `--framework`.
- **A primeira correspondência ganha.** Um repositório com indicadores PHP e JS é detetado como PHP, porque o PHP é verificado primeiro.
- **O teste gerado não é executado.** Apenas a sintaxe é verificada, e só quando o binário correspondente está instalado. Um teste sintaticamente válido pode ainda falhar em tempo de execução.
- **A validação de TypeScript é superficial.** `node --check` analisa o ficheiro como JavaScript; erros de tipo e muitas construções específicas de TS não são validados.
- **Framework desconhecido produz um ficheiro `.txt`.** Sem framework não há convenção nem verificação de sintaxe, e o destino é `tests/test_generated.txt` (ou `tests/test_<stem><ext>`).
- **`--file` sem diff envia o ficheiro inteiro.** Para um ficheiro grande e inalterado, isso pode consumir uma parte significativa da janela de contexto; o comando não faz chunking.
- **`--finding` depende da última revisão.** Lê o artefacto de revisão produzido por `gitpr -r` / `gitpr -f` através da maquinaria de `fix`. Sem revisão, o contexto degrada para o ID do achado.
- **Os caminhos são relativos ao diretório atual.** Executar a partir de um subdiretório escreve o teste relativo a esse subdiretório, não à raiz do repositório.
- **Sem cache, sem ledger.** Execuções repetidas chamam novamente o fornecedor, e a execução não é registada em `gitpr metrics`.
- **Sem integração com o git.** O novo ficheiro fica não seguido; `git add` e commit são da sua responsabilidade.
- **O comando `/tests` do chat é separado.** Não delega neste motor; use `gitpr tests generate` para geração estruturada.
- **O texto gerado segue o idioma da skill**, não o idioma de interface de `--lang`.

---

## 12. Documentação Relacionada

- [Revisão de Código com IA](code-review-ia.pt_pt.md) — de onde vêm os achados consumidos por `--finding`.
- [Comando Fix](fix-command.pt_pt.md) — os achados de revisão e a maquinaria de patch partilhada com `--finding`.
- [Templates de Skill](skill-template.pt_pt.md) — como `.gitpr.tests.md` é resolvido, descarregado e substituído.
- [Fornecedores de IA](providers-ia.pt_pt.md) — fornecedores, modelos, tentativas e configuração de chaves.
- [Guia do Revisor](explain-pr.pt_pt.md) — o outro comando de geração com IA.
- [Verificação Unificada de CI](check-ci.pt_pt.md) — que validações correm na CI em vez disso.
