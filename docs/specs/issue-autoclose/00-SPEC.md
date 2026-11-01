# SPEC — Fechamento automático de issue no PR (`close #N`)

> Para execução no Claude Code. Leia antes: `glossario.md`, `adrs/`, `entrevista.md`.
> Decisões estão fechadas nos ADRs. Se o código real divergir, pare e pergunte.

## 1. Objetivo

Quando o usuário cria uma issue com `gitpr -is` (provider GitHub), o gitpr grava o número em `.gitpr/conf/github.yml`. No próximo `gitpr` (fluxo de PR), se essa issue ainda estiver aberta, o gitpr pergunta se deve adicionar `close #N` à descrição do PR, imediatamente antes do badge.

## 2. Fluxo alvo

1. `gitpr -is` cria a issue com sucesso → `IssueRegistry.record(...)`.
2. `gitpr` (fluxo padrão) inicia:
   1. Se a feature estiver desligada, `--no-close-issue` presente ou provider diferente de GitHub: pula tudo.
   2. Lê o registro. Sem registro, ou registro de outro repositório: pula.
   3. Consulta a issue (`ScmProvider.get_issue`).
      - Aberta e não é PR: segue para o passo 4.
      - Fechada, 404 ou PR: limpa o registro em silêncio e pula.
      - Erro de rede, 401/403, 5xx ou timeout: aviso de uma linha, mantém o registro, pula.
   4. Decide:
      - `--close-issue`: aceita sem perguntar.
      - Sem TTY: não pergunta e não insere.
      - Com TTY: pergunta (padrão Sim). Se a branch de destino configurada ≠ branch padrão do repositório, inclui o aviso.
   5. Guarda a decisão em `PrContext.close_issue`.
3. TUI de stage → geração da descrição → montagem final do corpo.
4. Na montagem final: se `PrContext.close_issue` existir e o corpo não tiver keyword de fechamento para o número, insere a linha de fechamento antes do badge.
5. PR criado com sucesso e linha inserida (ou já presente por decisão do usuário): limpa o registro.

## 3. Tarefas

Cada tarefa é um commit isolado. Rode os testes ao final de cada uma.

### T0 — Investigação (sem código de produção)
Entregue um relatório curto com caminhos e trechos reais para:
1. Onde `gitpr -is` cria a issue e onde o número retornado fica disponível. Liste todos os outros caminhos que criam issue no GitHub (TUI de Issue, MCP, chat).
2. A interface atual de `ScmProvider` e de `GitHubProvider`: existem `get_issue` e `get_default_branch`? Qual o formato de retorno ao criar issue?
3. O ponto único de montagem final do corpo do PR e como o badge é inserido hoje (ou se ainda não existe).
4. O início do fluxo `gitpr` padrão: onde a TUI de stage é aberta e onde cabe a pergunta antes dela (premissa P1).
5. Como a branch de destino do PR é configurada e lida.
6. A TUI "config": como as opções são declaradas e persistidas.
7. O sistema de i18n: onde ficam as chaves e o teste que valida os 5 idiomas.
8. Como o projeto detecta TTY e modo não interativo hoje.
9. O mecanismo de leitura e escrita de YAML já usado, e se `.gitpr/conf/` já existe.
10. O padrão de testes (fixtures, mocks de HTTP) e de metrics.
Termine com uma lista de divergências em relação a esta SPEC e perguntas pendentes. Não avance sem confirmação.

### T1 — Registro (`IssueRegistry`)
- Módulo novo, por exemplo `src/infrastructure/state/issue_registry.py` (adaptar à estrutura real).
- API: `load()`, `record(issue)`, `clear()`, `matches_repo(owner_repo)`.
- Formato: ADR-001. Escrita atômica; arquivo corrompido tratado conforme o ADR.
- Garantir `.gitignore` na primeira gravação (`git check-ignore`; só acrescenta se necessário; mensagem de uma linha).
- Sem dependência de rede.

