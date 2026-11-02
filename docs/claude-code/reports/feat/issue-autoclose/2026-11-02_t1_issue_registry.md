## Completion Report — T1: registro local de issue (`IssueRegistry`)

### What was done

- Criado o pacote de feature `src/issue_autoclose/` (mesmo padrão de `src/fix/`).
- Implementado `IssueRegistry` em `src/issue_autoclose/issue_registry.py`
  com o contrato do ADR-001: `RegisteredIssue`, YAML `schema_version: 1`,
  `load()`, `record(issue)`, `clear()` e `matches_repo(owner_repo)`.
- Escrita atômica (arquivo temporário no mesmo diretório + `os.replace`); um
  arquivo corrompido é devolvido como `RegistryLoad(error=...)` e sobrescrito
  pela gravação seguinte.
- `.gitignore`: `record()` apenda `.gitpr/conf/github.yml` uma única vez, só
  quando `git check-ignore` não reconhece o caminho; devolve
  `RecordResult.gitignore_updated` para o chamador reportar em uma linha.
  Fora de um repositório git, nada é alterado.
- Nenhuma dependência de rede; nenhum token ou segredo é gravado.
- Acrescentado o termo **Issue registry** ao `CONTEXT.md` (decisão Q15).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/issue_autoclose/__init__.py` | feat | Marcador do pacote de feature |
| `src/issue_autoclose/issue_registry.py` | feat | Registro local: contrato, leitura, escrita atômica, limpeza e `.gitignore` |
| `tests/issue_autoclose/test_issue_registry.py` | test | 23 testes: round-trip, schema, corrupção, atomicidade, `.gitignore`, `matches_repo` |
| `CONTEXT.md` | docs | Glossário: "Issue registry" |

### Impact

- **Functionality:** nenhuma mudança no comportamento atual — o módulo ainda
  não é importado por nenhum fluxo de produção. A T3 fará a primeira ligação.
- **Performance:** nenhuma; a leitura é um único `open()` e a gravação um
  `os.replace()`.
- **Compatibility:** nenhuma. O arquivo `.gitpr/conf/github.yml` é criado
  apenas na primeira gravação; `.gitpr/conf/gitpr.config.yml` continua
  versionado (o `.gitignore` recebe só o arquivo novo, por ADR-001).
- **Decisão de fronteira:** o registro não imprime nada. `load()` devolve
  `RegistryLoad.error` e `record()` devolve `gitignore_updated`; a mensagem de
  uma linha fica no chamador (T3), onde o i18n e a tela são de casa.
- **Testes:** `tests/issue_autoclose/test_issue_registry.py` — 23 passed,
  5 subtests passed.

### Verificação da suíte

A suíte completa deste checkout Windows é instável por motivos pré-existentes,
alheios a esta tarefa. Execuções:

- Tudo exceto `tests/test_config_app.py` e `tests/test_commit_app.py`
  (que são os dois arquivos de UI instáveis):
  **3038 passed, 2 skipped, 1 deselected**; 8 falhas em `tests/test_plugins.py`
  por vazamento de `GITPR_LINTER_SECURITY` entre suítes.
- O prefixo inteiro até `test_plugins.py` em um único processo, com detector de
  vazamento: **2069 passed, 0 falhas, nenhum vazamento** — as mesmas 8 falhas
  não se reproduzem.
- Os dois arquivos de UI isolados: **102 passed**.
- Subdiretórios completos (`application` a `unit`): **1299 passed**.

Nenhuma falha ocorre em teste que importe o módulo novo. O problema é o mesmo
já visto na T0 (um teste de TUI trava sem TTY no Windows): a suíte depende de
estado de processo e do perfil `~/.gitpr` do desenvolvedor.

### Next steps

- T2: `ScmProvider.get_issue`, `get_default_branch`, `closing_line` e
  `IssueInfo`, com a implementação do GitHub.
- T3: `register_created_issue` chamado por `IssueApp.action_create_issue`;
  é lá que a mensagem única do `.gitignore` será impressa.
- Aguardar confirmação do usuário antes da T2.