### T2 — Extensão do `ScmProvider`
- Adicionar `get_issue(repo, number) -> IssueInfo` e `get_default_branch(repo) -> str` e `closing_line(number) -> str`.
- `IssueInfo`: `number`, `title`, `url`, `state`, `is_pull_request`.
- `GitHubProvider`: implementação com `GET /repos/{o}/{r}/issues/{n}` e `GET /repos/{o}/{r}`; `closing_line` devolve `close #N`.
- Demais providers: `NotImplementedError`.
- Timeout configurável (padrão 5 s). Erros mapeados para exceções tipadas: `IssueNotFound`, `ProviderUnavailable`, `ProviderAuthError`.

### T3 — Gravação ao criar issue
- Todos os caminhos de criação de issue GitHub chamam `IssueRegistry.record(...)` após sucesso, por uma função única (por exemplo `register_created_issue`).
- Só grava quando o provider é GitHub.
- Falha ao gravar não pode quebrar a criação da issue: aviso e segue.
- Registrar também `branch` atual, `created_at` e `repo`.

### T4 — Caso de uso `resolve_close_issue`
- Função pura de orquestração que recebe provider, registry, flags, `is_tty`, `target_branch` e uma função `ask` injetável.
- Implementa a árvore do passo 2.2 do fluxo e devolve `CloseIssueDecision | None`.
- Não escreve em tela diretamente; usa a função `ask` e um logger.
- Retorna também o aviso de branch de destino, quando aplicável.

### T5 — Inserção no corpo do PR
- No ponto único de montagem final do corpo: se houver decisão positiva, inserir `\n\nclose #N` imediatamente antes do badge (ou ao fim do corpo, se não houver badge).
- Idempotência conforme ADR-004: regex insensível a maiúsculas, com limite de palavra, aceitando `owner/repo#N`.
- Não alterar nada quando não houver decisão.

### T6 — Integração no fluxo `gitpr`
- Chamar `resolve_close_issue` no início do fluxo, antes da TUI de stage, e guardar o resultado em `PrContext`.
- Após a criação do PR com sucesso, chamar `IssueRegistry.clear()` se a linha foi aplicada ou já estava presente.
- Se a criação do PR falhar ou for cancelada, manter o registro.
- Flags de CLI: `--close-issue` e `--no-close-issue` (mutuamente exclusivas; erro claro se usadas juntas).

### T7 — Configuração e TUI "config"
- Nova chave `issue_autoclose.enabled` (padrão `true`) e `issue_autoclose.request_timeout_seconds` (padrão 5).
- Opção de ligar/desligar na TUI "config", seguindo o padrão das opções existentes.
- Atualizar o schema de configuração.

### T8 — i18n e metrics
- Chaves de i18n nos 5 idiomas: pergunta, aviso de branch de destino, aviso de falha de verificação, aviso de `.gitignore`, mensagem de erro das flags conflitantes.
- Passar no teste de auditoria de chaves existente.
- Evento opcional de metrics (`issue_autoclose` com `asked`, `accepted`, `skipped_reason`), sem dados sensíveis, seguindo o padrão local de `metrics.py`.

### T9 — Documentação
- README/ajuda da CLI: descrever o comportamento, as flags e o arquivo de registro.
- Nota no changelog.

## 4. Contratos

```python
@dataclass
class RegisteredIssue:
    repo: str          # "owner/name"
    number: int
    title: str
    url: str
    created_at: str    # ISO 8601
    branch: str | None

@dataclass
class IssueInfo:
    number: int
    title: str
    url: str
    state: str         # "open" | "closed"
    is_pull_request: bool

@dataclass
class CloseIssueDecision:
    number: int
    title: str
    line: str          # ex.: "close #123"

@dataclass
class PrContext:
    close_issue: CloseIssueDecision | None = None
```

Arquivo `.gitpr/conf/github.yml`:

```yaml
schema_version: 1
last_issue:
  repo: owner/name
  number: 123
  title: "Título da issue"
  url: https://github.com/owner/name/issues/123
  created_at: "2026-11-01T09:00:00-03:00"
  branch: main
```

## 5. Mensagem do prompt

`Issue #123 – <título> está aberta. Adicionar "close #123" ao final da descrição do PR? [S/n]`

Com aviso de branch: `Atenção: o PR aponta para "develop" e a branch padrão é "main". O GitHub só fecha a issue quando o merge é feito na branch padrão.`

## 6. Casos de borda

- `#12` não pode casar com `#123` na idempotência.
- Corpo que já contém `Closes #123` escrito pela IA ou pelo usuário: não duplica.
- Issue de outro repositório no registro: ignorada.
- Dois `gitpr -is` seguidos: vale o último.
- `gitpr` sem registro: comportamento idêntico ao atual, sem chamada de rede.
- Provider diferente de GitHub: feature inativa, sem erro.
- Registro com `number` inválido ou campos faltando: tratado como corrompido.
- Usuário interrompe com Ctrl+C na pergunta: sai do fluxo como em qualquer outro prompt do gitpr, sem alterar o registro.

## 7. Testes obrigatórios

1. Registro: gravar, ler, limpar; escrita atômica; arquivo corrompido; `.gitignore` acrescentado uma única vez.
2. Provider (HTTP mockado): issue aberta, fechada, PR, 404, 403, timeout, 5xx.
3. `resolve_close_issue`: cada ramo da árvore (sem registro, outro repo, aberta com TTY sim/não, sem TTY, `--close-issue`, `--no-close-issue`, falha de rede, branch de destino diferente da padrão).
4. Inserção: antes do badge, sem badge, com seção "Explain my PR", idempotência com variações de keyword e de número.
5. Ciclo de vida: limpa após PR criado; mantém após "não"; mantém após falha na criação do PR.
6. Gravação: todos os caminhos de criação de issue gravam; falha de gravação não quebra a criação.
7. CLI: flags conflitantes geram erro claro; sem TTY nunca pergunta.
8. Não regressão: sem registro, o fluxo `gitpr` e o corpo do PR ficam idênticos ao comportamento anterior; nenhuma chamada de rede extra.
9. i18n: auditoria dos 5 idiomas passa.
10. Segurança: o registro não contém token; o log não imprime token.

## 8. Critérios de aceite

- Fluxo manual feito nos itens 1 a 4 da seção 12 funciona.
- Todos os testes passam, incluindo a suíte anterior.
- Nenhum `requests`/HTTP novo fora do provider.
- Nenhuma chave de i18n faltando.

## 9. Fora de escopo

- GitLab, Bitbucket e Azure DevOps.
- "Não perguntar mais para esta issue".
- Múltiplas issues registradas ao mesmo tempo.
- Registro por usuário.
- Criar issue automaticamente ou fechar issue por API.
- Alterar a lógica de merge ou o fechamento fora do texto do PR.

## 10. Riscos

- A premissa P1 (momento da pergunta) pode precisar de ajuste na T6.
- A API de issues do GitHub também devolve PRs; o campo `pull_request` deve ser checado.
- Rate limit da API em uso intenso: tratado como falha de rede (ADR-003).
- Modificar `.gitignore` do usuário: restrito a uma linha, idempotente e informado.

## 11. Ordem de execução

T0 → T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9. Um commit por tarefa, com testes verdes.

## 12. Teste manual final

1. Em um repositório de teste no GitHub, rode `gitpr -is` e crie uma issue. Confirme `.gitpr/conf/github.yml` e a entrada no `.gitignore`.
2. Rode `gitpr`. Confirme a pergunta antes da TUI de stage, responda Sim, termine o PR e confira `close #N` antes do badge.
3. Confirme que o registro foi limpo após a criação do PR.
4. Crie outra issue, feche-a no GitHub, rode `gitpr`: não deve perguntar, e o registro deve ser limpo.
5. Rode `gitpr --no-close-issue` e `gitpr` em um terminal sem TTY: não deve perguntar.
